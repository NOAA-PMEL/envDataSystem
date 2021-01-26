import json
from daq.instrument.instrument import Instrument
from shared.data.message import Message
from daq.daq import DAQ
import asyncio
from shared.utilities.util import time_to_next
from daq.interface.interface import Interface
# from plots.plots import PlotManager
# from plots.apps.plot_app import TimeSeries1D


class BrechtelInstrument(Instrument):

    INSTANTIABLE = False

    def __init__(self, config, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):

        super(BrechtelInstrument, self).__init__(config, **kwargs)

        self.mfg = 'Brechtel'

    def setup(self):
        super().setup()

        # TODO: add properties get/set to interface for
        #       things like readmethod


class MCPC(BrechtelInstrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(MCPC, self).__init__(config, **kwargs)

        self.name = 'MCPC'
        self.model = 'MCPC'
        self.tag_list = [
            'concentration',
            'aerosol',
            'physics'
        ]

        # self.meas_map = dict()
        # self.meas_map = [
        #     'concentration',
        #     'raw_concentration'
        # ]

        self.iface_meas_map = None
        self.polling_task = None
        self.current_poll_cmds = ['read\n', 'raw=2\n']
        self.current_read_cnt = 0

        self.iface_options = {
            'read_method': 'readuntil',
            'read_terminator': '\r',
        }
        self.setup()

    def setup(self):
        super().setup()
        self.iface = next(iter(self.iface_map.values()))

        # add polling loop
        # if polled:
        self.is_polled = True
        self.poll_rate = 1  # every second

        # create parse_map and empty data_record
        self.parse_map = dict()
        self.data_record_template = dict()
        definition = self.get_definition_instance()
        meas_config = definition['DEFINITION']['measurement_config']
        for msetsname, mset in meas_config.items():
            # self.data_record_template[msetname] = dict()
            for name, meas in mset.items():
                parse_label = meas['parse_label']
                self.parse_map[parse_label] = name
                # self.data_record_template[msetsname][name] = None
                self.data_record_template[name] = {'VALUE': None}

    def start(self, cmd=None):
        super().start()

        # self.clean_data_record()
        if self.is_polled:
            self.polling_task = asyncio.ensure_future(self.poll_loop())

        self.current_read_cnt = 0

        # TODO: send start cmd to instrument

    def stop(self, cmd=None):
        if self.polling_task:
            self.polling_task.cancel()

        super().stop()

    async def poll_loop(self):
        print(f'polling loop started')
        while True:
            # TODO: implement current_poll_cmds
            cmds = self.current_poll_cmds
            print(f'cmds: {cmds}')
            # cmds = ['read\n']

            if self.iface:
                self.current_read_cnt = 0
                for cmd in cmds:
                    msg = Message(
                        sender_id=self.get_id(),
                        msgtype=Instrument.class_type,
                        subject='SEND',
                        body=cmd,
                    )
                    print(f'msg: {msg}')
                    await self.iface.message_from_parent(msg)

            # for k, iface in self.iface_map.items():
            #     for cmd in cmds:
            #         msg = Message(
            #             sender_id=self.get_id(),
            #             msgtype=Instrument.class_type,
            #             subject='SEND',
            #             body=cmd,
            #         )
            #         print(f'msg: {msg}')
            #         await iface.message_from_parent(msg)
            
            await asyncio.sleep(time_to_next(self.poll_rate))

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            id = msg.sender_id
            dt = self.parse(msg)
            print(f'dt = {dt}')
            # print(f'last_entry: {self.last_entry}')
            # if (
            #     'DATETIME' in self.last_entry and
            #     self.last_entry['DATETIME'] == entry['DATA']['DATETIME']
            # ):
            #     print(f'88888888888 skipped entry')
            #     return
            # self.last_entry['DATETIME'] = entry['DATA']['DATETIME']
            # print('entry = \n{}'.format(entry))

            # TODO: how to deal with record that crosses second bound?
            if self.current_read_cnt == len(self.current_poll_cmds):

                # entry['METADATA'] = self.get_metadata()

                entry = self.get_data_entry(dt, add_meta=False)
                # print(f'entry: {entry}')

                data = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                )
                # send data to next step(s)
                # to controller
                # data.update(subject='DATA', body=entry['DATA'])
                data.update(subject='DATA', body=entry)

                # reset read count
                self.current_read_cnt = 0 

                # await self.msg_buffer.put(data)
                # await self.to_parent_buf.put(data)
                # print(f'instrument data: {data.to_json()}')
                # await asyncio.sleep(.1)
                await self.message_to_ui(data)
                # await PlotManager.update_data(self.plot_name, data.to_json())
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
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body['DATETIME']

        line = msg.body['DATA'].rstrip()
        if len(line) == 0:
            self.current_read_cnt += 1
        else:
            parts = line.split('=')
            print(f'{parts[0]} = {parts[1]}')
            if parts[0] in self.parse_map:
                self.update_data_record(
                    dt,
                    {self.parse_map[parts[0]]: parts[1]},
                )

        # # TODO: how to limit to one/sec
        # # check for new second
        # # if data['DATETIME'] == self.last_entry['DATA']['DATETIME']:
        # #     # don't duplicate timestamp for now
        # #     return
        # # self.last_entry['DATETIME'] = data['DATETIME']

        # measurements = dict()

        # # TODO: data format issue: metadata in data or in its own field
        # #       e.g., units in data or measurement metadata?
        # # TODO: allow for "dimensions"
        # parsed = dict()
        # values = msg.body['DATA'].split('*')
        # parsed['checksum'] = values[1]
        # values = values[0].split('T')
        # parsed['tilt'] = values[1]
        # values = values[0].split('R')
        # parsed['roll'] = values[1]
        # values = values[0].split('P')
        # parsed['pitch'] = values[1]
        # values = values[0].split('C')
        # parsed['course'] = values[1]
        # # print(f'{course}, {pitch}, {roll}, {tilt}, {checksum}\n')

        # # values = msg.body['DATA'].split(',')
        # # print(f'values: {values}')
        # meas_list = [
        #     'course',
        #     'pitch',
        #     'roll',
        #     'tilt',
        #     # 'checksum',
        # ]
        controls_list = ['mcpc_power', 'mcpc_pump']

        # for name in meas_list:
        #     # TODO: use meta to convert to float, int
        #     try:
        #         val = float(parsed[name])
        #     except ValueError:
        #         val = -999
        #     measurements[name] = {
        #         'VALUE': val,
        #     }

        for name in controls_list:
            self.update_data_record(
                dt,
                {name: None},
            )

            # measurements[name] = {
            #     # 'VALUE': self.get_control_att(name, 'value'),
            #     'VALUE': None,
            # }

        # # for meas_name in self.meas_map['LIST']:
        # #     meas_def = self.meas_map['DEFINITION'][meas_name]
        # #     try:
        # #         val = float(values[meas_def['index']])
        # #     except ValueError:
        # #         val = -999
        # #     measurements[meas_name] = {
        # #         'VALUE': val,
        # #         'UNITS': meas_def['units'],
        # #         'UNCERTAINTY': meas_def['uncertainty']
        # #     }

        # data['MEASUREMENTS'] = measurements
        # entry['DATA'] = data
        # return entry
        return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return MCPC.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = MCPC.__module__
        definition['name'] = MCPC.__name__
        definition['mfg'] = 'Brechtel'
        definition['model'] = 'MCPC'
        definition['type'] = 'ParticleConcentration'
        definition['tags'] = [
            'concentration',
            'particle',
            'aerosol',
            'physics',
            'brechtel',
            'bmi'
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []

        # TODO: add interface entry for each measurement
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
            'short_name': 'conc',
            'parse_label': 'concent',
            'control': None,
        }
        y_data.append('concentration')

        process_meas = dict()
        process_meas['raw_concentration'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'raw_conc',
            'parse_label': 'rawconc',
            'control': None,
        }
        y_data.append('raw_concentration')

        process_meas['counts'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts sec-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'parse_label': 'cnt_sec',
            'control': None,
        }
        y_data.append('counts')

        process_meas['condenser_temp'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'cond_temp',
            'parse_label': 'condtmp',
            'control': None,
        }
        y_data.append('condenser_temp')

        process_meas['saturator_top_temp'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sat_top_temp',
            'parse_label': 'satttmp',
            'control': None,
        }
        y_data.append('saturator_top_temp')

        process_meas['saturator_bottom_temp'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sat_bot_temp',
            'parse_label': 'satbtmp',
            'control': None,
        }
        y_data.append('saturator_bottom_temp')

        process_meas['optics_temp'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'opt_temp',
            'parse_label': 'optctmp',
            'control': None,
        }
        y_data.append('optics_temp')

        process_meas['inlet_temp'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'parse_label': 'inlttmp',
            'control': None,
        }
        y_data.append('inlet_temp')

        process_meas['sample_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm3 min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'samp_flow',
            'parse_label': 'smpflow',
            'control': None,
        }
        y_data.append('sample_flow')

        process_meas['saturator_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm3 min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sat_flow',
            'parse_label': 'satflow',
            'control': None,
        }
        y_data.append('saturator_flow')

        process_meas['pressure'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'mbar',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'parse_label': 'pressure',
            'control': None,
        }
        y_data.append('pressure')

        process_meas['condenser_power'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'min_value': 0,
            'max_value': 250,
            'short_name': 'cond_power',
            'parse_label': 'condpwr',
            'control': None,
        }
        y_data.append('condenser_power')

        process_meas['saturator_top_power'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'min_value': 0,
            'max_value': 200,
            'short_name': 'sat_top_power',
            'parse_label': 'sattpwr',
            'control': None,
        }
        y_data.append('saturator_top_power')

        process_meas['saturator_bottom_power'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'min_value': 0,
            'max_value': 200,
            'short_name': 'sat_bot_power',
            'parse_label': 'satbpwr',
            'control': None,
        }
        y_data.append('saturator_bottom_power')

        process_meas['optics_power'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'min_value': 0,
            'max_value': 200,
            'parse_label': 'optcpwr',
            'control': None,
        }
        y_data.append('optics_power')

        process_meas['saturator_pump_power'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'min_value': 0,
            'max_value': 200,
            'short_name': 'sat_pump_power',
            'parse_label': 'satfpwr',
            'control': None,
        }
        y_data.append('saturator_pump_power')

        process_meas['fill_count'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'parse_label': 'fillcnt',
            'control': None,
        }
        y_data.append('fill_count')

        process_meas['error'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'parse_label': 'err_num',
            'control': None,
        }
        y_data.append('error')

        # TODO: add settings controls
        controls = dict()
        controls['mcpc_power'] = {
            'data_type': 'NUMERIC',
            # units are tied to parameter this controls
            'units': 'counts',
            'allowed_range': [0, 1],
            'default_value': 1,
            'label': 'MCPC Power',
            'parse_label': 'mcpcpwr',
            'control_group': 'Operation',
        }
        # y_data.append('inlet_temperature_sp')

        # TODO: add settings controls
        controls['mcpc_pump'] = {
            'data_type': 'NUMERIC',
            # units are tied to parameter this controls
            'units': 'counts',
            'allowed_range': [0, 1],
            'default_value': 1,
            'label': 'MCPC Pump',
            'parse_label': 'mcpcpmp',
            'control_group': 'Operation',
        }

        measurement_config['primary'] = primary_meas
        measurement_config['process'] = process_meas
        measurement_config['controls'] = controls
        definition['measurement_config'] = measurement_config

        plot_config = dict()
        time_series1d = dict()

        time_series1d['y_data'] = y_data
        time_series1d['default_y_data'] = ['concentration']
        plot_config['TimeSeries1D'] = time_series1d
        definition['plot_config'] = plot_config

        return {'DEFINITION': definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition
