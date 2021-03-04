run_config = {
    
    # RUN_TYPE:
    #   docker: run in docker containers including redis and postgresql db (default)
    #   system-python: runs from command line using "python manage.py runserver"
    #   system-daphne: runs using daphne
    # "SERVER_NAME": "Test Server",

    "DAQ_NAME": "UAS Cloudy Server",

    "RUN_TYPE": "docker",
    
    # Set username/groupname for run permissions - default to uid/gid of account during setup
    # "RUN_USER": "derek",
    # "RUN_GROUP": "derek",

    "DAQ_FQDN": "<host fqdn>",

    "DAQ_NAMESPACE": "default",

    # HOST:
    "UI_HOST": {
        "name": "localhost",
        "port": 8001
    },
    
    # DOCKER variable settings - ignrored for non docker run_type
    "DOCKER": {
        "volumes": {
            "daq_conf": "<path_to_daq_server_conf_data>",
            "daq_data_save": "<path_to_save_daq_servder_data>",
        },
    },
}