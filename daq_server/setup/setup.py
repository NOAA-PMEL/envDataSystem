#!/usr/bin/env python
import os

# import sys
import shutil
import platform
from pwd import getpwnam
from grp import getgrnam

# from daq_server.setup.daq_server_conf import run_config

# def config_setup(server_type="standalone"):
#     root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
#     # print(f"root_path {root_path}")

#     # # check if config folder has been setup
#     path = os.path.join(root_path, 'config')
#     if not os.path.exists(path):
#         os.makedirs(path)
#         print(f"New config directory file created")

#     path = os.path.join(root_path, 'config', 'settings.py')
#     if not os.path.exists(path):
#         if server_type == "docker":
#             src = os.path.join(root_path, 'setup', 'settings_docker.py')
#             shutil.copyfile(src, path)
#             src = os.path.join(root_path, 'setup', 'envdsys_variables.env')
#             dest = os.path.join(root_path, 'config', 'envdsys_variables.env')
#             shutil.copyfile(src, dest)
#             print(f"New settings.py files for docker created")
#         else:
#             src = os.path.join(root_path, 'setup', 'settings_orig.py')
#             shutil.copyfile(src, path)
#             print(f"New settings.py file created")

#     path = os.path.join(root_path, 'db')
#     if not os.path.exists(path):
#         os.makedirs(path)
#         print(f"New db directory created")


def create_settings_file(conf_vars):

    run_type = conf_vars["RUN_TYPE"]

    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # # check if config folder has been setup
    
    if run_type == "docker":
        daq_conf = conf_vars["DAQ_CFG_DIR"]
        # # save settings to volume folder
        # daq_conf = "/tmp/daq_conf"
        # try:
        #     daq_conf = run_config["DOCKER"]["volumes"]["daq_conf"]
        # except KeyError:
        #     pass
        # docker_path = os.path.join(root_path, ui_conf)
        if not os.path.exists(daq_conf):
            os.makedirs(daq_conf)
            print(f"New config directory file created")

        src = os.path.join(root_path, "setup", "daq_settings_docker.py")
        path = os.path.join(daq_conf, "daq_settings.py")
        shutil.copyfile(src, path)

        # create env file
        create_env_file(conf_vars)

    else:
        src = os.path.join(root_path, "setup", "daq_settings_orig.py")
        path = os.path.join(root_path, "config", "daq_settings.py")
        shutil.copyfile(src, path)
        # print(f"New settings.py file created")
        set_env_variables(conf_vars)

def get_conf_vars():

    # root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    try:
        from daq_server.setup.daq_server_conf import run_config
        run_type = run_config["RUN_TYPE"]

    except ModuleNotFoundError:
        init_server_config()
        print(
            f"Initialized server config file. Edit ./daq_server/setup/daq_server_conf.py and re-run"
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
        "RUN_TYPE": run_type,
        "RUN_UID": str(uid),
        "RUN_GID": str(gid),
        "DAQ_NAME": daq_name,
        "DAQ_FQDN": daq_fqdn,
        "DAQ_NODENAME": daq_nodename,
        "DAQ_NAMESPACE": daq_namespace,
        "UI_HOSTNAME": ui_host,
        "UI_HOSTPORT": ui_port,
        "DAQ_CFG_DIR": daq_conf,
        "DAQ_DATA_SAVE_DIR": daq_data_save_dir,
    }
    return env_vars


def create_env_file(conf_vars):
    # vars = get_conf_vars()
    vars = conf_vars

    root_path = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    )

    with open(
        # os.path.join(root_path, "docker", "daq_server", "daq_server_variables.env"), "w"
        os.path.join(root_path, "docker", "daq_server", ".env"), "w"
    ) as fd:
        for name, val in vars.items():
            if name != "RUN_TYPE":
                fd.write(f"{name}={val}\n")


def set_env_variables(conf_vars):
    # vars = get_conf_vars()
    vars = conf_vars
    for name, val in vars.items():
        if name != "RUN_TYPE":
            os.environ[name] = str(val)
            print(f"set env: {name}: {val}")

def init_server_config():
    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    src = os.path.join(root_path, "setup", "daq_server_conf_tmpl.py")
    dest = os.path.join(root_path, "setup", "daq_server_conf.py")
    shutil.copyfile(src, dest)

def set_platform_libs():
    arch = platform.architecture()
    machine = platform.machine()

    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    lj_src = None
    msg = f"setup incomplete for {arch} : {machine}"
    if arch[0] == "64bit":
        if machine == "x86_64": # 64bit linux
            lj_src = os.path.join(
                root_path,
                "setup",
                "deps",
                "labjack",
                "labjack_ljm_minimal_2019_04_10_x86_64.tar.gz",
            )

        elif machine == "aarch64": # Raspberry Pi
            lj_src = os.path.join(
                root_path,
                "setup",
                "deps",
                "labjack",
                "labjack_ljm_minimal_2020_03_31_aarch64_beta_0.tar.gz",
            )
    elif arch[0] == "32bit":
        if machine == "i386": # 64bit linux
            lj_src = os.path.join(
                root_path,
                "setup",
                "deps",
                "labjack",
                "labjack_ljm_minimal_2019_04_10_i386.tar.gz",
            )
        elif "armv7" in machine: # Raspberry Pi
            lj_src = os.path.join(
                root_path,
                "setup",
                "deps",
                "labjack",
                "labjack_ljm_minimal_2020_03_31_armhf_beta.tar.gz",
            )

    if lj_src:
        msg = f"setup labjack libraries for {arch} : {machine}"
        path = os.path.join(root_path, "setup", "deps", "labjack_ljm.tar.gz")
        shutil.copyfile(lj_src, path)
    print(msg)

def configure_daq_server():

    conf_vars = get_conf_vars()
    if conf_vars:
        if conf_vars["RUN_TYPE"] == "docker":
            set_platform_libs()
        create_settings_file(conf_vars)

    # run_type = "docker"
    # try:
    #     run_type = run_config["RUN_TYPE"]
    # except KeyError:
    #     pass

    # # setup architecture/machine specific files for docker install
    # if run_type == "docker":
    #     set_platform_libs()

    # create_settings_file(run_type)