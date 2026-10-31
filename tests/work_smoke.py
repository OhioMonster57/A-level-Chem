"""Exercise work history with explicit mocked AI replies; makes no provider calls."""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright, expect

OUT=Path('/tmp/element-work-tests');OUT.mkdir(exist_ok=True)
photo=OUT/'synthetic-work.jpg'
im=Image.new('RGB',(1100,1400),'white');draw=ImageDraw.Draw(im)
draw.text((60,100),'SYNTHETIC TEST PHOTO - NO REAL STUDENT WORK',fill='black')
draw.text((60,200),'Q1: Calculate amounts and interpret atomic masses.',fill='black')
draw.text((60,280),'Answer: synthetic example workings.',fill='black')
draw.text((60,800),'Q2: Explain isotopes. Answer: synthetic response.',fill='black');im.save(photo)

def fixture(page_id):
    def q(label,key,score,topics,box,difficulty):
        return {'label':label,'question_text':'Synthetic '+label+' test question only','student_answer':'Synthetic test answer <script>alert(1)</script>',
                'status':'graded','clarification':'','confidence':1,'difficulty':difficulty,'regions':[{'page_id':page_id,**box}],
                'topics':topics,'rubric':[{'dimension':dim,'possible':p,'earned':p*score/100,'feedback':'Synthetic fixture rationale.'} for dim,p in [('accuracy',50),('completeness',20),('reasoning',20),('communication',10)]],
                'feedback':'Synthetic fixture feedback. Practise showing working.','correction':'Synthetic corrected approach.','skills_to_practice':['Show formula substitution'],
                'percentage':score,'question_key':key*64,'rubric_version':'element-percent-v1'}
    return {'model':'MOCK-TEST-ONLY','rubric_version':'element-percent-v1','questions':[
        q('Q1','a',80,[{'topic':1,'allocation':40,'objective_refs':['1.8']},{'topic':5,'allocation':60,'objective_refs':['5.7']}],{'x':0,'y':0,'width':1,'height':.45},'standard'),
        q('Q2','b',50,[{'topic':1,'allocation':100,'objective_refs':['1.5']}],{'x':0,'y':.5,'width':1,'height':.45},'foundation')]}

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1400,'height':1050})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.route('**/api/health',lambda route:route.fulfill(json={'configured':True,'model':'MOCK-TEST-ONLY'}))
    def mark(route):
        request=route.request.post_data_json
        route.fulfill(json=fixture(request['pages'][0]['id']))
    page.route('**/api/mark-work',mark)
    page.goto('http://127.0.0.1:3000/#work')
    expect(page.get_by_role('button',name='Upload completed work',exact=False)).to_be_enabled()
    page.locator('#work-photos').set_input_files(photo)
    expect(page.get_by_role('heading',name='Photos ready for marking')).to_be_visible()
    page.reload()
    expect(page.get_by_role('heading',name='Photos ready for marking')).to_be_visible()
    page.get_by_role('button',name='Connect marking backend').click()
    page.locator('#work-backend').fill('http://127.0.0.1:3000')
    page.locator('#work-access').fill('test-session-token-not-a-real-credential')
    page.get_by_role('button',name='Check & save connection').click()
    expect(page.locator('#work-dialog')).not_to_be_visible()
    page.get_by_role('button',name='Read & mark these photos').click()
    expect(page.locator('#toast')).to_contain_text('confirm consent')
    page.locator('#work-consent').check()
    page.get_by_role('button',name='Read & mark these photos').click()
    expect(page.locator('.work-question')).to_have_count(2)
    expect(page.locator('.work-question').first).to_contain_text('Review before counting')
    page.locator('.work-question').first.get_by_role('button',name='Check & review').click()
    expect(page.locator('.work-transcript').nth(1)).to_contain_text('<script>')
    page.get_by_role('button',name='Accept checked assessment').click()
    page.locator('.work-question').nth(1).get_by_role('button',name='Check & review').click()
    page.get_by_role('button',name='Accept checked assessment').click()
    page.locator('#work-topic-filter').select_option('1')
    expect(page.locator('.work-topic-panel h2')).to_contain_text('60%')
    expect(page.locator('.work-topic-panel')).to_contain_text('2 of 26')
    assert page.locator('main canvas.work-crop').count()==2
    assert page.locator('main canvas.work-crop').first.evaluate('(c)=>c.width')>1
    with page.expect_download() as result:
        page.get_by_role('button',name='Export work history',exact=False).click()
    backup=OUT/'work-backup.json';result.value.save_as(backup)
    data=json.loads(backup.read_text())
    assert len(data['submissions'])==1 and len(data['submissions'][0]['questions'])==2
    assert 'test-session-token' not in backup.read_text()
    assert data['submissions'][0]['pages'][0]['dataUrl'].startswith('data:image/jpeg;')
    # A newer accepted repeat remains in history but replaces the previous question in the estimate.
    repeat=json.loads(json.dumps(data['submissions'][0]));repeat['id']='repeat-submission-test'
    repeat['createdAt']=(datetime.now(timezone.utc)+timedelta(seconds=2)).isoformat()
    repeat['questions']=repeat['questions'][:1];repeat['questions'][0]['id']='repeat-question-test'
    repeat['questions'][0]['percentage']=100
    for criterion in repeat['questions'][0]['rubric']:criterion['earned']=criterion['possible']
    data['submissions'].append(repeat)
    merged=OUT/'repeat-backup.json';merged.write_text(json.dumps(data))
    page.locator('#work-backup-file').set_input_files(merged)
    page.get_by_role('button',name='Merge work history').click()
    expect(page.locator('.work-topic-panel h2')).to_contain_text('67%')
    expect(page.locator('.work-question')).to_have_count(3)
    page.reload()
    page.locator('#work-topic-filter').select_option('1')
    expect(page.locator('.work-topic-panel h2')).to_contain_text('67%')
    page.screenshot(path=str(OUT/'marked-work.png'),full_page=True)
    page.goto('http://127.0.0.1:3000/#topic/1')
    expect(page.locator('.work-topic-panel h2')).to_contain_text('67%')
    page.set_viewport_size({'width':390,'height':844})
    page.goto('http://127.0.0.1:3000/#work')
    expect(page.locator('.work-question')).to_have_count(3)
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
    page.locator('.work-question').first.get_by_role('button',name='View assessment').click()
    page.get_by_role('button',name='Flag / exclude from estimate').click()
    page.locator('#work-topic-filter').select_option('1')
    expect(page.locator('.work-topic-panel h2')).to_contain_text('60%')
    # Invalid imported scores cannot change the saved history.
    bad=json.loads(json.dumps(data));bad['submissions'][0]['questions'][0]['percentage']=999
    badfile=OUT/'bad-work.json';badfile.write_text(json.dumps(bad))
    page.locator('#work-backup-file').set_input_files(badfile)
    expect(page.locator('#toast')).to_contain_text('Invalid percentage')
    checklist_before=page.evaluate("localStorage.getItem('element-9ch0-v1')")
    page.locator('.work-question').first.get_by_role('button',name='Delete upload',exact=True).click()
    page.locator('#work-delete-confirm').click()
    expect(page.locator('.work-question')).to_have_count(2)
    expect(page.locator('.work-topic-panel h2')).to_contain_text('60%')
    assert page.evaluate("localStorage.getItem('element-9ch0-v1')")==checklist_before
    assert not errors,errors
    print('PASS: photo persistence, consent, session connection, mocked marking, crops, review, mixed-topic weighted scores, backup, repeat-attempt history, flags, invalid data, mobile layout. No real AI calls.')
    browser.close()
