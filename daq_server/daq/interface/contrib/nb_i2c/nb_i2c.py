import asyncio
from daq.interface.interface import Interface, InterfaceFactory
from daq.interface.ifdevice import IFDevice
# from shared.data.message import Message
# from shared.data.status import Status
# import json
import binascii
from struct import unpack
from struct import error as structerror


class NB_I2C_Interface(Interface):

    class_type = 'NB_I2C_Interface'

    def __init__(self, config, ui_config=None, **kwargs):
        super(NB_I2C_Interface, self).__init__(
            config,
            ui_config=ui_config,
            **kwargs
        )

        self.name = 'NB_I2C_Interface'
        self.label = config['LABEL']

        self.address = None
        if 'I2C_ADDRESS' in config:
            self.i2c_address = config['I2C_ADDRESS']

        self.host_interface_cfg = None
        if 'HOST_IFACE' in config:
            self.host_interface_cfg = config['HOST_IFACE']

        self.host_ui_config = ui_config

        # self.host = 'localhost'
        # if 'HOST' in config:
        #     self.host = config['HOST']
        # self.port = 4001
        # if 'PORT' in config:
        #     self.port = config['PORT']
        # self.address = (self.host, self.port)
        self.setup()

    def setup(self):
        super().setup()
    #     self.add_interface()

    # def add_interface(self):
    #     print('Add host interface')

    #     if self.host_interface_cfg:

    #         iface_options = dict()

    #         iface = InterfaceFactory().create(
    #             self.host_interface_cfg,
    #             ui_config=self.ui_config,
    #             **iface_options
    #         )
    #         iface.to_parent_buf = self.from_child_buf
    #         self.iface_map[iface.get_id()] = iface
    #         # if cfg_comps:
    #         #     for comp, label in cfg_comps.items():
    #         #         if label == k:
    #         #             self.iface_components[comp] = iface.get_id()
    #         # else:
    #         #     self.iface_components['default'] = (
    #         #         iface.get_id()
    #         #     )
    #         # print(f'iface_map: {self.iface_map}')
    #         # print(f'iface_comp: {self.iface_components}')

    def start(self, cmd=None):
        super().start(cmd)
        # print(f'self.get_id(): {self.get_id()}')

    def add_ifdevice(self):
        # print('Add ifdevice')

        # TODO: remove hardcode and use config
        # TODO: add baud rate, etc from config
        ifdev_config = {
            "IFDEVICE": {
                "MODULE": "daq.interface.contrib.nb_i2c.nb_i2c",
                "CLASS": "NB_I2C_IFDevice"
            },
            "IFDEVCONFIG": {
                "DESCRIPTION": {
                    "LABEL": self.label,
                    "HOST_IFACE": self.host_interface_cfg,
                    "HOST_UI_CONFIG": self.host_ui_config
                }
            }
        }
        ui_config = dict()

        self.ifdevice = self.ifdevice_manager.create(
            'NB_I2C_IFDevice',
            ifdev_config,
            ui_config=ui_config,
            **self.kwargs
        )
        # self.ifdevice.register_parent(
        #     self.get_id(),
        #     to_parent_buffer=self.from_child_buf
        # )
        # self.ifdevice.to_parent_buf = self.from_child_buf
        print(f'self.ifdevice.to_parent_buf {self.ifdevice.to_parent_buf}')

    async def handle(self, msg, type=None):

        # interface will know if msg is json or object

        # check header to see if data to be sent to instrument
        #   - if yes, add timestamp
        # print('type: {}'.format(msg.type))
        if (type == 'FromChild' and msg.type == IFDevice.class_type):
            msg.type = Interface.class_type
            msg.sender_id = self.get_id()
            if (msg.subject == 'DATA'):
                if (
                    'address' in msg.body['DATA'] and
                    msg.body['DATA']['address'] == self.i2c_address
                ):
                    msg.update(msgtype=Interface.class_type)
                    # print(f'nbif to parent: {msg}')
                    await self.message_to_parent(msg)

        elif type == 'FromParent':
            # print(f'message{msg.subject}, {msg.body}')
            # parent_msg = self.handle_parent_message(msg)
            body = msg.body
            msg.update(
                body={
                    'address': self.i2c_address,
                    'cmd_args': body
                }
            )
            # print(f'nbif from parent {msg}')
            await self.ifdevice.message_from_parent(msg)
        else:
            print(f'Unknown Message type: {msg.type}, {msg.to_json()}')

    def get_definition_instance(self):
        return NB_I2C_Interface.get_definition()

    def get_definition():
        pass


class NB_I2C_IFDevice(IFDevice):

    # IFDevice.channel_map['test'] = 'test'

    def __init__(self, config, **kwargs):
        # def __init__(self, config):
        # print(config)
        print('NB_I2C_IFDevice init')
        super(NB_I2C_IFDevice, self).__init__(config, **kwargs)
        # super().__init__(config)

        # TODO: fix label
        self.label = config['DESCRIPTION']['LABEL']
        self.name = "NB_I2C_IFDevice"

        self.host_interface_cfg = None
        if 'HOST_IFACE' in config['DESCRIPTION']:
            self.host_interface_cfg = config['DESCRIPTION']['HOST_IFACE']

        self.host_ui_cfg = None
        if 'HOST_UI_CONFIG' in config['DESCRIPTION']:
            self.host_ui_cfg = config['DESCRIPTION']['HOST_UI_CONFIG']

        self.iface = None
        self.iface_map = {}

        self.read_status = 'READY'
        self.current_address = None
        self.current_cmd_type = 'WRITE'
        self.current_read_length = None
        # self.address = config['DESCRIPTION']['ADDRESS']

        self.data = None

        self.i2c_cmd_buffer = asyncio.Queue()

        self.setup()

    # def get_id(self):
    #     return self.__class__.__name__ + '_' + self.i2c_address

    def setup(self):
        super().setup()
        self.add_interface()

    def enable(self):
        super().enable()
        if self.iface:
            self.iface.enable()
            
        self.task_list.append(
            asyncio.ensure_future(self.send_cmd_loop())
        )

    # def disable(self):
        
    def add_interface(self):
        print('Add host interface')

        if self.host_interface_cfg:

            iface_options = dict()

            ifcfg = next(iter(self.host_interface_cfg.values()))
            iface = InterfaceFactory().create(
                ifcfg,
                ui_config=self.host_ui_cfg,
                **iface_options
            )
            iface.to_parent_buf = self.from_child_buf
            self.iface_map[iface.get_id()] = iface
            self.iface = iface

    def start(self, cmd=None):
        super().start(cmd)
        print('Starting NB_I2C_IFDevice')

        # self.client = TCPPortClient(
        #     address=self.address,
        #     **self.kwargs,
        # )
        # # print(f'tcp port: {self.client}')

        # # start dummy data loop
        # task = asyncio.ensure_future(self.data_loop())
        # self.task_list.append(task)
        # self.task_list.append(
        #     asyncio.ensure_future(self.send_cmd_loop())
        # )
        # self.task_list.append(
        #     asyncio.ensure_future(self.write_data())
        # )

        # if self.iface:
        #     self.iface.start()

    # def stop(self, cmd=None):
    #     super().stop(cmd)

    #     if self.iface:
    #         self.iface.stop()

    #     for task in self.task_list:
    #         task.cancel()

    async def send_cmd_loop(self):

        while True:
            if self.read_status == 'READY':
                msg = await self.i2c_cmd_buffer.get()

                # send command
                self.read_status = 'BUSY'
                self.current_address = msg.body['address']
                cmd = self.get_command(msg.body['cmd_args'])
                msg.update(
                    subject='SEND',
                    body=cmd
                )
                # print(f'nbid from parent: {msg}')
                await self.iface.message_from_parent(msg)
                # print("here")
            else:
                await asyncio.sleep(.1)

    def get_command(self, cmd_args):

        cmd = ''
        if cmd_args['command'] == 'write_byte':
            address = cmd_args["address"]
            data = cmd_args["data"]
            # args=['cmd'] = msg.subject
            cmd = f'#WB{address}{data}\n'
            self.current_cmd_type = 'WRITE'

        elif cmd_args['command'] == 'write_buffer':
            address = cmd_args["address"]
            length = cmd_args['write_length']
            data = cmd_args["data"]
            # args=['cmd'] = msg.subject
            cmd = f'#WW{address}{length}{data}\n'
            self.current_cmd_type = 'WRITE'

        elif cmd_args['command'] == 'read_byte':
            address = cmd_args["address"]
            cmd = f'#RB{address}\n'
            self.current_cmd_type = 'READ'
            self.current_read_length = 1

        elif cmd_args['command'] == 'read_buffer':
            address = cmd_args["address"]
            length = cmd_args['read_length']
            cmd = f'#RR{address}{length}\n'
            self.current_cmd_type = 'READ'
            self.current_read_length = length

        else:
            return None

        return cmd

    # async def (self):

    async def handle(self, msg, type=None):
        if (type == "FromParent"):
            # if msg.subject == 'SEND':
            #     await self.client.send(msg.body)
            if msg.subject == 'SEND':
                # place in queue
                await self.i2c_cmd_buffer.put(msg)

        elif (type == 'FromChild' and msg.type == Interface.class_type):
            # msg.type = IFDevice.class_type
            # msg.sender_id = self.get_id()
            # print(f'nbid {msg.to_json()}')
            if (msg.subject == 'DATA'):
                # update could be done in base class
                if self.read_status == 'BUSY':
                    # if msg.body == 'OK':
                    if '0x' not in msg.body['DATA']:
                        dt = msg.body['DATETIME']
                        result = msg.body['DATA'].strip()
                        body = {
                            'DATETIME': dt,
                            'DATA': {
                                'address': self.current_address,
                                'command': self.current_cmd_type,
                                'data': self.data,
                                'result': result
                            }
                        }
                        # msg = Message(
                        #     msgtype=IFDevice.class_type,
                        #     sender=self.get_id(),
                        #     # body=body
                        # )
                        # msg.data['DATA'] = body_data
                        id = self.get_id()
                        msg.update(
                            msgtype=IFDevice.class_type,
                            sender_id=self.get_id(),
                            body=body
                        )
                        self.read_status = 'READY'
                        # print(f'nbid to parent: {msg}')
                        await self.message_to_parents(msg)
                    else:
                        if self.current_cmd_type == 'READ':
                            try:
                                hexdata = msg.body['DATA'].strip()
                                bindata = binascii.unhexlify(
                                    hexdata[2:]
                                )
                                self.current_read_length
                                fmt = f'<{self.current_read_length}B'
                                self.data = unpack(fmt, bindata)
                            except structerror:
                                self.data = None
                        else:
                            self.data = None
                # else:
                #     await self.message_to_parent(msg)

        else:
            print('unkown msg')

        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            pass

    def get_definition_instance(self):
        return NB_I2C_IFDevice.get_definition()

    def get_definition():
        pass
