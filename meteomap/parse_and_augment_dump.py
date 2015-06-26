import re, sys, pickle, argparse, logging
from urllib.parse import urlparse, quote, unquote
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from meteomap.utils import open, ask_before_overwrite, Timer, configure_logging

logger = logging.getLogger(__name__)


def get_first_number(x):
    try:
        if x == 'trace' or x == '-':
            return 0.
        match = re.search('^([\d,.-]+)[\s]*[(][^)]*[)]', x).group(1)
        match = match.replace(',', '')
        return float(match)
    except Exception:
        logger.warning('not able to parse "%s", returning 0.', x)
    return 0.


def get_second_number(x):
    """ actually gets the number in the parentheses """
    try:
        if x == 'trace' or x == '-':
            return 0.
        match = re.search('[(][\d,.-]+[)]', x).group()
        match = match.replace(',', '')  # comma for thousands
        return float(match[1:-1])
    except Exception:
        logger.warning('not able to parse "%s", returning 0.', x)
    return 0.


ROW_PARSERS = {
    'record high °c (°f)': ('recordHigh', get_first_number),
    'record high °f (°c)': ('recordHigh', get_second_number),
    'avg high °c (°f)': ('avgHigh', get_first_number),
    'avg high °f (°c)': ('avgHigh', get_second_number),
    'daily mean °c (°f)': ('avg', get_first_number),
    'daily mean °f (°c)': ('avg', get_second_number),
    'avg low °c (°f)': ('avgLow', get_first_number),
    'avg low °f (°c)': ('avgLow', get_second_number),
    'record low °c (°f)': ('recordLow', get_first_number),
    'record low °f (°c)': ('recordLow', get_second_number),

    'mean monthly sunshine hours': ('monthlySunHours', float),
    # TODO this is redundant. somes cities like Perth have both but IMHO it's a
    # bit stupid...
    'mean daily sunshine hours': ('dailySunHours', float),

    'avg precipitation days': ('precipitationDays', float),
    'avg precipitation mm (inches)': ('precipitation', get_first_number),
    'avg precipitation inches (mm)': ('precipitation', get_second_number),
    'avg precipitation cm (inches)': ('precipitation',
                                        lambda x: get_second_number(x) * 100.),

    'avg rainy days': ('rainDays', float),
    'avg rainfall mm (inches)' : ('rain', get_first_number),
    'avg rainfall inches (mm)' : ('rain', get_second_number),

    'avg snowy days': ('snowDays', float),
    'avg snowfall cm (inches)': ('snow', get_first_number),
    'avg snowfall inches (cm)': ('snow', get_second_number),

    'record high humidex': ('humidex', float),
    'record low wind chill': ('chill', float),
    'percent possible sunshine': ('percentSun', float),
    'avg relative humidity (%) (at : lst)': ('humidity', float),
    'avg relative humidity (%)': ('humidity', float),
}

PROPERTY = 'http://dbpedia.org/property/'
ONTOLOGY = 'http://dbpedia.org/ontology/'

POP_KEYS = [
    ONTOLOGY + 'populationTotal',
    PROPERTY + 'population',
    PROPERTY + 'populationCity',
    ONTOLOGY + 'populationUrban',
    PROPERTY + 'populationUrban',
    ONTOLOGY + 'populationMetro',
    PROPERTY + 'populationTotal',
    PROPERTY + 'populationMetro',
    PROPERTY + 'metroPopulation',
    PROPERTY + 'populationEst',
    PROPERTY + 'populationBlank',
    PROPERTY + 'populationBlank1Name',
    ONTOLOGY + 'populationRural',
    PROPERTY + 'populationRural',
]


def parse_climate_table(html):
    """ returns somethings like
        {'average temp C (F)' : ['12 (13)', ..., '12 (13)']
         ... }
    """
    bs = BeautifulSoup(html)
    months = bs.find_all('th', text=re.compile(r'[\s]*Month[\s]*'))

    # if there is nothing, it means there were no climate table in that html
    # code
    if len(months) < 1:
        return None

    if len(months) > 1:
        logger.debug('more than one matching table in html, using the first one')
    table = months[0].parent.parent
    data = {}
    for tr in table.find_all('tr'):
        ths = tr.find_all(['th','td'])
        if len(ths) != 1 + 12 + 1:
            continue
        title = ths[0].get_text().strip()
        if title == 'Month':
            continue
        data[title] = [ths[i].get_text().strip()
                             .replace('−', '-').replace('—', '-')
                       for i in range(1,13)]
    return data


def parse_data(climate_data):
    """ refines again the output of parse_climate_table(...) """
    out = {}
    for title, data in climate_data.items():
        title = ''.join(c for c in title if not c.isdigit()).lower()
        title = title.replace('.', '') \
                     .replace('average', 'avg') \
                     .replace(' ', ' ')  # weird space to normal space
        regex = re.compile(' days [(].*[)]')
        title = regex.sub(' days', title)

        try:
            key, parse_fn = ROW_PARSERS[title]
        except KeyError:
            logger.warning('no parser for key "%s"', title)
            continue
        # each thing should be there only once!
        assert key not in out
        try:
            out[key] = [parse_fn(x) for x in data]
        except ValueError:
            logger.warning('not able to parse one of those values "%s" for "%s"',
                        data, title)
            continue
    return out


def parse_population(infos):
    """ goes into the infos of a city and deduces the population of the city
    """
    for pop_key in POP_KEYS:
        if pop_key in infos:
            # we take the maximum in the group of the first key we find
            # RENDU ICI TODO tester ca voir si le max fait qu'on a pas des
            # populations de 40 oui 27, qui etait le rank
            # FIXME remove above comment when done
            return max(float(x) for x in infos[pop_key])
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='augments the data form dbpedia with data from wikipedia'
                    ' directly, like population/elevation/climate')
    parser.add_argument('input_file', help='dbpedia dump')
    parser.add_argument('output_file',
                        help='file where to dump the augmented data')
    parser.add_argument('--max-cities', '-m', type=int)
    parser.add_argument('--min-pop', default=1e6, help='minimum population to'
                        ' keep the city (if there are multiple population'
                        ' fields, we keep the maximum)', type=int)
    args = parser.parse_args()

    configure_logging()

    dump_in = pickle.load(open(args.input_file))

    if True or ask_before_overwrite(args.output_file):
        dump_out = open(args.output_file, 'w')
    else:
        sys.exit()

    timer = Timer(len(dump_in))
    new_data = {}
    nb_no_climate = 0
    nb_coords_from_wiki = 0
    nb_coords_from_dbpedia = 0
    for i, (city, infos) in enumerate(dump_in.items()):
        timer.update(i)
        if args.max_cities is not None and i+1 > args.max_cities:
            break
        logger.debug(city)
        # parsing population
        pop = parse_population(infos)
        if pop < args.min_pop:
            continue

        wikiurl = urlparse('http://' + infos['source'])
        wikiurl = urlopen(wikiurl.netloc + quote(wikiurl.path))

        # title in the wikipedia sense
        title = unquote(wikiurl.geturl()).split('/')[-1].replace('_', ' ')

        if 'name' in infos:
            name = infos['name']
        else:
            # patate_,chose -> patate
            name = title.split(',')[0].strip()

        # lat long and name from wikipedia, while we're at it
        result = requests.get('http://en.wikipedia.org/w/api.php', params=dict(
            action='query',
            prop='coordinates',
            titles=title,
            colimit=1,
            format='json')).json()
        wikiapi_data = result['query']
        assert len(wikiapi_data) == 1
        wikiapi_data = wikiapi_data['pages']
        assert len(wikiapi_data) == 1
        wikiapi_data = next(iter(wikiapi_data.values()))
        name = wikiapi_data['title']
        # if the coordinates were returned by the API
        if 'coordinates' in wikiapi_data:
            coords = wikiapi_data['coordinates']
            assert len(coords) == 1
            lat = coords[0]['lat']
            lon = coords[0]['lon']
            nb_coords_from_wiki += 1
        # if not, sometimes the coordinates are somewhere else and dbpedia
        # picked them up
        else:
            lat = float(infos['lat'])
            lon = float(infos['long'])
            nb_coords_from_dbpedia += 1
        logger.debug('%s : (%f, %f)', name, lat, lon)

        if pop is None:
            # logger.debug('no pop for', city)
            # logger.debug(infos)
            continue

        # TODO
        # parse the elevation. it might already be in the dump.gz
        # the code is in obsolete parse_dbpedia_dump.py

        html = wikiurl.read()
        data = parse_climate_table(html)
        if data is None:
            nb_no_climate += 1
            # logger.debug('no climate for %s', city)
            continue

        parsed_data = parse_data(data)
        new_data[city] = {'population': pop,
                          'source': wikiurl.geturl(),
                          'lat': lat,  # float(infos['lat']),
                          'long': lon,  # float(infos['long']),
                          'name': name,
                          'month_stats': parsed_data}

    logger.info('parsed %i cities', len(new_data))
    logger.info('got %i coordinates from the wikipedia API',
                nb_coords_from_wiki)
    logger.info('got %i coordinates from dbpedia',
                nb_coords_from_dbpedia)
    pickle.dump(new_data, dump_out)
