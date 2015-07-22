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
        rad = math.pi / 180.
        delta_lat = (self.coords[0] - other.coords[0]) * rad
        delta_lon = (self.coords[1] - other.coords[1]) * rad
        a = math.sin(delta_lat/2.)**2 + math.cos(self.coords[0]*rad) \
            * math.cos(other.coords[0]*rad) * math.sin(delta_lon/2.)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return c * 6371.

    def __str__(self):
        return '{}, {}, {}'.format(self.name, self.region, self.country)

    def __repr__(self):
        return '<%s>' % self

def distance(c1, c2):
    return c1.distance(c2)
