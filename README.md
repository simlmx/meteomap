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
