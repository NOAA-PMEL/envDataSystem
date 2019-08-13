import abc
import importlib
import sys
from daq.daq import DAQ
import asyncio
from data.message import Message
from daq.interface.interface import Interface, InterfaceFactory


class InstrumentFactory():

    @staticmethod
    def create(config, **kwargs):
        create_cfg = config['INSTRUMENT']
        instconfig = config['INSTCONFIG']
        alias = None
        if 'ALIAS' in config:
            alias = config['ALIAS']
        print("module: " + create_cfg['MODULE'])
        print("class: " + create_cfg['CLASS'])

        try:
            # print('Creating: ' + config['name'])
            # print('   ClassName: ' + config['class'])
            mod_ = importlib.import_module(create_cfg['MODULE'])
            cls_ = getattr(mod_, create_cfg['CLASS'])
            # inst_class = eval(config['class'])
            # return inst_class.factory_create()
            return cls_(instconfig, alias=alias, **kwargs)

        # TODO: create custom exception class for our app
        # except ImportError:
        except:
            print("Instrument:Unexpected error:", sys.exc_info()[0])
            raise ImportError


class Instrument(DAQ):

    class_type = 'INSTRUMENT'

    def __init__(self, config, alias=None, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):
        super(Instrument, self).__init__(config, **kwargs)
        # super().__init__(
        #     config,
        #     ui_config=ui_config,
        #     auto_connect_ui=auto_connect_ui
        # )
        print('init Instrument')
        # self.config = config
        print(self.config)

        self.name = 'Instrument'
        self.type = 'Generic'
        self.label = self.config['DESCRIPTION']['LABEL']
        self.mfg = None
        self.model = None

        self.alias = dict()
        if alias:
            self.alias = alias

        self.serial_number = self.config['DESCRIPTION']['SERIAL_NUMBER']
        self.property_number = self.config['DESCRIPTION']['PROPERTY_NUMBER']

        # self.iface_send_buffer = None
        # self.iface_rcv_buffer = None
        self.iface_map = {}

        self.meas_map = {}
        self.measurements = dict()
        self.measurements['meta'] = dict()
        self.measurements['measurement_sets'] = dict()

        self.iface_test = None

        # temporary
        self.last_entry = {}

        # create read buffer and interfaces
        # self.create_msg_buffers(config=None)

        # *****
        # self.add_interfaces()
        # *****

        # self.setup()

        # self.add_measurements()

        # TODO: send meta to ui to "build" instrument there

        # add queues - these are not serializable so might
        #   need a helper function to dump configurable items

#        self.config['IFCONFIG'] = {
#            'IF_READ_Q': asyncio.Queue(loop=self.loop),
#            'IF_WRITE_Q': asyncio.Queue(loop=self.loop),
#        }

    def setup(self):

        self.add_interfaces()

        # add measurements
        self.add_measurements()

        # tell ui to build instrument
        msg = Message(
            sender_id=self.get_id(),
            msgtype='Instrument',
            subject='CONFIG',
            body={
                'purpose': 'SYNC',
                'type': 'INSTRUMENT_INSTANCE',
                'data': self.get_metadata()
            }
        )
        self.message_to_ui_nowait(msg)
        print(f'setup: {msg.body}')

    def get_ui_address(self):
        print(self.label)
        address = 'envdaq/instrument/'+self.label+'/'
        print(f'get_ui_address: {address}')
        return address

    # def connect(self, cmd=None):
    #     pass

    def start(self, cmd = None):
        # task = asyncio.ensure_future(self.read_loop())
        print(f'Starting Instrument {self}')
        super().start(cmd)

        # task = asyncio.ensure_future(self.from_child_loop())
        # self.task_list.append(task)

        for k, iface in self.iface_map.items():
            iface.start()

    def stop(self, cmd=None):
        print('Instrument.stop()')

        for k, iface in self.iface_map.items():
            iface.stop()

        super().stop(cmd)

    def shutdown(self):

        for k, iface in self.iface_map.items():
            iface.shutdown()

        super().shutdown()

    # def disconnect(self, cmd=None):
    #     pass

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

    @abc.abstractmethod
    async def handle(self, msg, type = None):
        pass

    def get_signature(self):
        # This will combine instrument metadata to generate
        #   a unique # ID
        return self.name+":"+self.label+":"
        + self.serial_number+":"+self.property_number

    # def create_msg_buffers(self, config):
    #     # self.read_buffer = MessageBuffer(config=config)
    #     self.iface_send_buffer = asyncio.Queue(loop=self.loop)
    #     self.iface_rcv_buffer = asyncio.Queue(loop=self.loop)

    def add_interfaces(self):
        print('Add interfaces')
        # for now, single interface but eventually loop
        # through configured interfaces
        # list = self.config['IFACE_LIST']
        print(f'config = {self.config["IFACE_LIST"]}')
        for k, ifcfg in self.config['IFACE_LIST'].items():
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            # print(ifcfg['INTERFACE'])
            # iface = InterfaceFactory().create(ifcfg['IFACE_CONFIG'])
            iface=InterfaceFactory().create(ifcfg)
            print(f'iface: {iface}')
            # iface.msg_buffer = self.iface_rcv_buffer
            # iface.msg_send_buffer = self.from_child_buf
            iface.to_parent_buf=self.from_child_buf
            self.iface_map[iface.get_id()]=iface

    def get_metadata(self):

        # print(f'**** get_metadata: {self}')

        # TODO: force alias or do a better job of defaults
        if len(self.alias) == 0:
            self.alias['name'] = self.label,
            self.alias['prefix'] = self.label

        meta = {
            'NAME': self.name,
            'TYPE': self.type,
            'LABEL': self.label,
            'MFG': self.mfg,
            'MODEL': self.model,
            'SERIAL_NUMBER': self.serial_number,
            'property_number': self.property_number,
            'measurement_meta': self.measurements['meta'],
            'alias': self.alias
        }
        return meta

    def get_last(self):
        return self.last_entry
    
    def add_measurements(self):
        # print('******add measurements')
        definition = self.get_definition_instance()
        # print('definition')
        if 'measurement_config' in definition['DEFINITION']:
            config = definition['DEFINITION']['measurement_config']
            self.measurements['meta'] = config
            for set_name, meas_set in config.items():
                # print(f'set_name: {set_name}')
                self.measurements['measurement_sets'][set_name] = dict()
                mset = self.measurements['measurement_sets'][set_name]
                for name, meas_cfg in meas_set.items():
                    # print(f'name: {name}')
                    mset[name] = dict()
                    mset[name]['value'] = None

        # print(f'add_measurement: {self.measurements}')


class DummyInstrument(Instrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):

        super(DummyInstrument, self).__init__(config, **kwargs)
        # super().__init__(
        #     config,
        #     ui_config=ui_config,
        #     auto_connect_ui=auto_connect_ui
        # )
        # print('init DummyInstrument')

        self.name = 'DummyInstrument'
        self.type = 'DummyType'
        self.mfg = 'DumbMfg'
        self.model = 'DumbModelSX'
        self.tag_list = [
            'dummy',
            'testing',
            'development',
        ]

        # need to allow for datasets...how?

        # definition = DummyInstrument.get_definition()

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

        self.setup()

    def setup(self):
        super().setup()

        # add instance specific setup here

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            id = msg.sender_id
            entry = self.parse(msg)
            self.last_entry = entry
            # print('entry = \n{}'.format(entry))

            data = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
            )
            # send data to next step(s)
            # to controller
            # data.update(subject='DATA', body=entry['DATA'])
            data.update(subject='DATA', body=entry)
            # await self.msg_buffer.put(data)
            # await self.to_parent_buf.put(data)
            await self.message_to_ui(data)
            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)
        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    def parse(self, msg):
        # print(f'parse: {msg.to_json()}')
        entry = dict()
        entry['METADATA'] = self.get_metadata()

        data = dict()
        data['DATETIME'] = msg.body['DATETIME']
        measurements = dict()

        # TODO: data format issue: metadata in data or in its own field
        #       e.g., units in data or measurement metadata?
        # TODO: allow for "dimensions"
        values = msg.body['DATA'].split(',')
        # print(f'values: {values}')
        meas_list = [
            'concentration',
            'inlet_temperature',
            'inlet_flow',
            'inlet_pressure',
            'pump_power'
        ]
        for i, name in enumerate(meas_list):
            # TODO: use meta to convert to float, int
            try:
                val = float(values[i])
            except ValueError:
                val = -999
            measurements[name] = {
                'VALUE': val,
            }

        # for meas_name in self.meas_map['LIST']:
        #     meas_def = self.meas_map['DEFINITION'][meas_name]
        #     try:
        #         val = float(values[meas_def['index']])
        #     except ValueError:
        #         val = -999
        #     measurements[meas_name] = {
        #         'VALUE': val,
        #         'UNITS': meas_def['units'],
        #         'UNCERTAINTY': meas_def['uncertainty']
        #     }

        data['MEASUREMENTS'] = measurements
        entry['DATA'] = data
        return entry

    def get_definition_instance(self):
        return DummyInstrument.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = DummyInstrument.__module__
        definition['name'] = DummyInstrument.__name__
        definition['mfg'] = 'DummyMfg'
        definition['model'] = 'DumbModelSX'
        definition['type'] = 'DummyType'
        definition['tags'] = [
            'dummy',
            'testing',
            'development',
        ]

        measurement_config = dict()

        primary_meas = dict()
        primary_meas['concentration'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': None,
        }

        process_meas = dict()
        process_meas['inlet_temperature'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': 'inlet_temperature_sp',
        }

        process_meas['inlet_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': 'inlet_flow_sp',
        }

        process_meas['inlet_pressure'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'mb',  # should be cfunits or udunits
            'uncertainty': 0.4,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
        }

        raw_meas = dict()
        raw_meas['pump_power'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': None,
        }

        controls = dict()
        controls['inlet_temperature_sp'] = {
            'data_type': 'NUMERIC',
            # units are tied to parameter this controls
            'allowed_range': [10.0, 30.0],
        }
        controls['inlet_flow_sp'] = {
            'data_type': 'NUMERIC',
            # units are tied to parameter this controls
            'allowed_range': [0.0, 2.0],
        }

        measurement_config['primary'] = primary_meas
        measurement_config['process'] = process_meas
        measurement_config['raw'] = raw_meas
        measurement_config['controls'] = controls

        definition['measurement_config'] = measurement_config

        DAQ.daq_definition['DEFINITION'] = definition
        return DAQ.daq_definition
