# import abc
import sys
import importlib
import asyncio
from daq.daq import DAQ
# from client.wsclient import WSClient
from daq.instrument.instrument import InstrumentFactory
from data.message import Message
# from daq.manager.manager import DAQManager


class ControllerFactory():

    @staticmethod
    def create(config, **kwargs):
        create_cfg = config['CONTROLLER']
        contconfig = config['CONTCONFIG']
        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            mod_ = importlib.import_module(create_cfg['MODULE'])
            print(mod_)
            cls_ = getattr(mod_, create_cfg['CLASS'])
            print(cls_)
            return cls_(contconfig, **kwargs)

        except:  # better to catch ImportException?
            print("Controller: Unexpected error:", sys.exc_info()[0])
            raise


class Controller(DAQ):

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
    def __init__(self, config, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):
        super(Controller, self).__init__(config, **kwargs)
        # super().__init__(
        #    config,
        #    ui_config=ui_config,
        #    auto_connect_ui=auto_connect_ui
        # )
        print('init Controller')
        print(self.config)

        self.name = 'Controller'

        self.instrument_list = []
        self.instrument_map = {}

        # signals/measurements from dataManager/aggregator
        self.signal_list = []
        self.signal_map = {}

        # self.self.loop = asyncio.get_event_loop()

        self.sendq = asyncio.Queue(loop=self.loop)
        # self.readq = asyncio.Queue(loop=self.event_loop)

        # TODO: eventuallly this will be from factory and in config
        # TODO: properly instantiate and close WSClient in controller
        # self.gui_client = WSClient(
        #     uri='ws://localhost:8001/ws/envdaq/data_test/')

        # self.task_list.append(asyncio.ensure_future(self.send_gui_data()))
        # self.task_list.append(asyncio.ensure_future(self.read_gui_data()))
        # asyncio.ensure_future(self.message_to_gui())
        # asyncio.ensure_future(self.from_gui_loop())
        # asyncio.ensure_future(self.send_data())

        # self.create_msg_buffers(config=None)

        # self.add_instruments()
        # self.add_signals()

    def setup(self):

        self.add_instruments()
        # self.add_signals()
        # print(f'id = {self.get_id()}')

        # tell ui to build instrument
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

    def get_ui_address(self):
        print(self.label)
        address = 'envdaq/controller/'+self.label+'/'
        print(f'get_ui_address: {address}')
        return address

    async def send_message(self, message):
        # TODO: Do I need queues? Message and string methods?
        # await self.sendq.put(message.to_json())
        await self.sendq.put(message)
        # await self.to_gui_buf.put(message)

    async def send_gui_data(self):

        while True:
            # body = 'fake message - {}'.format(datetime.utcnow().isoformat(timespec='seconds'))
            # msg = {'message': body}
            # message = Message(type='Test', sender_id='me', subject='test', body=msg)
            # # print('send_data: {}'.format(msg))
            # print('send_data: {}'.format(message.to_json))
            # # await client.send(json.dumps(msg))
            message = await self.sendq.get()
            # print('send gui message')
            await self.gui_client.send_message(message)
            # await asyncio.sleep(1)

    async def read_gui_data(self):

        while True:
            msg = await self.gui_client.read_message()
            # msg = await self.gui_client.read()
            # await self.handle(msg)
            await asyncio.sleep(0.01)
            print('read_gui_data: {}'.format(msg))

    def start(self, cmd=None):
        print('Starting Controller')
        super().start(cmd)

        # task = asyncio.ensure_future(self.read_loop())
        # task = asyncio.ensure_future(self.from_child_loop())
        # task = asyncio.ensure_future(self.from_gui_loop())
        # self.task_list.append(task)

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
        for k, icfg in self.config['INST_LIST'].items():
            # for instr in self.config['INST_LIST']:
            # inst = InstrumentFactory().create(icfg['INST_CONFIG'])
            inst = InstrumentFactory().create(icfg, ui_config=self.ui_config)
            # inst.msg_buffer = self.inst_msg_buffer
            inst.to_parent_buf = self.from_child_buf
            self.instrument_map[inst.get_id()] = inst

    def get_metadata(self):

        # print(f'**** get_metadata: {self}')

        instrument_meta = dict()
        instrument_meta['instrument_meta'] = dict()
        inst_meta = instrument_meta['instrument_meta']
        for name, inst in self.instrument_map.items():
            inst_meta[name] = inst.get_metadata()

        print(f'name: {self.name}')
        print(f'label: {self.label}')
        meta = {
            'NAME': self.name,
            'LABEL': self.label,
            'instrument_meta': instrument_meta
        }
        return meta

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

    async def handle(self, msg, type=None):
        # print(f'controller.handle: {msg.to_json()}')
        # await self.send_message(msg)
        await self.message_to_ui(msg)
        # await self.message_to_gui(msg)
        # await asyncio.sleep(0.01)

    # def _create_definition(self):
    #     self.daq_definition['module'] = self.__module__
    #     self.daq_definition['class'] = self.__name__

    def get_definition_instance(self):
        return DummyController.get_definition()

    def get_definition():
        definition = dict()
        definition['module'] = DummyController.__module__
        definition['name'] = DummyController.__name__
        DAQ.daq_definition['DEFINITION'] = definition
        return DAQ.daq_definition
