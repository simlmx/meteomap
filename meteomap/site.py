import json, argparse
from collections import defaultdict
from flask import Flask, request, render_template
from sqlalchemy import desc, func, cast
from sqlalchemy.orm import aliased
from geoalchemy2.elements import WKTElement
from geoalchemy2 import Geometry

from meteomap.tables import City, MonthlyStat, Stat
from meteomap.utils import init_session, configure_logging


app = Flask(__name__)


@app.route('/')
def index_route():
    return render_template('index.html', data='patate poil')


@app.route('/data')
def data_route():
    west = request.args.get('w')
    east = request.args.get('e')
    north = request.args.get('n')
    south = request.args.get('s')
    if west is None or east is None or south is None or north is None:
        return 'TODO 404'

    rectangle = 'POLYGON(({0} {1}, {0} {2}, {3} {2}, {3} {1}, {0} {1}))' \
        .format(west, south, north, east)
    session = init_session()
    sq = session.query(City) \
        .filter(func.ST_Covers(
            cast(rectangle, Geometry()),
            func.ST_SetSRID(cast(City.location, Geometry()), 0))) \
        .order_by(desc(City.population)) \
        .limit(25).subquery('city')

    query = session.query(
        sq.c.name,
        func.ST_Y(cast(sq.c.location, Geometry())),
        func.ST_X(cast(sq.c.location, Geometry())),
        sq.c.population, MonthlyStat.month,
        MonthlyStat.value, Stat.code) \
        .join(MonthlyStat) \
        .join(Stat)

    def default():
        return {'month_stats': defaultdict(dict)}
    cities = defaultdict(default)
    # print(query)
    # format what is returned from the query
    for row in query:
        name = row[0]
        cities[name]['lat'] = row[1]
        cities[name]['long'] = row[2]
        cities[name]['pop'] = row[3]
        cities[name]['month_stats'][row[6]][row[4]] = row[5]
    # from pprint import pprint
    # pprint(cities)
    return json.dumps(cities)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Start the server.')
    parser.add_argument('--debug', action='store_true',
                        help='Run the server in debug mode')
    args = parser.parse_args()
    configure_logging()
    app.run(debug=args.debug)
