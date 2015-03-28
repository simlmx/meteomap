import sys, gzip, pickle
from pprint import pprint
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import defaultdict
from meteomap.utils import Timer, open


def query(sparql, q, limit=None, batch=1000):
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
        results = sparql.query().convert()['results']['bindings']
        for r in results:
            yield r
            returned += 1
            if limit is not None and returned >= limit:
                return
        if len(results) == 0:
            break
        i+=1
    return






if __name__ == '__main__':
    #arg 1 : file to dump the data to
    output = sys.argv[1]

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
    cities = list(query(sparql,
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

    for i,city in enumerate(cities_dict.keys()):
        # get the properties of the city
        results = query(sparql,
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
            #FIXME
            raise NotImplementedError('replace the weird "−" with a real "-"'
                                      'so that we can easily parse the negative'
                                      'numbers later')
            # same for &minus;1.6'-> -1.6
            # remove the ugly code to fix those in the load_database.py code
            # when this is fixed

            cities_dict[city][att].append(val)

        timer.update(i)

    f = open(output, 'w')
    try:
        pickle.dump(dict(cities_dict), f)
    finally:
        f.close()
    pprint(cities_dict)
