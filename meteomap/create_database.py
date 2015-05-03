import argparse, sys
from sqlalchemy import create_engine
from tables import Base
from settings import DATABASE_STR, DATABASE


postgres_database = '{}://{}:{}@{}{}/postgres'.format(
    DATABASE['type'],
    DATABASE['user'],
    DATABASE['password'],
    DATABASE['host'],
    (':' + DATABASE['port']) if DATABASE['port'] != '' else '')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='create the database')
    parser.add_argument('--drop', action='store_true', help='use this arguemnt'
                       ' to DROP an already existing database before creating'
                       ' it')
    args = parser.parse_args()

    engine = create_engine(postgres_database)

    if args.drop:
        choice = ''
        while choice not in ['Y','N']:
            choice = input('are you sure you want to DROP the existing'
                            'database? (Y/N) ')
        if choice == 'Y':
            conn = engine.connect()
            conn.execute('commit')
            conn.execute('drop database ' + DATABASE['name'])
            conn.close()
        else:
            print('doing nothing')
            sys.exit()

    # do I need so try/except logic here?
    conn = engine.connect()
    conn.execute('commit')
    conn.execute('create database ' + DATABASE['name'])
    conn.close()

    engine = create_engine(DATABASE_STR)
    conn = engine.connect()
    conn.execute('create extension postgis')
    conn.close()
    Base.metadata.create_all(engine)
