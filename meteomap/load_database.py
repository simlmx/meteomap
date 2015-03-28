""" This script cleans the data we got from dbpedia and inserts it in the
    database
"""
import sys, pickle, datetime, re
from pprint import pprint
from numpy import mean
from meteomap.utils import open

PROPERTY = 'http://dbpedia.org/property/'
ONTOLOGY = 'http://dbpedia.org/ontology/'

IGNORE = [re.compile(x) for x in [
    PROPERTY + 'population.*Density.*',
    ONTOLOGY + 'population.*Density.*',
    PROPERTY + 'population.*Rank.*',
    ONTOLOGY + 'population.*Rank.*',
    ONTOLOGY + 'PopulatedPlace/population.*Density',
    PROPERTY + 'populationBlank.Title',
    PROPERTY + '.*AsOf',
    ONTOLOGY + '.*AsOf',
    PROPERTY + 'populationDemonym',
    PROPERTY + 'mayor',
    ONTOLOGY + 'mayor',
    PROPERTY + '.*Footnotes',
    PROPERTY + 'populationNote',
    PROPERTY + 'populationCombinedStatisticalArea',
    PROPERTY + '\d{4}Population',
    PROPERTY + 'populationDowntown',
    PROPERTY + 'populationRef',
    PROPERTY + 'populationDate',
    PROPERTY + 'populationEstimate',
    PROPERTY + 'populationCityProper',
    PROPERTY + 'populationCsa',
    PROPERTY + 'urbanPopulation',
    PROPERTY + 'populationMicro',
    PROPERTY + 'marcordLowC',  # this one seems a typo
    PROPERTY + 'populationSexRatio',
    PROPERTY + 'elevationRound',
    PROPERTY + 'populationEnumeratedPeople',
    PROPERTY + 'populationGrowthrate',
    PROPERTY + 'populationTotalType',
    PROPERTY + 'populationMentro',  # typo?
    PROPERTY + 'populationTribal',
    PROPERTY + 'populationCounty',
    PROPERTY + 'mark',
    PROPERTY + 'marksize',
    PROPERTY + 'populationGrowth',
    PROPERTY + 'populationFemales',
    PROPERTY + 'populationMales',
    PROPERTY + 'populationMale',
    PROPERTY + 'populationFemale',
    PROPERTY + 'proportionToAndhraPradeshPopulation',
    PROPERTY + 'populationInternational',
    PROPERTY + 'populationMetrorank',
    PROPERTY + 'populationDenonym',
    PROPERTY + 'populationCityRegion',
    PROPERTY + 'populationChangeSince',
    PROPERTY + 'populationGentilic',
    PROPERTY + 'populationPrincetonArea',
    PROPERTY + 'populationMetroKm',
    PROPERTY + 'metropolitanAreaPopulation',
    PROPERTY + 'populationHousehold',
    PROPERTY + 'populationUrbanKm',
    PROPERTY + 'populationDistrict',
    PROPERTY + 'populationTotal[(]city[)]_',
    PROPERTY + 'populationMostBeautifulThing',
    PROPERTY + 'deconRehab',
    PROPERTY + 'populationComb.Metro',
    PROPERTY + 'populationTotal[(]2011[)]_',
    PROPERTY + 'populationYear',
    PROPERTY + '[a-z]{3}Humidity%25_',
]]

def feet2meter(f):
    return f * 0.3048

def inch2mm(i):
    return i * 25.4

def inch2cm(i):
    return i * 2.54

def nothing(x):
    return x

def f2c(f):
    """ fareneith to celcius """
    return (f - 32)/1.8


class KeysParsingRule(object):
    def __init__(self, keys, parsing_fn=None, agg=mean):
        if isinstance(keys, str):
            keys = (keys,)
        self.keys = keys
        if parsing_fn is None:
            def parsing_fn(x):
                return x
        self.parsing_fn = parsing_fn
        self.agg = agg

    def find_keys_in(self, data):
        """ Check if this parsing rule matches something in the data
            and if yes returns it
        """
        values = []
        # we need to find all the `k` in `keys`
        got_all_current_keys = True
        for k in self.keys:
            if k in data:
                values.append(data[k])
            else:
                got_all_current_keys = False

        if not got_all_current_keys:
            return None
        else:
            def str_parse(x):
                return float(x.replace('−', '-').replace('&minus;', '-'))
            try:
                values = [[str_parse(x) for x in y] for y in values]
            except ValueError:
                print('this should not happen often, right?')
                return None
            values = [[self.parsing_fn(x) for x in y] for y in values]
            agg1 = [self.agg(x) for x in values]
            agg2 = self.agg(agg1)
            # I'm rounding to the nearest unit, is that wise?
            return round(agg2)

    def clear_keys_in(self, data):
        """ Clear our self.keys in data
        """
        for k in self.keys:
            # print('trying to clear', k)
            if k in data:
                # print('   worked')
                data.pop(k)


def get_generic(city_data, keys_and_parsing, clear_keys=True):
    """ Not only gets the city_data but **clears** (if `clear_keys` is True)
        the wanted keys in `city_data`. This is so that we can look at what
        was not used afterwards.
    """

    if isinstance(keys_and_parsing, KeysParsingRule):
        keys_and_parsing = [keys_and_parsing]

    for keys in keys_and_parsing:
        value = keys.find_keys_in(city_data)
        if value is not None:
            break

    if clear_keys:
        for k in keys_and_parsing:
            k.clear_keys_in(city_data)

    return value


ELEVATION_KEYS = [
    ONTOLOGY + 'elevation',
    (ONTOLOGY + 'maximumElevation', ONTOLOGY + 'minimumElevation'),
    ONTOLOGY + 'maximumElevation',
    ONTOLOGY + 'minimumElevation',
    PROPERTY + 'elevation',
    PROPERTY + 'elevationM',
    PROPERTY + 'avgElevation',
    (PROPERTY + 'elevationMax', PROPERTY + 'elevationMin'),
    (PROPERTY + 'elevationMaxM', PROPERTY + 'elevationMinM'),
    (PROPERTY + 'elevationMMin', PROPERTY + 'elevationMMax'),
    PROPERTY + 'elevationMax',
    PROPERTY + 'elevationMin',
    ((PROPERTY + 'elevationFt',), feet2meter),
    ((PROPERTY + 'elevationF',), feet2meter),
    ((PROPERTY + 'elevationImperial',), feet2meter),
    ((PROPERTY + 'elevationMaxFt', PROPERTY + 'elevationMinFt'), feet2meter),
    ((PROPERTY + 'elevationMaxFt', PROPERTY + 'elevationMinFt'), feet2meter),
    (PROPERTY, 'highestElevationImperial') # FIXME
]


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


def format_key(k):
    """ so we can use keys like
            'x'
            ('x', 'y')
            (('x', 'y'), fn) <-- they all become like this
    """
    # make sure we have something that looks like (('a', 'b'), fn)
    if isinstance(k, str):
        k = ((k,), (lambda x:x))
    elif isinstance(k[0], str):
        k = (k, lambda x:x)
    # we assume that if it's not a simple string, it's already
    # in the right format
    return k[0], k[1]


def get_elevation(city_data):
    keys = [KeysParsingRule(*format_key(k)) for k in ELEVATION_KEYS]
    return get_generic(city_data, keys)


def get_population(city_data):
    keys = [KeysParsingRule(*format_key(k)) for k in POP_KEYS]
    return get_generic(city_data, keys)


def get_month_stats(city_data):
    months = ['{:%b}'.format(datetime.datetime(2000, i+1, 1)).lower()
              for i in range(12)]
    mapping = {'avgHigh': ['HighC', 'High', (('HighF',), f2c)],
               'avgLow': ['LowC', 'Low', (('LowF',), f2c)],
               'highHumidex': ['HighHumidex', 'MaximumHumidex'],
               'chill': ['Chill'],
               'dailyMean' : ['MeanC', (('MeanF',), f2c), 'DailyMean'],
               'sun': ['Sun', 'dSun', 'Sol'],
               'percentSun': ['Percentsun'],
               'recordHigh': ['RecHigh', 'RecordHighC', (('RecordHighF',), f2c)],
               'recordLow': ['RecLow', 'RecordLowC', (('RecordLowF',), f2c)],
               'rain': ['RainMm',
                        (('RainCm',), lambda x: x*10.),
                        (('RainInch',), inch2mm)],
               'snow': ['SnowCm', 'SnowFall', 'SnowfallCm', 'Snowfall',
                        (('SnowfallMm',), lambda x: x/10.),
                        (('SnowInch',),inch2cm),
                        (('SnowfallInch',), inch2cm)],
               'precipitation': ['PrecipitationMm',
                                 (('PrecipitationCm',), lambda x: x*10.),
                                 (('PrecipitationInch',), inch2mm),
                                 'Mm'],
               'rainDays': ['RainDays', 'RanDays'],
               'snowDays': ['SnowDays'],
               'precipitationDays': ['PrecipitationDays'],
               'humidity': ['Humidity']}

    month_stats = {m:{} for m in months}
    for month in months:
        for k, vs in mapping.items():
            kprs = []
            for v in vs:
                v, parsing_fn = format_key(v)
                for prefix in [PROPERTY, ONTOLOGY]:
                    new_v = [prefix + month + x for x in v]
                    kprs.append(KeysParsingRule(new_v, parsing_fn))
                    # super hack
                    if month == 'sep':
                        new_v2 = [prefix + 'sept' + x for x in v]
                        kprs.append(KeysParsingRule(new_v2, parsing_fn))
            value = get_generic(city_data, kprs)
            if value is not None:
                month_stats[month][k] = value
    return month_stats


if __name__ == '__main__':
    nb_no_elevation = 0
    nb_no_pop = 0
    nb_no_month_stats = 0
    # arg 1 : file to open
    city_data = pickle.load(open(sys.argv[1]))
    # city_data = {'http://dbpedia.org/resource/Surakarta': city_data['http://dbpedia.org/resource/Surakarta']}
    filtered_cities = {}
    not_found = []
    for city, data in city_data.items():
        filtered_city = {}
        name = city.split('/')[-1]
        # latitude / longitude
        filtered_city['lat'] = data.pop('lat')
        filtered_city['long'] = data.pop('long')

        # remove keys we want to ignore
        for k in list(data.keys()):
            for regex in IGNORE:
                if regex.match(k):
                    # print('  removing', k, 'from', city)
                    # print('   using', regex.pattern)
                    data.pop(k)
                    break
                    # break
                # else:
                #     print('  ', k, 'not match', regex.pattern)

        # elevation
        filtered_city['elevation'] = get_elevation(data)
        # if el is None:
        #     nb_no_elevation += 1
            # for k in data:
            #     if 'elevation' in k.lower() or 'altitude' in k.lower():
            #         print(city)
            #         print('  ', k, data[k])

        filtered_city['population'] = get_population(data)
        # if pop is None:
        #     nb_no_pop += 1
        #     for k in data:
        #         if 'population' in k.lower() and \
        #                 'populationasof' not in k.lower() and \
        #                 'density' not in k.lower():
        #             print(city)
        #             print('  ', k, data[k])

        filtered_city['month_stats'] = get_month_stats(data)

        if filtered_city['population'] is not None \
                and len(filtered_city['month_stats']['jan']) > 0:
            print('YAY')
            filtered_cities[name] = filtered_city
            print(name)
            pprint(filtered_city)

        if len(data) > 0:
            print(name)
            print('DATA REMAINING - everything should be deliberately ignored'
                  ' or considered')
            for k in data:
                not_found.append(k)
            pprint(data)
            assert False

    for k in not_found:
        sp = k.split('/')
        name = sp[-1]
        cat = sp[-2]
        if cat not in ['ontology', 'property']:
            print("{} + '{}/{}',".format(sp[-3].upper(), sp[-2], sp[-1]))
        else:
            print("{} + '{}',".format(sp[-2].upper(), sp[-1]))

    # print('no elevation', nb_no_elevation)
    # print('no population', nb_no_pop)
    # print('no month stats', nb_no_month_stats)
