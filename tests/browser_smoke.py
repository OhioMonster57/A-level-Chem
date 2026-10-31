"""Run against python3 server.py. Requires Playwright and Chromium."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ARTIFACTS = Path('/tmp/element-tests')
ARTIFACTS.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1050})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:3000')
    page.get_by_role('heading', name='Make room for a little chemistry.').wait_for()
    expect(page.locator('.topic-card')).to_have_count(4)
    assert 'Official 9CH0' in page.locator('.source-notice').inner_text()
    page.screenshot(path=str(ARTIFACTS/'overview.png'), full_page=True)
    page.locator('nav a[data-nav="syllabus"]').click()
    expect(page.locator('.topic-card')).to_have_count(19)
    page.get_by_role('button', name='Year 2', exact=True).click()
    expect(page.locator('.topic-card')).to_have_count(9)
    page.get_by_role('button', name='All topics', exact=True).click()
    page.locator('#topic-search').fill('electrode')
    expect(page.locator('.topic-card').first).to_be_visible()
    page.locator('#topic-search').fill('xyznotarealtopic')
    expect(page.locator('.topic-card')).to_have_count(0)
    page.locator('#topic-search').fill('')
    page.locator('.topic-card').first.click()
    first = page.locator('.objective-row').first
    objective_id = first.get_attribute('data-objective')
    first.locator('select').select_option('learning')
    expect(page.locator('#due-count')).to_have_text('1')
    page.locator('.objective-row').first.locator('[data-action="detail"]').click()
    page.locator('#objective-notes').fill('Q1: isotopes. Scored 3/4. <script>alert(1)</script>')
    page.locator('#source-verified').check()
    page.get_by_role('button', name='Save notes', exact=True).click()
    page.reload()
    expect(page.locator('.objective-row').first.locator('select')).to_have_value('learning')
    assert 'Source checked' in page.locator('.objective-row').first.inner_text()
    page.locator('.objective-row').first.locator('[data-action="detail"]').click()
    assert '<script>' in page.locator('#objective-notes').input_value()
    page.get_by_role('button', name='Good · 7 days', exact=True).click()
    expect(page.locator('#due-count')).to_have_text('0')
    expect(page.locator('.objective-row').first.locator('select')).to_have_value('confident')
    page.locator('#status-filter').select_option('ready')
    expect(page.locator('.objective-row')).to_have_count(0)
    page.locator('nav a[data-nav="revision"]').click()
    page.get_by_role('heading', name='Coming up next').wait_for()
    page.locator('nav a[data-nav="practical"]').click()
    page.locator('.audit-card').first.wait_for()
    expect(page.locator('.audit-card')).to_have_count(16)
    page.locator('.audit-card').first.click()
    page.locator('#practical-title').fill('Official practical title to check')
    page.locator('#practical-notes').fill('My apparatus, results and uncertainty record.')
    page.locator('#practical-complete').check()
    page.get_by_role('button', name='Save practical record').click()
    expect(page.locator('.audit-card').first).to_contain_text('Evidence recorded')
    page.locator('nav a[data-nav="sources"]').click()
    page.get_by_role('heading', name='Your study record, to keep.').wait_for()
    with page.expect_download() as download:
        page.get_by_role('button', name='Export backup').click()
    target = ARTIFACTS/'backup.json'
    download.value.save_as(target)
    backup = json.loads(target.read_text(encoding='utf-8'))
    assert backup['records'][objective_id]['status'] == 'confident'
    assert backup['practicals']['1']['complete'] is True
    page.locator('#backup-file').set_input_files(target)
    page.get_by_role('button', name='Replace with backup').click()
    expect(page.locator('#toast')).to_contain_text('Backup restored')
    bad = ARTIFACTS/'invalid.json'
    bad.write_text('{"version":1,"objectives":[],"records":{}}', encoding='utf-8')
    page.locator('#backup-file').set_input_files(bad)
    expect(page.locator('#toast')).to_contain_text('not a supported')
    assert json.loads(page.evaluate("localStorage.getItem('element-9ch0-v1')"))['records'][objective_id]['status'] == 'confident'
    response = page.request.post('http://127.0.0.1:3000/api/import-spec', data=b'not a PDF', headers={'Content-Type':'application/pdf'})
    assert response.status == 400
    source_pdf = page.request.get('http://127.0.0.1:3000/specification.pdf')
    assert source_pdf.status == 200 and source_pdf.body().startswith(b'%PDF-')
    known = page.request.post('http://127.0.0.1:3000/api/import-spec', data=source_pdf.body(), headers={'Content-Type':'application/pdf'})
    assert known.status == 200 and known.json()['knownSpecification'] is True
    assert known.json()['metadata']['mainObjectives'] == 325
    page.set_viewport_size({'width':390, 'height':844})
    page.goto('http://127.0.0.1:3000/#overview')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path=str(ARTIFACTS/'mobile.png'), full_page=True)
    page.goto('http://127.0.0.1:3000/#topic/1')
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.locator('.objective-row').first.locator('button').click()
    assert page.get_by_role('dialog').is_visible()
    page.keyboard.press('Escape')
    page.get_by_role('button', name='Add objective', exact=False).click()
    page.locator('#new-objective-reference').fill('1.test')
    page.locator('#new-objective-text').fill('A synthetic requirement used only for testing.')
    page.get_by_role('button', name='Add objective', exact=True).click()
    expect(page.locator('.objective-list')).to_contain_text('A synthetic requirement used only for testing.')
    fixture_lines = ['Edexcel 9CH0 - SYNTHETIC TEST FIXTURE, not official content']
    for number in range(1, 20):
        fixture_lines += [f'Topic {number}: Test topic', f'{number}.1 understand this synthetic test requirement']
    stream = 'BT /F1 10 Tf 40 800 Td ' + ' 0 -14 Td '.join('(' + line + ') Tj' for line in fixture_lines) + ' ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>', b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>', f'<< /Length {len(stream)} >>\nstream\n{stream}\nendstream'.encode()]
    pdf = b'%PDF-1.4\n'
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n'
    xref = len(pdf)
    pdf += b'xref\n0 6\n0000000000 65535 f \n' + b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    pdf += f'trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()
    fixture = ARTIFACTS/'synthetic-spec.pdf'
    fixture.write_bytes(pdf)
    page.goto('http://127.0.0.1:3000/#sources')
    page.get_by_role('heading', name='Update carefully.').wait_for()
    page.locator('#pdf-file').set_input_files(fixture)
    expect(page.get_by_role('heading', name='19 candidate objectives')).to_be_visible()
    expect(page.locator('#import-dialog')).to_contain_text('Found content in 19 of 19 topics')
    page.locator('#confirm-pdf').check()
    page.get_by_role('button', name='Import draft checklist').click()
    expect(page.locator('.topic-card')).to_have_count(19)
    imported = json.loads(page.evaluate("localStorage.getItem('element-9ch0-v1')"))
    assert len([o for o in imported['objectives'] if o['category']=='content']) == 19
    assert all(not o['verified'] for o in imported['objectives'] if o['category']=='content')
    assert imported['practicals']['1']['complete'] is True
    assert len([o for o in imported['objectives'] if o['category']=='maths']) == 21
    page.goto('http://127.0.0.1:3000/#sources')
    page.get_by_role('button', name='Use official checklist', exact=False).first.click()
    page.get_by_role('button', name='Use official objectives', exact=True).click()
    upgraded = json.loads(page.evaluate("localStorage.getItem('element-9ch0-v1')"))
    assert len(upgraded['objectives']) == 596
    assert len(upgraded['previousChecklist']['objectives']) == len(imported['objectives'])
    assert upgraded['practicals']['1']['complete'] is True
    page.reload()
    expect(page.locator('.source-notice')).to_contain_text('Official 9CH0')
    with page.expect_download() as archived_download:
        page.get_by_role('button', name='Export previous checklist').click()
    archive = ARTIFACTS/'archived.json'
    archived_download.value.save_as(archive)
    assert len(json.loads(archive.read_text(encoding='utf-8'))['objectives']) == len(imported['objectives'])
    assert not errors, errors
    print(f'PASS: topic coverage, year/search/status filters, progress persistence, evidence escaping, source checks, revision scheduling, practical records, backup round trip, invalid input, mobile layout, manual objectives, actual PDF extraction and import. {len(backup["objectives"])} prompts.')
    browser.close()
