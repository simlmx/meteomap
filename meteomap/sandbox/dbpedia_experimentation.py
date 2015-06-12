import sys
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
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbp: <http://dbpedia.org/property/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        PREFIX yago: <http://dbpedia.org/class/yago/>


        SELECT ?city
               AVG(?lat) as ?lat AVG(?long) as ?long
               MIN(?source) as ?source
               MAX(?pop) as ?maxpop
               MIN(?name) as ?name
               MIN(?set_type) as ?set_type

        WHERE {
          {{ ?city a dbo:City } UNION { ?city a yago:City108524735}}.
          ?city geo:lat ?lat.
          ?city geo:long ?long.
          ?city prov:wasDerivedFrom ?source.
          ?city ?p ?pop.
          FILTER(regex(?p, "population", "i") &&
                 isNumeric(?pop))
          OPTIONAL { ?city dbp:name ?name }
          OPTIONAL { ?city dbp:settlementType ?set_type }
        }
        GROUP BY $city
        HAVING(MAX(?pop) > 1000000)
        LIMIT 100
        """)

    sys.exit()

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
                # {{?city a dbo:Citytv}} UNION {{?city a dbo:City}}.
                ?city a dbo:Settlement.
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
