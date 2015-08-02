import sys, argparse, csv, pickle, logging
from pprint import pprint
from meteomap.utils import Timer, open, ask_before_overwrite, configure_logging
from meteomap.city import City, distance
from collections import defaultdict

logger = logging.getLogger(__name__)


def _add_rank(cities_per_cat, catname):
    """ util for add_region_index and add_country_index """
    for cat, cities in cities_per_cat.items():
        sorted_cities = sorted(cities, key=lambda x: x.pop, reverse=True)
        for i,c in enumerate(sorted_cities):
            setattr(c, catname + '_rank', i)


def add_region_rank(cities_per_region):
    """ add an region_rank field to cities """
    _add_rank(cities_per_region, 'region')


def add_country_rank(cities_per_country):
    """ add an country_rank field to cities """
    _add_rank(cities_per_country, 'country')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='fetch the data from a'
                                     ' country file from geonames.org or from'
                                     ' their allCountries.zip file')
    parser.add_argument('input_file', help='geonames.org file (zipped or not)')
    parser.add_argument('output_file', help='file where to dump the data')
    parser.add_argument('--min-pop', default=500, help='minimum population to'
                        ' keep the city', type=int)
    parser.add_argument('--admin1codes-file', help='admin1CodesASCII.txt'
                        ' from geonames.org', required=True)
    parser.add_argument('--country-infos-file', help='countryInfo.txt'
                        ' from geonames.org', required=True)
    parser.add_argument('--force', action='store_true', help='don\'t ask'
                        ' before overwriting the output file')
    parser.add_argument('--max-cities', '-m', type=int)
    parser.add_argument('--too-close', type=float, default=25., help='a city'
                       ' will be ignored if there is a bigger city closer than'
                       ' this radius')
    args = parser.parse_args()

    configure_logging()

    output = args.output_file
    if not (args.force or ask_before_overwrite(output)):
        sys.exit()

    fields = ['country_region', 'name', 'asciiname', 'geonameid']
    regions = defaultdict(dict)
    with open(args.admin1codes_file) as f:
        reader = csv.DictReader(f, delimiter='\t', fieldnames=fields)
        for row in reader:
            country, region = row['country_region'].split('.')
            if region in regions[country]:
                raise Exception('A region is present twice in the file')
            regions[country][region] = row['name']
    # pprint(regions)

    countries = {}
    with open(args.country_infos_file) as f:
        reader = csv.reader((line for line in f if not line.startswith('#')),
                            delimiter='\t')
        for row in reader:
            countries[row[0]] = row[4]
    # pprint(countries)

    timer = Timer()

    fields = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude',
             'longitude', 'feature class', 'feature code', 'country code',
             'cc2', 'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code',
             'population', 'elevation', 'dem', 'timezone', 'modification date']

    logger.info('reading the data')
    cities = defaultdict(lambda : defaultdict(dict))
    nb_cities_kept = 0
    with open(args.input_file) as f:
        reader = csv.DictReader(f, delimiter='\t', fieldnames=fields,
                                quoting=csv.QUOTE_NONE)
        for i,city in enumerate(reader):
            # has to be a populated place
            if city['feature class'] != 'P':
                continue

            population = int(city['population'])

            # enough people or a special place
            enough_people = population > args.min_pop
            special_place = city['feature code'] in ['PPLA', 'PPLA2',
                'PPLC', 'PPLCH', 'PPLG', 'PPLH']

            if not (enough_people or special_place):
                continue

            # let's just keep what we need
            country_code = city['country code']
            if country_code not in regions:
                # logger.info(city)
                logger.info('country code "%s" not in our list', country_code)
                region = 'no region'
            elif city['admin1 code'] not in regions[country_code]:
                # logger.info(city)
                logger.info('region code "%s" for country "%s" not in our'
                             ' list: %s', city['admin1 code'], country_code,
                             str(list(regions[country_code].keys())))
                region = 'no region'
            else:
                region = regions[country_code][city['admin1 code']]
            country = countries[country_code]
            name = city['name']
            new_city = City(
                name = name,
                country = country,
                region = region,
                coords = (float(city['latitude']), float(city['longitude'])),
                modif_date = city['modification date'],
                pop = population,
                feature = city['feature code'],
            )

            # if unique_id in cities:
            keep_this_city = True
            if name in cities[country][region]:
                other_city = cities[country][region][name]
                other_date = other_city.modif_date
                this_date = new_city.modif_date
                if other_date == this_date:
                    logger.debug('duplicate city %s', name)
                    keep_this_city = False
                elif this_date > other_date:
                    keep_this_city = True
                else:
                    keep_this_city = False
            if keep_this_city:
                cities[country][region][name] = new_city
                nb_cities_kept += 1

            if args.max_cities is not None \
                    and nb_cities_kept >= args.max_cities:
                break
            timer.update()

    # pprint(cities)

    logger.info('removing cities close to a bigger city')
    timer = Timer(nb_cities_kept)
    cities_to_remove = set()
    for country, regions in cities.items():
        for region, cs in regions.items():
            cs = list(cs.values())
            # It's simpler if they are in decreasing order of population
            cs = sorted(cs, key=lambda x: x.pop, reverse=True)
            for i, city in enumerate(cs):
                for j in range(0, i):
                    city2 = cs[j]
                    # Here `city2` is bigger `city`
                    # If it's close and has not been flagged for deletion, we
                    # will remove `city`
                    if (country, region, city2.name) not in cities_to_remove \
                            and distance(city, city2) < args.too_close:
                        logger.debug('removing %s, too close to %s',
                                    city.name, city2.name)
                        cities_to_remove.add((country, region, city.name))
                        break
                timer.update()

    for country, region, city in cities_to_remove:
        del cities[country][region][city]

    # flatten the cities
    cities_flat = []
    cities_per_region = defaultdict(list)
    cities_per_country = defaultdict(list)
    for country, regions in cities.items():
        for region, cs in regions.items():
            for city in cs.values():
                cities_flat.append(city)
                cities_per_region[region].append(city)
                cities_per_country[country].append(city)

    cities = cities_flat
    # pprint(cities)
    # pprint(cities_per_region)
    # pprint(cities_per_country)

    add_region_rank(cities_per_region)
    add_country_rank(cities_per_country)

    logger.info('ended up with %i cities', len(cities_flat))

    with open(output, 'w') as f:
        pickle.dump(cities_flat, f)
