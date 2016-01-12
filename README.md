description
===========

Website displaying weather data for a few thousand cities on an interactive
map. The data is taken from Wikipedia. You can see the current version here:
http://meteomap-simlmx.rhcloud.com/

Originally the goal was to have a more efficient way to choose my travel itineraries, weather along the way being one of the main concerns.

prerequisites
=============

install a few libraries

    apt-get install postgresql libpython3-dev libncurses5-dev postgis

(there are clearly some missing)

have a postgresql database running


install
=======

    # get the code
    clone meteomap
    cd meteomap

    # create a virtual environment
    virtualenv -p python3 mm-ve
    source mm-ve/bin/activate

    # install the python requirements
    pip install -r requirements.txt
    
    # configure
    cp config_sample.json config.json # and edit config.json


database creation and population
================================

    # fetch the list of cities and associated files from geonames.org
    wget "http://download.geonames.org/export/dump/admin1CodesASCII.txt" -P tmp
    wget "http://download.geonames.org/export/dump/allCountries.zip" -P tmp
    wget "http://download.geonames.org/export/dump/countryInfo.txt" -P tmp

    # parse the city files
    python meteomap/parse_geonames.py --admin1codes-file tmp/admin1CodesASCII.txt \
    --country-infos-file tmp/countryInfo.txt tmp/allCountries.zip tmp/parsed_geonames_world.gz

    # add wiki data
    python meteomap/augment_with_wiki.py tmp/parsed_geonames_world.gz tmp/augmented_geonames_world.gz

    # create the database
    python meteomap/create_database.py

    # insert the data in the database
    python meteomap/load_database.py tmp/augmented_geonames_world.gz

    # start the site
    python meteomap/sites.py
