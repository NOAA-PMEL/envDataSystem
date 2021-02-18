#!/usr/bin/env python
import os
import sys
import subprocess

# from daq_server.setup.daq_server_conf import run_config
from daq_server.setup.setup import configure_daq_server, get_conf_vars

# Run settings
# run_settings = {
#     "run_type": "system",  # docker or system
#     "debug": False,  # only applies to server run_type
#     "host": "localhost",  # server host name
#     "port": 8001,
#     "docker_data_volume": "/<path_to_data>/Data/envDataSystem",
#     "docker_config_volume": "/<path_to_config>/envDataSystem/envdsys/config",
#     "docker_db_volume": "/<path_to_db_data>/db/postgresql",

# }

if __name__ == "__main__":
    # sys.argv.append("-c")
    print(sys.argv[1:])

    conf_vars = get_conf_vars()
    if not conf_vars: #  first run, edit conf and restart
        exit()

    do_config = False
    do_build = False
    do_start = False
    do_stop = False
    if len(sys.argv) > 1:
        opts = ["--config", "-c"]
        result = [s for s in sys.argv[1:] if any(xs in s for xs in opts)]
        if result:
            do_config = True
        opts = ["--build", "-b"]
        result = [s for s in sys.argv[1:] if any(xs in s for xs in opts)]
        if result:
            do_config = True
            do_build = True
        opts = ["start"]
        result = [s for s in sys.argv[1:] if any(xs in s for xs in opts)]
        if result:
            do_start = True
        opts = ["stop"]
        result = [s for s in sys.argv[1:] if any(xs in s for xs in opts)]
        if result:
            do_stop = True

        # if "--config" in sys.argv or "-c" in sys.argv:
        # if sys.argv[1] == "--config" or sys.argv[1] == "-c":
        #     do_config = True

    run_type = conf_vars["RUN_TYPE"]  
    # run_type = "docker"
    # try:
    #     run_type = run_config["RUN_TYPE"]
    # except IndexError:
    #     pass
    # except KeyError:
    #     pass

    print(f"RUN_TYPE: {run_type}")

    # set defaults
    daq_name = conf_vars["DAQ_NAME"]  
    # daq_name = "Test Server"
    # try:
    #     daq_name = run_config["DAQ_NAME"]
    # except KeyError:
    #     pass

    daq_fqdn = conf_vars["DAQ_FQDN"]  
    # daq_fqdn = "localhost"
    # try:
    #     daq_fqdn = run_config["DAQ_FQDN"]
    # except KeyError:
    #     pass
    daq_nodename = daq_fqdn.split(".")[0]

    daq_namespace = conf_vars["DAQ_NAMESPACE"]  
    # daq_namespace = "default"
    # try:
    #     daq_namespace = run_config["DAQ_NAMESPACE"]
    # except KeyError:
    #     pass

    ui_host = conf_vars["UI_HOSTNAME"]  
    # ui_host = "localhost"
    # try:
    #     ui_host = run_config["UI_HOST"]["name"]
    # except KeyError:
    #     pass

    ui_port = conf_vars["UI_HOSTPORT"]  
    # ui_port = "8001"
    # try:
    #     ui_port = run_config["UI_HOST"]["port"]
    # except KeyError:
    #     pass

    if run_type == "docker":
        # setup .env file for docker-compose

        daq_conf = conf_vars["DAQ_CFG_DIR"]  
        # daq_conf = "/tmp/daq_conf"
        # try:
        #     daq_conf = run_config["DOCKER"]["volumes"]["daq_conf"]
        # except KeyError:
        #     pass

        daq_data_save = conf_vars["DAQ_DATA_SAVE_DIR"]  
        # daq_data_save = "/tmp/daq_data"
        # try:
        #     daq_data_save = run_config["DOCKER"]["volumes"]["daq_data_save"]
        # except KeyError:
        #     pass

    if do_config:
        from daq_server.setup.setup import configure_daq_server

        print("Configuring DAQServer:")
        print(f"\tDAQ Name = {daq_name}")
        print(f"\tDAQ fqdn = {daq_fqdn}")
        print(f"\tDAQ nodename = {daq_nodename}")
        print(f"\tDAQ namespace = {daq_namespace}")
        print(f"\tui_host:port = {ui_host}:{ui_port}")
        if run_type == "docker":
            print(f"\tDAQ conf dir = {daq_conf}")
            print(f"\tDAQ data dir = {daq_data_save}")

        configure_daq_server()
        if run_type == "docker" and do_build:
            print("building containers...")
            os.chdir("docker/daq_server")
            result = subprocess.call(
                [
                    "docker-compose",
                    "-f",
                    "docker-compose-daq_server.yml",
                    # "--env-file",
                    # "docker/daq_server/daq_server_variables.env",
                    "build",
                    "daq_server",
                ]
            )
            os.chdir("../..")

    if do_start:
        # run based on run type
        if run_type == "docker":
            print("starting daq_server docker container environment...")
            # print("start docker")
            os.chdir("docker/daq_server")
            result = subprocess.call(
                [
                    "docker-compose",
                    "-f",
                    "docker-compose-daq_server.yml",
                    # "--env-file",
                    # "docker/daq_server/daq_server_variables.env",
                    "up",
                    "-d",
                    "daq_server"
                ]
            )
            os.chdir("../..")

        elif run_type == "system":
            print("starting daq_server system environment...")
            os.chdir("./daq_server")
            result = subprocess.call(
                ["python", "daq_server.py"]
            )

    elif do_stop:
        if run_type == "docker":
            print("stopping daq_server docker container environment...")
            # print("stop docker")
            os.chdir("docker/daq_server")
            result = subprocess.call(
                [
                    "docker-compose",
                    "-f",
                    "docker-compose-daq_server.yml",
                    # "--env-file",
                    # "docker/daq_server/daq_server_variables.env",
                    "down",
                ]
            )
            os.chdir("../..")
        else:
            print("Running via pyton, kill from command line or by pid")

        