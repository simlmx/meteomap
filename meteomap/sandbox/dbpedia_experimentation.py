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
    query_and_print(sparql,
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
          {{ ?city a dbo:City }
              UNION { ?city a yago:City108524735}
              UNION { ?city a yago:Capital108518505}}.
          ?city geo:lat ?lat.
          ?city geo:long ?long.
          ?city prov:wasDerivedFrom ?source.
          ?city ?p ?pop.
          FILTER(regex(?p, "population", "i") &&
                 isNumeric(?pop))
          OPTIONAL { ?city dbp:name ?name }
        }
        GROUP BY $city
        HAVING(MAX(?pop) > 10)
        """)
