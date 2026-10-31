"""Regression audit against the actual user-supplied specification fixture."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OfficialCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'app/official-data.json').read_text(encoding='utf-8'))
        cls.rows = cls.data['objectives']
        cls.by_ref = {o['reference']: o for o in cls.rows}
        cls.text = subprocess.run(['pdftotext', '-layout', str(ROOT / 'app/specification.pdf'), '-'],
                                  check=True, text=True, encoding='utf-8', capture_output=True).stdout

    def test_pdf_identity_and_all_topic_endpoints(self):
        self.assertEqual(hashlib.sha256((ROOT / 'app/specification.pdf').read_bytes()).hexdigest(),
                         'b01c2b0a26ef82215b56fd45dcd03668efe308890739dd3243ba59982ec36d35')
        expected = [26,27,13,15,16,39,2,11,9,4,5,24,22,19,35,12,16,22,8]
        main = [o for o in self.rows if o['kind'] == 'objective']
        self.assertEqual(len(main), 325)
        for topic, last in enumerate(expected, 1):
            self.assertEqual([r['reference'] for r in main if r['topic'] == topic],
                             [f'{topic}.{n}' for n in range(1, last+1)])
        # Count directly in the original content pages, independently of generated metadata.
        original = '\f'.join(self.text.split('\f')[16:54])
        numbered = re.findall(r'^\s*\d{1,2}[.)]?\s+(?:know|understand|be able|evaluate)\b', original, re.M)
        self.assertEqual(len(numbered), len(main))

    def test_previously_missed_points_and_conditions(self):
        self.assertIn('fill subshells singly', self.by_ref['1.20']['text'])  # no dot after 20 in PDF
        self.assertIn('evaluate data', self.by_ref['10.3']['text'])
        self.assertIn('Z = 36', self.by_ref['1.21(ii)']['text'])
        self.assertIn('Harcourt-Esson', self.by_ref['Core practical 13b']['text'])
        self.assertIn('Grignard', self.by_ref['18.20']['text'])
        for o in self.rows:
            self.assertNotIn('CORE PRACTICAL', o['text'])
            self.assertNotIn('Pearson Edexcel', o['text'])
            self.assertGreaterEqual(o['sourcePage'], 17)
            self.assertIs(o['verified'], False)
        self.assertEqual(self.by_ref['1.1']['sourcePage'], 17)
        self.assertEqual(self.by_ref['1.1']['printedPage'], 7)

    def test_subpoints_keep_parent_context_and_unique_ids(self):
        self.assertEqual(len(set(o['id'] for o in self.rows)), len(self.rows))
        children = [r for r in self.rows if r.get('parentId')]
        self.assertEqual(len(children), 205)
        by_id = {o['id']:o for o in self.rows}
        for child in children:
            parent = by_id[child['parentId']]
            self.assertEqual(child['topic'], parent['topic'])
            self.assertIn(child['sourceText'].splitlines()[0], parent['sourceText'])

    def test_appendices_and_practical_records(self):
        expected_math = ([f'B.0.{n}' for n in range(5)] + [f'B.1.{n}' for n in range(1,4)] +
                         [f'B.2.{n}' for n in range(1,6)] + [f'B.3.{n}' for n in range(1,6)] +
                         [f'B.4.{n}' for n in range(1,4)])
        maths = [o for o in self.rows if o['category']=='maths']
        self.assertEqual([r['reference'] for r in maths], expected_math)
        self.assertIn('mean titres', self.by_ref['B.1.2']['examples'])
        self.assertIn('chiral centres', self.by_ref['B.4.3']['examples'])
        for section,count in [('Appendix 5a',10),('Appendix 5b',10),('Apparatus and techniques',12),('Practical Endorsement: CPAC',11)]:
            self.assertEqual(sum(o['section']==section for o in self.rows), count)
        self.assertEqual([p['number'] for p in self.data['corePracticals']], list(range(1,17)))
        self.assertIn('aspirin', self.data['corePracticals'][-1]['title'])

    def test_readable_equations_retain_original_extraction(self):
        self.assertIn('−ΔH / T', self.by_ref['13.17']['displayText'])
        self.assertIn('∆H', self.by_ref['13.17']['sourceText'])
        self.assertIn('/ sum of the molar masses', self.by_ref['5.14']['displayText'])


if __name__ == '__main__':
    unittest.main()
