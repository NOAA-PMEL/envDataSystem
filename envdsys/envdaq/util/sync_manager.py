from envdaq.models import ControllerDef
from envinventory.models import InstrumentDef
from  channels.db import database_sync_to_async
import asyncio


class SyncManager():

    @staticmethod
    async def sync_data(config):
        await SyncManager.sync_data_nowait(config)

    @staticmethod
    @database_sync_to_async
    def sync_data_nowait(config):

        if 'SYSTEM_DEFINITIONS' in config:
            
            sys_def = config['SYSTEM_DEFINITIONS']
            
            for def_type, def_value in sys_def.items():
            
                if def_type == 'CONTROLLER_SYS_DEFS':
                    for name, cont_def in sys_def['CONTROLLER_SYS_DEFS'].items():
                        try:
                            controller = ControllerDef.objects.get(name=name)
                            # if force update, update current
                        except ControllerDef.DoesNotExist:
                            controller = ControllerDef(name=name)
                            controller.update(cont_def)
                elif def_type == 'INSTRUMENT_SYS_DEFS':
                    for name, inst_def in sys_def['INSTRUMENT_SYS_DEFS'].items():
                        try:
                            instrument = InstrumentDef.objects.get(name=name)
                            # if force update, update current
                        except InstrumentDef.DoesNotExist:
                            instrument = InstrumentDef(name=name)
                            instrument.update(inst_def)
        