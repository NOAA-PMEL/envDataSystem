import websockets
import asyncio
from client.client import ClientConnection


class WSClient(ClientConnection):

    async def connect(self):

        try:
            print(f'WSClient.connect.uri: {self.uri}')
            self.client = await websockets.client.connect(self.uri)
            self.is_connected = True
            # print(f'WSClient.connect(): {self.client}')
        except ConnectionError:
            print("not connected")
            self.client = None
            self.is_connected = False

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
            # print(f'read_loop: {websocket}')
            msg = await websocket.recv()
            # print('read loop: {}'.format(msg))
            await self.readq.put(msg)
            # print('after readq.put')

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
