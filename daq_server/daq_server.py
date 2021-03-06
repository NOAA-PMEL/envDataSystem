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
# import functools
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
        self.namespace = {
            "daq_server": "localhost-default",
        }

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
                self.daq_id = f"{fqdn.split('.')[0]}-{namespace}"
                self.namespace["daq_server"] = self.daq_id.replace(" ", "")

            if "last_config_file" in server_config:
                # dir_path = os.path.dirname(os.path.realpath(__file__))
                # print(dir_path)
                self.last_config_file = server_config["last_config_file"]
                fname = self.last_config_file
                if not os.path.isabs(self.last_config_file):
                    fname = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        self.last_config_file,
                    )
                try:
                    # with open(self.last_config_file) as cfg:
                    with open(fname) as cfg:
                        self.config = json.load(cfg)
                except FileNotFoundError as e:
                    print(e)
                    pass
                except TypeError:
                    pass

            # if "current_run_config" in server_config:
            #     self.current_run_config = server_config["current_run_config"]
            #     if self.current_run_config:
            #         self.config = self.current_run_config

        except ModuleNotFoundError:
            print("settings file not found, using defaults")
            self.server_name = ""

        # override config file settings
        if server_name:
            self.server_name = server_name
        if ui_config:
            self.ui_config = ui_config
        if config:
            self.config = config

        # self.do_ui_connection = auto_connect_ui
        self.do_ui_connection = True
        self.reg_client = None
        self.ui_client = None

        self.status = {
            # 'run_status': 'STOPPED',
            "ready_to_run": False,
            "connected_to_ui": False,
            "health": "OK",
        }

        # start managers
        SysManager.start()

        # Create message buffers
        self.create_msg_buffers()

        # Begin startup
        asyncio.ensure_future(self.open())

    def create_msg_buffers(self):
        # if need config, use self.config
        # self.read_buffer = MessageBuffer(config=config)
        self.to_ui_buf = asyncio.Queue(loop=self.loop)
        self.from_child_buf = asyncio.Queue(loop=self.loop)

    def add_controllers(self):
        print("add_controllers()")
        config = self.config
        # print(config)
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
                namespace=self.namespace,
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
            sender_id="daq_server",
            msgtype="DAQServer",
            subject="REGISTRATION",
            body={
                "purpose": "ADD",
                "regkey": self.registration_key,
                # "id": self.daq_id,
                "namespace": self.namespace,
                "config": self.config,
            },
        )
        print(f"Registering with UI server: {self.namespace}")
        await self.to_ui_buf.put(req)
        self.run_state = "REGISTERING"
        # await reg_client.close()

    async def connect_to_ui(self):
        print(f"connecting to ui: {self}")
        # build ui_address
        ui_address = f'ws://{self.ui_config["host"]}'
        ui_address += f':{self.ui_config["port"]}'
        # ui_address += f"/ws/envdaq/daqserver/{self.daq_id.replace(' ', '')}"
        ui_address += f"/ws/envdaq/daqserver/{self.namespace['daq_server']}"

        print(f"ui_address: {ui_address}")

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
            if self.do_ui_connection and (
                self.ui_client is None or not self.ui_client.isConnected()
            ):
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

                await self.register_with_UI()

            await asyncio.sleep(1)

    def start_connections(self):
        print("start_connections")
        self.start_ui_connection()

    def start_ui_connection(self):
        print("start_ui_connection")
        self.task_list.append(asyncio.create_task(self.run_ui_connection()))

    async def open(self):
        # task = asyncio.ensure_future(self.read_loop())
        # self.task_list.append(task)

        # cfg_fetch_freq = 10  # seconds

        # # for k, v in self.inst_map.items():
        # #     self.inst_map[k].start()
        # ui_config = self.ui_config
        # ui_ws_address = f'ws://{ui_config["host"]}:{ui_config["port"]}/'

        # ui_ws_address += f"ws/envdaq/daqserver/{self.daq_id}"

        # # await self.register_with_UI()

        # # # wait for registration
        # # while self.run_state != "READY_TO_CONNECT":
        # #     await asyncio.sleep(1)

        # # create gui client
        # print(f"Starting ui client: {ui_ws_address}")

        # self.ui_client = WSClient(uri=ui_ws_address)
        # while self.ui_client.isConnected() is not True:
        #     # print(f'waiting for is_conncted {self.ui_client.isConnected()}')
        #     # self.gui_client = WSClient(uri=gui_ws_address)
        #     # print(f"gui client: {self.gui_client.isConnected()}")
        #     await asyncio.sleep(1)

        self.start_connections()

        # print(f"UI client is connected: {self.ui_client.isConnected()}")

        # Start heartbeat ping
        # asyncio.create_task(self.ping_ui_server())

        # print("Creating message loops")
        # self.to_ui_buf = asyncio.Queue()
        # self.start_ui_message_loops()

        # self.run_state != "READY_TO_REGISTER":
        # await self.register_with_UI()

        # # This should only be done on request
        # print("sync DAQ")
        # # system_def = SysManager.get_definitions_all()
        # # print(f'system_def: {system_def}')
        # sys_def = Message(
        #     sender_id="daqserver",
        #     msgtype="DAQServer",
        #     subject="CONFIG",
        #     body={
        #         "purpose": "SYNC",
        #         "type": "SYSTEM_DEFINITION",
        #         "data": SysManager.get_definitions_all(),
        #     },
        # )
        # await self.to_ui_buf.put(sys_def)

        # wait for registration
        while self.run_state != "READY_TO_RUN":
            await self.configure_daq()
            await asyncio.sleep(1)

        if False:
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

            # print('Waiting for config...')
            # while self.config is None:
            #     pass

            # print(self.config)
            print("Create message buffers...")
            self.create_msg_buffer()
            print("Add controllers...")
            self.add_controllers()

            # TODO: Create 'health monitor' to check for status
            #       this should allow for all components to register
            #       so we know when things are ready, broken, etc

            # for now...sleep for a set amount of time to allow
            #   everything to get set up
        print("Waiting for setup...")
        # await asyncio.sleep(10)

        self.ui_task_list.append(asyncio.create_task(self.check_ready_to_run()))

        while not self.status["ready_to_run"]:
            await asyncio.sleep(1)

        print("Waiting for setup...done.")

        # PlotManager.get_server().start()

        await self.send_ready_to_ui()

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
        print(f"** daq_server ({self.namespace['daq_server']}) ready")
        await self.to_ui_buf.put(status)

    async def configure_daq(self):

        cfg_fetch_freq = 2  # seconds

        print("set self.config")
        while not self.config:
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

            # increase time between requests to avoid traffic
            cfg_fetch_freq += 1
            if cfg_fetch_freq > 30:
                cfg_fetch_freq = 30

        # print("Create message buffers...")
        # self.create_msg_buffer()
        print("Add controllers...")
        self.add_controllers()

        self.run_state = "READY_TO_RUN"

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

        for k, controller in self.controller_map.items():
            print(controller)
            controller.stop()
        # for instrument in self.inst_map:
        #     # print(sensor)
        #     instrument.stop()

        # tasks = asyncio.Task.all_tasks()
        # for t in self.task_list:
        #     # print(t)
        #     t.cancel()

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
                        self.config = config

                        # save config locally
                        if self.last_config_file:
                            with open(self.last_config_file, "w") as cfg:
                                json.dump(self.config, cfg)

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

                elif content["SUBJECT"] == "REGISTRATION":
                    if content["BODY"]["purpose"] == "SUCCESS":
                        self.registration_key = content["BODY"]["regkey"]
                        # config = content["BODY"]["config"]
                        self.config = content["BODY"]["config"]

                        if content["BODY"]["ui_reconfig_request"]:
                            await self.resend_config_to_ui()

            elif src == "FromChild":
                content = ""
                if "message" in d:
                    content = d["message"]
                # print(f"fromChild: {content}")

        await asyncio.sleep(0.01)

    async def check_ready_to_run(self):
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
                    "namespace": self.namespace
                },
            )
            await self.to_ui_buf.put(msg)
            await asyncio.sleep(2)

    def shutdown(self):
        print(f"daq_server ({self.namespace['daq_server']}) shutting down...")

        self.stop()

        # asyncio.get_event_loop().run_until_complete(self.ws_client.shutdown())
        # if self.ws_client is not None:
        #     self.ws_client.sync_close()
        for t in self.ui_task_list:
            # print(t)
            t.cancel()

        if self.ui_client is not None:
            print("closing ui client")
            self.loop.run_until_complete(self.ui_client.close())
            # self.ui_client.close()

        # await asyncio.sleep(2)

        for k, controller in self.controller_map.items():
            print(f"shutdown controller: {k}")
            controller.shutdown()
            # await asyncio.sleep(1)
        # for controller in self.controller_list:
        #     # print(sensor)
        #     controller.stop()

        # self.start_ui_message_loops()

        # asyncio.get_event_loop().stop()

        # self.server.close()
        # await asyncio.sleep(1)
        print("shutdown complete.")
        self.run_state = "SHUTDOWN"

    def start_ui_message_loops(self):
        self.ui_task_list.append(asyncio.ensure_future(self.to_ui_loop()))
        self.ui_task_list.append(asyncio.ensure_future(self.from_ui_loop()))

    def stop_ui_message_loops(self):
        # tasks = asyncio.Task.all_tasks()
        for t in self.ui_task_list:
            # print(t)
            t.cancel()
        # print("Tasks canceled")


async def heartbeat():
    while True:
        # print('lub-dub')
        await asyncio.sleep(util.time_to_next(10))


# async def output_to_screen(sensor_list):
async def output_to_screen():
    while True:
        print(datetime.utcnow().isoformat(timespec="seconds"))
        await asyncio.sleep(util.time_to_next(1))


def shutdown(server):
    print("shutdown:")
    # for k, controller in controller_map:
    #     # print(sensor)
    #     controller.stop()

    if server is not None:
        print("server shutdown...")
        server.shutdown()
        print("...done")

    tasks = asyncio.all_tasks(loop=event_loop)
    for t in tasks:
        # print(t)
        t.cancel()
    print("Tasks canceled")
    asyncio.get_event_loop().stop()
    # await asyncio.sleep(1)


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

    server = DAQServer()

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
        shutdown(server)
        # shutdown(None)
        event_loop.run_forever()

    finally:

        print("closing event loop")
        event_loop.close()
