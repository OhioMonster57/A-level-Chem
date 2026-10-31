"""Test the extracted local distribution with a fake key; no provider calls."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from zipfile import ZipFile
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_local_package import build

with tempfile.TemporaryDirectory() as folder:
    folder=Path(folder)
    archive=build(folder/'local.zip')
    with ZipFile(archive) as z:
        assert not any('.env' in name or '.git/' in name for name in z.namelist())
        z.extractall(folder)
    app=folder/'Element-Chemistry'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env={**os.environ,'STUDY_AI_API_KEY':'local-smoke-test-not-a-real-key','PYTHONUNBUFFERED':'1'}
    process=subprocess.Popen([sys.executable,'run_local.py','--port',str(port),'--no-browser'],cwd=app,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    try:
        url=f'http://127.0.0.1:{port}'
        for _ in range(50):
            try:
                with urllib.request.urlopen(url+'/api/health',timeout=1) as response:
                    assert response.status==200
                break
            except OSError:
                if process.poll() is not None:raise AssertionError(process.stdout.read())
                time.sleep(.1)
        else:raise AssertionError('Local launcher did not start')
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page();errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url+'/#work')
            expect(page.get_by_role('button',name='Upload completed work',exact=False)).to_be_enabled()
            expect(page.locator('main')).to_contain_text('Backend connection saved for this browser session')
            assert page.evaluate("sessionStorage.getItem('element-marking-session').length")>=40
            assert page.evaluate("localStorage.getItem('element-marking-backend')")==url
            assert 'local-smoke-test-not-a-real-key' not in page.content()
            assert 'local-smoke-test-not-a-real-key' not in page.evaluate('JSON.stringify(sessionStorage)')
            page.reload()
            expect(page.locator('main')).to_contain_text('Backend connection saved for this browser session')
            assert not errors,errors
            browser.close()
    finally:
        process.terminate()
        output=process.communicate(timeout=10)[0]
        assert 'local-smoke-test-not-a-real-key' not in output
    print('PASS: extracted ZIP, local launcher, automatic loopback connection, reload and API-key non-disclosure. No real AI calls.')
