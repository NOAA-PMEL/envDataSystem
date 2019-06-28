import asyncio
import time
import math
from daq.interface.interface import InterfaceFactory, Interface
from daq.instrument.instrument import InstrumentFactory, Instrument
from daq.controller.controller import ControllerFactory, Controller
from client.client import WSClient
# import websockets
import utilities.util as util
from datetime import datetime
import functools
import json


class FEServer(asyncio.Protocol):

    clients = {}

    def __init__(self, sendq):
        self.buffer = ""
        self.sendq = sendq
        print('init: ')
        print(self.sendq)
        # self.clients = {}
        self.task_list = []

        self.task_list.append(
            asyncio.ensure_future(self.read_loop())
        )

    async def read_loop(self):

        while True:

            msg = await self.sendq.get()
            # print('sendq: {}'.format(msg))
            self.send_to_clients(msg)
            # self.transport.write(msg)
            await asyncio.sleep(.1)

    def connection_made(self, transport):
        print('Connection made!')
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        FEServer.clients[self.address] = transport

        print(FEServer.clients, len(FEServer.clients))

    def data_received(self, data):
        # self.transport.write(data)
        self.send_to_clients(data.decode())
        print('data received: {}'.format(data.decode()))
        # self.broadcast(data)

    def eof_received(self):
        if self.transport.can_write_eof():
            self.transport.write_eof()

    def connection_lost(self, error):
        # if error:
        #     self.log.error('ERROR: {}'.format(error))
        # else:
        #     self.log.debug('closing')

        del self.clients[self.address]
        print(self.clients)
        super().connection_lost(error)

    def send_to_clients(self, msg):
        # print('here_send')
        print('msg = {}'.format(msg))
        # self.transport.write(msg.encode())
        # self.transport.write((msg+'\r\n').encode())
        print('send to clients: ', FEServer.clients)
        for k, v in FEServer.clients.items():
            print(k, v)
            # v.write(msg.encode())
            # w=v
            # w.write((msg+'\n').encode('idna'))
            # w.write((msg+'\r\n').encode())
            v.write((msg+'\r\n').encode())


class DAQServer():

    def __init__(self, config):
        self.controller_list = []
        self.controller_map = dict()
        self.task_list = []
        self.last_data = {}
        self.run_flag = False

        print(config)

        self.loop = asyncio.get_event_loop()

        # TODO: Add id - hostname, label, ?

        self.create_msg_buffer(config=None)
        self.add_controllers(config)

        # import config.dummy_cfg
        # testcfg = config.dummy_cfg.dummycpc_inst_cfg
        #
        # inst1 = InstrumentFactory().create(testcfg)
        # inst1.start()
        #
        # self.controller_list.append(inst1)

        # task = asyncio.ensure_future(self.output_to_screen())
        # self.task_list.append(task)
        # self.sendq = asyncio.Queue(loop=asyncio.get_event_loop())

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
        self.ws_client = WSClient(uri='ws://localhost:8001/ws/data/lobby/')
        # asyncio.ensure_future(self.ws_client)
        self.server = self.ws_client
        # asyncio.get_event_loop().run_forever(self.server)
        # server = event_loop.run_until_complete(factory)

    def create_msg_buffer(self, config):
        # self.read_buffer = MessageBuffer(config=config)
        self.controller_msg_buffer = asyncio.Queue(loop=self.loop)

    def add_controllers(self, config):
        print(config['CONT_LIST'])
        for k, icfg in config['CONT_LIST'].items():
            # for ctr in config['CONT_LIST']:
            print(f'key: {k}')
            # print(F'key = {k}')
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            # controller = ControllerFactory().create(icfg['CONT_CONFIG'])
            controller = ControllerFactory().create(icfg)
            controller.msg_buffer = self.controller_msg_buffer
            self.controller_map[controller.get_id()] = controller

    async def output_to_screen(self):
        while True:

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
            await self.sendq.put(json.dumps(data))
            # FEServer.send_to_clients(data)

            await asyncio.sleep(util.time_to_next(1))

    def shutdown(self):
        print('shutdown:')

        asyncio.get_event_loop().run_until_complete(self.server.shutdown())

        for controller in self.controller_list:
            # print(sensor)
            controller.stop()

        # tasks = asyncio.Task.all_tasks()
        for t in self.task_list:
            # print(t)
            t.cancel()
        # print("Tasks canceled")
        # asyncio.get_event_loop().stop()

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
    # for controller in controller_list:
    #     # print(sensor)
    #     controller.stop()

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
                    'LABEL': 'test_dummy',
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
                'LABEL': 'test_controller',
                'INST_LIST': inst_config, 
            }
        },
    }

    server_config = {
        'CONT_LIST': cont_config,
    }

    server = DAQServer(server_config)

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
        event_loop.run_forever()

    finally:

        print('closing event loop')
        event_loop.close()
