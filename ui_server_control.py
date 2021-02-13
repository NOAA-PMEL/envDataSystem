#!/usr/bin/env python
import os
import sys
import subprocess

from envdsys.setup.ui_server_conf import run_config
from envdsys.setup.setup import configure_ui_server

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
    # sys.argv.append("stop")
    print(sys.argv[1:])

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

    run_type = "docker"
    try:
        run_type = run_config["RUN_TYPE"]
    except IndexError:
        pass
    except KeyError:
        pass

    print(f"RUN_TYPE: {run_type}")

    # set defaults
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

    if run_type == "docker":
        # setup .env file for docker-compose

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

        ui_data_save = "/tmp/ui_data"
        try:
            ui_data_save = run_config["DOCKER"]["volumes"]["ui_data_save"]
        except KeyError:
            pass

    if do_config:
        from envdsys.setup.setup import configure_ui_server

        print("Configuring UIServer:")
        print(f"\thost:port = {host}:{port}")
        print(f"\tsave UI data = {ui_data_save}")
        if run_type == "docker":
            print(f"\tDB dir = {db_data}")
            print(f"\tUI conf dir = {ui_conf}")
            print(f"\tUI data dir = {ui_data_save}")

        configure_ui_server()
        if run_type == "docker" and do_build:
            print("building containers...")
            result = subprocess.call(
                [
                    "docker-compose",
                    "-f",
                    "docker-compose-envdsys.yml",
                    "--env-file",
                    "envdsys/setup/envdsys_variables.env",
                    "build",
                    "envdsys",
                ]
            )

    if do_start:
        print("starting envdsys docker containter environment...")
        # run based on run type
        if run_type == "docker":
            print("start docker")
            result = subprocess.call(
                [
                    "docker-compose",
                    "-f",
                    "docker-compose-envdsys.yml",
                    "--env-file",
                    "envdsys/setup/envdsys_variables.env",
                    "up",
                    "-d",
                    # "envdsys",
                ]
            )

        elif run_type == "system-python":
            os.chdir("./envdsys")
            result = subprocess.call(
                ["python", "manage.py", "runserver", f"{host}:{port}"]
            )

        elif run_type == "system-daphne":
            os.chdir("./envdsys")
            result = subprocess.call(
                ["daphne", "-b", host, "-p", port, "envdsys.asgi:application"]
            )

    elif do_stop:
        print("stopping envdsys docker containter environment...")
        if run_type == "docker":
            print("stop docker")
            result = subprocess.call(
                [
                    "docker-compose",
                    "-f",
                    "docker-compose-envdsys.yml",
                    "--env-file",
                    "envdsys/setup/envdsys_variables.env",
                    "down",
                ]
            )
        else:
            print("Running via pyton, kill from command line or by pid")

        