from pathlib import Path
import base64
import json
import tempfile
import unittest
from work_store import WorkStore, StoreError

IMAGE='data:image/jpeg;base64,'+base64.b64encode(b'\xff\xd8\xfftest image').decode()

def payload():
    return {'submission':{'id':'upload-test','title':'Δ chemistry','pages':[{'id':'photo-test','dataUrl':IMAGE}],
            'questions':[{'id':'question-test','question_text':'ΔH question','topics':[{'topic':5},{'topic':8}],
                          'regions':[{'page_id':'photo-test'}]}]},
            'crops':[{'questionId':'question-test','index':0,'dataUrl':IMAGE}]}

class WorkStoreTests(unittest.TestCase):
    def test_real_originals_crops_and_records_survive_new_store(self):
        with tempfile.TemporaryDirectory() as d:
            store=WorkStore(d);store.save(payload())
            root=Path(d)
            self.assertTrue((root/'uploads/upload-test/originals/photo-test.jpg').exists())
            for topic in [5,8]:
                self.assertTrue((root/f'topics/topic-{topic:02d}/upload-test/question-test-crop-01.jpg').exists())
            self.assertEqual(WorkStore(d).all()[0]['questions'][0]['question_text'],'ΔH question')
            self.assertIn('ΔH', (root/'topics/topic-05/upload-test/question-test.json').read_text(encoding='utf-8'))
    def test_invalid_save_does_not_replace_previous_record(self):
        with tempfile.TemporaryDirectory() as d:
            store=WorkStore(d);store.save(payload());before=store.all()
            broken=payload();broken['crops']=[]
            with self.assertRaises(StoreError):store.save(broken)
            self.assertEqual(store.all(),before)
            bad=payload();bad['submission']['id']='../escape'
            with self.assertRaises(StoreError):store.save(bad)
    def test_mapping_changes_clean_only_known_assets_and_delete_is_scoped(self):
        with tempfile.TemporaryDirectory() as d:
            store=WorkStore(d);store.save(payload())
            note=Path(d)/'topics/topic-05/upload-test/my-notes.txt';note.write_text('Keep my file',encoding='utf-8')
            changed=payload();changed['submission']['questions'][0]['topics']=[{'topic':8}]
            store.save(changed)
            self.assertTrue(note.exists())
            self.assertFalse((note.parent/'question-test-crop-01.jpg').exists())
            other=payload();other['submission']['id']='another-upload';store.save(other)
            store.delete('upload-test')
            self.assertEqual([s['id'] for s in store.all()],['another-upload'])

if __name__=='__main__':unittest.main()
