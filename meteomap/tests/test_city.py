import unittest
from numpy import array
from numpy.testing import assert_allclose
from meteomap.city import City, distance, fast_distance, lat_lon_fast_distance

class TestCity(unittest.TestCase):
    def test_city(self):
        c1 = City('montreal', 'b', 'c', (45., 73.), 'd', 123, 'e')
        c2 = City('quebec', 'b', 'c', (46., 71.), 'd', 123, 'e')
        self.assertAlmostEqual(distance(c1, c2), 191.5, 1)
        self.assertAlmostEqual(fast_distance(c1, c2), 191.5, 1)

    def test_distance_vector(self):
        # [mtl, qc, qc]
        lat = array([45., 46., 46.])
        lon = array([73., 71., 71.])
        # [[mtl-mtl, mtl-qc, mtl-qc],
        #  [qc-mtl, qc-qc, qc-qc],
        #  [qc-mtl, qc-qc, qc-qc]]
        ds = lat_lon_fast_distance(lat.reshape(-1,1), lon.reshape(-1,1),
                           lat.reshape(1,-1), lon.reshape(1,-1))
        mtl_qc = 191.5
        expected = array([[0, mtl_qc, mtl_qc], [mtl_qc, 0, 0], [mtl_qc, 0, 0]])
        assert_allclose(ds, expected, 0, 0.05)
