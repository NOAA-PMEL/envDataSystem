# import json
from daq.instrument.instrument import Instrument
from shared.data.message import Message
# from daq.daq import DAQ
import asyncio
from shared.utilities.util import time_to_next, dt_to_string
from daq.interface.interface import Interface
import math
import numpy as np


class TSIInstrument(Instrument):

    INSTANTIABLE = False

    def __init__(self, config, **kwargs):
        super(TSIInstrument, self).__init__(config, **kwargs)

        self.mfg = 'TSI'

    def setup(self):
        super().setup()

        # TODO: add properties get/set to interface for
        #       things like readmethod


class APS3320(TSIInstrument):

    '''
    TSI APS Model 3320: what follows is code from c++ program

    static const JSize k3320DumpChannels = 		80; 
    static const JSize k3320DpChannels = 		52; 
    static const JFloat k3320logStep = 			0.0337;

    static const JFloat k3320NomSampleFlow = 	1.0;  // lpm
    static const JFloat k3320NomSheathFlow = 	4.0;  // lpm
    static const JFloat k3320NomTotalFlow = 	5.0;  // lpm

    JFloat tsi3320Dp[k3320DpChannels] = 
                        {.50468,.54215,
                            .58166,.62506,.67305,.72353,.7775,
                            .83546,.89791,.96488,1.0368,1.1143,
                            1.1972,1.2867,1.3826,1.4855,1.5965,
                            1.7154,1.8433 ,1.9812,2.1291,2.2875,
                            2.4579,2.6413,2.8387,3.0505,3.2779,
                            3.5227,3.7856,4.0679,4.3717,4.698,
                            5.0482,5.4245,5.8292,6.2644,6.7317,
                            7.2338,7.7735,8.3536,8.9772,9.6468,
                            10.366,11.14,11.971,12.864,13.824,
                            14.855,15.963,17.154,18.435,19.81
                            };


    // communication constants
    static const JCharacter* kTSI_OK = "OK";
    static const JCharacter* kTSI_ERROR = "ERROR";
    static const JSize kMaxAttempts = 5;

    static const JCharacter* kTSI_GoCmd = 						"G";
    static const JCharacter* kTSI_DumpCmd = 					"D";
    static const JCharacter* kTSI_HaltCmd = 					"H";
    static const JCharacter* kTSI_ClearCmd = 					"C";

    static const JCharacter* kTSI3320_SampleFlowCmd = 			"RQA";
    static const JCharacter* kTSI3320_SheathFlowCmd = 			"RQS";
    static const JCharacter* kTSI3320_TotalFlowCmd = 			"RQT";

    static const JCharacter* kTSI3320_AccumulatorCmd = 			"R";
    static const JCharacter* kTSI3320_AccumulatorRecordACmd = 	"UA";
    static const JCharacter* kTSI3320_SSAccumulatorRecordBCmd = "UB";
    static const JCharacter* kTSI3320_CorrelatedRecordCCmd = 	"UC";
    static const JCharacter* kTSI3320_TOFRecordDCmd = 			"UD";
    static const JCharacter* kTSI3320_SSRecordSCmd = 			"US";
    static const JCharacter* kTSI3320_AuxialliaryRecordYCmd = 	"UY";

    static const JCharacter* kTSI3320_BoxTempCmd =	 			"RTB";
    static const JCharacter* kTSI3320_DetectorTempCmd =	 		"RTD";
    static const JCharacter* kTSI3320_InletTempCmd =	 		"RI";
    static const JCharacter* kTSI3320_InletRHCmd =	 			"RI";

    static const JCharacter* kTSI3320_LaserPowerCmd =	 		"RL";
    static const JCharacter* kTSI3320_StatusFlagsCmd =	 		"RF";


    static const JCharacter kCR = 0x0d;
    static const JCharacter kNL = 0x0a;
    '''

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(APS3320, self).__init__(config, **kwargs)

        self.name = 'APS3320'
        self.type = 'APS'
        self.model = '3320'
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

        self.scan_start_param = 'date'
        self.scan_stop_param = 'mcpc_errs'
        self.scan_ready = False
        self.current_size_dist = []
        self.scan_state = 999
        self.scan_run_state = 'STOPPED'

        self.scan_length = 120
        if 'scan_length' in config['DESCRIPTION']:
            self.scan_length = config['DESCRIPTION']['scan_length']

        # override how often metadata is sent
        self.include_metadata_interval = 300

        # this instrument appears to work with readline
        self.iface_options = {
            'read_method': 'readuntil',
            'read_terminator': '\r',
        }

        self.nominal_sample_flow = 1.0
        self.nominal_sheath_flow = 4.0

        self.diameters_um = [
            .50468, .54215,
            .58166, .62506, .67305, .72353, .7775,
            .83546, .89791, .96488, 1.0368, 1.1143,
            1.1972, 1.2867, 1.3826, 1.4855, 1.5965,
            1.7154, 1.8433, 1.9812, 2.1291, 2.2875,
            2.4579, 2.6413, 2.8387, 3.0505, 3.2779,
            3.5227, 3.7856, 4.0679, 4.3717, 4.698,
            5.0482, 5.4245, 5.8292, 6.2644, 6.7317,
            7.2338, 7.7735, 8.3536, 8.9772, 9.6468,
            10.366, 11.14, 11.971, 12.864, 13.824,
            14.855, 15.963, 17.154, 18.435, 19.81
        ]
        self.first_good_diameter = 0.89791

        self.setup()

    def get_datafile_config(self):
        config = super().get_datafile_config()
        config['save_interval'] = 0
        return config

    def setup(self):
        super().setup()

        # only has one interface
        self.iface = next(iter(self.iface_map.values()))

        # default coms: usb
        #   230400 8-N-1

        # TODO: this will depend on mode
        # add polling loop
        # if polled:
        self.is_polled = True
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
        if self.mode == 'mono':
            pass
        elif self.mode == 'scanning':
            asyncio.ensure_future(self.start_scanning())

    async def start_scanning(self):

        print(f'start scanning')
        # set unpolled report time to high number
        stu = f'STU65500\r'

        # clear
        clear = 'C\r'

        # Go
        go = 'G\r'

        # unpolled start
        unpolled_start = 'U1\r'

        cmd_list = [clear, stu, clear, go, unpolled_start]

        self.scan_ready = False

        if self.iface:
            for cmd in cmd_list:
                self.current_read_cnt = 0
                # cmd = 'sems_mode=2\n'
                msg = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject='SEND',
                    body=cmd,
                )
                # print(f'msg: {msg}')
                await self.iface.message_from_parent(msg)
                # TODO: wait for return OK
                await asyncio.sleep(.5)  # give the inst a sec
                self.scan_state = 'RUNNING'
            if self.is_polled:
                self.polling_task = asyncio.ensure_future(self.poll_loop())

    async def stop_scanning(self):

        print(f'stop scanning')

        # clear
        clear = 'C\r'

        # Go
        halt = 'H\r'

        # unpolled start
        unpolled_stop = 'U0\r'

        cmd_list = [halt, clear, unpolled_stop]

        self.scan_ready = False

        if self.iface:
            for cmd in cmd_list:
                self.current_read_cnt = 0
                # cmd = 'sems_mode=0\n'
                msg = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject='SEND',
                    body=cmd,
                )
                print(f'msg: {self.iface}, {msg.to_json()}')
                # self.scan_run_state = 'STOPPING'
                await self.iface.message_from_parent(msg)
                await asyncio.sleep(.25)
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

        scan_time = self.poll_rate
        sample_time = self.poll_rate - self.overhead
        start_sample = f'S{sample_time}\r'
        clear = 'C\r'
        cmds = [clear, start_sample]

        # wait for start of next scan period
        print(f'Starting scan in {time_to_next(scan_time)} seconds')
        await asyncio.sleep(time_to_next(scan_time))

        while True:
            # TODO: implement current_poll_cmds
            # cmds = self.current_poll_cmds

            # print(f'cmds: {cmds}')
            # cmds = ['read\n']
            self.scan_start_time = dt_to_string()
            self.scan_duration = self.poll_rate
            self.scan_ready = False

            if self.iface:
                # self.current_read_cnt = 0
                for cmd in cmds:
                    msg = Message(
                        sender_id=self.get_id(),
                        msgtype=Instrument.class_type,
                        subject='SEND',
                        body=cmd,
                    )
                    # print(f'msg: {msg.body}')
                    await self.iface.message_from_parent(msg)
                    await asyncio.sleep(.25)

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
            # print(f'aps scan: {msg.to_json()}')

            id = msg.sender_id

            # print(f'OK? {msg["BODY"]["DATA"]}')
            # if msg['BODY']['DATA'] == 'OK\r':
            #     print(f'OK')
            #     return

            dt = self.parse(msg)
            # return
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
                # if self.scan_ready:

                print(f'scan ready...dt = {dt}')
                self.update_data_record(
                    dt,
                    {'diameter_um': self.diameters_um},
                )

                entry = self.get_data_entry(dt)
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

                # print(f'999999999999 aps data: {data.to_json()}')
                await self.message_to_ui(data)
                await self.to_parent_buf.put(data)
                # await PlotManager.update_data(self.plot_name, data.to_json())
                if self.datafile:
                    await self.datafile.write_message(data)
            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)
        elif type == 'FromUI':
            if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
                print(f'msg: {msg.body}')
                self.send_status()

            elif (
                msg.subject == 'CONTROLS' and
                msg.body['purpose'] == 'REQUEST'
            ):
                print(f'msg: {msg.body}')
                await self.set_control(
                    msg.body['control'], msg.body['value']
                )

            elif (
                msg.subject == 'RUNCONTROLS' and
                msg.body['purpose'] == 'REQUEST'
            ):
                print(f'msg: {msg.body}')
                await self.handle_control_action(
                    msg.body['control'], msg.body['value']
                )
                # await self.set_control(msg.body['control'], msg.body['value'])

        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        if control and value is not None:
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
        print(f'parse: {msg.to_json()}')
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body['DATETIME']
        print(f'msg[DATETIME]: {dt}')

        line = msg.body['DATA'].rstrip()
        print(f'line = {line}')
        if ('OK' in line):
            return

        params = line.split(',')
        if params[1] == 'D':
            checksum = params[0]
            mode = params[2]
            status_flag = params[4]
            try:
                sample_time = float(params[5])
            except ValueError:
                sample_time = 0

            first_channel = 11
            data_channels = len(params)-10
            num_channel = 52

            # TODO: these are counts, not conc
            cnts = []
            for i in range(0, 52):
                cnts.append(0)

            for i in range(first_channel, len(params)):
                try:
                    n = float(params[i])
                    if n < 0:
                        n = 0
                    cnts[i-first_channel] = n
                except ValueError:
                    cnts[i-first_channel] = 0

            self.update_data_record(
                self.scan_start_time,
                {'bin_counts': cnts}
            )

            conc = []
            for n in cnts:
                if sample_time > 0:
                    # convert counts(s-1) to conc (cm-3)
                    # dn = n * (60 * self.nominal_sample_flow / 1000)
                    dn = (n / sample_time) / 16.67
                    conc.append(round(dn, 3))

            self.update_data_record(
                self.scan_start_time,
                {'bin_concentration': conc}
            )

            self.update_data_record(
                self.scan_start_time,
                {'sample_calc_time': sample_time}
            )

            # integrate concentration
            intN = 0
            for i in range(0, num_channel):
                if self.diameters_um[i] > self.first_good_diameter:
                    intN += conc[i]

            self.update_data_record(
                self.scan_start_time,
                {'integral_concentration': round(intN, 3)}
            )

            # populate these for now
            self.update_data_record(
                self.scan_start_time,
                {'sheath_flow': self.nominal_sheath_flow}
            )

            self.update_data_record(
                self.scan_start_time,
                {'sample_flow': self.nominal_sample_flow}
            )

            self.update_data_record(
                self.scan_start_time,
                {'sample_duration': self.poll_rate}
            )

            self.scan_ready = True

            print(f'conc: {conc}')
        return self.scan_start_time

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return APS3320.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = APS3320.__module__
        definition['name'] = APS3320.__name__
        definition['mfg'] = 'TSI'
        definition['model'] = '3320'
        definition['type'] = 'SizeDistribution'
        definition['tags'] = [
            'concentration',
            'particle',
            'aerosol',
            'physics',
            'tsi',
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

        raw_meas_2d = dict()
        raw_meas_2d['bin_counts'] = {
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
        dist_data.append('bin_concentration')

        primary_meas = dict()
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

        raw_meas = dict()
        raw_meas['sample_calc_time'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'seconds',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }

        process_meas = dict()
        process_meas['sheath_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('sheath_flow')

        process_meas['sample_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('sample_flow')

        process_meas['sample_duration'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'seconds',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }

        measurement_config['primary_2d'] = primary_meas_2d
        measurement_config['raw_2d'] = raw_meas_2d
        measurement_config['primary'] = primary_meas
        measurement_config['raw'] = raw_meas
        measurement_config['process'] = process_meas
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


class CPC3760A_DMPS(TSIInstrument):

    '''
    TSI CPC Model 3760A: DMPS Mode

    Eventually, this will be part of a compound instrument but
    for now I have to do it this way

    // communication constants
    static const JCharacter* kTSI_OK = "OK";
    static const JCharacter* kTSI_ERROR = "ERROR";
    static const JSize kMaxAttempts = 5;

    static const JCharacter* kTSI_DumpCmd = 					"D";
    static const JCharacter* kTSI_DumpCountsCmd = 					"DC";

    static const JCharacter kCR = 0x0d;
    static const JCharacter kNL = 0x0a;
    '''

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(CPC3760A_DMPS, self).__init__(config, **kwargs)

        self.name = 'CPC3760A_DMPS'
        self.type = 'DMPS'
        self.model = '3760A_DMPS'
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
        self.scan_start_param = 'date'
        self.scan_stop_param = 'mcpc_errs'
        self.scan_ready = False
        self.current_size_dist = []
        self.scan_state = 999
        self.scan_run_state = 'STOPPED'

        # override how often metadata is sent
        self.include_metadata_interval = 300

        # this instrument appears to work with readline
        self.iface_options = {
            'read_method': 'readuntil',
            'read_terminator': '\r',
        }

        # self.diameters_um = [
        #     .50468, .54215,
        #     .58166, .62506, .67305, .72353, .7775,
        #     .83546, .89791, .96488, 1.0368, 1.1143,
        #     1.1972, 1.2867, 1.3826, 1.4855, 1.5965,
        #     1.7154, 1.8433, 1.9812, 2.1291, 2.2875,
        #     2.4579, 2.6413, 2.8387, 3.0505, 3.2779,
        #     3.5227, 3.7856, 4.0679, 4.3717, 4.698,
        #     5.0482, 5.4245, 5.8292, 6.2644, 6.7317,
        #     7.2338, 7.7735, 8.3536, 8.9772, 9.6468,
        #     10.366, 11.14, 11.971, 12.864, 13.824,
        #     14.855, 15.963, 17.154, 18.435, 19.81
        # ]
        # self.first_good_diameter = 0.89791

        self.diameters_um = []
        self.dlogDp_list = []
        self.hv_list = []

        self.scan_length = 120
        if 'scan_length' in config['DESCRIPTION']:
            self.scan_length = config['DESCRIPTION']['scan_length']

        self.dp_steps = 10
        if 'dp_steps' in config['DESCRIPTION']:
            self.dp_steps = config['DESCRIPTION']['dp_steps']

        self.first_dp = .020
        if 'first_dp' in config['DESCRIPTION']:
            self.first_dp = config['DESCRIPTION']['first_dp']

        self.last_dp = .200
        if 'last_dp' in config['DESCRIPTION']:
            self.last_dp = config['DESCRIPTION']['last_dp']

        self.purge_time = 15
        if 'purge_time' in config['DESCRIPTION']:
            self.purge_time = config['DESCRIPTION']['purge_time']

        self.step_direction = 'down'
        if 'step_direction' in config['DESCRIPTION']:
            self.step_direction = config['DESCRIPTION']['step_direction']

        self.dma_type = 'HaukeShort'
        if 'dma_type' in config['DESCRIPTION']:
            self.dma_type = config['DESCRIPTION']['dma_type']

        self.sheath_flow = 9.0
        if 'sheath_flow' in config['DESCRIPTION']:
            self.sheath_flow = config['DESCRIPTION']['sheath_flow']

        self.sample_flow = 0.9
        if 'sample_flow' in config['DESCRIPTION']:
            self.sample_flow = config['DESCRIPTION']['sample_flow']

        self.hv_channel = None
        if 'hv_channel' in config['DESCRIPTION']:
            self.hv_channel = config['DESCRIPTION']['hv_channel']

        self.hv_sp_channel = None
        if 'hv_sp_channel' in config['DESCRIPTION']:
            self.hv_sp_channel = config['DESCRIPTION']['hv_sp_channel']

        self.Hauke_Rout = 0.0335  # meters
        self.Hauke_Rin = 0.02500  # meters
        self.HaukeShort_L = 0.110  # meters
        self.HaukeMed_L = 0.280  # meters
        self.HaukeLong_L = 0.500  # meters

        self.e_charge = 1.602e-19  # coulombs
        self.Pref = 1013.15  # HPa
        self.Tref = 293.15  # K (20C)
        self.Lambda_ref = 66.02  # nm
        self.Visc_ref = 1.832e-4  # poise

        self.CtoK = 273.15  # K (ie., 0C)
        self.Tdef = 20.0  # C - default if meas not available
        self.Pdef = 1013.15  # p - default if meas not available

        self.setup()

    def get_datafile_config(self):
        config = super().get_datafile_config()
        config['save_interval'] = 0
        return config

    def setup(self):
        super().setup()

        # only has one interface
        self.iface = next(iter(self.iface_map.values()))

        # default coms: usb
        #   230400 8-N-1

        # TODO: this will depend on mode
        # add polling loop
        # if polled:
        self.is_polled = True
        # self.poll_rate = 300  # every 5 minutes
        # self.overhead = 15 # seconds
        # self.poll_rate = 60  # every 5 minutes
        # self.overhead = 5  # seconds
        self.poll_rate = self.scan_length
        self.overhead = 15

        self.steps = 10
        self.secs_per_step = 3
        self.step_overhead = 1

        # TODO: calculate diameters and voltages
        self.calculate_dp_list()
        self.calculate_hv_list()

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

    def calculate_dp_list(self):

        self.diameters_um = []
        logStep = math.log10(self.last_dp/self.first_dp) / \
            float(self.dp_steps-1)
        logStep = pow(10.0, logStep)
        self.diameters_um.append(self.first_dp)
        self.dlogDp_list.append(logStep)

        for i in range(1, self.dp_steps):
            self.diameters_um.append(
                round(self.diameters_um[i-1]*logStep, 4)
            )

        print(f'diameters: {self.diameters_um}')

    def calculate_hv_list(self):

        self.hv_list = []

        if self.dma_type == 'HaukeShort':
            nomQSh = self.sheath_flow
            Rout = self.Hauke_Rout
            Rin = self.Hauke_Rin
            L = self.HaukeShort_L
        elif self.dma_type == 'HaukeMed':
            nomQSh = self.sheath_flow
            Rout = self.Hauke_Rout
            Rin = self.Hauke_Rin
            L = self.HaukeMed_L

        measP = 1000
        measT = 25.0
        measT_K = measT+self.CtoK
        term1 = self.Lambda_ref * (measT_K/self.Tref)
        term2 = (self.Pref/measP)
        term3 = (1.0+110.4/self.Tref)/(1.0+110.4/(measT+self.CtoK))
        lambda_calc = (
            # self.Lambda_ref * ((self.measT+self.CtoK)/self.Tref) *
            # (self.Pref/measP) *
            # (1.0+110.4/self.Tref)/(1.0+110.4/(measT+self.CtoK))
            term1 * term2 * term3
        )

        visc = (
            self.Visc_ref * pow(((measT+self.CtoK)/self.Tref), 1.5) *
            (self.Tref + 110.4) / ((measT+self.CtoK)+110.4)
        )

        for dp in self.diameters_um:
            diam = dp * 1000.0

            cSlip = (
                1.0 + lambda_calc/diam *
                (2.514 + 0.8 * math.exp(-0.55 * diam / lambda_calc))
            )

            Zp = (
                self.e_charge * cSlip * 100000000.0 /
                (3.0 * math.pi * visc * diam * 0.000001)
            )

            hVolt = (
                nomQSh*1000.0/60.0 * math.log(Rout/Rin) /
                (Zp * 2.0 * math.pi * L * 100.0)
            )
            self.hv_list.append(round(hVolt, 3))

        print(f'hv: {self.hv_list}')

    def start(self, cmd=None):
        super().start()

        self.mode = 'scanning'
        # self.clean_data_record()
        # if self.is_polled:
        #     self.polling_task = asyncio.ensure_future(self.poll_loop())

        self.current_read_cnt = 0

        # TODO: send start cmd to instrument
        if self.mode == 'mono':
            pass
        elif self.mode == 'scanning':
            asyncio.ensure_future(self.start_scanning())

    async def start_scanning(self):

        print(f'start scanning')
        # set unpolled report time to high number
        # stu = f'STU65500\r'

        # clear
        # clear = 'C\r'

        # Go
        # go = 'G\r'

        # unpolled start
        # unpolled_start = 'U1\r'

        dump_counts = 'DC\r'
        cmd_list = [dump_counts]

        self.scan_ready = False
        self.valid_step_counts = False

        if self.iface_components['cpc']:
            cpc_id = self.iface_components['cpc']
            for cmd in cmd_list:
                self.current_read_cnt = 0
                # cmd = 'sems_mode=2\n'
                msg = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject='SEND',
                    body=cmd,
                )
                # print(f'msg: {msg}')
                await self.iface_map[cpc_id].message_from_parent(msg)
                # TODO: wait for return OK
                await asyncio.sleep(.5)  # give the inst a sec
                self.scan_state = 'RUNNING'
            if self.is_polled:
                self.polling_task = asyncio.ensure_future(self.poll_loop())

    async def stop_scanning(self):

        print(f'stop scanning')

        dump_counts = 'DC\r'

        cmd_list = [dump_counts]
        self.scan_ready = False

        body = {
            'cmd': 'set_voltage',
            'channel': self.hv_sp_channel,
            'value': 0
        }
        msg = Message(
            sender_id=self.get_id(),
            msgtype=Instrument.class_type,
            subject='SEND',
            body=body,
        )
        # print(f'msg: {msg.body}')
        if self.iface_components['hv']:
            hv_id = self.iface_components['hv']
            await self.iface_map[hv_id].message_from_parent(msg)

        if self.iface_components['cpc']:
            cpc_id = self.iface_components['cpc']
            for cmd in cmd_list:
                self.current_read_cnt = 0
                # cmd = 'sems_mode=0\n'
                msg = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject='SEND',
                    body=cmd,
                )
                print(f'msg: {self.iface_map[cpc_id]}, {msg.to_json()}')
                # self.scan_run_state = 'STOPPING'
                await self.iface_map[cpc_id].message_from_parent(msg)
                await asyncio.sleep(.25)
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

        # # FOR TESTING ONLY! REMOVE
        # self.purge_time = 1
        scan_time = self.poll_rate
        sample_time = self.poll_rate - self.overhead
        step_scan_time = sample_time / self.dp_steps
        step_sample_time = step_scan_time - self.purge_time

        # wait for start of next scan period
        print(f'Starting scan in {time_to_next(scan_time)} seconds')
        await asyncio.sleep(time_to_next(scan_time))

        # start_sample = f'S{sample_time}\r'
        dump_counts = 'DC\r'
        cmds = [dump_counts]

        while True:
            # TODO: implement current_poll_cmds
            # cmds = self.current_poll_cmds

            # print(f'cmds: {cmds}')
            # cmds = ['read\n']
            self.scan_start_time = dt_to_string()
            self.scan_duration = self.poll_rate
            self.scan_ready = False
            self.current_scan_counts = []
            self.current_scan_secs = []

            # start steps
            self.current_step = 0
            self.step_increment = 1
            if self.step_direction == 'down':
                self.current_step = self.dp_steps-1
                self.step_increment = -1

            hv_id = self.iface_components['hv']
            cpc_id = self.iface_components['cpc']

            while (
                self.current_step >= 0 and
                self.current_step < self.dp_steps
            ):
                print(f'set HV: {self.hv_list[self.current_step]}')
                body = {
                    'cmd': 'set_voltage',
                    'channel': self.hv_sp_channel,
                    'value': self.hv_list[self.current_step]/1000.
                }
                msg = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject='SEND',
                    body=body,
                )
                # print(f'msg: {msg.body}')
                if self.iface_map[hv_id]:

                    await self.iface_map[hv_id].message_from_parent(msg)

                await asyncio.sleep(self.purge_time)
                self.valid_step_counts = False

                # clear count buffer
                if self.iface_map[cpc_id]:

                    # self.current_read_cnt = 0
                    msg = Message(
                        sender_id=self.get_id(),
                        msgtype=Instrument.class_type,
                        subject='SEND',
                        body=dump_counts,
                    )
                    # print(f'msg: {msg.body}')
                    await self.iface_map[cpc_id].message_from_parent(msg)

                    # wait for sample time
                    await asyncio.sleep(step_sample_time)
                    self.valid_step_counts = True
                    msg = Message(
                        sender_id=self.get_id(),
                        msgtype=Instrument.class_type,
                        subject='SEND',
                        body=dump_counts,
                    )
                    # print(f'msg: {msg.body}')
                    await self.iface_map[cpc_id].message_from_parent(msg)

                self.current_step += self.step_increment

            self.scan_ready = True

            self.current_step = 0
            self.step_increment = 1
            if self.step_direction == 'down':
                self.current_step = self.dp_steps-1
                self.step_increment = -1

            await asyncio.sleep(time_to_next(self.poll_rate))

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            # print(f'aps scan: {msg.to_json()}')

            id = msg.sender_id

            # print(f'OK? {msg["BODY"]["DATA"]}')
            # if msg['BODY']['DATA'] == 'OK\r':
            #     print(f'OK')
            #     return

            dt = self.parse(msg)
            # return
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
                # if self.scan_ready:

                print(f'scan ready...dt = {dt}')
                self.update_data_record(
                    dt,
                    {'diameter_um': self.diameters_um},
                )

                # # entry['METADATA'] = self.get_metadata()
                # self.update_data_record(
                #     dt,
                #     {'sheath_flow_sp': 2.5},
                # )
                # self.update_data_record(
                #     dt,
                #     {'number_bins': 30},
                # )
                # self.update_data_record(
                #     dt,
                #     {'bin_time': 1},
                # )

                # if len(self.current_size_dist) == 30:
                #     self.update_data_record(
                #         dt,
                #         {'size_distribution': self.current_size_dist},
                #     )

                #     # calculate diameters
                #     min_dp = 10
                #     param = self.get_data_record_param(
                #         dt,
                #         'actual_max_dp'
                #     )
                #     if not param:
                #         max_dp = 300
                #     else:
                #         max_dp = float(param)
                #     dlogdp = math.pow(
                #         10,
                #         math.log10(max_dp/min_dp)/(30-1)
                #     )
                #     # dlogdp = dlogdp / (30-1)
                #     diam = []
                #     diam.append(10)
                #     for x in range(1, 30):
                #         dp = round(diam[x-1] * dlogdp, 2)
                #         diam.append(dp)

                #     self.update_data_record(
                #         dt,
                #         {'diameter': diam},
                #     )

                entry = self.get_data_entry(dt)
                print(f'entry: {entry}')

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
                await self.to_parent_buf.put(data)
                # await PlotManager.update_data(self.plot_name, data.to_json())
                if self.datafile:
                    await self.datafile.write_message(data)
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
        if control and value is not None:
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
        print(f'parse: {msg.to_json()}')
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body['DATETIME']
        print(f'msg[DATETIME]: {dt}')

        # print(f'{msg.sender_id}, {self.iface_components["cpc"]}')
        if msg.sender_id == self.iface_components['cpc']:

            line = msg.body['DATA'].rstrip()
            print(f'line = {line}')
            if ('OK' in line):
                return

            if not self.valid_step_counts:
                print(f'waiting...')
                return None

            params = line.split(',')
            # TODO: add try to catch bad values
            self.current_scan_secs.append(float(params[0]))
            self.current_scan_counts.append(float(params[1]))

            if self.scan_ready:

                if self.step_direction == 'down':
                    self.current_scan_counts.reverse()
                    self.current_scan_secs.reverse()

                dn = []
                for count, sec in zip(
                    self.current_scan_counts,
                    self.current_scan_secs
                ):

                    conc = (
                        (count / sec) *
                        (60.0 / self.sample_flow) *
                        (1.0 / 1000.0)
                    )
                    dn.append(round(conc, 4))
                # counts = np.array(self.current_scan_counts)
                # secs = np.array(self.current_scan_secs)

                # conc = counts/secs
                # conc *= (60.0 / self.sample_flow)
                # conc *= (1/1000)
                # conc = (
                #     (counts/secs) *
                #     (60 / self.sample_flow) *
                #     (1.0 / 1000.0)
                # )

                self.update_data_record(
                    self.scan_start_time,
                    {'bin_concentration': dn}
                )

                self.update_data_record(
                    self.scan_start_time,
                    {'bin_counts': self.current_scan_counts}
                )

                self.update_data_record(
                    self.scan_start_time,
                    {'bin_seconds': self.current_scan_secs}
                )

                npdn = np.array(dn)
                intN = np.sum(npdn)
                self.update_data_record(
                    self.scan_start_time,
                    {'integral_concentration': round(intN, 2)}
                )

                return self.scan_start_time

        return None
        # params = line.split(',')
        # if params[1] == 'D':
        #     checksum = params[0]
        #     mode = params[2]
        #     status_flag = params[4]
        #     try:
        #         sample_time = float(params[5])
        #     except ValueError:
        #         sample_time = 0

        #     first_channel = 11
        #     data_channels = len(params)-10
        #     num_channel = 52

        #     conc = []
        #     for i in range(0, 52):
        #         conc.append(0)

        #     for i in range(first_channel, len(params)):
        #         try:
        #             conc[i-first_channel] = float(params[i])
        #         except ValueError:
        #             conc[i-first_channel] = 0

        #     self.update_data_record(
        #         self.scan_start_time,
        #         {'bin_concentration': conc}
        #     )

        #     # integrate concentration
        #     intN = 0
        #     for i in range(0, num_channel):
        #         if self.diameters_um[i] > self.first_good_diameter:
        #             intN += conc[i]

        #     self.update_data_record(
        #         self.scan_start_time,
        #         {'integral_concentration': intN}
        #     )

        #     # populate these for now
        #     self.update_data_record(
        #         self.scan_start_time,
        #         {'sheath_flow': None}
        #     )

        #     self.update_data_record(
        #         self.scan_start_time,
        #         {'sample_flow': None}
        #     )

        #     self.scan_ready = True

        #     print(f'conc: {conc}')
        # return self.scan_start_time

    #     # if len(line) == 0:
    #     #     self.current_read_cnt += 1
    #     # else:
    #     parts = line.split('=')

    #     if len(parts) < 2:
    #         return dt

    #     # self.scan_state = 999
    #     # if self.scan_run_state == 'STOPPING':
    #     #     if parts[0] == 'scan_state':
    #     #         self.scan_state = int(parts[1])

    #     # print(f'77777777777777{parts[0]} = {parts[1]}')
    #     if parts[0] in self.parse_map:
    #         self.update_data_record(
    #             dt,
    #             {self.parse_map[parts[0]]: parts[1]},
    #         )
    #         if self.scan_stop_param == parts[0]:
    #             self.scan_ready = True
    #         elif self.scan_start_param == parts[0]:
    #             self.current_size_dist.clear()
    #     elif parts[0].find('bin') >= 0:
    #         self.current_size_dist.append(
    #             float(parts[1])
    #         )
    #     # # TODO: how to limit to one/sec
    #     # # check for new second
    #     # # if data['DATETIME'] == self.last_entry['DATA']['DATETIME']:
    #     # #     # don't duplicate timestamp for now
    #     # #     return
    #     # # self.last_entry['DATETIME'] = data['DATETIME']

    #     # measurements = dict()

    #    # controls_list = ['mcpc_power', 'mcpc_pump']

    #     # for name in controls_list:
    #     #     self.update_data_record(
    #     #         dt,
    #     #         {name: None},
    #     #     )

    #     return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return CPC3760A_DMPS.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = CPC3760A_DMPS.__module__
        definition['name'] = CPC3760A_DMPS.__name__
        definition['mfg'] = 'TSI'
        definition['model'] = '3760A_DMPS'
        definition['type'] = 'SizeDistribution'
        definition['tags'] = [
            'concentration',
            'particle',
            'aerosol',
            'physics',
            'tsi',
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
                'units': ['dateTime', 'nm'],
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

        raw_2d['bin_seconds'] = {
            'dimensions': {
                'axes': ['TIME', 'DIAMETER'],
                'unlimited': 'TIME',
                'units': ['dateTime', 'um'],
            },
            'units': 'seconds',  # should be cfunits or udunits
            'uncertainty': 0.1,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'bin_secs',
            # 'parse_label': 'bin',
            'control': None,
            'axes': {
                # 'TIME', 'datetime',
                'DIAMETER': 'diameter_um',
            }
        }
        dist_data.append('bin_seconds')

        primary_meas = dict()
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

        process_meas = dict()
        process_meas['sheath_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('sheath_flow')

        process_meas['sample_flow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'liters min-1',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('sample_flow')

        process_meas['sample_duration'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'seconds',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sat_bot_temp',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }

        measurement_config['primary_2d'] = primary_meas_2d
        measurement_config['primary'] = primary_meas
        measurement_config['process'] = process_meas
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
