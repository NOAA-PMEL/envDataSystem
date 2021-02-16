#!/usr/bin/env python
import os
import sys
# from setup.setup import config_setup

if __name__ == '__main__':

    do_collectstatic = False
    if len(sys.argv) > 1:
        opts = ["collectstatic"]
        result = [s for s in sys.argv[1:] if any(xs in s for xs in opts)]
        if result:
            do_collectstatic = True

    if do_collectstatic:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings_orig')
        os.environ['DJANGO_SETTINGS_MODULE'] = 'setup.settings_orig'
    else:
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
