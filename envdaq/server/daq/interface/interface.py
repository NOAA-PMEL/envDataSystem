import abc
import asyncio
from daq.interface.ifdevice import IFDevice, DummyIFDevice, IFDeviceFactory
import utilities.util as util
import json
import importlib
import sys


class Managers():
    __managers = dict()
    # TODO: need a way to stop/shutdown gracefully

    @staticmethod
    def start():
        print('starting IFDeviceManager')
        Managers().__managers['IFDeviceManager'] = IFDeviceManager()
        print(f'start: {Managers().__managers["IFDeviceManager"]}')

    @staticmethod
    def get(mgr_type):
        print(f'mgr_type = {mgr_type}')
        if (len(Managers().__managers) == 0):
            Managers().start()
            print(len(Managers().__managers))
        print(f'get: {Managers().__managers["IFDeviceManager"]}')
        for k in Managers().__managers.keys():
            print(k)
        for k, v in Managers().__managers.items():
            print(f'k = {k}')
        print('get manager: {}'.format(mgr_type))
        print(Managers().__managers)
        print(Managers().__managers[mgr_type])
        return Managers().__managers[mgr_type]


class IFDeviceManager():

    def __init__(self):
        print('IFDeviceManger init')
        self.devmap = dict()

    def create(self, dev_type, config, **kwargs):
        print('IFDeviceManager.create()')
        # TODO: use config values to find module,class for type like factory?
        if (dev_type == 'DummyIFDevice'):
            print('create DummyIFDevice')
            dev = IFDeviceFactory().create(config, **kwargs)
            # dev = DummyIFDevice(config, ui_config=None)
            print(f'dev = {dev}')
            id = dev.get_id()
            # TODO: why am I del dev here?
            if id in self.devmap:
                del dev
                dev = self.devmap[id]
            else:
                self.devmap[id] = dev
        else:

            dev = None

        print(f'devmap: {self.devmap}')
        # print(DummyIFDevice.get_channel_map())
        return dev


class InterfaceFactory():

    @staticmethod
    def create(config):
        print(config)
        create_cfg = config['INTERFACE']
        ifconfig = config['IFCONFIG']

        # inst_config = config['instrument']
        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            # print('Creating: ' + config['name'])
            # print('   ClassName: ' + config['class'])
            mod_ = importlib.import_module(create_cfg['MODULE'])
            # print(f'mod: {mod_}')
            cls_ = getattr(mod_, create_cfg['CLASS'])
            # print(f'cls: {cls_}')
            # inst_class = eval(config['class'])
                                                                                                                        # return inst_class.factory_create()
            test = cls_(ifconfig)
            print(test)
            return test

        except:
            print("Interface: Unexpected error:", sys.exc_info()[0])
            raise


class Interface(abc.ABC):

    class_type = 'INTERFACE'

    def __init__(self, config):
        print('Interface init')
        self.loop = asyncio.get_event_loop()

        print(config)
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

        self.dev_manager = Managers().get('IFDeviceManager')
        print(f'dev_manager: {self.dev_manager}')
        self.ifdevice = None
#        print(self.dev_mananger)

    def connect(self, cmd=None):
        pass

    def start(self, cmd=None):
        print('Starting Interface')
        task = asyncio.ensure_future(self.read_loop())
        self.task_list.append(task)
        if self.ifdevice is not None:
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
        print('*****Interface: starting read_loop')
        while True:
            print(self.ifdev_rcv_buffer)
            msg = await self.ifdev_rcv_buffer.get()
            print(f'*****iface.read_loop: {msg.to_json()}')
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

        ifdev_config = json.loads('{"IFDEVICE": {"MODULE": "daq.interface.ifdevice", "CLASS": "DummyIFDevice"}, "IFDEVCONFIG": {"DESCRIPTION": {"LABEL": "Dummy IFDevice", "SERIAL_NUMBER": "1234", "PROPERTY_NUMBER": "CD0001234"}}}')
        ui_config = dict()
        ui_config['do_ui_connection'] = False
        # self.dev_mananger
        print('DummyInterface init')
        # self.ifdevice = self.dev_mananger.create('DummyIFDevice', config)
        # print(self.dev_manager)
        self.ifdevice = self.dev_manager.create('DummyIFDevice', ifdev_config, ui_config=ui_config)
        # self.idevice = IFDeviceFactory().create(ifdev_config, ui_config=None)
        # self.idevice = DummyIFDevice(ifdev_config, ui_config=None)
        # print(f'ifdevice: {self.ifdevice}')
        self.create_msg_buffers()
        # in order to make sense, child:send == parent:rcv
        # self.ifdevice.msg_send_buffer = self.ifdev_rcv_buffer
        # if self.ifdevice is not None:
        self.ifdevice.to_parent_buf = self.ifdev_rcv_buffer
        print(self.ifdevice.to_parent_buf)

    async def handle(self, msg):

        # interface will know if msg is json or object

        # check header to see if data to be sent to instrument
        #   - if yes, add timestamp
        print('type: {}'.format(msg.type))
        if (msg.type == IFDevice.class_type):
            msg.type = Interface.class_type
            msg.sender_id = self.get_id()
            if (msg.subject == 'DATA'):
                # update could be done in base class
                msg.update(msgtype=Interface.class_type)
                msg.body['DATETIME'] = util.dt_to_string()
                print(f'DummyInterface: {msg.to_json()}')
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
