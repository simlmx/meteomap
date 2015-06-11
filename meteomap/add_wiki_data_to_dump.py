import re, sys, pickle, argparse, logging
from urllib.parse import urlparse, quote
from urllib.request import urlopen
from bs4 import BeautifulSoup
from meteomap.utils import open, ask_before_overwrite, Timer, configure_logging
from pprint import pprint

logger = logging.getLogger(__name__)


def get_first_number(x):
    try:
        return float(re.search('^[\d.-]+', x).group())
    except Exception:
        logger.warning('not able to parse "%s", returning 0.', x)
    return 0.


def get_second_number(x):
    """ actually gets the number in the parentheses """
    try:
        match = re.search('[(][\d.-]+[)]', x).group()
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
    'avg low °f (°c)': ('averageLow', get_second_number),
    'record low °c (°f)': ('recordLow', get_first_number),
    'record low °f (°c)': ('recordLow', get_second_number),

    'mean monthly sunshine hours': ('monthlySunHours', float),
    # TODO this is redundant. somes cities like Perth have both but IMHO it's a
    # bit stupid...
    'mean daily sunshine hours': ('dailySunHours', float),

    'avg precipitation days (≥  mm)': ('precipitationDays', float),
    'avg precipitation days (≥  in)': ('precipitationDays', float),
    'avg precipitation days': ('precipitationDays', float),
    'avg precipitation mm (inches)': ('precipitation', get_first_number),
    'avg precipitation inches (mm)': ('precipitation', get_second_number),
    'avg precipitation cm (inches)': ('precipitation',
                                        lambda x: get_second_number(x) * 100.),

    'avg rainy days (≥  mm)': ('rainDays', float),
    'avg rainy days (≥  in)': ('rainDays', float),
    'avg rainy days (≥ ≥  mm)': ('rainDays', float),
    'avg rainy days': ('rainDays', float),
    'avg rainfall mm (inches)' : ('rain', get_first_number),
    'avg rainfall inches (mm)' : ('rain', get_second_number),

    'avg snowy days (≥  in)': ('snowDays', float),
    'avg snowy days (≥  cm)': ('snowDays', float),
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
        logger.info('more than one matching table in html, using the first one')
    table = months[0].parent.parent
    data = {}
    for tr in table.find_all('tr'):
        ths = tr.find_all(['th','td'])
        if len(ths) != 1 + 12 + 1:
            continue
        title = ths[0].get_text().strip()
        if title == 'Month':
            continue
        data[title] = [ths[i].get_text().strip().replace('−', '-').replace(',', '.') for i in range(1,13)]
    return data


def parse_data(climate_data):
    """ refines again the output of parse_climate_table(...) """
    out = {}
    for title, data in climate_data.items():
        title = ''.join(c for c in title if not c.isdigit()).lower()
        title = title.replace('.', '') \
                     .replace('average', 'avg') \
                     .replace(' ', ' ')  # weird space to normal space

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
            return min(float(x) for x in infos[pop_key])
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='augments the data form dbpedia with data from wikipedia'
                    ' directly, like population/elevation/climate')
    parser.add_argument('input_file', help='dbpedia dump')
    parser.add_argument('output_file',
                        help='file where to dump the augmented data')
    parser.add_argument('--max-cities', '-m', type=int)
    args = parser.parse_args()

    configure_logging('INFO')

    dump_in = pickle.load(open(args.input_file))

    if True or ask_before_overwrite(args.output_file):
        dump_out = open(args.output_file, 'w')
    else:
        sys.exit()

    timer = Timer(len(dump_in))
    new_data = {}
    nb_no_climate = 0
    for i, (city, infos) in enumerate(dump_in.items()):
        if args.max_cities is not None and i+1 > args.max_cities:
            break
        logger.debug(city)
        # TODO remove at some point
        # NOW DOING THIS IN THE fetch_dbpedia.py STEP
        # WE CAN PROBABLY REMOVE IT FROM HERE ALL TOGETHER
        # quick skip of the really small settlements
        # this might not be optimal, we probably want some other criterion to
        # decide if we should skip or not.
        # we still want to do it because loading the HTML of a wikipedia page
        # currently seems to be the bottleneck of the whole thing
        # max_pop = 0
        # for k,v in infos.items():
        #     if 'population' in k and int(v) > max_pop:
        #         max_pop = int(v)
        # if max_pop < 1e5:
        #     continue

        # parsing population
        pop = parse_population(infos)
        if pop is None:
            # logger.debug('no pop for', city)
            # logger.debug(infos)
            continue

        url = urlparse('http://' + infos['source'])
        url = urlopen(url.netloc + quote(url.path))
        html = url.read()
        data = parse_climate_table(html)
        if data is None:
            nb_no_climate += 1
            # logger.debug('no climate for %s', city)
            continue

        parsed_data = parse_data(data)
        new_data[city] = {'population': pop,
                          'source': url.geturl(),
                          'lat': infos['lat'],
                          'long': infos['long']}
        new_data[city].update(parsed_data)
        timer.update(i+1)

    pickle.dump(new_data, dump_out)
