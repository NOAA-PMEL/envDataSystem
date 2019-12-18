import asyncio
from client.client import ClientConnection
from collections import deque


class TCPPortClient(ClientConnection):

    def __init__(
        self,
        *,
        uri=None,
        # host=None,
        # port=None,
        address=None,
        loop=None,
        auto_connect=True,
        send_method='ascii',
        read_method='readline',
        read_terminator='\n',
        read_num_bytes=1,
        decode_errors='strict',
        **kwargs
    ):
        super(TCPPortClient, self).__init__(
            uri=uri,
            loop=loop,
            auto_connect=auto_connect,
            **kwargs,
        )

        # TODO: if uri but no address, build from uri
        if address:
            self.address = address
        else:
            return None

        self.send_method = send_method
        self.read_method = read_method
        self.read_terminator = read_terminator
        self.read_num_bytes = read_num_bytes
        self.decode_errors = decode_errors

        self.return_packet_bytes = deque(maxlen=25000)

        self.binary_read_bytes_set = False

    class _TCPPortClient():
        def __init__(self, address=None):
            print(f'_TCPPortClient')
            self.address = address
            self.reader = None
            self.writer = None
            self.connect_state = ClientConnection.CLOSED
            if address:
                asyncio.ensure_future(self.connect(address))

        async def connect(self, address):
            self.connect_state = ClientConnection.CONNECTING
            # tcp_con = await asyncio.open_connection(
            #     host=address[0],
            #     port=address[1]
            # )
            try:
                # print(f'{address}, {address[0]}, {address[1]}')
                self.reader, self.writer = await asyncio.open_connection(
                    host=address[0],
                    port=address[1]
                )
                print(f'connect: {self.reader}, {self.writer}')
                print(f'{self.address}')
                self.connect_state = ClientConnection.CONNECTED
            except (asyncio.TimeoutError, ConnectionRefusedError):
                self.reader = None
                self.writer = None
                print(f'connect error:')
                self.connect_state = ClientConnection.CLOSED

        async def readline(self, decode_errors='strict'):
            # print('here')
            if self.reader:
                # print(f'readline: {self.reader}')
                msg = await self.reader.readline()
                # print(f'{msg}')
                return msg.decode(errors=decode_errors)

        async def readuntil(
            self,
            terminator='\n',
            decode_errors='strict'
        ):
            # print(f'readuntil')
            msg = await self.reader.readuntil(terminator.encode())
            # print(f'readmsg: {msg}')
            return msg.decode(errors=decode_errors)

        async def read(self, num_bytes=1, decode_errors='strict'):
            msg = await self.reader.read(num_bytes)
            return msg.decode(errors=decode_errors)

        async def readbinary(self, num_bytes=1, decode_errors='strict'):
            msg = await self.reader.read(num_bytes)
            return msg

        async def write(self, msg):
            if self.writer:
                # print(f'msg: {msg}')
                self.writer.write(msg.encode())
                await self.writer.drain()
                # print(f'written')

        async def close(self):
            self.connect_state = ClientConnection.CLOSED
            self.writer.close()
            await self.writer.wait_closed()
            print(f'tcp client done closing')

    # override client.Connectionstate to use inner class
    def ConnectionState(self):
        if self.client:
            return self.client.connect_state
        else:
            return super().ConnectionState()

    async def connect(self):
        # if self.is_connected:
        # self.connect_state = ClientConnection.CONNECTING
        if (
            self.ConnectionState() == ClientConnection.CONNECTED
        ) or (
                self.ConnectionState() == ClientConnection.CONNECTING
        ):
            return

        try:
            self.connect_state = ClientConnection.CONNECTING
            print(f'tcpport.connect.uri: {self.address}')
            # self.client = await websockets.client.connect(self.uri)
            # self.reader, self.writer = await serial_asyncio.open_serial_connection(
            #     url=self.uri,
            # )
            self.client = self._TCPPortClient(address=self.address)

            # self.is_connected = True
            # self.connect_state = ClientConnection.CONNECTING
            # print(f'tcpport.connect(): {self.client}')
        except Exception as e:
            # except (asyncio.TimeoutError, ConnectionRefusedError):
            #     print("Network port not responding")
            print(f"not connected: {e}")
            self.client = None
            self.is_connected = False
            self.connect_state = ClientConnection.CLOSED

    async def open(self):

        # print('tcpport.open')
        # timeout = 10
        try:
            print(f'TCPPort.connect.uri: {self.address}')
            # self.client = await websockets.client.connect(self.uri)
            # self.reader, self.writer = await serial_asyncio.open_serial_connection(
            #     url=self.uri,
            # )
            # self.client = self._TCPPortClient()
            self.client = self._TCPPortClient(address=self.address)

            # self.is_connected = True
            # self.ConnectionState() = ClientConnection.CONNECTING
            # print(f'tcpport.connect(): {self.client}')
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

    async def read_loop(self, tcpport):

        print('starting read loop')
        while True:
            # print(f'read_loop: {self.ConnectionState()}')
            if self.ConnectionState() == ClientConnection.CONNECTED:
                # print(f'read_loop: {tcpport}')
                if self.read_method == 'readline':
                    msg = await tcpport.readline(
                        decode_errors=self.decode_errors
                    )
                elif self.read_method == 'readuntil':
                    msg = await tcpport.readuntil(
                        self.read_terminator,
                        decode_errors=self.decode_errors
                    )
                elif self.read_method == 'readbytes':
                    msg = await tcpport.read(
                        self.read_num_bytes,
                        decode_errors=self.decode_errors
                    )
                elif self.read_method == 'readbinary':
                    ret_packet_size = await self.get_return_packet_size()
                    msg = await tcpport.readbinary(
                        ret_packet_size
                    )
                    
                # print('read loop: {}'.format(msg))
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

    async def get_return_packet_size(self):
        
        while len(self.return_packet_bytes) == 0:
            asyncio.sleep(.1)
        return self.return_packet_bytes.popleft()

    async def send_loop(self, tcpport):
        # TODO: add try except loop to catch invalid state
        # print('starting send loop')
        while True:
            # print(f'sendq: {self.sendq}')
            msg = await self.sendq.get()
            # print('send loop: {}'.format(msg))
            # print(f'websocket: {websocket}')
            if self.send_method == 'binary':
                self.return_packet_bytes.append(
                    msg['return_packet_bytes']
                )
            await tcpport.write(msg['send_packet'])

    async def shutdown_complete(self):

        while True:
            if (self.is_shutdown):
                return

    async def close_client(self):

        await self.client.close()
