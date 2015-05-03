import sys, gzip, pickle, argparse, time
from urllib.error import URLError
from pprint import pprint
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import defaultdict
from meteomap.utils import Timer, open, ask_before_overwrite


def sparql_query(sparql, q, limit=None, batch=1000):
    """
        will do several LIMIT `batch` OFFSET X calls
        assuming sparql.setReturnFormat(JSON) has been called
    """
    if limit is not None and limit < batch:
        batch = limit
    i = 0
    returned = 0
    while True:
        sparql.setQuery(q + ' LIMIT {} OFFSET {}'.format(batch, i*batch))
        try:
            results = sparql.query().convert()['results']['bindings']
        except URLError as e:
            print(e)
            time.sleep(.5)
        for r in results:
            yield r
            returned += 1
            if limit is not None and returned >= limit:
                return
        if len(results) == 0:
            break
        i+=1
    return


def clean_minuses(x):
    return x.replace('−', '-').replace('&minus;', '-')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='fetch the data from dbpedia')
    parser.add_argument('output_file', help='file where to dump the data')
    args = parser.parse_args()
    output = args.output_file
    if not ask_before_overwrite(output):
        sys.exit()

    sparql = SPARQLWrapper('http://dbpedia.org/sparql')
    sparql.setReturnFormat(JSON)
    # nb_cities = int(query(sparql,
    #     """
    #     PREFIX dbo: <http://dbpedia.org/ontology/>
        # PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        # PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

    #     SELECT (count(?city) as ?count)
    #     WHERE {
    #         ?city a dbo:City.
    #         ?city geo:lat ?lat.
    #         ?city geo:long ?long}
    #     """
    # )[0]['count']['value'])

    # print('Expecting', nb_cities, 'cities')

    print('getting all the cities')
    cities = list(sparql_query(sparql,
        """
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

        SELECT ?city AVG(?lat) as ?lat AVG(?long) as ?long
        WHERE {
          ?city a dbo:City.
          ?city geo:lat ?lat.
          ?city geo:long ?long. }
        GROUP BY $city
        """, limit=1e9))
    print('got', len(cities))

    def f():
        return defaultdict(list)
    cities_dict = defaultdict(f)

    for c in cities:
        city = c['city']['value']
        lat = c['lat']['value']
        lon = c['long']['value']
        cities_dict[city]['lat'] = lat
        cities_dict[city]['long'] = lon

    timer = Timer(len(cities))

    for city in cities_dict.keys():
        # get the properties of the city
        results = sparql_query(sparql,
            """
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

            SELECT ?p ?o
            WHERE {{
                <{}> ?p ?o.
                FILTER(
                    (regex(?p, "population", "i") ||
                        regex(?p, "elevation", "i") ||
                        regex(?p, "/jan.+") ||
                        regex(?p, "/feb.+") ||
                        regex(?p, "/mar.+") ||
                        regex(?p, "/apr.+") ||
                        regex(?p, "/may.+") ||
                        regex(?p, "/jun.+") ||
                        regex(?p, "/jul.+") ||
                        regex(?p, "/aug.+") ||
                        regex(?p, "/sep.+") ||
                        regex(?p, "/oct.+") ||
                        regex(?p, "/nov.+") ||
                        regex(?p, "/dec.+"))
                )
            }}
            """.format(city))

        for c in results:
            att = c['p']['value']
            val = c['o']['value']
            # some negative values are weird
            val = clean_minuses(val)
            cities_dict[city][att].append(val)

        timer.update()

    # pprint(cities_dict)

    with open(output, 'w') as f:
        pickle.dump(dict(cities_dict), f)
