import asyncio
import serial_asyncio
from client.client import ClientConnection


class SerialPortClient(ClientConnection):

    def __init__(
        self,
        *,
        uri=None,
        # host=None,
        # port=None,
        # address=None,
        loop=None,
        auto_connect=True,
        read_method='readline',
        read_terminator='\n',
        read_num_bytes=1,
        **kwargs
    ):
        super(SerialPortClient, self).__init__(
            uri=uri,
            loop=loop,
            auto_connect=auto_connect,
            **kwargs,
        )

        self.read_method = read_method
        self.read_terminator = read_terminator
        self.read_num_bytes = read_num_bytes

    class _SerialPortClient():
        def __init__(self, uri=None):
            print(f'_SerialPortClient')
            if uri:
                asyncio.ensure_future(self.connect(uri))
            else:
                self.reader = None
                self.writer = None

        async def connect(self, uri):
            try:
                self.reader, self.writer = (
                    await serial_asyncio.open_serial_connection(
                        url=uri,
                    )
                )
                print(f'connect: {self.reader}, {self.writer}')
            except Exception as e:
                print(f'connect error: {e}')

        async def readline(self):
            if self.reader:
                msg = await self.reader.readline()
                return msg.decode()

        async def readuntil(self, terminator='\n'):
            msg = await self.reader.readuntil(terminator.encode())
            return msg.decode()

        async def read(self, num_bytes=1):
            msg = await self.reader.read(num_bytes)
            return msg.decode()

        async def write(self, msg):
            if self.writer:
                self.writer.write(msg.encode())
                await self.writer.drain()

        async def close(self):
            self.writer.close()
            await self.writer.wait_closed()

    async def connect(self):
        if self.is_connected:
            return
        try:
            print(f'SerialPort.connect.uri: {self.uri}')
            # self.client = await websockets.client.connect(self.uri)
            # self.reader, self.writer = await serial_asyncio.open_serial_connection(
            #     url=self.uri,
            # )
            self.client = self._SerialPortClient(uri=self.uri)

            self.is_connected = True
            # print(f'SerialPort.connect(): {self.client}')
        except Exception as e:
            print(f"not connected: {e}")
            self.client = None
            self.is_connected = False

    async def open(self):

        # print('SerialPort.open')
        # timeout = 10
        try:
            print(f'SerialPort.connect.uri: {self.uri}')
            # self.client = await websockets.client.connect(self.uri)
            # self.reader, self.writer = await serial_asyncio.open_serial_connection(
            #     url=self.uri,
            # )
            self.client = self._SerialPortClient()

            self.is_connected = True
            # print(f'SerialPort.connect(): {self.client}')
        except Exception as e:
            print(f"not connected: {e}")
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

    async def read_loop(self, serialport):

        print('starting read loop')
        while True:
            # print(f'read_loop: {websocket}')
            if self.read_method == 'readline':
                msg = await serialport.readline()
            elif self.read_method == 'readuntil':
                msg = await serialport.readuntil(
                    self.read_terminator
                )
            elif self.read_method == 'readbytes':
                msg = await serialport.readuntil(
                    self.read_num_bytes
                )
            # print('read loop: {}'.format(msg))
            await self.readq.put(msg)
            # print('after readq.put')

    async def send_loop(self, serialport):
        # TODO: add try except loop to catch invalid state
        # print('starting send loop')
        while True:
            # print(f'sendq: {self.sendq}')
            msg = await self.sendq.get()
            # print('send loop: {}'.format(msg))
            # print(f'websocket: {websocket}')
            await serialport.send(msg)

    async def shutdown_complete(self):

        while True:
            if (self.is_shutdown):
                return

    async def close_client(self):

        await self.client.close()
