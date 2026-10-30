"""Dependency-free local app server. Study data stays in the browser."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import tempfile

ROOT = Path(__file__).parent / 'app'
MAX_PDF = 15 * 1024 * 1024


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
        super().end_headers()

    def respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != '/api/import-spec':
            return self.respond(404, {'error': 'Not found'})
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
    parser.add_argument('--port', type=int, default=3000)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()
    print(f'Chemistry tracker listening on port {args.port}', flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
