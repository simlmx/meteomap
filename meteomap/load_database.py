import pickle, argparse, sys, logging, math
from collections import defaultdict
from geoalchemy2.elements import WKTElement
from geoalchemy2 import Geometry
from sqlalchemy import desc, func, cast
from meteomap.utils import (open, session_scope, Timer, are_you_sure,
                            configure_logging)
from meteomap.tables import City, Stat, MonthlyStat
from meteomap.city import lat_lon_distance

logger = logging.getLogger(__name__)


def fill_cities(data, session):
    stats_dict = dict(session.query(Stat.code, Stat.id))
    timer = Timer(len(data))
    for city in data:
        geom = WKTElement('POINT({:.8f} {:.8f})'.format(
            city.coords[1], city.coords[0], srid=4326))

        city_db = City(
            location = geom,
            name = city.name,
            region = city.region,
            country = city.country,
            source = city.wiki_source,
            population = city.pop,
            country_rank = city.country_rank,
            region_rank = city.region_rank)
        session.add(city_db)
        # commit the cities so we can use them
        # I'm not sure this is the clean way to do it...
        session.commit()

        for code, month_stats in city.month_stats.items():
            if code not in stats_dict:
                continue
            for month_idx, value in enumerate(month_stats):
                ms = MonthlyStat(
                    month = month_idx,
                    city_id = city_db.id,
                    stat_id = stats_dict[code],
                    value = value)
                session.add(ms)
        timer.update()
    # for the last monthly stats
    session.commit()

class DistancesCache(object):
    def __init__(self, objects, distance_fn):
        self.timer = Timer(len(objects)**2 / 2)
        self.distance_fn = distance_fn
        self.objects = objects
        self._distances = defaultdict(dict)

    def get_distance(self, index1, index2):
        try:
            return self._distances[index1][index2]
        except KeyError:
            x = self._distances[index1][index2] = self.distance_fn(
                self.objects[index1], self.objects[index2])
            self.timer.update()
            return x

    def __call__(self, i1, i2):
        return self.get_distance(i1, i2)


def add_priority_index(session, fast_mode=False):
    """ decides the order in which the cities should be selected """
    cities = session.query(City,
                          func.ST_Y(cast(City.location, Geometry())),
                          func.ST_X(cast(City.location, Geometry()))) \
        .order_by(City.country_rank, City.region_rank, desc(City.population)) \
        .yield_per(1000).all()

    if fast_mode:
        logger.info('doing the fast version of priority index')
        for i,city in enumerate(cities):
            city[0].priority_index = i
        session.commit()
        return


    # FIXME prendre une distance approximative plus rapide à calculer
    # FIXME faire la distance sur la map ET NON sur le globe
    def distance_fn(tuple1, tuple2):
        _,lat1,lon1 = tuple1
        _,lat2,lon2 = tuple2
        return lat_lon_distance(lat1, lon1, lat2, lon2)

    indices = [0]
    indices_left = list(range(1,len(cities)))
    distances = DistancesCache(cities, distance_fn)
    while len(indices_left) > 0:
        # let's find the next city amongst the next candidates
        mean_dist = 0.
        mean_dist_sq = 0.
        std_dist = None
        max_dist = None
        max_dist_idx = None
        logger.debug('\nlooking for the next one')
        z = None
        for no_candidate, i_left in enumerate(indices_left):
            # find how close is the nearest neighbor for this city
            # we are looking for the city with the fartest nearest neighbor
            dist_nearest_neighbor = 1e9
            for i_chosen in indices:
                cur_dist = distances(i_left, i_chosen)
                if cur_dist < dist_nearest_neighbor:
                    dist_nearest_neighbor = cur_dist
            logger.debug('candidate %i has a city at %f', no_candidate,
                         dist_nearest_neighbor)

            if max_dist is None or dist_nearest_neighbor > max_dist:
                logger.debug('(new max)')
                max_dist = dist_nearest_neighbor
                max_dist_idx = no_candidate

            mean_dist = (mean_dist * no_candidate + dist_nearest_neighbor) \
                / (no_candidate + 1)
            mean_dist_sq = (mean_dist_sq * no_candidate
                            + dist_nearest_neighbor**2) \
                / (no_candidate + 1)
            logger.debug('updated mean: %f', mean_dist)

            if no_candidate > 0:
                std_dist = math.sqrt(mean_dist_sq - (mean_dist)**2) \
                    * (no_candidate + 1) / no_candidate  # correction for sample
                if std_dist == 0.:
                    continue
                z = (max_dist - mean_dist) / std_dist
            else:
                continue

            logger.debug('updated std: %f', std_dist)
            logger.debug('z of max: %f', z)

            # check if our max is big enough. this is to speed up things
            if z > 2.:
                logger.debug('choosing the max %i, z=%f',
                                indices_left[max_dist_idx], z)
                indices.append(indices_left.pop(max_dist_idx))
                break
        else:
            logger.debug('choosing the max one %i at the end', max_dist_idx)
            indices.append(indices_left.pop(max_dist_idx))
        logger.debug('done, chosen: %i, remaining: %i', len(indices),
                     len(indices_left))

    assert len(indices) == len(cities)
    for priority_index, i in enumerate(indices):
        cities[i][0].priority_index = priority_index
    session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='fills the database')
    parser.add_argument('input_file', help='parsed and augmented dump')
    parser.add_argument('--clear-cities', help='clears the cities before'
                        ' entering new ones', action='store_true')
    parser.add_argument('--force-clear-cities', help='no prompt before clearing'
                       ' cities', action='store_true')
    parser.add_argument('--fast-priority-index', help='faster but the cities '
                        ' look less nice (less spread out) on the map',
                        action='store_true')
    parser.add_argument('--max-cities', '-m', type=int)
    args = parser.parse_args()

    configure_logging()

    with session_scope() as session:
        nb_cities = session.query(City).count()

    if nb_cities > 0:
        if args.clear_cities:
            # Here we are erasing already existing cities before inserting new
            # ones.
            if args.force_clear_cities or are_you_sure(
                    'Are you sure you want to erase all the existing cities?'):
                with session_scope() as session:
                    session.query(MonthlyStat).delete()
                    session.query(City).delete()
            else:
                print('Did nothing.')
                sys.exit()
        else:
            # Here we are simply appending the new cities. You want to be sure
            # that this won't conflict in some way...
            if not are_you_sure(
                    'The database is not empty, there are already {} cities,'
                    ' do you still wish to pursue with loading data? If you'
                    ' want to clear already existing cities, use the'
                    ' --clear-cities flag'
                    .format(nb_cities)):
                print('Did nothing.')
                sys.exit()

    with open(args.input_file) as f:
        data = pickle.load(f)

    if args.max_cities is not None:
        data = data[:args.max_cities]

    with session_scope() as session:
        logger.info('filling the database')
        fill_cities(data, session)
        logger.info('adding the priority index')
        add_priority_index(session, args.fast_priority_index)
