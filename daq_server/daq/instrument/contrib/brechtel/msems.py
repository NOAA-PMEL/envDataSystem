# import json
# from envdsys.envdaq.models import ControllerDef
from daq.instrument.instrument import Instrument
from daq.instrument.contrib.brechtel.brechtel import BrechtelInstrument
from shared.data.message import Message
from shared.data.status import Status
from daq.daq import DAQ
import asyncio
from shared.utilities.util import time_to_next
from daq.interface.interface import Interface

# from plots.plots import PlotManager
import math


class MSEMS(BrechtelInstrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(MSEMS, self).__init__(config, **kwargs)

        self.name = "MSEMS"
        self.model = "MSEMS"
        self.tag_list = [
            "concentration",
            "aerosol",
            "physics",
            "sizing",
            "size distribution",
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

        self.monitor_start_param = "pressure"
        self.monitor_stop_param = "sd_save"
        # self.scan_start_param = "scan_date" # change in return value delmiter messes this up
        self.scan_start_param = "scan_date"
        self.scan_stop_param = "mcpc_errs"
        self.scan_first_found = False
        self.scan_ready = False
        self.current_bin_counts = []
        self.current_size_dist = []
        self.scan_state = 999
        self.reading_scan = False
        self.scan_time = None
        self.scan_run_state = "STOPPED"

        self.msems_mode = "off"

        # override how often metadata is sent
        self.include_metadata_interval = 300

        # this instrument appears to work with readline
        # self.iface_options = {
        #     'read_method': 'readuntil',
        #     'read_terminator': '\r',
        # }
        self.setup()

    def get_datafile_config(self):
        config = super().get_datafile_config()
        config["save_interval"] = 0
        return config

    def setup(self):
        super().setup()

        # only has one interface
        # self.iface = next(iter(self.iface_map.values()))

        # default coms: usb
        #   230400 8-N-1

        # TODO: this will depend on mode
        # add polling loop
        # if polled:
        self.is_polled = False
        self.poll_rate = 2  # every second

        # create parse_map and empty data_record
        self.parse_map = dict()
        self.data_record_template = dict()
        definition = self.get_definition_instance()
        meas_config = definition["DEFINITION"]["measurement_config"]
        for msetsname, mset in meas_config.items():
            # self.data_record_template[msetname] = dict()
            for name, meas in mset.items():
                if "parse_label" in meas:
                    parse_label = meas["parse_label"]
                    self.parse_map[parse_label] = name
                    # self.data_record_template[msetsname][name] = None
                    self.data_record_template[name] = {"VALUE": None}

        self.status['ready_to_run'] = True
        self.status2.set_run_status(Status.READY_TO_RUN)
        self.enable()

        print("done")

    async def shutdown(self):
        print("MSEMS shutdown")
        print("msems stop")
        self.stop()
        print("msems disable")
        self.disable()
        print("msems dereg")
        await self.deregister_from_UI()
        print("msems super shutdown")
        # TODO need to wait for deregister before closing loops and connection
        await super().shutdown()

    def enable(self):

        super().enable()

        # if self.is_polled:
        self.polling_task = asyncio.create_task(self.poll_loop())

    def disable(self):
        if self.polling_task:
            self.polling_task.cancel()
        super().disable()

    def start(self, cmd=None):
        super().start()

        self.msems_mode = "scanning"
        # self.clean_data_record()
        # if self.is_polled:
        #     self.polling_task = asyncio.ensure_future(self.poll_loop())

        self.current_read_cnt = 0

        # TODO: send start cmd to instrument
        if self.msems_mode == "mono":
            pass
        elif self.msems_mode == "scanning":
            asyncio.ensure_future(self.start_scanning())

    async def start_scanning(self):

        # make sure mcpc is on and pump is started
        await self.set_control("mcpc_power_control", 1)
        await asyncio.sleep(.1)

        await self.set_control("mcpc_pump_power_control", 1)
        await asyncio.sleep(.1)

        # send scan settings before starting
        scan_settings_list = [
            "sheath_flow_sp",
            "number_bins",
            "bin_time",
            "scan_type",
            "max_diameter_sp",
            "min_diameter_sp",
            "plumbing_time",
            "sheath_c2",
            "sheath_c1",
            "sheath_c0",
            "cal_temp",
            "imp_slope",
            "imp_offset",
            "pressure_slope",
            "pressure_offset",
            "hv_slope",
            "hv_offset",
            "ext_volts_slope",
            "ext_volts_offset",
        ]
        # if self.iface:
        if self.iface_components["default"]:
            if_id = self.iface_components["default"]
            self.current_read_cnt = 0
            await asyncio.sleep(.1)

            for setting in scan_settings_list:
                try:
                    await self.set_control(
                        setting,
                        self.current_run_settings[setting]
                    )
                except KeyError:
                    pass

            # # TODO: make this into a control eventually
            # cmd = "bin_time=1.0\n"
            # msg = Message(
            #     sender_id=self.get_id(),
            #     msgtype=Instrument.class_type,
            #     subject="SEND",
            #     body=cmd,
            # )
            # # print(f'msg: {msg}')
            # # await self.iface.message_from_parent(msg)
            # await self.iface_map[if_id].message_from_parent(msg)

            # Start scanning
            cmd = "msems_mode=2\n"
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
                subject="SEND",
                body=cmd,
            )
            # print(f'msg: {msg}')
            # await self.iface.message_from_parent(msg)
            await self.iface_map[if_id].message_from_parent(msg)
            # self.scan_state = "RUNNING"

    async def stop_scanning(self):
        if self.iface_components["default"]:
            if_id = self.iface_components["default"]
            # if self.iface:
            self.current_read_cnt = 0
            cmd = "msems_mode=0\n"
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
                subject="SEND",
                body=cmd,
            )
            # print(f'msg: {self.iface}, {msg.to_json()}')
            # self.scan_run_state = 'STOPPING'
            # await self.iface.message_from_parent(msg)
            await self.iface_map[if_id].message_from_parent(msg)
            # while self.scan_state > 0:
            #     await asyncio.sleep(.1)
            # self.scan_run_state = 'STOPPED'

    def stop(self, cmd=None):
        # if self.polling_task:
        #     self.polling_task.cancel()


        # TODO: add function that waits for scanning to actually stop
        if self.msems_mode == "mono":
            pass
        elif self.msems_mode == "scanning":
            # self.loop.run_until_complete(
            #     asyncio.wait(
            #         asyncio.ensure_future(
            #             self.stop_scanning()
            #         )
            #     )
            # )
            asyncio.ensure_future(self.stop_scanning())
        # TODO: add delay while scanning is stopped
        self.msems_mode = "off"

        super().stop()

    async def update_settings_loop(self):
        # print(f'send_status: {self.name}, {self.status}')

        if not self.current_run_settings:
            self.get_current_run_settings()
        while True:
        # while self.current_run_settings:
            if self.status2.get_run_status() in [Status.READY_TO_RUN, Status.STOPPED]:
                settings = Message(
                    sender_id=self.get_id(),
                    msgtype=self.class_type,
                    subject="SETTINGS",
                    body={
                        'purpose': 'UPDATE',
                        'settings': self.current_run_settings,
                        # 'note': note,
                    }
                )
                await self.message_to_ui(settings)
            await asyncio.sleep(2)

    async def poll_loop(self):
        print("polling loop started")
        while True:
            # TODO: implement current_poll_cmds
            # cmds = self.current_poll_cmds
            # print(f'cmds: {cmds}')
            # cmds = ['read\n']

            # if self.iface:
            if self.iface_components["default"]:
                if_id = self.iface_components["default"]
                self.current_read_cnt = 0
                if self.msems_mode == "off":
                    # do monitor reading "all" or "read"?
                    cmds = ["read\n"]
                    for cmd in cmds:
                        msg = Message(
                            sender_id=self.get_id(),
                            msgtype=Instrument.class_type,
                            subject="SEND",
                            body=cmd,
                        )
                        # print(f'msg: {msg.to_json()}')

                        # await self.iface_map[if_id].message_from_parent(msg)

            await asyncio.sleep(time_to_next(self.poll_rate))

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if type == "FromChild" and msg.type == Interface.class_type:
            # id = msg.sender_id
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
            if self.msems_mode == "scanning" and self.scan_ready:

                # use scan_time
                dt = self.scan_time

                # bin_time = 1
                try:
                    bin_time = self.current_run_settings["bin_time"]
                except KeyError:
                    bin_time = 1

                try:
                    number_bins = self.current_run_settings["number_bins"]
                except KeyError:
                    number_bins = 30
                # print(f'dt = {dt}')
                # entry['METADATA'] = self.get_metadata()
                # self.update_data_record(
                #     dt,
                #     {"sheath_flow_sp": 2.5},
                # )
                # self.update_data_record(
                #     dt,
                #     {"number_bins": 30},
                # )
                # self.update_data_record(
                #     dt,
                #     {"bin_time": bin_time},
                # )

                for control, value in self.current_run_settings.items():
                    # try:
                        # pl = self.controls[control]["parse_label"]
                        # if pl in self.data_record_template:
                    self.update_data_record(dt, {control: value}, value)
                    # except KeyError:
                    #     pass

                # if len(self.current_size_dist) == 30:
                # if len(self.current_bin_counts) == 30:
                if len(self.current_bin_counts) == number_bins:
                    self.update_data_record(
                        dt,
                        # {'bin_concentration': self.current_size_dist}
                        {"bin_counts": self.current_bin_counts},
                    )

                    # flow = self.get_data_record_param(dt, 'mcpc_sample_flow')
                    # bin_time = self.get_data_record_param(dt, 'bin_time')
                    # print(f'flow: {flow}, bin_time: {bin_time}')
                    try:
                        flow = float(self.get_data_record_param(dt, "mcpc_sample_flow"))
                        bin_time = float(self.get_data_record_param(dt, "bin_time"))
                    except Exception as e:
                        print(f"Exception! {e}")
                        flow = 0.35
                        bin_time = 1.0

                    try:
                        # print(f'flow: {flow}, bin_time: {bin_time}')
                        # print(type(flow))
                        # print(type(bin_time))
                        intN = 0
                        conc = []
                        # if flow and bin_time:
                        cm3 = float(flow) * 1000.0 / 60.0 / float(bin_time)
                        # conc = [n/cm3 for n in self.current_bin_counts]
                        # for cnt in self.current_size_dist:
                        for cnt in self.current_bin_counts:
                            # print(f'cnt: {cnt}, cm3: {cm3}')
                            n = cnt / cm3
                            # print(f'n: {n}')
                            conc.append(round(n, 3))
                            intN += n
                            # print(f'intN: {intN}')
                        # else:
                        # conc = [0 for n in self.current_size_dist]
                        # intN = 0

                        self.update_data_record(
                            dt,
                            # {'bin_concentration': self.current_size_dist}
                            {"bin_concentration": conc},
                        )

                        self.update_data_record(
                            dt, {"integral_concentration": round(intN, 3)}
                        )
                    except Exception as e:
                        print(f"Exception2! {e}")
                    # if flow is None:
                    #     flow = 0.35
                    # if bin_time is None:
                    #     bin_time = 1
                    # print(f'here: {type(flow)}, {type(bin_time)}')
                    # cm3 = flow*1000./60./bin_time
                    # cm3 = 0.35 * 1000. / 60.0 / 1
                    # print(f'flow: {flow}, bin_time: {bin_time}, cm3: {cm3}')
                    # conc = [n/cm3 for n in self.current_size_dist]
                    # self.current_size_dist.clear()
                    # for n in self.current_bin_counts:
                    #     self.current_size_dist.append(n/cm3)
                    # self.update_data_record(
                    #     dt,
                    #     # {'bin_concentration': self.current_size_dist}
                    #     {'bin_concentration': dist}
                    # )

                    # intN = 0
                    # # for n in self.current_size_dist:
                    # for n in dist:
                    #     intN += n
                    #     print(f'{n} - {intN}')
                    # self.update_data_record(
                    #     dt,
                    #     {'integral_concentration': intN}
                    # )

                    # calculate diameters
                    try:
                        min_dp = self.current_run_settings["min_diameter_sp"]
                    except KeyError:
                        min_dp = 10

                    param = self.get_data_record_param(dt, "actual_max_dp")
                    if not param:
                        try:
                            max_dp = self.current_run_settings["min_diameter_sp"]
                        except KeyError:
                            max_dp = 300
                    else:
                        max_dp = float(param)
                    dlogdp = math.pow(10, math.log10(max_dp / min_dp) / (30 - 1))
                    # dlogdp = dlogdp / (30-1)
                    diam = []
                    diam_um = []
                    diam.append(10)
                    diam_um.append(10 / 1000)
                    for x in range(1, 30):
                        dp = round(diam[x - 1] * dlogdp, 2)
                        diam.append(dp)
                        diam_um.append(round(dp / 1000, 3))

                    self.update_data_record(
                        dt,
                        {"diameter_nm": diam},
                    )

                    self.update_data_record(
                        dt,
                        {"diameter_um": diam_um},
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
                data.update(subject="DATA", body=entry)

                # reset read count
                self.current_read_cnt = 0
                self.scan_first_found = False
                self.scan_ready = False

                # await self.msg_buffer.put(data)
                # await self.to_parent_buf.put(data)
                # print(f'999999999999msems data: {data.to_json()}')
                # await asyncio.sleep(.1)
                await self.message_to_ui(data)
                await self.to_parent_buf.put(data)
                # await PlotManager.update_data(self.plot_name, data.to_json())
                if self.datafile:
                    await self.datafile.write_message(data)
            
            elif self.msems_mode == "off":
                # monitoring the data
                # print(f"monitor: {dt}")
                pass

            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)
        # elif type == "FromUI":
        #     if msg.subject == "STATUS" and msg.body["purpose"] == "REQUEST":
        #         print(f"msg: {msg.body}")
        #         self.send_status()

        #     elif msg.subject == "CONTROLS" and msg.body["purpose"] == "REQUEST":
        #         print(f"msg: {msg.body}")
        #         await self.set_control(msg.body["control"], msg.body["value"])

        #     elif msg.subject == "RUNCONTROLS" and msg.body["purpose"] == "REQUEST":

        #         print(f"msg: {msg.body}")
        #         await self.handle_control_action(msg.body["control"], msg.body["value"])
        await super().handle(msg, type)
        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        if control and value:
            # print(f"msems control action: {control}, {value}")
            if control == "start_stop":
                # if value == "START":
                #     self.start()
                # elif value == "STOP":
                #     self.stop()

                # self.set_control_att(control, "action_state", "OK")
                await super(MSEMS, self).handle_control_action(control, value)

            else:
                try:
                    # print(
                    #     f'send command to msems: {self.controls[control]["parse_label"]}={value}'
                    # )
                    if self.iface_components["default"]:
                        if_id = self.iface_components["default"]
                        cmd = f'{self.controls[control]["parse_label"]}={value}\n'
                        # print(f"msems control: {cmd.strip()}")
                        # cmd = "msems_mode=2\n"
                        msg = Message(
                            sender_id=self.get_id(),
                            msgtype=Instrument.class_type,
                            subject="SEND",
                            body=cmd,
                        )
                        await self.iface_map[if_id].message_from_parent(msg)

                    self.set_control_att(control, "action_state", "OK")
                except KeyError:
                    print(f"can't set {control}")
                    self.set_control_att(control, "action_state", "NOT_OK")
        # await super(MSEMS, self).handle(msg, type)

    def parse(self, msg):
        # print(f'parse: {msg.to_json()}')
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body["DATETIME"]

        line = msg.body["DATA"].rstrip().split()
        # if len(line) == 0:
        #     self.current_read_cnt += 1
        # else:
        parts = []
        for entry in line:
            if "=" in entry:
                parts=entry.split("=")
            # parts = line.split("=")
            if len(parts) < 2:
                return dt

            # self.scan_state = 999
            # if self.scan_run_state == 'STOPPING':
            #     if parts[0] == 'scan_state':
            #         self.scan_state = int(parts[1])
            # print(f"parse: {dt} {parts[0]}={parts[1]}")
            # print(f'77777777777777{parts[0]} = {parts[1]}')
            if parts[0] == "scan_state":
                self.scan_state = parts[1]
                print(f"scan state: {self.scan_state}")
                if self.scan_state == "4":
                    # print(f"reading scan data")
                    self.reading_scan = True
                    self.scan_ready = False
                    self.current_bin_counts.clear()
                    self.scan_time = dt

                else:
                    if self.reading_scan:
                        self.scan_ready = True
                    self.reading_scan = False
            if self.reading_scan:
                if parts[0] in self.parse_map:
                    self.update_data_record(
                        # dt,
                        self.scan_time,
                        {self.parse_map[parts[0]]: parts[1]},
                    )
                    # if self.scan_stop_param == parts[0]:
                    #     if self.scan_first_found:
                    #         self.scan_ready = True
                    #     else:
                    #         self.scan_ready = False
                    # elif self.scan_start_param == parts[0]:

                    #     # self.current_size_dist.clear()
                    #     self.scan_first_found = True
                    #     self.current_bin_counts.clear()
                elif parts[0].find("bin") >= 0:
                    self.current_bin_counts.append(float(parts[1]))
                    # self.current_size_dist.append(float(parts[1]))
                    # print(f"{parts[0]}={parts[1]}")
                    # print(f'{self.current_size_dist}')
                    # print(f"{self.current_bin_counts}")
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
        definition["module"] = MSEMS.__module__
        definition["name"] = MSEMS.__name__
        definition["mfg"] = "Brechtel"
        definition["model"] = "MSEMS"
        definition["type"] = "SizeDistribution"
        definition["tags"] = [
            "concentration",
            "particle",
            "aerosol",
            "physics",
            "brechtel",
            "bmi",
            "sizing",
            "size distribution",
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []
        dist_data = []

        # TODO: add interface entry for each measurement
        primary_meas_2d = dict()
        primary_meas_2d["bin_counts"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "um"],
            },
            "units": "count",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "bin_cnt",
            "parse_label": "bin",
            "control": None,
            "axes": {
                # 'TIME', 'datetime',
                "DIAMETER": "diameter_um",
            },
        }
        dist_data.append("bin_counts")

        primary_meas_2d["bin_concentration"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "um"],
            },
            "units": "cm-3",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "CALCULATED",
            "data_type": "NUMERIC",
            "short_name": "bin_conc",
            # 'parse_label': 'bin',
            "control": None,
            "axes": {
                # 'TIME', 'datetime',
                "DIAMETER": "diameter_um",
            },
        }
        dist_data.append("bin_concentration")

        primary_meas_2d["diameter_um"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "um"],
            },
            "units": "nm",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "CALCULATED",
            "data_type": "NUMERIC",
            "short_name": "dp",
            "parse_label": "diameter_um",
            "control": None,
            "axes": {
                # 'TIME', 'datetime',
                "DIAMETER": "diameter_um",
            },
        }
        dist_data.append("diameter_um")

        primary_meas_2d["diameter_nm"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "nm"],
            },
            "units": "nm",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "CALCULATED",
            "data_type": "NUMERIC",
            "short_name": "dp",
            "parse_label": "diameter",
            "control": None,
            "axes": {
                # 'TIME', 'datetime',
                "DIAMETER": "diameter_um",
            },
        }
        dist_data.append("diameter_nm")

        primary_meas = dict()
        primary_meas["integral_concentration"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "cm-3",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "CALCULATED",
            "data_type": "NUMERIC",
            "short_name": "int_conc",
            "parse_label": "int_conc",
            "control": None,
        }
        y_data.append("integral_concentration")

        process_meas = dict()
        process_meas["sems_date"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "date",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "sems_date",
            "parse_label": "scan_date",
            "control": None,
        }
        # y_data.append('sems_date')

        process_meas["sems_time"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "dateTime",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "parse_label": "scan_time",
            "control": None,
        }
        # y_data.append('counts')

        process_meas["scan_direction"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "scan_dir",
            "parse_label": "scan_direction",
            "control": None,
        }
        # y_data.append('condenser_temp')

        process_meas["actual_max_dp"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "nm",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "max_dp",
            "parse_label": "actual_max_dia",
            "control": "max_diameter_sp",
        }
        y_data.append("actual_max_dp")

        process_meas["max_volts"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "volts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            # 'short_name': 'sat_bot_temp',
            "parse_label": "scan_max_volts",
            "control": None,
        }
        y_data.append("max_volts")

        process_meas["min_volts"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "volts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            # 'short_name': 'opt_temp',
            "parse_label": "scan_min_volts",
            "control": None,
        }
        y_data.append("min_volts")

        process_meas["sheath_flow_avg"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "liters min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "sheath_avg",
            "parse_label": "sheath_flw_avg",
            "control": None,
        }
        y_data.append("sheath_flow_avg")

        process_meas["sheath_flow_sd"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "liters min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "sheath_sd",
            "parse_label": "sheath_flw_stdev",
            "control": None,
        }
        y_data.append("sheath_flow_sd")

        process_meas["sample_flow_avg"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "liters min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "sample_avg",
            "parse_label": "mcpc_smpf_avg",
            "control": None,
        }
        y_data.append("sample_flow_avg")

        process_meas["sample_flow_sd"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "liters min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "sample_sd",
            "parse_label": "mcpc_smpf_stdev",
            "control": None,
        }
        y_data.append("sample_flow_sd")

        process_meas["pressure_avg"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "mbar",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "press_avg",
            "parse_label": "press_avg",
            "control": None,
        }
        y_data.append("pressure_avg")

        process_meas["pressure_sd"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "mbar",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "press_sd",
            "parse_label": "press_stdev",
            "control": None,
        }
        y_data.append("pressure_sd")

        process_meas["temperature_avg"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_avg",
            "parse_label": "temp_avg",
            "control": None,
        }
        y_data.append("temperature_avg")

        process_meas["temperature_sd"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_sd",
            "parse_label": "temp_stdev",
            "control": None,
        }
        y_data.append("temperature_sd")

        process_meas["msems_error"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "parse_label": "msems_errs",
            "control": None,
        }
        y_data.append("msems_error")

        process_meas["mcpc_sample_flow"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "cm3 min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "mcpc_samp_flow",
            "parse_label": "mcpc_smpf",
            "control": None,
        }
        y_data.append("mcpc_sample_flow")

        process_meas["mcpc_saturator_flow"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "cm3 min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "mcpc_sat_flow",
            "parse_label": "mcpc_satf",
            "control": None,
        }
        y_data.append("mcpc_saturator_flow")

        process_meas["mcpc_condenser_temp"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "min_value": 0,
            "max_value": 50,
            "short_name": "mcpc_cond_temp",
            "parse_label": "mcpc_cndt",
            "control": None,
        }
        y_data.append("mcpc_condenser_temp")

        process_meas["mcpc_error"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "parse_label": "mcpc_errs",
            "control": None,
        }
        y_data.append("mcpc_error")

        # TODO: add settings controls
        controls = dict()
        controls["mcpc_power_control"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 1],
            "default_value": 0,
            "label": "MCPC power",
            "parse_label": "mcpcpwr",
            "control_group": "Power",
        }
        controls["mcpc_pump_power_control"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 1],
            "default_value": 0,
            "label": "MCPC pump power",
            "parse_label": "mcpcpmp",
            "control_group": "Power",
        }

        controls["sheath_flow_sp"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "liters min-1",
            "allowed_range": [0, 4],
            "default_value": 2.5,
            "label": "Sheath Flow",
            "parse_label": "sheath_sp",
            "control_group": "Flows",
        }
        y_data.append("sheath_flow_sp")

        # TODO: add settings controls
        controls["number_bins"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 100],
            "default_value": 30,
            "label": "Number of bins",
            "parse_label": "num_bins",
            "control_group": "Scan Settings",
        }
        controls["bin_time"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "sec",
            "allowed_range": [0.25, 60],
            "default_value": 1,
            "label": "Seconds per bin",
            "parse_label": "bin_time",
            "control_group": "Scan Settings",
        }

        controls["scan_type"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 2],
            "default_value": 0,
            "label": "Scan type",
            "parse_label": "scan_type",
            "control_group": "Scan Settings",
        }

        controls["max_diameter_sp"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "nm",
            "allowed_range": [10, 300],
            "default_value": 300,
            "label": "Max Dp",
            "parse_label": "scan_max_dia",
            "control_group": "Scan Settings",
        }

        controls["min_diameter_sp"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "nm",
            "allowed_range": [10, 300],
            "default_value": 10,
            "label": "Min Dp",
            "parse_label": "scan_min_dia",
            "control_group": "Scan Settings",
        }

        controls["plumbing_time"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "sec",
            "allowed_range": [0, 10],
            "default_value": 1.2,
            "label": "Plumbing time",
            "parse_label": "plumbing_time",
            "control_group": "Scan Settings",
        }

        controls["mcpc_a_installed"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 1],
            "default_value": 1,
            "label": "MCPC A installed",
            "parse_label": "mcpc_a_yn",
            "control_group": "Hardware Settings",
        }

        controls["mcpc_b_installed"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 1],
            "default_value": 00,
            "label": "MCPC B installed",
            "parse_label": "mcpc_b_yn",
            "control_group": "Hardware Settings",
        }

        controls["mcpc_b_flow_sp"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "liters min-1",
            "allowed_range": [0, 2],
            "default_value": 0.36,
            "label": "MCPC B flow",
            "parse_label": "mcpc_b_flw",
            "control_group": "Hardware Settings",
        }

        controls["sample_rh_installed"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 1],
            "default_value": 0,
            "label": "Sample RH installed",
            "parse_label": "samp_rh_yn",
            "control_group": "Hardware Settings",
        }

        controls["sheath_rh_installed"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 1],
            "default_value": 0,
            "label": "Sheath RH installed",
            "parse_label": "sheath_rh_yn",
            "control_group": "Hardware Settings",
        }

        controls["column_type"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [0, 2],
            "default_value": 1,
            "label": "Column type",
            "parse_label": "sheath_rh_yn",
            "control_group": "Hardware Settings",
        }

        controls["sheath_c2"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  -1562.3,
            "default_value": -5063.00,
            "label": "Sheath C2",
            "parse_label": "sheath_c2",
            "control_group": "Calibration",
        }

        controls["sheath_c1"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  1556.5,
            "default_value": 1454.50,
            "label": "Sheath C1",
            "parse_label": "sheath_c1",
            "control_group": "Calibration",
        }

        controls["sheath_c0"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  -5603.2,
            "default_value": -5773.00,
            "label": "Sheath C0",
            "parse_label": "sheath_c0",
            "control_group": "Calibration",
        }

        controls["cal_temp"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  27.2,
            "default_value": 30.6,
            "label": "Calibration T",
            "parse_label": "cal_temp",
            "control_group": "Calibration",
        }

        controls["imp_slope"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  2329,
            "default_value": 2329.5,
            "label": "Impactor slope",
            "parse_label": "impct_slp",
            "control_group": "Calibration",
        }

        controls["imp_offset"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  -679,
            "default_value": -935.7,
            "label": "Impactor offset",
            "parse_label": "impct_off",
            "control_group": "Calibration",
        }

        controls["pressure_slope"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  3885.9,
            "default_value": 3940.0,
            "label": "Pressure slope",
            "parse_label": "press_slp",
            "control_group": "Calibration",
        }

        controls["pressure_offset"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  -1266.3,
            "default_value": -1791.0,
            "label": "Pressure offset",
            "parse_label": "press_off",
            "control_group": "Calibration",
        }

        controls["hv_slope"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  1491.1,
            "default_value": 1494.0,
            "label": "HV slope",
            "parse_label": "hv_slope",
            "control_group": "Calibration",
        }

        controls["hv_offset"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            # 'default_value':  776.2,
            "default_value": 782.8,
            "label": "HV offset",
            "parse_label": "hv_offset",
            "control_group": "Calibration",
        }

        controls["ext_volts_slope"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            "default_value": 4841.0,
            "label": "ExtVolts slope",
            "parse_label": "ext_volts_slope",
            "control_group": "Calibration",
        }

        controls["ext_volts_offset"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": "counts",
            "allowed_range": [-65535, 65535],
            "default_value": -4713.0,
            "label": "ExtVolts offset",
            "parse_label": "ext_volts_offset",
            "control_group": "Calibration",
        }

        measurement_config["primary_2d"] = primary_meas_2d
        measurement_config["primary"] = primary_meas
        measurement_config["process"] = process_meas
        measurement_config["controls"] = controls

        definition["measurement_config"] = measurement_config

        plot_config = dict()

        size_dist = dict()
        size_dist["app_type"] = "SizeDistribution"
        size_dist["y_data"] = ["bin_concentration", "bin_counts", "diameter_um"]
        size_dist["default_y_data"] = ["bin_concentration"]
        source_map = {
            "default": {
                "y_data": {"default": ["bin_concentration", "diameter_um"]},
                "default_y_data": ["bin_concentration"],
            },
        }
        size_dist["source_map"] = source_map

        time_series1d = dict()
        time_series1d["app_type"] = "TimeSeries1D"
        time_series1d["y_data"] = y_data
        time_series1d["default_y_data"] = ["integral_concentration"]
        source_map = {
            "default": {
                "y_data": {"default": y_data},
                "default_y_data": ["integral_concentration"],
            },
        }
        time_series1d["source_map"] = source_map

        # size_dist['dist_data'] = dist_data
        # size_dist['default_dist_data'] = ['size_distribution']

        plot_config["plots"] = dict()
        plot_config["plots"]["raw_size_dist"] = size_dist
        plot_config["plots"]["main_ts1d"] = time_series1d
        definition["plot_config"] = plot_config

        return {"DEFINITION": definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition
