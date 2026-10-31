"""Dependency-free local app server. Study data stays in the browser."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import hashlib
import json
import hmac
import os
import re
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlsplit
import grading

ROOT = Path(__file__).parent / 'app'
MAX_PDF = 15 * 1024 * 1024
GRADE_LOCK = threading.Lock()
GRADE_TIMES = []


def extract_objectives(text):
    """Conservative candidate extraction; users must review against the PDF."""
    topics = {}
    current = None
    objective = None
    for raw in text.splitlines():
        line = raw.strip()
        heading = re.match(r'^Topic\s+(\d{1,2})\s*[:–-]\s*(.*)', line, re.I)
        if heading:
            number = int(heading[1])
            current = number if 1 <= number <= 19 else None
            objective = None
            if current:
                topics.setdefault(current, [])
            continue
        if current is None or not line:
            continue
        if re.match(r'^(?:Assessment (?:information|overview|objectives)|Appendix|Science Practical Endorsement)', line, re.I):
            current = None
            objective = None
            continue
        if re.match(r'^CORE PRACTICAL|^Topic\s+\d+[A-Z]:', line, re.I):
            objective = None
            continue
        if re.search(r'Pearson Edexcel|^Specification\s*[–-]|^©|^Issue\s+\d|^Students (?:should|will)|^Content overview', line, re.I) or line.isdigit():
            continue
        match = re.match(r'^(?:(\d{1,2})\.(\d{1,2})|(?:([0-9]{1,2})[.)]?))\s+(.+)', line)
        if match:
            if match[1] and int(match[1]) != current:
                objective = None
                continue
            number = int(match[2] or match[3])
            content = match[4]
            # Contents tables and page references are not learning objectives.
            if re.search(r'\.{3,}|\s{3,}\d+$', raw) or len(content) < 8:
                objective = None
                continue
            objective = {'id': f'spec-{current}-{number}', 'topic': current,
                         'reference': f'{current}.{number}', 'text': content,
                         'category': 'content', 'source': 'pdf', 'verified': False}
            if not any(x['id'] == objective['id'] for x in topics[current]):
                topics[current].append(objective)
            else:
                objective = None
        elif objective:
            if re.match(r'^(?:Topic\s|Assessment|Appendix|Qualification|Science Practical)', line, re.I):
                objective = None
            else:
                objective['text'] += ' ' + line
    return [item for key in sorted(topics) for item in topics[key]]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        origin = self.headers.get('Origin', '')
        if origin and self.origin_allowed():
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        super().end_headers()

    def respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def origin_allowed(self):
        origin = self.headers.get('Origin', '')
        if not origin:
            return True
        allowed = {s.strip() for s in os.environ.get('STUDY_ALLOWED_ORIGIN', '').split(',') if s.strip()}
        parsed = urlsplit(origin)
        return origin in allowed or (parsed.scheme in ('http', 'https') and parsed.netloc == self.headers.get('Host'))

    def do_OPTIONS(self):
        if not self.origin_allowed():
            return self.respond(403, {'error': 'This website origin is not allowed by the marking backend.'})
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/local-session':
            host = self.headers.get('Host', '')
            expected = f'127.0.0.1:{self.server.server_port}'
            if (os.environ.get('STUDY_LOCAL_MODE') != '1'
                    or self.client_address[0] != '127.0.0.1'
                    or host != expected
                    or self.headers.get('X-Element-Local') != '1'
                    or (self.headers.get('Origin') and self.headers['Origin'] != 'http://'+expected)):
                return self.respond(403, {'error': 'Local automatic connection is unavailable.'})
            return self.respond(200, {'accessToken': os.environ.get('STUDY_ACCESS_TOKEN', ''), 'configured': bool(grading.ai_key())})
        if self.path == '/api/health':
            if not self.origin_allowed():
                return self.respond(403, {'error': 'Website origin not allowed.'})
            provided = self.headers.get('Authorization', '')
            expected = os.environ.get('STUDY_ACCESS_TOKEN', '')
            if provided and (not expected or not hmac.compare_digest(provided.encode(), ('Bearer '+expected).encode())):
                return self.respond(401, {'error': 'The backend access token is incorrect.'})
            return self.respond(200, {'configured': bool(grading.ai_key() and os.environ.get('STUDY_ACCESS_TOKEN')),
                                      'model': os.environ.get('STUDY_AI_MODEL', 'gpt-4.1'),
                                      'rubric_version': grading.RUBRIC_VERSION})
        return super().do_GET()

    def mark_work(self):
        if not self.origin_allowed():
            return self.respond(403, {'error': 'Add this website origin to STUDY_ALLOWED_ORIGIN on your backend.'})
        token = os.environ.get('STUDY_ACCESS_TOKEN', '')
        if not token or not grading.ai_key():
            return self.respond(503, {'error': 'Marking is not configured. Set STUDY_AI_API_KEY and STUDY_ACCESS_TOKEN securely on the backend.'})
        if not hmac.compare_digest(self.headers.get('Authorization', '').encode(), ('Bearer '+token).encode()):
            return self.respond(401, {'error': 'The backend access token is missing or incorrect. Reconnect in Marked work settings.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.respond(400, {'error': 'Invalid upload size.'})
        if not 0 < size <= grading.MAX_BODY:
            return self.respond(413, {'error': 'The marking upload is too large. Use fewer or smaller photos.'})
        if not GRADE_LOCK.acquire(blocking=False):
            return self.respond(429, {'error': 'Another marking session is running. Please wait before retrying.'})
        try:
            now = time.monotonic()
            GRADE_TIMES[:] = [t for t in GRADE_TIMES if now-t < 3600]
            if len(GRADE_TIMES) >= 12:
                return self.respond(429, {'error': 'This backend has reached its limit of 12 marking sessions per hour. Try again later.'})
            payload = json.loads(self.rfile.read(size))
            grading.validate_pages(payload)
            GRADE_TIMES.append(now)
            result = grading.grade(payload)
            return self.respond(200, result)
        except grading.GradingError as error:
            return self.respond(error.status, {'error': str(error)})
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self.respond(400, {'error': 'The marking request was not valid JSON.'})
        except Exception:
            return self.respond(502, {'error': 'Marking could not be completed. Your saved photos and history are unchanged.'})
        finally:
            GRADE_LOCK.release()

    def do_POST(self):
        if self.path == '/api/mark-work':
            return self.mark_work()
        if self.path != '/api/import-spec':
            return self.respond(404, {'error': 'Not found'})
        if not self.origin_allowed():
            return self.respond(403, {'error': 'Website origin not allowed.'})
        token = os.environ.get('STUDY_ACCESS_TOKEN', '')
        if token and not hmac.compare_digest(self.headers.get('Authorization', '').encode(), ('Bearer '+token).encode()):
            return self.respond(401, {'error': 'Connect the backend access token before importing a PDF on this server.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_PDF:
                return self.respond(413, {'error': 'Choose a PDF smaller than 15 MB.'})
            pdf = self.rfile.read(size)
            if not pdf.startswith(b'%PDF-'):
                return self.respond(400, {'error': 'This file is not a PDF.'})
            known = json.loads((ROOT / 'official-data.json').read_text())
            if hashlib.sha256(pdf).hexdigest() == known['metadata']['sha256']:
                return self.respond(200, {'knownSpecification': True,
                                         'metadata': known['metadata']})
            with tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / 'spec.pdf'
                source.write_bytes(pdf)
                result = subprocess.run(['pdftotext', '-layout', str(source), '-'],
                                        capture_output=True, timeout=25, check=True)
            text = result.stdout.decode('utf-8', errors='replace')
            if not re.search(r'9CH0', text, re.I):
                return self.respond(400, {'error': 'No 9CH0 qualification code found. Please use the UK Edexcel A level Chemistry specification.'})
            objectives = extract_objectives(text)
            if not objectives:
                return self.respond(422, {'error': 'No numbered objectives could be extracted. The PDF layout may be unsupported. Your existing checklist is unchanged.'})
            return self.respond(200, {'objectives': objectives,
                                     'topics': sorted(set(x['topic'] for x in objectives)),
                                     'warning': 'Extraction is a draft. Compare every topic and sub-point with the original PDF; practical and maths appendices require separate review.'})
        except FileNotFoundError:
            return self.respond(503, {'error': 'PDF import needs pdftotext (poppler-utils) on the server.'})
        except (ValueError, subprocess.SubprocessError):
            return self.respond(422, {'error': 'The PDF could not be read. Try an unencrypted, text-based specification PDF.'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', '3000')))
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()
    print(f'Chemistry tracker listening on port {args.port}', flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
