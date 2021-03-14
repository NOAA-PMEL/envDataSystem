import os

server_config = {

    # 'name': 'Test Server',
    'name': os.environ['DAQ_NAME'],

    # fqdn = "who.pmel.noaa.gov"
    # nodename = fqdn.split(".")[0]

    # daq_namespace = "test"

    # 'ui_config': {
    #     'host': '192.168.86.51',
    #     'port': 8001
    # },
    'ui_config': {
        # 'host': "localhost",
        'host': os.environ["UI_HOSTNAME"],
        # 'port': 8001,
        'port': os.environ["UI_HOSTPORT"],
    },

    # 'base_file_path': '/home/horton/derek/Data/envDataSystem',
    'base_file_path': os.environ['DAQ_DATA_SAVE_DIR'],

    "daq_id": {
        # "fqdn": <daq_server fqdn>,
        "fqdn": os.environ["DAQ_FQDN"],
        # "node": <daq_server nodename>,
        "node": os.environ["DAQ_NODENAME"],
        # "namespace": "daq_namespace"
        "namespace": os.environ["DAQ_NAMESPACE"]
    },

    "last_config_file": "config/last_config.json",

    "current_config_file": "config/current_config.json",

    "current_run_config": {}

}
