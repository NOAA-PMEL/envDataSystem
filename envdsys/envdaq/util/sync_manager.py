from envdaq.models import ControllerDef, Controller
from envinventory.models import InstrumentDef, Instrument
from channels.db import database_sync_to_async
import asyncio


class SyncManager():

    @staticmethod
    async def sync_data(config, force=True):
        await SyncManager.sync_data_nowait(config, force)

    @staticmethod
    @database_sync_to_async
    def sync_data_nowait(config, force=True):

        if 'SYSTEM_DEFINITIONS' in config:

            sys_def = config['SYSTEM_DEFINITIONS']
            print(f"sys_def:{sys_def}")
            for def_type, def_value in sys_def.items():

                if def_type == 'CONTROLLER_SYS_DEFS':
                    for name, cont_def in sys_def['CONTROLLER_SYS_DEFS'].items():
                        try:
                            controller = ControllerDef.objects.get(name=name)
                            if force:
                                controller.update(cont_def)
                            # if force update, update current
                        except ControllerDef.DoesNotExist:
                            # print(f'**** new controller: {name}')
                            controller = ControllerDef(name=name)
                            controller.update(cont_def)
                elif def_type == 'INSTRUMENT_SYS_DEFS':
                    for name, inst_def in sys_def['INSTRUMENT_SYS_DEFS'].items():
                        try:
                            # print(f'3333333333inst_def: {name}')
                            instrument = InstrumentDef.objects.get(name=name)
                            if force:
                                instrument.update(inst_def)
                            # if force update, update current
                        except InstrumentDef.DoesNotExist:
                            # print(f'22222222222new inst def')
                            instrument = InstrumentDef(name=name)
                            # print(f'{instrument}: {inst_def}')
                            instrument.update(inst_def)
                # elif def_type == 'INSTRUMENT_INSTANCE':
                #     for name, inst_def in sys_def['INSTRUMENT_'].items():
                #         try:
                #             instrument = InstrumentDef.objects.get(name=name)
                #             # if force update, update current
                #         except InstrumentDef.DoesNotExist:
                #             instrument = InstrumentDef(name=name)
                #             instrument.update(inst_def)

    @staticmethod
    async def sync_instrument_instance(config):
        await SyncManager.sync_instrument_instance_nowait(config)

    @staticmethod
    @database_sync_to_async
    def sync_instrument_instance_nowait(config):
        # pass
        if config:
            # print(f'***** config: {config}')
            # print(f'instance: {config["NAME"]}, {config["MODEL"]},')
            try:
                inst_def = InstrumentDef.objects.get(
                    name=config['NAME'],
                    model=config['MODEL'],
                )
                # print(inst_def)

                try:
                    inst = Instrument.objects.get(
                        definition=inst_def,
                        serial_number=config['SERIAL_NUMBER']
                    )
                    # print(f'44444444444existing inst: {inst}')
                except Instrument.DoesNotExist:
                    # print(f'^^^^^create new: {inst_def}, {config["SERIAL_NUMBER"]}')
                    inst = Instrument(
                        definition=inst_def,
                        serial_number=config['SERIAL_NUMBER'],
                    )
                    inst.save()
                    # TODO: add tags    

            except InstrumentDef.DoesNotExist:
                # TODO: deal with missing instrument def
                print(f'Invalid InstrumentDef: {config["NAME"]}')
                return

    @staticmethod
    async def sync_controller_instance(config):
        await SyncManager.sync_controller_instance_nowait(config)

    @staticmethod
    @database_sync_to_async
    def sync_controller_instance_nowait(config):
        # pass
        if config:
            # print(f'controller instance: {config["NAME"]}')
            try:
                cont_def = ControllerDef.objects.get(
                    name=config['NAME'],
                    # model=config['MODEL'],
                )
                # print(f'ControllerDef: {cont_def}')

                try:
                    cont = Controller.objects.get(
                        name=config['LABEL'],
                        alias_name=config['alias']['name'],
                        definition=cont_def,
                        # serial_number=config['SERIAL_NUMBER']
                    )
                    cont.update_instruments(config['instrument_meta'])
                    cont.update_measurements(config['measurement_meta'])
                except Controller.DoesNotExist:
                    # print(f'^^^^^create new: {inst_def}, {config["SERIAL_NUMBER"]}')
                    cont = Controller(
                        name=config['LABEL'],
                        alias_name=config['alias']['name'],
                        definition=cont_def,
                        # serial_number=config['SERIAL_NUMBER'],
                    )
                    cont.save()
                    cont.update_instruments(config['instrument_meta'])
                    # TODO: just do one update here to make simpler
                    cont.update_measurements(config['measurement_meta'])
                    # TODO: add tags    
            
            except ControllerDef.DoesNotExist:
                # TODO: deal with missing instrument def
                print(f'Invalid ControllerDef: {config["NAME"]}')
                return
         
 