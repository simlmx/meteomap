import sys, argparse
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from meteomap.utils import session_scope, are_you_sure, configure_logging
from meteomap.tables import Stat, Base
from meteomap.settings import DATABASE_STR_WITUOUT_TABLE, DATABASE_STR


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
    ('monthlySunHours', 'Sunshine hours', 'hours', 'Monthly sunshine hours'),
]


def fill_stat_table(session):
    for code, name, unit, description in STATS:
        s = Stat(code = code,
                 name = name,
                 unit = unit,
                 description = description)
        session.add(s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Creates the database.'
                    ' Only fills with the stat descriptions')
    parser.add_argument('--force-drop', action='store_true')
    args = parser.parse_args()

    configure_logging()

    with session_scope(url=DATABASE_STR_WITUOUT_TABLE) as session:
        session.execute('commit')
        try:
            session.execute('create database meteomap')
        except ProgrammingError:
            # the database already exists
            if args.force_drop or are_you_sure(
                    'The database already exists, do you wish to DROP it?'):
                session.execute('drop database meteomap')
                session.execute('create database meteomap')
            else:
                print('Did nothing.')
                sys.exit()

    with session_scope() as session:
        session.execute('create extension postgis')

    # create all the tables
    engine = create_engine(DATABASE_STR)
    Base.metadata.create_all(engine)

    with session_scope() as session:
        fill_stat_table(session)
