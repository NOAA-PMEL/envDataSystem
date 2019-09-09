import json
from daq.instrument.instrument import Instrument
from daq.instrument.contrib.brechtel.brechtel import BrechtelInstrument
from data.message import Message
from daq.daq import DAQ
import asyncio
from utilities.util import time_to_next
from daq.interface.interface import Interface
from plots.plots import PlotManager
import math


class MSEMS(BrechtelInstrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(MSEMS, self).__init__(config, **kwargs)

        self.name = 'MSEMS'
        self.model = 'MSEMS'
        self.tag_list = [
            'concentration',
            'aerosol',
            'physics',
            'sizing',
            'size distribution',
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

        self.scan_start_param = 'date'
        self.scan_stop_param = 'mcpc_errs'
        self.scan_ready = False
        self.current_size_dist = []
        self.scan_state = 999
        self.scan_run_state = 'STOPPED'

        # this instrument appears to work with readline
        # self.iface_options = {
        #     'read_method': 'readuntil',
        #     'read_terminator': '\r',
        # }
        self.setup()

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

        self.mode = 'scanning'
        # self.clean_data_record()
        if self.is_polled:
            self.polling_task = asyncio.ensure_future(self.poll_loop())

        self.current_read_cnt = 0

        # TODO: send start cmd to instrument
        if self.mode == 'mono':
            pass
        elif self.mode == 'scanning':
            asyncio.ensure_future(self.start_scanning())

    async def start_scanning(self):
        if self.iface:
            self.current_read_cnt = 0
            cmd = 'sems_mode=2\n'
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
                subject='SEND',
                body=cmd,
            )
            print(f'msg: {msg}')
            await self.iface.message_from_parent(msg)
            self.scan_state = 'RUNNING'

    async def stop_scanning(self):
        if self.iface:
            self.current_read_cnt = 0
            cmd = 'sems_mode=0\n'
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
                subject='SEND',
                body=cmd,
            )
            print(f'msg: {self.iface}, {msg.to_json()}')
            # self.scan_run_state = 'STOPPING'
            await self.iface.message_from_parent(msg)
            # while self.scan_state > 0:
            #     await asyncio.sleep(.1)
            # self.scan_run_state = 'STOPPED'

    def stop(self, cmd=None):
        if self.polling_task:
            self.polling_task.cancel()

        if self.mode == 'mono':
            pass
        elif self.mode == 'scanning':
            # self.loop.run_until_complete(
            #     asyncio.wait(
            #         asyncio.ensure_future(
            #             self.stop_scanning()
            #         )
            #     )
            # )
            asyncio.ensure_future(
                self.stop_scanning()
            )
        # TODO: add delay while scanning is stopped
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

            # await asyncio.sleep(time_to_next(self.poll_rate))

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            id = msg.sender_id
            dt = self.parse(msg)
            # print(f'dt = {dt}')
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
            # if self.current_read_cnt == len(self.current_poll_cmds):
            if self.mode == 'scanning' and self.scan_ready:

                print(f'dt = {dt}')
                # entry['METADATA'] = self.get_metadata()
                self.update_data_record(
                    dt,
                    {'sheath_flow_sp': 2.5},
                )
                self.update_data_record(
                    dt,
                    {'number_bins': 30},
                )
                self.update_data_record(
                    dt,
                    {'bin_time': 1},
                )

                if len(self.current_size_dist) == 30:
                    self.update_data_record(
                        dt,
                        {'size_distribution': self.current_size_dist},
                    )

                    # calculate diameters
                    min_dp = 10
                    param = self.get_data_record_param(
                        dt,
                        'actual_max_dp'
                    )
                    if not param:
                        max_dp = 300
                    else:
                        max_dp = float(param)
                    dlogdp = math.pow(
                        10,
                        math.log10(max_dp/min_dp)/(30-1)
                    )
                    # dlogdp = dlogdp / (30-1)
                    diam = []
                    diam.append(10)
                    for x in range(1, 30):
                        dp = round(diam[x-1] * dlogdp, 2)
                        diam.append(dp)

                    self.update_data_record(
                        dt,
                        {'diameter': diam},
                    )

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
                self.scan_ready = False

                # await self.msg_buffer.put(data)
                # await self.to_parent_buf.put(data)
                print(f'999999999999msems data: {data.to_json()}')
                # await asyncio.sleep(.1)
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
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body['DATETIME']

        line = msg.body['DATA'].rstrip()
        # if len(line) == 0:
        #     self.current_read_cnt += 1
        # else:
        parts = line.split('=')
        if len(parts) < 2:
            return dt

        # self.scan_state = 999
        # if self.scan_run_state == 'STOPPING':
        #     if parts[0] == 'scan_state':
        #         self.scan_state = int(parts[1])

        # print(f'77777777777777{parts[0]} = {parts[1]}')
        if parts[0] in self.parse_map:
            self.update_data_record(
                dt,
                {self.parse_map[parts[0]]: parts[1]},
            )
            if self.scan_stop_param == parts[0]:
                self.scan_ready = True
            elif self.scan_start_param == parts[0]:
                self.current_size_dist.clear()
        elif parts[0].find('bin') >= 0:
            self.current_size_dist.append(
                float(parts[1])
            )
        # # TODO: how to limit to one/sec
        # # check for new second
        # # if data['DATETIME'] == self.last_entry['DATA']['DATETIME']:
        # #     # don't duplicate timestamp for now
        # #     return
        # # self.last_entry['DATETIME'] = data['DATETIME']

        # measurements = dict()

       # controls_list = ['mcpc_power', 'mcpc_pump']

        # for name in controls_list:
        #     self.update_data_record(
        #         dt,
        #         {name: None},
        #     )

        return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return MSEMS.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = MSEMS.__module__
        definition['name'] = MSEMS.__name__
        definition['mfg'] = 'Brechtel'
        definition['model'] = 'MSEMS'
        definition['type'] = 'SizeDistribution'
        definition['tags'] = [
            'concentration',
            'particle',
            'aerosol',
            'physics',
            'brechtel',
            'bmi',
            'sizing',
            'size distribution'
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []
        dist_data = []

        # TODO: add interface entry for each measurement
        primary_meas_2d = dict()
        primary_meas_2d['size_distribution'] = {
            'dimensions': {
                'axes': ['TIME', 'diameter'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'nm'],
            },
            'units': 'cm-3',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'size_dist',
            'parse_label': 'bin',
            'control': None,
        }
        dist_data.append('size_distribution')

        primary_meas_2d['diameter'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'nm'],
            },
            'units': 'nm',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'dp',
            'parse_label': 'diameter',
            'control': None,
        }
        dist_data.append('diameter')

        process_meas = dict()
        process_meas['sems_date'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'date',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sems_date',
            'parse_label': 'date',
            'control': None,
        }
        # y_data.append('sems_date')

        process_meas['sems_time'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'dateTime',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'parse_label': 'time',
            'control': None,
        }
        # y_data.append('counts')

        process_meas['scan_direction'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'scan_dir',
            'parse_label': 'scan_direction',
            'control': None,
        }
        # y_data.append('condenser_temp')

        process_meas['actual_max_dp'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'nm',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'max_dp',
            'parse_label': 'actual_max_dia',
            'control': None,
        }
        y_data.append('actual_max_dp')

        process_meas['max_volts'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'volts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('max_volts')

        process_meas['min_volts'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'volts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'opt_temp',
            'parse_label': 'scan_min_volts',
            'control': None,
        }
        y_data.append('min_volts')

        process_meas['sheath_flow_avg'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sheath_avg',
            'parse_label': 'sheath_flw_avg',
            'control': None,
        }
        y_data.append('sheath_flow_avg')

        process_meas['sheath_flow_sd'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sheath_sd',
            'parse_label': 'sheath_flw_stdev',
            'control': None,
        }
        y_data.append('sheath_flow_sd')

        process_meas['sample_flow_avg'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sample_avg',
            'parse_label': 'mcpc_smpf_avg',
            'control': None,
        }
        y_data.append('sample_flow_avg')

        process_meas['sample_flow_sd'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'sample_sd',
            'parse_label': 'mcpc_smpf_stdev',
            'control': None,
        }
        y_data.append('sample_flow_sd')

        process_meas['pressure_avg'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'mbar',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'press_avg',
            'parse_label': 'press_avg',
            'control': None,
        }
        y_data.append('pressure_avg')

        process_meas['pressure_sd'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'mbar',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'press_sd',
            'parse_label': 'press_stdev',
            'control': None,
        }
        y_data.append('pressure_sd')

        process_meas['temperature_avg'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'temp_avg',
            'parse_label': 'temp_avg',
            'control': None,
        }
        y_data.append('temperature_avg')

        process_meas['temperature_sd'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'temp_sd',
            'parse_label': 'temp_stdev',
            'control': None,
        }
        y_data.append('temperature_sd')

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
            'parse_label': 'sems_errs',
            'control': None,
        }
        y_data.append('error')

        process_meas['mcpc_sample_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm3 min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'mcpc_samp_flow',
            'parse_label': 'mcpc_smpf',
            'control': None,
        }
        y_data.append('mcpc_sample_flow')

        process_meas['mcpc_saturator_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'cm3 min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'mcpc_sat_flow',
            'parse_label': 'mcpc_satf',
            'control': None,
        }
        y_data.append('mcpc_saturator_flow')

        process_meas['mcpc_condenser_temp'] = {
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
            'short_name': 'mcpc_cond_temp',
            'parse_label': 'mcpc_cndt',
            'control': None,
        }
        y_data.append('mcpc_condenser_temp')

        process_meas['mcpc_error'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'parse_label': 'mcpc_errs',
            'control': None,
        }
        y_data.append('mcpc_error')

        # TODO: add settings controls
        controls = dict()
        controls['sheath_flow_sp'] = {
            'data_type': 'NUMERIC',
            # units are tied to parameter this controls
            'units': 'liters min-1',
            'allowed_range': [0, 4],
            'default_value': 2.5,
            'label': 'Sheath Flow',
            'parse_label': 'sheath_sp',
            'control_group': 'Operation',
        }
        y_data.append('sheath_flow_sp')

        # TODO: add settings controls
        controls['number_bins'] = {
            'data_type': 'NUMERIC',
            # units are tied to parameter this controls
            'units': 'counts',
            'allowed_range': [0, 100],
            'default_value': 30,
            'label': 'Number of bins',
            'parse_label': 'num_bins',
            'control_group': 'Operation',
        }
        controls['bin_time'] = {
            'data_type': 'NUMERIC',
            # units are tied to parameter this controls
            'units': 'sec',
            'allowed_range': [0.25, 60],
            'default_value': 1,
            'label': 'Seconds per bin',
            'parse_label': 'bin_time',
            'control_group': 'Operation',
        }

        measurement_config['primary'] = primary_meas_2d
        # measurement_config['primary'] = primary_meas
        measurement_config['process'] = process_meas
        measurement_config['controls'] = controls
        definition['measurement_config'] = measurement_config

        plot_config = dict()
        time_series1d = dict()
        size_dist = dict()

        size_dist['dist_data'] = dist_data
        size_dist['default_dist_data'] = ['size_distribution']
        time_series1d['y_data'] = y_data
        time_series1d['default_y_data'] = ['concentration']
        plot_config['TimeSeries1D'] = time_series1d
        plot_config['SizeDistribution'] = size_dist
        definition['plot_config'] = plot_config

        return {'DEFINITION': definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition
