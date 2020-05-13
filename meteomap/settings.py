import os
import json


DATABASE_STR_WITHOUT_TABLE = '{}://{}:{}@{}:{}'.format(
    'postgresql+psycopg2',
    os.environ['METEOMAP_DB_USER'],
    os.environ['METEOMAP_DB_PASSWORD'],
    os.environ['METEOMAP_DB_HOST'],
    os.environ['METEOMAP_DB_PORT'],
)

DATABASE_STR = '{}/{}'.format(
    DATABASE_STR_WITHOUT_TABLE,
    os.environ['METEOMAP_DB_NAME'],
)

MAX_CITIES = int(os.environ['METEOMAP_MAX_CITIES'])

# TODO This is a bit legacy.
LOGGING_CONFIG = {
    "level": "INFO",
    "handlers": ["file", "console"],
    "email": {
        "server": "your email server",
        "port": 1234,
        "address": "your email",
        "pass": "your email password"
    }
}
