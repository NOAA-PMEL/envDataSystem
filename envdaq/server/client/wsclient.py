import websockets
import asyncio
from client.client import ClientConnection


class WSClient(ClientConnection):

    def __init__(
        self,
        *,
        uri=None,
        # host=None,
        # port=None,
        # address=None,
        loop=None,
        auto_connect=True,
        **kwargs
    ):
        super(WSClient, self).__init__(
            uri=uri,
            loop=loop,
            auto_connect=auto_connect,
            **kwargs,
        )

    # self.host = host
    # self.port = port
    # self.address = address

    async def connect(self):
        self.connect_state = ClientConnection.CONNECTING
        try:
            print(f'WSClient.connect.uri: {self.uri}')
            self.client = await websockets.client.connect(self.uri)
            self.is_connected = True
            # print(f'WSClient.connect(): {self.client}')
            self.connect_state = ClientConnection.CONNECTED
        except ConnectionError:
            print("not connected")
            self.client = None
            self.is_connected = False
            self.connect_state = ClientConnection.CLOSED

    async def open(self):

        # print('WSClient.open')
        # timeout = 10
        try:
            self.client = await websockets.client.connect(self.uri)
            self.is_connected = True
        except ConnectionError:
            print("not connected")
            self.client = None
            self.is_connected = False

        # self.is_connected = True
        self.run_task_list.append(
            asyncio.ensure_future(self.send_loop(self.client))
        )
        self.run_task_list.append(
            asyncio.ensure_future(self.read_loop(self.client))
        )
        # self.is_running = True
        while True:
            await asyncio.sleep(.1)

    async def read_loop(self, websocket):

        # print('starting read loop')
        while True:
            try:
                # print(f'read_loop: {websocket}')
                msg = await websocket.recv()
                # print('read loop: {}'.format(msg))
                await self.readq.put(msg)
                # print('after readq.put')
            except websockets.exceptions.ConnectionClosed:
                print(f'ws connection closed')
                await self.client.close()
                self.client = None
                self.connect_state = ClientConnection.CLOSED
                await asyncio.sleep(.5)

    async def send_loop(self, websocket):
        # TODO: add try except loop to catch invalid state
        # print('starting send loop')
        while True:
            # print(f'sendq: {self.sendq}')
            msg = await self.sendq.get()
            # print('send loop: {}'.format(msg))
            # print(f'websocket: {websocket}')
            await websocket.send(msg)

    async def shutdown_complete(self):

        while True:
            if (self.is_shutdown):
                return

    async def close_client(self):

        await self.client.close()
