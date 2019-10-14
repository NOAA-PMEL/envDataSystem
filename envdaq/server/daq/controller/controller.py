# import abc
# import sys
import importlib
import asyncio
from daq.daq import DAQ
from daq.instrument.instrument import InstrumentFactory, Instrument
from data.message import Message
# from plots.plots import PlotManager
# from plots.apps.plot_app import TimeSeries1D
# from daq.manager.manager import DAQManager


class ControllerFactory():

    @staticmethod
    def create(config, **kwargs):
        create_cfg = config['CONTROLLER']
        contconfig = config['CONTCONFIG']
        alias = None
        if 'ALIAS' in config:
            alias = config['ALIAS']
        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            mod_ = importlib.import_module(create_cfg['MODULE'])
            print(mod_)
            cls_ = getattr(mod_, create_cfg['CLASS'])
            print(cls_)
            return cls_(contconfig, alias=alias, **kwargs)

        except Exception as e:  # better to catch ImportException?
            print(f"Controller: Unexpected error: {e}")
            raise e


class Controller(DAQ):

    class_type = 'CONTROLLER'

    # TODO: add way to pass gui hints/defines to front end
    gui_def = {
        'CONTROLS': {
            'RUN': {
                'LABEL': 'Run',
                'DESCRIPTION': 'Start/Stop controller',
                'WIDGET': 'Button',
                'OPTIONS': ['Start', 'Stop'],
            },
            'AUTOSTART': {
                'LABEL': 'Auto Start',
                'DESCRIPTION': 'Select to automatically run on startup',
                'WIDGET': 'Boolean',
            },
            'ACTIVE': {
                'LABEL': 'Active',
                'DESCRIPTION': 'Select to activate/deactivate controller',
                'WIDGET': 'Boolean',
            },
            'STATUS': {
                'LABEL': 'Status',
                'DESCRIPTION': 'Controller status indicator',
                'WIDGET': 'ColorTextOutput',
                'OPTIONS': [('OK', 'green'), ('Not OK', 'red')],
            }
        }

    }

    # def __init__(self, config):
    def __init__(self, config, alias=None, **kwargs):
        super(Controller, self).__init__(config, **kwargs)

        print('init Controller')
        print(self.config)

        self.name = 'Controller'

        self.alias = dict()
        if alias:
            self.alias = alias

        self.instrument_list = []
        self.instrument_map = {}

        self.component_map = dict()

        # TODO: flesh out sensor objects as simple instruments
        self.sensor_list = []
        self.sensor_map = dict()
        # signals/measurements from dataManager/aggregator
        self.signal_list = []
        self.signal_map = {}

        self.measurements = dict()
        self.measurements['meta'] = dict()

        # self.add_instruments()
        # self.add_signals()

    def setup(self):
        print(f'Controller setup')
        super().setup()

        self.configure_components()

        self.add_instruments()
        # self.add_signals()
        # print(f'id = {self.get_id()}')

        meta = self.get_metadata()

        # TODO: move this to actual instrument
        # # add plots to PlotServer
        # PlotManager.add_app(
        #     TimeSeries1D(
        #         meta,
        #         name=('/instrument_'+meta['plot_meta']['name'])
        #     ),
        #     start_after_add=True
        # )

        # # plot_app_name = ('/instrument_'+meta['plot_meta']['name'])
        # # plot_app_name = self.add_plot_app()
        # # if plot_app_name:
        # meta['plot_app'] = {
        #     'name': ('/controller_'+meta['plot_meta']['name'])
        # }

        # tell ui to build controller
        msg = Message(
            sender_id=self.get_id(),
            msgtype='Controller',
            subject='CONFIG',
            body={
                'purpose': 'SYNC',
                'type': 'CONTROLLER_INSTANCE',
                # TODO: controller needs metadata
                'data': self.get_metadata()
            }
        )
        self.message_to_ui_nowait(msg)
        # print(f'setup: {msg.body}')

        if (self.config['AUTO_START']):
            self.start()

    def configure_components(self):
        pass

    def get_ui_address(self):
        # print(self.label)
        if self.alias and ('name' in self.alias):
            address = 'envdaq/controller/'+self.alias['name']+'/'
        else:
            address = 'envdaq/controller/'+self.label+'/'
        print(f'get_ui_address: {address}')
        return address

    def start(self, cmd=None):
        print('Starting Controller')
        super().start(cmd)

        # start instruments
        for k, v in self.instrument_map.items():
            self.instrument_map[k].start()

    def stop(self, cmd=None):
        print('Controller.stop()')

        # if self.gui_client is not None:
        #     self.loop.run_until_complete(self.gui_client.close())

        # for controller in self.controller_map:
        #     controller.stop()

        # self.gui_client.sync_close()

        # TODO: stop should clean up tasks
        for k, instrument in self.instrument_map.items():
            # print(instrument)
            instrument.stop()

        # Do super last to finish clean up
        super().stop(cmd)

    def shutdown(self):
        print('controller:shutdown')

        # TODO: need to add a check in stop() to see if
        #       instrument is already stopped.
        # self.stop()

        # if self.gui_client is not None:
        #     # self.loop.run_until_complete(self.gui_client.close())
        #     self.gui_client.sync_close()

        for k, instrument in self.instrument_map.items():
            # print(sensor)
            instrument.shutdown()

        # tasks = asyncio.Task.all_tasks()
        # for t in self.task_list:
        #     # print(t)
        #     t.cancel()

    # async def read_loop(self):
    #     while True:
    #         msg = await self.inst_msg_buffer.get()
    #         # TODO: should handle be a async? If not, could block
    #         await self.handle(msg)
    #         # await asyncio.sleep(.1)

        super().shutdown()

    async def handle(self, msg, type=None):
        print(f'controller handle: {msg}')
        await asyncio.sleep(0.01)

    # def get_signature(self):
    #     # This will combine instrument metadata to generate
    #     #   a unique # ID
    #     return self.name+":"+self.label+":"
    #     +self.serial_number+":"+self.property_number

    # def create_msg_buffer(self, config):
    #     # self.read_buffer = MessageBuffer(config=config)
    #     self.inst_msg_buffer = asyncio.Queue(loop=self.loop)

    # # TODO: How do we want to id instruments? Need to clean this up
    # def add_instrument(self, instrument):
    #     self.inst_map[instrument.get_signature()] = instrument

    def add_instruments(self):
        print('Add instruments')
        # has_map = False
        # if 'INST_MAP' in self.config:
        #     has_map = True
        #     for itype, ilist in self.config['INST_MAP'].items():
        #         self.instrument_map[itype] = []
        #     self.instrument_map['UNKNOWN'] = []

        comp_inst = None
        if 'INSTRUMENTS' in self.component_map:
            comp_inst = self.component_map['INSTRUMENTS']

        for k, icfg in self.config['INST_LIST'].items():
            # for instr in self.config['INST_LIST']:
            # inst = InstrumentFactory().create(icfg['INST_CONFIG'])
            inst = InstrumentFactory().create(icfg, ui_config=self.ui_config)
            # inst.msg_buffer = self.inst_msg_buffer
            inst.to_parent_buf = self.from_child_buf
            self.instrument_map[inst.get_id()] = inst

            if ('INST_MAP' in self.config and comp_inst):
                for itype, ilist in self.config['INST_MAP'].items():
                    if k in ilist:
                        if itype in comp_inst:
                            comp_inst[itype].append(inst)
                            inst.register_data_request(
                                {
                                    'class': 'CONTROLLER',
                                    'id': self.label,
                                    'alias': self.alias,
                                    'ui_address': self.get_ui_address()
                                }
                            )

        self.build_controller_meta()

        # if has_map:
        #     for itype, ilist in self.config['INST_MAP'].items():
        #         if k in ilist:
        #             self.instrument_map[itype].append(inst)

    def build_controller_meta(self):
        pass

    def get_metadata(self):

        # print(f'**** get_metadata: {self}')

        if len(self.alias) == 0:
            self.alias['name'] = self.label.replace(' ', '')
            self.alias['prefix'] = self.label.replace(' ', '')

        instrument_meta = dict()
        # instrument_meta['instrument_meta'] = dict()
        # inst_meta = instrument_meta['instrument_meta']
        inst_meta = dict()
        for name, inst in self.instrument_map.items():
            inst_meta[name] = inst.get_metadata()
        instrument_meta['instrument_meta'] = inst_meta

        # print(f'plot_config = {plot_config}')
        print(f'name: {self.name}')
        print(f'label: {self.label}')
        meta = {
            'NAME': self.name,
            'LABEL': self.label,
            'alias': self.alias,
            'instrument_meta': instrument_meta,
            'measurement_meta': self.measurements['meta']
        }
        return meta

    def get_plot_meta(self):

        y_data = []
        for name, inst in self.instrument_map.items():
            if 'plot_meta' in inst:
                plot_meta = inst['plot_meta']
                plot_config = plot_meta
                # print(f'controller: plot_meta {plot_meta]}')
        #     inst_meta[name] = inst.get_metadata()

        # definition = self.get_definition_instance()
        # if 'plot_config' not in definition['DEFINITION']:
        #     return dict()

        # plot_config = definition['DEFINITION']['plot_config']
        # self.plot_name = '/instrument_'+self.alias['name']
        # plot_config['name'] = self.plot_name

        return plot_config


# class BasicController(Controller):

#     def __init__(self, config):
#         super().__init__(config)

#     async def handle(self, msg):
#         pass

#     def start(self):
#         pass

#     def stop(self):
#         pass


class DummyController(Controller):
    INSTANTIABLE = True
    # def __init__(self, config):

    def __init__(self, config, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):
        super(DummyController, self).__init__(config, **kwargs)
        # super().__init__(
        #     config,
        #     ui_config=ui_config,
        #     auto_connect_ui=auto_connect_ui
        # )
        self.name = 'DummyController'

        # self.INSTANTIABLE = True

        # DummyController.set_instantiable(True)
        # DummyController.INSTANTIABLE = True
        # DAQ.INSTANTIABLE = True
        self.setup()

    def setup(self):
        super().setup()
        # add extra here

        # build dummy istrument map
        # self.dummy_instrument_map = dict()
        # for inst_id, inst in self.instrument_map.items():
        #     print(f'()()() setup: {inst.type}, {inst.label}, {inst.alias}')
        #     if 'dummy' in inst.tag_list:
        #         self.dummy_instrument_map[inst_id] = {
        #             'instrument': inst,
        #             # anything else? alias? label?
        #         }

        # print(f'dummy_map: {self.dummy_instrument_map}')

    def configure_components(self):

        self.component_map['INSTRUMENTS'] = {
            'GPS': [],
            'DUMMY': [],
        }

    def build_controller_meta(self):

        meas_meta = dict()

        if len(self.component_map['INSTRUMENTS']['GPS']) > 0:
            # configure GPS measurements
            gps = dict()
            for inst in self.component_map['INSTRUMENTS']['GPS']:

                inst_meta = inst.get_metadata()
                inst_alias = inst_meta['alias']
                inst_id = inst_meta['ID']

                inst_meas = inst_meta['measurement_meta']
                inst_plots = inst_meta['plot_meta']


                # meas_meta[inst_id] = dict()
                # meas_meta[inst_id]['alias'] = inst_alias
                gps[inst_id] = dict()
                gps[inst_id]['alias'] = inst_alias
                gps[inst_id]['measurement_meta'] = dict()
                mm = gps[inst_id]['measurement_meta']
                for mtype, meas in inst_meas.items():
                    if 'latitude' in meas:
                        mm['latitude'] = (
                            meas['latitude']
                        )
                        # meas_meta[inst_id]['latitude'] = {
                        # gps[inst_id]['latitude'] = {
                        #     'measurement_meta': meas['latitude'],
                        # }
                    if 'longitude' in meas:
                        mm['longitude'] = (
                            meas['longitude']
                        )
                        # meas_meta[inst_id]['longitude'] = {
                        # gps[inst_id]['longitude'] = {
                        #     'measurement_meta': meas['longitude'],
                        # }
                    if 'altitude' in meas:
                        mm['altitude'] = (
                            meas['altitude']
                        )
                        # meas_meta[inst_id]['altitude'] = {
                        # gps[inst_id]['altitude'] = {
                        #     'measurement_meta': meas['altitude'],
                        # }
            meas_meta['GPS'] = gps

        if len(self.component_map['INSTRUMENTS']['DUMMY']) > 0:
            # configure GPS measurements
            dummy = dict()
            for inst in self.component_map['INSTRUMENTS']['DUMMY']:

                inst_meta = inst.get_metadata()
                inst_alias = inst_meta['alias']
                inst_id = inst_meta['ID']

                inst_meas = inst_meta['measurement_meta']
                inst_plots = inst_meta['plot_meta']

                # meas_meta = dict()
                # meas_meta[inst_id] = dict()
                # meas_meta[inst_id]['alias'] = inst_alias
                dummy[inst_id] = dict()
                dummy[inst_id]['alias'] = inst_alias
                dummy[inst_id]['measurement_meta'] = dict()
                mm = dummy[inst_id]['measurement_meta']
                for mtype, meas in inst_meas.items():
                    if 'size_distribution' in meas:
                        mm['size_distribution'] = (
                            meas['size_distribution']
                        )
                        # {
                        # # dummy[inst_id]['size_distribution'] = {
                        #     'measurement_meta': meas['size_distribution'],
                        # }
                    if 'diameter' in meas:
                        mm['diameter'] = (
                            meas['diameter']
                        )
                        # meas_meta[inst_id]['diameter'] = {
                        # dummy[inst_id]['diameter'] = {
                        #     'measurement_meta': meas['diameter'],
                        # }
                    if 'concentration' in meas:
                        mm['concentration'] = (
                            meas['concentration']
                        )
                        # meas_meta[inst_id]['concentration'] = {
                        # dummy[inst_id]['concentration'] = {
                        #     'measurement_meta': meas['concentration'],
                        # }
            meas_meta['DUMMY'] = dummy
        
        # add controller measurements
        print('here')
        # add controls

        self.measurements['meta'] = meas_meta

        # build plot_meta

    async def handle(self, msg, type=None):
        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Instrument.class_type):
            id = msg.sender_id
            # entry = self.parse(msg)
            # self.last_entry = entry
            # print('entry = \n{}'.format(entry))

            data = Message(
                sender_id=self.get_id(),
                msgtype=Controller.class_type,
            )
            # send data to next step(s)
            # to controller
            # data.update(subject='DATA', body=entry['DATA'])
            data.update(subject='DATA', body=entry)
            # print(f'instrument data: {data.to_json()}')

            await self.message_to_ui(data)
            # await PlotManager.update_data(self.plot_name, data.to_json())

            # print(f'data_json: {data.to_json()}\n')
        elif type == 'FromUI':
            if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                self.send_status()

            elif msg.subject == 'CONTROLS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                await self.set_control(msg.body['control'], msg.body['value'])
            elif msg.subject == 'RUNCONTROLS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                await self.handle_control_action(msg.body['control'], msg.body['value'])
                # await self.set_control(msg.body['control'], msg.body['value'])

        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        pass
        if control and value:
            if control == 'start_stop':
                if value == 'START':
                    self.start()
                elif value == 'STOP':
                    self.stop()

        #     elif control == 'inlet_temperature_sp':
        #         # check bounds
        #         # send command to instrument via interface
        #         cmd = Message(
        #             sender_id=self.get_id(),
        #             msgtype=Instrument.class_type,
        #             subject="COMMAND",
        #             body='inlet_temp='+value,
        #         )

        #         # print(f'{self.iface_map}')
        #         # await self.to_child_buf.put(cmd)
        #         await self.iface_map['DummyInterface:test_interface'].message_from_parent(cmd)
        #         self.set_control_att(control, 'action_state', 'OK')

    # def _create_definition(self):
    #     self.daq_definition['module'] = self.__module__
    #     self.daq_definition['class'] = self.__name__

    def get_definition_instance(self):
        return DummyController.get_definition()

    def get_definition():
        definition = dict()
        definition['module'] = DummyController.__module__
        definition['name'] = DummyController.__name__
        return {'DEFINITION': definition}
        # DAQ.daq_definition['DEFINITION'] = definition
        # return DAQ.daq_definition
