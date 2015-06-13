import sys, json, argparse

from flask import Flask, request
from sqlalchemy import desc, func
from geoalchemy2.elements import WKTElement

from meteomap.tables import City
from meteomap.utils import init_session, configure_logging


app = Flask(__name__)


@app.route('/')
def home_route():
    return '<a href="data?n=46&s=45&w=-73&e=-74">Montreal</a>'

@app.route('/data')
def data_route():
    west = request.args.get('w')
    east = request.args.get('e')
    north = request.args.get('n')
    south = request.args.get('s')
    if west is None or east is None or south is None or north is None:
        return 'no data'

    session = init_session()
    data = session.query(City.name, City.population) \
        .filter(
            func.ST_Covers(
                WKTElement(
                    'POLYGON(({0} {1}, {0} {2}, {3} {2}, {3} {1}, {0} {1}))'
                    .format(south, east, west, north),
                    srid=4326),
                City.location)) \
        .order_by(desc(City.population)) \
        .limit(100).all()
    data = [x._asdict() for x in data]
    return json.dumps(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Start the server.')
    parser.add_argument('--debug', action='store_true',
                        help='Run the server in debug mode')
    args = parser.parse_args()
    configure_logging()
    app.run(debug=args.debug)
