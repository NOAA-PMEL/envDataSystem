import abc
import importlib
import copy
import random
from daq.daq import DAQ
import asyncio
from shared.data.message import Message
from shared.data.status import Status
from shared.utilities.util import time_to_next
from daq.interface.interface import Interface, InterfaceFactory


class InstrumentFactory:
    @staticmethod
    def create(config, **kwargs):
        create_cfg = config["INSTRUMENT"]
        instconfig = config["INSTCONFIG"]
        alias = None
        if "ALIAS" in config:
            alias = config["ALIAS"]
        namespace = None
        if "namespace" in config:
            namespace = config["namespace"]
        # print("module: " + create_cfg['MODULE'])
        # print("class: " + create_cfg['CLASS'])

        try:
            # print('Creating: ' + config['name'])
            # print('   ClassName: ' + config['class'])
            mod_ = importlib.import_module(create_cfg["MODULE"])
            cls_ = getattr(mod_, create_cfg["CLASS"])
            # inst_class = eval(config['class'])
            # return inst_class.factory_create()
            return cls_(instconfig, alias=alias, namespace=namespace, **kwargs)

        # TODO: create custom exception class for our app
        # except ImportError:
        except Exception as e:  # better to catch ImportException?
            print(f"Instrument: Unexpected error: {e}")
            raise e
            # raise ImportError


class Instrument(DAQ):

    class_type = "INSTRUMENT"

    def __init__(self, config, alias=None, **kwargs):

        super(Instrument, self).__init__(config, **kwargs)

        # TODO: Need some way of specifying "standard"
        #       measurements (inherit from second class?)
        print("init Instrument")
        # self.config = config
        print(self.config)

        self.name = "Instrument"
        self.type = "Generic"
        self.label = self.config["DESCRIPTION"]["LABEL"]
        self.mfg = None
        self.model = None

        self.alias = dict()
        if alias:
            self.alias = alias

        self.plot_name = "/default_plot"
        self.plot_list = []

        self.serial_number = self.config["DESCRIPTION"]["SERIAL_NUMBER"]
        self.property_number = self.config["DESCRIPTION"]["PROPERTY_NUMBER"]

        # self.iface_send_buffer = None
        # self.iface_rcv_buffer = None
        self.iface_map = {}

        self.meas_map = {}
        self.measurements = dict()
        self.measurements["meta"] = dict()
        self.measurements["measurement_sets"] = dict()

        self.iface_test = None

        # add instrument specific options for iface, ifdev, client
        self.iface_options = {}

        self.data_record_template = dict()
        self.data_record = dict()

        # temporary
        self.last_entry = {"DATETIME": ""}

        # self.namespace['instrument'] = f"{self.label}".replace(" ", "")
        # if self.alias and ("name" in self.alias):
        #     self.namespace['instrument'] = f"{self.alias['name']}".replace(" ", "")

        self.keepalive_ping = True

        # # parameters to include metadata in output
        # self.include_metadata = True
        # # set interval to 0 to always send metadata
        # self.include_metadata_interval = 60

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

    # def get_datafile_config(self):
    #     config = {
    #         'base_path': self.get_base_filepath(),
    #     }
    #     return config

    # def get_base_filepath(self):
    #     system_base = '/home/horton/derek/tmp/envDataSystem/'
    #     inst_base = 'instrument/'
    #     definition = self.get_definition_instance()
    #     inst_base += definition['DEFINITION']['type']+'/'
    #     inst_base += definition['DEFINITION']['mfg']+'/'
    #     inst_base += definition['DEFINITION']['model']+'_'
    #     inst_base += self.serial_number+'/'

    #     return system_base+inst_base

    def setup(self):
        super().setup()
        # print(f'*******instrument.setup')
        self.add_interfaces()

        # add measurements
        self.add_measurements()
        # meta = self.get_metadata()
        # # tell ui to build instrument

        self.get_current_run_settings()

        # # add namespace to metadata
        # meta['namespace'] = self.namespace

        # # TODO: how to pass config and data to PlotApp: custom meta or
        # #       what we are using now? How do we specify defaults
        # # plot_config = dict()
        # # plot_config['name'] = '/instrument_'+meta['alias']['name']
        # # plot_data = dict()

        # # use current meta

        # # TODO: implement last_config

        # # for now, set controls to default
        # if 'measurement_meta' in meta:
        #     if 'controls' in meta['measurement_meta']:
        #         controls = meta['measurement_meta']['controls']
        #         for control, config in controls.items():
        #             if 'default_value' in config:
        #                 # TODO: on start, have to go through and send all
        #                 #       control values to instrument
        #                 self.set_control_att(
        #                     control, 'value', config['default_value']
        #                 )

        # # add dictionary specifying which measurements go with which plot
        # # if there are more than one.

        # # plot_config['data'] = plot_data

        # # print(f'{meta["plot_meta"]}')
        # # print(f'{meta["plot_meta"]["name"]}')
        # # TODO: move this to actual instrument
        # # # add plots to PlotServer

        # # TESTING: moving this to django side
        # # PlotManager.add_app(
        # #     TimeSeries1D(
        # #         meta,
        # #         # name=('/instrument_'+meta['plot_meta']['name'])
        # #         name=(meta['plot_meta']['name'])
        # #     ),
        # #     start_after_add=False
        # # )

        # print(f"app_name: {meta['plot_meta']['name']}")
        # meta['plot_app'] = {
        #     'name': (meta['plot_meta']['name'])
        # }

        # tell ui to build instrument
        if False:
            self.send_config_to_ui()
        # msg = Message(
        #     sender_id=self.get_id(),
        #     msgtype='Instrument',
        #     subject='CONFIG',
        #     body={
        #         'purpose': 'SYNC',
        #         'type': 'INSTRUMENT_INSTANCE',
        #         'data': meta
        #     }
        # )
        # self.message_to_ui_nowait(msg)
        # print(f'setup: {msg.body}')

        # Ready to start
        # self.status['ready_to_run'] = True
        # self.status2.set_run_status(Status.READY_TO_RUN)
        # self.enable()

    # def add_plot_app(self, plot_typ):

    #     meta = self.get_metadata()

    #     # if plot_type == 'TimeSeries1D':

    def resend_config_to_ui(self):

        self.send_config_to_ui()

        # for k, inst in self.instrument_map.items():
        #     inst.resend_config_to_ui()

    def send_config_to_ui(self):

        meta = self.get_metadata()

        # add namespace to metadata
        meta["namespace"] = self.namespace

        # for now, set controls to default
        if "measurement_meta" in meta:
            if "controls" in meta["measurement_meta"]:
                controls = meta["measurement_meta"]["controls"]
                for control, config in controls.items():
                    if "default_value" in config:
                        # TODO: on start, have to go through and send all
                        #       control values to instrument
                        self.set_control_att(control, "value", config["default_value"])

        # print(f"app_name: {meta['plot_meta']['name']}")
        # plot_app_name = ('/instrument_'+meta['plot_meta']['name'])
        # plot_app_name = self.add_plot_app()
        # if plot_app_name:
        meta["plot_app"] = {
            # 'name': ('/instrument_'+meta['plot_meta']['name'])
            "name": (meta["plot_meta"]["name"])
        }

        msg = Message(
            sender_id=self.get_id(),
            msgtype="Instrument",
            subject="CONFIG",
            body={"purpose": "SYNC", "type": "INSTRUMENT_INSTANCE", "data": meta},
        )
        self.message_to_ui_nowait(msg)

    def get_ui_address(self):
        # print(self.label)
        # print(f'instrument.get_ui_address: {self}')
        # print(f'inst.get_ui_address: {self.alias}, {self.namespace}, {self}')
        # if self.alias and ('name' in self.alias):
        #     # print(f'self.alias: {self.alias}')
        #     address = 'envdaq/instrument/'+self.alias['name']+'/'
        # else:
        #     address = 'envdaq/instrument/'+self.label+'/'

        address_parts = [
            # "envdaq",
            # self.namespace['daq_server'],
            # self.namespace['controller'],
            # "instrument",
            # self.namespace['instrument'],
            # ""
            "envdaq",
            f"{self.namespace.get_host()}",
            f"{self.namespace.get_namespace_sig(section='PARENT')['namespace']}",
            "instrument",
            f"{self.namespace.get_namespace_sig(section='LOCAL')['namespace']}",
            "",
        ]
        address = "/".join(address_parts)
        # address = f"envdaq/{self.namespace['daq_server']}/{self.namespace['controller']/instrument/{self.namespace['instrument']}/"
        return address

    # def connect(self, cmd=None):
    #     pass

    async def register_with_UI(self):

        # ui_config = self.ui_config
        # ui_ws_address = f'ws://{ui_config["host"]}:{ui_config["port"]}/'
        # ui_ws_address += "ws/envdaq/daqserver/register"

        # self.reg_client = WSClient(uri=ui_ws_address)
        # while self.reg_client.isConnected() is not True:
        #     # print(f'waiting for is_conncted {self.ui_client.isConnected()}')
        #     # self.gui_client = WSClient(uri=gui_ws_address)
        #     # print(f"gui client: {self.gui_client.isConnected()}")
        #     await asyncio.sleep(1)

        req = Message(
            sender_id=self.get_id(),
            msgtype=Instrument.class_type,
            subject="REGISTRATION",
            body={
                "purpose": "ADD",
                "regkey": self.registration_key,
                # "id": self.daq_id,
                "namespace": self.namespace.to_dict(),
                "config": self.config,
                "metadata": self.get_metadata(),
                "status": self.status2.to_dict(),
            },
        )
        print(f"Registering with UI server: {self.namespace.to_dict()}")
        await self.to_ui_buf.put(req)
        self.run_state = "REGISTERING"
        self.status2.set_registration_status(Status.REGISTERING)
        # await reg_client.close()

    async def deregister_from_UI(self):

        # ui_config = self.ui_config
        # ui_ws_address = f'ws://{ui_config["host"]}:{ui_config["port"]}/'
        # ui_ws_address += "ws/envdaq/daqserver/register"

        # self.reg_client = WSClient(uri=ui_ws_address)
        # while self.reg_client.isConnected() is not True:
        #     # print(f'waiting for is_conncted {self.ui_client.isConnected()}')
        #     # self.gui_client = WSClient(uri=gui_ws_address)
        #     # print(f"gui client: {self.gui_client.isConnected()}")
        #     await asyncio.sleep(1)

        req = Message(
            sender_id=self.get_id(),
            msgtype=Instrument.class_type,
            subject="REGISTRATION",
            body={
                "purpose": "REMOVE",
                "regkey": self.registration_key,
                # "id": self.daq_id,
                "namespace": self.namespace.to_dict(),
                # "config": self.config,
            },
        )
        print(f"Unregistering with UI server: {self.namespace.to_dict()}")
        await self.to_ui_buf.put(req)
        self.run_state = "UNREGISTERING"
        self.status2.set_run_status(Status.UNREGISTERING)
        # await reg_client.close()

    def get_data_entry(self, timestamp, force_add_meta=False):
        # print(f'timestamp: {timestamp}')
        entry = {
            # 'METADATA': self.get_metadata(),
            "DATA": {
                "DATETIME": timestamp,
                "MEASUREMENTS": self.get_data_record(timestamp),
            },
        }
        # add data request list for ui to use
        entry["DATA_REQUEST_LIST"] = self.data_request_list

        if self.include_metadata or force_add_meta:
            entry["METADATA"] = self.get_metadata()
            self.include_metadata = False

        if len(self.alias) > 0:
            entry["alias"] = self.alias

        return entry

    def get_data_record(self, timestamp):
        if timestamp in self.data_record:
            return self.data_record.pop(timestamp)

        return None

    def get_data_record_param(self, timestamp, name):
        if timestamp in self.data_record and name in self.data_record[timestamp]:
            return self.data_record[timestamp][name]["VALUE"]

    def update_data_record(
        self,
        timestamp,
        data,
        dataset="primary",
    ):
        """
        Update data records dictionary using timestamp as
        key value.

        Parameters:

        timestamp(str): string representation of timestamp
            format: YYYY-MM-DDThh:mm:ssZ

        data(dict): dictionary of measurement(s)
            format: {meas_name: val, ...}

        dataset(str): dataset to store data in

        Returns:

        nothing
        """

        if not self.data_record:
            self.data_record = dict()

        if timestamp not in self.data_record:
            # create blank data record
            self.data_record[timestamp] = copy.deepcopy(self.data_record_template)
            # if dataset not in self.data_record[timestamp]:
            #     for label, name in self.parse_map.items():
            #         self.data_record[timestamp][name] = None

        for name, value in data.items():
            # print(f'{name} = {value}')
            # self.data_record[timestamp][dataset][name] = value
            try:
                self.data_record[timestamp][name] = {"VALUE": value}
            except KeyError:
                pass

        while len(self.data_record) > 5:
            least = "9999-99-99T23:59:59Z"
            for k, v in self.data_record.items():
                if k < least:
                    least = k
            try:
                self.data_record.pop(least)
            except Exception:
                print("update exception")
                pass

    async def send_metadata_loop(self):

        while True:
            if self.include_metadata_interval > 0:
                # wt = utilities.util.time_to_next(
                #     self.include_metadata_interval
                # )
                # print(f'wait time: {wt}')
                await asyncio.sleep(time_to_next(self.include_metadata_interval))
                self.include_metadata = True
            else:
                self.include_metadata = True
                asyncio.sleep(1)

    def enable(self):
        super().enable()
        for k, iface in self.iface_map.items():
            iface.enable()

    def disable(self):
        print("ifdevice disable disable ifaces")
        for k, iface in self.iface_map.items():
            iface.disable()
        print("ifdevice disable super")
        super().disable()

    def start(self, cmd=None):
        # task = asyncio.ensure_future(self.read_loop())
        print(f"Starting Instrument {self}")
        super().start(cmd)

        self.open_datafile()
        # self.datafile = DataFile(
        #     # base_path=self.get_base_filepath(),
        #     config=self.get_datafile_config()
        # )
        # if self.datafile:
        #     self.datafile.open()

        # task = asyncio.ensure_future(self.from_child_loop())
        # self.task_list.append(task)

        # for k, iface in self.iface_map.items():
        #     iface.start()

    def stop(self, cmd=None):
        # print("Instrument.stop()")

        if self.datafile:
            self.datafile.close()

        for k, iface in self.iface_map.items():
            iface.stop()

        super().stop(cmd)

    async def shutdown(self):

        # for k, iface in self.iface_map.items():
        #     await iface.shutdown()

        await super().shutdown()

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
    async def handle(self, msg, type=None):
        await super(Instrument, self).handle(msg, type)

    async def handle_control_action(self, control, value):
        await super(Instrument, self).handle_control_action(control, value)

    def get_signature(self):
        # This will combine instrument metadata to generate
        #   a unique # ID
        return self.name + ":" + self.label + ":"
        +self.serial_number + ":" + self.property_number

    # def create_msg_buffers(self, config):
    #     # self.read_buffer = MessageBuffer(config=config)
    #     self.iface_send_buffer = asyncio.Queue(loop=self.loop)
    #     self.iface_rcv_buffer = asyncio.Queue(loop=self.loop)

    def add_interfaces(self):

        print("Add interfaces")
        # for now, single interface but eventually loop
        # through configured interfaces
        # list = self.config['IFACE_LIST']
        cfg_comps = None
        self.iface_components = dict()
        # print(f'config = {self.config["IFACE_LIST"]}')
        if "IFACE_MAP" in self.config:
            cfg_comps = self.config["IFACE_MAP"]
        print(f"self.iface_options = {self.iface_options}")
        for k, ifcfg in self.config["IFACE_LIST"].items():
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            # print(ifcfg['INTERFACE'])
            # iface = InterfaceFactory().create(ifcfg['IFACE_CONFIG'])
            iface = InterfaceFactory().create(
                ifcfg, ui_config=self.ui_config, **self.iface_options
            )
            print(f"iface: {k}: {iface}")
            # iface.msg_buffer = self.iface_rcv_buffer
            # iface.msg_send_buffer = self.from_child_buf
            iface.to_parent_buf = self.from_child_buf
            self.iface_map[iface.get_id()] = iface
            if cfg_comps:
                for comp, label in cfg_comps.items():
                    if label == k:
                        self.iface_components[comp] = iface.get_id()
            else:
                self.iface_components["default"] = iface.get_id()
            print(f"iface_map: {self.iface_map}")
            print(f"iface_comp: {self.iface_components}")

    def get_metadata(self):

        # print(f'**** get_metadata: {self}')

        # TODO: force alias or do a better job of defaults
        if len(self.alias) == 0:
            self.alias["name"] = self.label.replace(" ", "")
            self.alias["prefix"] = self.label.replace(" ", "")

        meta = {
            "NAME": self.name,
            "TYPE": self.type,
            "LABEL": self.label,
            "MFG": self.mfg,
            "MODEL": self.model,
            "SERIAL_NUMBER": self.serial_number,
            "property_number": self.property_number,
            "measurement_meta": self.measurements["meta"],
            "plot_meta": self.get_plot_meta(),
            "alias": self.alias,
            "namespace": self.namespace.to_dict(),
            "ID": self.get_id(),
        }
        return meta

    def get_plot_meta(self):

        definition = self.get_definition_instance()
        if "plot_config" not in definition["DEFINITION"]:
            return dict()

        plot_config = definition["DEFINITION"]["plot_config"]

        self.plot_list.clear()
        if "plots" in plot_config:
            for plot_name, plot_def in plot_config["plots"].items():
                # replace default id w/ instance id
                # TODO: this is req but add feedback if missing
                if "source_map" in plot_def:
                    if "default" in plot_def["source_map"]:

                        plot_def["source_map"][self.get_id()] = plot_def[
                            "source_map"
                        ].pop("default")

                        plot_def["source_map"][self.get_id()]["alias"] = self.alias

                        mm = "measurement_meta"
                        plot_def["source_map"][self.get_id()][mm] = self.measurements[
                            "meta"
                        ]

                app_name = "/instrument_" + self.alias["name"] + "_" + plot_name
                plot_config["plots"][plot_name]["app_name"] = app_name
                self.plot_list.append(app_name)

        self.plot_name = "/instrument_" + self.alias["name"]
        plot_config["name"] = self.plot_name
        plot_config["app_list"] = self.plot_list

        return plot_config

    def get_last(self):
        return self.last_entry

    def add_measurements(self):
        # print('******add measurements')
        definition = self.get_definition_instance()
        # print('definition')
        if "measurement_config" in definition["DEFINITION"]:
            config = definition["DEFINITION"]["measurement_config"]
            self.measurements["meta"] = config
            for set_name, meas_set in config.items():
                # print(f'set_name: {set_name}')
                self.measurements["measurement_sets"][set_name] = dict()
                mset = self.measurements["measurement_sets"][set_name]
                for name, meas_cfg in meas_set.items():
                    # print(f'name: {name}')
                    mset[name] = dict()
                    mset[name]["value"] = None

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

        self.name = "DummyInstrument"
        self.type = "DummyType"
        self.mfg = "DumbMfg"
        self.model = "DumbModelSX"
        self.tag_list = [
            "dummy",
            "testing",
            "development",
        ]

        # need to allow for datasets...how?

        # definition = DummyInstrument.get_definition()

        self.meas_map = dict()
        self.meas_map["LIST"] = [
            "concentration",
            "inlet_temperature",
            "inlet_flow",
            "inlet_pressure",
        ]
        self.meas_map["DEFINITION"] = {
            "concentration": {
                "index": 0,
                "units": "cm-3",
                "uncertainty": 0.01,
            },
            "inlet_temperature": {"index": 1, "units": "degC", "uncertainty": 0.2},
            "inlet_flow": {
                "index": 2,
                "units": "l/min",
                "uncertainty": 0.2,
            },
            "inlet_pressure": {"index": 3, "units": "mb", "uncertainty": 0.5},
        }

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
        definition = self.get_definition_instance()
        meas_config = definition["DEFINITION"]["measurement_config"]
        for msetsname, mset in meas_config.items():
            # self.data_record_template[msetname] = dict()
            for name, meas in mset.items():
                self.data_record_template[name] = {"VALUE": None}

        self.status["ready_to_run"] = True
        self.status2.set_run_status(Status.READY_TO_RUN)
        self.enable()

    async def shutdown(self):
        # print("DummyInstrument shutdown")
        # print("dummy instrument stop")
        self.stop()
        # print("dummy instrument disable")
        self.disable()
        # print("dummy instrument dereg")
        await self.deregister_from_UI()
        # print("dummy instrument super shutdown")

        # TODO need to wait for deregister before closing loops and connection
        await super().shutdown()

    def start(self, cmd=None):
        # task = asyncio.ensure_future(self.read_loop())
        print(f"Starting Instrument {self}")
        super().start(cmd)
        for k, iface in self.iface_map.items():
            iface.start()

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if type == "FromChild" and msg.type == Interface.class_type:
            # print(f'+++++FromChild.handle: {msg.to_json()}')
            # # id = msg.sender_id
            # entry = self.parse(msg)
            # self.last_entry = entry
            # # print('entry = \n{}'.format(entry))
            # print(f"dummy handle: {")

            dt = self.parse(msg)
            # print(f'dt = {dt}')
            # entry = {
            #     'METADATA': self.get_metadata(),
            #     'DATA': {
            #         'DATETIME': dt,
            #         'MEASUREMENTS': self.get_data_record(dt)
            #     }
            entry = self.get_data_entry(dt)
            # print(f'entry: {entry}')
            # data = dict()
            # data['DATETIME'] = dt
            # data['MEASUREMENTS'] = self.get_data_record(dt)
            # entry['DATA'] = data

            data = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
            )
            # send data to next step(s)
            # to controller
            # data.update(subject='DATA', body=entry['DATA'])
            data.update(subject="DATA", body=entry)

            # await self.msg_buffer.put(data)
            # await self.to_parent_buf.put(data)
            print(f'instrument data: {data.to_json()}')

            await self.message_to_ui(data)
            await self.to_parent_buf.put(data)
            if self.datafile:
                await self.datafile.write_message(data)

            # await self.data_file.write_message(data)

            # await PlotManager.update_data(self.plot_name, data.to_json())

            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)

        # elif type == 'FromUI':
        #     if msg.subject == 'STATUS' and msg.body['purpose'] == 'REQUEST':
        #         # print(f'msg: {msg.body}')
        #         self.send_status()

        #     elif msg.subject == 'CONTROLS' and msg.body['purpose'] == 'REQUEST':

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
        #         # await self.set_control(msg.body['control'], msg.body['value'])

        await super().handle(msg, type)
        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        if control and value:
        #     if control == "start_stop":
        #         if value == "START":
        #             self.start()
        #         elif value == "STOP":
        #             self.stop()

        #         self.set_control_att(control, "action_state", "OK")

            if control == "inlet_temperature_sp":
                # check bounds
                # send command to instrument via interface
                cmd = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject="COMMAND",
                    body="inlet_temp=" + value,
                )

                # print(f'{self.iface_map}')
                # await self.to_child_buf.put(cmd)
                await self.iface_map[
                    "DummyInterface:test_interface"
                ].message_from_parent(cmd)
                self.set_control_att(control, "action_state", "OK")

            elif control == "inlet_flow_sp":
                # check bounds
                # send command to instrument via interface
                cmd = Message(
                    sender_id=self.get_id(),
                    msgtype=Instrument.class_type,
                    subject="COMMAND",
                    body="inlet_flow=" + value,
                )

                print(f"{self.iface_map}")
                # await self.to_child_buf.put(cmd)
                await self.iface_map[
                    "DummyInterface:test_interface"
                ].message_from_parent(cmd)
                self.set_control_att(control, "action_state", "OK")

            # await super().handle_control_action(control, value)
        await super(DummyInstrument, self).handle_control_action(control, value)

    def parse(self, msg):
        # print(f'parse: {msg.to_json()}')
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body["DATETIME"]
        # measurements = dict()

        # TODO: data format issue: metadata in data or in its own field
        #       e.g., units in data or measurement metadata?
        # TODO: allow for "dimensions"
        values = msg.body["DATA"].split(",")
        # print(f'values: {values}')
        meas_list = [
            "concentration",
            "inlet_temperature",
            "inlet_flow",
            "inlet_pressure",
            "pump_power",
        ]
        controls_list = ["inlet_temperature_sp", "inlet_flow_sp"]
        for i, name in enumerate(meas_list):
            # TODO: use meta to convert to float, int
            try:
                val = float(values[i])
            except ValueError:
                val = -999
            # measurements[name] = {
            #     'VALUE': val,
            # }

            self.update_data_record(dt, {name: val})

        # add fake size dist data
        sd = []
        dp = []
        for n in range(0, 20):
            sd.append(round(random.random() * 10.0, 4))
        self.update_data_record(dt, {"size_distribution": sd})
        dp.append(10)
        for n in range(1, 20):
            dp.append(round(dp[n - 1] * 1.4, 2))
        self.update_data_record(dt, {"diameter": dp})

        sd2 = []
        dp2 = []
        for n in range(0, 50):
            sd2.append(round(random.random() * 10.0, 4))
        self.update_data_record(dt, {"size_distribution2": sd2})
        dp2.append(100)
        for n in range(1, 50):
            dp2.append(round(dp2[n - 1] * 1.15, 2))
        self.update_data_record(dt, {"diameter2": dp2})

        for name in controls_list:
            # measurements[name] = {
            #     'VALUE': self.get_control_att(name, 'value'),
            # }
            self.update_data_record(
                dt,
                {name: 1.0}
                # {name: self.get_control_att(name, 'value')}
            )
            # print(f'controls: {name} = {self.get_control_att(name, "value")}')

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

        # data['MEASUREMENTS'] = measurements
        # entry['DATA'] = data
        # return entry
        return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return DummyInstrument.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition["module"] = DummyInstrument.__module__
        definition["name"] = DummyInstrument.__name__
        definition["mfg"] = "DummyMfg"
        definition["model"] = "DumbModelSX"
        definition["type"] = "DummyType"
        definition["tags"] = [
            "dummy",
            "testing",
            "development",
        ]

        measurement_config = dict()

        # array for plot conifg
        y_data = []
        dist_data = []
        # dim_data = []

        # TODO: add interface entry for each measurement
        primary_meas_2d = dict()
        primary_meas_2d["size_distribution"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "nm"],
            },
            "units": "cm-3",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "size_dist",
            "parse_label": "bin",
            "control": None,
            "axes": {
                # 'TIME', 'datetime',
                "DIAMETER": "diameter",
            },
        }
        dist_data.append("size_distribution")

        primary_meas_2d["diameter"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "nm"],
            },
            "units": "nm",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "dp",
            "parse_label": "diameter",
            "control": None,
        }
        dist_data.append("diameter")

        primary_meas_2d["size_distribution2"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "nm"],
            },
            "units": "cm-3",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "size_dist2",
            "parse_label": "bin2",
            "control": None,
            "axes": {
                # 'TIME', 'datetime',
                "DIAMETER": "diameter2",
            },
        }
        dist_data.append("size_distribution2")

        primary_meas_2d["diameter2"] = {
            "dimensions": {
                "axes": ["TIME", "DIAMETER"],
                "unlimited": "TIME",
                "units": ["dateTime", "nm"],
            },
            "units": "nm",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "short_name": "dp2",
            "parse_label": "diameter2",
            "control": None,
        }
        dist_data.append("diameter2")

        primary_meas = dict()
        primary_meas["concentration"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "cm-3",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": None,
        }
        y_data.append("concentration")

        process_meas = dict()
        process_meas["inlet_temperature"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "degC",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": "inlet_temperature_sp",
        }
        y_data.append("inlet_temperature")

        process_meas["inlet_flow"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "liters min-1",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": "inlet_flow_sp",
        }
        y_data.append("inlet_flow")

        process_meas["inlet_pressure"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "mb",  # should be cfunits or udunits
            "uncertainty": 0.4,
            "source": "MEASURED",
            "data_type": "NUMERIC",
        }
        y_data.append("inlet_pressure")

        raw_meas = dict()
        raw_meas["counts"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "pref_color": "black",
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": None,
        }

        raw_meas["pump_power"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "counts",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "pref_color": "black",
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": None,
        }
        y_data.append("pump_power")

        controls = dict()
        controls["inlet_temperature_sp"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": process_meas["inlet_temperature"]["units"],
            "allowed_range": [10.0, 30.0],
            "default_value": 25.0,
            "label": "Inlet Temperature SP",
            "control_group": "Temperatures",
        }
        y_data.append("inlet_temperature_sp")

        controls["inlet_flow_sp"] = {
            "data_type": "NUMERIC",
            # units are tied to parameter this controls
            "units": process_meas["inlet_flow"]["units"],
            "allowed_range": [0.0, 2.0],
            "default_value": 1.0,
            "control_group": "Flows",
        }
        y_data.append("inlet_flow_sp")

        measurement_config["primary"] = primary_meas
        measurement_config["process"] = process_meas
        measurement_config["raw"] = raw_meas
        measurement_config["controls"] = controls
        measurement_config["primary_2d"] = primary_meas_2d

        definition["measurement_config"] = measurement_config

        # dist_data

        plot_config = dict()

        size_dist = dict()
        size_dist["app_type"] = "SizeDistribution"
        size_dist["y_data"] = ["size_distribution", "diameter_nm"]
        # size_dist['y_data'] = ['size_distribution', 'diameter']
        size_dist["default_y_data"] = ["size_distribution"]
        # size_dist['dimensions'] = ['diameter']
        source_map = {
            "default": {
                "y_data": {
                    "short": ["size_distribution", "diameter"],
                    "long": ["size_distribution2", "diameter2"],
                },
                "default_y_data": ["size_distribution"],
            },
        }
        size_dist["source_map"] = source_map

        time_series1d = dict()
        time_series1d["app_type"] = "TimeSeries1D"
        time_series1d["y_data"] = y_data
        time_series1d["default_y_data"] = ["concentration"]
        source_map = {
            "default": {
                "y_data": {
                    "default": y_data,
                },
                "default_y_data": ["concentration"],
            },
        }
        time_series1d["source_map"] = source_map

        plot_config["plots"] = dict()
        # plot_config['plots'][plot_id/name]
        plot_config["plots"]["raw_size_dist"] = size_dist
        plot_config["plots"]["dummy_ts1d"] = time_series1d
        definition["plot_config"] = plot_config

        # TODO: make definition cleaner so authors don't have to kludge
        return {"DEFINITION": definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition


class DummyGPS(Instrument):

    INSTANTIABLE = True

    def __init__(self, config, **kwargs):
        # def __init__(
        #     self,
        #     config,
        #     ui_config=None,
        #     auto_connect_ui=True
        # ):

        super(DummyGPS, self).__init__(config, **kwargs)
        # super().__init__(
        #     config,
        #     ui_config=ui_config,
        #     auto_connect_ui=auto_connect_ui
        # )
        # print('init DummyInstrument')

        self.name = "DummyGPS"
        self.type = "DummyGPSType"
        self.mfg = "DumbMfg"
        self.model = "DumbModelGPS"
        self.tag_list = [
            "gps",
            "position",
            "dummy",
            "testing",
            "development",
        ]

        # need to allow for datasets...how?

        # definition = DummyInstrument.get_definition()

        self.meas_map = dict()
        self.meas_map["LIST"] = ["gps_time", "latitude", "longitude", "altitude"]
        self.meas_map["DEFINITION"] = {
            "concentration": {
                "index": 0,
                "units": "cm-3",
                "uncertainty": 0.01,
            },
            "inlet_temperature": {"index": 1, "units": "degC", "uncertainty": 0.2},
            "inlet_flow": {
                "index": 2,
                "units": "l/min",
                "uncertainty": 0.2,
            },
            "inlet_pressure": {"index": 3, "units": "mb", "uncertainty": 0.5},
        }

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
        definition = self.get_definition_instance()
        meas_config = definition["DEFINITION"]["measurement_config"]
        for msetsname, mset in meas_config.items():
            # self.data_record_template[msetname] = dict()
            for name, meas in mset.items():
                self.data_record_template[name] = {"VALUE": None}

        self.status["ready_to_run"] = True
        self.status2.set_run_status(Status.READY_TO_RUN)
        self.enable()

    def start(self, cmd=None):
        # task = asyncio.ensure_future(self.read_loop())
        print(f"Starting Instrument {self}")
        super().start(cmd)
        for k, iface in self.iface_map.items():
            iface.start()

    async def shutdown(self):
        print("DummyInstrument shutdown")
        self.stop()
        self.disable()
        await self.deregister_from_UI()

        # TODO need to wait for deregister before closing loops and connection
        await super().shutdown()

    async def handle(self, msg, type=None):

        # print(f'%%%%%Instrument.handle: {msg.to_json()}')
        # handle messages from multiple sources. What ID to use?
        if type == "FromChild" and msg.type == Interface.class_type:
            # # id = msg.sender_id
            # entry = self.parse(msg)
            # self.last_entry = entry
            # # print('entry = \n{}'.format(entry))

            dt = self.parse(msg)
            # print(f'dt = {dt}')

            # add fake gps data
            self.update_data_record(dt, {"gps_time": dt})
            val = 42 + round(random.random() * 10, 3)
            self.update_data_record(dt, {"latitude": val})
            val = -50 + round(random.random() * 10, 3)
            self.update_data_record(dt, {"longitude": val})
            val = 500 + round(random.random() * 100, 3)
            self.update_data_record(dt, {"altitude": val})

            # entry = {
            #     'METADATA': self.get_metadata(),
            #     'DATA': {
            #         'DATETIME': dt,
            #         'MEASUREMENTS': self.get_data_record(dt)
            #     }
            entry = self.get_data_entry(dt)
            # print(f'entry: {entry}')
            # data = dict()
            # data['DATETIME'] = dt
            # data['MEASUREMENTS'] = self.get_data_record(dt)
            # entry['DATA'] = data

            data = Message(
                sender_id=self.get_id(),
                msgtype=Instrument.class_type,
            )
            # send data to next step(s)
            # to controller
            # data.update(subject='DATA', body=entry['DATA'])
            data.update(subject="DATA", body=entry)

            # await self.msg_buffer.put(data)
            # await self.to_parent_buf.put(data)
            # print(f'instrument data: {data.to_json()}')

            await self.message_to_ui(data)
            await self.to_parent_buf.put(data)
            if self.datafile:
                await self.datafile.write_message(data)

            # await self.data_file.write_message(data)

            # await PlotManager.update_data(self.plot_name, data.to_json())

            # print(f'data_json: {data.to_json()}\n')
            # await asyncio.sleep(0.01)

        elif type == "FromUI":
            if msg.subject == "STATUS" and msg.body["purpose"] == "REQUEST":
                # print(f'msg: {msg.body}')
                self.send_status()

            elif msg.subject == "CONTROLS" and msg.body["purpose"] == "REQUEST":

                # print(f'msg: {msg.body}')
                await self.set_control(msg.body["control"], msg.body["value"])

            elif msg.subject == "RUNCONTROLS" and msg.body["purpose"] == "REQUEST":

                # print(f'msg: {msg.body}')
                await self.handle_control_action(msg.body["control"], msg.body["value"])
                # await self.set_control(msg.body['control'], msg.body['value'])

        # print("DummyInstrument:msg: {}".format(msg.body))
        # else:
        #     await asyncio.sleep(0.01)

    async def handle_control_action(self, control, value):
        await super().handle_control_action(control, value)
        # if control and value:
        #     if control == "start_stop":
        #         if value == "START":
        #             self.start()
        #         elif value == "STOP":
        #             self.stop()

        #         self.set_control_att(control, "action_state", "OK")
        # if control and value:
        #     if control == 'start_stop':
        #         if value == 'START':
        #             self.start()
        #         elif value == 'STOP':
        #             self.stop()

        # print(f'{self.iface_map}')
        # await self.to_child_buf.put(cmd)
        # await self.iface_map['DummyInterface:test_interface'].message_from_parent(cmd)
        # self.set_control_att(control, 'action_state', 'OK')

    def parse(self, msg):
        # print(f'parse: {msg.to_json()}')
        # entry = dict()
        # entry['METADATA'] = self.get_metadata()

        # data = dict()
        # data['DATETIME'] = msg.body['DATETIME']
        dt = msg.body["DATETIME"]
        # measurements = dict()
        return dt
        # TODO: data format issue: metadata in data or in its own field
        #       e.g., units in data or measurement metadata?
        # TODO: allow for "dimensions"
        values = msg.body["DATA"].split(",")
        # print(f'values: {values}')
        meas_list = [
            "concentration",
            "inlet_temperature",
            "inlet_flow",
            "inlet_pressure",
            "pump_power",
        ]
        controls_list = ["inlet_temperature_sp", "inlet_flow_sp"]
        for i, name in enumerate(meas_list):
            # TODO: use meta to convert to float, int
            try:
                val = float(values[i])
            except ValueError:
                val = -999
            # measurements[name] = {
            #     'VALUE': val,
            # }

            self.update_data_record(dt, {name: val})

        for name in controls_list:
            # measurements[name] = {
            #     'VALUE': self.get_control_att(name, 'value'),
            # }
            self.update_data_record(dt, {name: self.get_control_att(name, "value")})
            # print(f'controls: {name} = {self.get_control_att(name, "value")}')

        return dt

    def get_definition_instance(self):
        # make sure it's good for json
        # def_json = json.dumps(DummyInstrument.get_definition())
        # print(f'def_json: {def_json}')
        # return json.loads(def_json)
        return DummyGPS.get_definition()

    def get_definition():
        # TODO: come up with static definition method
        definition = dict()
        definition["module"] = DummyGPS.__module__
        definition["name"] = DummyGPS.__name__
        definition["mfg"] = "DummyMfg"
        definition["model"] = "DumbModelGPS"
        definition["type"] = "DummyGPSType"
        definition["tags"] = [
            "gps",
            "position",
            "dummy",
            "testing",
            "development",
        ]

        # interface components
        components = dict()
        components["interface"] = {"default": ["RS-232", "USB"]}
        definition["components"] = components

        # instrument options
        options = dict()
        options["test_option1"] = {"default": True, "choices": [True, False]}
        options["test_option2"] = {
            "default": 1.0,
            "choice_range": (0, 5),
            "choice_step": 0.1,
        }
        definition["options"] = options

        measurement_config = dict()

        # array for plot conifg
        y_data = []
        # dist_data = []
        # dim_data = []

        # TODO: add interface entry for each measurement
        # primary_meas_2d = dict()
        # primary_meas_2d['size_distribution'] = {
        #     'dimensions': {
        #         'axes': ['TIME', 'DIAMETER'],
        #         'unlimited': 'TIME',
        #         'units': ['dateTime', 'nm'],
        #     },
        #     'units': 'cm-3',  # should be cfunits or udunits
        #     'uncertainty': 0.1,
        #     'source': 'MEASURED',
        #     'data_type': 'NUMERIC',
        #     'short_name': 'size_dist',
        #     'parse_label': 'bin',
        #     'control': None,
        #     'axes': {
        #         'DIAMETER': 'diameter',
        #     }
        # }
        # dist_data.append('size_distribution')

        # primary_meas_2d['diameter'] = {
        #     'dimensions': {
        #         'axes': ['TIME', 'DIAMETER'],
        #         'unlimited': 'TIME',
        #         'units': ['dateTime', 'nm'],
        #     },
        #     'units': 'nm',  # should be cfunits or udunits
        #     'uncertainty': 0.1,
        #     'source': 'MEASURED',
        #     'data_type': 'NUMERIC',
        #     'short_name': 'dp',
        #     'parse_label': 'diameter',
        #     'control': None,
        # }
        # dist_data.append('diameter')

        primary_meas = dict()
        primary_meas["gps_time"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "dateTime",  # should be cfunits or udunits
            "uncertainty": 0.1,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": None,
        }
        y_data.append("gps_time")

        primary_meas["latitude"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "deg",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": None,
        }
        y_data.append("latitude")

        primary_meas["longitude"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "deg",  # should be cfunits or udunits
            "uncertainty": 0.2,
            "source": "MEASURED",
            "data_type": "NUMERIC",
            "control": None,
        }
        y_data.append("longitude")

        primary_meas["altitude"] = {
            "dimensions": {
                "axes": ["TIME"],
                "unlimited": "TIME",
                "units": ["dateTime"],
            },
            "units": "m",  # should be cfunits or udunits
            "uncertainty": 0.4,
            "source": "MEASURED",
            "data_type": "NUMERIC",
        }
        y_data.append("altitude")

        measurement_config["primary"] = primary_meas

        definition["measurement_config"] = measurement_config

        # dist_data

        plot_config = dict()

        time_series1d = dict()
        time_series1d["app_type"] = "TimeSeries1D"
        time_series1d["y_data"] = y_data
        time_series1d["default_y_data"] = ["altitude"]
        source_map = {
            "default": {
                "y_data": {
                    "default": y_data,
                },
                "default_y_data": ["altitude"],
            },
        }
        time_series1d["source_map"] = source_map

        plot_config["plots"] = dict()
        plot_config["plots"]["gps_ts1d"] = time_series1d
        definition["plot_config"] = plot_config

        # TODO: make definition cleaner so authors don't have to kludge
        return {"DEFINITION": definition}
        # DAQ.daq_definition['DEFINITION'] = definition

        # return DAQ.daq_definition
