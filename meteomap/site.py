import json, argparse
from collections import defaultdict
from flask import Flask, request, render_template
from sqlalchemy import func, cast
from geoalchemy2 import Geometry
from meteomap.tables import City, MonthlyStat, Stat
from meteomap.utils import session_scope, configure_logging
from meteomap.settings import config


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
    month = request.args.get('m')

    if west is None or east is None or south is None or north is None:
        return 'TODO 404'

    rectangle = 'POLYGON(({0} {1}, {0} {2}, {3} {2}, {3} {1}, {0} {1}))' \
        .format(west, south, north, east)
    with session_scope() as session:
        # choose N cities
        sq = session.query(City) \
            .filter(func.ST_Covers(
                cast(rectangle, Geometry()),
                func.ST_SetSRID(cast(City.location, Geometry()), 0))) \
            .order_by(City.priority_index) \
            .limit(config['nb_cities_at_once']).subquery('city')

        # get their data
        query = session.query(
            sq.c.id,
            sq.c.name,
            func.ST_Y(cast(sq.c.location, Geometry())),
            func.ST_X(cast(sq.c.location, Geometry())),
            sq.c.population, MonthlyStat.month,
            MonthlyStat.value, Stat.code) \
            .join(MonthlyStat) \
            .join(Stat) \
            .filter(Stat.code.in_(['avgHigh', 'precipitation']))

        if month is not None:
            query = query.filter(MonthlyStat.month == month)

        def default():
            return {'month_stats': defaultdict(dict)}
        cities = defaultdict(default)
        # print(query)
        # format what is returned from the query
        for row in query:
            id = row[0]
            cities[id]['name'] = row[1]
            cities[id]['coords'] = (row[2], row[3])
            cities[id]['pop'] = row[4]
            cities[id]['month_stats'][row[7]][row[5]] = row[6]
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
