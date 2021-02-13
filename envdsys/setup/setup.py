#!/usr/bin/env python
import os
# import sys
import shutil
from envdsys.setup.ui_server_conf import run_config

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
        ui_conf = "/tmp/ui_conf"
        try:
            ui_conf = run_config["DOCKER"]["volumes"]["ui_conf"]
        except KeyError:
            pass
        # docker_path = os.path.join(root_path, ui_conf)
        if not os.path.exists(ui_conf):
            os.makedirs(ui_conf)
            print(f"New config directory file created")

        src = os.path.join(root_path, 'setup', 'settings_docker.py')
        path = os.path.join(ui_conf, 'settings.py')
        shutil.copyfile(src, path)

        # create env file
        create_env_file()
    else:
        src = os.path.join(root_path, 'setup', 'settings.py')
        path = os.path.join(root_path, 'config', 'settings.py')
        shutil.copyfile(src, path)
        # print(f"New settings.py file created")

def create_env_file():

    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # open env file
    # write env variables for docker-compose

    host = "localhost"
    try:
        host = run_config["HOST"]["name"]
    except KeyError:
        pass

    port = "8001"
    try:
        port = run_config["HOST"]["port"]
    except KeyError:
        pass

    ui_data_save = True
    try:
        ui_data_save = run_config["UI_DATA_SAVE"]
    except KeyError:
        pass

    db_data = "/tmp/db"
    try:
        db_data = run_config["DOCKER"]["volumes"]["db_data"]
    except KeyError:
        pass

    ui_conf = "/tmp/ui_conf"
    try:
        ui_conf = run_config["DOCKER"]["volumes"]["ui_conf"]
    except KeyError:
        pass

    ui_data_save_dir = "/tmp/ui_data"
    try:
        ui_data_save_dir = run_config["DOCKER"]["volumes"]["ui_data_save"]
    except KeyError:
        pass

    with open(os.path.join(root_path, 'setup', 'envdsys_variables.env'), "w") as fd:
        fd.write(f"HOSTNAME={host}\n")
        fd.write(f"HOSTPORT={port}\n")
        fd.write(f"UI_DATA_SAVE={ui_data_save}\n")
        fd.write(f"DB_DATA_DIR={db_data}\n")
        fd.write(f"UI_CFG_DIR={ui_conf}\n")
        fd.write(f"UI_DATA_SAVE_DIR={ui_data_save_dir}\n")

def configure_ui_server():
    
    run_type = "docker"
    try:
        run_type = run_config["RUN_TYPE"]
    except KeyError:
        pass

    create_settings_file(run_type)