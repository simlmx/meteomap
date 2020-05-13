description
===========

Website displaying weather data for a few thousand cities on an interactive
map. The data is taken from Wikipedia. You can see the current version here:
http://meteomap-simlmx.rhcloud.com/

Originally the goal was to have a more efficient way to choose my travel itineraries, weather along the way being one of the main concerns.

So far optimized for desktop... and probably not for all browsers.


prerequisites
=============

`docker`


configuration
=============

    cp config_sample.json config.json
    # and edit the file if needed


database creation and population
================================

    # create a folder where we will put the downloadedfiles
    mkdir download

    # fetch the list of cities and associated files from geonames.org
    wget "http://download.geonames.org/export/dump/admin1CodesASCII.txt" -P downloads
    wget "http://download.geonames.org/export/dump/allCountries.zip" -P downloads
    wget "http://download.geonames.org/export/dump/countryInfo.txt" -P downloads

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.tx

    # parse the city files
    python meteomap/parse_geonames.py --admin1codes-file downloads/admin1CodesASCII.txt \
    --country-infos-file downloads/countryInfo.txt downloads/allCountries.zip downloads/parsed_geonames_world.gz

    # add wiki data
    python meteomap/augment_with_wiki.py downloads/parsed_geonames_world.gz downloads/augmented_geonames_world.gz

    # create the database
    python meteomap/create_database.py

    # insert the data in the database
    python meteomap/load_database.py downloads/augmented_geonames_world.gz


Running the website
==================

    make run
    # Go to 0.0.0.0:8000


Deploy in prod
===============

* `pg_dump` the database locally and then push it to the prod database.
* The heroku deployment is in the `heroku` branch
