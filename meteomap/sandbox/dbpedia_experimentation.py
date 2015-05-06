from SPARQLWrapper import SPARQLWrapper, JSON
from collections import defaultdict
from pprint import pprint

def query_and_print(sparql, query):
    """ small util """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    for x in results['results']['bindings']:
        print('---------------')
        pprint(x)
    return results['results']['bindings']



if __name__ == '__main__':
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    query_and_print(sparql,"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

            SELECT count(?city)
            # WHERE {{ ?city a dbo:City} UNION { ?city dbo:type dbo:Citytv}}
            # WHERE {?city a dbo:City}
            WHERE {?city a dbo:City}
            """)

    cities_dict = defaultdict(lambda : {})
    batch = 1000
    i = 0
    results = [None]
    while len(results) > 0:
        results = query_and_print(sparql, """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

            SELECT ?city ?lat ?long ?p ?o
            WHERE {{
                {{?city a dbo:Citytv}} UNION {{?city a dbo:City}}.
                ?city ?p ?o.
                ?city geo:lat ?lat.
                ?city geo:long ?long.
                FILTER(
                    (regex(?p, ".?population.?") ||
                     regex(?p, "elevation.?") ||
                     regex(?p, "jan.+") ||
                     regex(?p, "feb.+") ||
                     regex(?p, "mar.+") ||
                     regex(?p, "apr.+") ||
                     regex(?p, "may.+") ||
                     regex(?p, "jun.+") ||
                     regex(?p, "jul.+") ||
                     regex(?p, "aug.+") ||
                     regex(?p, "sep.+") ||
                     regex(?p, "oct.+") ||
                     regex(?p, "nov.+") ||
                     regex(?p, "dec.+")) &&
                    (datatype(?o) = xsd:integer ||
                     datatype(?o) = xsd:float)
                )
            }}
            # ORDER BY $city
            LIMIT {}
            OFFSET {}
            """.format(batch, i*batch))
        i+=1

        for c in results:
            city = c['city']['value']
            att = c['p']['value']
            val = c['o']['value']
            cities_dict[city][att] = val

        pprint(cities_dict)
        print(len(cities_dict))




    # query_and_print("""
        # PREFIX owl: <http://www.w3.org/2002/07/owl#>
    #     PREFIX dbo: <http://dbpedia.org/ontology/>
    #     PREFIX dbp: <http://dbpedia.org/property/>

    #     SELECT ?city ?p ?o
    #     WHERE {
    #         ?city a dbo:City.


