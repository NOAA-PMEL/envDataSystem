import abc
import asyncio
from daq.interface.ifdevice import IFDevice, DummyIFDevice
import utilities.util as util

import importlib
import sys


class Managers():
    __managers = dict()
    # TODO: need a way to stop/shutdown gracefully

    @staticmethod
    def start():
        print('starting IFDeviceManager')
        Managers().__managers['IFDeviceManager'] = IFDeviceManager()

    @staticmethod
    def get(type):
        if (len(Managers().__managers) == 0):
            Managers().start()
        print('get manager: {}'.format(type))
        print(Managers().__managers)
        return Managers().__managers[type]


class IFDeviceManager():

    def __init__(self):
        self.devmap = {}

    def create(self, dev_type, config):
        # TODO: use config values to find module,class for type like factory?
        if (dev_type == 'DummyIFDevice'):

            dev = DummyIFDevice(config)
            id = dev.get_id()
            # TODO: why am I del dev here?
            if id in self.devmap:
                del dev
                dev = self.devmap[id]
            else:
                self.devmap[id] = dev
        else:

            dev = None

        print(self.devmap)
        # print(DummyIFDevice.get_channel_map())
        return dev


class InterfaceFactory():

    @staticmethod
    def create(config):
        create_cfg = config['INTERFACE']
        ifconfig = config['IFCONFIG']

        # inst_config = config['instrument']
        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            # print('Creating: ' + config['name'])
            # print('   ClassName: ' + config['class'])
            mod_ = importlib.import_module(create_cfg['MODULE'])
            cls_ = getattr(mod_, create_cfg['CLASS'])
            # inst_class = eval(config['class'])
                                                                                                                        # return inst_class.factory_create()
            return cls_(ifconfig)

        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise


class Interface(abc.ABC):

    class_type = 'INTERFACE'

    def __init__(self, config):
        self.loop = asyncio.get_event_loop()

        self.config = config
        # if no NAME given, create one with address
        self.label = self.config['LABEL']

        #  Message buffers (Queues)
        self.msg_send_buffer = None
        self.msg_rcv_buffer = None

        self.ifdev_send_buffer = None
        self.ifdev_rcv_buffer = None

        self.gui_send_buffer = None

        # self.create_msg_buffer()
        # self.read_q = config['IF_READ_Q']
#        self.write_q = config['IF_WRITE_Q']

        self.task_list = []

        self.dev_mananger = Managers().get('IFDeviceManager')
        self.ifdevice = None
#        print(self.dev_mananger)

    def connect(self, cmd=None):
        pass

    def start(self, cmd=None):
        print('Starting iface')
        task = asyncio.ensure_future(self.read_loop())
        self.task_list.append(task)
        self.ifdevice.start()

    def read(self, cmd=None):
        pass

    def write(self, cmd):
        pass

    # TODO: howto clean up managers?
    def stop(self, cmd=None):
        # for instrument in self.inst_map:
        #     # print(sensor)
        #     instrument.stop()

        # tasks = asyncio.Task.all_tasks()
        for t in self.task_list:
            # print(t)
            t.cancel()

    def disconnect(self, cmd=None):
        pass

    async def read_loop(self):

        while True:
            msg = await self.ifdev_rcv_buffer.get()
            await self.handle(msg)
            # await asyncio.sleep(.1)

    @abc.abstractmethod
    async def handle(self, msg):
        pass

    def create_msg_buffers(self, config=None):
        # self.read_buffer = MessageBuffer(config=config)
        self.ifdev_send_buffer = asyncio.Queue(loop=self.loop)
        self.ifdev_rcv_buffer = asyncio.Queue(loop=self.loop)

    def get_id(self):
        id = self.__class__.__name__
        if self.label is not None:
            id += ":"+self.label

        return id


class DummyInterface(Interface):

    def __init__(self, config):
        super().__init__(config)

        # self.dev_mananger
        self.ifdevice = self.dev_mananger.create('DummyIFDevice', config)
        self.create_msg_buffers()
        # in order to make sense, child:send == parent:rcv
        self.ifdevice.msg_send_buffer = self.ifdev_rcv_buffer

    async def handle(self, msg):

        # interface will know if msg is json or object

        # check header to see if data to be sent to instrument
        #   - if yes, add timestamp
        # print('type: {}'.format(msg.type))
        if (msg.type == IFDevice.class_type):
            msg.type = Interface.class_type
            msg.sender_id = self.get_id()
            if (msg.subject == 'DATA'):
                # update could be done in base class
                msg.update(msgtype=Interface.class_type)
                msg.body['DATETIME'] = util.dt_to_string()
                # print(f'DummyInterface: {msg.to_json()}')
                # self.msg_buffer.put_nowait(msg)
                await self.msg_send_buffer.put(msg)
        else:
            print('Unknown Message type: {}'.format(msg.type))


if __name__ == "__main__":

    config = {
        'INTERFACE': {
            'MODULE': 'daq.interface',
            'CLASS': 'DummyInterface',
        },
        'IFCONFIG': {
            'ADDRESS': 'DummyAddress',
            'SerialNumber': '1234'
        }
    }
    # print(config['IFTYPE'])
    # print(config['IFCONFIG'])

    iface = InterfaceFactory()
    iface.create(config)
