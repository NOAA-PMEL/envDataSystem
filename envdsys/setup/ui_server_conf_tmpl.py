run_config = {
    
    # RUN_TYPE:
    #   docker: run in docker containers including redis and postgresql db (default)
    #   system-python: runs from command line using "python manage.py runserver"
    #   system-daphne: runs using daphne
    "RUN_TYPE": "docker",

    # Set username/groupname for run permissions - default to uid/gid of account during setup
    # "RUN_USER": "derek",
    # "RUN_GROUP": "derek",
    
    # HOST:
    "HOST": {
        "name": "localhost",
        "port": 8001,
        # "network": "<env network name"
    },
    
    # DOCKER variable settings - ignrored for non docker run_type
    "DOCKER": {
        "volumes": {
            "db_data": "<path_to_db_data>",
            "ui_conf": "<path_to_envdys_conf_data>",
            "ui_data_save": "<path_to_save_ui_data>",
        },
    },
}