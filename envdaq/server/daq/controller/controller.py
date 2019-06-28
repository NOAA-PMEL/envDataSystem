import abc
import importlib
import asyncio
import sys
import json
from client.client import WSClient
from instrument.instrument import InstrumentFactory, Instrument


class ControllerFactory():

    @staticmethod
    def create(config):
        create_cfg = config['CONTROLLER']
        instconfig = config['CONTCONFIG']

        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            mod_ = importlib.import_module(create_cfg['MODULE'])
            cls_ = getattr(mod_, create_cfg['CLASS'])
            return cls_(instconfig)

        except:  # better to catch ImportException?
            print("Unexpected error:", sys.exc_info()[0])
            raise


class Controller(abc.ABC):

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

    def __init__(self):
        self.instrument_list = []
        self.inst_map = {}

        self.event_loop = asyncio.get_event_loop()

        self.sendq = asyncio.Queue(loop=self.event_loop)
        # self.readq = asyncio.Queue(loop=self.event_loop)

        # TODO: eventuallly this will be from factory and in config
        self.gui_client = WSClient(uri='ws://localhost:8000/ws/data/lobby/')
        asyncio.ensure_future(self.read_gui_data())
        asyncio.ensure_future(self.send_data())

    # # TODO: How do we want to id instruments? Need to clean this up
    # def add_instrument(self, instrument):
    #     self.inst_map[instrument.get_signature()] = instrument

    def add_instruments(self):
        for k, icfg in self.config['INST_LIST'].items():
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            inst = InstrumentFactory().create(icfg['INST_CONFIG'])
            inst.msg_buffer = self.inst_msg_buffer
            self.inst_map[inst.get_id()] = inst
    
    async def send_message(self, message):
        # TODO: Do I need queues? Message and string methods?
        await self.sendq.put(message.to_json())

    async def send_gui_data(self):

        while True:
            # body = 'fake message - {}'.format(datetime.utcnow().isoformat(timespec='seconds'))
            # msg = {'message': body}
            # message = Message(type='Test', sender_id='me', subject='test', body=msg)
            # # print('send_data: {}'.format(msg))
            # print('send_data: {}'.format(message.to_json))
            # # await client.send(json.dumps(msg))
            msg = await self.sendq.get()
            await self.gui_client.send_message(msg)
            # await asyncio.sleep(1)

    async def read_gui_data(self, client):

        while True:
            msg = await self.gui_client.read_message()
            await self.handle(msg)
            # print('read_loop: {}'.format(msg))

    @abc.abstractmethod
    async def handle(self, msg):
        pass


class BasicController(Controller):

    def __init__(self):
        super().__init__()

    async def handle(self, msg):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class DummyController(Controller):

    def __init__(self):
        super().__init__()
        pass
