prerequisites
=============

postgresql database running


install
=======

    # get the code
    clone meteomap
    cd meteomap

    # create a virtual environment
    virtualenv -p python3 mm-ve
    source mm-ve/bin/activate

    # install the python requirements
    pip install -r py_req.txt
    
    # configure
    cp config_sample.json config.json # and edit config.json


database creation and population
================================

    # fetch the data
    python meteomap/fetch_dbpedia.py tmp/dbpedia_dump.gz

    # parse the dbpedia data and augment with wikipedia data
    python meteomap/parse_and_augment_dump.py tmp/dbpedia_dump.gz tmp/parsed_dump.gz

    # create the database
    python meteomap/create_database.py

    # insert the data in the database
    python meteomap/load_database.py tmp/parsed_dump.gz
