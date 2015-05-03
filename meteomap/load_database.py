import pickle, sys, datetime
from meteomap.utils import open, session_scope, Timer
from meteomap.tables import City, Stat, MonthlyStat


STATS = [
    ('avgHigh', 'Average High', '°C', 'Highest temperature for the day.'),
    ('avgLow', 'Average Low', '°C', 'Lowest temperature for the day.'),
    ('recordHigh', 'Record High', '°C', 'Record for highest temperature for the day.'),
    ('recordLow', 'Record Low', '°C', 'Record for lowest temperature for the day.'),
    ('avg', 'Daily Mean', '°C', 'Average temperature for the day.'),

    ('rain', 'Rainfall', 'mm', 'Rain for the month.'),
    ('snow', 'Snowfall', 'cm', 'Snow for the month.'),
    ('precipitation', 'Precipitation', 'mm', 'Precipitation (rain and snow) for the day.'),

    ('rainDays', 'Rainy Days', 'days', 'Number of rainy days.'),
    ('snowDays', 'Snowy Days', 'days', 'Number of snowy days.'),
    ('precipitationDays', 'Precipitation Days', 'days',
     'Number of days with precipitation (rain or snow).'),

    ('humidity', 'Humidity', '%', 'Percentage of humidity.'),
    ('percentSunDays', 'Percent possible sunshine', '%', 'Ratio of sunshine and daylight durations'),
    ('sunHours', 'Sunshine hours', '%', 'Monthly sunshine hours'),
]


def fill_stat_table(session):
    for code, name, unit, description in STATS:
        s = Stat(code = code,
                 name = name,
                 unit = unit,
                 description = description)
        session.add(s)


def fill_cities(data, session):
    stats_dict = dict(session.query(Stat.code, Stat.id))
    months = ['{:%b}'.format(datetime.datetime(2000, i+1, 1)).lower()
              for i in range(12)]
    months_dict = dict([
        (datetime.datetime(2000, i+1, 1).strftime('%b').lower(), i+1)
        for i in range(12)])
    timer = Timer(len(data))
    for city_name, city_data in data.items():
        pop = city_data['population'] if 'population' in city_data else None
        el = city_data['elevation'] if 'elevation' in city_data else None
        city = City(location = 'POINT({:.8f} {:.8f})'.format(city_data['lat'],
                                                        city_data['long']),
                    name = city_name.split(',')[0].replace('_', ''),
                    population = pop,
                    elevation = el)
        session.add(city)
        # commit the cities so we can use them
        # I'm not sure this is the clean way to do it...
        session.commit()
        for month, month_stats in city_data['month_stats'].items():
            for code, value in month_stats.items():
                if code not in stats_dict:
                    continue
                ms = MonthlyStat(
                    month = months_dict[month],
                    city_id = city.id,
                    stat_id = stats_dict[code],
                    value = value)
                session.add(ms)
        timer.update()


if __name__ == '__main__':
    # arg 1 - dump file
    with open(sys.argv[1]) as f:
        data = pickle.load(f)

    # arg 2 - --no-dry-run
    dryrun = len(sys.argv) > 2 and sys.argv[2] != '--no-dry-run'

    # TODO real argparse options, notably for choosing which part to INSERT

    if True:
        with session_scope(dryrun) as session:
            # stats table
            fill_stat_table(session)

    with session_scope(dryrun) as session:
        # city data
        fill_cities(data, session)
