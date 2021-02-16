#!/usr/bin/env python
import os

# import sys
import shutil
from pwd import getpwnam
from grp import getgrnam
# from envdsys.setup.ui_server_conf import run_config


# def config_setup(server_type="standalone"):
#     root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
#     # print(f"root_path {root_path}")

#     # # check if config folder has been setup
#     path = os.path.join(root_path, "config")
#     if not os.path.exists(path):
#         os.makedirs(path)
#         print(f"New config directory file created")

#     path = os.path.join(root_path, "config", "settings.py")
#     if not os.path.exists(path):
#         if server_type == "docker":
#             src = os.path.join(root_path, "setup", "settings_docker.py")
#             shutil.copyfile(src, path)
#             src = os.path.join(root_path, "setup", "envdsys_variables.env")
#             dest = os.path.join(root_path, "config", "envdsys_variables.env")
#             shutil.copyfile(src, dest)
#             print(f"New settings.py files for docker created")
#         else:
#             src = os.path.join(root_path, "setup", "settings_orig.py")
#             shutil.copyfile(src, path)
#             print(f"New settings.py file created")

#     path = os.path.join(root_path, "db")
#     if not os.path.exists(path):
#         os.makedirs(path)
#         print(f"New db directory created")


# def create_settings_file(run_type):
def create_settings_file(conf_vars):

    run_type = conf_vars["RUN_TYPE"]

    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # # check if config folder has been setup

    if run_type == "docker":
        ui_conf = conf_vars["UI_CFG_DIR"]
        # # save settings to volume folder
        # ui_conf = "/tmp/ui_conf"
        # try:
        #     ui_conf = run_config["DOCKER"]["volumes"]["ui_conf"]
        # except KeyError:
        #     pass
        # # docker_path = os.path.join(root_path, ui_conf)
        if not os.path.exists(ui_conf):
            os.makedirs(ui_conf)
            print(f"New config directory file created")

        src = os.path.join(root_path, "setup", "settings_docker.py")
        path = os.path.join(ui_conf, "settings.py")
        shutil.copyfile(src, path)

        # create env file
        create_env_file(conf_vars)
    else:
        src = os.path.join(root_path, "setup", "settings.py")
        path = os.path.join(root_path, "config", "settings.py")
        shutil.copyfile(src, path)
        # print(f"New settings.py file created")


def get_conf_vars():

    run_type = "docker"
    try:
        from envdsys.setup.ui_server_conf import run_config
        run_type = run_config["RUN_TYPE"]

    except ModuleNotFoundError:
        init_server_config()
        print(
            f"Initialized server config file. Edit ./envdsys/setup/ui_server_conf.py and re-run"
        )
        return None
    except KeyError:
        print("Unable to determine run_type. Check conf file.")
        return None

    uid = os.getuid()
    try:
        username = run_config["RUN_USER"]
        uid = getpwnam(username).pw_uid
    except KeyError:
        pass

    gid = os.getgid()
    try:
        groupname = run_config["RUN_GROUP"]
        gid = getgrnam(groupname).gr_gid
    except KeyError:
        pass

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

    conf_vars = {
        "RUN_TYPE": run_type,
        "RUN_UID": str(uid),
        "RUN_GID": str(gid),
        "UI_HOSTNAME": host,
        "UI_HOSTPORT": port,
        "UI_DATA_SAVE": ui_data_save,
        "DB_DATA_DIR": db_data,
        "UI_CFG_DIR": ui_conf,
        "UI_DATA_SAVE_DIR": ui_data_save_dir,
    }
    # print(conf_vars)
    return conf_vars


def create_env_file(conf_vars):

    # root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    root_path = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    )

    # vars = get_conf_vars()
    vars = conf_vars

    # add allowed_hosts entry
    vars["UI_ALLOWED_HOSTS"] = "127.0.0.1,localhost"
    if conf_vars["UI_HOSTNAME"] not in vars["UI_ALLOWED_HOSTS"]:
        vars['UI_ALLOWED_HOSTS'] = ",".join(["127.0.0.1,localhost", conf_vars["UI_HOSTNAME"]])

    with open(
        os.path.join(root_path, "docker", "envdsys", "envdsys_variables.env"), "w"
    ) as fd:
        for name, val in vars.items():
            if name != "RUN_TYPE":
                fd.write(f"{name}={val}\n")

def init_server_config():
    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    src = os.path.join(root_path, "setup", "ui_server_conf_tmpl.py")
    dest = os.path.join(root_path, "setup", "ui_server_conf.py")
    shutil.copyfile(src, dest)

def configure_ui_server():

    conf_vars = get_conf_vars()
    if conf_vars:
        create_settings_file(conf_vars)

    # run_type = "docker"
    # try:
    #     from envdsys.setup.ui_server_conf import run_config

    #     run_type = run_config["RUN_TYPE"]
    # except ModuleNotFoundError:
    #     init_server_config()
    #     print(
    #         f"Initialized server config file. Edit ./envdsys/setup/ui_server_conf.py and re-run"
    #     )
    #     exit()
    # except KeyError:
    #     pass

    # create_settings_file(run_type)