import unittest
from meteomap.add_wiki_data_to_dump import get_first_number, get_second_number

class TestAddWikiData(unittest.TestCase):
    def test_parsing_fn(self):
        self.assertEqual(get_first_number('10.1 (12.3)'), 10.1)
        self.assertEqual(get_first_number('1,000.1 (12.3)'), 1000.1)
        self.assertEqual(get_second_number('10.1 (1,200.3)'), 1200.3)
        self.assertEqual(get_second_number('1,000.1 (12.3)'), 12.3)
        self.assertEqual(get_first_number('1 (2)'), 1.)
        self.assertEqual(get_second_number('1 (2)'), 2.)
