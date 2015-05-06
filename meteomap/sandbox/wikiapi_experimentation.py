import requests

from SPARQLWrapper import SPARQLWrapper, JSON
from meteomap.fetch_dbpedia import sparql_query


def query(**request):
    request['action'] = 'query'
    request['format'] = 'json'
    lastContinue = {'continue': ''}
    while True:
        # Clone original request
        req = request.copy()
        # Modify it with the values returned in the 'continue' section of the last result.
        req.update(lastContinue)
        # Call API
        result = requests.get('http://en.wikipedia.org/w/api.php', params=req).json()
        if 'error' in result:
            raise Exception(result['error'])
        if 'warnings' in result:
            print(result['warnings'])
        if 'query' in result:
            yield result['query']
        if 'continue' not in result:
            break
        # if 'batchcomplete' in result:
        #     break
        lastContinue = result['continue']


def embeddedin(title, limit=500):
    for r in query(eititle=title, eilimit=limit, list='embeddedin'):
        if 'embeddedin' in r:
            for e in r['embeddedin']:
                yield e
        else:
            return


if __name__ == '__main__':

    sparql = SPARQLWrapper('http://dbpedia.org/sparql')
    sparql.setReturnFormat(JSON)
    # RENDU ICI : utiliser dbpedia pour verifier lequel de ceux qui utilisent
    # le shortcut template est le bon
    # en gros on peut faire une query du genre
    # select ?o
    # where { dbresource:"title" a ?o }
    # et regarder si y a un City

    cities = {}
    # find all the wikipedia pages using the "Weather box" template
    for result in embeddedin('Template:weather box'):
        origin_title = result['title']

        # if they are normal pages, all good
        if ':' not in origin_title:
            cities[origin_title] = origin_title
            continue

        # but they might be special pages we don't care about
        prefix, title = origin_title.split(':')
        if prefix.lower() in ['user', 'user talk', 'wikipedia', 'talk',
                              'wikipedia talk', 'draft', 'module',
                              'template talk']:
            continue

        # this one is weird
        elif prefix == 'Template' and title == 'Weather box':
            print('ignoring weather box template itself...')
            continue

        # or it might be a case of nested templates
        elif prefix == 'Template':
            # TODO : going only one sublevel down, "we need to go deeper"?
            subres = [x['title'] for x in embeddedin(origin_title)]
            found = False
            print(origin_title)
            for x in subres:
                print(' check for', x)
                if ':' in x:
                    print(' uh oh')
                sparql.setQuery(
                    'ASK { <http://dbpedia.org/resource/%s> a'
                    ' <http://dbpedia.org/ontology/Settlement> }' % x.replace(' ', '_'))
                if sparql.query().convert()['boolean']:
                    found = True
                    cities[x] = origin_title
                    print('  [x] is a city', x, origin_title)
                    # break
                else:
                    print('  [ ] is not a city', x)
            # else:
        else:
            raise NotImplementedError(prefix)
    # print(cities)
    print(len(cities))
    print(len(set(cities)))
