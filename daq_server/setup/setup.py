#!/usr/bin/env python
import os
# import sys
import shutil
from daq_server.setup.daq_server_conf import run_config

def config_setup(server_type="standalone"):
    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # print(f"root_path {root_path}")

    # # check if config folder has been setup
    path = os.path.join(root_path, 'config')
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"New config directory file created")
    
    path = os.path.join(root_path, 'config', 'settings.py')
    if not os.path.exists(path):
        if server_type == "docker":
            src = os.path.join(root_path, 'setup', 'settings_docker.py')
            shutil.copyfile(src, path)
            src = os.path.join(root_path, 'setup', 'envdsys_variables.env')
            dest = os.path.join(root_path, 'config', 'envdsys_variables.env')
            shutil.copyfile(src, dest)
            print(f"New settings.py files for docker created")
        else:
            src = os.path.join(root_path, 'setup', 'settings_orig.py')
            shutil.copyfile(src, path)
            print(f"New settings.py file created")

    path = os.path.join(root_path, 'db')
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"New db directory created")

def create_settings_file(run_type):

    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # # check if config folder has been setup

    if run_type == "docker":
        # save settings to volume folder
        daq_conf = "/tmp/daq_conf"
        try:
            daq_conf = run_config["DOCKER"]["volumes"]["daq_conf"]
        except KeyError:
            pass
        # docker_path = os.path.join(root_path, ui_conf)
        if not os.path.exists(daq_conf):
            os.makedirs(daq_conf)
            print(f"New config directory file created")

        src = os.path.join(root_path, 'setup', 'daq_settings.py')
        path = os.path.join(daq_conf, 'daq_settings.py')
        shutil.copyfile(src, path)

        # create env file
        create_env_file()
    else:
        src = os.path.join(root_path, 'setup', 'daq_settings.py')
        path = os.path.join(root_path, 'config', 'daq_settings.py')
        shutil.copyfile(src, path)
        # print(f"New settings.py file created")
        set_env_variables()


def create_env_vars():

    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # open env file
    # write env variables for docker-compose

    daq_name = "Test Server"
    try:
        daq_name = run_config["DAQ_NAME"]
    except KeyError:
        pass

    daq_fqdn = "localhost"
    try:
        daq_fqdn = run_config["DAQ_FQDN"]
    except KeyError:
        pass
    daq_nodename = daq_fqdn.split(".")[0]

    daq_namespace = "default"
    try:
        daq_namespace = run_config["DAQ_NAMESPACE"]
    except KeyError:
        pass

    ui_host = "localhost"
    try:
        ui_host = run_config["UI_HOST"]["name"]
    except KeyError:
        pass

    ui_port = "8001"
    try:
        ui_port = run_config["UI_HOST"]["port"]
    except KeyError:
        pass

    daq_conf = "/tmp/daq_conf"
    try:
        daq_conf = run_config["DOCKER"]["volumes"]["daq_conf"]
    except KeyError:
        pass

    daq_data_save_dir = "/tmp/daq_data"
    try:
        daq_data_save_dir = run_config["DOCKER"]["volumes"]["daq_data_save"]
    except KeyError:
        pass

    env_vars = {
        "DAQ_NAME": daq_name,
        "DAQ_FQDN": daq_fqdn,
        "DAQ_NODENAME": daq_nodename,
        "DAQ_NAMESPACE": daq_namespace,
        "UI_HOSTNAME": ui_host,
        "UI_HOSTPORT": ui_port,
        "DAQ_CFG_DIR": daq_conf,
        "DAQ_DATA_SAVE_DIR": daq_data_save_dir
    }
    return env_vars

def create_env_file():
    vars = create_env_vars()

    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    with open(os.path.join(root_path, 'docker', 'daq_server', 'daq_server_variables.env'), "w") as fd:
        for name, val in vars.items():
            fd.write(f"{name}={val}\n")

def set_env_variables():
    vars = create_env_vars()
    for name, val in vars.items():
        os.environ[name]=val

def configure_daq_server():
    
    run_type = "docker"
    try:
        run_type = run_config["RUN_TYPE"]
    except KeyError:
        pass

    create_settings_file(run_type)