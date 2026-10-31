"""Local-only, atomic work records and human-browsable topic image libraries."""
import base64
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import threading
import uuid

LOCK=threading.RLock()
ID=re.compile(r'^[A-Za-z0-9_-]{1,100}$')

class StoreError(ValueError):pass

def safe_id(value):
    if not isinstance(value,str) or not ID.fullmatch(value):raise StoreError('Invalid work record ID.')
    return value

def image_bytes(url):
    if not isinstance(url,str) or len(url)>4*1024*1024 or not url.startswith(('data:image/jpeg;base64,','data:image/png;base64,')):
        raise StoreError('Invalid saved image.')
    try:raw=base64.b64decode(url.split(',',1)[1],validate=True)
    except (ValueError,TypeError):raise StoreError('Invalid image encoding.') from None
    ext='jpg' if url.startswith('data:image/jpeg;') else 'png'
    if not raw.startswith(b'\xff\xd8\xff' if ext=='jpg' else b'\x89PNG\r\n\x1a\n'):raise StoreError('Image content does not match its format.')
    return raw,ext

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('wb') as f:
            f.write(data);f.flush()
            import os
            os.fsync(f.fileno())
        temp.replace(path)
    finally:
        if temp.exists():temp.unlink()

class WorkStore:
    def __init__(self,root):
        self.root=Path(root).expanduser().resolve()
        self.root.mkdir(parents=True,exist_ok=True)
    def path(self,*parts):
        path=self.root.joinpath(*parts)
        # Refuse directory links escaping the selected study folder.
        if not path.resolve().is_relative_to(self.root):raise StoreError('Unsafe link in the study data folder.')
        return path
    def all(self):
        with LOCK:
            records=[]
            for path in self.path('uploads').glob('*/record.json'):
                if not path.resolve().is_relative_to(self.root):raise StoreError('Unsafe data-folder link.')
                try:records.append(json.loads(path.read_text(encoding='utf-8')))
                except (OSError,ValueError):raise StoreError('A saved record could not be read. Keep the data folder and restore a backup; no records were deleted.') from None
            return records
    def save(self,payload):
        if not isinstance(payload,dict):raise StoreError('Invalid save request.')
        s=deepcopy(payload.get('submission'));crops=payload.get('crops',[])
        if not isinstance(s,dict):raise StoreError('Missing submission.')
        sid=safe_id(s.get('id'))
        if not isinstance(s.get('pages'),list) or not 1<=len(s['pages'])<=6 or not isinstance(s.get('questions'),list) or len(s['questions'])>40:
            raise StoreError('Invalid work record.')
        pages={}
        for p in s['pages']:
            if not isinstance(p,dict):raise StoreError('Invalid page record.')
            pid=safe_id(p.get('id'))
            if pid in pages:raise StoreError('Duplicate page ID.')
            pages[pid]=image_bytes(p.get('dataUrl'))
        questions={}
        for q in s['questions']:
            if not isinstance(q,dict):raise StoreError('Invalid question record.')
            qid=safe_id(q.get('id'))
            if qid in questions:raise StoreError('Duplicate question ID.')
            if not isinstance(q.get('topics'),list) or any(not isinstance(t,dict) or type(t.get('topic')) is not int or not 1<=t['topic']<=19 for t in q['topics']):raise StoreError('Invalid question topic.')
            if not isinstance(q.get('regions'),list) or not 1<=len(q['regions'])<=12 or any(not isinstance(r,dict) or r.get('page_id') not in pages for r in q['regions']):raise StoreError('Invalid question regions.')
            questions[qid]=q
        if not isinstance(crops,list) or len(crops)>480:raise StoreError('Invalid crop list.')
        assets={}
        for crop in crops:
            if not isinstance(crop,dict):raise StoreError('Invalid crop record.')
            qid=safe_id(crop.get('questionId'));index=crop.get('index')
            if qid not in questions or type(index) is not int or not 0<=index<len(questions[qid]['regions']):raise StoreError('Invalid crop reference.')
            if (qid,index) in assets:raise StoreError('Duplicate crop.')
            assets[qid,index]=image_bytes(crop.get('dataUrl'))
        expected={(qid,i) for qid,q in questions.items() for i in range(len(q['regions']))}
        if set(assets)!=expected:raise StoreError('Crop images are incomplete. Save again with all question regions.')
        with LOCK:
            old_paths=set()
            previous=self.path('uploads',sid,'record.json')
            if previous.exists():
                old=json.loads(previous.read_text(encoding='utf-8'))
                for q in old.get('questions',[]):
                    qid=safe_id(q.get('id'))
                    for t in q.get('topics',[]):
                        number=t.get('topic')
                        if type(number) is not int or not 1<=number<=19:raise StoreError('Invalid previous topic record; preserve the folder and restore a backup.')
                        folder=self.path('topics',f'topic-{number:02d}',sid)
                        old_paths.add(folder/(qid+'.json'))
                        for i in range(min(len(q.get('regions',[])),12)):
                            for ext in ['jpg','png']:old_paths.add(folder/f'{qid}-crop-{i+1:02d}.{ext}')
            new_paths=set()
            for pid,(raw,ext) in pages.items():atomic(self.path('uploads',sid,'originals',pid+'.'+ext),raw)
            topic_paths={}
            for qid,q in questions.items():
                for t in q['topics']:
                    number=t['topic'];folder=self.path('topics',f'topic-{number:02d}',sid)
                    new_paths.add(folder/(qid+'.json'))
                    atomic(folder/(qid+'.json'),json.dumps(q,ensure_ascii=False,indent=2).encode('utf-8'))
                    for i in range(len(q['regions'])):
                        raw,ext=assets[qid,i];name=f'{qid}-crop-{i+1:02d}.{ext}'
                        path=folder/name;new_paths.add(path);atomic(path,raw)
                        topic_paths.setdefault(qid,[]).append(str(path.relative_to(self.root)))
            # This atomic primary record is the source of truth; derived topic files are regenerable.
            atomic(self.path('uploads',sid,'record.json'),json.dumps(s,ensure_ascii=False,indent=2).encode('utf-8'))
            for path in old_paths-new_paths:
                if path.is_file():path.unlink()
            return {'saved':True,'dataDir':str(self.root),'crops':topic_paths}
    def delete(self,sid):
        safe_id(sid)
        with LOCK:
            folder=self.path('uploads',sid)
            if folder.exists():shutil.rmtree(folder)
            for number in range(1,20):
                folder=self.path('topics',f'topic-{number:02d}',sid)
                if folder.exists():shutil.rmtree(folder)
        return {'deleted':True}
