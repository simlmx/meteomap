import re, sys
from bs4 import BeautifulSoup
import wikipedia


def get_first_number(x):
    return float(re.search('^[\d.-]+', x).group())


def get_second_number(x):
    """ actually gets the number in the parentheses """
    match = re.search('[(][\d.-]+[)]', x).group()
    return float(match[1:-1])


ROW_PARSERS = {
    'Record high °C (°F)': ('recordHigh', get_first_number),
    'Record high °F (°C)': ('recordHigh', get_second_number),
    'Average high °C (°F)': ('avgHigh', get_first_number),
    'Average high °F (°C)': ('avgHigh', get_second_number),
    'Daily mean °C (°F)': ('avg', get_first_number),
    'Daily mean °F (°C)': ('avg', get_second_number),
    'Average low °C (°F)': ('avgLow', get_first_number),
    'Average low °F (°C)': ('averageLow', get_second_number),
    'Record low °C (°F)': ('recordLow', get_first_number),
    'Record low °F (°C)': ('recordLow', get_second_number),


    'Mean monthly sunshine hours': ('monthlySunHours', float),
    # TODO this is redundant. somes cities like Perth have both but IMHO it's a
    # bit stupid...
    'Mean daily sunshine hours': ('dailySunHours', float),

    'Avg. precipitation days (≥ 0.1 mm)': ('precipitationDays', float),
    'Avg. precipitation days (≥ 0.2 mm)': ('precipitationDays', float),
    'Avg. precipitation days (≥ 0.01 in)': ('precipitationDays', float),
    'Avg. precipitation days': ('precipitationDays', float),

    'Average precipitation mm (inches)': ('precipitation', get_first_number),
    'Average precipitation inches (mm)': ('precipitation', get_second_number),

    'Avg. rainy days (≥ 0.2 mm)': ('rainDays', float),
    'Average rainfall mm (inches)' : ('rain', get_first_number),

    'Avg. snowy days (≥ 0.1 in)': ('snowDays', float),
    'Avg. snowy days (≥ 0.2 cm)': ('snowDays', float),
    'Average snowfall cm (inches)': ('snow', get_first_number),
    'Average snowfall inches (cm)': ('snow', get_second_number),

    'Record high humidex': ('humidex', float),
    'Record low wind chill': ('chill', float),
    'Percent possible sunshine': ('percentSun', float),

    'Average relative humidity (%)': ('humidity', float),
}


def parse_climate_table(html):
    """ returns somethings like
        {'average temp C (F)' : ['12 (13)', ..., '12 (13)']
         ... }
    """
    bs = BeautifulSoup(html)
    months = bs.find_all('th', text=re.compile(r'[\s]*Month[\s]*'))
    # print(months)
    assert len(months) >= 1
    if len(months) > 1:
        print('warning, more than one matching table... taking the first')
    table = months[0].parent.parent
    # print(table)
    data = {}
    for tr in table.find_all('tr'):
        ths = tr.find_all(['th','td'])
        if len(ths) != 1 + 12 + 1:
            continue
        # print('--------------')
        # print(ths[0].get_text().strip())
        title = ths[0].get_text().strip()
        if title == 'Month':
            continue
        data[title] = [ths[i].get_text().strip().replace('−', '-') for i in range(1,13)]
    return data


def parse_data(climate_data):
    """ refines again the output of parse_climate_table(...) """
    out = {}
    for title, data in climate_data.items():
        try:
            key, parse_fn = ROW_PARSERS[title]
        except KeyError:
            print("no parser for key '%s'" % title)
            continue
        # each thing should be there only once!
        assert key not in out
        try:
            out[key] = [parse_fn(x) for x in data]
        except ValueError:
            print('not able to parse one of those values:', data,
                  '\nfor ', title)
            continue
    return out


if __name__ == '__main__':
    cities = sys.argv[1:]
    # essaie 1
    for city in cities:
        v = wikipedia.WikipediaPage(city)
        data = parse_climate_table(v.html())
        parsed_data = parse_data(data)
        print(parsed_data)
