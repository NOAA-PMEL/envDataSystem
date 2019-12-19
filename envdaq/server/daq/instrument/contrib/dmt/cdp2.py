# import json
import sys
from daq.instrument.instrument import Instrument
from daq.instrument.contrib.dmt.dmt import DMTInstrument
from data.message import Message
# from daq.daq import DAQ
import asyncio
from utilities.util import time_to_next
from daq.interface.interface import Interface
# from plots.plots import PlotManager
import math
from struct import pack, unpack
from struct import error as structerror

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    print("error GPIO - might need sudo")


class CDP2(DMTInstrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(CDP2, self).__init__(config, **kwargs)

        self.name = 'CDP2'
        self.model = 'CDP2'
        self.tag_list = [
            'concentration',
            'cloud',
            'droplet',
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

        # self.scan_start_param = 'date'
        # self.scan_stop_param = 'mcpc_errs'
        # self.scan_ready = False
        # self.current_size_dist = []
        # self.scan_state = 999
        self.scan_run_state = 'STOPPED'

        # TODO: allow params to be passed in config
        self.start_byte = 27  # Esc char
        self.setup_command = 1
        self.data_command = 2

        self.adc_threshold = 60
        self.bin_count = 30

        # Sizes=<30>3,4,5,6,7,8,9,10,11,12,13,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50
        self.lower_dp_bnd = [
            2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
            12, 13, 14, 16, 18, 20, 22, 24, 26, 28,
            30, 32, 34, 36, 38, 40, 42, 44, 46, 48
        ]
        self.uppder_dp_bnd = [
            3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
            13, 14, 16, 18, 20, 22, 24, 26, 28,  30,
            32, 34, 36, 38, 40, 42, 44, 46, 48, 50
        ]

        # Thresholds=<30>91,111,159,190,215,243,254,272,301,355,382,488,636,751,846,959,1070,1297,1452,1665,1851,2016,2230,2513,2771,3003,3220,3424,3660,4095
        self.upper_bin_th = [
            91, 111, 159, 190, 215, 243, 254, 272, 301, 355,
            382, 488, 636, 751, 846, 959, 1070, 1297, 1452, 1665,
            1851, 2016, 2230, 2513, 2771, 3003, 3220, 3424, 3660, 4095
        ]

        self.dof_reject = True
        self.sample_area = 0.264  # (mm^2)

        # override how often metadata is sent
        self.include_metadata_interval = 300

        # this instrument appears to work with readline
        self.iface_options = {
            'send_method': 'binary',
            'read_method': 'readbinary',
        }

        self.gpio_enable_ch = 31

        self.setup()

    # def get_datafile_config(self):
    #     config = super().get_datafile_config()
    #     config['save_interval'] = 0
    #     return config

    def setup(self):
        super().setup()

        # only has one interface
        self.iface = next(iter(self.iface_map.values()))

        # default coms: RS-422
        #   57600 8-N-1

        # TODO: this will depend on mode
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
                # parse_label = meas['parse_label']
                # self.parse_map[parse_label] = name
                # self.data_record_template[msetsname][name] = None
                self.data_record_template[name] = {'VALUE': None}

        # TODO: read config file to init probe

    def get_cdp_command(self, cmd_type):

        # universal start byte (Esc char)
        cmd = pack('<B', self.start_byte)

        if cmd_type == 'CONFIGURE':
            cmd += pack('<B', self.setup_command)
            cmd += pack('<H', self.adc_threshold)
            cmd += pack('<H', 0)  # unused
            cmd += pack('<H', self.bin_count)
            cmd += pack('<H', self.dof_reject)

            # unused bins
            for i in range(0, 5):
                cmd += pack('<H', 0)

            # upper bin thresholds
            for n in self.upper_bin_th:
                cmd += pack('<H', n)

            # fill last unused bins
            for n in range(0, 10):
                cmd += pack('<H', n)

        elif cmd_type == 'SEND_DATA':
            cmd += pack('B', self.data_command)

        else:
            return None

        checksum = 0
        for ch in cmd:
            checksum += ch

        cmd += pack('<H', checksum)
        return cmd

    def start(self, cmd=None):
        super().start()

        # turn on 'enable' line via gpio
        if 'RPi.GPIO' in sys.modules:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.gpio_enable_ch, GPIO.OUT, initial=GPIO.LOW)
            GPIO.output(self.gpio_enable_ch, GPIO.HIGH)

        self.scan_run_state = 'CONFIGURE'
        if self.is_polled:
            self.polling_task = asyncio.ensure_future(self.poll_loop())

        # TODO: Send config string to unit and wait for ACK
        # print(f'self.status = SETUP')
        # print(f'send CDP2 config to unit')
        # self.scan_run_state = 'CONFIGURE'

        # cmd = self.get_cdp_command('CONFIGURE')
        # if cmd:
        #     msg = Message(
        #         sender_id=self.get_id(),
        #         msgtype=Instrument.class_type,
        #         subject='SEND',
        #         body={
        #             'return_packet_bytes': 4,
        #             'send_packet': cmd,
        #         }
        #     )
        #     print(f'msg: {msg}')
        #     await self.iface.message_from_parent(msg)

        # self.current_read_cnt = 0

        # # TODO: send start cmd to instrument
        # if self.mode == 'mono':
        #     pass
        # elif self.mode == 'scanning':
        #     asyncio.ensure_future(self.start_scanning())

    def stop(self, cmd=None):
        if 'RPi.GPIO' in sys.modules:
            GPIO.output(self.gpio_enable_ch, GPIO.LOW)
            GPIO.cleanup(self.gpio_enable_ch)

        self.scan_run_state = 'STOPPED'
        if self.polling_task:
            self.polling_task.cancel()

        super().stop()

    async def poll_loop(self):
        print(f'polling loop started')

        configure_cmd = self.get_cdp_command('CONFIGURE')
        send_data_cmd = self.get_cdp_command('SEND_DATA')

        while True:
            # TODO: implement current_poll_cmds
            cmds = self.current_poll_cmds
            print(f'cmds: {cmds}')
            # cmds = ['read\n']

            if self.iface:

                if self.scan_run_state == 'STOPPED':

                    for cmd in cmds:
                        msg = Message(
                            sender_id=self.get_id(),
                            msgtype=Instrument.class_type,
                            subject='SEND',
                            body={
                                'return_packet_bytes': 4,
                                'send_packet': configure_cmd,
                            }
                        )
                        self.scan_run_state = 'CONFIGURE'
                        print(f'msg: {msg}')
                        await self.iface.message_from_parent(msg)

                elif self.scan_run_state == 'RUN':

                    for cmd in cmds:
                        msg = Message(
                            sender_id=self.get_id(),
                            msgtype=Instrument.class_type,
                            subject='SEND',
                            body={
                                'return_packet_bytes': 156,
                                'send_packet': send_data_cmd,
                            }
                        )
                        print(f'msg: {msg}')
                        await self.iface.message_from_parent(msg)

            await asyncio.sleep(time_to_next(self.poll_rate))

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            # id = msg.sender_id
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

                self.set_control_att(control, 'action_state', 'OK')

    def parse(self, msg):
        # print(f'parse: {msg.to_json()}')
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body['DATETIME']

        packet = msg.body['DATA']

        if self.scan_run_state == 'CONFIGURE':
            ack_fmt = '<4B'
            data = unpack(ack_fmt, packet)
            if data[0] == 6:
                self.scan_run_state = 'RUN'
                return None

        elif self.scan_run_state == 'RUN':
            data_format = '<8HI5HI30IH'
            try:
                data = unpack(data_format, packet)

            except structerror:
                print(f'bad packet {packet}')
                return None

            val = data[0]*0.061
            self.update_data_record(
                dt,
                {'laser_current': val}
            )

            val = 5*data[1]/4095
            self.update_data_record(
                dt,
                {'dump_spot_monitor': val}
            )

            v = 5*data[2]/4095
            degC = 1 / (((math.log((5/v) - 1))/3750) + 1/298) - 273
            self.update_data_record(
                dt,
                {'wingboard_temperature': degC}
            )

            v = 5*data[3]/4095
            degC = 1 / (((math.log((5/v) - 1))/3750) + 1/298) - 273
            self.update_data_record(
                dt,
                {'laser_temperature': degC}
            )

            val = 5*data[4]/4095
            self.update_data_record(
                dt,
                {'sizer_baseline': val}
            )

            val = 5*data[5]/4095
            self.update_data_record(
                dt,
                {'qualifier_baseline': val}
            )

            val = (5*data[6]/4095)*2
            self.update_data_record(
                dt,
                {'5v_monitor': val}
            )

            v = 5*data[7]/4095
            degC = 1 / (((math.log((5/v) - 1))/3750) + 1/298) - 273
            self.update_data_record(
                dt,
                {'control_board_temperature': degC}
            )

            self.update_data_record(
                dt,
                {'reject_dof': data[8]}
            )

            self.update_data_record(
                dt,
                {'average_transit': data[9]}
            )

            self.update_data_record(
                dt,
                {'qual_bandwidth': data[10]}
            )

            self.update_data_record(
                dt,
                {'qual_threshold': data[11]}
            )

            self.update_data_record(
                dt,
                {'dt_bandwidth': data[12]}
            )

            self.update_data_record(
                dt,
                {'dynamic_threshold': data[13]}
            )

            self.update_data_record(
                dt,
                {'adc_overflow': data[14]}
            )

            bc = []
            dp = []
            intN = 0
            for i in range(0, self.bin_count):
                bc.append(data[15+i])
                intN += data[15+i]
                dp.append(
                    (self.lower_dp_bnd[i] + self.uppder_dp_bnd)/2
                )

            self.update_data_record(
                dt,
                {'bin_counts': bc}
            )

            self.update_data_record(
                dt,
                {'diameter_um': dp}
            )

            self.update_data_record(
                dt,
                {'integral_counts': dp}
            )

        return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return CDP2.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = CDP2.__module__
        definition['name'] = CDP2.__name__
        definition['mfg'] = 'DMT'
        definition['model'] = 'CDP2'
        definition['type'] = 'SizeDistribution'
        definition['tags'] = [
            'concentration',
            'particle',
            'cloud',
            'droplet',
            'physics',
            'DMT',
            'Droplet Measurement Technologies',
            'sizing',
            'size distribution'
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []
        dist_data = []

        # TODO: add interface entry for each measurement
        primary_meas_2d = dict()
        primary_meas_2d['bin_counts'] = {
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
            'parse_label': 'diameter',
            'control': None,
            'axes': {
                # 'TIME', 'datetime',
                'DIAMETER': 'diameter_um',
            }
        }
        dist_data.append('diameter_um')

        primary_meas = dict()
        primary_meas['integral_counts'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'int_counts',
            'control': None,
        }
        y_data.append('integral_counts')

        raw_meas = dict()
        raw_meas['laser_current'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'mA',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'laser_cur',
            'control': None,
        }
        y_data.append('laser_current')

        raw_meas['dump_spot_monitor'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'V',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'dump_sp_mon',
            'control': None,
        }
        y_data.append('dump_spot_monitor')

        raw_meas['wingboard_temperature'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'wing_temp',
            'control': None,
        }
        y_data.append('wingboard_temperature')

        raw_meas['laser_temperature'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'laser_temp',
            'control': None,
        }
        y_data.append('laser_temperature')

        raw_meas['sizer_baseline'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'V',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('sizer_baseline')

        raw_meas['qualifier_baseline'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'V',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'qual_base',
            'control': None,
        }
        y_data.append('qualifier_baseline')

        raw_meas['5v_monitor'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'V',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('5v_monitor')

        raw_meas['control_board_temperature'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'ctrl_brd_T',
            'control': None,
        }
        y_data.append('control_board_temperature')

        raw_meas['reject_dof'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('reject_dof')

        raw_meas['average_transit'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            'short_name': 'avg_trans',
            'control': None,
        }
        y_data.append('average_transit')

        raw_meas['qual_bandwidth'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('qual_bandwidth')

        raw_meas['qual_threshold'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('qual_threshold')

        raw_meas['dt_bandwidth'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('dt_bandwidth')

        raw_meas['dynamic_threshold'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('dynamic_threshold')

        raw_meas['adc_overflow'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'counts',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'CALCULATED',
            'data_type': 'NUMERIC',
            # 'short_name': 'sizer_base',
            'control': None,
        }
        y_data.append('adc_overflow')

        measurement_config['primary_2d'] = primary_meas_2d
        measurement_config['primary'] = primary_meas
        measurement_config['raw'] = raw_meas
        # measurement_config['controls'] = controls

        definition['measurement_config'] = measurement_config

        plot_config = dict()

        size_dist = dict()
        size_dist['app_type'] = 'SizeDistribution'
        size_dist['y_data'] = ['bin_counts', 'diameter_um']
        size_dist['default_y_data'] = ['bin_counts']
        source_map = {
            'default': {
                'y_data': {
                    'default': ['bin_counts', 'diameter_um']
                },
                'default_y_data': ['bin_counts']
            },
        }
        size_dist['source_map'] = source_map

        time_series1d = dict()
        time_series1d['app_type'] = 'TimeSeries1D'
        time_series1d['y_data'] = y_data
        time_series1d['default_y_data'] = ['integral_counts']
        source_map = {
            'default': {
                'y_data': {
                    'default': y_data
                },
                'default_y_data': ['integral_counts']
            },
        }
        time_series1d['source_map'] = source_map

        # size_dist['dist_data'] = dist_data
        # size_dist['default_dist_data'] = ['size_distribution']

        plot_config['plots'] = dict()
        plot_config['plots']['raw_size_dist'] = size_dist
        plot_config['plots']['main_ts1d'] = time_series1d
        definition['plot_config'] = plot_config

        return {'DEFINITION': definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition
