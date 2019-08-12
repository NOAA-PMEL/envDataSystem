# from envdaq.models import Configuration, DAQServer
from envdaq.models import DAQServer
from envtags.models import Configuration
from django.core.exceptions import ObjectDoesNotExist
import asyncio
from  channels.db import database_sync_to_async


class ConfigurationUtility():

    def __init__(self):
        pass

    async def get_config(self, input=None):
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

        # daq = await get_daq()

        # if daq is None:
        #     return ''

        # daq = DAQServer.objects.get(pk=1)
        # # print(f'daq.config = {daq.configuration.config}')
        # return daq.configuration.get_config()
        config = await self.get_config_sync(input)
        return config

    @database_sync_to_async
    def get_config_sync(self, input=None):
        daq = DAQServer.objects.get(pk=1)
        # print(f'daq.config = {daq.configuration.config}')
        return daq.configuration.get_config()

    async def get_daq(pk=None, name=None, tags=None):
        # TODO: add ability to choose wanted daq

        # for now, hardcoded
        try:
            daq = database_sync_to_async(DAQServer.objects.get(pk=1))
        except ObjectDoesNotExist:
            daq = None

        return daq
