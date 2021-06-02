from json.decoder import JSONDecodeError
import os
import sys
import asyncio
from importlib import import_module
from datetime import datetime
import json


# These are now imported below after path is set

# from daq.manager.sys_manager import SysManager
# from daq.controller.controller import ControllerFactory  # , Controller
# from client.wsclient import WSClient
# # from data.message import Message
# # import websockets
# import utilities.util as util
# import functool
# from plots.plots import PlotManager


class DAQServer:
    def __init__(self, config=None, server_name=None, ui_config=None):
        self.controller_list = []
        self.controller_map = dict()
        self.task_list = []
        self.ui_task_list = []
        self.last_data = {}
        self.run_flag = False
        self.registration_key = None
        self.run_state = "STOPPED"
        self.config_state = "NOT_CONFIGURED"

        # defaults
        self.server_name = ""
        self.ui_config = {
            "host": "localhost",
            "port": 8001,
        }
        self.base_file_path = "/tmp"
        self.current_run_config = {}

        # daq_id: used by ui to delineate between different daq_servers - {nodename}-{namespace}
        self.daq_id = "localhost-default"
        self.uri = "localhost"
        # self.namespace = {
        #     "daq_server": "localhost-default",
        # }
        self.namespace = Namespace(
            name="default", host="localhost", ns_type=Namespace.DAQSERVER
        )

        self.autoenable_daq = False
        self.enable_daq = True

        self.loop = asyncio.get_event_loop()

        # try to import config from daq_settings.py
        try:
            daq_settings = import_module("config.daq_settings")
            server_config = daq_settings.server_config

            if "name" in server_config:
                self.server_name = server_config["name"]

            if "ui_config" in server_config:
                self.ui_config = server_config["ui_config"]

            if "base_file_path" in server_config:
                self.base_file_path = server_config["base_file_path"]

            if "daq_id" in server_config:
                fqdn = server_config["daq_id"]["fqdn"]
                namespace = server_config["daq_id"]["namespace"]
                # self.uri = fqdn
                # self.daq_id = f"{fqdn.split('.')[0]}-{namespace}"
                # self.namespace["daq_server"] = self.daq_id.replace(" ", "")

                self.namespace.host = fqdn
                self.namespace.name = namespace.replace(" ", "")

                self.daq_id = self.namespace.get_namespace_sig()["name"]
                self.uri = self.namespace.get_namespace_sig()["host"]

            self.current_config_file = "./current_config.json"
            if "current_config_file" in server_config:
                self.current_config_file = server_config["current_config_file"]

            self.config = dict()
            # if "last_config_file" in server_config:
            #     # dir_path = os.path.dirname(os.path.realpath(__file__))
            #     # print(dir_path)
            #     self.last_config_file = server_config["last_config_file"]
            #     fname = self.last_config_file
            #     if not os.path.isabs(self.last_config_file):
            #         fname = os.path.join(
            #             os.path.dirname(os.path.realpath(__file__)),
            #             self.last_config_file,
            #         )
            #     try:
            #         # with open(self.last_config_file) as cfg:
            #         with open(fname) as cfg:
            #             self.config = json.load(cfg)
            #     except FileNotFoundError as e:
            #         print(e)
            #         pass
            #     except TypeError:
            #         pass

            # if self.config:
            #     self.config_state = "CONFIGURED"

            # if "current_run_config" in server_config:
            #     self.current_run_config = server_config["current_run_config"]
            #     if self.current_run_config:
            #         self.config = self.current_run_config

        except ModuleNotFoundError:
            print("settings file not found, using defaults")
            self.server_name = ""

        # TODO I don't think these override any more...get rid of them?
        # override config file settings
        if server_name:
            self.server_name = server_name
        if ui_config:
            self.ui_config = ui_config
        if config:
            self.config = config

        # self.do_ui_connection = auto_connect_ui
        self.do_ui_connection = False  # change this when try config
        self.reg_client = None
        self.ui_client = None

        self.status = {
            # 'run_status': 'STOPPED',
            "ready_to_run": False,
            "connected_to_ui": False,
            "health": "OK",
        }

        self.status2 = Status()

        # start managers
        SysManager.start()

        # Create message buffers
        self.to_ui_buf = None
        self.from_child_buf = None
        self.create_msg_buffers()

        # Begin startup
        self.run_task = None
        self.start_daq()

    def start_daq(self):
        self.run_task = asyncio.ensure_future(self.open())

    async def restart_daq(self):
        self.status2.set_run_status(Status.RESTARTING)
        # await asyncio.sleep(1)
        # await self.shutdown()
        # await asyncio.sleep(5)
        # self.start_daq()

    def create_msg_buffers(self):
        # if need config, use self.config
        # self.read_buffer = MessageBuffer(config=config)
        self.to_ui_buf = asyncio.Queue(loop=self.loop)
        self.from_child_buf = asyncio.Queue(loop=self.loop)

    def add_controllers(self):
        print("add_controllers()")
        config = self.config
        print(config)
        print(config["ENVDAQ_CONFIG"])
        # print(config['ENVDAQ_CONFIG']['CONT_LIST'])
        for k, icfg in config["ENVDAQ_CONFIG"]["CONT_LIST"].items():
            # for ctr in config['CONT_LIST']:
            print(f"key: {k}")
            # print(F'key = {k}')
            # self.iface_map[iface.name] = iface
            # print(ifcfg['IFACE_CONFIG'])
            # controller = ControllerFactory().create(icfg['CONT_CONFIG'])
            controller = ControllerFactory().create(
                icfg,
                ui_config=self.ui_config,
                base_file_path=self.base_file_path,
                # namespace=self.namespace,
            )
            print(controller)
            controller.to_parent_buf = self.from_child_buf
            self.controller_map[controller.get_id()] = controller

    async def send_message(self, message):
        # TODO: Do I need queues? Message and string methods?
        # await self.sendq.put(message.to_json())
        await self.to_ui_buf.put(message)

    async def to_ui_loop(self):

        # print("send_ui_loop init")
        while True:
            message = await self.to_ui_buf.get()
            # print('send server message')
            await self.ui_client.send_message(message)
            # await asyncio.sleep(1)

    async def from_ui_loop(self):

        # print('read_ui_loop init')
        while True:
            msg = await self.ui_client.read_message()
            # print(f'msg = {msg.to_json()}')
            await self.handle(msg, src="FromUI")
            # print(msg)
            # print('read_loop: {}'.format(msg))

    async def output_to_screen(self):
        while True:

            # TODO: use controller_msg_buffer here
            # for controller in self.controller_list:
            #
            #     data = controller.get_last()
            #     # parse data
            #     print('data: {}'.format(data))
            ts = datetime.utcnow().isoformat(timespec="seconds")
            msgstr = "This is a test {}".format(ts)
            data = {
                "message": msgstr,
            }
            # print('data msg: {}'.format(data))
            await self.to_ui_buf.put(json.dumps(data))
            # FEServer.send_to_clients(data)

            await asyncio.sleep(util.time_to_next(1))

    # TODO: add run() to check for broken connections

    async def register_with_UI(self):

        req = Message(
            sender_id="daq_server",
            msgtype="DAQServer",
            subject="REGISTRATION",
            body={
                "purpose": "ADD",
                "regkey": self.registration_key,
                # "id": self.daq_id,
                # "uri": self.uri,
                "namespace": self.namespace.to_dict(),
                "config": self.config,
                # "config2": json.dumps(self.config),
                "status": self.status2.to_dict(),
            },
        )
        print(f"daq_server:register_with_UI: {req.to_dict()}")
        print(f"Registering with UI server: {self.namespace.get_namespace_sig()}")
        self.status2.set_registration_status(Status.REGISTERING)
        await self.to_ui_buf.put(req)
        self.run_state = "REGISTERING"
        # await reg_client.close()

    async def deregister_from_UI(self):

        # print(f'config: {json.dumps(self.config)}')
        req = Message(
            sender_id="daq_server",
            msgtype="DAQServer",
            subject="REGISTRATION",
            body={
                "purpose": "REMOVE",
                "regkey": self.registration_key,
                "namespace": self.namespace.to_dict(),
                # "id": self.daq_id,
                # "uri": self.uri,
                # "namespace": self.namespace,
                # "config": self.config,
                # "config2": json.dumps(self.config),
                # "status": self.status2
            },
        )
        print(f"Deregistering FROM UI server: {self.namespace.get_namespace_sig()}")
        # self.status2.set_registration_status(Status.UNREGISTERING)
        await self.to_ui_buf.put(req)
        self.status2.set_registration_status(Status.UNREGISTERING)
        self.run_state = "UNREGISTERING"
        # await reg_client.close()

    async def connect_to_ui(self):
        ns_sig = self.namespace.get_namespace_sig()
        print(f"connecting to ui: {self}")
        # build ui_address
        ui_address = f'ws://{self.ui_config["host"]}'
        ui_address += f':{self.ui_config["port"]}'
        # ui_address += f"/ws/envdaq/daqserver/{self.daq_id.replace(' ', '')}"
        # ui_address += f"/ws/envdaq/daqserver/{self.namespace['daq_server']}/"
        # ui_address += f"/ws/envdaq/{self.namespace.ns_type}/{self.namespace.get_local_namespace()}/"
        ui_address += f"/ws/envdaq/{self.namespace.ns_type}/{ns_sig['host']}/{ns_sig['namespace']}/"

        print(f"ui_address: {ui_address}")

        # self.ui_client = WSClient(uri=quote(ui_address))
        self.ui_client = WSClient(uri=ui_address)
        while self.ui_client.isConnected() is not True:
            self.status2.set_connection_status(Status.CONNECTING)
            # self.gui_client = WSClient(uri=gui_ws_address)
            # print(f"gui client: {self.gui_client.isConnected()}")
            await asyncio.sleep(1)

    async def run_ui_connection(self):

        while True:
            if self.do_ui_connection and (
                self.ui_client is None or not self.ui_client.isConnected()
            ):
                self.status2.set_connection_status(Status.NOT_CONNECTED)
                # close tasks for current ui if any
                for t in self.ui_task_list:
                    t.cancel()

                # make connection
                print("connect to ui")
                await self.connect_to_ui()

                # start ui queues
                self.ui_task_list.append(asyncio.ensure_future(self.to_ui_loop()))
                self.ui_task_list.append(asyncio.ensure_future(self.from_ui_loop()))
                self.ui_task_list.append(asyncio.create_task(self.ping_ui_server()))

                self.status2.set_connection_status(Status.CONNECTED)

                await self.register_with_UI()
                # self.status2.set_connection_status(Status.CONNECTED)

            await asyncio.sleep(1)

    def start_connections(self):
        print("start_connections")
        self.start_ui_connection()

    def start_ui_connection(self):
        print("start_ui_connection")
        self.task_list.append(asyncio.create_task(self.run_ui_connection()))

    def enable(self):

        if self.config and (self.enable_daq or self.autoenable_daq):
            print("enabling")
            self.status2.set_enabled_status(Status.ENABLING)
            self.add_controllers()
            self.status2.set_enabled_status(Status.ENABLED)

            asyncio.create_task(self.check_ready_to_run())
            asyncio.create_task(self.send_ready_to_run())

    def disable(self):

        if self.status2.get_enabled_status() == Status.ENABLED:
            self.status2.set_enabled_status(Status.DISABLING)
            self.stop()
            self.remove_controllers()
            self.status2.set_enabled_status(Status.DISABLED)

    async def open(self):
        # task = asyncio.ensure_future(self.read_loop())
        # self.task_list.append(task)

        cfg_fetch_freq = 10  # seconds

        self.status2.set_run_status(Status.STARTING)

        self.configure_daq_local()

        self.start_connections()

        # will only enable if allowed to do so
        self.enable()

        # print(f"UI client is connected: {self.ui_client.isConnected()}")

        # Start heartbeat ping
        # asyncio.create_task(self.ping_ui_server())

        # print("Creating message loops")
        # self.to_ui_buf = asyncio.Queue()
        # self.start_ui_message_loops()

        # self.run_state != "READY_TO_REGISTER":
        # await self.register_with_UI()

        # This should only be done on request
        do_this = False
        if do_this:
            print("sync DAQ")
            # system_def = SysManager.get_definitions_all()
            # print(f'system_def: {system_def}')
            sys_def = Message(
                sender_id="daqserver",
                msgtype="DAQServer",
                subject="CONFIG",
                body={
                    "purpose": "SYNC",
                    "type": "SYSTEM_DEFINITION",
                    "data": SysManager.get_definitions_all(),
                },
            )
            await self.to_ui_buf.put(sys_def)

        # wait for registration
        if do_this:
            while self.status2.get_config_status() != Status.CONFIGURED:
                # while self.run_state != "READY_TO_RUN":
                print(f"config: {self.status2.get_config_status()}")
                await self.configure_daq()
                await asyncio.sleep(1)

        if do_this:
            # once configured, add controllers
            print("Add controllers...")
            self.add_controllers()

        if do_this:
            # if self.config_state != "CONFIGURED":
            print("set self.config")
            while self.config is None:
                # get config from gui
                print("Getting config from gui")
                req = Message(
                    sender_id="daqserver",
                    msgtype="DAQServer",
                    subject="CONFIG",
                    body={
                        "purpose": "REQUEST",
                        "type": "ENVDAQ_CONFIG",
                        "server_name": self.server_name,
                    },
                )
                await self.to_ui_buf.put(req)
                await asyncio.sleep(cfg_fetch_freq)
            self.config_state = "CONFIGURED"
            # print('Waiting for config...')
            # while self.config is None:
            #     pass

            # print(self.config)
            # print("Create message buffers...")
            # self.create_msg_buffers()
            print("Add controllers...")
            self.add_controllers()

            # TODO: Create 'health monitor' to check for status
            #       this should allow for all components to register
            #       so we know when things are ready, broken, etc

            # for now...sleep for a set amount of time to allow
            #   everything to get set up
        print("Waiting for setup...")
        # await asyncio.sleep(10)

        # asyncio.create_task(self.check_ready_to_run())
        # self.ui_task_list.append(asyncio.create_task(self.check_ready_to_run()))
        # self.ui_task_list.append(asyncio.create_task(self.send_ready_to_run()))

        if do_this:
            # if True:
            print(f"run_status: {self.status2.get_run_status()}")
            while self.status2.get_run_status() != Status.READY_TO_RUN:
                # while not self.status["ready_to_run"]:
                print(f"run_status: {self.status2.get_run_status()}")
                await asyncio.sleep(1)

            print("Waiting for setup...done.")

            # PlotManager.get_server().start()

            await self.send_ready_to_ui()

            self.status2.set_run_status(Status.RUNNING)
            self.run_state = "RUNNING"
            # status = Message(
            #     sender_id="DAQ_SERVER",
            #     msgtype="GENERIC",
            #     subject="READY_STATE",
            #     body={
            #         "purpose": "STATUS",
            #         "status": "READY",
            #         # 'note': note,
            #     },
            # )
            # print(f"_____ send no wait _____: {status.to_json()}")
            # await self.to_ui_buf.put(status)

        # end tmp if statement

    async def send_ready_to_ui(self):

        status = Message(
            sender_id="DAQ_SERVER",
            msgtype="GENERIC",
            subject="READY_STATE",
            body={
                "purpose": "STATUS",
                "status": "READY",
                # 'note': note,
            },
        )
        # print(f"_____ send no wait _____: {status.to_json()}")
        # print(f"** daq_server ({self.namespace['daq_server']}) ready")
        print(f"** daq_server ({self.namespace.get_namespace_sig()}) ready")
        await self.to_ui_buf.put(status)

    def read_current_config(self):
        # read current config file
        fname = self.current_config_file
        if not os.path.isabs(self.current_config_file):
            fname = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                self.current_config_file,
            )
        if not os.path.exists(fname):
            self.clear_current_config()

        try:
            # with open(self.last_config_file) as cfg:
            with open(fname) as cfg:
                self.config = json.load(cfg)
                # print(f"{self.config}")

                try:
                    self.uri = self.config["uri"]
                except KeyError:
                    pass

                try:
                    ns = self.config["namespace"]
                    self.namespace = Namespace().from_dict(ns)
                except KeyError:
                    pass

                try:
                    self.autoenable = self.config["autoenable_daq"]
                except KeyError:
                    pass
            # print(f"self.config***: {self.config}")
        except FileNotFoundError as e:
            print(e)
            pass
        except JSONDecodeError as e:
            self.config = dict()
        except TypeError:
            self.clear_current_config()
            pass

    def clear_current_config(self):
        self.config = dict()
        self.save_current_config(self.config)

    def save_current_config(self, config):
        # read current config file
        # print(config)
        # if config:
        if True:
            if "uri" not in config:
                config["uri"] = self.uri

            if "namespace" not in config:
                config["namespace"] = self.namespace.to_dict()

            if "autoenable" not in config:
                config["autoenable_daq"] = self.autoenable_daq

            self.config = config
            fname = self.current_config_file
            if not os.path.isabs(self.current_config_file):
                fname = os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    self.current_config_file,
                )
            try:
                # test = json.dumps(config)
                # print(test)
                # with open(self.last_config_file) as cfg:
                with open(fname, "w") as cfg:
                    json.dump(config, cfg)
                    # self.config = json.load(cfg)
            except FileNotFoundError as e:
                print(e)
                pass
            except TypeError:
                print(f"Couldn't save configuration file: {fname}")
                pass

    def configure_daq_local(self):

        self.status2.set_config_status(Status.CONFIGURING)
        self.read_current_config()
        if self.config:
            try:
                self.namespace = Namespace().from_dict(self.config["namespace"])
            except KeyError:
                pass

            try:
                self.autoenable_daq = self.config["autoenable_daq"]
            except KeyError:
                pass

            try:
                self.uri = self.config["uri"]
            except KeyError:
                pass

            self.status2.set_config_status(Status.NOT_CONFIGURED)
            try:
                if self.config["ENVDAQ_CONFIG"]:
                    self.status2.set_config_status(Status.CONFIGURED)
            except KeyError:
                pass

        else:
            self.status2.set_config_status(Status.NOT_CONFIGURED)

        print(f"self.config: {self.config}")
        # have tried to configure, now connect to UI
        self.do_ui_connection = True

    async def configure_daq(self):

        # should check/read file every second. If no

        cfg_fetch_freq = 2  # seconds
        cfg_fetch_time = 5  # seconds
        cfg_fetch_current = 6  # force try on first loop
        print("set self.config")
        while not self.config:

            self.status2.set_config_status(Status.CONFIGURING)

            self.read_current_config()

            if False:
                # if self.config:
                #     print(f"self.config: {self.config}")

                if not self.config and (cfg_fetch_current > cfg_fetch_time):
                    # get config from gui
                    print("Getting config from gui")
                    req = Message(
                        sender_id="daqserver",
                        msgtype="DAQServer",
                        subject="CONFIG",
                        body={
                            "purpose": "REQUEST",
                            "type": "ENVDAQ_CONFIG",
                            "server_name": self.server_name,
                        },
                    )
                    await self.to_ui_buf.put(req)
                    cfg_fetch_current = 0

                await asyncio.sleep(1)
                cfg_fetch_current += 1
                # await asyncio.sleep(cfg_fetch_freq)

                # increase time between requests to avoid traffic
                cfg_fetch_freq += 1
                if cfg_fetch_freq > 30:
                    cfg_fetch_freq = 30

            # print("Create message buffers...")
            # self.create_msg_buffer()
            # self.status2.set_config_status(Status.CONFIGURED)

            # print("Add controllers...")
            # self.add_controllers()
        if self.config:
            self.status2.set_config_status(Status.CONFIGURED)

        # self.run_state = "READY_TO_RUN"

        # reset back to original
        cfg_fetch_freq = 2

    async def resend_config_to_ui(self):
        for k, ctl in self.controller_map.items():
            ctl.resend_config_to_ui()

        await asyncio.sleep(5)  # wait for config to be sent
        await self.send_ready_to_ui()

    def start(self):
        pass

    def stop(self):
        # TODO: check if stopped already

        # self.gui_client.sync_close()
        self.status2.set_run_status(Status.STOPPING)
        for k, controller in self.controller_map.items():
            print(f"controller.stop: {k}")
            controller.stop()
        # for instrument in self.inst_map:
        #     # print(sensor)
        #     instrument.stop()

        # tasks = asyncio.Task.all_tasks()
        # for t in self.task_list:
        #     # print(t)
        #     t.cancel()
        self.status2.set_run_status(Status.STOPPED)

    async def from_child_loop(self):
        # print(f'started from_child_loop: {self.name} {self.from_child_buf}')
        # while self.from_child_buf is None:
        #     pass

        while True:
            msg = await self.from_child_buf.get()
            # print(f"daq_server:from_child_loop: {msg}")
            await self.handle(msg, src="FromChild")
            # await asyncio.sleep(.1)

    async def read_loop(self):
        while True:
            # msg = await self.inst_msg_buffer.get()
            # TODO: should handle be a async? If not, could block
            # await self.handle(msg)
            await asyncio.sleep(0.1)

    async def handle(self, msg, src=None):
        # print(f"****controller handle: {src} - {msg.to_json()}")

        if src == "FromUI":
            d = msg.to_dict()
            if "message" in d:
                content = d["message"]

                if content["SUBJECT"] == "CONFIG":
                    if content["BODY"]["purpose"] == "REPLY":
                        config = content["BODY"]["config"]
                        # self.config = config
                        # test = json.dumps(config)
                        # print(test)
                        self.save_current_config(config)

                    elif content["BODY"]["purpose"] == "PUSH":
                        config = content["BODY"]["config"]
                        print(f"new config: {config}")
                        self.save_current_config(config)
                        await asyncio.sleep(1)
                        await self.restart_daq()

                        # TODO check for enable

                        # disable current config
                        # self.disable()

                        # # enable new config
                        # self.enable_daq = True
                        # self.enable()

                    elif content["BODY"]["purpose"] == "ENABLE":

                        enable_daq = content["BODY"]["value"]

                        if enable_daq:
                            # enable new config
                            self.enable_daq = True
                            self.enable()
                        else:
                            self.enable_daq = False
                            self.disable()

                    elif content["BODY"]["purpose"] == "AUTOENABLE":
                        # config = content["BODY"]["config"]
                        autoenable_daq = content["BODY"]["value"]
                        self.config["autoenable_daq"] = autoenable_daq
                        self.save_current_config(self.config)

                        # enable if True else leave running
                        if autoenable_daq:
                            self.enable_daq = True
                            self.enable()

                    elif content["BODY"]["purpose"] == "SYNCREQUEST":
                        # print("sync DAQ")
                        # system_def = SysManager.get_definitions_all()
                        # print(f'system_def: {system_def}')
                        sys_def = Message(
                            sender_id="daqserver",
                            msgtype="DAQServer",
                            subject="CONFIG",
                            body={
                                "purpose": "SYNC",
                                "type": "SYSTEM_DEFINITION",
                                "data": SysManager.get_definitions_all(),
                            },
                        )
                        await self.to_ui_buf.put(sys_def)

                elif content["SUBJECT"] == "STATUS":
                    print(f"DAQServerStatus: {content}")
                    if content["BODY"]["purpose"] == "REQUEST":
                        print(f"Status Request: {content}")
                        await self.send_status()

                elif content["SUBJECT"] == "REGISTRATION":
                    print(f"reg: {content['BODY']}")
                    if content["BODY"]["purpose"] == "SUCCESS":
                        self.registration_key = content["BODY"]["regkey"]
                        # if content["BODY"]["config"]:

                        # self.config = content["BODY"]["config"]
                        # self.save_current_config(json.loads(content["BODY"]["config"]))
                        self.status2.set_registration_status(Status.REGISTERED)
                        print(f"server reg success: {self.status2.to_dict()}")
                        if content["BODY"]["ui_reconfig_request"]:
                            await self.resend_config_to_ui()

                elif content["SUBJECT"] == "UNREGISTRATION":
                    print(f"unreg: {content['BODY']}")
                    if content["BODY"]["purpose"] == "SUCCESS":
                        self.status2.set_registration_status(Status.NOT_REGISTERED)
                        print(f"unreg: {self.status2.get_registration_status()}")

            elif src == "FromChild":
                content = ""
                if "message" in d:
                    content = d["message"]
                # print(f"fromChild: {content}")

        await asyncio.sleep(0.01)

    async def check_ready_to_run(self):
        print("check_ready_to_run")
        wait = True
        while wait:
            wait = False
            for k, v in self.controller_map.items():
                if not v.status["ready_to_run"]:
                    wait = True
                    print(f"Waiting for controller: {k}")
                    break
            await asyncio.sleep(1)
        self.status["ready_to_run"] = True
        self.status2.set_run_status(Status.READY_TO_RUN)

    async def send_ready_to_run(self):

        print(f"run_status: {self.status2.get_run_status()}")
        while self.status2.get_run_status() != Status.READY_TO_RUN:
            # while not self.status["ready_to_run"]:
            print(f"run_status: {self.status2.get_run_status()}")
            await asyncio.sleep(1)

        print("Waiting for setup...done.")

        # PlotManager.get_server().start()

        await self.send_ready_to_ui()

        self.status2.set_run_status(Status.RUNNING)
        self.run_state = "RUNNING"

    async def send_status(self):

        # for now, only done by request but we could do like ping
        msg = Message(
            sender_id="DAQ_SERVER",
            msgtype="DAQServerStatus",
            subject="DAQServerStatus",
            body={
                # "id": self.daq_id
                "purpose": "UPDATE",
                "status": self.status2.to_dict(),
            },
        )
        await self.to_ui_buf.put(msg)

    async def ping_ui_server(self):

        # wait for things to get started before pinging
        await asyncio.sleep(5)

        while self.ui_client.isConnected():
            msg = Message(
                sender_id="DAQ_SERVER",
                msgtype="PING",
                subject="PING",
                body={
                    # "id": self.daq_id
                    "namespace": self.namespace.to_dict()
                },
            )
            # print(f"ping server: {self.namespace.to_dict()}")
            await self.to_ui_buf.put(msg)
            await asyncio.sleep(2)

    def remove_controllers(self):

        for k in self.controller_map.keys():
            self.remove_controller(k, do_pop=False)

        self.controller_map.clear()

    def remove_controller(self, controller_key, do_pop=True):
        print("removing controllers: ")
        if controller_key in self.controller_map:
            print(f"key: {controller_key}")
            asyncio.create_task(self.controller_map[controller_key].shutdown())
            if do_pop:
                self.controller_map.pop(controller_key)

    async def shutdown(self):
        # print(f"daq_server ({self.namespace['daq_server']}) shutting down...")
        print(f"daq_server ({self.namespace.get_namespace_sig()}) shutting down...")

        self.stop()
        self.disable()

        await self.deregister_from_UI()
        print("here1")
        wait_secs = 0
        while (
            self.status2.get_registration_status() != Status.NOT_REGISTERED
            and wait_secs < 10
        ):
            wait_secs += 1
            await asyncio.sleep(1)

        # try:
        #     await asyncio.sleep(5)
        # except Exception as e:
        #     print(e)

        print("here2")
        self.status2.set_run_status(Status.SHUTTING_DOWN)

        # asyncio.get_event_loop().run_until_complete(self.ws_client.shutdown())
        # if self.ws_client is not None:
        #     self.ws_client.sync_close()
        # wait_time = 0
        # print(self.status2.get_registration_status())
        # while self.status2.get_registration_status() != Status.NOT_REGISTERED:
        #     await asyncio.sleep(1)
        #     print(self.status2.get_registration_status())
        # while self.status2.get_registration_status() != Status.NOT_REGISTERED and wait_time<5:
        #     await asyncio.sleep(1)
        #     print(self.status2.get_registration_status())
        #     wait_time+=1
        # self.remove_controllers()

        self.do_ui_connection = False
        print("cancel ui task list")
        for t in self.ui_task_list:
            # print(t)
            t.cancel()

        if self.ui_client is not None:
            print("closing ui client")
            # self.loop.run_until_complete(self.ui_client.close())
            # self.ui_client.close()
            # await self.ui_client_close()
            self.ui_client = None

        # await asyncio.sleep(2)
        # self.remove_controllers()
        # for k, controller in self.controller_map.items():
        #     print(f"shutdown controller: {k}")
        #     controller.shutdown()
        # await asyncio.sleep(1)
        # for controller in self.controller_list:
        #     # print(sensor)
        #     controller.stop()

        # self.start_ui_message_loops()

        # asyncio.get_event_loop().stop()

        # self.server.close()
        # await asyncio.sleep(5)
        # print("shutdown complete.")
        # self.controller_list = []
        # self.controller_map.clear()

        self.run_state = "SHUTDOWN"
        self.status2.set_run_status(Status.SHUTDOWN)

    def start_ui_message_loops(self):
        self.ui_task_list.append(asyncio.ensure_future(self.to_ui_loop()))
        self.ui_task_list.append(asyncio.ensure_future(self.from_ui_loop()))

    def stop_ui_message_loops(self):
        # tasks = asyncio.Task.all_tasks()
        for t in self.ui_task_list:
            # print(t)
            t.cancel()
        # print("Tasks canceled")


class DAQServerManager:
    def __init__(self):
        self.server = None
        self.do_run = True

        asyncio.get_event_loop().create_task(self.run())

    async def run(self):

        while self.do_run:
            if not self.server:
                self.server = DAQServer()

            if self.server.status2.get_run_status() == Status.RESTARTING:
                await self.server.shutdown()
                await asyncio.sleep(1)
                self.server = None
                # tasks = asyncio.all_tasks(loop=event_loop)
                # for t in tasks:
                #     # print(t)
                #     t.cancel()

            await asyncio.sleep(1)

    async def shutdown(self):
        print("shutdown:")
        # for k, controller in controller_map:
        #     # print(sensor)
        #     controller.stop()
        self.do_run = False
        if self.server:
            print("server shutdown...")
            await self.server.shutdown()
            print("...done")

        tasks = asyncio.all_tasks(loop=event_loop)
        for t in tasks:
            # print(t)
            t.cancel()
        print("Tasks canceled")
        asyncio.get_event_loop().stop()
        # await asyncio.sleep(1)


async def heartbeat():
    # duration = 0
    while True:
        # print('lub-dub')
        await asyncio.sleep(util.time_to_next(10))
        # duration += 10
        # if duration > 10:
        #     raise KeyboardInterrupt


# async def output_to_screen(sensor_list):
async def output_to_screen():
    while True:
        print(datetime.utcnow().isoformat(timespec="seconds"))
        await asyncio.sleep(util.time_to_next(1))


# async def shutdown(server):
#     print("shutdown:")
#     # for k, controller in controller_map:
#     #     # print(sensor)
#     #     controller.stop()

#     if server is not None:
#         print("server shutdown...")
#         await server.shutdown()
#         print("...done")

#     tasks = asyncio.all_tasks(loop=event_loop)
#     for t in tasks:
#         # print(t)
#         t.cancel()
#     print("Tasks canceled")
#     asyncio.get_event_loop().stop()
#     # await asyncio.sleep(1)


if __name__ == "__main__":

    print(f"args: {sys.argv[1:]}")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # print(BASE_DIR)
    # sys.path.append(os.path.join(BASE_DIR, "envdsys/shared"))
    sys.path.append(os.path.join(BASE_DIR, "envdsys"))

    from daq.manager.sys_manager import SysManager
    from daq.controller.controller import ControllerFactory  # , Controller
    from client.wsclient import WSClient
    import shared.utilities.util as util
    from shared.data.message import Message
    from shared.data.status import Status
    from shared.data.namespace import Namespace

    # iface_config = {
    #     'test_interface': {
    #         'INTERFACE': {
    #             'MODULE': 'daq.interface.interface',
    #             'CLASS': 'DummyInterface',
    #         },
    #         'IFCONFIG': {
    #             'LABEL': 'test_interface',
    #             'ADDRESS': 'DummyAddress',
    #             'SerialNumber': '1234'
    #         },
    #     },
    # }

    # inst_config = {
    #     'test_dummy': {
    #         'INSTRUMENT': {
    #             'MODULE': 'daq.instrument.instrument',
    #             'CLASS': 'DummyInstrument',
    #         },
    #         'INSTCONFIG': {
    #             'DESCRIPTION': {
    #                 'LABEL': 'Test Dummy',
    #                 'SERIAL_NUMBER': '1234',
    #                 'PROPERTY_NUMBER': 'CD0001234',
    #             },
    #             'IFACE_LIST': iface_config,
    #         }
    #     }
    # }

    # cont_config = {
    #     'test_controller': {
    #         'CONTROLLER': {
    #             'MODULE': 'daq.controller.controller',
    #             'CLASS': 'DummyController',
    #         },
    #         'CONTCONFIG': {
    #             'LABEL': 'Test Controller',
    #             'INST_LIST': inst_config,
    #             'AUTO_START': True,
    #         }
    #     },
    # }

    # server_config = {
    #     'CONT_LIST': cont_config,
    # }

    # print(json.dumps(server_config))
    # with open('data.json', 'w') as f:
    # json.dump(server_config, f)
    # server = DAQServer(server_config)

    manager = DAQServerManager()
    # server = DAQServer()

    event_loop = asyncio.get_event_loop()

    task = asyncio.ensure_future(heartbeat())
    # task = asyncio.ensure_future(output_to_screen())
    task_list = asyncio.all_tasks(loop=event_loop)
    #
    try:
        event_loop.run_until_complete(asyncio.wait(task_list))
        # event_loop.run_forever()
    except KeyboardInterrupt:
        print("closing client")
        # event_loop.run_until_complete(shutdown(server))
        event_loop.run_until_complete(manager.shutdown())
        # shutdown(None)
        event_loop.run_forever()

    finally:

        print("closing event loop")
        event_loop.close()
