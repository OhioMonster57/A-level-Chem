import base64
from copy import deepcopy
import io
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer

import grading
from server import Handler, GRADE_TIMES

PAGES = [{'id':'test-page', 'dataUrl':'data:image/png;base64,'+base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'synthetic test bytes').decode()}]

def question():
    return {'label':'Q1', 'question_text':'Calculate the amount of 2 g of a substance with molar mass 20 g/mol.',
            'student_answer':'0.1 mol', 'status':'graded','clarification':'','confidence':.9,'difficulty':'standard',
            'regions':[{'page_id':'test-page','x':0,'y':0,'width':1,'height':1}],
            'topics':[{'topic':5,'allocation':100,'objective_refs':['5.7']}],
            'rubric':[{'dimension':d,'possible':p,'earned':e,'feedback':'Synthetic fixture feedback'} for d,p,e in [('accuracy',40,40),('completeness',15,15),('reasoning',35,25),('communication',10,10)]],
            'feedback':'Synthetic fixture: correct result; show the division.','correction':'n = m/M = 2/20 = 0.1 mol.', 'skills_to_practice':['Show formula substitution']}

class GradingValidationTests(unittest.TestCase):
    def test_recomputes_percentage_instead_of_trusting_model_score(self):
        q=question();q['percentage']=100
        result=grading.validate_result({'questions':[q]},PAGES)
        self.assertEqual(result['questions'][0]['percentage'],90)
        self.assertEqual(len(q['question_key']),64)

    def test_uncertain_reading_is_never_scored(self):
        q=question();q['confidence']=.4
        q=grading.validate_result({'questions':[q]},PAGES)['questions'][0]
        self.assertEqual(q['status'],'needs_clarification')
        self.assertIsNone(q['percentage'])
        self.assertEqual(q['rubric'],[])

    def test_rejects_bad_topic_references_allocations_and_crops(self):
        for change in ['reference','allocation','crop','rubric']:
            q=question()
            if change=='reference':q['topics'][0]['objective_refs']=['1.1']
            if change=='allocation':q['topics'][0]['allocation']=60
            if change=='crop':q['regions'][0]['x']=.5
            if change=='rubric':q['rubric'][0]['earned']=101
            with self.subTest(change=change),self.assertRaises(grading.GradingError):
                grading.validate_result({'questions':[q]},PAGES)

    def test_pages_cannot_reference_arbitrary_remote_urls(self):
        with self.assertRaises(grading.GradingError):
            grading.validate_pages({'pages':[{'id':'p','dataUrl':'https://example.com/private'}]})
        with self.assertRaises(grading.GradingError):
            grading.validate_pages({'pages':[PAGES[0],PAGES[0]]})

    def test_provider_request_has_images_schema_no_storage_and_sanitised_errors(self):
        calls=[]
        def opener(request,timeout):
            calls.append(json.loads(request.data))
            body={'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps({'questions':[question()]})}]}]}
            return io.BytesIO(json.dumps(body).encode())
        with patch.dict(os.environ,{'STUDY_AI_API_KEY':'test-only-not-a-real-key'}):
            result=grading.grade({'pages':PAGES},opener=opener)
            self.assertEqual(result['questions'][0]['percentage'],90)
            self.assertIs(calls[0]['store'],False)
            self.assertTrue(calls[0]['text']['format']['strict'])
            self.assertEqual(calls[0]['input'][0]['content'][-1]['type'],'input_image')
            def denied(*args,**kwargs):
                raise urllib.error.HTTPError('https://api.openai.com',401,'sensitive test body',{},None)
            with self.assertRaisesRegex(grading.GradingError,'credential was rejected'):
                grading.grade({'pages':PAGES},opener=denied)

class QuietHandler(Handler):
    def log_message(self,*args):pass

class GatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def call(self,path,body=None,token='',origin='https://ohiomonster57.github.io'):
        headers={'Origin':origin}
        if token:headers['Authorization']='Bearer '+token
        request=urllib.request.Request(self.url+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
        try:
            with urllib.request.urlopen(request) as response:return response.status,json.load(response),response.headers
        except urllib.error.HTTPError as error:return error.code,json.load(error),error.headers
    def test_gateway_auth_cors_and_provider_are_separate(self):
        with patch.dict(os.environ,{'STUDY_AI_API_KEY':'test-only','STUDY_ACCESS_TOKEN':'test-token','STUDY_ALLOWED_ORIGIN':'https://ohiomonster57.github.io'}),patch('grading.grade',return_value={'questions':[]} ) as mocked:
            GRADE_TIMES.clear()
            self.assertEqual(self.call('/api/mark-work',{'pages':PAGES})[0],401)
            self.assertEqual(self.call('/api/mark-work',{'pages':PAGES},'test-token','https://untrusted.example')[0],403)
            self.assertEqual(self.call('/api/health',token='wrong')[0],401)
            self.assertEqual(self.call('/api/import-spec',{'not':'a pdf'})[0],401)
            status,body,headers=self.call('/api/mark-work',{'pages':PAGES},'test-token')
            self.assertEqual(status,200)
            self.assertEqual(headers['Access-Control-Allow-Origin'],'https://ohiomonster57.github.io')
            self.assertEqual(mocked.call_count,1)
    def test_local_session_is_disabled_by_default_and_same_origin_only(self):
        with patch.dict(os.environ,{'STUDY_LOCAL_MODE':'','STUDY_ACCESS_TOKEN':'local-test'}):
            self.assertEqual(self.call('/api/local-session',origin=self.url)[0],403)
        with patch.dict(os.environ,{'STUDY_LOCAL_MODE':'1','STUDY_ACCESS_TOKEN':'local-test'}):
            self.assertEqual(self.call('/api/local-session',origin=self.url)[0],403)
            req=urllib.request.Request(self.url+'/api/local-session',headers={'X-Element-Local':'1','Origin':self.url})
            with urllib.request.urlopen(req) as response:
                self.assertEqual(json.load(response)['accessToken'],'local-test')
            bad=urllib.request.Request(self.url+'/api/local-session',headers={'X-Element-Local':'1','Origin':'https://untrusted.example'})
            with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(bad)
            self.assertEqual(error.exception.code,403)

    def test_unconfigured_backend_is_honest(self):
        with patch.dict(os.environ,{'STUDY_AI_API_KEY':'','OPENAI_API_KEY':'','STUDY_ACCESS_TOKEN':''}):
            self.assertEqual(self.call('/api/mark-work',{'pages':PAGES},origin=self.url)[0],503)

if __name__=='__main__':unittest.main()
