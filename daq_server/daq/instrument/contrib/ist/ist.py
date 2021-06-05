# import json
from daq.instrument.instrument import Instrument
from shared.data.message import Message
from shared.data.status import Status
# from daq.daq import DAQ
import asyncio
from shared.utilities.util import time_to_next
from daq.interface.interface import Interface
# import math
# import numpy as np


class ISTInstrument(Instrument):

    INSTANTIABLE = False

    def __init__(self, config, **kwargs):
        super(ISTInstrument, self).__init__(config, **kwargs)

        self.mfg = 'IST'

    def setup(self):
        super().setup()

        # TODO: add properties get/set to interface for
        #       things like readmethod

class HYT271(ISTInstrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(HYT271, self).__init__(config, **kwargs)

        self.name = 'HYT271'
        self.type = 'TandRH'
        self.model = 'HYT271'
        self.tag_list = [
            'temperature',
            'relative_humidity',
            'rh',
            'met',
            'environmental',
            'i2c'
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

        # override how often metadata is sent
        self.include_metadata_interval = 300

        # this instrument appears to work with readline
        self.iface_options = {
            # 'read_method': 'readuntil',
            # 'read_terminator': '\r',
            'decode_errors': 'ignore'
        }

        self.data_ready = False

        self.setup()

    # def get_datafile_config(self):
    #     config = super().get_datafile_config()
    #     config['save_interval'] = 0
    #     return config

    def setup(self):
        super().setup()

        # only has one interface
        # self.iface = next(iter(self.iface_map.values()))
        self.iface = None
        if self.iface_components["default"]:
            if_id = self.iface_components["default"]
            self.iface = self.iface_map[if_id]
        else:
            self.iface = next(iter(self.iface_map.values()))

        # default coms: serial
        #   9600 8-N-1

        # TODO: this will depend on mode
        # add polling loop
        # if polled:
        self.is_polled = True
        self.poll_rate = 1

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

        self.status['ready_to_run'] = True
        self.status2.set_run_status(Status.READY_TO_RUN)
        self.enable()

    async def shutdown(self):
        # print("MSEMS shutdown")
        # print("msems stop")
        self.stop()
        self.disable()
        # print("msems dereg")
        await self.deregister_from_UI()
        # print("msems super shutdown")
        # TODO need to wait for deregister before closing loops and connection
        await super().shutdown()

    def enable(self):
        super().enable()
        # print(f"polled: {self.is_polled}")
        if self.is_polled:
            self.polling_task = asyncio.ensure_future(self.poll_loop())

    def disable(self):
        if self.polling_task:
            self.polling_task.cancel()
        super().disable()

    def start(self, cmd=None):
        super().start()

        # if self.is_polled:
        #     self.polling_task = asyncio.ensure_future(self.poll_loop())

    def stop(self, cmd=None):
        # if self.polling_task:
        #     self.polling_task.cancel()

        # TODO: add delay while scanning is stopped
        super().stop()

    async def poll_loop(self):
        print(f'polling loop started')

        # wait for start of next scan period
        # print(f'Starting scan in {time_to_next(scan_time)} seconds')
        await asyncio.sleep(time_to_next(self.poll_rate))

        while True:
            # TODO: implement current_poll_cmds
            # cmds = self.current_poll_cmds

            # print(f'cmds: {cmds}')
            # cmds = ['read\n']

            if self.iface:
                # meas_cmd = '#WW44022C06\n'
                # read_cmd = '#RR4406\n'

                # cmd = '{ 99RDD}\r'

                # send read command
                cmd_args = {
                    'command': 'write_byte',
                    'address': '28',
                    # 'write_length': '02',
                    'data': '00'
                }

                msg = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject='SEND',
                    body=cmd_args,
                )
                # print(f'msg: {msg.body}')
                await self.iface.message_from_parent(msg)

                await self.ready_to_read()

                # send read command
                cmd_args = {
                    'command': 'read_buffer',
                    'address': '28',
                    'read_length': '04'
                }

                msg = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject='SEND',
                    body=cmd_args,
                )
                # print(f'msg: {msg.body}')
                await self.iface.message_from_parent(msg)

            await asyncio.sleep(time_to_next(self.poll_rate))

    async def ready_to_read(self):

        while not self.data_ready:
            await asyncio.sleep(.1)

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if (type == 'FromChild' and msg.type == Interface.class_type):
            # print(f'aps scan: {msg.to_json()}')

            # id = msg.sender_id

            dt = self.parse(msg)

            if dt:
                entry = self.get_data_entry(dt)
                # print(f'entry: {entry}')

                data = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                )
                # send data to next step(s)
                # to controller
                data.update(subject='DATA', body=entry)

                # send data to user interface
                await self.message_to_ui(data)
                # send data to controller
                await self.to_parent_buf.put(data)

                # save data
                if self.datafile:
                    await self.datafile.write_message(data)

                # print(f'data_json: {data.to_json()}\n')
                # await asyncio.sleep(0.01)

        # elif type == 'FromUI':
        #     if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
        #         # print(f'msg: {msg.body}')
        #         self.send_status()

        #     elif (
        #         msg.subject == 'CONTROLS' and
        #         msg.body['purpose'] == 'REQUEST'
        #     ):
        #         # print(f'msg: {msg.body}')
        #         await self.set_control(msg.body['control'], msg.body['value'])

        #     elif (
        #         msg.subject == 'RUNCONTROLS' and
        #         msg.body['purpose'] == 'REQUEST'
        #     ):
        #         # print(f'msg: {msg.body}')
        #         await self.handle_control_action(
        #             msg.body['control'], msg.body['value']
        #         )

        await super().handle(msg, type)

        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        await super(HYT271, self).super(control, value)

        # if control and value:
        #     if control == 'start_stop':
        #         if value == 'START':
        #             self.start()
        #         elif value == 'STOP':
        #             self.stop()

        #         self.set_control_att(control, 'action_state', 'OK')

    def parse(self, msg):
        # print(f'parse: {msg.to_json()}')

        dt = msg.body['DATETIME']
        # print(f'msg[DATETIME]: {dt}')

        # line = msg.body['DATA'].strip()
        # print(f'line = {line}')

        if 'command' in msg.body['DATA']:
            if msg.body['DATA']['command'] == 'WRITE':
                if msg.body['DATA']['result'] == 'OK':
                    self.data_ready = True
                    return None

            elif msg.body['DATA']['command'] == 'READ':
                if msg.body['DATA']['result'] == 'OK':
                    self.data_ready = False
                    data = msg.body['DATA']['data']

                    if data:
                        rh = ((((data[0] & 0x3F) * 256) + data[1]) * 100.0) / 16383.0
                        temp = ((data[2] * 256) + (data[3] & 0xFC)) / 4
                        cTemp = (temp / 16384.0) * 165.0 - 40.0
                        # print(f'{round(cTemp, 2)}, {round(rh, 2)}')
                        self.update_data_record(
                            dt,
                            {'temperature': round(cTemp, 2)}
                        )

                        self.update_data_record(
                            dt,
                            {'relative_humidity': round(rh, 2)}
                        )

                        return dt

        return None
        # >>> temp = data[0] * 256 + data[1]
        # >>> cTemp = -45 + (175 * temp / 65535.0)
        # >>> humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
        # >>> cTemp
        # 21.25085831998169
        # >>> humidity
        # 51.917296101319906

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return HYT271.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition['module'] = HYT271.__module__
        definition['name'] = HYT271.__name__
        definition['mfg'] = 'IST'
        definition['model'] = 'HYT271'
        definition['type'] = 'TandRH'
        definition['tags'] = [
            'temperature',
            'relative_humidity',
            'rh',
            'met',
            'environmental',
            'i2c'
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []

        # TODO: add interface entry for each measurement

        primary_meas = dict()
        primary_meas['temperature'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': 'degC',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            # 'short_name': 'int_conc',
            # 'parse_label': 'scan_max_volts',
            'control': None,
        }
        y_data.append('temperature')

        primary_meas['relative_humidity'] = {
            'dimensions': {
                'axes': ['TIME'],
                'unlimited': 'TIME',
                'units': ['dateTime'],
            },
            'units': '%',  # should be cfunits or udunits
            'uncertainty': 0.2,
            'source': 'MEASURED',
            'data_type': 'NUMERIC',
            'short_name': 'rh',
            'control': None,
        }
        y_data.append('relative_humidity')

        # primary_meas['dewpoint'] = {
        #     'dimensions': {
        #         'axes': ['TIME'],
        #         'unlimited': 'TIME',
        #         'units': ['dateTime'],
        #     },
        #     'units': 'degC',  # should be cfunits or udunits
        #     'uncertainty': 0.2,
        #     'source': 'calculated',
        #     'data_type': 'NUMERIC',
        #     # 'short_name': 'rh',
        #     'control': None,
        # }
        # y_data.append('dewpoint')

        measurement_config['primary'] = primary_meas

        # measurement_config['controls'] = controls

        definition['measurement_config'] = measurement_config

        plot_config = dict()

        time_series1d = dict()
        time_series1d['app_type'] = 'TimeSeries1D'
        time_series1d['y_data'] = y_data
        time_series1d['default_y_data'] = ['temperature']
        source_map = {
            'default': {
                'y_data': {
                    'default': y_data
                },
                'default_y_data': ['temperature']
            },
        }
        time_series1d['source_map'] = source_map

        plot_config['plots'] = dict()
        plot_config['plots']['main_ts1d'] = time_series1d
        definition['plot_config'] = plot_config

        return {'DEFINITION': definition}
