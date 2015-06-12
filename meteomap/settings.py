import json

# read some infos for our config
config = json.load(open('config.json'))

DATABASE = {
    'type': 'postgresql+psycopg2',
    'name': config['db']['name'],
    'user': config['db']['user'],
    'password': config['db']['password'],
    'host': config['db']['host'],
    'port': config['db']['port'],
}

DATABASE_STR_WITUOUT_TABLE = '{}://{}:{}@{}{}'.format(
    DATABASE['type'],
    DATABASE['user'],
    DATABASE['password'],
    DATABASE['host'],
    ':' + DATABASE['port'] if DATABASE['port'] != '' else '')

DATABASE_STR = '{}/{}'.format(DATABASE_STR_WITUOUT_TABLE, DATABASE['name'])

LOGGING_CONFIG = config['logging']
