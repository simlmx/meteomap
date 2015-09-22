import pickle, argparse, sys, logging, heapq
import numpy
from geoalchemy2.elements import WKTElement
from geoalchemy2 import Geometry
from sqlalchemy import desc, func, cast
from meteomap.utils import (open, session_scope, Timer, are_you_sure,
                            configure_logging)
from meteomap.tables import City, Stat, MonthlyStat
from meteomap.city import lat_lon_fast_distance

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


def add_priority_index(session, fast_mode=False):
    """ decides the order in which the cities should be selected """
    cities = session.query(City,
                          func.ST_Y(cast(City.location, Geometry())),
                          func.ST_X(cast(City.location, Geometry()))) \
        .join(MonthlyStat) \
        .order_by(City.region_rank, City.country_rank,
                  desc(func.count(MonthlyStat.id))) \
        .group_by(City.id) \
        .yield_per(1000).all()

    if fast_mode:
        logger.info('doing the fast version of priority index')
        for i,city in enumerate(cities):
            city[0].priority_index = i
        session.commit()
        return

    def distance_fn(tuple1, tuple2):
        _,lat1,lon1 = tuple1
        _,lat2,lon2 = tuple2
        return lat_lon_fast_distance(lat1, lon1, lat2, lon2)

    indices = [0]
    indices_left = list(range(1,len(cities)))

    # pre-calculate the distances between all the cities
    logger.info('pre-calculating the distances between all cities')
    lats = numpy.array([c[1] for c in cities])
    lons = numpy.array([c[2] for c in cities])
    distances = lat_lon_fast_distance(lats.reshape(-1,1),
                                      lons.reshape(-1,1),
                                      lats.reshape(1,-1),
                                      lons.reshape(1,-1))

    class CityComp(object):
        idx = None
        max_dist = None
        max_dist_idx = None

        def __init__(self, max_dist, max_dist_idx):
            self.max_dist = max_dist
            self.max_dist_idx = max_dist_idx

        def __lt__(self, other):
            return self.max_dist < other.max_dist

    # each city is compared to all the previous ones (maximum)
    timer = Timer(len(indices_left))
    # percent of closest cities to choose from
    perc_closest_cities = 0.1
    # same but max
    max_closest_cities = 200
    while len(indices_left) > 0:
        # let's find the next city amongst the next candidates
        # this will be our (heap) list of good candidates, i.e. the ones
        # farthest from all the others
        good_candidates = []
        nb_keep = min(perc_closest_cities * len(indices_left),
                      max_closest_cities)
        nb_keep = max(1, nb_keep)  # at least 1!
        logger.debug('will keep the farthest %i', nb_keep)
        # max_dist = 0.
        # max_dist_idx = 0
        logger.debug('---------looking for the next one----------')
        for no_candidate, i_left in enumerate(indices_left):
            # logger.debug('candidate %i, idx %i', no_candidate, i_left)
            # find how close is the nearest neighbor for this city
            # we are looking for the city with the fartest nearest neighbor
            dist_nearest_neighbor = 1e9
            # get the distance of our candidate to the closest (already chosen)
            # city
            too_close = False
            for i_chosen in indices:
                cur_dist = distances[i_chosen, i_left]
                # if we already have enough candidates, and if the current is
                # worse than all others, let's skip it
                if len(good_candidates) >= nb_keep \
                        and cur_dist <= good_candidates[0].max_dist:
                    too_close = True
                    # logger.debug('too close @%f', cur_dist)
                    break
                dist_nearest_neighbor = min(dist_nearest_neighbor, cur_dist)
            # we don't compare the distance of this candidate with all cities
            # if it's closer to (already chosen) city than our best candidate
            # so far
            if too_close:
                continue
            # dist_nearest_neighbor = numpy.min(distances[indices][:,i_left])
            # logger.debug('candidate %i has a city at %f', no_candidate,
                         # dist_nearest_neighbor)

            # if dist_nearest_neighbor > best_candidate.max_dist:
                # logger.debug('(new max)')
            new_candidate = CityComp(dist_nearest_neighbor, no_candidate)
            # logger.debug('trying to add new candidate with dist %f',
                         # new_candidate.max_dist)
            # if we don't have enough anyway
            if len(good_candidates) < nb_keep:
                heapq.heappush(good_candidates, new_candidate)
            else:
                # if we have enough, just keep the n best
                rejected_cand = heapq.heappushpop(good_candidates,
                                                  new_candidate)
                # logger.debug('removed candidate %i with dist %f',
                            # rejected_cand.max_dist_idx,
                            # rejected_cand.max_dist)

        # take the smallest index in our good candidates. this corresponds to
        # the best (according to our first ORDER BY) amongst the "far enough"
        # candidates
        best_candidate = min(good_candidates, key=lambda x: x.max_dist_idx)
        logger.debug('keeping %s with pop %i',
                     cities[indices_left[best_candidate.max_dist_idx]][0].name,
                     cities[indices_left[best_candidate.max_dist_idx]][0].population,)
        # input('press to continue')
        indices.append(indices_left.pop(best_candidate.max_dist_idx))
        logger.debug('done, best candidate was %i with distance %f',
                     best_candidate.max_dist_idx, best_candidate.max_dist)
        logger.debug('done, chosen: %i, remaining: %i', len(indices),
                     len(indices_left))
        timer.update()

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
    parser.add_argument('--country', help='Will only keep cities in this'
                        ' country and ignore the rest')
    parser.add_argument('--max-cities', '-m', type=int)
    args = parser.parse_args()

    configure_logging()

    with session_scope() as session:
        nb_cities = session.query(City).count()

    if args.force_clear_cities and not args.clear_cities:
        print('You must specify the --clear-cities argument if you want to'
              ' use the --force-clear-cities argument')

    if nb_cities > 0:
        if args.clear_cities:
            # Here we are erasing already existing cities before inserting new
            # ones.
            if args.force_clear_cities or are_you_sure(
                    'Are you sure you want to erase all the existing cities?'):
                with session_scope() as session:
                    logger.info('deleting cities')
                    session.query(MonthlyStat).delete()
                    session.query(City).delete()
                    session.commit()
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

    logger.info('loading the data')
    with open(args.input_file) as f:
        data = pickle.load(f)

    if args.max_cities is not None:
        data = data[:args.max_cities]

    with session_scope() as session:
        logger.info('filling the database')
        fill_cities(data, session)
        logger.info('adding the priority index')
        add_priority_index(session, args.fast_priority_index)
