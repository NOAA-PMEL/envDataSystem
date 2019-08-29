from daq.instrument.instrument import Instrument
from data.message import Message
from daq.daq import DAQ
from daq.interface.interface import Interface, InterfaceFactory
# import json
from plots.plots import PlotManager
from plots.apps.plot_app import TimeSeries1D


class MagCompass(Instrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):

        super(MagCompass, self).__init__(config, **kwargs)
        # super().__init__(
        #     config,
        #     ui_config=ui_config,
        #     auto_connect_ui=auto_connect_ui
        # )
        # print('init DummyInstrument')

        self.name = 'MagCompass'
        self.type = 'Navigation'
        self.mfg = 'PMEL'
        self.model = 'MagneticCompass'
        self.tag_list = [
            'navigation',
            'heading',
            'course',
            'orientation'
        ]

        # need to allow for datasets...how?

        # definition = DummyInstrument.get_definition()

        self.meas_map = dict()
        self.meas_map['LIST'] = [
            'course',
            'pitch',
            'roll',
            'tilt'
        ]
        # self.meas_map['DEFINITION'] = {
        #     'course': {
        #         'index': 0,
        #         'units': 'cm-3',
        #         'uncertainty': 0.01,
        #     },
        #     'inlet_temperature': {
        #         'index': 1,
        #         'units': 'degC',
        #         'uncertainty': 0.2
        #     },
        #     'inlet_flow': {
        #         'index': 2,
        #         'units': 'l/min',
        #         'uncertainty': 0.2,
        #     },
        #     'inlet_pressure': {
        #         'index': 3,
        #         'units': 'mb',
        #         'uncertainty': 0.5
        #     }
        # }

        self.iface_meas_map = None

        self.setup()

    def setup(self):
        super().setup()
        # print(f'dummyinstrument.setup')
        # add instance specific setup here

        # meta = self.get_metadata()
        # PlotManager.add_app(
        #     TimeSeries1D(
        #         meta,
        #         name=('/instrument_'+meta['plot_meta']['name'])
        #     ),
        #     start_after_add=True
        # )

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            id = msg.sender_id
            entry = self.parse(msg)
            # print(f'last_entry: {self.last_entry}')
            # if (
            #     'DATETIME' in self.last_entry and
            #     self.last_entry['DATETIME'] == entry['DATA']['DATETIME']
            # ):
            #     print(f'88888888888 skipped entry')
            #     return
            # self.last_entry['DATETIME'] = entry['DATA']['DATETIME']
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
            # print(f'instrument data: {data.to_json()}')
            await self.message_to_ui(data)
            await PlotManager.update_data(self.plot_name, data.to_json())
            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)
        elif type == 'FromUI':
            if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                self.send_status()

            elif msg.subject == 'CONTROLS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                await self.set_control(msg.body['control'], msg.body['value'])
            elif msg.subject == 'RUNCONTROLS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                await self.handle_control_action(msg.body['control'], msg.body['value'])
                # await self.set_control(msg.body['control'], msg.body['value'])

        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        if control and value:
            if control == 'start_stop':
                if value == 'START':
                    self.start()
                elif value == 'STOP':
                    self.stop()

                # print(f'{self.iface_map}')
                # await self.to_child_buf.put(cmd)
                # await self.iface_map['DummyInterface:test_interface'].message_from_parent(cmd)
                self.set_control_att(control, 'action_state', 'OK')

    def parse(self, msg):
        # print(f'parse: {msg.to_json()}')
        entry = dict()
        entry['METADATA'] = self.get_metadata()

        data = dict()
        data['DATETIME'] = msg.body['DATETIME']

        # TODO: how to limit to one/sec
        # check for new second
        # if data['DATETIME'] == self.last_entry['DATA']['DATETIME']:
        #     # don't duplicate timestamp for now
        #     return
        # self.last_entry['DATETIME'] = data['DATETIME']

        measurements = dict()

        # TODO: data format issue: metadata in data or in its own field
        #       e.g., units in data or measurement metadata?
        # TODO: allow for "dimensions"
        parsed = dict()
        values = msg.body['DATA'].split('*')
        parsed['checksum'] = values[1]
        values = values[0].split('T')
        parsed['tilt'] = values[1]
        values = values[0].split('R')
        parsed['roll'] = values[1]
        values = values[0].split('P')
        parsed['pitch'] = values[1]
        values = values[0].split('C')
        parsed['course'] = values[1]
        # print(f'{course}, {pitch}, {roll}, {tilt}, {checksum}\n')

        # values = msg.body['DATA'].split(',')
        # print(f'values: {values}')
        meas_list = [
            'course',
            'pitch',
            'roll',
            'tilt',
            # 'checksum',
        ]
        controls_list = []

        for name in meas_list:
            # TODO: use meta to convert to float, int
            try:
                val = float(parsed[name])
            except ValueError:
                val = -999
            measurements[name] = {
                'VALUE': val,
            }

        for name in controls_list:
            measurements[name] = {
                'VALUE': self.get_control_att(name, 'value'),
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
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return MagCompass.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = MagCompass.__module__
        definition['name'] = MagCompass.__name__
        definition['mfg'] = 'PMEL'
        definition['model'] = 'MagneticCompass'
        definition['type'] = 'Navigation'
        definition['tags'] = [
            'navigation',
            'heading',
            'course',
            'orientation'
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []

        # TODO: add interface entry for each measurement
        primary_meas = dict()
        primary_meas['course'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'deg',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': None,
        }
        y_data.append('course')

        primary_meas['pitch'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'deg',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': None,
        }
        y_data.append('pitch')

        primary_meas['roll'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'deg',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': None,
        }
        y_data.append('roll')

        primary_meas['tilt'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'deg',  # should be cfunits or udunits
            'uncertainty': 0.4,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'control': None,
        }
        y_data.append('tilt')

        measurement_config['primary'] = primary_meas

        definition['measurement_config'] = measurement_config

        plot_config = dict()
        time_series1d = dict()

        time_series1d['y_data'] = y_data
        time_series1d['default_y_data'] = ['course']
        plot_config['TimeSeries1D'] = time_series1d
        definition['plot_config'] = plot_config

        return {'DEFINITION': definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition
