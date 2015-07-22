import unittest
from meteomap.city import City, distance

class TestCity(unittest.TestCase):
    def test_city(self):
        c1 = City('montreal', 'b', 'c', (45., 73.), 'd', 123, 'e')
        c2 = City('quebec', 'b', 'c', (46., 71.), 'd', 123, 'e')
        self.assertAlmostEqual(distance(c1, c2), 191.5, 1)
