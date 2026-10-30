import unittest
from server import extract_objectives


class SpecificationExtractionTests(unittest.TestCase):
    def test_preserves_subpoints_and_separates_topics(self):
        text = '''Pearson Edexcel 9CH0
Topic 1: Atomic Structure and the Periodic Table
Students should:
1.1 know the structure of an atom in terms of
    a protons
    b neutrons
    c electrons
1.2 understand the terms atomic number and mass number
Pearson Edexcel Level 3 Advanced GCE in Chemistry
12
Topic 2: Bonding and Structure
2.1 understand ionic bonding as electrostatic attraction
    between oppositely charged ions
'''
        rows = extract_objectives(text)
        self.assertEqual([o['reference'] for o in rows], ['1.1', '1.2', '2.1'])
        self.assertIn('c electrons', rows[0]['text'])
        self.assertNotIn('Pearson', rows[1]['text'])
        self.assertIn('between oppositely charged ions', rows[2]['text'])
        self.assertTrue(all(o['verified'] is False for o in rows))

    def test_rejects_mismatched_topic_numbers_and_contents_lines(self):
        text = '''Topic 3: Redox I
3.1 understand oxidation and reduction
4.1 understand an unrelated topic
Topic 4: Inorganic chemistry .............. 21
Topic 4: Inorganic chemistry
4.1 understand chemical trends in a group
'''
        rows = extract_objectives(text)
        self.assertEqual([r['reference'] for r in rows], ['3.1', '4.1'])
        self.assertEqual(rows[0]['text'], 'understand oxidation and reduction')

    def test_no_invented_objectives_for_empty_text(self):
        self.assertEqual(extract_objectives('9CH0\nContents\nTopic 1: Atomic structure\n'), [])


if __name__ == '__main__':
    unittest.main()
