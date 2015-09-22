import json, argparse
from collections import defaultdict
from flask import Flask, request, render_template
from sqlalchemy import func, cast
from sqlalchemy.sql.functions import ReturnTypeFromArgs
from geoalchemy2 import Geometry
from meteomap.tables import City, MonthlyStat, Stat
from meteomap.utils import session_scope, configure_logging
from meteomap.settings import config


app = Flask(__name__)


class unaccent(ReturnTypeFromArgs):
    pass


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
    nb = int(request.args.get('nb', config['max_nb_cities_at_once']))
    if nb > config['max_nb_cities_at_once']:
        nb = config['max_nb_cities_at_once']

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
            .limit(nb).subquery('city')

        # get their data
        query = session.query(
            sq.c.id,
            sq.c.name,
            func.ST_Y(cast(sq.c.location, Geometry())),
            func.ST_X(cast(sq.c.location, Geometry())),
            sq.c.population, MonthlyStat.month,
            MonthlyStat.value, Stat.code, sq.c.country, sq.c.source) \
            .join(MonthlyStat) \
            .join(Stat) \
            .filter(Stat.code.in_(['avgHigh', 'avgLow', 'precipitation',
                                   'precipitationDays', 'monthlySunHours',
                                   'rain', 'rainDays']))

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
            cities[id]['country'] = row[8]
            cities[id]['source'] = row[9]

        # changing rain to precipitation
        # TODO something similar with snow?
        for _,c in cities.items():
            for old, new in [('rain', 'precipitation'),
                             ('rainDays', 'precipitationDays')]:
                if old in c['month_stats'] and new not in c['month_stats']:
                    c['month_stats'][new] = c['month_stats'].pop(old)

        # from pprint import pprint
        # pprint(cities)
    return json.dumps(cities)


@app.route('/stats')
def stats_route():
    with session_scope() as session:
        infos = {getattr(x, 'code'): {c.name: getattr(x, c.name)
                                      for c in x.__table__.columns
                                      if c.name not in ['id', 'code']}
                 for x in session.query(Stat)}
    return json.dumps(infos)


@app.route('/search')
def search_route():
    query = request.args.get('q')
    per_page = request.args.get('per_page', 10, type=int)
    page = request.args.get('page', 0, type=int)
    if query is None:
        return json.dumps({'results':[]})
    result = {}
    with session_scope() as session:
        results = session.query(
            City.name,
            City.country,
            func.ST_Y(cast(City.location, Geometry())),
            func.ST_X(cast(City.location, Geometry())),
            City.id
            ) \
            .filter(unaccent(City.name).ilike(unaccent('%' + query + '%'))) \
            .limit(per_page + 1) \
            .offset(page * per_page) \
            .all()

        more = len(results) == per_page + 1
        results = results[:per_page]
        result = json.dumps({
            'results':
            [{'id': c[4], 'text': '{}, {}'.format(c[0], c[1]), 'coords': (c[2], c[3])} for i,c in enumerate(results)],
            'more': more})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Start the server.')
    parser.add_argument('--debug', action='store_true',
                        help='Run the server in debug mode')
    args = parser.parse_args()
    configure_logging()
    app.run(debug=args.debug)
