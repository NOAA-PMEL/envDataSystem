import asyncio
# import time
# import math
# from daq.interface.interface import InterfaceFactory, Interface
# from daq.instrument.instrument import InstrumentFactory, Instrument
# from daq.controller.controller import ControllerFactory, Controller
from client.client import WSClient
from data.message import Message
# import websockets
import utilities.util as util
from datetime import datetime
# import functools
import json


# class FEServer(asyncio.Protocol):

#     clients = {}

#     def __init__(self, sendq):
#         self.buffer = ""
#         self.sendq = sendq
#         print('init: ')
#         print(self.sendq)
#         # self.clients = {}
#         self.task_list = []

#         self.task_list.append(
#             asyncio.ensure_future(self.read_loop())
#         )

#     async def read_loop(self):

#         while True:

#             msg = await self.sendq.get()
#             # print('sendq: {}'.format(msg))
#             self.send_to_clients(msg)
#             # self.transport.write(msg)
#             await asyncio.sleep(.1)

#     def connection_made(self, transport):
#         print('Connection made!')
#         self.transport = transport
#         self.address = transport.get_extra_info('peername')
#         FEServer.clients[self.address] = transport

#         print(FEServer.clients, len(FEServer.clients))

#     def data_received(self, data):
#         # self.transport.write(data)
#         self.send_to_clients(data.decode())
#         print('data received: {}'.format(data.decode()))
#         # self.broadcast(data)

#     def eof_received(self):
#         if self.transport.can_write_eof():
#             self.transport.write_eof()

#     def connection_lost(self, error):
#         # if error:
#         #     self.log.error('ERROR: {}'.format(error))
#         # else:
#         #     self.log.debug('closing')

#         del self.clients[self.address]
#         print(self.clients)
#         super().connection_lost(error)

#     def send_to_clients(self, msg):
#         # print('here_send')
#         print('msg = {}'.format(msg))
#         # self.transport.write(msg.encode())
#         # self.transport.write((msg+'\r\n').encode())
#         print('send to clients: ', FEServer.clients)
#         for k, v in FEServer.clients.items():
#             print(k, v)
#             # v.write(msg.encode())
#             # w=v
#             # w.write((msg+'\n').encode('idna'))
#             # w.write((msg+'\r\n').encode())
#             v.write((msg+'\r\n').encode())


class DAQServer():

    def __init__(self, config=None, gui_config=None):
        self.controller_list = []
        self.controller_map = dict()
        self.task_list = []
        self.last_data = {}
        self.run_flag = False

        self.loop = asyncio.get_event_loop()

        if gui_config is None:
            gui_config = {
                'host': 'localhost',
                'port': 8001,
            }
        self.gui_config = gui_config

        self.config = config

        self.gui_client = None

        # gui_ws_address = f'ws://{gui_config["host"]}:{gui_config["port"]}/'
        # gui_ws_address += 'ws/envdaq/daqserver/'
        # # create gui client
        # self.gui_client = WSClient(uri=gui_ws_address)

        # self.to_gui_buf = asyncio.Queue(loop=asyncio.get_event_loop())
        # task_list.append(
        #     asyncio.ensure_future(self.send_gui_loop())
        # )
        # task_list.append(
        #     asyncio.ensure_future(self.send_gui_loop())
        # )

        # Begin startup
        asyncio.ensure_future(self.start())

        # if config is None:
        #     # get config from gui
        #     await self.to_gui_buf.put(
        #         Message(
        #             sender_id='daqserver',
        #             msgtype='DAQServer',
        #             subject='CONFIG',
        #             body={
        #                 'purpose': 'REQUEST',
        #                 'type': 'ENVDAQ_CONFIG',
        #             }
        #         )
        #     )
        # else:
        #     self.config = config

        # print(config)

        # TODO: Add id - hostname, label, ?

        # self.create_msg_buffer()
        # self.add_controllers()

        # import config.dummy_cfg
        # testcfg = config.dummy_cfg.dummycpc_inst_cfg
        #
        # inst1 = InstrumentFactory().create(testcfg)
        # inst1.start()
        #
        # self.controller_list.append(inst1)

        # task = asyncio.ensure_future(self.output_to_screen())
        # self.task_list.append(task)
        # self.to_gui_buf = asyncio.Queue(loop=asyncio.get_event_loop())

        # SERVER_ADDRESS = ('127.0.0.1', 8299)
        # server_factory = functools.partial(
        #     FEServer,
        #     sendq=self.sendq,
        # )
        # ws_factory =
        #   WebSocketClientFactory('ws://localhost:8000/ws/data/lobby/')
        # ws_factory.protocol = WSClientProtocol
        # WSSERVER_ADDRESS = ('127.0.0.1', 8000)
        # client_args = functools.partial(
        #     WSClientProtocol,
        #     sendq=self.sendq,
        # )
        # self.server =
        #   asyncio.get_event_loop().create_server(server_factory, *SERVER_ADDRESS)
        # asyncio.ensure_future(self.server)
        # self.ws_client =
        #   asyncio.get_event_loop().create_connection(client_args, *WSSERVER_ADDRESS)
        # self.ws_client = websockets.connect(
        #     'ws://localhost:8000/ws/data/lobby/',
        #     create_protocol=WSClientProtocol,
        #     )

        # GOOD CONNECTION ****
        # self.gui_client = WSClient(uri='ws://localhost:8001/ws/envdaq/daqserver/')
        # asyncio.ensure_future(self.send_gui_data())

        # get config from front end
        # await self.send_gui_data
        # self.gui_client = WSClient(uri='ws://localhost:8001/ws/envdaq/server/')
        # asyncio.ensure_future(self.send_gui_data())
        # asyncio.ensure_future(self.send_gui_data())
        # # asyncio.ensure_future(self.ws_client())
        # self.server = self.ws_client
        # self.ws_client.open()
        # ********************

        # asyncio.get_event_loop().run_forever(self.server)
        # server = event_loop.run_until_complete(factory)

    def create_msg_buffer(self):
        # if need config, use self.config
        # self.read_buffer = MessageBuffer(config=config)
        self.from_child_buf = asyncio.Queue(loop=self.loop)

    def add_controllers(self):
        config = self.config
        print(config['CONT_LIST'])
        for k, icfg in config['CONT_LIST'].items():
            # for ctr in config['CONT_LIST']:
            print(f'key: {k}')
            # print(F'key = {k}')
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            # controller = ControllerFactory().create(icfg['CONT_CONFIG'])
            controller = ControllerFactory().create(icfg)
            controller.to_parent_buf = self.from_child_buf
            self.controller_map[controller.get_id()] = controller

    async def send_message(self, message):
        # TODO: Do I need queues? Message and string methods?
        # await self.sendq.put(message.to_json())
        await self.to_gui_buf.put(message)

    async def send_gui_loop(self):

        print('send_gui_loop init')
        while True:
            # body = 'fake message - {}'.format(datetime.utcnow().isoformat(timespec='seconds'))
            # msg = {'message': body}
            # message = Message(type='Test', sender_id='me', subject='test', body=msg)
            # # print('send_data: {}'.format(msg))
            # print('send_data: {}'.format(message.to_json))
            # # await client.send(json.dumps(msg))
            message = await self.to_gui_buf.get()
            print('send server message')
            await self.gui_client.send_message(message)
            # await asyncio.sleep(1)

    async def read_gui_loop(self):

        # print('read_gui_loop init')
        while True:
            msg = await self.gui_client.read_message()
            print(f'msg = {msg.to_json()}')
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

    async def start(self):
        # task = asyncio.ensure_future(self.read_loop())
        # self.task_list.append(task)

        # for k, v in self.inst_map.items():
        #     self.inst_map[k].start()
        gui_config = self.gui_config
        gui_ws_address = f'ws://{gui_config["host"]}:{gui_config["port"]}/'
        gui_ws_address += 'ws/envdaq/daqserver/'
        # create gui client
        print(f'Starting gui client: {gui_ws_address}')

        self.gui_client = WSClient(uri=gui_ws_address)

        print(f'Creating message loops')
        self.to_gui_buf = asyncio.Queue(loop=self.loop)
        self.task_list.append(asyncio.ensure_future(self.send_gui_loop()))
        self.task_list.append(asyncio.ensure_future(self.read_gui_loop()))

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
                }
            )
            await self.to_gui_buf.put(req)
            await asyncio.sleep(1)

        print('Waiting for config...')
        while self.config is None:
            pass

        print(self.config)

        self.create_msg_buffer()
        # self.add_controllers()

    def stop(self):
        # self.gui_client.sync_close()
        if self.gui_client is not None:
            self.loop.run_until_complete(self.gui_client.close())

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
            print(f'here1: {msg.subject}')
            if 'message' in d:
                print('here2')
                content = d['message']
                print(f'content = {content}')
                if (content['SUBJECT'] == 'CONFIG'):
                    if (content['BODY']['purpose'] == 'RESPONSE'):
                        config = content['BODY']['config']
                        print(f'reponse from gui: {config}')
                        self.config = config
            elif (src == 'FromChild'):
                print(f'fromChild: {content}')

        await asyncio.sleep(0.01)

    def shutdown(self):
        print('shutdown:')

        # asyncio.get_event_loop().run_until_complete(self.ws_client.shutdown())
        # if self.ws_client is not None:
        #     self.ws_client.sync_close()

        for controller in self.controller_list:
            # print(sensor)
            controller.stop()

        # tasks = asyncio.Task.all_tasks()
        for t in self.task_list:
            # print(t)
            t.cancel()
        # print("Tasks canceled")
        # asyncio.get_event_loop().stop()

        self.stop()
        # self.server.close()

# def time_to_next(sec):
#     now = time.time()
#     delta = sec - (math.fmod(now, sec))
#     return delta


async def heartbeat():
    while True:
        print('lub-dub')
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
