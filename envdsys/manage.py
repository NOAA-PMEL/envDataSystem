#!/usr/bin/env python
import os
import sys
# from setup.setup import config_setup

if __name__ == '__main__':

    # # print(f'arguments: {sys.argv}')
    # if sys.argv[1] == "envdsys_setup":
    #     server_type = "standalone"
    #     try:
    #         server_type = sys.argv[2]
    #     except IndexError:
    #         pass

    #     config_setup(server_type=server_type)
    #     print(f"envdsys setup for {server_type} complete...exit.")
    #     exit()

    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'envdsys.settings')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

 
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
