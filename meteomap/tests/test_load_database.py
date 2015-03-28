import unittest
from meteomap.load_database import get_generic, KeysParsingRule

class TestGetGeneric(unittest.TestCase):
    def test_get_generic(self):
        keys = [KeysParsingRule('a'), KeysParsingRule(['b', 'c'])]
        self.assertEqual(get_generic({'a': ['9.'], 'x': ['123']}, keys), 9.,)
        self.assertEqual(get_generic({'a': ['8.', '10'], 'x': ['123']}, keys), 9.,)
        self.assertEqual(get_generic({'b': ['8.', '10'], 'c': ['7']}, keys), 8.,)
        self.assertEqual(get_generic({'b': ['8.', '10']}, keys), None)
