from daq.daq import DAQ
import asyncio
import random
from utilities import util
from data.message import Message
import importlib
from client.serialport import SerialPortClient
from client.tcpport import TCPPortClient
from labjack import ljm
# import abc


class IFDeviceFactory():

    @staticmethod
    def create(config, **kwargs):
        print(config)
        create_cfg = config['IFDEVICE']
        ifdevconfig = config['IFDEVCONFIG']
        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            # print('Creating: ' + config['name'])
            # print('   ClassName: ' + config['class'])
            mod_ = importlib.import_module(create_cfg['MODULE'])
            cls_ = getattr(mod_, create_cfg['CLASS'])
            # inst_class = eval(config['class'])
            # return inst_class.factory_create()
            return cls_(ifdevconfig, **kwargs)

        # TODO: create custom exception class for our app
        # except ImportError:
        except Exception as e:
            print(f"IFDevice: Unexpected error: {e}")
            raise ImportError


class IFDevice(DAQ):
    # class IFDevice():

    # channel_map = {'default': 'default'}
    class_type = 'IFDEVICE'

    def __init__(self, config, **kwargs):
        # def __init__(self, config):
        print('IFDevice init')
        super(IFDevice, self).__init__(config, **kwargs)
        # super().__init__(config)

        # self.config = config
        # self.task_list = []

        # # Message buffers
        # #   to/from parent
        # self.msg_send_buffer = None
        # self.msg_rcv_buffer = None

        self.name = 'IFDevice'
        self.type = 'Generic'
        self.label = self.config['DESCRIPTION']['LABEL']
        self.mfg = None
        self.model = None
        self.kwargs = kwargs

        # self.serial_number = self.config['DESCRIPTION']['SERIAL_NUMBER']
        # self.property_number = self.config['DESCRIPTION']['PROPERTY_NUMBER']

        self.parent_map = dict()
        self.started = False

        self.iface_map = dict()
        # self.add_interfaces()

    # # @abc.abstractmethod
    # def get_id(self):
    #     id = super().get_id()
    #     # id = 'tmp'
    #     return id

    def register_parent(
        self,
        parent_id,
        to_parent_buffer=None
    ):
        # if parent_id in self.parent_map:
        #     return
        # self.parent_map[parent_id] = {
        #     'to_parent_buffer': to_parent_buffer
        # }
        super().register_parent(
            parent_id,
            to_parent_buffer
        )
        if not self.started:
            self.start()          

    def deregister_parent(self, parent_id):
        
        # try:
        #     del self.parent_map[parent_id]
        # except KeyError:
        #     pass

        if (
            # self.started and
            len(self.parent_map) == 0
        ):
            self.stop()

    def get_ui_address(self):
        print(self.label)
        address = 'envdaq/ifdevice/'+self.label+'/'
        print(f'get_ui_address: {address}')
        return address

    # def connect(self, msg=None):
    #     pass

    def start(self, cmd=None):
        super().start(cmd)

        for k, iface in self.iface_map.items():
            iface.start()

        self.started = True

    def stop(self, cmd=None):

        for k, iface in self.iface_map.items():
            iface.stop()

        super().stop(cmd)

        self.started = False

    # def disconnect(self, msg=None):
    #     pass

    def shutdown(self):

        if self.started:
            print(f'waiting registered devices to clear')
            return

        for k, iface in self.iface_map.items():
            iface.shutdown()

        # for id, parent in self.parent_map.items():
        #     self.deregister_parent(id)

        super().shutdown()

        self.started = False

    # def add_interfaces(self):
    #     print('Add interfaces')
    #     # for now, single interface but eventually loop
    #     # through configured interfaces
    #     # list = self.config['IFACE_LIST']
    #     print(f'config = {self.config["IFACE_LIST"]}')
    #     for k, ifcfg in self.config['IFACE_LIST'].items():
    #         # self.iface_map[iface.name] = iface
    #         # print(ifcfg['IFACE_CONFIG'])
    #         # print(ifcfg['INTERFACE'])
    #         # iface = InterfaceFactory().create(ifcfg['IFACE_CONFIG'])
    #         iface = InterfaceFactory().create(ifcfg)
    #         print(f'iface: {iface}')
    #         # iface.msg_buffer = self.iface_rcv_buffer
    #         iface.msg_send_buffer = self.from_child_buf
    #         self.iface_map[iface.get_id()] = iface

    # async def handle(self, msg, type=None):
    #     print(f'ifdevice.handle: {msg}')
    #     await asyncio.sleep(.1)
    #     # pass

    def handle2(self, data):
        pass

    # def get_channel_map():
    #    return IFDevice.channel_map


class DummyIFDevice(IFDevice):

    # IFDevice.channel_map['test'] = 'test'

    def __init__(self, config, **kwargs):
        # def __init__(self, config):
        print(config)
        print('DummyIFDevice init')
        super(DummyIFDevice, self).__init__(config, **kwargs)
        # super().__init__(config)

        # TODO: fix label
        self.label = "DummyIFDevice"
        self.name = "DummyIFDevice"

        if 'DUMMY_PORT' in config['DESCRIPTION']:
            self.dummy_port = config['DESCRIPTION']['DUMMY_PORT']
        else:
            self.dummy_port = 1
    # def get_id(self):
    #     return ('DummyIFDevice')

        self.setup()

    def get_id(self):
        return self.__class__.__name__ + '_' + str(self.dummy_port)

    def setup(self):
        super().setup()

    def start(self, cmd=None):
        super().start(cmd)
        print('Starting IFDevice')
        # start dummy data loop
        task = asyncio.ensure_future(self.data_loop())
        self.task_list.append(task)

    async def data_loop(self):

        while True:

            data = '{},{},{},{},{}'.format(
                round(random.random()*1000.0, 4),
                round(random.random()*10.0, 4),
                round(random.random()*5.0, 4),
                round(random.random()*20.0, 4),
                int(round(random.random()*2000.0, 4))
            )
            # print('ifdevice: data = {}'.format(data))
            await self.handle2(data)
            await asyncio.sleep(util.time_to_next(1))

    async def handle2(self, data):
        # def handle2(self, data):

        out = {'DATA': data}
        # print(out)
        # msg = Message(subject='DATA', body=out)
        msg = Message(
            sender_id=self.get_id(),
            msgtype=IFDevice.class_type,
            subject='DATA',
            body=out
        )
        # print(msg.to_dict())
        # print(msg.to_json())
        # self.msg_send_buffer.put_nowait(msg)
        # print(f'to parent: {msg.to_json()}')
        await self.message_to_parent(msg)

    async def handle(self, msg, type=None):
        print(f'ifdevice.handle: {msg}')
        await asyncio.sleep(.1)

    def get_definition_instance(self):
        return IFDevice.get_definition()

    def get_definition():
        pass


class SerialPortIFDevice(IFDevice):

    # IFDevice.channel_map['test'] = 'test'

    def __init__(self, config, **kwargs):
        # def __init__(self, config):
        print(config)
        print('SerialPortIFDevice init')
        super(SerialPortIFDevice, self).__init__(config, **kwargs)
        # super().__init__(config)

        # TODO: fix label
        self.label = config['DESCRIPTION']['LABEL']
        self.name = "SerialPortIFDevice"

        self.devpath = config['DESCRIPTION']['DEVPATH']
        self.baudrate = config['DESCRIPTION']['baudrate']
        self.bytesize = config['DESCRIPTION']['bytesize']
        self.parity = config['DESCRIPTION']['parity']
        self.stopbits = config['DESCRIPTION']['stopbits']
        self.xonxoff = config['DESCRIPTION']['xonxoff']
        self.rtscts = config['DESCRIPTION']['rtscts']

        self.setup()

    def get_id(self):
        return self.__class__.__name__ + '_' + self.devpath

    def setup(self):
        super().setup()

    def start(self, cmd=None):
        super().start(cmd)
        print('Starting SerialPortIFDevice')

        self.client = SerialPortClient(
            uri=self.devpath,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            parity=self.parity,
            stopbits=self.stopbits,
            xonxoff=self.xonxoff,
            rtscts=self.rtscts,
            **self.kwargs,
        )
        print(f'serial port: {self.client}')

        # # start dummy data loop
        # task = asyncio.ensure_future(self.data_loop())
        # self.task_list.append(task)
        self.task_list.append(
            asyncio.ensure_future(self.read_data())
        )
        # self.task_list.append(
        #     asyncio.ensure_future(self.write_data())
        # )

    async def read_data(self):
        while True:
            data = await self.client.read()
            msg = Message(
                sender_id=self.get_id(),
                msgtype=IFDevice.class_type,
                subject='DATA',
                body={
                    'DATA': data
                }
            )
            # print(f'serialportread: {data}')
            await self.message_to_parents(msg)

    # async def write_data(self, msg):
    #     # while True:
    #     #     msg = await self.message_from_parent()
    #     await self.client.write(msg.body['COMMAND'])

    async def handle(self, msg, type=None):
        if (type == "FromParent"):
            if msg.subject == 'SEND':
                await self.client.send(msg.body)
                print(f'66666serialportifdevice.handle: {msg}')
        await asyncio.sleep(.1)

    def get_definition_instance(self):
        return IFDevice.get_definition()

    def get_definition():
        pass


class TCPPortIFDevice(IFDevice):

    # IFDevice.channel_map['test'] = 'test'

    def __init__(self, config, **kwargs):
        # def __init__(self, config):
        print(config)
        print('TCPPortIFDevice init')
        super(TCPPortIFDevice, self).__init__(config, **kwargs)
        # super().__init__(config)

        # TODO: fix label
        self.label = config['DESCRIPTION']['LABEL']
        self.name = "TCPPortIFDevice"

        self.address = config['DESCRIPTION']['ADDRESS']

        self.setup()

    def get_id(self):
        return self.__class__.__name__ + '_' + self.address[0] + '_' + self.address[1]

    def setup(self):
        super().setup()

    def start(self, cmd=None):
        super().start(cmd)
        print('Starting SerialPortIFDevice')

        self.client = TCPPortClient(
            address=self.address,
            **self.kwargs,
        )
        print(f'tcp port: {self.client}')

        # # start dummy data loop
        # task = asyncio.ensure_future(self.data_loop())
        # self.task_list.append(task)
        self.task_list.append(
            asyncio.ensure_future(self.read_data())
        )
        # self.task_list.append(
        #     asyncio.ensure_future(self.write_data())
        # )

    async def read_data(self):
        while True:
            data = await self.client.read()
            msg = Message(
                sender_id=self.get_id(),
                msgtype=IFDevice.class_type,
                subject='DATA',
                body={
                    'DATA': data
                }
            )
            # print(f'tcpportread: {data}')
            await self.message_to_parents(msg)

    # async def write_data(self, msg):
    #     # while True:
    #     #     msg = await self.message_from_parent()
    #     await self.client.write(msg.body['COMMAND'])

    async def handle(self, msg, type=None):
        if (type == "FromParent"):
            if msg.subject == 'SEND':
                await self.client.send(msg.body)
                # print(f'tcpportifdevice.handle: {msg.to_json()}')
        else:
            print('unkown msg')
        
        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            pass

    def get_definition_instance(self):
        return IFDevice.get_definition()

    def get_definition():
        pass

# class IFDeviceOLD(DAQ):
#     # class IFDevice():

#     # channel_map = {'default': 'default'}
#     class_type = 'IFDEVICE'

#     def __init__(self, config, **kwargs):
#         # def __init__(self, config):
#         print('IFDevice init')
#         super(IFDevice, self).__init__(config, **kwargs)
#         # super().__init__(config)

#         self.config = config
#         self.task_list = []

#         # Message buffers
#         #   to/from parent
#         self.msg_send_buffer = None
#         self.msg_rcv_buffer = None

#     # @abc.abstractmethod
#     def get_id(self):
#         id = super().get_id()
#         # id = 'tmp'
#         return id

#     def get_ui_address(self):
#         print(self.label)
#         address = 'envdaq/ifdevice/'+self.label+'/'
#         print(f'get_ui_address: {address}')
#         return address

#     def connect(self, msg=None):
#         pass

#     def start(self, msg=None):
#         pass

#     def stop(self, msg=None):
#         pass

#     def disconnect(self, msg=None):
#         pass

#     async def handle(self, data, type=None):
#         await asyncio.sleep(1)
#         # pass

#     def handle2(self, data):
#         pass

#     # def get_channel_map():
#     #    return IFDevice.channel_map


class LabJackT7Device(IFDevice):

    # IFDevice.channel_map['test'] = 'test'

    def __init__(self, config, **kwargs):
        # def __init__(self, config):
        print(config)
        print('LabJackT7Device init')
        super(LabJackT7Device, self).__init__(config, **kwargs)
        # super().__init__(config)

        # TODO: fix label
        self.label = config['DESCRIPTION']['LABEL']
        self.name = "LabJackT7Device"

        self.device_type = 'T7'
        self.conection_type = 'ANY'
        if 'connection_type' in config['DESCRIPTION']:
            self.conection_type = config['DESCRIPTION']['connection_type']
        self.identifier = 'ANY'
        if 'identifier' in config['DESCRIPTION']:
            self.identifier = config['DESCRIPTION']['identifier']
        if 'serial_number' in config['DESCRIPTION']:
            self.identifier = config['DESCRIPTION']['serial_number']

        self.lj = None

        # self.devpath = config['DESCRIPTION']['DEVPATH']
        # self.baudrate = config['DESCRIPTION']['baudrate']
        # self.bytesize = config['DESCRIPTION']['bytesize']
        # self.parity = config['DESCRIPTION']['parity']
        # self.stopbits = config['DESCRIPTION']['stopbits']
        # self.xonxoff = config['DESCRIPTION']['xonxoff']
        # self.rtscts = config['DESCRIPTION']['rtscts']

        self.setup()

    def get_id(self):
        return self.__class__.__name__ + '_' + self.identifier

    def setup(self):
        super().setup()

    def start(self, cmd=None):
        super().start(cmd)
        print('Starting LabJackT7Device')

        try:
            self.lj = ljm.openS(
                deviceType=self.device_type,
                connectionType=self.conection_type,
                identifier=self.identifier
            )
        except ljm.LJMError as e:
            print(f'could not connect to labjack: {e}')
            self.lj = None

        # self.client = SerialPortClient(
        #     uri=self.devpath,
        #     baudrate=self.baudrate,
        #     bytesize=self.bytesize,
        #     parity=self.parity,
        #     stopbits=self.stopbits,
        #     xonxoff=self.xonxoff,
        #     rtscts=self.rtscts,
        #     **self.kwargs,
        # )
        # print(f'serial port: {self.client}')

        # # start dummy data loop
        # task = asyncio.ensure_future(self.data_loop())
        # self.task_list.append(task)

        # self.task_list.append(
        #     asyncio.ensure_future(self.read_data())
        # )

        # self.task_list.append(
        #     asyncio.ensure_future(self.write_data())
        # )

    def stop(self, cmd=None):
        if self.lj:
            ljm.close(self.lj)
        self.lj = None

        super().stop(cmd)

    async def read_data(self):
        while True:
            data = await self.client.read()
            msg = Message(
                sender_id=self.get_id(),
                msgtype=IFDevice.class_type,
                subject='DATA',
                body={
                    'DATA': data
                }
            )
            # print(f'serialportread: {data}')
            await self.message_to_parent(msg)

    # async def write_data(self, msg):
    #     # while True:
    #     #     msg = await self.message_from_parent()
    #     await self.client.write(msg.body['COMMAND'])

    async def handle(self, msg, type=None):
        if (type == "FromParent"):
            if msg.subject == 'SEND':
                
                # await self.client.send(msg.body)
                # print(f'66666serialportifdevice.handle: {msg}')

                if msg.body['cmd'] == 'set_voltage':
                    ljm.eWriteName(
                        self.lj,
                        msg.body['channel'],
                        msg.body['value']
                    )
        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            pass

    def get_definition_instance(self):
        return IFDevice.get_definition()

    def get_definition():
        pass
