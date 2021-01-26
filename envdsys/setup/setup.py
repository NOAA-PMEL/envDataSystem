#!/usr/bin/env python
import os
# import sys
import shutil

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
