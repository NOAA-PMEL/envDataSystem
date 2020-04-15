import json
from daq.instrument.instrument import Instrument
from data.message import Message
from daq.daq import DAQ
import asyncio
from utilities.util import time_to_next, dt_to_string
from daq.interface.interface import Interface
import math
import numpy as np


class HandixInstrument(Instrument):

    INSTANTIABLE = False

    def __init__(self, config, **kwargs):
        super(HandixInstrument, self).__init__(config, **kwargs)

        self.mfg = 'Handix'

    def setup(self):
        super().setup()

        # TODO: add properties get/set to interface for
        #       things like readmethod


class POPS(HandixInstrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(POPS, self).__init__(config, **kwargs)

        self.name = 'POPS'
        self.type = 'POPS'
        self.model = 'POPS'
        self.tag_list = [
            'concentration',
            'aerosol',
            'physics',
            'sizing',
            'size distribution',
            'coarse mode'
        ]

        # self.meas_map = dict()
        # self.meas_map = [
        #     'concentration',
        #     'raw_concentration'
        # ]

        self.iface_meas_map = None
        self.polling_task = None
        # self.current_poll_cmds = ['read\n', 'raw=2\n']
        # self.current_read_cnt = 0

        self.mode = 'scanning'

        self.scan_length = 120
        if 'scan_length' in config['DESCRIPTION']:
            self.scan_length = config['DESCRIPTION']['scan_length']

        # override how often metadata is sent
        self.include_metadata_interval = 300

        # this instrument appears to work with readline
        # self.iface_options = {
        #     'read_method': 'readuntil',
        #     'read_terminator': '\r',
        # }

        self.log_min = 1.6
        self.log_max = 4.817
        self.num_bins = 16
        self.scan_ready = False
        self.setup()

        self.lower_dp_bnd = [
            0.1226, 0.1329, 0.1448, 0.1588, 0.1761, 0.1977, 0.2251, 0.304,
            0.4181, 0.5001, 0.6202, 0.9295, 1.2742, 1.5913, 2.0666, 2.6485
        ]
        self.uppder_dp_bnd = [
            0.1329, 0.1448, 0.1588, 0.1761, 0.1977, 0.2251, 0.304, 0.4181,
            0.5001, 0.6202, 0.9295, 1.2742, 1.5913, 2.0666, 2.6485, 3.4129
        ]

    # def get_datafile_config(self):
    #     config = super().get_datafile_config()
    #     config['save_interval'] = 0
    #     return config

    def setup(self):
        super().setup()

        # only has one interface
        self.iface = next(iter(self.iface_map.values()))

        # default coms: usb
        #   230400 8-N-1

        # TODO: this will depend on mode
        # add polling loop
        # if polled:
        self.is_polled = False
        # self.poll_rate = 300  # every 5 minutes
        # self.overhead = 15 # seconds
        # self.poll_rate = 10  # every 5 minutes
        self.poll_rate = self.scan_length
        self.overhead = 15  # seconds
        # self.overhead = 1  # seconds

        # create parse_map and empty data_record
        self.parse_map = dict()
        # self.data_record_template = dict()

        definition = self.get_definition_instance()
        meas_config = definition['DEFINITION']['measurement_config']
        for msetsname, mset in meas_config.items():
            # self.data_record_template[msetname] = dict()
            for name, meas in mset.items():
                # parse_label = meas['parse_label']
                # self.parse_map[parse_label] = name
                # self.data_record_template[msetsname][name] = None
                self.data_record_template[name] = {'VALUE': None}

    def start(self, cmd=None):
        super().start()

        self.mode = 'scanning'
        # self.clean_data_record()
        # if self.is_polled:
        #     self.polling_task = asyncio.ensure_future(self.poll_loop())

        self.current_read_cnt = 0

        # TODO: send start cmd to instrument
        # if self.mode == 'mono':
        #     pass
        # elif self.mode == 'scanning':
        #     asyncio.ensure_future(self.start_scanning())

    # async def start_scanning(self):

    #     print(f'start scanning')

    #     self.scan_ready = False

    #     if self.iface:
    #         for cmd in cmd_list:
    #             self.current_read_cnt = 0
    #             # cmd = 'sems_mode=2\n'
    #             msg = Message(
    #                 sender_id=self.get_id(),
    #                 msgtype=Instrument.class_type,
    #                 subject='SEND',
    #                 body=cmd,
    #             )
    #             # print(f'msg: {msg}')
    #             await self.iface.message_from_parent(msg)
    #             # TODO: wait for return OK
    #             await asyncio.sleep(.5)  # give the inst a sec
    #             self.scan_state = 'RUNNING'
    #         if self.is_polled:
    #             self.polling_task = asyncio.ensure_future(self.poll_loop())

    # async def stop_scanning(self):

    #     print(f'stop scanning')

    #     # clear
    #     clear = 'C\r'

    #     # Go
    #     halt = 'H\r'

    #     # unpolled start
    #     unpolled_stop = 'U0\r'

    #     cmd_list = [halt, clear, unpolled_stop]

    #     self.scan_ready = False

    #     if self.iface:
    #         for cmd in cmd_list:
    #             self.current_read_cnt = 0
    #             # cmd = 'sems_mode=0\n'
    #             msg = Message(
    #                 sender_id=self.get_id(),
    #                 msgtype=Instrument.class_type,
    #                 subject='SEND',
    #                 body=cmd,
    #             )
    #             print(f'msg: {self.iface}, {msg.to_json()}')
    #             # self.scan_run_state = 'STOPPING'
    #             await self.iface.message_from_parent(msg)
    #             await asyncio.sleep(.25)
    #             # while self.scan_state > 0:
    #             #     await asyncio.sleep(.1)
    #             # self.scan_run_state = 'STOPPED'

    def stop(self, cmd=None):
        # if self.polling_task:
        #     self.polling_task.cancel()

        # if self.mode == 'mono':
        #     pass
        # elif self.mode == 'scanning':
        #     # self.loop.run_until_complete(
        #     #     asyncio.wait(
        #     #         asyncio.ensure_future(
        #     #             self.stop_scanning()
        #     #         )
        #     #     )
        #     # )
        #     asyncio.ensure_future(
        #         self.stop_scanning()
        #     )
        # TODO: add delay while scanning is stopped
        super().stop()

    # async def poll_loop(self):
    #     print(f'polling loop started')

    #     scan_time = self.poll_rate
    #     sample_time = self.poll_rate - self.overhead
    #     start_sample = f'S{sample_time}\r'
    #     clear = 'C\r'
    #     cmds = [clear, start_sample]

    #     # wait for start of next scan period
    #     print(f'Starting scan in {time_to_next(scan_time)} seconds')
    #     await asyncio.sleep(time_to_next(scan_time))

    #     while True:
    #         # TODO: implement current_poll_cmds
    #         # cmds = self.current_poll_cmds

    #         # print(f'cmds: {cmds}')
    #         # cmds = ['read\n']
    #         self.scan_start_time = dt_to_string()
    #         self.scan_duration = self.poll_rate
    #         self.scan_ready = False

    #         if self.iface:
    #             # self.current_read_cnt = 0
    #             for cmd in cmds:
    #                 msg = Message(
    #                     sender_id=self.get_id(),
    #                     msgtype=Instrument.class_type,
    #                     subject='SEND',
    #                     body=cmd,
    #                 )
    #                 # print(f'msg: {msg.body}')
    #                 await self.iface.message_from_parent(msg)
    #                 await asyncio.sleep(.25)

    #         # for k, iface in self.iface_map.items():
    #         #     for cmd in cmds:
    #         #         msg = Message(
    #         #             sender_id=self.get_id(),
    #         #             msgtype=Instrument.class_type,
    #         #             subject='SEND',
    #         #             body=cmd,
    #         #         )
    #         #         print(f'msg: {msg}')
    #         #         await iface.message_from_parent(msg)

    #         await asyncio.sleep(time_to_next(self.poll_rate))

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            # print(f'aps scan: {msg.to_json()}')

            id = msg.sender_id

            dt = self.parse(msg)

            if self.scan_ready:
                
                # calc dp
                dp = []
                for low, hi in zip(self.lower_dp_bnd, self.uppder_dp_bnd):
                    dp.append(round(math.sqrt(low*hi), 4))

                self.update_data_record(
                    dt,
                    {'diameter_um': dp},
                )

                # calc bin_conc
                conc = []
                cnts = self.get_data_record_param(dt, 'bin_counts')
                flow = self.get_data_record_param(dt, 'sample_flow')
                if cnts and flow:
                    for n in cnts:
                        conc.append(round(n/flow, 4))

                self.update_data_record(
                    dt,
                    {'bin_concentration': conc},
                )

                entry = self.get_data_entry(dt)
                # print(f'entry: {entry}')

                self.scan_ready = False

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
                # print(f'999999999999msems data: {data.to_json()}')
                # await asyncio.sleep(.1)
                await self.message_to_ui(data)
                await self.to_parent_buf.put(data)
                # await PlotManager.update_data(self.plot_name, data.to_json())
                if self.datafile:
                    await self.datafile.write_message(data)
            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)
        elif type == 'FromUI':
            if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
                # print(f'msg: {msg.body}')
                self.send_status()

            elif msg.subject == 'CONTROLS' and msg.body['purpose'] == 'REQUEST':
                # print(f'msg: {msg.body}')
                await self.set_control(msg.body['control'], msg.body['value'])
            elif msg.subject == 'RUNCONTROLS' and msg.body['purpose'] == 'REQUEST':
                # print(f'msg: {msg.body}')
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
        # print(f'msg[DATETIME]: {dt}')

        line = msg.body['DATA'].strip()
        # print(f'line = {line}')

        # DateTime	PartCt	PartCon	BL	STD	P	POPS_Flow	LDTemp	LD_Mon	Temp	b0	b1	b2	b3

        params = line.split(',')

        if (params[0] == 'POPS'):

            labels = [
                # 'pops_datetime',
                'integral_counts',
                'integral_concentration',
                'det_baseline',
                'det_baseline_sd',
                'pressure',
                'sample_flow',
                'temperature_laser',
                'monitor_laser',
                'temperature_board',
            ]

            self.update_data_record(
                dt,
                {'pops_datetime': params[1]}
            )

            for i, label in enumerate(labels):

                try:
                    val = float(params[i+2])
                    if math.isnan(val):
                        val = None
                except ValueError:
                    val = None

                self.update_data_record(
                    dt,
                    {label: val}
                )
            start_i = len(labels) + 2
            stop_i = start_i + self.num_bins

            bin_counts = []
            for i in range(start_i, stop_i):
                cnt = float(params[i])
                bin_counts.append(cnt)
            self.update_data_record(
                dt,
                {'bin_counts': bin_counts}
            )

            self.scan_ready = True

        return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return POPS.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = POPS.__module__
        definition['name'] = POPS.__name__
        definition['mfg'] = 'Handix'
        definition['model'] = 'POPS'
        definition['type'] = 'SizeDistribution'
        definition['tags'] = [
            'concentration',
            'particle',
            'aerosol',
            'physics',
            'handix',
            'coarse mode',
            'sizing',
            'size distribution'
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []
        dist_data = []

        # TODO: add interface entry for each measurement
        primary_meas_2d = dict()
        primary_meas_2d['bin_concentration'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'bin_conc',
            # 'parse_label': 'bin',
            'control': None,
            'axes': {
                # 'TIME', 'datetime',
                'DIAMETER': 'diameter_um',
            }
        }
        dist_data.append('bin_concentration')

        primary_meas_2d['diameter_um'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'um',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'dp',
            # 'parse_label': 'diameter',
            'control': None,
        }
        dist_data.append('diameter_um')

        raw_2d = dict()
        raw_2d['bin_counts'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'bin_count',
            # 'parse_label': 'bin',
            'control': None,
            'axes': {
                # 'TIME', 'datetime',
                'DIAMETER': 'diameter_um',
            }
        }
        dist_data.append('bin_counts')

        primary_meas = dict()
        primary_meas['pops_datetime'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'dateTime',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'calculated',
            'data_type': 'NUMERIC',
            # 'short_name': 'int_conc',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        # y_data.append('pops_datetime')

        primary_meas['integral_concentration'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'calculated',
            'data_type': 'NUMERIC',
            'short_name': 'int_conc',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('integral_concentration')

        primary_meas['integral_counts'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 's-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'calculated',
            'data_type': 'NUMERIC',
            'short_name': 'int_counts',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('integral_counts')

        env_meas = dict()
        env_meas['pressure'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'hPa',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('pressure')

        env_meas['temperature_board'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('temperature_board')

        process_meas = dict()
        process_meas['sample_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm3 s-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('sample_flow')

        raw_meas = dict()
        raw_meas['det_baseline'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('det_baseline')

        raw_meas['det_baseline_sd'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('det_baseline_sd')

        raw_meas['temperature_laser'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degc',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('temperature_laser')

        raw_meas['monitor_laser'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('monitor_laser')

        measurement_config['primary_2d'] = primary_meas_2d
        measurement_config['raw_2d'] = raw_2d
        measurement_config['primary'] = primary_meas
        measurement_config['process'] = process_meas
        measurement_config['env'] = env_meas
        measurement_config['raw'] = raw_meas

        # measurement_config['controls'] = controls

        definition['measurement_config'] = measurement_config

        plot_config = dict()

        size_dist = dict()
        size_dist['app_type'] = 'SizeDistribution'
        size_dist['y_data'] = dist_data,
        size_dist['default_y_data'] = ['bin_concentration']
        source_map = {
            'default': {
                'y_data': {
                    'default': dist_data
                },
                'default_y_data': ['bin_concentration']
            },
        }
        size_dist['source_map'] = source_map

        time_series1d = dict()
        time_series1d['app_type'] = 'TimeSeries1D'
        time_series1d['y_data'] = y_data
        time_series1d['default_y_data'] = ['integral_concentration']
        source_map = {
            'default': {
                'y_data': {
                    'default': y_data
                },
                'default_y_data': ['integral_concentration']
            },
        }
        time_series1d['source_map'] = source_map

        plot_config['plots'] = dict()
        plot_config['plots']['raw_size_dist'] = size_dist
        plot_config['plots']['main_ts1d'] = time_series1d
        definition['plot_config'] = plot_config

        return {'DEFINITION': definition}
