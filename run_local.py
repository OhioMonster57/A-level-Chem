"""Start Element privately on this computer; never writes API keys to disk."""
import argparse
import getpass
import os
from pathlib import Path
import secrets
import threading
import warnings
import webbrowser
from http.server import ThreadingHTTPServer


def main():
    parser = argparse.ArgumentParser(description='Run your chemistry tracker locally, with a private API-key prompt.')
    parser.add_argument('--port', type=int, default=3000)
    parser.add_argument('--data-dir', default=str(Path.home() / 'Documents' / 'Element-Chemistry'), help='Folder for local photos, crops and marking history.')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('Choose a port between 1 and 65535.')
    key = os.environ.get('STUDY_AI_API_KEY') or os.environ.get('OPENAI_API_KEY')
    if not key:
        print('Element Chemistry — local edition\n')
        print('Paste your OpenAI API key at the hidden prompt below.')
        print('It is held in this running process only, not saved in a file or sent to GitHub.')
        print('Photos are sent to OpenAI only when you request marking. Separate API billing applies.\n')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', getpass.GetPassWarning)
                key = getpass.getpass('OpenAI API key (hidden; Enter to study without AI): ').strip()
        except (getpass.GetPassWarning, EOFError):
            print('A secure hidden prompt is unavailable. Run this script in a terminal, or supply STUDY_AI_API_KEY securely in the process environment.')
            return 1
        except KeyboardInterrupt:
            print('\nCancelled.')
            return 0
    if key:
        os.environ['STUDY_AI_API_KEY'] = key
    os.environ['STUDY_ACCESS_TOKEN'] = secrets.token_urlsafe(32)
    os.environ['STUDY_LOCAL_MODE'] = '1'
    os.environ['STUDY_DATA_DIR'] = str(Path(args.data_dir).expanduser().resolve())
    os.environ['STUDY_ALLOWED_ORIGIN'] = f'http://127.0.0.1:{args.port}'
    try:
        from work_store import WorkStore, atomic
        store = WorkStore(os.environ['STUDY_DATA_DIR'])
        probe = store.path('.write-check')
        atomic(probe, b'local storage check')
        probe.unlink()
    except OSError:
        print('Cannot write your study folder. Run again with --data-dir pointing to a writable folder.')
        return 1
    from server import Handler
    try:
        httpd = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError:
        print(f'Could not open port {args.port}. Close an existing tracker server, or run with --port 3001. A different port has separate browser history.')
        return 1
    address = f'http://127.0.0.1:{args.port}/#work'
    print(f'\nOpen {address}')
    print('Study files: '+os.environ['STUDY_DATA_DIR'])
    print('Keep this terminal open. Press Ctrl+C to stop.')
    if not key:
        print('No API key supplied: the checklist and stored work are available; automatic marking is disabled.')
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(address)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nTracker stopped.')
    finally:
        httpd.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
