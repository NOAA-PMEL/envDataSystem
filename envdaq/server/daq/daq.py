import abc
import asyncio


class DAQ(abc.ABC):

    def __init__(self, config):
        # TODO: Should DAQ have generic in/out buffers?
        print('init DAQ')
        self.loop = asyncio.get_event_loop()
        self.config = config
        self.task_list = []

        self.name = None
        self.label = None

        # Message buffers (Queues)
        #   to/from parent
        self.to_parent_buf = None
        self.from_parent_buf = None
        #   to/from child
        self.to_child_buf = None
        self.from_child_buf = None
        #   to/from gui
        self.to_gui_buf = None
        self.from_gui_buf = None

        self.create_msg_buffers()
        
    def get_id(self):
        id = self.__class__.__name__
        if self.label is not None:
            id += ":"+self.label

        return id

    def create_msg_buffers(self, config=None):
        '''
        Create all receive buffers. Send buffers
        will be set by senders
        '''

        self.from_parent_buf = asyncio.Queue(loop=self.loop)
        self.from_child_buf = asyncio.Queue(loop=self.loop)
        # self.from_gui_buf = asyncio.Queue(loop=self.loop)

    # @abc.abstractmethod
    # def connect_msg_buffers(self, config=None):
    #     '''
    #     Inherited class needs to connect to/from buffers
    #     '''
    #     pass

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
            print(f'from_child_loop: {msg}')
            await self.handle(msg, type="FromChild")
            # await asyncio.sleep(.1)

    async def from_gui_loop(self):
        while True:
            msg = await self.from_gui_buf.get()
            await self.handle(msg, type="FromGUI")
            # await asyncio.sleep(.1)

    async def message_to_parent(self, msg):
        # while True:
        await self.to_parent_buf.put(msg)

    async def message_to_gui(self, msg):
        # while True:
        await self.to_gui_buf.put(msg)

    async def message_from_parent(self, msg):
        '''
        This is to be used by parent to send messages to 
        children
        '''
        # while True:
        await self.from_parent_buf.put(msg)
