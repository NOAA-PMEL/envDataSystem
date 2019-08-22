import abc
import asyncio
import utilities.util as util
import json
import importlib
import sys
from daq.daq import DAQ
from daq.interface.ifdevice import IFDevice, DummyIFDevice, IFDeviceFactory
from daq.manager.manager import Managers


class InterfaceFactory():

    @staticmethod
    def create(config, **kwargs):
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
            test = cls_(ifconfig, **kwargs)
            # print(test)
            return test

        except Exception as e:
            print(f"Interface: Unexpected error: {e}")
            raise


class Interface(DAQ):

    class_type = 'INTERFACE'

    def __init__(self, config, **kwargs):
        super(Interface, self).__init__(config, **kwargs)
        print('Interface init')

        self.name = 'Interface'

        # print(config)
        # self.config = config
        # if no NAME given, create one with address
        # self.label = self.config['LABEL']

        #  Message buffers (Queues)
#         self.msg_send_buffer = None
#         self.msg_rcv_buffer = None

#         self.ifdev_send_buffer = None
#         self.ifdev_rcv_buffer = None

#         self.gui_send_buffer = None

#         # self.create_msg_buffer()
#         # self.read_q = config['IF_READ_Q']
# #        self.write_q = config['IF_WRITE_Q']

#         self.task_list = []

        self.ifdevice_manager = Managers().get('IFDeviceManager')
        print(f'device_manager: {self.ifdevice_manager}')
        self.ifdevice = None
#        print(self.dev_mananger)

    def setup(self):
        super().setup()
        self.add_ifdevice()

    @abc.abstractmethod
    def add_ifdevice(self):
        pass
        # print('Add ifdevice')
        # # print(f'config = {self.config["IFACE_LIST"]}')
        # # for k, ifcfg in self.config['IFACE_LIST'].items():
        # #     # self.iface_map[iface.name] = iface
        # #     # print(ifcfg['IFACE_CONFIG'])
        # #     # print(ifcfg['INTERFACE'])
        # #     # iface = InterfaceFactory().create(ifcfg['IFACE_CONFIG'])
        # #     iface = InterfaceFactory().create(ifcfg)
        # #     print(f'iface: {iface}')
        # #     # iface.msg_buffer = self.iface_rcv_buffer
        # #     iface.msg_send_buffer = self.from_child_buf
        # #     self.iface_map[iface.get_id()] = iface

        # # TODO: remove hardcode and use config
        # ifdev_config = json.loads(
        #     '{"IFDEVICE": {"MODULE": "daq.interface.ifdevice", "CLASS": "DummyIFDevice"}, "IFDEVCONFIG": {"DESCRIPTION": {"LABEL": "Dummy IFDevice", "SERIAL_NUMBER": "1234", "PROPERTY_NUMBER": "CD0001234"}}}')
        # ui_config = dict()
        # # ui_config['do_ui_connection'] = False

        # self.ifdevice = self.ifdevice_manager.create(
        #     'DummyIFDevice', ifdev_config, ui_config=ui_config)
        # self.ifdevice.to_parent_buf = self.from_child_buf

    def get_ui_address(self):
        print(self.label)
        address = 'envdaq/interface/'+self.label+'/'
        print(f'get_ui_address: {address}')
        return address

    # def connect(self, cmd=None):
    #     pass

    def start(self, cmd=None):
        print('Starting Interface')
        super().start(cmd)

        # task = asyncio.ensure_future(self.read_loop())
        # self.task_list.append(task)
        if self.ifdevice is not None:
            self.ifdevice.start()

    # def read(self, cmd=None):
    #     pass

    # def write(self, cmd):
    #     pass

    # TODO: howto clean up managers?
    def stop(self, cmd=None):
        # for instrument in self.inst_map:
        #     # print(sensor)
        #     instrument.stop()

        # tasks = asyncio.Task.all_tasks()
        # for t in self.task_list:
        #     # print(t)
        #     t.cancel()

        if self.ifdevice is not None:
            self.ifdevice.stop()

        super().stop(cmd)

    def shutdown(self):
        # for instrument in self.inst_map:
        #     # print(sensor)
        #     instrument.stop()

        # tasks = asyncio.Task.all_tasks()
        # for t in self.task_list:
        #     # print(t)
        #     t.cancel()

        if self.ifdevice is not None:
            self.ifdevice.shutdown()

        super().shutdown()

    # def disconnect(self, cmd=None):
    #     pass

    # async def read_loop(self):
    #     print('*****Interface: starting read_loop')
    #     while True:
    #         print(self.ifdev_rcv_buffer)
    #         msg = await self.ifdev_rcv_buffer.get()
    #         print(f'*****iface.read_loop: {msg.to_json()}')
    #         await self.handle(msg)
    #         # await asyncio.sleep(.1)

    @abc.abstractmethod
    async def handle(self, msg):
        pass

    def get_signature(self):
        # This will combine instrument metadata to generate
        #   a unique # ID
        return self.name+":"+self.label

    # def create_msg_buffers(self, config=None):
    #     # self.read_buffer = MessageBuffer(config=config)
    #     self.ifdev_send_buffer = asyncio.Queue(loop=self.loop)
    #     self.ifdev_rcv_buffer = asyncio.Queue(loop=self.loop)

    def get_id(self):
        id = self.__class__.__name__
        if self.label is not None:
            id += ":"+self.label

        return id

# class Interface(abc.ABC):

#     class_type = 'INTERFACE'

#     def __init__(self, config):
#         print('Interface init')
#         self.loop = asyncio.get_event_loop()

#         print(config)
#         self.config = config
#         # if no NAME given, create one with address
#         self.label = self.config['LABEL']

#         #  Message buffers (Queues)
#         self.msg_send_buffer = None
#         self.msg_rcv_buffer = None

#         self.ifdev_send_buffer = None
#         self.ifdev_rcv_buffer = None

#         self.gui_send_buffer = None

#         # self.create_msg_buffer()
#         # self.read_q = config['IF_READ_Q']
# #        self.write_q = config['IF_WRITE_Q']

#         self.task_list = []

#         self.dev_manager = Managers().get('IFDeviceManager')
#         print(f'dev_manager: {self.dev_manager}')
#         self.ifdevice = None
# #        print(self.dev_mananger)

#     def connect(self, cmd=None):
#         pass

#     def start(self, cmd=None):
#         print('Starting Interface')
#         task = asyncio.ensure_future(self.read_loop())
#         self.task_list.append(task)
#         if self.ifdevice is not None:
#             self.ifdevice.start()

#     def read(self, cmd=None):
#         pass

#     def write(self, cmd):
#         pass

#     # TODO: howto clean up managers?
#     def stop(self, cmd=None):
#         # for instrument in self.inst_map:
#         #     # print(sensor)
#         #     instrument.stop()

#         # tasks = asyncio.Task.all_tasks()
#         for t in self.task_list:
#             # print(t)
#             t.cancel()

#     def disconnect(self, cmd=None):
#         pass

#     async def read_loop(self):
#         print('*****Interface: starting read_loop')
#         while True:
#             print(self.ifdev_rcv_buffer)
#             msg = await self.ifdev_rcv_buffer.get()
#             print(f'*****iface.read_loop: {msg.to_json()}')
#             await self.handle(msg)
#             # await asyncio.sleep(.1)

#     @abc.abstractmethod
#     async def handle(self, msg):
#         pass

#     def create_msg_buffers(self, config=None):
#         # self.read_buffer = MessageBuffer(config=config)
#         self.ifdev_send_buffer = asyncio.Queue(loop=self.loop)
#         self.ifdev_rcv_buffer = asyncio.Queue(loop=self.loop)

#     def get_id(self):
#         id = self.__class__.__name__
#         if self.label is not None:
#             id += ":"+self.label

#         return id


class DummyInterface(Interface):

    class_type = 'DUMMY_INTERFACE'

    def __init__(self, config, **kwargs):
        super(DummyInterface, self).__init__(config, **kwargs)

        # ifdev_config = json.loads('{"IFDEVICE": {"MODULE": "daq.interface.ifdevice", "CLASS": "DummyIFDevice"}, "IFDEVCONFIG": {"DESCRIPTION": {"LABEL": "Dummy IFDevice", "SERIAL_NUMBER": "1234", "PROPERTY_NUMBER": "CD0001234"}}}')
        # ui_config = dict()
        # ui_config['do_ui_connection'] = False
        # # self.dev_mananger
        # print('DummyInterface init')
        # # self.ifdevice = self.dev_mananger.create('DummyIFDevice', config)
        # # print(self.dev_manager)
        # self.ifdevice = self.ifdevice_manager.create('DummyIFDevice', ifdev_config, ui_config=ui_config)
        # # self.idevice = IFDeviceFactory().create(ifdev_config, ui_config=None)
        # # self.idevice = DummyIFDevice(ifdev_config, ui_config=None)
        # # print(f'ifdevice: {self.ifdevice}')
        # self.create_msg_buffers()
        # # in order to make sense, child:send == parent:rcv
        # # self.ifdevice.msg_send_buffer = self.ifdev_rcv_buffer
        # # if self.ifdevice is not None:
        # self.ifdevice.to_parent_buf = self.ifdev_rcv_buffer
        # print(self.ifdevice.to_parent_buf)

        self.name = 'DummyInterface'
        self.setup()

    def setup(self):
        super().setup()
        
    def add_ifdevice(self):
        print('Add ifdevice')
        # print(f'config = {self.config["IFACE_LIST"]}')
        # for k, ifcfg in self.config['IFACE_LIST'].items():
        #     # self.iface_map[iface.name] = iface
        #     # print(ifcfg['IFACE_CONFIG'])
        #     # print(ifcfg['INTERFACE'])
        #     # iface = InterfaceFactory().create(ifcfg['IFACE_CONFIG'])
        #     iface = InterfaceFactory().create(ifcfg)
        #     print(f'iface: {iface}')
        #     # iface.msg_buffer = self.iface_rcv_buffer
        #     iface.msg_send_buffer = self.from_child_buf
        #     self.iface_map[iface.get_id()] = iface

        # TODO: remove hardcode and use config
        ifdev_config = json.loads(
            '{"IFDEVICE": {"MODULE": "daq.interface.ifdevice", "CLASS": "DummyIFDevice"},'
            ' "IFDEVCONFIG": {"DESCRIPTION": {"LABEL": "Dummy IFDevice", "SERIAL_NUMBER": "1234", "PROPERTY_NUMBER": "CD0001234"}}}'
        )
        ui_config = dict()
        # ui_config['do_ui_connection'] = False
        
        self.ifdevice = self.ifdevice_manager.create(
            'DummyIFDevice', ifdev_config, ui_config=ui_config)
        self.ifdevice.to_parent_buf = self.from_child_buf

    async def handle(self, msg, type=None):

        # interface will know if msg is json or object

        # check header to see if data to be sent to instrument
        #   - if yes, add timestamp
        # print('type: {}'.format(msg.type))
        if (type == 'FromChild' and msg.type == IFDevice.class_type):
            msg.type = Interface.class_type
            msg.sender_id = self.get_id()
            if (msg.subject == 'DATA'):
                # update could be done in base class
                msg.update(msgtype=Interface.class_type)
                msg.body['DATETIME'] = util.dt_to_string()
                # print(f'DummyInterface: {msg.to_json()}')
                # self.msg_buffer.put_nowait(msg)
                # await self.msg_send_buffer.put(msg)
                await self.message_to_parent(msg)
        elif type == 'FromParent':
            print(f'message{msg.subject}, {msg.body}')
        else:
            print(f'Unknown Message type: {msg.type}, {msg.to_json()}')

    def get_definition_instance(self):
        return DummyInterface.get_definition()

    def get_definition():
        pass


class SerialPortInterface(Interface):

    class_type = 'SERIALPORT_INTERFACE'

    def __init__(self, config, **kwargs):
        super(SerialPortInterface, self).__init__(config, **kwargs)

        # ifdev_config = json.loads('{"IFDEVICE": {"MODULE": "daq.interface.ifdevice", "CLASS": "DummyIFDevice"}, "IFDEVCONFIG": {"DESCRIPTION": {"LABEL": "Dummy IFDevice", "SERIAL_NUMBER": "1234", "PROPERTY_NUMBER": "CD0001234"}}}')
        # ui_config = dict()
        # ui_config['do_ui_connection'] = False
        # # self.dev_mananger
        # print('DummyInterface init')
        # # self.ifdevice = self.dev_mananger.create('DummyIFDevice', config)
        # # print(self.dev_manager)
        # self.ifdevice = self.ifdevice_manager.create('DummyIFDevice', ifdev_config, ui_config=ui_config)
        # # self.idevice = IFDeviceFactory().create(ifdev_config, ui_config=None)
        # # self.idevice = DummyIFDevice(ifdev_config, ui_config=None)
        # # print(f'ifdevice: {self.ifdevice}')
        # self.create_msg_buffers()
        # # in order to make sense, child:send == parent:rcv
        # # self.ifdevice.msg_send_buffer = self.ifdev_rcv_buffer
        # # if self.ifdevice is not None:
        # self.ifdevice.to_parent_buf = self.ifdev_rcv_buffer
        # print(self.ifdevice.to_parent_buf)

        self.name = 'SerialPortInterface'
        self.label = config['LABEL']
        self.address = config['ADDRESS']
        self.setup()

    def setup(self):
        super().setup()
        
    def add_ifdevice(self):
        print('Add ifdevice')
        # print(f'config = {self.config["IFACE_LIST"]}')
        # for k, ifcfg in self.config['IFACE_LIST'].items():
        #     # self.iface_map[iface.name] = iface
        #     # print(ifcfg['IFACE_CONFIG'])
        #     # print(ifcfg['INTERFACE'])
        #     # iface = InterfaceFactory().create(ifcfg['IFACE_CONFIG'])
        #     iface = InterfaceFactory().create(ifcfg)
        #     print(f'iface: {iface}')
        #     # iface.msg_buffer = self.iface_rcv_buffer
        #     iface.msg_send_buffer = self.from_child_buf
        #     self.iface_map[iface.get_id()] = iface

        # TODO: remove hardcode and use config
        # TODO: add baud rate, etc from config
        ifdev_config = {
            "IFDEVICE": {
                "MODULE": "daq.interface.ifdevice",
                "CLASS": "SerialPortIFDevice"
            },
            "IFDEVCONFIG": {
                "DESCRIPTION": {
                    "LABEL": self.label,
                    "DEVPATH": self.address

                }
            }
        }
        # ifdev_config = json.loads(
        #     '{"IFDEVICE": {"MODULE": "daq.interface.ifdevice", "CLASS": "SerialPortIFDevice"},'
        #     ' "IFDEVCONFIG": {"DESCRIPTION": {"LABEL": "SerialPort IFDevice", "DEVPATH": "/dev/ttyUSB0"}}}'
        # )
        ui_config = dict()
        # ui_config['do_ui_connection'] = False
        
        self.ifdevice = self.ifdevice_manager.create(
            'SerialPortIFDevice', ifdev_config, ui_config=ui_config)
        self.ifdevice.to_parent_buf = self.from_child_buf

    async def handle(self, msg, type=None):

        # interface will know if msg is json or object

        # check header to see if data to be sent to instrument
        #   - if yes, add timestamp
        # print('type: {}'.format(msg.type))
        if (type == 'FromChild' and msg.type == IFDevice.class_type):
            msg.type = Interface.class_type
            msg.sender_id = self.get_id()
            if (msg.subject == 'DATA'):
                # update could be done in base class
                msg.update(msgtype=Interface.class_type)
                msg.body['DATETIME'] = util.dt_to_string()
                # print(f'Serial: {msg.to_json()}')
                # self.msg_buffer.put_nowait(msg)
                # await self.msg_send_buffer.put(msg)
                await self.message_to_parent(msg)
        elif type == 'FromParent':
            print(f'message{msg.subject}, {msg.body}')
        else:
            print(f'Unknown Message type: {msg.type}, {msg.to_json()}')

    def get_definition_instance(self):
        return DummyInterface.get_definition()

    def get_definition():
        pass

# class DummyInterface(Interface):

#     def __init__(self, config):
#         super().__init__(config)

#         ifdev_config = json.loads('{"IFDEVICE": {"MODULE": "daq.interface.ifdevice", "CLASS": "DummyIFDevice"}, "IFDEVCONFIG": {"DESCRIPTION": {"LABEL": "Dummy IFDevice", "SERIAL_NUMBER": "1234", "PROPERTY_NUMBER": "CD0001234"}}}')
#         ui_config = dict()
#         ui_config['do_ui_connection'] = False
#         # self.dev_mananger
#         print('DummyInterface init')
#         # self.ifdevice = self.dev_mananger.create('DummyIFDevice', config)
#         # print(self.dev_manager)
#         self.ifdevice = self.ifdevice_manager.create('DummyIFDevice', ifdev_config, ui_config=ui_config)
#         # self.idevice = IFDeviceFactory().create(ifdev_config, ui_config=None)
#         # self.idevice = DummyIFDevice(ifdev_config, ui_config=None)
#         # print(f'ifdevice: {self.ifdevice}')
#         self.create_msg_buffers()
#         # in order to make sense, child:send == parent:rcv
#         # self.ifdevice.msg_send_buffer = self.ifdev_rcv_buffer
#         # if self.ifdevice is not None:
#         self.ifdevice.to_parent_buf = self.ifdev_rcv_buffer
#         print(self.ifdevice.to_parent_buf)

#     async def handle(self, msg):

#         # interface will know if msg is json or object

#         # check header to see if data to be sent to instrument
#         #   - if yes, add timestamp
#         print('type: {}'.format(msg.type))
#         if (msg.type == IFDevice.class_type):
#             msg.type = Interface.class_type
#             msg.sender_id = self.get_id()
#             if (msg.subject == 'DATA'):
#                 # update could be done in base class
#                 msg.update(msgtype=Interface.class_type)
#                 msg.body['DATETIME'] = util.dt_to_string()
#                 print(f'DummyInterface: {msg.to_json()}')
#                 # self.msg_buffer.put_nowait(msg)
#                 await self.msg_send_buffer.put(msg)
#         else:
#             print('Unknown Message type: {}'.format(msg.type))


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
