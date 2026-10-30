"""Verify the actual Pages artifact beneath a repository subpath, without Python APIs."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    site = Path(folder) / 'A-level-Chem'
    shutil.copytree(ROOT / 'app', site)
    (site / 'deployment-config.js').write_text('window.ELEMENT_DEPLOYMENT = { staticHosting: true };\n')
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=folder))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            page = browser.new_page()
            errors, failed = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: failed.append(response.url) if response.status >= 400 else None)
            url = f'http://127.0.0.1:{server.server_port}/A-level-Chem/'
            page.goto(url)
            expect(page.locator('.source-notice')).to_contain_text('Official 9CH0')
            page.goto(url+'#topic/1')
            page.locator('[data-status]').first.select_option('learning')
            page.reload()
            expect(page.locator('[data-status]').first).to_have_value('learning')
            link = page.locator('.source-page').first.get_attribute('href')
            assert link.startswith('specification.pdf#page=')
            response = page.request.get(url+'specification.pdf')
            assert response.status == 200 and response.body().startswith(b'%PDF-')
            page.goto(url+'#sources')
            expect(page.locator('main')).to_contain_text('PDF upload is unavailable on this hosted website')
            expect(page.locator('[data-action="import-pdf"]')).to_have_count(0)
            with page.expect_download() as downloaded:
                page.get_by_role('button', name='Export backup', exact=True).click()
            backup = Path(folder)/'backup.json'
            downloaded.value.save_as(backup)
            page.locator('#backup-file').set_input_files(backup)
            page.get_by_role('button', name='Replace with backup').click()
            expect(page.locator('#toast')).to_contain_text('Backup restored')
            assert not errors, errors
            assert not [u for u in failed if not u.endswith('favicon.ico')], failed
            browser.close()
            print('PASS: Pages subpath, official data, persistence, PDF links, hosted-mode UI and backup round trip.')
    finally:
        server.shutdown()
        server.server_close()
