import os
import sys
import asyncio
from importlib import import_module
from datetime import datetime
import json

# These are now imported below after path is set

# from daq.manager.sys_manager import SysManager
# from daq.controller.controller import ControllerFactory  # , Controller
# from client.wsclient import WSClient
# # from data.message import Message
# # import websockets
# import utilities.util as util
# import functools
# from plots.plots import PlotManager


class DAQServer():

    def __init__(
        self,
        config=None,
        server_name=None,
        ui_config=None
    ):
        self.controller_list = []
        self.controller_map = dict()
        self.task_list = []
        self.last_data = {}
        self.run_flag = False
        
        # defaults
        self.server_name = ''
        self.ui_config = {
            'host': 'localhost',
            'port': 8001,
        }
        self.base_file_path = '/tmp'
        
        self.loop = asyncio.get_event_loop()

        # try to import config from daq_settings.py
        try:
            daq_settings = import_module('daq_settings')
            server_config = daq_settings.server_config
            
            if 'name' in server_config:
                self.server_name = server_config['name']
            
            if 'ui_config' in server_config:
                self.ui_config = server_config['ui_config']

            if 'base_file_path' in server_config:
                self.base_file_path = (
                    server_config['base_file_path']
                )

        except ModuleNotFoundError:
            print(f'settings file not found, using defaults')
            self.server_name = ''

        # override config file settings
        if server_name:
            self.server_name = server_name
        if ui_config:
            self.ui_config = ui_config

        self.config = config

        self.ui_client = None

        # start managers
        SysManager.start()

        # Begin startup
        asyncio.ensure_future(self.open())

    def create_msg_buffer(self):
        # if need config, use self.config
        # self.read_buffer = MessageBuffer(config=config)
        self.from_child_buf = asyncio.Queue(loop=self.loop)

    def add_controllers(self):
        print('add_controllers()')
        config = self.config
        # print(config)
        # print(config['ENVDAQ_CONFIG']['CONT_LIST'])
        for k, icfg in config['ENVDAQ_CONFIG']['CONT_LIST'].items():
            # for ctr in config['CONT_LIST']:
            print(f'key: {k}')
            # print(F'key = {k}')
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            # controller = ControllerFactory().create(icfg['CONT_CONFIG'])
            controller = ControllerFactory().create(
                icfg,
                ui_config=self.ui_config,
                base_file_path=self.base_file_path
            )
            print(controller)
            controller.to_parent_buf = self.from_child_buf
            self.controller_map[controller.get_id()] = controller

    async def send_message(self, message):
        # TODO: Do I need queues? Message and string methods?
        # await self.sendq.put(message.to_json())
        await self.to_gui_buf.put(message)

    async def send_gui_loop(self):

        print('send_gui_loop init')
        while True:
            message = await self.to_gui_buf.get()
            # print('send server message')
            await self.ui_client.send_message(message)
            # await asyncio.sleep(1)

    async def read_gui_loop(self):

        # print('read_gui_loop init')
        while True:
            msg = await self.ui_client.read_message()
            # print(f'msg = {msg.to_json()}')
            await self.handle(msg, src='FromGUI')
            # print(msg)
            # print('read_loop: {}'.format(msg))

    async def output_to_screen(self):
        while True:

            # TODO: use controller_msg_buffer here
            # for controller in self.controller_list:
            #
            #     data = controller.get_last()
            #     # parse data
            #     print('data: {}'.format(data))
            ts = datetime.utcnow().isoformat(timespec='seconds')
            msgstr = 'This is a test {}'.format(ts)
            data = {
                'message': msgstr,
            }
            print('data msg: {}'.format(data))
            await self.to_gui_buf.put(json.dumps(data))
            # FEServer.send_to_clients(data)

            await asyncio.sleep(util.time_to_next(1))

    # TODO: add run() to check for broken connections

    async def open(self):
        # task = asyncio.ensure_future(self.read_loop())
        # self.task_list.append(task)

        cfg_fetch_freq = 10  # seconds

        # for k, v in self.inst_map.items():
        #     self.inst_map[k].start()
        gui_config = self.ui_config
        gui_ws_address = f'ws://{gui_config["host"]}:{gui_config["port"]}/'
        gui_ws_address += 'ws/envdaq/daqserver/'
        # create gui client
        print(f'Starting ui client: {gui_ws_address}')

        self.ui_client = WSClient(uri=gui_ws_address)
        while self.ui_client.isConnected() is not True:
            # print(f'waiting for is_conncted {self.ui_client.isConnected()}')
            # self.gui_client = WSClient(uri=gui_ws_address)
            # print(f"gui client: {self.gui_client.isConnected()}")
            await asyncio.sleep(1)

        print(f'gui client is connected: {self.ui_client.isConnected()}')

        print(f'Creating message loops')
        self.to_gui_buf = asyncio.Queue(loop=self.loop)
        self.task_list.append(asyncio.ensure_future(self.send_gui_loop()))
        self.task_list.append(asyncio.ensure_future(self.read_gui_loop()))

        print('sync DAQ')
        # system_def = SysManager.get_definitions_all()
        # print(f'system_def: {system_def}')
        sys_def = Message(
            sender_id='daqserver',
            msgtype='DAQServer',
            subject='CONFIG',
            body={
                'purpose': 'SYNC',
                'type': 'SYSTEM_DEFINITION',
                'data': SysManager.get_definitions_all()

            }
        )
        await self.to_gui_buf.put(sys_def)

        print('set self.config')
        while self.config is None:
            # get config from gui
            print(f'Getting config from gui')
            req = Message(
                sender_id='daqserver',
                msgtype='DAQServer',
                subject='CONFIG',
                body={
                    'purpose': 'REQUEST',
                    'type': 'ENVDAQ_CONFIG',
                    'server_name': self.server_name
                }
            )
            await self.to_gui_buf.put(req)
            await asyncio.sleep(cfg_fetch_freq)

        # print('Waiting for config...')
        # while self.config is None:
        #     pass

        # print(self.config)
        print('Create message buffers...')
        self.create_msg_buffer()
        print('Add controllers...')
        self.add_controllers()

        # TODO: Create 'health monitor' to check for status
        #       this should allow for all components to register
        #       so we know when things are ready, broken, etc

        # for now...sleep for a set amount of time to allow
        #   everything to get set up
        print(f'Waiting for setup...')
        await asyncio.sleep(5)
        print(f'Waiting for setup...done.')

        # PlotManager.get_server().start()
        status = Message(
            sender_id='DAQ_SERVER',
            msgtype='GENERIC',
            subject="READY_STATE",
            body={
                'purpose': 'STATUS',
                'status': 'READY',
                # 'note': note,
            }
        )
        print(f'_____ send no wait _____: {status.to_json()}')
        await self.to_gui_buf.put(status)

    def start(self):
        pass

    def stop(self):
        # TODO: check if stopped already

        # self.gui_client.sync_close()

        for k, controller in self.controller_map.items():
            print(controller)
            controller.stop()
        # for instrument in self.inst_map:
        #     # print(sensor)
        #     instrument.stop()

        # tasks = asyncio.Task.all_tasks()
        # for t in self.task_list:
        #     # print(t)
        #     t.cancel()

    async def from_child_loop(self):
        # print(f'started from_child_loop: {self.name} {self.from_child_buf}')
        # while self.from_child_buf is None:
        #     pass

        while True:
            msg = await self.from_child_buf.get()
            print(f'daq_server:from_child_loop: {msg}')
            await self.handle(msg, src="FromChild")
            # await asyncio.sleep(.1)

    async def read_loop(self):
        while True:
            # msg = await self.inst_msg_buffer.get()
            # TODO: should handle be a async? If not, could block
            # await self.handle(msg)
            await asyncio.sleep(.1)

    async def handle(self, msg, src=None):
        print(f'****controller handle: {src} - {msg.to_json()}')

        if (src == 'FromGUI'):
            d = msg.to_dict()
            if 'message' in d:
                content = d['message']
                if (content['SUBJECT'] == 'CONFIG'):
                    if (content['BODY']['purpose'] == 'REPLY'):
                        config = content['BODY']['config']
                        self.config = config
            elif (src == 'FromChild'):
                print(f'fromChild: {content}')

        await asyncio.sleep(0.01)

    def shutdown(self):
        print('daq_server:shutdown:')

        self.stop()

        # asyncio.get_event_loop().run_until_complete(self.ws_client.shutdown())
        # if self.ws_client is not None:
        #     self.ws_client.sync_close()

        if self.ui_client is not None:
            self.loop.run_until_complete(self.ui_client.close())

        for k, controller in self.controller_map.items():
            controller.shutdown()
        # for controller in self.controller_list:
        #     # print(sensor)
        #     controller.stop()

        # tasks = asyncio.Task.all_tasks()
        for t in self.task_list:
            # print(t)
            t.cancel()
        # print("Tasks canceled")
        # asyncio.get_event_loop().stop()

        # self.server.close()


async def heartbeat():
    while True:
        # print('lub-dub')
        await asyncio.sleep(util.time_to_next(10))


# async def output_to_screen(sensor_list):
async def output_to_screen():
    while True:
        print(datetime.utcnow().isoformat(timespec='seconds'))
        await asyncio.sleep(util.time_to_next(1))


def shutdown(server):
    print('shutdown:')
    # for k, controller in controller_map:
    #     # print(sensor)
    #     controller.stop()

    if server is not None:
        server.shutdown()

    tasks = asyncio.Task.all_tasks()
    for t in tasks:
        # print(t)
        t.cancel()
    print("Tasks canceled")
    asyncio.get_event_loop().stop()
    # await asyncio.sleep(1)


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # print(BASE_DIR)
    sys.path.append(os.path.join(BASE_DIR, 'envdsys/shared'))

    from daq.manager.sys_manager import SysManager
    from daq.controller.controller import ControllerFactory  # , Controller
    from client.wsclient import WSClient
    import utilities.util as util
    from data.message import Message

    iface_config = {
        'test_interface': {
            'INTERFACE': {
                'MODULE': 'daq.interface.interface',
                'CLASS': 'DummyInterface',
            },
            'IFCONFIG': {
                'LABEL': 'test_interface',
                'ADDRESS': 'DummyAddress',
                'SerialNumber': '1234'
            },
        },
    }

    inst_config = {
        'test_dummy': {
            'INSTRUMENT': {
                'MODULE': 'daq.instrument.instrument',
                'CLASS': 'DummyInstrument',
            },
            'INSTCONFIG': {
                'DESCRIPTION': {
                    'LABEL': 'Test Dummy',
                    'SERIAL_NUMBER': '1234',
                    'PROPERTY_NUMBER': 'CD0001234',
                },
                'IFACE_LIST': iface_config,
            }
        }
    }

    cont_config = {
        'test_controller': {
            'CONTROLLER': {
                'MODULE': 'daq.controller.controller',
                'CLASS': 'DummyController',
            },
            'CONTCONFIG': {
                'LABEL': 'Test Controller',
                'INST_LIST': inst_config,
                'AUTO_START': True,
            }
        },
    }

    server_config = {
        'CONT_LIST': cont_config,
    }

    # print(json.dumps(server_config))
    # with open('data.json', 'w') as f:
    # json.dump(server_config, f)
    # server = DAQServer(server_config)
    server = DAQServer()

    event_loop = asyncio.get_event_loop()

    task = asyncio.ensure_future(heartbeat())
    # task = asyncio.ensure_future(output_to_screen())
    task_list = asyncio.Task.all_tasks()
#
    try:
        event_loop.run_until_complete(asyncio.wait(task_list))
        # event_loop.run_forever()
    except KeyboardInterrupt:
        print('closing client')
        shutdown(server)
        # shutdown(None)
        event_loop.run_forever()

    finally:

        print('closing event loop')
        event_loop.close()
