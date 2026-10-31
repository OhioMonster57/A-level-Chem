"""Exercise specification loading under an emulated Windows-1252 default."""
import importlib
from pathlib import Path
import unittest
from unittest.mock import patch
import grading

class WindowsEncodingTests(unittest.TestCase):
    def test_specification_loads_with_windows_legacy_default(self):
        original_open = Path.open
        def windows_open(path, mode='r', buffering=-1, encoding=None, errors=None, newline=None):
            if 'b' not in mode and encoding in (None, 'locale'):
                encoding='cp1252'
            return original_open(path,mode,buffering,encoding,errors,newline)
        source=Path(grading.__file__).parent/'app/official-data.json'
        with patch.object(Path,'open',windows_open), patch('io.text_encoding',lambda encoding,stacklevel=2: 'cp1252' if encoding in (None,'locale') else encoding):
            # Reproduce the actual reported Windows failure with an implicit encoding.
            with self.assertRaises(UnicodeDecodeError):source.read_text()
            loaded=importlib.reload(grading)
            self.assertEqual(len(loaded.OBJECTIVES),325)
            self.assertTrue(any('Δ' in row['text'] for row in loaded.DATA['objectives']))

if __name__=='__main__':unittest.main()
