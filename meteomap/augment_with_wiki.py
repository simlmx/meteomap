import re, sys, pickle, argparse, logging, time
from pprint import pprint
from itertools import count
import wikipedia as wiki
from bs4 import BeautifulSoup
from meteomap.utils import open, ask_before_overwrite, Timer, configure_logging
from Levenshtein import ratio

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
    bs = BeautifulSoup(html, 'html.parser')
    months = bs.find_all('th', text=re.compile(r'[\s]*Month[\s]*'))

    # if there is nothing, it means there were no climate table in that html
    # code
    if len(months) < 1:
        return {}

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
    parser.add_argument('--force', action='store_true', help='don\'t ask'
                        ' before overwriting the output file')
    parser.add_argument('--country', help='Will only look for cities in this'
                        ' country.')
    parser.add_argument('--region', help='Will only look for cities in this'
                        ' region.')
    parser.add_argument('--city', help='Will only look for that city.')
    parser.add_argument('--append', action='store_true', help='Will add'
                        ' unexisting cities to the already existing output'
                        ' file. Ignored if it doesn\'t exist.')
    parser.add_argument('--update-only', action='store_true',
                       help = 'We assume we already have cities in the output'
                        ' and we will only (re-)augment those, skipping all the'
                        ' others')
    parser.add_argument('--logging-level', choices =
                        ['debug', 'info', 'warning', 'error', 'critical'],
                        default='info')
    args = parser.parse_args()

    configure_logging(args.logging_level.upper())

    # validation of the passed arguments
    if args.append and args.update_only:
        raise Exception('can not use --append and --update-only at the'
                        ' same time')

    with open(args.input_file) as f:
        dump_in = pickle.load(f)

    if not (args.append or args.force or ask_before_overwrite(args.output_file)):
        sys.exit()

    if args.skip_wiki:
        logger.info('skipping wikipedia')
        for c in dump_in:
            c.month_stats = {'avgHigh': [0] * 12, 'precipitation': [0] * 12}
            c.wiki_source = ''
        with open(args.output_file, 'w') as dump_out:
            pickle.dump(dump_in, dump_out)
        sys.exit()

    if args.append or args.update_only:
        logger.info('updating in %s', args.output_file)
        with open(args.output_file) as f:
            new_data = {'{}/{}/{}'.format(x.name, x.region, x.country): x
                        for x in pickle.load(f)}
            logger.info('updating from %i cities', len(new_data))
    else:
        new_data = {}

    nb_cities_at_start = len(new_data)

    # print every 100
    def print_if(n):
        if n < 100:
            return Timer.default_print_if(n)
        else:
            return n % 100 == 0

    def keep_city(city):
        if (args.country is None or city.country == args.country) and \
                (args.region is None or city.region == args.region) and \
                (args.city is None or city.name == args.city):
            return True
        return False

    nb_cities = sum(1 for x in dump_in if keep_city(x))
    if args.max_cities is not None and args.max_cities < nb_cities:
        nb_cities = args.max_cities
    timer = Timer(nb_cities, print_if=print_if)
    nb_no_wiki = 0
    nb_no_climate = 0
    nb_already_there = 0
    nb_coords_from_wiki = 0
    nb_coords_from_geonames = 0
    nb_done = 0
    for city in dump_in:
        if args.max_cities is not None and nb_done >= args.max_cities:
            break
        if not keep_city(city):
            continue
        timer.update()
        logger.debug(city)

        city_id = '{}/{}/{}'.format(city.name, city.region, city.country)
        # if the city is already there
        if city_id in new_data:
            nb_already_there += 1
            if args.append:
                continue
        elif args.update_only:
            continue

        got_wiki = False
        got_climate = False
        for potential_page in [city.name + ', ' + city.country,
                               city.name + ', ' + city.region]:
            for essaie in count():
                # should we also be looking for `city.name` by itself?
                try:
                    page = wiki.page(potential_page)
                    # check that the title of the page makes sense, i.e. that
                    # we have the right page
                    title_lower = page.title.lower()
                    city_name_lower = city.name.lower()
                    title_ok = False
                    for comp in [city_name_lower, potential_page.lower(),
                                city_name_lower + ' municipality',
                                city_name_lower + ' city']:
                        rt = ratio(title_lower, comp)
                        logger.debug('ratio("%s", "%s") = %f',
                                     title_lower, comp, rt)
                        if rt > .8:
                            title_ok = True
                            break
                    if not title_ok:
                        break
                    got_wiki = True
                    html = page.html()
                    climate_data = parse_climate_table(html)
                    climate_data = parse_data(climate_data)
                    # this can happen if there is a table that looks like our
                    # table but isn't : we end up parsing 0 rows
                    if len(climate_data) == 0:
                        break
                    got_climate = True
                    break
                except wiki.PageError:
                    break
                except wiki.exceptions.DisambiguationError:
                    break
                except Exception:
                    logger.exception('unhandled exception while looking for wiki'
                                    'page "%s"', potential_page)
                    logger.info('sleeping %i seconds', essaie+1)
                    time.sleep(essaie+1)
            if got_climate:
                break

        nb_done += 1

        # if we were updating, we had a city that wasn't supposed to be there
        if not got_climate and args.update_only:
            del new_data[city_id]

        if not got_wiki:
            logger.info('did not find page for city %s, %s, %s'
                        % (city.name, city.region, city.country))
            nb_no_wiki += 1
            continue
        elif not got_climate:
            logger.info('did not find climate table for city %s, %s, %s'
                        % (city.name, city.region, city.country))
            nb_no_climate += 1
            continue

        for essaie in count():
            try:
                coords = page.coordinates
                break
            except KeyError:
                coords = None
                break
            except Exception:
                logger.exception('unhandled exception while looking for wiki'
                                 ' coords')
                logger.info('sleeping %i seconds', essaie+1)
                time.sleep(essaie+1)

        if coords is not None:
            coords = [float(x) for x in coords]
            nb_coords_from_wiki += 1
        else:
            coords = city.coords
            nb_coords_from_geonames += 1

        city.month_stats = climate_data
        city.wiki_source = page.url
        city.coords = coords

        new_data[city_id] = city

        logger.info('* Got data for city %s, %s, %s' % (city.name, city.region, city.country))

    logger.info('started with %i cities', nb_cities_at_start)
    logger.info('went threw %i new cities (%i were skipped because we already'
                ' had them)', nb_done, nb_already_there)
    logger.info('skipped %i cities with no wikipedia page', nb_no_wiki)
    logger.info('skipped %i cities with no climate table', nb_no_climate)
    logger.info('kept %i new cities', len(new_data) - nb_cities_at_start)
    logger.info('wrote a total of %i cities', len(new_data))
    logger.info('got %i coordinates from the wikipedia API',
                nb_coords_from_wiki)
    logger.info('got %i coordinates from geonames',
                nb_coords_from_geonames)
    with open(args.output_file, 'w') as dump_out:
        pickle.dump(list(new_data.values()), dump_out)
