import sys, pickle, argparse, time
from urllib.error import URLError
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import defaultdict
from meteomap.utils import Timer, open, ask_before_overwrite, configure_logging


def sparql_query(sparql, q, limit=None, batch=1000):
    """
        will do several LIMIT `batch` OFFSET X calls
        assuming sparql.setReturnFormat(JSON) has been called
    """
    if limit is not None and limit < batch:
        batch = limit
    i_batch = 0
    nb_returned = 0
    while True:
        sparql.setQuery(q + ' LIMIT {} OFFSET {}'.format(batch, i_batch*batch))
        try:
            results = sparql.query().convert()['results']['bindings']
        except URLError as e:
            print(e)
            time.sleep(.5)
        for r in results:
            yield r
            nb_returned += 1
            if limit is not None and nb_returned >= limit:
                return
        if len(results) == 0:
            break
        i_batch += 1
    return


def clean_minuses(x):
    return x.replace('−', '-').replace('&minus;', '-')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='fetch the data from dbpedia')
    parser.add_argument('output_file', help='file where to dump the data')
    parser.add_argument('--min-pop', default=1e5, help='minimum population to'
                        ' keep the city (if there are multiple population'
                        ' fields, we keep the maximum)')
    parser.add_argument('--max-cities', '-m', type=int)
    args = parser.parse_args()

    configure_logging()

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
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX yago: <http://dbpedia.org/class/yago/>

        SELECT ?city
               AVG(?lat) as ?lat AVG(?long) as ?long
               MIN(?source) as ?source
               MAX(?pop) as ?maxpop
               MIN(?name) as ?name

        WHERE {
          # ?city a dbo:Settlement.
          {{ ?city a dbo:City } UNION { ?city a yago:City108524735}}.
          ?city geo:lat ?lat.
          ?city geo:long ?long.
          ?city prov:wasDerivedFrom ?source.
          ?city ?p ?pop.
          FILTER(regex(?p, "population", "i") &&
                 isNumeric(?pop))
          OPTIONAL { ?city dbp:name ?name }
        }
        GROUP BY $city
        HAVING(MAX(?pop) > %i)
        """ % args.min_pop , limit=args.max_cities))
    print('got', len(cities))

    def f():
        return defaultdict(list)
    cities_dict = defaultdict(f)

    for c in cities:
        city = c['city']['value']
        for k in c.keys():
            cities_dict[city][k] = c[k]['value']

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
                    regex(?p, "population", "i") ||
                    regex(?p, "elevation", "i"))
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
