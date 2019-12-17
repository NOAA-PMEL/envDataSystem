import asyncio
import serial
import serial_asyncio
from client.client import ClientConnection


class SerialPortClient(ClientConnection):

    # TODO: more testing on re-establishing connection
    #       I think the serial port persists in a weird way
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
        decode_error='strict',
        baudrate=9600,
        bytesize=8,
        parity=serial.PARITY_NONE,
        stopbits=1,
        xonxoff=0,
        rtscts=0,
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
        self.decode_error = decode_error
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.xonxoff = xonxoff
        self.rtscts = rtscts

    class _SerialPortClient():
        def __init__(
            self,
            uri=None,
            baudrate=9600,
            bytesize=8,
            parity=serial.PARITY_NONE,
            stopbits=1,
            xonxoff=0,
            rtscts=0,
        ):
            print(f'_SerialPortClient')
            self.reader = None
            self.writer = None
            self.connect_state = ClientConnection.CLOSED
            self.baudrate = baudrate
            self.bytesize = bytesize
            self.parity = parity
            self.stopbits = stopbits
            self.xonxoff = xonxoff
            self.rtscts = rtscts

            if uri:
                asyncio.ensure_future(self.connect(uri))

        async def connect(self, uri):
            self.connect_state = ClientConnection.CONNECTING
            try:
                self.reader, self.writer = (
                    await serial_asyncio.open_serial_connection(
                        url=uri,
                        baudrate=self.baudrate,
                        bytesize=self.bytesize,
                        parity=self.parity,
                        stopbits=self.stopbits,
                        xonxoff=self.xonxoff,
                        rtscts=self.rtscts,
                    )
                )
                print(f'connect: {self.reader}, {self.writer}')
                self.connect_state = ClientConnection.CONNECTED
            except Exception as e:
                self.reader = None
                self.writer = None
                print(f'connect error: {e}')
                self.connect_state = ClientConnection.CLOSED

        async def readline(self):
            if self.reader:
                msg = await self.reader.readline()
                return msg.decode(error=self.decode_error)

        async def readuntil(self, terminator='\n'):
            msg = await self.reader.readuntil(terminator.encode())
            # print(f'readuntil: {msg}')
            return msg.decode(error=self.decode_error)

        async def read(self, num_bytes=1):
            msg = await self.reader.read(num_bytes)
            return msg.decode(error=self.decode_error)

        async def write(self, msg):
            if self.writer:
                print(f'msg: {msg}')
                self.writer.write(msg.encode())
                await self.writer.drain()

        async def close(self):
            self.connect_state = ClientConnection.CLOSED
            self.writer.close()
            await self.writer.wait_closed()

    # override client.Connectionstate to use inner class
    def ConnectionState(self):
        if self.client:
            return self.client.connect_state
        else:
            return super().ConnectionState()

    async def connect(self):
        # if self.is_connected:
        #     return
        if (
            self.ConnectionState() == ClientConnection.CONNECTED
        ) or (
                self.ConnectionState() == ClientConnection.CONNECTING
        ):
            return

        try:
            self.connect_state = ClientConnection.CONNECTING
            print(f'SerialPort.connect.uri: {self.uri}')
            # self.client = await websockets.client.connect(self.uri)
            # self.reader, self.writer = await serial_asyncio.open_serial_connection(
            #     url=self.uri,
            # )
            self.client = self._SerialPortClient(
                uri=self.uri,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts,
            )

            # self.is_connected = True
            print(f'SerialPort.connect(): {self.client}')
        except Exception as e:
            print(f"not connected: {e}")
            self.client = None
            self.is_connected = False
            self.connect_state = ClientConnection.CLOSED

    async def open(self):

        # print('SerialPort.open')
        # timeout = 10
        try:
            print(f'SerialPort.connect.uri: {self.uri}')
            # self.client = await websockets.client.connect(self.uri)
            # self.reader, self.writer = await serial_asyncio.open_serial_connection(
            #     url=self.uri,
            # )
            # self.client = self._SerialPortClient()
            self.client = self._SerialPortClient(
                uri=self.uri,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                xonxoff=self.xonxoff,
                rtscts=self.rtscts,
            )

            # self.is_connected = True
            # print(f'SerialPort.connect(): {self.client}')
        except Exception as e:
            print(f"not connected: {e}")
            self.client = None
            self.is_connected = False
            self.connect_state = ClientConnection.CLOSED

        # self.is_connected = True
        self.run_task_list.append(
            asyncio.ensure_future(self.send_loop(self.client))
        )
        self.run_task_list.append(
            asyncio.ensure_future(self.read_loop(self.client))
        )
        # self.is_running = True
        while True:
            await asyncio.sleep(1)

    async def read_loop(self, serialport):

        print('starting read loop')
        while True:
            if self.ConnectionState() == ClientConnection.CONNECTED:
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
                # await self.readq.put(msg)
                # print('after readq.put')
                if msg:
                    await self.readq.put(msg)
                else:
                    print(f'server appears to have closed...closing')
                    await self.client.close()
                    self.client = None
                    self.connect_state = ClientConnection.CLOSED
                    await asyncio.sleep(.5)
                # print('after readq.put')
            else:
                await asyncio.sleep(.1)

    async def send_loop(self, serialport):
        # TODO: add try except loop to catch invalid state
        # print('starting send loop')
        while True:
            print(f'7777sendq: {self.sendq.qsize()}')
            msg = await self.sendq.get()
            print('8888send loop: {}'.format(msg))
            # print(f'websocket: {websocket}')
            await serialport.write(msg)

    async def shutdown_complete(self):

        while True:
            if (self.is_shutdown):
                return

    async def close_client(self):

        await self.client.close()
