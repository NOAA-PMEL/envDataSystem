import importlib
import sys
from daq.daq import DAQ
import asyncio
import abc
from data.message import MessageBuffer, Message
from daq.interface.interface import Interface, InterfaceFactory


class InstrumentFactory():

    @staticmethod
    def create(config):
        create_cfg = config['INSTRUMENT']
        instconfig = config['INSTCONFIG']
        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            # print('Creating: ' + config['name'])
            # print('   ClassName: ' + config['class'])
            mod_ = importlib.import_module(create_cfg['MODULE'])
            cls_ = getattr(mod_, create_cfg['CLASS'])
            # inst_class = eval(config['class'])
            # return inst_class.factory_create()
            return cls_(instconfig)

        # TODO: create custom exception class for our app
        # except ImportError:
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise ImportError


class Instrument(DAQ):

    class_type = 'INSTRUMENT'

    def __init__(self, config):
        super().__init__(config)
        print('init Instrument')
        # self.config = config
        print(self.config)

        self.name = 'Instrument'
        self.type = 'Generic'
        self.label = self.config['DESCRIPTION']['LABEL']
        self.mfg = None
        self.model = None

        self.serial_number = self.config['DESCRIPTION']['SERIAL_NUMBER']
        self.property_number = self.config['DESCRIPTION']['PROPERTY_NUMBER']

        # self.iface_send_buffer = None
        # self.iface_rcv_buffer = None
        self.iface_map = {}

        self.meas_map = {}

        self.iface_test = None

        # temporary
        self.last_entry = {}

        # create read buffer and interfaces
        # self.create_msg_buffers(config=None)
        self.add_interfaces()
        # add queues - these are not serializable so might
        #   need a helper function to dump configurable items

#        self.config['IFCONFIG'] = {
#            'IF_READ_Q': asyncio.Queue(loop=self.loop),
#            'IF_WRITE_Q': asyncio.Queue(loop=self.loop),
#        }

    def connect(self, cmd=None):
        pass

    def start(self, cmd=None):
        # task = asyncio.ensure_future(self.read_loop())
        print('Starting Instrument')
        task = asyncio.ensure_future(self.from_child_loop())
        self.task_list.append(task)

        for k, v in self.iface_map.items():
            self.iface_map[k].start()

    def stop(self, cmd=None):
        pass

    def disconnect(self, cmd=None):
        pass

    # async def read_loop(self):

    #     while True:
    #         msg = await self.iface_rcv_buffer.get()
    #         await self.handle(msg)
    #         # await asyncio.sleep(.1)

    def write(self, msg):
        pass

    def save_to_file(self):
        pass

    def send_to_datamanager(self):
        pass

    async def handle(self, msg, type=None):
        pass

    def get_signature(self):
        # This will combine instrument metadata to generate
        #   a unique # ID
        return self.name+":"+self.label+":"
        +self.serial_number+":"+self.property_number

    # def create_msg_buffers(self, config):
    #     # self.read_buffer = MessageBuffer(config=config)
    #     self.iface_send_buffer = asyncio.Queue(loop=self.loop)
    #     self.iface_rcv_buffer = asyncio.Queue(loop=self.loop)

    def add_interfaces(self):
        # for now, single interface but eventually loop
        # through configured interfaces
        # list = self.config['IFACE_LIST']
        for k, ifcfg in self.config['IFACE_LIST'].items():
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            # iface = InterfaceFactory().create(ifcfg['IFACE_CONFIG'])
            iface = InterfaceFactory().create(ifcfg)
            # iface.msg_buffer = self.iface_rcv_buffer
            iface.msg_send_buffer = self.from_child_buf
            self.iface_map[iface.get_id()] = iface

    def get_metadata(self):

        meta = {
            'NAME': self.name,
            'TYPE': self.type,
            'LABEL': self.label,
            'MFG': self.mfg,
            'MODEL': self.model,
            'SERIAL_NUMBER': self.serial_number,
            'property_number': self.property_number
        }
        return meta

    def get_last(self):
        return self.last_entry


class DummyInstrument(Instrument):

    def __init__(self, config):

        super().__init__(config)
        print('init DummyInstrument')

        self.name = 'DummyInstrument'
        self.type = 'DummyType'
        self.mfg = 'DumbMfg'
        self.model = 'DumbModelSX'

        # need to allow for datasets...how?

        self.meas_map = dict()
        self.meas_map['LIST'] = [
            'concentration',
            'inlet_temperature',
            'inlet_flow',
            'inlet_pressure'
        ]
        self.meas_map['DEFINITION'] = {
            'concentration': {
                'index': 0,
                'units': 'cm-3',
                'uncertainty': 0.01,
            },
            'inlet_temperature': {
                'index': 1,
                'units': 'degC',
                'uncertainty': 0.2
            },
            'inlet_flow': {
                'index': 2,
                'units': 'l/min',
                'uncertainty': 0.2,
            },
            'inlet_pressure': {
                'index': 3,
                'units': 'mb',
                'uncertainty': 0.5
            }
        }

        self.iface_meas_map = None

    async def handle(self, msg, type=None):

        # handle messages from multiple sources. What ID to use?
        if (msg.type == Interface.class_type):
            id = msg.sender_id
            entry = self.parse(msg)
            self.last_entry = entry
            print('entry = \n{}'.format(entry))

            data = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
            )
            # send data to next step(s)
            # to controller
            # data.update(subject='DATA', body=entry['DATA'])
            data.update(subject='DATA', body=entry)
            # await self.msg_buffer.put(data)
            await self.to_parent_buf.put(data)
            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)
        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    def parse(self, msg):

        entry = dict()
        entry['METADATA'] = self.get_metadata()

        data = dict()
        data['DATETIME'] = msg.body['DATETIME']
        measurements = dict()

        # TODO: data format issue: metadata in data or in its own field
        #       e.g., units in data or measurement metadata?
        # TODO: allow for "dimensions"
        values = msg.body['DATA'].split(',')
        for meas_name in self.meas_map['LIST']:
            meas_def = self.meas_map['DEFINITION'][meas_name]
            try:
                val = float(values[meas_def['index']])
            except ValueError:
                val = -999
            measurements[meas_name] = {
                'VALUE': val,
                'UNITS': meas_def['units'],
                'UNCERTAINTY': meas_def['uncertainty']
            }

        data['MEASUREMENTS'] = measurements
        entry['DATA'] = data
        return entry
