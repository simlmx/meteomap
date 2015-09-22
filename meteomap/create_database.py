import sys, argparse
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from meteomap.utils import session_scope, are_you_sure, configure_logging
from meteomap.tables import Stat, Base
from meteomap.settings import DATABASE_STR_WITUOUT_TABLE, DATABASE_STR, DATABASE


STATS = [
    ('recordHigh', 'Record High', '°C', 'Record for highest temperature for the day.', 'RH'),
    ('avgHigh', 'Average High', '°C', 'Highest temperature for the day.', 'AH'),
    ('avg', 'Daily Mean', '°C', 'Average temperature for the day.', 'AV'),
    ('avgLow', 'Average Low', '°C', 'Lowest temperature for the day.', 'AL'),
    ('recordLow', 'Record Low', '°C', 'Record for lowest temperature for the day.', 'RL'),

    ('precipitation', 'Precipitation', 'mm', 'Precipitation (rain and snow) for the day.', 'PR'),
    ('rain', 'Rainfall', 'mm', 'Rain for the month.', 'RA'),
    ('snow', 'Snowfall', 'cm', 'Snow for the month.', 'SN'),

    ('rainDays', 'Rainy Days', 'days', 'Number of rainy days.', 'RD'),
    ('snowDays', 'Snowy Days', 'days', 'Number of snowy days.', 'SD'),
    ('precipitationDays', 'Precip. Days', 'days',
     'Number of days with precipitation (rain or snow).', 'PD'),

    ('humidity', 'Humidity', '%', 'Perc. of humidity.', 'HU'),
    ('percentSunDays', 'Percent possible sunshine', '%', 'Ratio of sunshine and daylight durations', 'SD'),
    ('monthlySunHours', 'Sunshine hours', 'hours', 'Monthly sunshine hours', 'SH'),
]


def fill_stat_table(session):
    for code, name, unit, description, name_short in STATS:
        s = Stat(code = code,
                 name = name,
                 unit = unit,
                 description = description,
                 name_short = name_short)
        session.add(s)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Creates the database.'
                    ' Only fills with the stat descriptions')
    parser.add_argument('--force-drop', action='store_true')
    args = parser.parse_args()

    configure_logging()

    db_name = DATABASE['name']

    with session_scope(url=DATABASE_STR_WITUOUT_TABLE) as session:
        session.execute('commit')
        try:
            session.execute('create database ' + db_name)
        except ProgrammingError:
            # the database already exists
            if args.force_drop or are_you_sure(
                    'The database "{}" already exists, do you wish to DROP it?'
                    .format(db_name)):
                session.execute('drop database ' + db_name)
                session.execute('create database ' + db_name)
            else:
                print('Did nothing.')
                sys.exit()

    with session_scope() as session:
        session.execute('create extension postgis')
        session.execute('create extension unaccent')

    # create all the tables
    engine = create_engine(DATABASE_STR)
    Base.metadata.create_all(engine)

    with session_scope() as session:
        fill_stat_table(session)
