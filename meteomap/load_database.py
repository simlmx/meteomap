import pickle, argparse, sys
from geoalchemy2.elements import WKTElement
from sqlalchemy import desc
from meteomap.utils import (open, session_scope, Timer, are_you_sure,
                            configure_logging)

from meteomap.tables import City, Stat, MonthlyStat


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
            population = city.pop)
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

    # FIXME NOT TESTED
    # Add the region_index and country_index
    last_country = None
    for x in session.query(City) \
            .order_by(City.country, desc(City.population)) \
            .yield_per(1000):
        if last_country is None or last_country != x.country:
            idx = 0
        x.country_index = idx
        idx += 1
        last_country = x.country
    session.commit()

    last_region = None
    for x in session.query(City) \
            .order_by(City.region, desc(City.population)) \
            .yield_per(1000):
        if last_region is None or last_region != x.region:
            idx = 0
        x.region_index = idx
        idx += 1
        last_region = x.region
    session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='fills the database')
    parser.add_argument('input_file', help='parsed and augmented dump')
    parser.add_argument('--clear-cities', help='clears the cities before'
                        ' entering new ones', action='store_true')
    parser.add_argument('--force-clear-cities', help='no prompt before clearing'
                       ' cities', action='store_true')
    parser.add_argument('--max-cities', '-m', type=int)
    args = parser.parse_args()

    configure_logging()

    with session_scope() as session:
        nb_cities = session.query(City).count()

    if nb_cities > 0:
        if args.clear_cities:
            # Here we are erasing already existing cities before inserting new
            # ones.
            if args.force_clear_cities or are_you_sure('Are you sure you want to erase all the existing'
                            ' cities?'):
                with session_scope() as session:
                    session.query(MonthlyStat).delete()
                    session.query(City).delete()
            else:
                print('Did nothing.')
                sys.exit()
        else:
            # Here we are simply appending the new cities. You want to be sure that
            # this won't conflict in some way...
            if not are_you_sure(
                    'The database is not empty, there are already {} cities, do you'
                    ' still wish to pursue with loading data? If you want to clear'
                    ' already existing cities, use the --clear-cities flag'
                    .format(nb_cities)):
                print('Did nothing.')
                sys.exit()

    with open(args.input_file) as f:
        data = pickle.load(f)

    if args.max_cities is not None:
        data = data[:args.max_cities]

    with session_scope() as session:
        fill_cities(data, session)
