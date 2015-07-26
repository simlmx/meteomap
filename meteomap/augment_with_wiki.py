import re, sys, pickle, argparse, logging
from pprint import pprint
import wikipedia as wiki
from bs4 import BeautifulSoup
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='augments the data form geonames.org with data from'
        'wikipedia, mainly the climate data')
    parser.add_argument('input_file', help='parsed geonames dump')
    parser.add_argument('output_file',
                        help='output file for the augmented data')
    parser.add_argument('--max-cities', '-m', type=int)
    parser.add_argument('--skip-wiki', action='store_true', help='skip the'
                        ' wikipedia API calling part. mostly for debugging')
    parser.add_argument('--wiki-sub', help='use wiki data previously fetched'
                        ' in this file only')
    parser.add_argument('--force', action='store_true', help='don\'t ask'
                        ' before overwriting the output file')
    args = parser.parse_args()

    configure_logging()

    dump_in = pickle.load(open(args.input_file))

    if not (args.force or ask_before_overwrite(args.output_file)):
        sys.exit()

    if args.skip_wiki:
        logger.info('skipping wikipedia')
        for c in dump_in:
            c.month_stats = {'avgHigh':range(12), 'precipitation': range(12)}
            c.wiki_source = ''
        dump_out = open(args.output_file, 'w')
        pickle.dump(dump_in, dump_out)
        sys.exit()

    wiki_sub = None
    if args.wiki_sub is not None:
        logger.info('using wiki data from %s', args.wiki_sub)
        wiki_sub = {'{}/{}/{}'.format(x.name, x.region, x.country): x for x in
                    pickle.load(open(args.wiki_sub))}


    timer = Timer(len(dump_in))
    new_data = []
    nb_no_wiki = 0
    nb_no_climate = 0
    nb_coords_from_wiki = 0
    nb_coords_from_geonames = 0
    for i, city in enumerate(dump_in):
        timer.update()
        if args.max_cities is not None and i+1 > args.max_cities:
            break
        logger.debug(city)

        if wiki_sub is not None:
            city_id = '{}/{}/{}'.format(city.name, city.region, city.country)
            if city_id in wiki_sub:
                other_city = wiki_sub[city_id]
                city.coords = other_city.coords
                city.month_stats = other_city.month_stats
                city.wiki_source = other_city.wiki_source
                new_data.append(city)
            continue

        got_wiki = False
        for potential_page in [city.name + ', ' + city.region,
                               city.name + ', ' + city.country]:
            # should we also be looking for `city.name` by itself?
            try:
                page = wiki.page(potential_page)
                got_wiki = True
                break
            except wiki.PageError:
                # logger.info('didn\'t find wiki page "%s"', potential_page)
                pass
            except wiki.exceptions.DisambiguationError:
                pass
                # logger.info('landed on disambiguation for page "%s"',
                #                  potential_page)
                # logger.exception()
            except Exception:
                logger.info('unhandled exception while looking for wiki page'
                            ' "%s"', potential_page)
                logger.exception()
                continue

        if not got_wiki:
            logger.info('didn\'t find a page for city %s', city)
            nb_no_wiki += 1
            continue

        html = page.html()
        climate_data = parse_climate_table(html)
        if climate_data is None:
            logger.debug('no climate table for %s', city)
            nb_no_climate += 1
            continue
        climate_data = parse_data(climate_data)

        # because the wikipedia library crashes there sometimes
        try:
            coords = page.coordinates
        except KeyError:
            coords = None

        if coords is not None:
            coords = [float(x) for x in coords]
            nb_coords_from_wiki += 1
        else:
            coords = city.coords
            nb_coords_from_geonames += 1

        city.month_stats = climate_data
        city.wiki_source = page.url
        city.coords = coords

        new_data.append(city)

    # pprint(new_data)
    # for city in new_data:
        # print(city)
        # pprint(city.month_stats)
        # print(city.wiki_source)

    logger.info('got %i cities', len(new_data))
    logger.info('skipped %i cities with no wikipedia page', nb_no_wiki)
    logger.info('skipped %i cities with no climate table', nb_no_climate)
    logger.info('got %i coordinates from the wikipedia API',
                nb_coords_from_wiki)
    logger.info('got %i coordinates from dbpedia',
                nb_coords_from_geonames)
    dump_out = open(args.output_file, 'w')
    pickle.dump(new_data, dump_out)
