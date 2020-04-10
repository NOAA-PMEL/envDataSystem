import sys
import os
import abc
import asyncio
import json
import websockets
# from client.wsclient import WSClient
# from client.serialport import SerialPortClient
# from daq.interface.interface import InterfaceFactory
# from data.message import Message
from importlib import import_module


## serial client not entering run()?

class ConnectorMessage():

    def __init__(
        self,
        address=None,
        id=None,
        body=None,
        connector_message=None
    ):
        self.address = address
        self.path = id
        self.body = body

        if connector_message:
            self.from_json(connector_message)

    def to_json(self):
        msg = {
            'address': self.address,
            'path': self.path,
            'msg': self.body
        }
        return json.dumps(msg)

    def from_json(self, message):
        try:
            print(f'con message: {message}')
            msg = json.loads(message)
        except json.JSONDecodeError:
            print(f'invalid json message')
            return

        if 'address' in msg:
            self.address = msg['address']
        if 'path' in msg:
            self.path = msg['path']
        if 'msg' in msg:
            self.body = msg['msg']
        return self


class Connector(abc.ABC):

    class_type = 'Connector'

    def __init__(
        self,
        config,
    ):

        self.config = config

        self.loop = asyncio.get_event_loop()
        self.task_list = []
        self.iface = None

        # self.from_parent_buf = asyncio.Queue(loop=self.loop)
        self.from_ui_buf = asyncio.Queue(loop=self.loop)
        self.to_ui_buf = asyncio.Queue(loop=self.loop)
        self.from_client_buf = asyncio.Queue(loop=self.loop)
        self.to_client_buf = asyncio.Queue(loop=self.loop)
        self.from_iface_buf = asyncio.Queue(loop=self.loop)
        self.to_iface_buf = asyncio.Queue(loop=self.loop)
        # self.to_ui_buf = asyncio.Queue(loop=self.loop)

        self.iface_options = dict()

        self.status = {
            'run_status': 'STOPPED',
            'connected_to_ui': False,
            'health': 'OK'
        }

        self.add_interface()

        self.clients = dict()

    def check_clients(self):

        for id, client in self.clients.items():
            if not client or client.closed:
                self.clients[id] = None

    def add_client(self, client_id, client):

        self.check_clients()

        if client_id not in self.clients or not self.clients[client_id]:
            self.clients[client_id] = client

    def get_client(self, client_id):

        self.check_clients()

        if client_id in self.clients:
            return self.clients[client_id]

        return None

    @abc.abstractmethod
    async def to_ui_loop(self):
        pass

    @abc.abstractmethod
    async def to_server_loop(self):
        pass

    def start_local_loops(self):
        pass

    def start(self):

        if self.status['run_status'] != 'STARTED':

            self.task_list.append(
                asyncio.ensure_future(self.to_ui_loop())
            )

            self.task_list.append(
                asyncio.ensure_future(self.to_server_loop())
            )

            self.task_list.append(
                asyncio.ensure_future(self.from_iface_loop())
            )

            self.start_local_loops()

            if self.iface:
                self.iface.start()

            self.status['run_status'] = 'STARTED'

    def stop(self, cmd=None):

        for t in self.task_list:
            t.cancel()

        if self.iface:
            self.iface.stop()

        self.status['run_status'] = 'STOPPED'

    async def shutdown(self):

        # if self.ui_client is not None:
        #     # self.loop.run_until_complete(self.gui_client.close())
        #     self.ui_client.sync_close()

        # for t in self.ui_task_list:
        #     t.cancel()
        self.stop()
        await asyncio.sleep(.1)

    def add_interface(self):

        # only one interface allowed, only first is used
        for k, ifcfg in self.config['IFACE_LIST'].items():
            ui_config = dict()
            ui_config['host'] = self.config['CONNECTOR_CFG']['ui_address'][0]
            ui_config['port'] = self.config['CONNECTOR_CFG']['ui_address'][1]
            # ui_config = dict()
            self.iface = InterfaceFactory().create(
                ifcfg,
                ui_config=ui_config,
                **self.iface_options
            )
            print(f'iface: {k}: {self.iface}')
            self.iface.to_parent_buf = self.from_iface_buf
            break

    async def from_iface_loop(self):

        while True:
            msg = await self.from_iface_buf.get()
            print(f'from_iface_loop: {msg.to_json()}')
            # await self.handle_iface2(msg, type='FromIFace')
            await self.handle_iface(msg, type="FromIFace")

    @abc.abstractmethod
    async def handle_iface(self, msg, type=None):
        pass

    @abc.abstractmethod
    def get_id(self):
        pass


class ConnectorServer(Connector):
    def __init__(
        self,
        config,
        connector_address=('localhost', 9001),
        ui_address=('localhost', 8001)
    ):
        super(ConnectorServer, self).__init__(config)

        if 'CONNECTOR_CFG' in config:
            cfg = config['CONNECTOR_CFG']
            if 'connector_address' in cfg:
                self.connector_address = cfg['connector_address']
            else:
                self.connector_address = connector_address
            if 'ui_address' in cfg:
                self.ui_address = cfg['ui_address']
            else:
                self.ui_address = ui_address
        else:
            self.connector_address = connector_address
            self.ui_address = ui_address

        self.server = None

    def get_id(self):
        return 'ConnectorServer'

    async def handle_iface(self, msg, type=None):
        print(f'!!! msg: {msg}, type={type}')
        if (type == 'FromIFace'):
            # if (msg.subject == 'DATA'):
            con_msg = ConnectorMessage().from_json(
                msg.body['DATA']
            )
            print(f'!!! con_message: {msg.to_json()}, {con_msg.to_json()}')
            await self.from_ui_buf.put(con_msg)


class WSConnectorServer(ConnectorServer):

    def __init__(
        self,
        config,
        connector_address=('localhost', 9001),
        ui_address=('localhost', 8001)
    ):
        super().__init__(config, ui_address)

    def start(self):
        super().start()

        self.ws_server_protocol = websockets.server.serve(
            self.read_ws,
            self.connector_address[0],
            self.connector_address[1],
        )
        self.server = self.loop.run_until_complete(
            self.ws_server_protocol
        )

    async def shutdown(self):
        await super().shutdown()

        self.server.close()
        await self.server.wait_closed()

    async def read_ws(self, ws, path):

        self.add_client(path, ws)

        # msg = await ws.recv()
        async for msg in ws:
            print(f'read_ws: {msg}')
            con_msg = ConnectorMessage(
                address=self.ui_address,
                id=path,
                body=msg,
            )

            await self.to_ui_buf.put(con_msg)

    async def to_ui_loop(self):

        # con_msg = ConnectorMessage(
        #     address=self.ui_address,
        #     id='/a/b/c',
        #     body='test',
        # )
        # body = f'{con_msg.to_json()}\n'
        # test = Message(
        #         sender_id=self.get_id(),
        #         msgtype=Connector.class_type,
        #         subject='SEND',
        #         body=body,
        # )
        # print(f'test msg: {test.to_json()}')

        # await self.iface.message_from_parent(test)
            
        while True:

            con_msg = await self.to_ui_buf.get()
            body = f'{con_msg.to_json()}\n'
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Connector.class_type,
                subject='SEND',
                body=body,
            )
            print(f'msg: {msg.to_json()}')
            await self.iface.message_from_parent(msg)

    async def to_server_loop(self):

        while True:
            con_msg = await self.from_ui_buf.get()
            # msg = ConnectorMessage()
            # msg.from_json(con_msg)

            # con_msg = msg.body

            # if id in con_msg:
            if "path" in con_msg:
                # client = self.get_client(con_msg['id'])
                client = self.get_client(con_msg['path'])
                if client:
                    # msg = f'{con_msg["body"]}\n'
                    msg = f'{con_msg["body"]}'
                    await client.send(msg)


class ConnectorUI(Connector):
    def __init__(
        self,
        config,
        # connector_address=('localhost', 9001),
        ui_address=('localhost', 8001)
    ):
        super(ConnectorUI, self).__init__(config)

        if 'CONNECTOR_CFG' in config:
            cfg = config['CONNECTOR_CFG']
            if 'ui_address' in cfg:
                self.ui_address = cfg['ui_address']
            else:
                self.ui_address = ui_address
        else:
            self.ui_address = ui_address

        print(f'self.ui_address: {self.ui_address}')
        # self.connector_address = connector_address
        # self.ui_address = ui_address
        # self.server = None

    def get_id(self):
        return 'ConnectorUI'

    def start_local_loops(self):
        self.task_list.append(
            asyncio.ensure_future(self.read_client_loop())
        )

    async def read_client_loop(self):

        while True:
            # loop through ws clients and read if
            #   messages are ready
            for path, client in self.clients.items():
                if client.message_waiting():
                    msg = await client.read()
                    con_msg = ConnectorMessage(
                        address=self.ui_address,
                        id=path,
                        body=msg,
                    )
                    print(f'read_client_loop: {con_msg.to_json()}')
                    await self.from_ui_buf.put(con_msg)
            await asyncio.sleep(.1)

    async def handle_iface(self, msg, type=None):
        # super().handle_iface(msg, type)
        print(f'handle iface ui: {msg.to_json()}')
        if (type == 'FromIFace'):
            # if (msg.subject == 'DATA'):
            con_msg = ConnectorMessage().from_json(
                msg.body['DATA']
            )
            print(f'con_message: {msg.to_json()}, {con_msg.to_json()}')
            await self.to_ui_buf.put(con_msg)


class WSConnectorUI(ConnectorUI):

    def __init__(
        self,
        config,
        # connector_address=('localhost', 9001),
        ui_address=('localhost', 8001)
    ):
        super().__init__(config, ui_address)

        # self.ws_server_protocol = websockets.server.serve(
        #     self.read_ws,
        #     self.connector_address[0],
        #     self.connector_address[1],
        # )
        # self.server = self.loop.run_until_complete(
        #     self.ws_server_protocol
        # )

    def get_uri(self, address, path):

        uri = f'ws://{address[0]}'
        uri += f':{address[1]}'
        uri += path.replace(" ", "")
        return uri

    # async def read_ws(self, ws, path):

    #     self.add_client(path, ws)

    #     msg = await ws.recv()
    #     # async for msg in ws:
    #     con_msg = ConnectorMessage(
    #         address=self.ui_address,
    #         id=path,
    #         body=msg,
    #     )

    #     await self.to_ui_buf.put(con_msg)

    async def to_ui_loop(self):

        while True:

            con_msg = await self.to_ui_buf.get()
            print(f'to_ui_loop: {con_msg}')
            
            if con_msg.address and con_msg.path:
                path = con_msg.path
                uri = self.get_uri(
                    con_msg.address,
                    path
                )
                if path not in self.clients:
                    self.clients[path] = WSClient(uri=uri)

                await self.clients[path].send(con_msg.body)
            # await asyncio.sleep(.1)

    async def to_server_loop(self):

        while True:
            con_msg = await self.from_ui_buf.get()
            # msg = ConnectorMessage()
            # msg.from_json(con_msg)

            # con_msg = msg.body
            body = f'{con_msg.to_json()}\n'
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Connector.class_type,
                subject='SEND',
                body=body,
            )
            print(f'msg: {msg.to_json()}')
            await self.iface.message_from_parent(msg)
            # await asyncio.sleep(0.1)


async def heartbeat():
    while True:
        print('lub-dub')
        await asyncio.sleep(10)


def main(connector_type):

    def_cfg = dict()
    def_cfg['CONNECTOR_CFG'] = {
        'connector_address': ('localhost', 9001),
        'ui_address': ('localhost', 8001)
    }
    def_cfg["IFACE_LIST"] = {

        "serial_usb0": {
            "INTERFACE": {
                "MODULE": "daq.interface.interface",
                "CLASS": "SerialPortInterface"
            },
            "IFCONFIG": {
                "LABEL": "serial_usb0",
                "ADDRESS": "/dev/ttyUSB0",
                "baudrate": 38400,
                "SerialNumber": "0001"
            }
        }
    }

    connector_config = None
    try:
        con_settings = import_module(
            'connector.connector_settings'
        )
        connector_config = con_settings.connector_config

        # if 'name' in connector_config:
        #     self.server_name = connector_config['name']

        # if 'ui_config' in server_config:
        #     self.ui_config = server_config['ui_config']

        # if 'base_file_path' in server_config:
        #     self.base_file_path = (
        #         server_config['base_file_path']
        #     )

    except ModuleNotFoundError:
        print(f'settings file not found, using defaults')

    if not connector_config:
        connector_config = def_cfg

    if connector_type == 'server':
        con = WSConnectorServer(
            connector_config,
            # connector_address=('localhost', 9001),
            # ui_address=('localhost', 8001)
        )
    elif connector_type == 'ui':
        con = WSConnectorUI(
            connector_config,
            # connector_address=('localhost', 9001),
            # ui_address=('localhost', 8001)
        )
    con.start()

    event_loop = asyncio.get_event_loop()
    asyncio.ensure_future(heartbeat())
    task_list = asyncio.Task.all_tasks()

    try:
        event_loop.run_until_complete(asyncio.wait(task_list))
        event_loop.run_forever()
    except KeyboardInterrupt:
        print('closing server')
        # start_server.close()
        # asyncio.wait(connector.shutdown())
        # shutdown()
        # print(f'task_list: {task_list}')
        for task in task_list:
            # print("cancel task")
            # print(f'task: {task}')
            task.cancel()

        # connector.shutdown()

        event_loop.run_until_complete(con.shutdown())
        # event_loop.run_until_complete(asyncio.wait(asyncio.ensure_future(connector.shutdown())))
        # server.close()
        # event_loop.run_forever()
        # event_loop.run_until_complete(asyncio.wait(asyncio.ensure_future(shutdown)))

    finally:

        print('closing event loop')
        event_loop.close()


if __name__ == "__main__":
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # print(BASE_DIR)
    sys.path.append(os.path.join(BASE_DIR, 'envdsys/shared'))

    # from daq.manager.sys_manager import SysManager
    # from daq.controller.controller import ControllerFactory  # , Controller
    from client.wsclient import WSClient
    # import utilities.util as util
    from daq.interface.interface import InterfaceFactory
    from data.message import Message

    # main('ui')
    main(sys.argv[1])
