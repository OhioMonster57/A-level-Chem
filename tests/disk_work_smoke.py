"""Real local disk persistence and progress UI; AI reply explicitly mocked."""
import asyncio
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright, expect

ROOT=Path(__file__).resolve().parents[1]

async def exercise(folder,port):
    data_dir=folder/'study-files';photo=folder/'question.jpg'
    im=Image.new('RGB',(1000,1400),'white');d=ImageDraw.Draw(im);d.text((70,150),'SYNTHETIC TEST: calculate n from m and M',fill='black');d.text((70,280),'Answer and workings for storage test only.',fill='black');im.save(photo)
    env={**os.environ,'STUDY_AI_API_KEY':'fake-key-no-provider-calls','PYTHONUNBUFFERED':'1'}
    def start():
        proc=subprocess.Popen([sys.executable,'run_local.py','--port',str(port),'--no-browser','--data-dir',str(data_dir)],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for _ in range(70):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=1):return proc
            except OSError:
                if proc.poll() is not None:raise AssertionError(proc.stdout.read())
                time.sleep(.1)
        raise AssertionError('Local server did not start')
    process=start();url=f'http://127.0.0.1:{port}'
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            context=await browser.new_context(viewport={'width':1400,'height':1000});page=await context.new_page();errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            async def mark(route):
                body=route.request.post_data_json;pid=body['pages'][0]['id']
                await asyncio.sleep(2.5)
                q={'label':'Q1','question_text':'Calculate an amount of substance.','student_answer':'Synthetic test answer','status':'graded','clarification':'','confidence':.9,'difficulty':'standard','regions':[{'page_id':pid,'x':0,'y':0,'width':1,'height':.6}], 'topics':[{'topic':5,'allocation':100,'objective_refs':['5.7']}], 'rubric':[{'dimension':d,'possible':v,'earned':v*.85,'feedback':'Test-only rationale'} for d,v in [('accuracy',50),('completeness',20),('reasoning',20),('communication',10)]], 'feedback':'Show units in the final result.','correction':'Use n = m/M.','skills_to_practice':['Record final units'],'percentage':85,'question_key':hashlib.sha256(b'calculate an amount of substance').hexdigest(),'rubric_version':'test-only'}
                q['rubric'][0]['earned']=45.5;q['rubric'][2]['earned']=14
                await route.fulfill(json={'questions':[q],'model':'MOCK-TEST-ONLY','rubric_version':'test-only'})
            await page.route('**/api/mark-work',mark)
            await page.goto(url+'/#work')
            await expect(page.get_by_role('button',name='Upload completed work',exact=False)).to_be_enabled()
            await expect(page.locator('main')).to_contain_text(str(data_dir))
            await page.locator('#work-photos').set_input_files(photo)
            await expect(page.get_by_role('heading',name='Photos ready for marking')).to_be_visible()
            records=list(data_dir.glob('uploads/*/record.json'));assert len(records)==1
            original=json.loads(records[0].read_text(encoding='utf-8'))
            assert list(data_dir.glob('uploads/*/originals/*.jpg'))
            await page.locator('#work-consent').check()
            await page.get_by_role('button',name='Read & mark these photos').click()
            await expect(page.locator('.work-progress')).to_be_visible()
            await expect(page.locator('#work-phase')).to_contain_text('Waiting')
            await expect(page.locator('#work-progress-bar')).not_to_have_attribute('value')
            await expect(page.locator('.work-question')).to_have_count(1)
            await expect(page.locator('.work-notice.success')).to_contain_text('Marking complete')
            assert list(data_dir.glob('topics/topic-05/*/*-crop-01.jpg'))
            await page.locator('.work-question').get_by_role('button',name='Check & review').click()
            await page.get_by_role('button',name='Accept checked assessment').click()
            await page.goto(url+'/#topic/5')
            await expect(page.locator('.topic-question-library article')).to_have_count(1)
            await expect(page.locator('.topic-question-library')).to_contain_text('85%')
            await page.locator('.topic-question-library').get_by_role('button',name='Weakness',exact=True).click()
            await expect(page.locator('#work-dialog')).to_contain_text('5.7 · Review point')
            await expect(page.locator('#work-dialog')).to_contain_text('Knowledge tip:')
            await expect(page.locator('#work-dialog')).to_contain_text('Show units in the final result.')
            await expect(page.locator('#work-dialog')).to_contain_text('Reasoning & working')
            await expect(page.locator('#work-dialog')).to_contain_text('not a fresh AI request')
            await page.locator('#work-dialog [data-work-action="close"]').first.click()
            await page.goto(url+'/#topic/2')
            await page.locator('.topic-question-library').get_by_role('button',name='Weakness',exact=True).click()
            await expect(page.locator('#work-dialog')).to_contain_text('Not enough evidence yet')
            await expect(page.locator('#work-dialog .weakness-point')).to_have_count(0)
            await page.keyboard.press('Escape')
            await page.goto(url+'/#topic/5')
            await page.locator('[data-status]').first.select_option('confident')
            for _ in range(40):
                disk=json.loads((data_dir/'checklist.json').read_text(encoding='utf-8'))
                if any(r['status']=='confident' for r in disk['records'].values()):break
                await asyncio.sleep(.05)
            else:raise AssertionError('Checklist did not save to disk')
            await page.goto(url+'/#overview')
            await expect(page.locator('.confidence-charts')).to_be_visible()
            await expect(page.locator('.confidence-legend')).to_contain_text('Confident')
            await page.screenshot(path='/tmp/element-disk-dashboard.png',full_page=True)
            await context.close()  # Removes access to this context's browser state.
            process.terminate();process.communicate(timeout=10)
            process=start()
            context=await browser.new_context();page=await context.new_page()
            await page.goto(url+'/#work')
            await expect(page.locator('.work-question')).to_have_count(1)
            await expect(page.locator('.work-question')).to_contain_text('Accepted evidence')
            await page.goto(url+'/#topic/5')
            await expect(page.locator('.topic-question-library article')).to_have_count(1)
            await expect(page.locator('[data-status]').first).to_have_value('confident')
            # An explicit provider failure is shown persistently, not just as a short toast.
            ImageDraw.Draw(im).rectangle((0,0,120,120),fill='red');im.save(photo)
            await page.goto(url+'/#work');await page.locator('#work-photos').set_input_files(photo)
            await expect(page.get_by_role('heading',name='Photos ready for marking')).to_be_visible()
            await page.route('**/api/mark-work',lambda route:route.fulfill(status=502,json={'error':'Synthetic test: API usage limit reached.'}))
            await page.locator('#work-consent').check();await page.get_by_role('button',name='Read & mark these photos').click()
            await expect(page.locator('.work-notice.error')).to_contain_text('API usage limit reached')
            # Move an existing IndexedDB record to disk without deleting the browser copy.
            legacy=json.loads(records[0].read_text(encoding='utf-8'));legacy['id']='legacy-browser-copy';legacy['title']='Legacy browser work'
            await page.evaluate('''value => new Promise((resolve,reject)=>{const r=indexedDB.open('element-marked-work-v1',1);r.onsuccess=()=>{const d=r.result;const t=d.transaction('submissions','readwrite');t.objectStore('submissions').put(value);t.oncomplete=()=>{d.close();resolve();};t.onerror=()=>reject(t.error);};r.onerror=()=>reject(r.error);})''',legacy)
            await page.get_by_role('button',name='Copy previous browser history to folder').click()
            await expect(page.locator('#toast')).to_contain_text('copied to your study folder')
            assert (data_dir/'uploads/legacy-browser-copy/record.json').exists()
            improved=json.loads(records[0].read_text(encoding='utf-8'));improved['id']='improved-upload'
            improved['createdAt']=(datetime.now(timezone.utc)+timedelta(seconds=2)).isoformat()
            improved['questions'][0]['id']='improved-question';improved['questions'][0]['percentage']=100
            for criterion in improved['questions'][0]['rubric']:criterion['earned']=criterion['possible']
            backup=folder/'improved-work.json';backup.write_text(json.dumps({'format':'element-marked-work','version':1,'submissions':[improved]}),encoding='utf-8')
            await page.locator('#work-backup-file').set_input_files(backup)
            await page.get_by_role('button',name='Merge work history').click()
            await page.goto(url+'/#topic/5')
            await page.locator('.topic-question-library').get_by_role('button',name='Weakness',exact=True).click()
            await expect(page.locator('#work-dialog')).to_contain_text('No low-scoring areas identified')
            await expect(page.locator('#work-dialog')).to_contain_text('Improvement in repeated questions')
            await expect(page.locator('#work-dialog .weakness-point')).to_have_count(0)
            assert not errors,errors
            await browser.close()
        print('PASS: disk originals/crops/question files, real marking progress UI, persistent errors, topic library, confidence charts, checklist persistence, fresh browser and process restart. No AI calls.')
    finally:
        if process.poll() is None:process.terminate();process.communicate(timeout=10)

with tempfile.TemporaryDirectory() as folder:
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    asyncio.run(exercise(Path(folder),port))
