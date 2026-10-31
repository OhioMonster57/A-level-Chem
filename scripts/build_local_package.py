"""Build a local-only distribution from an explicit, credential-free file list."""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
FILES=['run_local.py','server.py','grading.py','START-WINDOWS.cmd','START-MAC.command','LOCAL-START-HERE.md',
       'app/index.html','app/style.css','app/app.js','app/work.js','app/data.js','app/official-data.js',
       'app/official-data.json','app/coverage-audit.json','app/specification.pdf','app/deployment-config.js']

def build(output):
    with ZipFile(output,'w',ZIP_DEFLATED) as archive:
        for name in FILES:
            archive.write(ROOT/name,'Element-Chemistry/'+name)
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist())==len(FILES)
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='/workspace/element-chemistry-local.zip')
    args=parser.parse_args()
    print(build(Path(args.output)))
