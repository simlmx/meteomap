import pickle, pprint, sys
from meteomap.utils import open

if __name__ == '__main__':
    some_file = sys.argv[1]
    pprint.pprint(pickle.load(open(some_file)))
