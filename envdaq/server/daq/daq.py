import abc
import asyncio
from client.wsclient import WSClient
from urllib.parse import quote 

class DAQ(abc.ABC):

    def __init__(
        self,
        config,
        ui_config=None,
        auto_connect_ui=True,
        **kwargs
    ):

        # TODO: Should DAQ have generic in/out buffers?
        print('init DAQ')
        self.loop = asyncio.get_event_loop()
        self.config = config
        self.ui_config = ui_config
        self.auto_connect_ui = auto_connect_ui
        self.task_list = []
        self.ui_task_list = []

        self.name = None        
        self.label = None
        if 'LABEL' in config:
            self.label = config['LABEL']
        print(f"id: {self.get_id()}")

        # in case we want to add heierarchy
        self.parent = None

        # Message buffers (Queues)
        #   to/from parent
        self.to_parent_buf = None
        self.from_parent_buf = None
        #   to/from child
        self.to_child_buf = None
        self.from_child_buf = None
        #   to/from gui
        self.to_ui_buf = None
        self.from_ui_buf = None
        self.create_msg_buffers()

        # ui client
        self.ui_client = None

        # start loop to maintain ui
        if (
            'do_ui_connection' in self.ui_config and
            self.ui_config['do_ui_connection'] is False
        ):
            print('no ui connection')
            pass
        else:
            self.task_list.append(
                asyncio.ensure_future(self.run_ui_connection())
            )
        # # make ui connection
        # self.ui_task_list.append(
        #     asyncio.ensure_future(self.open_ui_connection())
        # )

    def get_id(self):
        id = self.__class__.__name__
        if self.label is not None:
            id += ":"+self.label

        return id

    @abc.abstractmethod
    def get_ui_address(self):
        pass

    async def connect_to_ui(self):

        # build ui_address
        # ui_address = 'ws://localhost:8001/ws/'+quote(self.get_ui_address())
        ui_address = 'ws://localhost:8001/ws/'+self.get_ui_address().replace(" ", "")
        # ui_address.replace(" ", "")
        print(f'ui_address: {ui_address}')
        # ui_address = 'ws://localhost:8001/ws/envdaq/data_test/'

        # self.ui_client = WSClient(uri=quote(ui_address))
        self.ui_client = WSClient(uri=ui_address)
        while self.ui_client.isConnected() is not True:
            # self.gui_client = WSClient(uri=gui_ws_address)
            # print(f"gui client: {self.gui_client.isConnected()}")
            await asyncio.sleep(1)

    async def run_ui_connection(self):

        while True:

            if (
                self.auto_connect_ui and (
                    self.ui_client is None or not self.ui_client.isConnected()
                )
            ):
                # close tasks for current ui if any
                for t in self.ui_task_list:
                    t.cancel()

                # make connection
                print('connect to ui')
                await self.connect_to_ui()

                # start ui queues
                self.to_ui_buf = asyncio.Queue(loop=self.loop)
                self.ui_task_list.append(
                    asyncio.ensure_future(self.to_ui_loop())
                )
                self.ui_task_list.append(
                    asyncio.ensure_future(self.from_ui_loop())
                )
            await asyncio.sleep(1)

    # async def open_ui_connection(self):

    #     while self.ui_client.isConnected() is False:
    #         # if self.ui_client.isConnected() is False:
    #         self.ui_client = self.connect_to_ui()

    def start(self, cmd=None):
        # self.create_msg_buffers()
        self.task_list.append(
            asyncio.ensure_future(self.from_parent_loop())
        )

        self.task_list.append(
            asyncio.ensure_future(self.from_child_loop())
        )

    def stop(self, cmd=None):

        for t in self.task_list:
            t.cancel()

    def shutdown(self):

        if self.ui_client is not None:
            # self.loop.run_until_complete(self.gui_client.close())
            self.ui_client.sync_close()

        for t in self.ui_task_list:
            t.cancel()

    def create_msg_buffers(self, config=None):
        '''
        Create all buffers controlled by this instance.
        '''

        self.from_parent_buf = asyncio.Queue(loop=self.loop)
        self.from_child_buf = asyncio.Queue(loop=self.loop)

        # I don't think we need a from_ui_buf
        # self.from_ui_buf = asyncio.Queue(loop=self.loop)

    @abc.abstractmethod
    async def handle(self, msg, type=None):
        pass

    async def from_parent_loop(self):
        while True:
            msg = await self.from_parent_buf.get()
            await self.handle(msg, type="FromParent")
            # await asyncio.sleep(.1)

    async def from_child_loop(self):
        print(f'started from_child_loop: {self.name} {self.from_child_buf}')
        # while self.from_child_buf is None:
        #     pass

        while True:
            msg = await self.from_child_buf.get()
            print(f'****from_child_loop: {msg.to_json()}')
            await self.handle(msg, type="FromChild")
            # await asyncio.sleep(.1)

    async def to_ui_loop(self):
        while True:
            message = await self.to_gui_buf.get()
            # print('send server message')
            await self.ui_client.send_message(message)

    async def from_ui_loop(self):
        while True:
            message = await self.ui_client.read_message()
            # print(f'message = {message.to_json()}')
            await self.handle(message, src='FromUI')

    async def message_to_parent(self, msg):
        # while True:
        print(f'message_to_parent: {msg.to_json()}')
        await self.to_parent_buf.put(msg)

    async def message_to_ui(self, msg):
        # while True:
        await self.to_ui_buf.put(msg)

    async def message_from_parent(self, msg):
        '''
        This is to be used by parent to send messages to
        children
        '''
        # while True:
        await self.from_parent_buf.put(msg)
