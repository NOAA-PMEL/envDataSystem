import abc
import asyncio
from data.message import Message


class ClientConnection(abc.ABC):

    def __init__(
        self,
        *,
        uri=None,
        host=None,
        port=None,
        address=None,
        loop=None,
        auto_connect=True
    ):

        self.client = None

        self.uri = uri
        self.host = host
        self.port = port
        self.address = address

        # print(f'uri={self.uri}, host={self.host}, port={self.port}')

        self.is_connected = False

        self.keep_connected = False
        if auto_connect:
            self.keep_connected = True

        print(f'auto_connect={auto_connect}, keep_connected={self.keep_connected}')
        self.loop = loop
        if loop is None:
            self.loop = asyncio.get_event_loop()

        self.sendq = asyncio.Queue(loop=self.loop)
        self.readq = asyncio.Queue(loop=self.loop)

        self.run_task_list = []
        self.task_list = []
        self.task_list.append(
            # asyncio.ensure_future(self.open())
            asyncio.ensure_future(self.run())
        )
        print('WSClient: done with init')
        # print(self.task_list)
        # self.is_running = False

    def open_connection(self):
        self.keep_connected = True

    async def run(self):

        timeout = 1  # seconds

        # print('run...')

        while True:

            while self.keep_connected:
                # print('keep connected')
                if self.is_connected is not True:
                    # print('connecting to server')
                    for t in self.run_task_list:
                        # print(f'killing run task: {t}')
                        t.cancel()

                    await self.connect()
                    # print(f'after connect: {self.client}')
                    if self.is_connected is True:
                        self.run_task_list.append(
                            asyncio.ensure_future(self.send_loop(self.client))
                        )
                        self.run_task_list.append(
                            asyncio.ensure_future(self.read_loop(self.client))
                        )

                await asyncio.sleep(timeout)

            await asyncio.sleep(timeout)

    @abc.abstractmethod
    async def connect(self):
        pass

    @abc.abstractmethod
    async def open(self):
        pass

    def isConnected(self):
        return self.is_connected

    async def read(self):
        # read from client: msg can have more than just a Message
        msg = await self.readq.get()
        # print('read: {}'.format(msg))
        return msg
        # return await self.readq.get()

    async def read_message(self):
        # helper function to easily read a Message
        msg_json = await self.read()
        # print(f'read_message: {msg_json}')
        msg = Message()
        msg.from_json(msg_json)
        # msg = Message().from_json(msg_json)
        # print(f'after convert: {msg}')
        # print(f'after convert: {message.to_json()}')
        return msg
        # return Message().from_json(msg_json)

    async def send(self, msg):
        # send to client: msg can have more than just a Message
        # print('send: {}'.format(msg))
        await self.sendq.put(msg)
        # print('msg sent')
        # await self.sendq.put(msg)

    async def send_message(self, message):
        # helper function to easily send a Message
        # print(f'send_message: {message}')
        msg = message.to_json()
        # print(f'send_message: {msg}')
        await self.send(msg)

    @abc.abstractmethod
    async def close_client(self):
        pass

    def sync_close(self):

        if self.client is not None:
            self.loop.run_until_complete(self.close())

    async def close(self):

        print('closing client')
        self.keep_connected = False

        # await self.shutdown_client()
        if self.client is not None:
            await self.close_client()
        print('client closed')
        self.is_connected = False

        # print('killing run_tasks')
        for t in self.run_task_list:
            t.cancel()

        # print('killing tasks')
        for t in self.task_list:
            t.cancel()


# class WSClient(ClientConnection):

#     async def connect(self):

#         try:
#             self.client = await websockets.client.connect(self.uri)
#             self.is_connected = True
#             print(self.client)
#         except ConnectionError:
#             print("not connected")
#             self.client = None
#             self.is_connected = False

#     async def open(self):

#         print('WSClient.open')
#         # timeout = 10
#         try:
#             self.client = await websockets.client.connect(self.uri)
#             self.is_connected = True
#         except ConnectionError:
#             print("not connected")
#             self.client = None
#             self.is_connected = False

#         # self.is_connected = True
#         print('here')
#         print(self.client)
#         self.run_task_list.append(
#             asyncio.ensure_future(self.send_loop(self.client))
#         )
#         self.run_task_list.append(
#             asyncio.ensure_future(self.read_loop(self.client))
#         )
#         # self.is_running = True
#         while True:
#             await asyncio.sleep(.1)

#     async def read_loop(self, websocket):

#         while True:
#             msg = await websocket.recv()
#             # print('read loop: {}'.format(msg))
#             await self.readq.put(msg)
#             # print('after readq.put')

#     async def send_loop(self, websocket):
#         # TODO: add try except loop to catch invalid state
#         print('starting send loop')
#         while True:
#             print(f'sendq: {self.sendq}')
#             msg = await self.sendq.get()
#             print('send loop: {}'.format(msg))
#             print(f'websocket: {websocket}')
#             await websocket.send(msg)

#     async def shutdown_complete(self):

#         while True:
#             if (self.is_shutdown):
#                 return

#     async def close_client(self):

#         await self.client.close()
