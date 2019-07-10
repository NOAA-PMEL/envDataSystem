import abc
import asyncio
import websockets
from data.message import Message


class ClientConnection(abc.ABC):

    def __init__(
        self, *, uri=None, host=None, port=None, address=None, loop=None
    ):

        self.client = None

        self.uri = uri
        self.host = host
        self.port = port
        self.address = address

        print(f'uri={self.uri}, host={self.host}, port={self.port}')

        self.loop = loop
        if loop is None:
            self.loop = asyncio.get_event_loop()

        self.sendq = asyncio.Queue(loop=asyncio.get_event_loop())
        self.readq = asyncio.Queue(loop=asyncio.get_event_loop())

        self.run_task_list = []
        self.task_list = []
        self.task_list.append(
            asyncio.ensure_future(self.open())
        )

        print(self.task_list)
        # self.is_running = False

    @abc.abstractmethod
    async def open(self):
        pass

    async def read(self):
        msg = await self.readq.get()
        # print('read: {}'.format(msg))
        return msg
        # return await self.readq.get()

    async def read_message(self):
        msg_json = await self.read()
        return Message().from_json(msg_json)

    async def send(self, msg):
        print('send: {}'.format(msg))
        await self.sendq.put(msg)
        # await self.sendq.put(msg)

    async def send_message(self, message):
        print(f'send_message: {message}')
        msg = message.to_json()
        print(f'send_message: {msg}')
        await self.send(msg)

    @abc.abstractmethod
    async def close_client(self):
        pass

    def sync_close(self):

        if self.client is not None:
            self.loop.run_until_complete(self.close())
       
    async def close(self):

        print('closing client')
        # await self.shutdown_client()
        if self.client is not None:
            await self.close_client()

        for t in self.run_task_list:
            t.cancel()

        for t in self.task_list:
            t.cancel()


class WSClient(ClientConnection):

    async def open(self):

        print('WSClient.open')
        self.client = await websockets.client.connect(self.uri)
        print(self.client)
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

        while True:
            msg = await websocket.recv()
            # print('read loop: {}'.format(msg))
            await self.readq.put(msg)

    async def send_loop(self, websocket):

        while True:
            msg = await self.sendq.get()
            # print('send loop: {}'.format(msg))
            await websocket.send(msg)

    async def shutdown_complete(self):

        while True:
            if (self.is_shutdown):
                return

    async def close_client(self):

        await self.client.close()
