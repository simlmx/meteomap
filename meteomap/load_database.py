import pickle, argparse, sys
from geoalchemy2.elements import WKTElement
from meteomap.utils import (open, session_scope, Timer, are_you_sure,
                            configure_logging)

from meteomap.tables import City, Stat, MonthlyStat


def fill_cities(data, session):
    stats_dict = dict(session.query(Stat.code, Stat.id))
    timer = Timer(len(data))
    for city_data in data.values():
        pop = city_data['population'] if 'population' in city_data else None
        el = city_data['elevation'] if 'elevation' in city_data else None
        geom = WKTElement('POINT({:.8f} {:.8f})'.format(city_data['long'],
                                             city_data['lat']), srid=4326)
        city = City(location = geom,
                    name = city_data['name'],
                    source = city_data['source'],
                    population = pop,
                    elevation = el)
        session.add(city)
        # commit the cities so we can use them
        # I'm not sure this is the clean way to do it...
        session.commit()
        for code, month_stats in city_data['month_stats'].items():
            if code not in stats_dict:
                continue
            for month_idx, value in enumerate(month_stats):
                ms = MonthlyStat(
                    month = month_idx,
                    city_id = city.id,
                    stat_id = stats_dict[code],
                    value = value)
                session.add(ms)
        timer.update()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='fills the database')
    parser.add_argument('input_file', help='parsed and augmented dump')
    parser.add_argument('--clear-cities', help='clears the cities before'
                        ' entering new ones', action='store_true')
    parser.add_argument('--max-cities', '-m', type=int)
    args = parser.parse_args()

    configure_logging()

    if args.clear_cities:
        # Here we are erasing already existing cities before inserting new
        # ones.
        if are_you_sure('Are you sure you want to erase all the existing'
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
        with session_scope() as session:
            nb_cities = session.query(City).count()

        if nb_cities > 0 and not are_you_sure(
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
