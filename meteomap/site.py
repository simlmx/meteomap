import sys, json

from flask import Flask, request
from sqlalchemy import desc

from meteomap.tables import City
from meteomap.utils import init_session


app = Flask(__name__)


@app.route('/')
def home_route():
    return '<a href="data?n=46&s=45&w=-74&e=74">data</a>'

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
        .order_by(desc(City.population)) \
        .limit(100).all()
    data = [x._asdict() for x in data]
    return json.dumps(data)


if __name__ == '__main__':
    # arg1 : --debug
    debug = False
    if len(sys.argv) > 1 and sys.argv[1] == '--debug':
        debug = True
    debug = app.run(debug=debug)
