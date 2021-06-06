from datetime import datetime

import pytz
from daq.instrument.instrument import Instrument
from shared.data.message import Message
from shared.data.status import Status
import asyncio
from shared.utilities.util import time_to_next, string_to_dt, dt_to_string
from daq.interface.interface import Interface


class ADInstrument(Instrument):

    INSTANTIABLE = False

    def __init__(self, config, **kwargs):

        super(ADInstrument, self).__init__(config, **kwargs)

        self.mfg = "AerosolDevices"

    def setup(self):
        super().setup()

        # TODO: add properties get/set to interface for
        #       things like readmethod


class MAGIC210(ADInstrument):
    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        super(MAGIC210, self).__init__(config, **kwargs)

        self.name = "MAGIC210"
        self.model = "210"
        self.tag_list = [
            "concentration",
            "aerosol",
            "physics",
        ]

        self.iface_meas_map = None
        self.polling_task = None

        # override how often metadata is sent
        self.include_metadata_interval = 300

        # this instrument appears to work with readline
        # self.iface_options = {
        #     'read_method': 'readuntil',
        #     'read_terminator': '\r',
        # }
        self.setup()

    # def get_datafile_config(self):
    #     config = super().get_datafile_config()
    #     config["save_interval"] = 0
    #     return config

    def setup(self):
        super().setup()

        # default coms:
        # Baud rate: 115200
        # Bits: 8
        # Stop bits: 1
        # Parity: none
        # Flow Control: none

        self.iface = None
        if self.iface_components["default"]:
            if_id = self.iface_components["default"]
            self.iface = self.iface_map[if_id]
        else:
            self.iface = next(iter(self.iface_map.values()))

        self.is_polled = False
        # self.poll_rate = 2  # every second
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

        self.status["ready_to_run"] = True
        self.status2.set_run_status(Status.READY_TO_RUN)
        self.enable()

        print("done")

    async def shutdown(self):
        self.stop()
        self.disable()
        await self.deregister_from_UI()
        await super().shutdown()

    def enable(self):

        super().enable()

        # # if self.is_polled:
        # self.polling_task = asyncio.create_task(self.poll_loop())
        # asyncio.create_task(self.toggle_mcpc_power(power=0))

    def disable(self):
        # asyncio.create_task(self.toggle_mcpc_power(power=0))
        # if self.polling_task:
        #     self.polling_task.cancel()
        super().disable()

    def start(self, cmd=None):
        super().start()
        asyncio.create_task(self.start_logging)

    async def start_logging(self):

        if self.iface:
        # if self.iface_components["default"]:
        #     if_id = self.iface_components["default"]
        #     self.current_read_cnt = 0
        #     await asyncio.sleep(0.1)

            # Start logging
            cmd = "Log,1\n"
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
                subject="SEND",
                body=cmd,
            )
            # print(f'msg: {msg}')
            # await self.iface.message_from_parent(msg)
            # await self.iface_map[if_id].message_from_parent(msg)
            await self.iface.message_from_parent(msg)


        # TODO: Send start command:
        # Log,1 <- Starts sending data every second

    async def stop_logging(self):

        if self.iface:
        # if self.iface_components["default"]:
        #     if_id = self.iface_components["default"]
        #     self.current_read_cnt = 0
        #     await asyncio.sleep(0.1)

            # Start logging
            cmd = "Log,0\n"
            msg = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
                subject="SEND",
                body=cmd,
            )
            # print(f'msg: {msg}')
            # await self.iface.message_from_parent(msg)
            # await self.iface_map[if_id].message_from_parent(msg)
            await self.iface.message_from_parent(msg)



    def stop(self, cmd=None):

        # TODO: Send start command:
        # Log,0 <- Stops sending data
        asyncio.create_task(self.stop_logging())
        super().stop()

    async def handle(self, msg, type=None):

        # print(f'%%%%% MAGIC210.handle: {msg.to_json()}')
        if type == "FromChild" and msg.type == Interface.class_type:
            dt = self.parse(msg)
            # print(f'dt = {dt}')
            if dt:

                entry = self.get_data_entry(dt)

                data = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                )
                data.update(subject="DATA", body=entry)

                await self.message_to_ui(data)

        await super().handle(msg, type)

    async def handle_control_action(self, control, value):
        if control and value is not None:
            if control == "start_stop":
                await super(MAGIC210, self).handle_control_action(control, value)

    def parse(self, msg):
        # print(f'parse: {msg}')
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body["DATETIME"]
        if dt:
            line = msg.body["DATA"].strip()

            params = line.split(",")
            if len(params) < 23:
                return None

            labels = [
                "magic_datetime",
                "concentration",  # 1
                "dew_pt_inlet",
                "temperature_inlet",
                "rh_inlet",
                "temperature_conditioner",
                "temperature_initiator",
                "temperature_moderator",
                "temperature_optics",
                "temperature_heatsink",
                "temperature_pcb",
                "temperature_cabinet",
                "ps_voltage",
                "diff_pressure",
                "pressure",
                "sample_flow",
                "interval_time",  # 16
                "live_time",
                "dead_time",
                "raw_counts_lower",
                "raw_counts_higher",
                "error",
                "error_string",
                "serial_number",
            ]

            # TODO parse magic_dt
            dts = params[0]
            try:
                # dt = datetime.strptime(magic_dt,'%Y/%m/%d %H:%M:%S')
                # pytz.utc.localize(dt)
                tmp_dt = string_to_dt(dts, format='%Y/%m/%d %H:%M:%S')
                magic_dt = dt_to_string(tmp_dt)
            except ValueError:
                magic_dt = ""
            self.update_data_record(dt, {"magic_datetime": magic_dt})

            for i in range(1, 16):
                val = float(params[i])
                self.update_data_record(dt, {labels[i]: round(val, 3)})

            # interval_time
            val = int(params[16])
            self.update_data_record(dt, {labels[16]: val})

            # live/dead times
            val = int(params[17])
            self.update_data_record(dt, {labels[17]: val})
            val = int(params[18])
            self.update_data_record(dt, {labels[18]: val})

            # raw_counts
            val = int(params[19])
            self.update_data_record(dt, {labels[19]: val})
            val = int(params[20])
            self.update_data_record(dt, {labels[20]: val})

            # error
            val = int(params[21])
            self.update_data_record(dt, {labels[21]: val})

            # error_string
            self.update_data_record(dt, {labels[22]: params[22]})

            # s/n
            val = int(params[23])
            self.update_data_record(dt, {labels[23]: val})

        return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return MAGIC210.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition["module"] = MAGIC210.__module__
        definition["name"] = MAGIC210.__name__
        definition["mfg"] = "AerosolDevices"
        definition["model"] = "210"
        definition["type"] = "ParticleConcentration"
        definition["tags"] = [
            "concentration",
            "particle",
            "aerosol",
            "physics",
            "aerosoldevices",
            "ad",
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []

        # TODO: add interface entry for each measurement

        primary_meas = dict()
        primary_meas["concentration"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "cm-3",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "conc",
            "parse_label": "conc",
            "control": None,
        }
        y_data.append("concentration")

        process_meas = dict()
        process_meas["dew_pt_inlet"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "dewpt_in",
            "control": None,
        }
        y_data.append("dew_pt_inlet")

        process_meas["temperature_inlet"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_in",
            "control": None,
        }
        y_data.append("temperature_inlet")

        process_meas["rh_inlet"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "%",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "rh_in",
            "control": None,
        }
        y_data.append("rh_inlet")

        process_meas["temperature_conditioner"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_cond",
            "control": None,
        }
        y_data.append("temperature_conditioner")

        process_meas["temperature_initiator"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_ini",
            "control": None,
        }
        y_data.append("temperature_initiator")

        process_meas["temperature_moderator"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_mod",
            "control": None,
        }
        y_data.append("temperature_moderator")

        process_meas["temperature_optics"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_opt",
            "control": None,
        }
        y_data.append("temperature_optics")

        process_meas["temperature_heatsink"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_hsk",
            "control": None,
        }
        y_data.append("temperature_heatsink")

        process_meas["temperature_pcb"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_pcb",
            "control": None,
        }
        y_data.append("temperature_pcb")

        process_meas["temperature_cabinet"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "temp_cab",
            "control": None,
        }
        y_data.append("temperature_cabinet")

        process_meas["ps_voltage"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "volts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "ps_v",
            "control": None,
        }
        y_data.append("ps_voltage")

        process_meas["diff_pressure"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "mb",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "dpress",
            "control": None,
        }
        y_data.append("diff_pressure")

        process_meas["pressure"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "mb",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "press",
            "control": None,
        }
        y_data.append("pressure")

        process_meas["sample_flow"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "cm3 min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "samp_flow",
            "control": None,
        }
        y_data.append("sample_flow")

        process_meas["interval_time"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "sec",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "intv_time",
            "control": None,
        }
        y_data.append("interval_time")

        process_meas["live_time"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "live_time",
            "control": None,
        }
        y_data.append("live_time")

        process_meas["dead_time"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "dead_time",
            "control": None,
        }
        y_data.append("dead_time")

        process_meas["raw_counts_lower"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "raw_cnts_lo",
            "control": None,
        }
        y_data.append("raw_counts_lower")

        process_meas["raw_counts_higher"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "raw_cnts_hi",
            "control": None,
        }
        y_data.append("raw_counts_higher")

        process_meas["error"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "parse_label": "err",
            "control": None,
        }
        y_data.append("error")

        process_meas["error_string"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "string",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "err_string",
            "control": None,
        }
        # y_data.append("mcpc_sample_flow")
        
        info_meas = dict()
        info_meas['magic_datetime'] = {
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

        info_meas["serial_number"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "ser_num",
            "control": None,
        }

        # y_data.append('pops_datetime')

        # y_data.append("mcpc_saturator_flow")

        # TODO: add settings controls
        controls = dict()
        # controls["mcpc_power_control"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 1],
        #     "default_value": 0,
        #     "label": "MCPC power",
        #     "parse_label": "mcpcpwr",
        #     "control_group": "Power",
        # }
        # controls["mcpc_pump_power_control"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 1],
        #     "default_value": 0,
        #     "label": "MCPC pump power",
        #     "parse_label": "mcpcpmp",
        #     "control_group": "Power",
        # }

        # controls["sheath_flow_sp"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "liters min-1",
        #     "allowed_range": [0, 4],
        #     "default_value": 2.5,
        #     "label": "Sheath Flow",
        #     "parse_label": "sheath_sp",
        #     "control_group": "Flows",
        # }
        # y_data.append("sheath_flow_sp")

        # # TODO: add settings controls
        # controls["number_bins"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 100],
        #     "default_value": 30,
        #     "label": "Number of bins",
        #     "parse_label": "num_bins",
        #     "control_group": "Scan Settings",
        # }
        # controls["bin_time"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "sec",
        #     "allowed_range": [0.25, 60],
        #     "default_value": 1,
        #     "label": "Seconds per bin",
        #     "parse_label": "bin_time",
        #     "control_group": "Scan Settings",
        # }

        # controls["scan_type"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 2],
        #     "default_value": 0,
        #     "label": "Scan type",
        #     "parse_label": "scan_type",
        #     "control_group": "Scan Settings",
        # }

        # controls["max_diameter_sp"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "nm",
        #     "allowed_range": [10, 300],
        #     "default_value": 300,
        #     "label": "Max Dp",
        #     "parse_label": "scan_max_dia",
        #     "control_group": "Scan Settings",
        # }

        # controls["min_diameter_sp"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "nm",
        #     "allowed_range": [10, 300],
        #     "default_value": 10,
        #     "label": "Min Dp",
        #     "parse_label": "scan_min_dia",
        #     "control_group": "Scan Settings",
        # }

        # controls["plumbing_time"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "sec",
        #     "allowed_range": [0, 10],
        #     "default_value": 1.2,
        #     "label": "Plumbing time",
        #     "parse_label": "plumbing_time",
        #     "control_group": "Scan Settings",
        # }

        # controls["mcpc_a_installed"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 1],
        #     "default_value": 1,
        #     "label": "MCPC A installed",
        #     "parse_label": "mcpc_a_yn",
        #     "control_group": "Hardware Settings",
        # }

        # controls["mcpc_b_installed"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 1],
        #     "default_value": 00,
        #     "label": "MCPC B installed",
        #     "parse_label": "mcpc_b_yn",
        #     "control_group": "Hardware Settings",
        # }

        # controls["mcpc_b_flow_sp"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "liters min-1",
        #     "allowed_range": [0, 2],
        #     "default_value": 0.36,
        #     "label": "MCPC B flow",
        #     "parse_label": "mcpc_b_flw",
        #     "control_group": "Hardware Settings",
        # }

        # controls["sample_rh_installed"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 1],
        #     "default_value": 0,
        #     "label": "Sample RH installed",
        #     "parse_label": "samp_rh_yn",
        #     "control_group": "Hardware Settings",
        # }

        # controls["sheath_rh_installed"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 1],
        #     "default_value": 0,
        #     "label": "Sheath RH installed",
        #     "parse_label": "sheath_rh_yn",
        #     "control_group": "Hardware Settings",
        # }

        # controls["column_type"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [0, 2],
        #     "default_value": 1,
        #     "label": "Column type",
        #     "parse_label": "sheath_rh_yn",
        #     "control_group": "Hardware Settings",
        # }

        # controls["sheath_c2"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  -1562.3,
        #     "default_value": -5063.00,
        #     "label": "Sheath C2",
        #     "parse_label": "sheath_c2",
        #     "control_group": "Calibration",
        # }

        # controls["sheath_c1"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  1556.5,
        #     "default_value": 1454.50,
        #     "label": "Sheath C1",
        #     "parse_label": "sheath_c1",
        #     "control_group": "Calibration",
        # }

        # controls["sheath_c0"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  -5603.2,
        #     "default_value": -5773.00,
        #     "label": "Sheath C0",
        #     "parse_label": "sheath_c0",
        #     "control_group": "Calibration",
        # }

        # controls["cal_temp"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  27.2,
        #     "default_value": 30.6,
        #     "label": "Calibration T",
        #     "parse_label": "cal_temp",
        #     "control_group": "Calibration",
        # }

        # controls["imp_slope"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  2329,
        #     "default_value": 2329.5,
        #     "label": "Impactor slope",
        #     "parse_label": "impct_slp",
        #     "control_group": "Calibration",
        # }

        # controls["imp_offset"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  -679,
        #     "default_value": -935.7,
        #     "label": "Impactor offset",
        #     "parse_label": "impct_off",
        #     "control_group": "Calibration",
        # }

        # controls["pressure_slope"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  3885.9,
        #     "default_value": 3940.0,
        #     "label": "Pressure slope",
        #     "parse_label": "press_slp",
        #     "control_group": "Calibration",
        # }

        # controls["pressure_offset"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  -1266.3,
        #     "default_value": -1791.0,
        #     "label": "Pressure offset",
        #     "parse_label": "press_off",
        #     "control_group": "Calibration",
        # }

        # controls["hv_slope"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  1491.1,
        #     "default_value": 1494.0,
        #     "label": "HV slope",
        #     "parse_label": "hv_slope",
        #     "control_group": "Calibration",
        # }

        # controls["hv_offset"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     # 'default_value':  776.2,
        #     "default_value": 782.8,
        #     "label": "HV offset",
        #     "parse_label": "hv_offset",
        #     "control_group": "Calibration",
        # }

        # controls["ext_volts_slope"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     "default_value": 4841.0,
        #     "label": "ExtVolts slope",
        #     "parse_label": "ext_volts_slope",
        #     "control_group": "Calibration",
        # }

        # controls["ext_volts_offset"] = {
        #     "data_type": "NUMERIC",
        #     # units are tied to parameter this controls
        #     "units": "counts",
        #     "allowed_range": [-65535, 65535],
        #     "default_value": -4713.0,
        #     "label": "ExtVolts offset",
        #     "parse_label": "ext_volts_offset",
        #     "control_group": "Calibration",
        # }

        measurement_config["primary"] = primary_meas
        measurement_config["process"] = process_meas
        # measurement_config["controls"] = controls

        definition["measurement_config"] = measurement_config

        plot_config = dict()

        time_series1d = dict()
        time_series1d["app_type"] = "TimeSeries1D"
        time_series1d["y_data"] = y_data
        time_series1d["default_y_data"] = ["concentration"]
        source_map = {
            "default": {
                "y_data": {"default": y_data},
                "default_y_data": ["concentration"],
            },
        }
        time_series1d["source_map"] = source_map

        # size_dist['dist_data'] = dist_data
        # size_dist['default_dist_data'] = ['size_distribution']

        plot_config["plots"] = dict()
        plot_config["plots"]["main_ts1d"] = time_series1d
        definition["plot_config"] = plot_config

        return {"DEFINITION": definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition
