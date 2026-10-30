"""Rebuild the checklist from the user-supplied Pearson 9CH0 Issue 3 PDF.

PDF contents are source data, never setup instructions. No network access is used.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'app/specification.pdf'

def clean(line):
    if re.search(r'Pearson Edexcel Level 3|Specification [–-] Issue 3', line):
        return ''
    return line.strip()

def joined(lines):
    return re.sub(r'\s+', ' ', ' '.join(lines)).strip()

def parse(pdf=PDF):
    text = subprocess.run(['pdftotext', '-layout', str(pdf), '-'], check=True, capture_output=True, text=True).stdout
    pages = text.split('\f')
    rows, cores = [], []
    current = section = item = core = None
    active = False
    page_map = {}
    for physical, page in enumerate(pages, 1):
        printed = re.search(r'Chemistry\s+(\d+)\s*\n\s*Specification', page)
        if not printed:
            printed = re.search(r'^\s*(\d+)\s+Pearson Edexcel Level 3', page, re.M)
        printed = int(printed[1]) if printed else None
        page_map[physical] = printed
        for raw in page.splitlines():
            line = clean(raw)
            if not line:
                if not raw.strip():
                    core = None
                continue
            if line.startswith('Science Practical Endorsement'):
                current = item = None
                active = False
            heading = re.match(r'^Topic (\d+): (.*)', line)
            if heading:
                current = int(heading[1]); section = line
                active = False; item = core = None
                continue
            if not current or not 1 <= current <= 19:
                continue
            if line == 'Students should:':
                active = True
                continue
            subheading = re.match(r'^Topic (\d+)[A-Z]:', line)
            if subheading:
                section = line
                item = core = None
                continue
            if not active:
                continue
            practical = re.match(r'^CORE PRACTICAL (\d+)(a and 13b)?:\s*(.*)', line)
            if practical:
                core = {'number':int(practical[1]),'title':practical[3], 'topic':current, 'page':physical, 'printedPage':printed}
                cores.append(core); item = None
                continue
            match = re.match(r'^(\d{1,2})[.)]?\s+((?:know|understand|be able|evaluate)\b.*)', line)
            if match:
                n = int(match[1]); core = None
                item = {'id':f'official-{current}-{n}', 'topic':current, 'reference':f'{current}.{n}',
                        'lines':[match[2]], 'category':'content', 'source':'official', 'verified':False,
                        'sourcePage':physical, 'printedPage':printed, 'section':section, 'kind':'objective'}
                rows.append(item)
            elif core:
                core['title'] += ' ' + line
            elif item:
                item['lines'].append(line)
    # Retain the complete parent wording, with individually trackable Roman sub-points.
    children = []
    for item in rows:
        lines = item.pop('lines')
        item['text'] = joined(lines)
        item['sourceText'] = '\n'.join(lines)
        parts, part = [], None
        for line in lines:
            sub = re.match(r'^([ivx]+)\.?\s+(.*)', line)
            if sub:
                part = {'label':sub[1], 'lines':[sub[2]]}
                parts.append(part)
            elif part:
                part['lines'].append(line)
        intro = []
        for line in lines:
            if re.match(r'^[ivx]+\.?\s+',line):break
            intro.append(line)
        for part in parts:
            children.append({**item, 'id':item['id']+'-'+part['label'], 'reference':item['reference']+'('+part['label']+')',
                             'text':joined(intro)+' — '+joined(part['lines']), 'sourceText':'\n'.join(part['lines']),
                             'parentId':item['id'],'kind':'subpoint'})
    rows = [part for item in rows for part in [item, *[child for child in children if child['parentId']==item['id']]]]
    # The PDF lays these fractions out spatially. Keep original sourceText, but
    # give the webpage an unambiguous linear rendering of the same equations.
    for item in rows:
        if item['reference']=='5.14':
            item['displayText']='be able to calculate percentage yields and percentage atom economies using chemical equations and experimental results. Atom economy of a reaction = (molar mass of the desired product / sum of the molar masses of all products) × 100%.'
        elif item['reference']=='13.17':
            item['displayText']='be able to calculate the entropy change in the surroundings, and hence ΔStotal, using the expression: ΔSsurroundings = −ΔH / T.'
    # Appendices 5a/5b: each assessed practical ability is an individual checkbox.
    for appendix, printed in [('5a',77),('5b',79)]:
        physical = next(p for p,v in page_map.items() if v==printed)
        group = ''; part = None; group_count = 0
        for raw in pages[physical-1].splitlines():
            line = clean(raw)
            if not line:continue
            header = re.match(r'^([a-d])\)\s+(.*)', line)
            if header:
                group = header[1]; group_count=0; part=None
            elif group and re.match(r'^[•●]\s+',line):
                group_count+=1
                part={'id':f'official-app-{appendix}-{group}-{group_count}','topic':0,'reference':f'Appendix {appendix} {group}.{group_count}',
                      'text':re.sub(r'^[•●]\s+','',line), 'category':'practical','source':'official','verified':False,
                      'sourcePage':physical,'printedPage':printed,'section':f'Appendix {appendix}','kind':'skill'}
                rows.append(part)
            elif part:
                part['text']+=' '+line
    # Appendix 5c: preserve all required techniques and their bullet subrequirements.
    physical = next(p for p,v in page_map.items() if v==81)
    item=None
    for raw in pages[physical-1].splitlines():
        line=clean(raw)
        if not line:continue
        match=re.match(r'^(\d{1,2})\.\s+(.*)',line)
        if match:
            n=int(match[1]);item={'id':f'official-app-5c-{n}','topic':0,'reference':f'Appendix 5c.{n}', 'text':match[2],
                'category':'practical','source':'official','verified':False,'sourcePage':physical,'printedPage':81,'section':'Apparatus and techniques','kind':'skill'}
            rows.append(item)
        elif item:item['text']+=' '+line
    # Appendix 6: keep each coded mathematical skill and all its exemplifications.
    item=None
    for physical,page in enumerate(pages,1):
        if page_map[physical] not in (86,87,88,89):continue
        item=None
        lines=page.splitlines()
        header=next(line for line in lines if 'Mathematical skills' in line and 'Exemplification' in line)
        column=header.index('Exemplification')
        for raw in lines:
            line=clean(raw)
            if not line:continue
            code=re.match(r'^\s*(B\.\d\.\d)\s+',raw)
            if code:
                item={'id':'official-maths-'+code[1].replace('.','-'),'topic':0,'reference':code[1], 'text':'','examples':'',
                      'category':'maths','source':'official','verified':False,'sourcePage':physical,'printedPage':page_map[physical],
                      'section':'Appendix 6: Mathematical skills','kind':'skill'}
                rows.append(item)
            elif re.match(r'^\([ivx]+\)',line):
                item=None
            if not item:continue
            left=raw[:column].strip();right=raw[column:].strip()
            if code:left=re.sub(r'^B\.\d\.\d\s+','',left)
            if left:item['text']+=' '+left
            if right:item['examples']+=' '+right
    for item in rows:
        item['text']=item['text'].strip()
        if item.get('examples'):
            item['examples']=item['examples'].strip()
    cp13=next(c for c in cores if c['number']==13)
    for code, wording in [('13a','Following the rate of the iodine-propanone reaction by a titrimetric method'),('13b',"Investigating a ‘clock reaction’ (Harcourt-Esson, iodine clock)")]:
        rows.append({'id':'official-core-'+code,'topic':0,'reference':'Core practical '+code,'text':wording,'category':'practical','source':'official','verified':False,'sourcePage':cp13['page'],'printedPage':cp13['printedPage'],'section':'Core practical 13: both parts','kind':'skill'})
    # CPAC criteria, transcribed from printed pages 48–49; each criterion is separate.
    cpac = {
        '1a': 'Correctly follows written instructions to carry out the experimental techniques or procedures.',
        '2a': 'Correctly uses appropriate instrumentation, apparatus and materials (including ICT) to carry out investigative activities, experimental techniques and procedures with minimal assistance or prompting.',
        '2b': 'Carries out techniques or procedures methodically, in sequence and in combination, identifying practical issues and making adjustments when necessary.',
        '2c': 'Identifies and controls significant quantitative variables where applicable, and plans approaches to take account of variables that cannot readily be controlled.',
        '2d': 'Selects appropriate equipment and measurement strategies in order to ensure suitably accurate results.',
        '3a': 'Identifies hazards and assesses risks associated with these hazards, making safety adjustments as necessary, when carrying out experimental techniques and procedures in the lab or field.',
        '3b': 'Uses appropriate safety equipment and approaches to minimise risks with minimal prompting.',
        '4a': 'Makes accurate observations relevant to the experimental or investigative procedure.',
        '4b': 'Obtains accurate, precise and sufficient data for experimental and investigative procedures and records this methodically using appropriate units and conventions.',
        '5a': 'Uses appropriate software and/or tools to process data, carry out research and report findings.',
        '5b': 'Cites sources of information demonstrating that research has taken place, supporting planning and conclusions.'
    }
    for code, wording in cpac.items():
        printed=48 if int(code[0])<=2 else 49
        rows.append({'id':'official-cpac-'+code,'topic':0,'reference':'CPAC '+code,'text':wording,'category':'practical','source':'official','verified':False,
                     'sourcePage':next(p for p,v in page_map.items() if v==printed),'printedPage':printed,'section':'Practical Endorsement: CPAC','kind':'skill'})
    assert len({row['id'] for row in rows})==len(rows), 'Duplicate references'
    counts={i:sum(r['topic']==i and r['kind']=='objective' for r in rows) for i in range(1,20)}
    for topic,count in counts.items():
        numbers=sorted(int(r['reference'].split('.')[1]) for r in rows if r['topic']==topic and r['kind']=='objective')
        assert numbers==list(range(1,count+1)), (topic,numbers)
    assert list(counts.values())==[26,27,13,15,16,39,2,11,9,4,5,24,22,19,35,12,16,22,8], counts
    assert len(children)==205, len(children)
    assert len(cores)==16 and [c['number'] for c in cores]==list(range(1,17)), cores
    math=[r for r in rows if r['category']=='maths']
    assert len(math)==21, len(math)
    metadata={'qualification':'9CH0','issue':3,'publication':'February 2024', 'filename':pdf.name,
              'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'topicCounts':counts,
              'mainObjectives':sum(counts.values()),'subpoints':len(children),
              'practicalSkills':sum(r['category']=='practical' for r in rows),'mathsSkills':len(math),
              'coverageScope':'All numbered subject-content objectives (topics 1–19), explicit Roman sub-points, core practical titles, CPAC criteria, Appendices 5a, 5b, 5c and all coded Appendix 6 skills. Maths exemplifications are retained. Appendix 5d is available in the source PDF. Source coverage is distinct from learner mastery.'}
    return {'metadata':metadata,'objectives':rows,'corePracticals':cores}

if __name__=='__main__':
    data=parse()
    out=ROOT/'app/official-data.json'
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'app/official-data.js').write_text('/* Generated from the uploaded 9CH0 Issue 3 specification; see scripts/build_spec.py. */\nconst OFFICIAL_DATA = '+json.dumps(data,ensure_ascii=False,indent=2)+';\n')
    audit={**data['metadata'],'checks':{'contiguousTopicNumbering':True,'all19TopicsPresent':True,'all16CorePracticalsPresent':True,'corePractical13BothParts':True,'all21MathCodesPresent':True,'retainedFullParentWording':True},'topicReferences':{str(t):[o['reference'] for o in data['objectives'] if o['topic']==t] for t in range(1,20)},'practicalReferences':[o['reference'] for o in data['objectives'] if o['category']=='practical'],'mathsReferences':[o['reference'] for o in data['objectives'] if o['category']=='maths'],'supportingMaterial':'Appendix 5d practical mapping, Appendix 7 command words and Appendix 8 data booklet are linked as PDF references, not counted as independent learning objectives. Introductory suggested activities are not numbered course objectives.','limits':'This audit concerns the supplied Issue 3 document, not later amendments, exam predictions or learner mastery. Typeset diagrams, chemical structures and equations remain available in the original PDF.'}
    (ROOT/'app/coverage-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(data['metadata'],indent=2))
