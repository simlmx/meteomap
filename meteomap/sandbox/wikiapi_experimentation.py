import requests, sys

from SPARQLWrapper import SPARQLWrapper, JSON
from meteomap.fetch_dbpedia import sparql_query


def coordinate_query(**request):
    request['action'] = 'query'
    request['prop'] = 'coordinates'
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
        lastContinue = result['cocontinue']


if __name__ == '__main__':
    print(sys.argv[1])
    result = requests.get('http://en.wikipedia.org/w/api.php', params=dict(
        action='query',
        prop='coordinates',
        titles=sys.argv[1],
        colimit=1,
        coprimary='all',
        format='json')).json()
    from pprint import pprint
    pprint(result)
