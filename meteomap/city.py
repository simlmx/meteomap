import math

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

    def __str__(self):
        s = '{}, {}, {}\n'.format(self.name, self.region, self.country)
        for at, val in self.__dict__.items():
            s += ' ' + at + ': ' + str(val) + '\n'
        return s

    def __repr__(self):
        return '<%s>' % self

def lat_lon_distance(lat1, lon1, lat2, lon2):
    """ calculates the km distance between two points specified as their
        lat and lon coordinates
    """
    rad = math.pi / 180.
    delta_lat = (lat1 - lat2) * rad
    delta_lon = (lon1 - lon2) * rad
    a = math.sin(delta_lat/2.)**2 + math.cos(lat1*rad) \
        * math.cos(lat2*rad) * math.sin(delta_lon/2.)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return c * 6371.

def distance(c1, c2):
    return c1.distance(c2)
