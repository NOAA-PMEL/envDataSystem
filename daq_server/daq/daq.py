import abc
import asyncio
import json
from json.decoder import JSONDecodeError
import os
from pathlib import Path
from client.wsclient import WSClient
# from plots.apps.plot_app import PlotApp
from shared.data.message import Message
from shared.data.status import Status
from shared.data.datafile import DataFile
from shared.utilities.util import time_to_next, dt_to_string


# from urllib.parse import quote


class DAQ(abc.ABC):

    # TODO: how to do this more elegantly?
    INSTANTIABLE = False
    # daq_definition = {'DEFINITION': {}}

    def __init__(
        self,
        config,
        ui_config=None,
        base_file_path=None,
        auto_connect_ui=True,
        namespace=None,
        **kwargs
    ):
        # non-abstract DAQ children need to set this to True
        #   in order for system to recognize as valid
        # TODO: make an abstract method to retrieve value
        #       to force children to deal with it?

        # TODO: Should DAQ have generic in/out buffers?
        print('init DAQ')
        self.loop = asyncio.get_event_loop()
        self.config = config
        self.ui_config = ui_config
        self.do_ui_connection = auto_connect_ui
        self.task_list = []
        self.ui_task_list = []
        self.registration_key = None

        self.plot_app = None

        self.datafile = None

        self.keepalive_ping = False

        # set base file path for all file saves
        # base_file_path = '/tmp'
        if base_file_path:
            self.base_file_path = base_file_path

        # parameters to include metadata in output
        self.include_metadata = True
        # set interval to 0 to always send metadata
        self.include_metadata_interval = 60

        # self.daq_definition = dict()
        # self.daq_definition['DEFINITION'] = dict()

        # self.INSTANTIABLE = False

        self.name = None
        self.label = None
        if 'LABEL' in config:
            self.label = config['LABEL']
        # print(f"id: {self.get_id()}")

        # print(f"16namespace = {self.namespace} - {self.alias}")

        # if namespace is passed, store a copy
        self.namespace = {}
        if namespace:
            self.namespace = namespace.copy()
        # self.parent_id = "parent-default"
        # if parent_id:
        #     self.parent_id = parent_id
        # self.daq_id = f"{self.parent_id}-default"

        # in case we want to add heierarchy
        # parent = {
        #   class: 'CONTROLLER',
        #   id: <controller_name>,
        # }
        self.parent = None
        self.parent_map = dict()

        self.data_request_list = []

        # Message buffers (Queues)
        #   to/from parent
        self.to_parent_buf = None
        self.from_parent_buf = None
        #   to/from child
        self.to_child_buf = None
        self.from_child_buf = None
        #   to/from gui
        self.to_ui_buf = None
        self.from_ui_buf = None
        self.create_msg_buffers()

        # ui client
        self.ui_client = None

        # controls
        self.controls = dict()
        self.status = {
            'run_status': 'STOPPED',
            'ready_to_run': False,
            'connected_to_ui': False,
            'health': 'OK'
        }
        self.status2 = Status()
        self.current_run_settings = dict()
        # start loop to maintain ui
        # if (
        #     'do_ui_connection' in self.ui_config and
        #     self.ui_config['do_ui_connection'] is False
        # ):
        #     print('no ui connection')
        #     pass
        # else:
        # self.task_list.append(
        #     asyncio.ensure_future(self.run_ui_connection())
        # )
        # # make ui connection
        # self.ui_task_list.append(
        #     asyncio.ensure_future(self.open_ui_connection())
        # )

    def get_namespace_as_string(self):
        names = [k for k, v in self.namespace.items()]
        ns = "-".join(names)
        return ns
        
    def open_datafile(self):

        cfg = self.get_datafile_config()
        if cfg:
            self.datafile = DataFile(
                # base_path=self.get_base_filepath(),
                config=self.get_datafile_config()
            )
            if self.datafile:
                self.datafile.open()

    def get_datafile_config(self):
        bfp = self.get_base_filepath()
        if bfp:
            config = {
                'base_path': self.get_base_filepath(),
            }
            return config
        return None

    def get_base_filepath(self):
        # system_base = '/home/horton/derek/tmp/envDataSystem/'
        # inst_base = 'instrument/'
        # definition = self.get_definition_instance()
        # inst_base += definition['DEFINITION']['type']+'/'
        # inst_base += definition['DEFINITION']['mfg']+'/'
        # inst_base += definition['DEFINITION']['model']+'_'
        # inst_base += self.serial_number+'/'

        if self.base_file_path:
            return self.base_file_path + '/' + self.alias['name']

        return None
        # return system_base+inst_base

    @abc.abstractmethod
    def setup(self):
        print('daq.setup')

        self.start_connections()

    # @abc.abstractmethod
    def setup_datafile(self):
        pass

    def start_connections(self):
        print('start_connections')
        self.start_ui_connection()

    def start_ui_connection(self):
        print('start_ui_connection')
        self.task_list.append(
            asyncio.ensure_future(self.run_ui_connection())
        )

    # TODO: convert all to_parent_buffers to
    #       registration process
    def register_parent(
        self,
        parent_id,
        to_parent_buffer=None
    ):
        if parent_id in self.parent_map:
            return
        self.parent_map[parent_id] = {
            'to_parent_buffer': to_parent_buffer
        }

    def deregister_parent(self, parent_id):

        try:
            del self.parent_map[parent_id]
        except KeyError:
            pass

    def register_data_request(self, entry):
        if (
            entry and
            entry not in self.data_request_list
        ):

            self.data_request_list.append(entry)

    def get_id(self):
        id = self.__class__.__name__
        if self.label is not None:
            id += "_"+self.label

        return id

    def current_run_settings_file(self) -> Path:
        ns_path = Path("config") / "run"
        # ns_path = ["config", "run"]

        if "daq_server" in self.namespace:
            # ns_path.append(self.namespace['daq_server'])
            ns_path /= self.namespace['daq_server']
        if "controller" in self.namespace:
            # ns_path.append(self.namespace['controller'])
            ns_path /= self.namespace['controller']
        if "instrument" in self.namespace:
            # ns_path.append(self.namespace['instrument'])
            ns_path /= self.namespace['instrument']
        # if not os.path.exists(os.path.join(ns_path)):
        #     os.makedirs(ns_path)
        # Path.mkdir(ns_path, parents=True, exist_ok=True)
        fname = ns_path / "current_run_settings.json"
        return fname

    def get_current_run_settings(self):

        if not self.controls:
            definition = self.get_definition_instance()
            try:
                self.controls = definition['DEFINITION']['measurement_config']['controls']
            except KeyError:
                print("no run settings to get")
                return

        fname = self.current_run_settings_file()
        Path.mkdir(fname.parent, parents=True, exist_ok=True)
        try:
            with open(fname) as cfg:
                self.current_run_settings = json.load(cfg)
                # print(f"{self.current_run_settings}")
        except (FileNotFoundError, JSONDecodeError, TypeError):
            self.set_current_run_settings_default()
            # saved settings not valid for some reason, set to default

        need_save = False
        for control, config in self.controls.items():
            if control not in self.current_run_settings:
                self.current_run_settings[control] = None
                need_save = True
                if 'default_value' in config:
                    self.current_run_settings[control] =config['default_value']
        if need_save:
            self.save_current_run_settings()

    def update_current_run_settings(self):
        if self.controls:
            for control, settings in self.controls.items():
                try:
                    # print(f"{control}, {settings}")
                    self.current_run_settings[control] = settings["value"]
                except KeyError:
                    pass
                    # print(f"update crs error: {control}")
            # print(f"updated run settings: {self.current_run_settings}")
            self.save_current_run_settings()

    def save_current_run_settings(self):
        if self.current_run_settings:
            fname = self.current_run_settings_file()
            Path.mkdir(fname.parent, parents=True, exist_ok=True)
            try:
                # test = json.dumps(self.current_run_settings)
                # print(test)
                with open(fname, "w") as cfg:
                    json.dump(self.current_run_settings, cfg)
            except (FileNotFoundError, JSONDecodeError, TypeError) as e:
                print(f"Could not save current_run_settigns: {fname}: {e}")             

    def set_current_run_settings_default(self):
        if not self.controls:
            definition = self.get_definition_instance()
            try:
                self.controls = definition['DEFINITION']['measurement_config']['controls']
            except KeyError:
                print("no run settings to get")
                return

            for control, config in self.controls.items():
                self.current_run_settings[control] = None
                if 'default_value' in config:
                    # TODO: on start, have to go through and send all
                    #       control values to instrument
                    self.current_run_settings[control] =config['default_value']
                    # self.set_control_att(
                    #     control, 'value', config['default_value']
                    # )
            self.save_current_run_settings()

    def get_controls(self):
        return self.controls

    def get_control(self, control):
        if control:
            controls = self.get_controls()
            if control in controls:
                return controls[control]
        return None

    async def set_controls(self, controls):
        if controls:
            for control, value in controls.items():
                await self.set_control(control, value)
        # self.controls = controls

    async def set_control(self, control, value):
        if control and value:
            await self.handle_control_action(control, value)
            if (await self.control_action_success(control)):
                self.set_control_att(control, 'value', value)
                self.update_current_run_settings()
            else:
                print(f'Setting {control} unsuccessful')

        # TODO: setting control should trigger action
        # print(f'set_control[{control}] = {value}')

    # TODO: implement this as an abstract method
    # @abc.abstractmethod
    async def handle_control_action(self, control, value):
        # default control actions
        if control and value:
            if control == "start_stop":
                if value == "START":
                    self.start()
                elif value == "STOP":
                    self.stop()

    def set_control_att(self, control, att, value):
        if control not in self.controls:
            self.controls[control] = dict()
        try:
            self.controls[control][att] = value
            # self.controls[control]['action_state'] = state
        except Exception as e:
            print(f'exc: {e}')

    def get_control_att(self, control, att):

        if control in self.controls:
            try:
                return self.controls[control][att]
            except Exception as e:
                print(f'No attribute {att} in {control}: {e}')
                return ''

    async def control_action_success(self, control):

        timeout = 50  # seconds * 10 for faster response
        cnt = 0
        while cnt < timeout:
            try:
                # print(
                #     f'success; {self.get_control_att(control, "action_state")}'
                # )
                if self.get_control_att(control, 'action_state') == 'OK':
                    self.set_control_att(control, 'action_state', 'IDLE')
                    return True
            except Exception as e:
                print(f'exception: {e}')
                await asyncio.sleep(.1)
                cnt += 0.1
            
        return False

    # TODO: add this abstract method to all daq
    # @abc.abstractclassmethod
    def get_definition():
        pass

    @abc.abstractclassmethod
    def get_definition_instance():
        pass

    # @classmethod
    # def can_instantiate():
    #     return object.__class__().INSTANTIATE

    # @classmethod
    # def get_instantiable():
    #     return DAQ.INSTANTIABLE

    # @classmethod
    # def set_instantiable(val):
    #     if val:
    #         DAQ.INSTANTIABLE = True
    #     else:
    #         DAQ.INSTANTIABLE = False

    @abc.abstractmethod
    def get_ui_address(self):
        pass

    async def register_with_UI(self):
        pass

    async def connect_to_ui(self):
        print(f'connecting to ui: {self}')
        # build ui_address
        ui_address = f'ws://{self.ui_config["host"]}'
        ui_address += f':{self.ui_config["port"]}'
        ui_address += '/ws/'+self.get_ui_address().replace(" ", "")
        # ui_address.replace(" ", "")
        print(f'ui_address: {ui_address}')

        # self.ui_client = WSClient(uri=quote(ui_address))
        self.ui_client = WSClient(uri=ui_address)
        while self.ui_client.isConnected() is not True:
            # self.gui_client = WSClient(uri=gui_ws_address)
            # print(f"gui client: {self.gui_client.isConnected()}")
            await asyncio.sleep(1)

    async def run_ui_connection(self):

        # # start ui queues
        # self.ui_task_list.append(
        #     asyncio.ensure_future(self.to_ui_loop())
        # )
        # self.ui_task_list.append(
        #     asyncio.ensure_future(self.from_ui_loop())
        # )

        while True:
            if (
                self.do_ui_connection and (
                    self.ui_client is None or not self.ui_client.isConnected()
                )
            ):
                self.status2.set_connection_status(Status.CONNECTING)
                # close tasks for current ui if any
                for t in self.ui_task_list:
                    t.cancel()

                # make connection
                print('connect to ui')
                await self.connect_to_ui()

                # start ui queues
                self.ui_task_list.append(
                    asyncio.ensure_future(self.to_ui_loop())
                )
                self.ui_task_list.append(
                    asyncio.ensure_future(self.from_ui_loop())
                )
                if self.keepalive_ping:
                    self.ui_task_list.append(
                        asyncio.create_task(self.ping_ui_server())
                    )

                await self.register_with_UI()

            self.status2.set_connection_status(Status.CONNECTED)
            await asyncio.sleep(1)

    # async def open_ui_connection(self):

    #     while self.ui_client.isConnected() is False:
    #         # if self.ui_client.isConnected() is False:
    #         self.ui_client = self.connect_to_ui()

    def send_status(self, note=''):
        # print(f'send_status: {self.name}, {self.status}')
        status = Message(
            sender_id=self.get_id(),
            msgtype='GENERIC',
            subject="STATUS",
            body={
                'purpose': 'UPDATE',
                'status': self.status,
                # 'note': note,
            }
        )
        status = self.status2.to_message(sender_id=self.get_id())
        # print(f'send no wait: {self.name}, {self.status}')
        self.message_to_ui_nowait(status)
        # self.message_to_ui_nowait(status)

    async def send_settings_to_ui(self):
        if self.current_run_settings:
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
           
    async def update_settings_loop(self):
        # overload this function if you want an update
        #   settings loop. 
        pass
        # # print(f'send_status: {self.name}, {self.status}')
        # if not self.current_run_settings:
        #     self.get_current_run_settings()
        # while True:
        #     # while self.current_run_settings:
        #     if self.status2.get_run_status() in [Status.READY_TO_RUN, Status.STOPPED]:
        #         settings = Message(
        #             sender_id=self.get_id(),
        #             msgtype=self.class_type,
        #             subject="SETTINGS",
        #             body={
        #                 'purpose': 'UPDATE',
        #                 'settings': self.current_run_settings,
        #                 # 'note': note,
        #             }
        #         )
        #         await self.message_to_ui(settings)
        #     await asyncio.sleep(2)

    async def send_metadata_loop(self):

        while True:
            if self.include_metadata_interval > 0:
                # wt = utilities.util.time_to_next(
                #     self.include_metadata_interval
                # )
                # print(f'wait time: {wt}')
                await asyncio.sleep(
                    time_to_next(
                        self.include_metadata_interval
                    )
                )
                self.include_metadata = True
            else:
                self.include_metadata = True
                asyncio.sleep(1)

    def enable(self):
        if self.status2.get_enabled_status() != Status.ENABLED:
        # if self.status['run_status'] != 'STARTED':
            self.task_list.append(
                asyncio.ensure_future(self.from_parent_loop())
            )

            self.task_list.append(
                asyncio.ensure_future(self.from_child_loop())
            )

            self.task_list.append(
                asyncio.create_task(self.update_settings_loop())
            )
            self.status2.set_enabled_status(Status.ENABLED)

    def disable(self):
        self.stop()
        for t in self.task_list:
            t.cancel()
        self.status2.set_enabled_status(Status.DISABLED)

    def start(self, cmd=None):
        # self.create_msg_buffers()
        self.status2.set_run_status(Status.STARTING)
        # only need to start this, will be cancelled by
        #   daq on stop
        self.include_metadata = True
        self.task_list.append(
            asyncio.ensure_future(
                self.send_metadata_loop()
            )
        )

        # if self.status2.get_run_status() != Status.RUNNING:
        # # if self.status['run_status'] != 'STARTED':
        #     self.task_list.append(
        #         asyncio.ensure_future(self.from_parent_loop())
        #     )

        #     self.task_list.append(
        #         asyncio.ensure_future(self.from_child_loop())
        #     )
        self.status['run_status'] = 'STARTED'
        self.status2.set_run_status(Status.RUNNING)

        self.send_status()

    def stop(self, cmd=None):
        self.status2.set_run_status(Status.STOPPING)
        # for t in self.task_list:
        #     t.cancel()

        self.status['run_status'] = 'STOPPED'
        self.status2.set_run_status(Status.STOPPED)
        self.send_status()

    async def ping_ui_server(self):

        # wait for things to get started before pinging
        await asyncio.sleep(5)

        while self.ui_client.isConnected():
            msg = Message(
                sender_id=self.get_id(),
                msgtype="PING",
                subject="PING",
                body={
                    # "id": self.daq_id
                    "namespace": self.namespace
                }
            )
            await self.to_ui_buf.put(msg)
            await asyncio.sleep(2)

    def shutdown(self):

        # if self.started:
        #     print(f'wait for shutdown...')
        #     return
        self.status2.set_run_status(Status.SHUTTING_DOWN)
        if self.ui_client is not None:
            # self.loop.run_until_complete(self.gui_client.close())
            self.ui_client.sync_close()
        self.disable()
        # for t in self.ui_task_list:
        #     t.cancel()
        self.status2.set_run_status(Status.SHUTDOWN)

    def create_msg_buffers(self, config=None):
        '''
        Create all buffers controlled by this instance.
        '''

        self.from_parent_buf = asyncio.Queue(loop=self.loop)
        self.from_child_buf = asyncio.Queue(loop=self.loop)
        self.to_ui_buf = asyncio.Queue(loop=self.loop)

        # I don't think we need a from_ui_buf
        # self.from_ui_buf = asyncio.Queue(loop=self.loop)

    @abc.abstractmethod
    async def handle(self, msg, type=None):

        if type == "FromUI":
            if msg.subject == "STATUS" and msg.body["purpose"] == "REQUEST":
                # print(f"msg: {msg.body}")
                self.send_status()

            elif msg.subject == "CONTROLS" and msg.body["purpose"] == "REQUEST":
                # print(f"msg: {msg.body}")
                await self.set_control(msg.body["control"], msg.body["value"])
            elif msg.subject == "RUNCONTROLS" and msg.body["purpose"] == "REQUEST":
                # print(f"msg: {msg.body}")
                await self.handle_control_action(msg.body["control"], msg.body["value"])
                # await self.set_control(msg.body['control'], msg.body['value'])

            elif msg.subject == "REGISTRATION":
                print(f"reg: {msg.subject}")
                if msg.body["purpose"] == "SUCCESS":
                    self.registration_key = msg.body["regkey"]
                    # if content["BODY"]["config"]:

                    # self.config = content["BODY"]["config"]
                        # self.save_current_config(json.loads(content["BODY"]["config"]))
                    self.status2.set_registration_status(Status.REGISTERED)
                    # if content["BODY"]["ui_reconfig_request"]:
                    #     await self.resend_config_to_ui()

    async def from_parent_loop(self):
        while True:
            msg = await self.from_parent_buf.get()
            # print(f'daq from parent: {msg.to_json()}')
            await self.handle(msg, type="FromParent")
            # await asyncio.sleep(.1)

    async def from_child_loop(self):
        # print(f'started from_child_loop: {self.name} {self.from_child_buf}')
        # while self.from_child_buf is None:
        #     pass

        while True:
            msg = await self.from_child_buf.get()
            # print(f'****from_child_loop: {msg.to_json()}')
            # print(f'from_child: {self.get_id()}')
            await self.handle(msg, type="FromChild")
            # await asyncio.sleep(.1)

    async def to_ui_loop(self):
        while True:
            message = await self.to_ui_buf.get()
            # print(f'&&&&&&&&&&&&&&&send server message: {message.to_json()}')
            await self.ui_client.send_message(message)

    async def from_ui_loop(self):
        # print(f'starting daq from_ui_loop')
        while True:
            message = await self.ui_client.read_message()
            # print(f'message = {message.to_json()}')
            await self.handle(message, type='FromUI')

    async def message_to_parent(self, msg):
        # while True:
        # print(f'message_to_parent: {self.get_id()}, {msg.to_json()}')
        await self.to_parent_buf.put(msg)

    async def message_to_parents(self, msg):
        # while True:
        # print(f'message_to_parents: {self.get_id()}, {msg.to_json()}')
        for id, parent in self.parent_map.items():
            if parent['to_parent_buffer']:
                # print(f'mtp: {msg.to_json()}')
                await parent['to_parent_buffer'].put(msg)

    def message_to_ui_nowait(self, msg):
        # print(f'no wait: {msg.to_json()}')
        asyncio.ensure_future(self.message_to_ui(msg))

    async def message_to_ui(self, msg):
        # while True:
        # print('******message_to_ui')
        # print(f'message_to_ui: {msg.to_json()}')
        await self.to_ui_buf.put(msg)

    async def message_from_parent(self, msg):
        '''
        This is to be used by parent to send messages to
        children
        '''
        # while True:
        await self.from_parent_buf.put(msg)
