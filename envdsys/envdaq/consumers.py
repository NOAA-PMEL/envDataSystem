# envdaq/consumers.py
from json.decoder import JSONDecodeError
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncConsumer
import json
import os
from shared.data.namespace import Namespace
from envdaq.models import DAQController, DAQInstrument, DAQServer

from envdaq.util.daq import ConfigurationUtility
from envnet.models import DAQRegistration
from envnet.registry.registry import ServiceRegistry, DAQRegistry
from envtags.models import Configuration

# import envdaq.util.util as time_util
from shared.utilities.util import dt_to_string
from shared.data.message import Message
from envdaq.util.sync_manager import SyncManager
from plots.plots import PlotManager
from django.conf import settings
from datamanager.datamanager import DataManager
from channels.db import database_sync_to_async


class DataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.data_group_name = "data_test"
        self.data_win_group_name = "data_test_win"

        # Join room group
        await self.channel_layer.group_add(self.data_group_name, self.channel_name)

        await self.accept()

        # cfg = await channels.db.database_sync_to_async(envdaq.util.daq.get_config)()
        # print(f'consumer:cfg = {cfg}')

        # await self.data_message({'message': 'hi'})
        # await self.channel_layer.group_send(
        #     self.data_win_group_name,
        #     {
        #         'type': 'message',
        #         'message': 'hi again'
        #     }
        # )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.data_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        # print(text_data)
        # await self.data_message({'message': 'hi again'})
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"DataConsumer error {e}")
            return
        # message = text_data_json['BODY']
        message = text_data_json["message"]
        # message = text_data_json
        # message = "hi again"
        # message = text_data_json
        # print(message)
        # message = 'hi again'
        # await self.data_message({'message': message})
        # message = (
        #     self.room_name +
        #     ' - ' +
        #     self.chatroom_group_name +
        #     ' - ' +
        #     self.channel_name
        # )
        # Send message to room group

        await self.channel_layer.group_send(
            self.data_group_name, {"type": "data_message", "message": message}
        )

        # await self.channel_layer.group_send(
        #     self.data_group_name,
        #     {
        #         'type': 'data_message',
        #         'message': message
        #     }
        # )

    # Receive message from room group
    async def data_message(self, event):
        message = event["message"]
        # print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


class ControllerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.daq_host = self.scope["url_route"]["kwargs"]["daq_host"]
            self.parent_namespace = self.scope["url_route"]["kwargs"][
                "parent_namespace"
            ]
            self.controller_namespace = self.scope["url_route"]["kwargs"][
                "controller_namespace"
            ]
        except KeyError:
            self.daq_host = "localhost"
            self.parent_namespace = "default"
            self.controller_namespace = "default"

        self.controller_group_name = f"{self.daq_host}-{self.parent_namespace}-controller-{self.controller_namespace}"

        self.controller_id = f"{self.parent_namespace}-{self.controller_namespace}"
        # print(f'name = {self.namespace}')

        self.ui_save_base_path = "/tmp/envDataSystem/UIServer"
        self.ui_save_data = False
        # if "DATA_MANAGER" in settings:
        if "ui_save_base_path" in settings.DATA_MANAGER:
            self.ui_save_base_path = settings.DATA_MANAGER["ui_save_base_path"]
        if "ui_save_data" in settings.DATA_MANAGER:
            self.ui_save_data = settings.DATA_MANAGER["ui_save_data"]
        # TODO get parent_namespace as path or set this later.
        path_list = [
            self.ui_save_base_path,
            self.parent_namespace,
            self.controller_namespace,
        ]
        self.ui_save_path = os.path.join(*path_list)
        DataManager.open_datafile(self.ui_save_path)

        self.manage_group_name = "envdaq-manage"
        self.registry_group_name = "envnet-manage"

        # Join room group
        await self.channel_layer.group_add(self.manage_group_name, self.channel_name)
        await self.channel_layer.group_add(self.registry_group_name, self.channel_name)

        # Join room group
        await self.channel_layer.group_add(
            self.controller_group_name, self.channel_name
        )

        # get hostname/port for plot server
        self.hostname = self.scope["server"][0]
        self.port = self.scope["server"][1]

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.controller_group_name, self.channel_name
        )
        await self.channel_layer.group_discard(
            self.manage_group_name, self.channel_name
        )
        await self.channel_layer.group_discard(
            self.registry_group_name, self.channel_name
        )

        # DataManager.close_datafile(self.ui_save_base_path)

    # Receive message from WebSocket
    async def receive(self, text_data):

        # TODO: parse incoming message

        # if data, pass along to socket

        # if server request (e.g., send config) send
        #   message to server. Do I need to send
        #   to whole group? Does this break down
        #   as controller_req, instrument_req, etc?

        # if status, pass to socket

        # print(text_data)
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"ControllerConsumer error {e}")
            print(f"text_data: {text_data}")
            return

        message = data["message"]

        if message["SUBJECT"] == "DATA":
            # print(f'controller data message')
            await self.channel_layer.group_send(
                self.controller_group_name,
                {"type": "daq_message", "message": message},
            )
            src_id = message["SENDER_ID"]
            await PlotManager.update_data_by_source(src_id, data)
            if self.ui_save_data:
                # TODO set path and open file here.
                await DataManager.send_data(self.ui_save_path, data)

        elif message["SUBJECT"] == "PING":
            # RegistrationManager.ping(message['BODY']['namespace']['daq_server'])
            # RegistrationManager.ping(self.namespace, type="Controller")

            body = message["BODY"]
            # print(f"controller ping: {body}")
            namespace = Namespace().from_dict(body["namespace"])
            ns_sig = namespace.get_namespace_sig()

            # await DAQRegistry.ping(reg_id=self.controller_id, type="Controller")
            await DAQRegistry.ping(reg_id=ns_sig, type=Namespace.CONTROLLER)

        elif message["SUBJECT"] == "REGISTRATION":
            body = message["BODY"]
            if body["purpose"] == "ADD":

                config_requested = False

                self.namespace = Namespace().from_dict(body["namespace"])
                ns_sig = self.namespace.get_namespace_sig()
                parent_ns_sig = self.namespace.get_namespace_sig(section="PARENT")[
                    "namespace"
                ]

                controller_host = ns_sig["host"]
                controller_name = ns_sig["name"]
                controller_sig = ns_sig["namespace"]

                daq_controller = await self.get_daq_controller(
                    host=controller_host,
                    parent_ns_sig=parent_ns_sig,
                    name=controller_name,
                )

                try:
                    metadata = body["metadata"]
                    await self.update_daq_controller_metadata(daq_controller, metadata)
                    PlotManager.add_apps(metadata)
                # add metadata (measurements, etc)
                except KeyError:
                    pass

                # add plot apps from metadata

                # namespace = body["namespace"]
                registration = await DAQRegistry.get_registration(
                    # namespace=self.daqserver_namespace, type="Controller"
                    # reg_id=self.controller_id,
                    reg_id=ns_sig,
                    type=Namespace.CONTROLLER,
                )
                # print(f"registration2-get: {registration}")
                # registration2 = await DAQRegistry.register(
                #     namespace=self.daqserver_namespace,
                #     type="DAQServer",
                #     config=body["config"],
                # )
                # print(f"registration2: {registration2}")
                if registration:
                    if body["regkey"]:  # daq running (likely a reconnect)
                        # same: daq_server config takes precedence
                        print(f"body = {body}")
                        if body["regkey"] == registration["regkey"]:
                            registration["config"] = body["config"]
                            # registration["config2"] = body["config2"]
                            # RegistrationManager.update(body['id'], registration)
                            # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                            registration = await DAQRegistry.update_registration(
                                # namespace=self.daqserver_namespace,
                                # reg_id=self.controller_id,
                                reg_id=ns_sig,
                                # namespace=namespace,
                                namespace=self.namespace.to_dict(),
                                registration=registration,
                                type=Namespace.CONTROLLER,
                            )
                else:  # no reg, no connection to daq since UI start
                    if body["regkey"]:  # daq has been running
                        ui_reconfig_request = True
                        registration = {
                            # "regkey": body["regkey"],
                            "config": body["config"],
                            # "config2": body["config2"],
                        }
                        # RegistrationManager.update(body['id'], registration)
                        # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                        registration = await DAQRegistry.update_registration(
                            # self.daqserver_namespace, registration, type="Controller"
                            # reg_id=self.controller_id,
                            reg_id=ns_sig,
                            # namespace=namespace,
                            namespace=self.namespace.to_dict(),
                            registration=registration,
                            type=Namespace.CONTROLLER,
                        )
                    else:  # daq has started
                        registration = await DAQRegistry.register(
                            # body['id'],
                            # reg_id=self.controller_id,
                            reg_id=ns_sig,
                            # namespace=namespace,
                            namespace=self.namespace.to_dict(),
                            # self.daqserver_namespace,
                            config=body["config"],
                            # config2=body["config2"],
                            type=Namespace.CONTROLLER,
                        )

                # print("before reply")
                # reply = {
                #     "TYPE": "UI",
                #     "SENDER_ID": "ControllerConsumer",
                #     "TIMESTAMP": dt_to_string(),
                #     "SUBJECT": "REGISTRATION",
                #     "BODY": {
                #         "purpose": "SUCCESS",
                #         "regkey": registration["regkey"],
                #         "config": registration["config"],
                #         "config2": registration["config2"],
                #         "config_requested": config_requested,
                #     },
                # }
                reply = {
                    "TYPE": "UI",
                    "SENDER_ID": "ControllerConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "REGISTRATION",
                    "BODY": {
                        "purpose": "SUCCESS",
                        "regkey": registration["regkey"],
                        "config": registration["config"],
                        "config_requested": config_requested,
                    },
                }
                # print(f"reply: {reply}")
                # print(json.dumps(reply))
                await self.daq_message({"message": reply})

                controller_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.CONTROLLER
                )

                msg_body = {
                    "purpose": "REGISTRY",
                    "controller_registry": controller_registration_map,
                    # "controller_registry": controller_registration_map,
                    # "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="ControllerConsumer",
                    subject="DAQServerRegistry",
                    body=msg_body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.manage_group_name,
                    {
                        "type": "daq_message",
                        "message": message.to_dict()["message"],
                    },
                )

                # body={
                #     "purpose": "ADD",
                #     "key": self.registration_key,
                #     "id": self.daq_id,
                #     "config": self.config,
                # },

            if body["purpose"] == "REMOVE":
                print("remove")
                body = message["BODY"]
                namespace = Namespace().from_dict(body["namespace"])
                ns_sig = namespace.get_namespace_sig()

                # RegistrationManager.remove(body['id'])
                # RegistrationManager.remove(self.namespace, type="Controller")
                await DAQRegistry.unregister(
                    # reg_id=self.controller_id,
                    reg_id=ns_sig,
                    type=Namespace.CONTROLLER,
                )

                reply = {
                    "TYPE": "UI",
                    "SENDER_ID": "ControllerConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "UNREGISTRATION",
                    "BODY": {
                        "purpose": "SUCCESS",
                    },
                }
                print(f"success: {reply}")
                await self.daq_message({"message": reply})

                controller_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.CONTROLLER
                )

                msg_body = {
                    "purpose": "REGISTRY",
                    "controller_registry": controller_registration_map,
                    # "controller_registry": controller_registration_map,
                    # "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="ControllerConsumer",
                    subject="DAQServerRegistry",
                    body=msg_body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.manage_group_name,
                    {
                        "type": "daq_message",
                        "message": message.to_dict()["message"],
                    },
                )
                DataManager.close_datafile(self.ui_save_base_path)

        elif message["SUBJECT"] == "CONFIG":
            body = message["BODY"]
            # if (body['purpose'] == 'REQUEST'):
            #     if (body['type'] == 'ENVDAQ_CONFIG'):
            #         # do we ever get here?
            #         cfg = await ConfigurationUtility().get_config()

            #         reply = {
            #             'TYPE': 'GUI',
            #             'SENDER_ID': 'DAQServerConsumer',
            #             'TIMESTAMP': dt_to_string(),
            #             'SUBJECT': 'CONFIG',
            #             'BODY': {
            #                 'purpose': 'REPLY',
            #                 'type': 'ENVDAQ_CONFIG',
            #                 'config': cfg,
            #             }
            #         }
            #     # print(f'reply: {reply}')
            #     await self.data_message({'message': reply})
            if body["purpose"] == "SYNC":
                if body["type"] == "CONTROLLER_INSTANCE":
                    # TODO: add field to force sync option
                    # send config data to syncmanager
                    await SyncManager.sync_controller_instance(body["data"])
                    PlotManager.add_apps(body["data"])

        elif message["SUBJECT"] == "RUNCONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "ControllerConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "RUNCONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {"type": "daq_message", "message": msg},
                )

        elif message["SUBJECT"] == "CONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "ControllerConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "CONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {"type": "daq_message", "message": msg},
                )
        elif message["SUBJECT"] == "STATUS":
            if message["BODY"]["purpose"] == "REQUEST":
                # print(f'status request: {message}')
                body = message["BODY"]
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "ControllerConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "STATUS",
                    "BODY": body,
                }
                # print(f'controller request: status {msg}')
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {"type": "daq_message", "message": msg},
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {"type": "daq_message", "message": message},
                )

    # Receive message from room group
    async def daq_message(self, event):
        message = event["message"]
        # print(f' --3434-- daq_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    # Receive message from room group
    async def requested_message(self, event):
        message = event["message"]
        # print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def get_daq_controller(
        self,
        host="localhost",
        parent_ns_sig="default",
        name="default",
        force_create=True,
    ):

        daq_controller = None
        try:
            controllers = DAQController.objects.filter(name=name)

            for controller in controllers:
                ns = controller.get_namespace()
                parent_sig = ns.get_namespace_sig(section="PARENT")

                if (
                    parent_sig["host"] == host
                    and parent_sig["namespace"] == parent_ns_sig
                ):
                    return controller

        except DAQController.DoesNotExist:
            pass
            # TODO create a controller?
            # daq_server = None
            # if force_create:
            #     daq_server = DAQServer(name=name, host=host)
            #     daq_server.save()
            #     print(f"daq_server_new: {daq_server}")

        return daq_controller

    @database_sync_to_async
    def update_daq_controller_metadata(self, controller, metadata):
        if controller:
            try:
                meas_meta = metadata["measurement_meta"]
                controller.measurement_sets = meas_meta
                controller.save()
            except KeyError:
                pass

    # Receive message from room group
    async def daq_message(self, event):
        message = event["message"]
        # print(f'daq_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


class InstrumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # self.daqserver_namespace = self.scope["url_route"]["kwargs"][
            #     "daq_namespace"
            # ]
            # self.controller_namespace = self.scope["url_route"]["kwargs"][
            #     "controller_namespace"
            # ]
            self.daq_host = self.scope["url_route"]["kwargs"]["daq_host"]
            self.parent_namespace = self.scope["url_route"]["kwargs"][
                "parent_namespace"
            ]
            self.instrument_namespace = self.scope["url_route"]["kwargs"][
                "instrument_namespace"
            ]
        except KeyError:
            # self.daqserver_namespace = "default"
            # self.controller_namespace = "default"
            self.daq_host = "localhost"
            self.parent_namespace = "default"
            self.instrument_namespace = "default"

        # self.instrument_group_name = f"{self.daqserver_namespace}-{self.controller_namespace}-instrument-{self.instrument_namespace}"
        self.instrument_group_name = f"{self.daq_host}-{self.parent_namespace}-instrument-{self.instrument_namespace}"

        # self.instrument_id = f"{self.daqserver_namespace}-{self.controller_namespace}-{self.instrument_namespace}"
        self.instrument_id = f"{self.parent_namespace}-{self.instrument_namespace}"

        self.ui_save_base_path = "/tmp/envDataSystem/UIServer"
        self.ui_save_data = False
        # if "DATA_MANAGER" in settings:
        if "ui_save_base_path" in settings.DATA_MANAGER:
            self.ui_save_base_path = settings.DATA_MANAGER["ui_save_base_path"]
        if "ui_save_data" in settings.DATA_MANAGER:
            self.ui_save_data = settings.DATA_MANAGER["ui_save_data"]
        path_list = [
            # self.ui_save_base_path,
            # self.daqserver_namespace,
            # self.controller_namespace,
            # self.instrument_namespace,
            self.ui_save_base_path,
            self.parent_namespace,
            self.instrument_namespace,
        ]
        self.ui_save_path = os.path.join(*path_list)
        DataManager.open_datafile(self.ui_save_path)

        self.manage_group_name = "envdaq-manage"
        self.registry_group_name = "envnet-manage"
        await self.channel_layer.group_add(self.manage_group_name, self.channel_name)
        await self.channel_layer.group_add(self.registry_group_name, self.channel_name)

        # print(f'name = {self.instrument_namespace}')
        # Join room group
        await self.channel_layer.group_add(
            self.instrument_group_name, self.channel_name
        )

        self.hostname = self.scope["server"][0]
        self.port = self.scope["server"][1]

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.instrument_group_name, self.channel_name
        )
        await self.channel_layer.group_discard(
            self.manage_group_name, self.channel_name
        )
        await self.channel_layer.group_discard(
            self.registry_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):

        # TODO: parse incoming message

        # if data, pass along to socket

        # if server request (e.g., send config) send
        #   message to server. Do I need to send
        #   to whole group? Does this break down
        #   as controller_req, instrument_req, etc?

        # if status, pass to socket

        # print(f'^^^^^ {text_data}')
        # text_data_json = json.loads(text_data)
        # message = text_data_json['message']
        # # print(f'InstrumentConsumer.receive: {message}')

        # await self.channel_layer.group_send(
        #     self.instrument_group_name,
        #     {
        #         'type': 'daq_message',
        #         'message': message
        #     }
        # )

        # print(text_data)
        # text_data_json = json.loads(text_data)
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"InstrumentConsumer error {e}")
            print(f"text_data: {text_data}")
            return

        message = data["message"]
        # print(f'message: {message}')
        if message["SUBJECT"] == "DATA":
            # print(f'data message')
            await self.channel_layer.group_send(
                self.instrument_group_name,
                {"type": "daq_message", "message": message},
            )
            # print(f'123123123 data: {message}')
            src_id = message["SENDER_ID"]
            print(f"*** update plot: {src_id}, {data}")
            await PlotManager.update_data_by_source(src_id, data)
            # if self.ui_save_data:
            #     await DataManager.send_data(self.ui_save_path, data)

            # print(f'message ***111***: {message}')
            if "BODY" in message and "DATA_REQUEST_LIST" in message["BODY"]:
                # TODO: make this a utility function
                for dr in message["BODY"]["DATA_REQUEST_LIST"]:
                    if dr["class"] == "CONTROLLER":
                        controller_ns = Namespace().from_dict(dr["namespace"])
                        controller_parent_ns_sig = controller_ns.get_namespace_sig(
                            section="PARENT"
                        )["namespace"]

                        # group_name = f'controller_{dr["alias"]["name"]}'
                        # group_name = f"{self.daqserver_namespace}-controller-{self.controller_namespace}"
                        group_name = f"{self.daq_host}-{controller_parent_ns_sig}-controller-{controller_ns.name}"

                        await self.channel_layer.group_send(
                            group_name.replace(" ", ""),
                            {"type": "daq_message", "message": message},
                        )

            # if 'alias' in message['BODY']:
            #     alias_name = message['BODY']['alias']['name']
            # alias_name = message.BODY.alias.name
            # print(f'alias: {alias_name}')
            # await PlotManager.update_data_by_key(alias_name, data)

        elif message["SUBJECT"] == "SETTINGS":
            # print(f'settings: {message}')
            await self.channel_layer.group_send(
                self.instrument_group_name,
                {"type": "daq_message", "message": message},
            )

        elif message["SUBJECT"] == "PING":
            # await DAQRegistry.ping(reg_id=self.instrument_id, type="Instrument")

            body = message["BODY"]
            # print(f"instrument ping: {body}")
            namespace = Namespace().from_dict(body["namespace"])
            ns_sig = namespace.get_namespace_sig()

            # await DAQRegistry.ping(reg_id=self.controller_id, type="Controller")
            await DAQRegistry.ping(reg_id=ns_sig, type=Namespace.INSTRUMENT)

        elif message["SUBJECT"] == "REGISTRATION":
            body = message["BODY"]
            if body["purpose"] == "ADD":
                # daq_namespace = body["namespace"]["daq_server"]
                # namespace = body["namespace"]
                # print(f'namespace: {self.daqserver_namespace}, {daq_namespace}')
                # registration = RegistrationManager.get(body['id'])
                # registration = RegistrationManager.get(daq_namespace, type="DAQServer")
                ui_reconfig_request = False

                self.namespace = Namespace().from_dict(body["namespace"])
                ns_sig = self.namespace.get_namespace_sig()
                parent_ns_sig = self.namespace.get_namespace_sig(section="PARENT")[
                    "namespace"
                ]

                instrument_host = ns_sig["host"]
                instrument_name = ns_sig["name"]
                instrument_sig = ns_sig["namespace"]

                daq_instrument = await self.get_daq_instrument(
                    host=instrument_host,
                    parent_ns_sig=parent_ns_sig,
                    name=instrument_name,
                )

                try:
                    metadata = body["metadata"]
                    await self.update_daq_instrument_metadata(daq_instrument, metadata)
                    PlotManager.add_apps(metadata)
                except KeyError:
                    pass

                registration = await DAQRegistry.get_registration(
                    # reg_id=self.instrument_id, type="Instrument"
                    reg_id=ns_sig,
                    type=Namespace.INSTRUMENT,
                )
                # print(f"registration2-get: {registration}")
                # registration2 = await DAQRegistry.register(
                #     namespace=self.daqserver_namespace,
                #     type="DAQServer",
                #     config=body["config"],
                # )
                # print(f"registration2: {registration2}")
                if registration:
                    if body["regkey"]:  # daq running (likely a reconnect)
                        # same: daq_server config takes precedence
                        if body["regkey"] == registration["regkey"]:
                            registration["config"] = body["config"]
                            # RegistrationManager.update(body['id'], registration)
                            # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                            registration = await DAQRegistry.update_registration(
                                # reg_id=self.instrument_id,
                                # namespace=namespace,
                                # registration=registration,
                                # type="Instrument",
                                reg_id=ns_sig,
                                # namespace=namespace,
                                namespace=self.namespace.to_dict(),
                                registration=registration,
                                type=Namespace.INSTRUMENT,
                            )
                else:  # no reg, no connection to daq since UI start
                    if body["regkey"]:  # daq has been running
                        ui_reconfig_request = True
                        registration = {
                            # "regkey": body["regkey"],
                            "config": body["config"],
                        }
                        # RegistrationManager.update(body['id'], registration)
                        # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                        registration = await DAQRegistry.update_registration(
                            # reg_id=self.instrument_id,
                            # namespace=namespace,
                            # registration=registration,
                            # type="Instrument",
                            reg_id=ns_sig,
                            # namespace=namespace,
                            namespace=self.namespace.to_dict(),
                            registration=registration,
                            type=Namespace.INSTRUMENT,
                        )
                    else:  # daq has started
                        registration = await DAQRegistry.register(
                            # body['id'],
                            # reg_id=self.instrument_id,
                            # namespace=namespace,
                            # config=body["config"],
                            # type="Instrument",
                            reg_id=ns_sig,
                            namespace=self.namespace.to_dict(),
                            config=body["config"],
                            type=Namespace.INSTRUMENT,
                        )

                reply = {
                    "TYPE": "UI",
                    "SENDER_ID": "InstrumentConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "REGISTRATION",
                    "BODY": {
                        "purpose": "SUCCESS",
                        "regkey": registration["regkey"],
                        "config": registration["config"],
                        "ui_reconfig_request": ui_reconfig_request,
                    },
                }
                # print(f"reply2: {json.dumps(reply)}")

                # ui_reconfig_request = False
                # registration = RegistrationManager.get(
                #     self.daqserver_namespace, type="DAQServer"
                # )
                # if registration:  # reg exists - UI running, unknown daq state
                #     # if daq_server has key, check against current registration
                #     if body["regkey"]:  # daq running (likely a reconnect)
                #         # same: daq_server config takes precedence
                #         if body["regkey"] == registration["regkey"]:
                #             registration["config"] = body["config"]
                #             # RegistrationManager.update(body['id'], registration)
                #             # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                #             RegistrationManager.update(
                #                 self.daqserver_namespace, registration, type="DAQServer"
                #             )

                # else:  # no reg, no connection to daq since UI start
                #     if body["regkey"]:  # daq has been running
                #         ui_reconfig_request = True
                #         registration = {
                #             "regkey": body["regkey"],
                #             "config": body["config"],
                #         }
                #         # RegistrationManager.update(body['id'], registration)
                #         # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                #         RegistrationManager.update(
                #             self.daqserver_namespace, registration, type="DAQServer"
                #         )
                #     else:  # daq has started
                #         registration = RegistrationManager.add(
                #             # body['id'],
                #             self.daqserver_namespace,
                #             config=body["config"],
                #             type="DAQServer",
                #         )

                # print("before reply")
                # reply = {
                #     "TYPE": "UI",
                #     "SENDER_ID": "DAQServerConsumer",
                #     "TIMESTAMP": dt_to_string(),
                #     "SUBJECT": "REGISTRATION",
                #     "BODY": {
                #         "purpose": "SUCCESS",
                #         "regkey": registration["regkey"],
                #         "config": registration["config"],
                #         "ui_reconfig_request": ui_reconfig_request,
                #     },
                # }
                # print(f"reply: {reply}")
                # print(json.dumps(reply))
                await self.daq_message({"message": reply})

                instrument_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.INSTRUMENT
                )

                msg_body = {
                    "purpose": "REGISTRY",
                    "instrument_registry": instrument_registration_map,
                    # "controller_registry": controller_registration_map,
                    # "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="InstrumentConsumer",
                    subject="DAQServerRegistry",
                    body=msg_body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.manage_group_name,
                    {
                        "type": "daq_message",
                        "message": message.to_dict()["message"],
                    },
                )

            if body["purpose"] == "REMOVE":
                print("remove")

                body = message["BODY"]
                namespace = Namespace().from_dict(body["namespace"])
                ns_sig = namespace.get_namespace_sig()

                await DAQRegistry.unregister(
                    # reg_id=self.controller_id,
                    reg_id=ns_sig,
                    type=Namespace.INSTRUMENT,
                )

                reply = {
                    "TYPE": "UI",
                    "SENDER_ID": "InstrumentConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "UNREGISTRATION",
                    "BODY": {
                        "purpose": "SUCCESS",
                    },
                }
                print(f"success: {reply}")
                await self.daq_message({"message": reply})

                instrument_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.INSTRUMENT
                )

                msg_body = {
                    "purpose": "REGISTRY",
                    "instrument_registry": instrument_registration_map,
                    # "controller_registry": controller_registration_map,
                    # "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="InstrumentConsumer",
                    subject="DAQServerRegistry",
                    body=msg_body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.manage_group_name,
                    {
                        "type": "daq_message",
                        "message": message.to_dict()["message"],
                    },
                )
                DataManager.close_datafile(self.ui_save_base_path)

                # RegistrationManager.remove(body['id'])
                # RegistrationManager.remove(self.daqserver_namespace, type="DAQServer")
                # await DAQRegistry.unregister(
                #     namespace=self.instrument_id, type="Instrument"
                # )

        elif message["SUBJECT"] == "CONFIG":
            body = message["BODY"]
            # if (body['purpose'] == 'REQUEST'):
            #     if (body['type'] == 'ENVDAQ_CONFIG'):
            #         # do we ever get here?
            #         cfg = await ConfigurationUtility().get_config()

            #         reply = {
            #             'TYPE': 'GUI',
            #             'SENDER_ID': 'DAQServerConsumer',
            #             'TIMESTAMP': dt_to_string(),
            #             'SUBJECT': 'CONFIG',
            #             'BODY': {
            #                 'purpose': 'REPLY',
            #                 'type': 'ENVDAQ_CONFIG',
            #                 'config': cfg,
            #             }
            #         }
            #     # print(f'reply: {reply}')
            #     await self.data_message({'message': reply})
            if body["purpose"] == "SYNC":
                if body["type"] == "INSTRUMENT_INSTANCE":
                    # TODO: add field to force sync option
                    # send config data to syncmanager
                    await SyncManager.sync_instrument_instance(body["data"])
                    PlotManager.add_apps(body["data"])
        elif message["SUBJECT"] == "RUNCONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "InstrumentConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "RUNCONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {"type": "daq_message", "message": msg},
                )

        elif message["SUBJECT"] == "CONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "InstrumentConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "CONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {"type": "daq_message", "message": msg},
                )

        elif message["SUBJECT"] == "STATUS":
            if message["BODY"]["purpose"] == "REQUEST":
                body = message["BODY"]
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "InstrumentConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "STATUS",
                    "BODY": body,
                }
                print(f"consumer: {message}")
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {"type": "daq_message", "message": msg},
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {"type": "daq_message", "message": message},
                )

                # await self.daq_message(
                #     {'message': msg}
                # )
                # print(f'msg: {msg}')

    @database_sync_to_async
    def get_daq_instrument(
        self,
        host="localhost",
        parent_ns_sig="default",
        name="default",
        force_create=True,
    ):

        daq_instrument = None
        try:
            instruments = DAQInstrument.objects.filter(name=name)

            for instrument in instruments:
                ns = instrument.get_namespace()
                parent_sig = ns.get_namespace_sig(section="PARENT")

                if (
                    parent_sig["host"] == host
                    and parent_sig["namespace"] == parent_ns_sig
                ):
                    return instrument

        except DAQInstrument.DoesNotExist:
            pass
            # TODO create a controller?
            # daq_server = None
            # if force_create:
            #     daq_server = DAQServer(name=name, host=host)
            #     daq_server.save()
            #     print(f"daq_server_new: {daq_server}")

        return daq_instrument

    @database_sync_to_async
    def update_daq_instrument_metadata(self, instrument, metadata):
        if instrument:
            try:
                meas_meta = metadata["measurement_meta"]
                instrument.measurement_sets = meas_meta
                instrument.save()
            except KeyError:
                pass

    # Receive message from room group
    async def daq_message(self, event):
        message = event["message"]
        # print(f'daq_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


class InterfaceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.interface_name = self.scope["url_route"]["kwargs"]["interface_name"]
        self.interface_group_name = "interface_{}".format(self.interface_name)
        # print(f'name = {self.interface_name}')
        # Join room group
        await self.channel_layer.group_add(self.interface_group_name, self.channel_name)

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.interface_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        pass
        # TODO: parse incoming message

        # if data, pass along to socket

        # if server request (e.g., send config) send
        #   message to server. Do I need to send
        #   to whole group? Does this break down
        #   as controller_req, instrument_req, etc?

        # if status, pass to socket

        # print(text_data)
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"InterfaceConsumer error {e}")
            return

        message = text_data_json["message"]

        # Send message to room group
        # await self.channel_layer.group_send(
        #     self.interface_group_name,
        #     {
        #         'type': 'interface_message',
        #         'message': message
        #     }
        # )

        if message["SUBJECT"] == "DATA":
            # print(f'controller data message')
            await self.channel_layer.group_send(
                self.interface_group_name,
                {"type": "interface_message", "message": message},
            )

        elif message["SUBJECT"] == "CONFIG":
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                pass
                # if (body['type'] == 'ENVDAQ_CONFIG'):
                #     # do we ever get here?
                #     cfg = await ConfigurationUtility().get_config()

                #     reply = {
                #         'TYPE': 'GUI',
                #         'SENDER_ID': 'InterfaceConsumer',
                #         'TIMESTAMP': dt_to_string(),
                #         'SUBJECT': 'CONFIG',
                #         'BODY': {
                #             'purpose': 'REPLY',
                #             'type': 'ENVDAQ_CONFIG',
                #             'config': cfg,
                #         }
                #     }
                # # print(f'reply: {reply}')
                # await self.interface_message({'message': reply})
            # if (body['purpose'] == 'SYNC'):
            #     if (body['type'] == 'CONTROLLER_INSTANCE'):
            #         # TODO: add field to force sync option
            #         # send config data to syncmanager
            #         await SyncManager.sync_interface_instance(body['data'])

        elif message["SUBJECT"] == "RUNCONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "InterfaceConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "RUNCONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {"type": "interface_message", "message": msg},
                )

        elif message["SUBJECT"] == "CONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "InterfaceConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "CONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {"type": "interface_message", "message": msg},
                )
        elif message["SUBJECT"] == "STATUS":
            if message["BODY"]["purpose"] == "REQUEST":
                # print(f'status request: {message}')
                body = message["BODY"]
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "InterfaceConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "STATUS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {"type": "interface_message", "message": msg},
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {"type": "interface_message", "message": message},
                )

    # Receive message from room group
    async def interface_message(self, event):
        message = event["message"]
        # print(f'interface_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


class IFDeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.ifdevice_name = self.scope["url_route"]["kwargs"]["ifdevice_name"]
        self.ifdevice_group_name = "ifdevice_{}".format(self.ifdevice_name)
        # print(f'name = {self.ifdevice_name}')
        # Join room group
        await self.channel_layer.group_add(self.ifdevice_group_name, self.channel_name)

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.ifdevice_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):

        # TODO: parse incoming message

        # if data, pass along to socket

        # if server request (e.g., send config) send
        #   message to server. Do I need to send
        #   to whole group? Does this break down
        #   as controller_req, instrument_req, etc?

        # if status, pass to socket

        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"IFDeviceConsumer error {e}")
            return

        message = text_data_json["message"]

        # await self.channel_layer.group_send(
        #     self.ifdevice_group_name,
        #     {
        #         'type': 'ifdevice_message',
        #         'message': message
        #     }
        # )

        if message["SUBJECT"] == "DATA":
            # print(f'controller data message')
            await self.channel_layer.group_send(
                self.ifdevice_group_name,
                {"type": "ifdevice_message", "message": message},
            )

        elif message["SUBJECT"] == "CONFIG":
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                pass
                # if (body['type'] == 'ENVDAQ_CONFIG'):
                #     # do we ever get here?
                #     cfg = await ConfigurationUtility().get_config()

                #     reply = {
                #         'TYPE': 'GUI',
                #         'SENDER_ID': 'InterfaceConsumer',
                #         'TIMESTAMP': dt_to_string(),
                #         'SUBJECT': 'CONFIG',
                #         'BODY': {
                #             'purpose': 'REPLY',
                #             'type': 'ENVDAQ_CONFIG',
                #             'config': cfg,
                #         }
                #     }
                # # print(f'reply: {reply}')
                # await self.interface_message({'message': reply})
            # if (body['purpose'] == 'SYNC'):
            #     if (body['type'] == 'CONTROLLER_INSTANCE'):
            #         # TODO: add field to force sync option
            #         # send config data to syncmanager
            #         await SyncManager.sync_interface_instance(body['data'])

        elif message["SUBJECT"] == "RUNCONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "IFDeviceConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "RUNCONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {"type": "ifdevice_message", "message": msg},
                )

        elif message["SUBJECT"] == "CONTROLS":
            # print(f'message: {message}')
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "IFDeviceConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "CONTROLS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {"type": "ifdevice_message", "message": msg},
                )
        elif message["SUBJECT"] == "STATUS":
            if message["BODY"]["purpose"] == "REQUEST":
                # print(f'status request: {message}')
                body = message["BODY"]
                msg = {
                    "TYPE": "UI",
                    "SENDER_ID": "IFDeviceConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "STATUS",
                    "BODY": body,
                }
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {"type": "ifdevice_message", "message": msg},
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {"type": "ifdevice_message", "message": message},
                )

    # Receive message from room group
    async def ifdevice_message(self, event):
        message = event["message"]
        # print(f'ifdevice_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


class DAQServerConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        # print(f"scope: {self.scope}")
        # self.namespace = Namespace()
        try:
            self.daqserver_host = self.scope["url_route"]["kwargs"]["daq_host"]
            self.daqserver_namespace = self.scope["url_route"]["kwargs"][
                "daq_namespace"
            ]
            # self.daqserver_group_name = f"daqserver_{self.scope['url_route']['kwargs']['daq_namespace']}_messages"
        except KeyError:
            self.daqserver_host = "localhost"
            self.daqserver_namespace = "default"
            self.daqserver_group_name = "daq_default_messages"

        self.daqserver_group_name = (
            f"daqserver_{self.daqserver_host}_{self.daqserver_namespace}_messages"
        )
        self.manage_group_name = "envdaq-manage"
        self.registry_group_name = "envnet-manage"

        # self.server_name = (
        #     self.scope['url_route']['kwargs']['server_name']
        # )
        self.hostname = self.scope["server"][0]
        self.port = self.scope["server"][1]
        # print(f'hostname:port : {self.hostname}:{self.port}')
        # self.daqserver_group_name = 'daq_messages'

        # Join room group
        await self.channel_layer.group_add(self.daqserver_group_name, self.channel_name)
        await self.channel_layer.group_add(self.manage_group_name, self.channel_name)
        await self.channel_layer.group_add(self.registry_group_name, self.channel_name)

        await self.accept()

        # get current daq
        # TODO: add ability to key this with name, tags, project, etc
        # daq = envdaq.util.daq.get_daq()
        # cfg = ConfigurationUtility().get_config()
        # print(f'consumer:cfg = {cfg}')

        # await self.data_message({'message': 'hi'})
        # await self.channel_layer.group_send(
        #     self.data_win_group_name,
        #     {
        #         'type': 'message',
        #         'message': 'hi again'
        #     }
        # )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.daqserver_group_name, self.channel_name
        )
        await self.channel_layer.group_discard(
            self.manage_group_name, self.channel_name
        )
        await self.channel_layer.group_discard(
            self.registry_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # print(text_data)
        # text_data_json = json.loads(text_data)
        # print(f"***** daqserverconsumer.receive")
        try:
            data = json.loads(text_data)
            # print(f"receive.data: {data}")
        except json.JSONDecodeError as e:
            print(f"DAQServerConsumer error {e}")
            return

        message = data["message"]
        # print(f'999999 message: {message}')

        if message["SUBJECT"] == "PING":
            body = message["BODY"]
            # print(f"server ping: {body}")
            namespace = Namespace().from_dict(body["namespace"])
            ns_sig = namespace.get_namespace_sig()
            # RegistrationManager.ping(message['BODY']['namespace']['daq_server'])
            # RegistrationManager.ping(self.daqserver_namespace)

            # await self.channel_layer.group_send(
            #     self.registry_group_name,
            #     {"type": "daq_message", "message": message},
            # )
            # await DAQRegistry.ping(reg_id=self.daqserver_namespace, type="DAQServer")
            await DAQRegistry.ping(reg_id=ns_sig, type=Namespace.DAQSERVER)

        elif message["SUBJECT"] == "REGISTRATION":
            body = message["BODY"]

            # TODO do I need this?
            await self.channel_layer.group_send(
                self.registry_group_name,
                {"type": "daq_message", "message": message},
            )

            if body["purpose"] == "ADD":
                # print('add')
                # print(f"add: {self.scope}")
                print(f"body: {body}")
                print(f"namespace: {body['namespace']}, {body['namespace']['name']}")

                self.namespace = Namespace().from_dict(body["namespace"])
                # self.namespace = namespace
                ns_sig = self.namespace.get_namespace_sig()
                print(f"ns_sig: {ns_sig}")

                # daq_id = namespace.get_namespace()
                # self.daqserver_namespace = daq_id
                daq_host = ns_sig["host"]
                daq_name = ns_sig["name"]
                daq_sig = ns_sig["namespace"]
                # ns_name = namespace.name
                # daq_id = body["namespace"]["daq_server"]
                # namespace = body["namespace"]
                # uri = body["uri"]

                daq_server = await self.get_daq_server(host=daq_host, name=daq_name)
                print(f"daq_server: {daq_server}, {daq_host}, {daq_name}, {daq_server}")

                ui_config_version = None
                if daq_server:
                    ui_config_version = await sync_to_async(daq_server.get_config)()

                daq_config_version = None
                try:
                    # print(f"daq_config: {body['config']}, \n {body['config2']}")
                    # daq_config_version = json.loads(body["config2"])
                    daq_config_version = body["config"]
                except (KeyError, JSONDecodeError):
                    pass

                current_config_version = dict()
                if ui_config_version and daq_config_version:
                    current_config_version = daq_config_version
                    if ui_config_version != daq_config_version:
                        print("***ALERT***: Config versions are different!")

                if ui_config_version:
                    print(f"using UI configuration version")
                    current_config_version = ui_config_version
                if daq_config_version:  # takes precedence
                    print(f"using daq_server configuration version")
                    current_config_version = daq_config_version

                current_config_version = daq_config_version

                # print(f'namespace: {self.daqserver_namespace}, {daq_namespace}')
                # registration = RegistrationManager.get(body['id'])
                # registration = RegistrationManager.get(daq_namespace, type="DAQServer")
                ui_reconfig_request = False

                # registration = await DAQRegistry.get_registration(
                #     # namespace=self.daqserver_namespace, type="DAQServer"
                #     # reg_id=daq_id, type="DAQServer"
                #     reg_id2=ns_sig,
                #     type="DAQServer",
                # )
                registration = await DAQRegistry.get_registration(
                    # namespace=self.daqserver_namespace, type="DAQServer"
                    # reg_id=daq_id, type="DAQServer"
                    reg_id=ns_sig,
                    type=Namespace.DAQSERVER,
                )
                # print(f"registration2-get: {registration}")
                # registration2 = await DAQRegistry.register(
                #     namespace=self.daqserver_namespace,
                #     type="DAQServer",
                #     config=body["config"],
                # )
                print(f"registration: {registration}")
                if registration:
                    if body["regkey"]:  # daq running (likely a reconnect)
                        # same: daq_server config takes precedence
                        if body["regkey"] == registration["regkey"]:
                            registration["config"] = body["config"]
                            # registration["config2"] = json.loads(body["config2"])
                            # RegistrationManager.update(body['id'], registration)
                            # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                            # registration = await DAQRegistry.update_registration(
                            #     # namespace=self.daqserver_namespace,
                            #     # reg_id=daq_id,
                            #     reg_id2=ns_sig,
                            #     namespace=self.namespace.to_dict(),
                            #     registration=registration,
                            #     type="DAQServer",
                            # )
                            registration = await DAQRegistry.update_registration(
                                # namespace=self.daqserver_namespace,
                                # reg_id=daq_id,
                                reg_id=ns_sig,
                                namespace=self.namespace.to_dict(),
                                registration=registration,
                                type=Namespace.DAQSERVER,
                            )
                else:  # no reg, no connection to daq since UI start
                    if body["regkey"]:  # daq has been running
                        ui_reconfig_request = True
                        registration = {
                            # "regkey": body["regkey"],
                            "config": body["config"],
                            # "config2": json.loads(body["config2"]),
                        }
                        # RegistrationManager.update(body['id'], registration)
                        # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
                        # registration = await DAQRegistry.update_registration(
                        #     # namespace=self.daqserver_namespace,
                        #     # reg_id=daq_id,
                        #     reg_id2=ns_sig,
                        #     namespace=self.namespace.to_dict(),
                        #     registration=registration,
                        #     type="DAQServer",
                        # )
                        registration = await DAQRegistry.update_registration(
                            reg_id=ns_sig,
                            namespace=self.namespace.to_dict(),
                            registration=registration,
                            type=Namespace.DAQSERVER,
                        )
                    else:  # daq has started
                        # registration = await DAQRegistry.register(
                        #     # body['id'],
                        #     # namespace=self.daqserver_namespace,
                        #     # reg_id=daq_id,
                        #     reg_id2=ns_sig,
                        #     namespace=self.namespace.to_dict(),
                        #     config=body["config"],
                        #     config2=json.loads(body["config2"]),
                        #     type="DAQServer",
                        # )
                        registration = await DAQRegistry.register(
                            reg_id=ns_sig,
                            namespace=self.namespace.to_dict(),
                            config=body["config"],
                            type=Namespace.DAQSERVER,
                        )
                # print(f"config2: {json.loads(body['config2'])}")
                print(f"registration: {registration}")
                print(f"self.namespace: {self.namespace}")
                # reply = {
                #     "TYPE": "UI",
                #     "SENDER_ID": "DAQServerConsumer",
                #     "TIMESTAMP": dt_to_string(),
                #     "SUBJECT": "REGISTRATION",
                #     "BODY": {
                #         "purpose": "SUCCESS",
                #         "regkey": registration["regkey"],
                #         "config": registration["config"],
                #         "config2": registration["config2"],
                #         "ui_reconfig_request": ui_reconfig_request,
                #     },
                # }
                reply = {
                    "TYPE": "UI",
                    "SENDER_ID": "DAQServerConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "REGISTRATION",
                    "BODY": {
                        "purpose": "SUCCESS",
                        "regkey": registration["regkey"],
                        "config": registration["config"],
                        "ui_reconfig_request": ui_reconfig_request,
                    },
                }
                await self.daq_message({"message": reply})

                daqserver_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.DAQSERVER
                )
                # controller_registration_map = await DAQRegistry.get_registry(type="Controller")
                # instrument_registration_map = await DAQRegistry.get_registry(type="Instrument")
                # print(f"<<< daqserver_registration_map: {daqserver_registration_map}")
                # print(f"<<< controller_registration_map: {controller_registration_map}\n\n")
                # print(f"<<< instrument_registration_map: {instrument_registration_map}\n\n")
                msg_body = {
                    "purpose": "REGISTRY",
                    "daqserver_registry": daqserver_registration_map,
                    # "controller_registry": controller_registration_map,
                    # "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="DAQServerConsumer",
                    subject="DAQServerRegistry",
                    body=msg_body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.manage_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

                # body = {
                #     "purpose": "UPDATE_CLIENT",
                # }
                # message = Message(
                #     msgtype="UI",
                #     sender_id="DAQServerConsumer",
                #     subject="DAQServerRegistry",
                #     body=body,
                # )
                # print(f"register:update_client: {message.to_dict()}")
                # await self.channel_layer.group_send(
                #     self.manage_group_name,
                #     {"type": "daq_message", "message": message.to_dict()["message"]},
                # )

                # DAQServerRegistry
                # UPDATE_CLIENT

                # body={
                #     "purpose": "ADD",
                #     "key": self.registration_key,
                #     "id": self.daq_id,
                #     "config": self.config,
                # },

            elif body["purpose"] == "REMOVE":
                print("remove")
                # RegistrationManager.remove(body['id'])
                # RegistrationManager.remove(self.daqserver_namespace, type="DAQServer")
                body = message["BODY"]
                # print(f"ping: {body}")
                namespace = Namespace().from_dict(body["namespace"])
                ns_sig = namespace.get_namespace_sig()

                # await DAQRegistry.unregister(
                #     # reg_id=self.daqserver_namespace, type="DAQServer"
                #     reg_id2=daq_ns,
                #     type="DAQServer",
                # )
                await DAQRegistry.unregister(
                    # reg_id=self.daqserver_namespace, type="DAQServer"
                    reg_id=ns_sig,
                    type=Namespace.DAQSERVER,
                )
                reply = {
                    "TYPE": "UI",
                    "SENDER_ID": "DAQServerConsumer",
                    "TIMESTAMP": dt_to_string(),
                    "SUBJECT": "UNREGISTRATION",
                    "BODY": {
                        "purpose": "SUCCESS",
                    },
                }
                print(f"success: {reply}")
                await self.daq_message({"message": reply})

                PlotManager.remove_server()
                # # update registrations on clients
                # try:
                #     regs = DAQRegistration.objects.all()
                #     # print(f'regs: {regs}')
                # except DAQRegistration.DoesNotexist:
                #     regs = []

                # daq_registration_map = {}
                # if regs:
                #     for reg in regs:
                #         daq_registration_map[reg.namespace] = reg.get_registration()

                daqserver_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.DAQSERVER
                )
                # controller_registration_map = await DAQRegistry.get_registry(type="Controller")
                # instrument_registration_map = await DAQRegistry.get_registry(type="Instrument")
                # print(f"<<< daqserver_registration_map: {daqserver_registration_map}")
                # print(f"<<< controller_registration_map: {controller_registration_map}\n\n")
                # print(f"<<< instrument_registration_map: {instrument_registration_map}\n\n")
                msg_body = {
                    "purpose": "REGISTRY",
                    "daqserver_registry": daqserver_registration_map,
                    # "controller_registry": controller_registration_map,
                    # "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="DAQServerConsumer",
                    subject="DAQServerRegistry",
                    body=msg_body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.manage_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

        elif message["SUBJECT"] == "DAQServerStatus":

            body = message["BODY"]
            if body["purpose"] == "REQUEST":

                body = {
                    "purpose": "REQUEST",
                }
                message = Message(
                    msgtype="UI",
                    sender_id="DAQServerConsumer",
                    subject="STATUS",
                    body=body,
                )
                print(f"request_status: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.daqserver_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

            elif body["purpose"] == "UPDATE":

                body = {"purpose": "UPDATE", "status": body["status"]}
                message = Message(
                    msgtype="UI",
                    sender_id="DAQServerConsumer",
                    subject="DAQServerStatus",
                    body=body,
                )
                print(f"update_status: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.daqserver_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

        elif message["SUBJECT"] == "DAQServerConfig":

            # print(f"REQUEST: self.namespace: {self.namespace.get_namespace_sig()}")
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                # ns_sig = self.namespace.get_namespace_sig()
                daq_host = self.daqserver_host
                daq_name = self.daqserver_namespace
                # ns_namespace = ns_sig["namespace"]

                server_map = dict()
                current_daq_server = await self.get_daq_server(
                    host=daq_host, name=daq_name
                )
                if current_daq_server:
                    print(f"current_daq_server: {current_daq_server}")
                    ui_current_config = await sync_to_async(
                        current_daq_server.get_config
                    )()
                    namespace = current_daq_server.get_namespace()
                    ns_sig = namespace.get_namespace_sig()

                    # ns_host = self.namespace[""]
                    # current_reg = await DAQRegistry.get_registration(
                    #     reg_id2=ns_sig,
                    #     type="DAQServer"
                    #     # reg_id=self.daqserver_namespace, type="DAQServer"
                    # )
                    current_reg = await DAQRegistry.get_registration(
                        reg_id=ns_sig,
                        type=Namespace.DAQSERVER
                        # reg_id=self.daqserver_namespace, type="DAQServer"
                    )
                    print(f"id={self.daqserver_namespace}, reg={current_reg}")
                    current_config = {}
                    if current_reg:
                        # current_config = current_reg["config2"]
                        current_config = current_reg["config"]

                    if ui_current_config != current_config:
                        print("***ALERT***: Config versions are different!")

                    # print(f"()()current_config: {current_config}, {type(current_config)}")
                    # config_list = await self.get_config_list()
                    server_map = await self.get_daqserver_map()
                    # print(f"&&& {config_list}")
                    # get list of available configurations
                    # config_list = []
                    # try:
                    #     configs = await database_sync_to_async(Configuration.objects.all)()
                    #     for config in configs:
                    #         try:
                    #             cfg = json.loads(config.config)
                    #             if "ENVDAQ" in cfg:
                    #                 config_list.append(config.config)
                    #         except TypeError:
                    #             pass
                    # except Configuration.DoesNotExist:
                    #     pass

                body = {
                    "purpose": "UPDATE",
                    # "current_config": current_config,
                    # "config_list": config_list,
                    "current_server": f"{current_daq_server}",
                    "current_config": current_config,
                    "server_map": server_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="DAQServerConsumer",
                    subject="DAQServerConfig",
                    body=body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.daqserver_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

            elif body["purpose"] == "PUSH":

                try:
                    new_config = body["config"]
                except JSONDecodeError:
                    new_config = dict()

                print(f"***DAQServerConfig:PUSH: {new_config}")
                push_body = {
                    "purpose": "PUSH",
                    # "current_config": current_config,
                    # "config_list": config_list,
                    "config": new_config,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="DAQServerConsumer",
                    subject="CONFIG",
                    body=push_body,
                )

                await self.channel_layer.group_send(
                    self.daqserver_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

        elif message["SUBJECT"] == "CONFIG":
            body = message["BODY"]
            if body["purpose"] == "REQUEST":
                if body["type"] == "ENVDAQ_CONFIG":
                    if "server_name" in body:
                        daq_name = body["server_name"]
                    cfg = await ConfigurationUtility().get_config(name=daq_name)

                    reply = {
                        "TYPE": "UI",
                        "SENDER_ID": "DAQServerConsumer",
                        "TIMESTAMP": dt_to_string(),
                        "SUBJECT": "CONFIG",
                        "BODY": {
                            "purpose": "REPLY",
                            "type": "ENVDAQ_CONFIG",
                            "config": cfg,
                        },
                    }
                # print(f'reply: {reply}')
                await self.daq_message({"message": reply})
            elif body["purpose"] == "SYNC":
                if body["type"] == "SYSTEM_DEFINITION":
                    # TODO: add field to force sync option
                    # send config data to syncmanager
                    await SyncManager.sync_data(body["data"])
        elif message["SUBJECT"] == "READY_STATE":
            # print('$$$$$$$ READY_STATE')
            if message["BODY"]["status"] == "READY":
                # print(f'___ READY TO GO ___: {message}')
                print("READY TO RUN:")
                print(f"    daq_server: {self.daqserver_namespace}")
                print(f"    UI Server: {self.hostname}:{self.port}")
                ws_origin = f"{self.hostname}:{self.port}"

                # TODO: add docker host to ws_origin
                PlotManager.get_server().start(add_ws_origin=ws_origin)

        # message = text_data_json['BODY']

        # await self.channel_layer.group_send(
        #     self.data_group_name,
        #     {
        #         'type': 'data_message',
        #         'message': message
        #     }
        # )

    # Receive message from room group
    async def daq_message(self, event):
        message = event["message"]
        # print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    @database_sync_to_async
    def get_daq_server(self, host="localhost", name="default", force_create=True):

        try:
            daq_server = DAQServer.objects.get(name=name, host=host)
            print(f"name,host: daq_server_exists: {daq_server}")
        # try:
        #     daq_server = DAQServer.objects.get(name=name, host=host)
        #     print(f"daq_server_exists: {daq_server}")
        except DAQServer.DoesNotExist:
            daq_server = None
            if force_create:
                daq_server = DAQServer(name=name, host=host)
                daq_server.save()
                print(f"daq_server_new: {daq_server}")

        return daq_server

    @database_sync_to_async
    def get_config_list(self):
        config_list = []
        try:
            configs = Configuration.objects.all()
            print(configs)
            for config in configs:
                try:
                    cfg = json.loads(config.config)
                    if "ENVDAQ_CONFIG" in cfg:
                        config_list.append(cfg["NAME"])
                except (TypeError, JSONDecodeError):
                    pass
        except Configuration.DoesNotExist:
            pass
        return config_list

    @database_sync_to_async
    def get_daqserver_map(self):
        server_map = dict()
        try:
            servers = DAQServer.objects.all()
            print(servers)
            for server in servers:
                server_map[f"{server}"] = server.get_config()
        except Configuration.DoesNotExist:
            pass
        return server_map

    @database_sync_to_async
    def get_daq_registry(self):
        try:
            regs = DAQRegistration.objects.all()
            print(f"regs: {regs}")

        except DAQRegistration.DoesNotexist:
            # TODO: return 404 ... lookup how
            pass
            regs = []

        daq_registration_map = {}
        if regs:
            for reg in regs:
                # reg_key = json.dumps(reg.)
                daq_registration_map[reg.namespace] = reg.get_registration()

        return daq_registration_map


# class InitConsumer(SyncConsumer):
#     def test():
#         print('test')
#     # def __init__(self):
#     #     print('init')


#     # async def connect(self):
#     #     print(f'scope: {self.scope}')
#     #     # try:
#     #     #     self.daqserver_namespace = self.scope["url_route"]["kwargs"][
#     #     #         "daq_namespace"
#     #     #     ]
#     #     #     self.daqserver_group_name = f"daqserver_{self.scope['url_route']['kwargs']['daq_namespace']}_messages"
#     #     # except KeyError:
#     #     #     self.daqserver_namespace = "default"
#     #     #     self.daqserver_group_name = "daq_default_messages"


class DAQConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        print(f"scope: {self.scope}")
        # try:
        #     self.daqserver_namespace = self.scope["url_route"]["kwargs"][
        #         "daq_namespace"
        #     ]
        #     self.daqserver_group_name = f"daqserver_{self.scope['url_route']['kwargs']['daq_namespace']}_messages"
        # except KeyError:
        #     self.daqserver_namespace = "default"
        #     self.daqserver_group_name = "daq_default_messages"

        self.daq_group_name = ""
        self.manage_group_name = "envdaq-manage"
        self.registry_group_name = "envnet-manage"

        # self.server_name = (
        #     self.scope['url_route']['kwargs']['server_name']
        # )
        self.hostname = self.scope["server"][0]
        self.port = self.scope["server"][1]
        self.daq_group_name = f"daq-{self.hostname}-{self.port}"
        # print(f'hostname:port : {self.hostname}:{self.port}')
        # self.daqserver_group_name = 'daq_messages'

        # Join room group
        await self.channel_layer.group_add(self.daq_group_name, self.channel_name)
        await self.channel_layer.group_add(self.manage_group_name, self.channel_name)
        # await self.channel_layer.group_add(self.registry_group_name, self.channel_name)

        await self.accept()

        # get current daq
        # TODO: add ability to key this with name, tags, project, etc
        # daq = envdaq.util.daq.get_daq()
        # cfg = ConfigurationUtility().get_config()
        # print(f'consumer:cfg = {cfg}')

        # await self.data_message({'message': 'hi'})
        # await self.channel_layer.group_send(
        #     self.data_win_group_name,
        #     {
        #         'type': 'message',
        #         'message': 'hi again'
        #     }
        # )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.daq_group_name, self.channel_name)
        # await self.channel_layer.group_discard(
        #     self.manage_group_name, self.channel_name
        # )
        # await self.channel_layer.group_discard(
        #     self.registry_group_name, self.channel_name
        # )

    # Receive message from WebSocket
    async def receive(self, text_data):
        print(json.loads(text_data))
        # # text_data_json = json.loads(text_data)

        # try:
        #     data = json.loads(text_data)
        # except json.JSONDecodeError as e:
        #     print(f"DAQServerConsumer error {e}")
        #     return

        # message = data["message"]
        # # print(f'999999 message: {message}')

        # new_message = "hi"
        # await self.daq_message({"message": "hi"})

        # # print(text_data)
        # # text_data_json = json.loads(text_data)

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"DAQConsumer error {e}")
            return

        message = data["message"]
        # print(f'999999 message: {message}')

        if message["SUBJECT"] == "DAQServerRegistry":
            body = message["BODY"]

            if body["purpose"] == "UPDATE_CLIENT":
                print(f"update_client")
                daqserver_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.DAQSERVER
                )
                controller_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.CONTROLLER
                )
                instrument_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.INSTRUMENT
                )
                # controller_registration_map = await DAQRegistry.get_registry(type="Controller")
                # instrument_registration_map = await DAQRegistry.get_registry(type="Instrument")
                print(f"<<< daqserver_registration_map: {daqserver_registration_map}\n")
                print(
                    f"<<< controller_registration_map: {controller_registration_map}\n\n"
                )
                # print(f"<<< instrument_registration_map: {instrument_registration_map}\n\n")
                msg_body = {
                    "purpose": "REGISTRY",
                    "daqserver_registry": daqserver_registration_map,
                    "controller_registry": controller_registration_map,
                    "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="DAQConsumer",
                    subject="DAQServerRegistry",
                    body=msg_body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.daq_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

            elif body["purpose"] == "REQUEST":
                print(f"request")
                # print('add')
                # print(f'add: {self.scope}')
                # print(f"body: {body}")
                # daq_namespace = body["namespace"]["daq_server"]

                # try:
                #     regs = await database_sync_to_async(DAQRegistration.objects.all())
                #     print(f"regs: {regs}")

                # except DAQRegistration.DoesNotexist:
                #     # TODO: return 404 ... lookup how
                #     pass
                #     regs = []

                # daq_registration_map = {}
                # if regs:
                #     for reg in regs:
                #         daq_registration_map[reg.namespace] = reg.get_registration()

                # daq_registration_map = await self.get_daq_registry()
                daqserver_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.DAQSERVER
                )
                controller_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.CONTROLLER
                )
                instrument_registration_map = await DAQRegistry.get_registry(
                    type=Namespace.INSTRUMENT
                )
                # controller_registration_map = await DAQRegistry.get_registry(type="Controller")
                # instrument_registration_map = await DAQRegistry.get_registry(type="Instrument")
                print(f"<<< daqserver_registration_map: {daqserver_registration_map}")
                print(
                    f"<<< controller_registration_map: {controller_registration_map}\n\n"
                )
                # print(f"<<< instrument_registration_map: {instrument_registration_map}\n\n")
                body = {
                    "purpose": "REGISTRY",
                    "daqserver_registry": daqserver_registration_map,
                    "controller_registry": controller_registration_map,
                    "instrument_registry": instrument_registration_map,
                }
                message = Message(
                    msgtype="UI",
                    sender_id="DAQConsumer",
                    subject="DAQServerRegistry",
                    body=body,
                )
                print(f"message_to_dict: {message.to_dict()}")
                # await self.daq_message(message.to_dict())
                await self.channel_layer.group_send(
                    self.daq_group_name,
                    {"type": "daq_message", "message": message.to_dict()["message"]},
                )

    @database_sync_to_async
    def get_daq_registry(self):
        try:
            regs = DAQRegistration.objects.all()
            print(f"regs: {regs}")

        except DAQRegistration.DoesNotexist:
            # TODO: return 404 ... lookup how
            pass
            regs = []

        daq_registration_map = {}
        if regs:
            for reg in regs:
                # reg_key = json.dumps(reg.)
                daq_registration_map[reg.namespace] = reg.get_registration()

        return daq_registration_map

    async def daq_message(self, event):
        message = event["message"]
        print(f"data_message: {json.dumps(message)}")
        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


class ManagementConsumer(AsyncConsumer):
    async def manage(self, message):
        print("start")
        print(message)
        try:
            command = message["command"]
            from setup.ui_server_conf import run_config

            if command == "INIT_ENVDAQ":
                print("Start envdaq servers")
                # try:
                #     network = run_config["HOST"]["network"]
                # except KeyError:
                #     network = None

                # from envnet.registry.registry import ServiceRegistry
                await DAQRegistry.start()
            elif command == "REGISTER_SERVICE":
                try:
                    config = {
                        "host": run_config["HOST"]["name"],
                        "port": run_config["HOST"]["port"],
                        "service_list": {"envdsys_daq": {}},
                    }
                    await ServiceRegistry.register(config=config)
                except KeyError:
                    pass
        except KeyError:
            pass

    async def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.data_group_name = "DAQManagementConsumer"
        self.data_win_group_name = "daqmanage"
        print(f"scope={self.scope}")
        # Join room group
        # await self.channel_layer.group_add(self.data_group_name, self.channel_name)

        await self.accept()

    async def receive(self, text_data):
        # print(text_data)
        # text_data_json = json.loads(text_data)

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"DAQServerConsumer error {e}")
            return

        message = data["message"]
