from envdaq.models import Configuration, DAQ
from django.core.exceptions import ObjectDoesNotExist


def get_config(input=None):
    '''
    Build json config file from database. Starts with
    local server and builds from there based on last stored
    setup
    '''

    # TODO: this could have options for last_good, get_named
    #       project, etc will come in here.

    # TODO: should we build configs based on pk/id of controllers
    #       and instruments? E.g., 
    #       CONT_LIST: [23, 24, 25] where eacha are pk values and 
    #       the build script will look up those controllers and append
    #       those config entries in a logical/consistent way. This
    #       way each item will maintain its own config. But also
    #       requires model entries for each (which should be the case)

    daq = get_daq()

    if daq is None:
        return ''



    daq = DAQ.objects.get(pk=1)
    print(f'daq.config = {daq.configuration.config}')
    return daq.configuration.config


def get_daq(pk=None, name=None, tags=None):
    # TODO: add ability to choose wanted daq

    # for now, hardcoded
    try:
        daq = DAQ.objects.get(pk=1)
    except ObjectDoesNotExist:
        daq = None

    return daq
