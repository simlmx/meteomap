from numpy import sqrt, cos, sin, radians, arctan2

class City(object):
    """ abstraction of a city """
    def __init__(self, name, country, region, coords, modif_date, pop, feature):
        self.name = name
        self.country = country
        self.region = region
        self.coords = coords
        self.modif_date = modif_date
        self.pop = pop
        self.feature = feature

    def distance(self, other):
        return lat_lon_distance(
            self.coords[0],
            self.coords[1],
            other.coords[0],
            other.coords[1])

    def fast_distance(self, other):
        return lat_lon_fast_distance(
            self.coords[0],
            self.coords[1],
            other.coords[0],
            other.coords[1])

    def __str__(self):
        s = '{}, {}, {}\n'.format(self.name, self.region, self.country)
        for at, val in self.__dict__.items():
            s += ' ' + at + ': ' + str(val) + '\n'
        s = s[:-1]
        return s

    def __repr__(self):
        return '<%s>' % self

def lat_lon_distance(lat1, lon1, lat2, lon2):
    """ calculates the km distance between two points specified as their
        lat and lon coordinates
    """
    delta_lat = radians(lat1 - lat2)
    delta_lon = radians(lon1 - lon2)
    a = sin(delta_lat/2.)**2 + cos(radians(lat1)) \
        * cos(radians(lat2)) * sin(delta_lon/2.)**2
    c = 2 * arctan2(sqrt(a), sqrt(1-a))
    return c * 6371.

def lat_lon_fast_distance(lat1, lon1, lat2, lon2):
    """ faster approxmation the previous """
    x = radians(lon2 - lon1) * cos(0.5 * radians(lat2+lat1))
    y = radians(lat2 - lat1)
    return 6371. * sqrt(x**2 + y**2)

def distance(c1, c2):
    return c1.distance(c2)

def fast_distance(c1, c2):
    return c1.fast_distance(c2)
