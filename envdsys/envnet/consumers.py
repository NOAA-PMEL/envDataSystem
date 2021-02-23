import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncConsumer
# import channels.db
import json
# import asyncio
# import os

from envnet.registry.registry import ServiceRegistry 
from envdaq.util.daq import ConfigurationUtility

# import envdaq.util.util as time_util
# from shared.utilities.util import dt_to_string
# from shared.data.message import Message
# from envdaq.util.sync_manager import SyncManager
# from plots.plots import PlotManager
# from envdaq.util.registration import RegistrationManager
# from django.conf import settings
# from datamanager.datamanager import DataManager

class ServiceRegistryConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        print(f'scope: {self.scope}')
        # try:
        #     self.daqserver_namespace = self.scope["url_route"]["kwargs"][
        #         "daq_namespace"
        #     ]
        #     self.daqserver_group_name = f"daqserver_{self.scope['url_route']['kwargs']['daq_namespace']}_messages"
        # except KeyError:
        #     self.daqserver_namespace = "default"
        #     self.daqserver_group_name = "daq_default_messages"

        # self.server_name = (
        #     self.scope['url_route']['kwargs']['server_name']
        # )
        self.hostname = self.scope["server"][0]
        self.port = self.scope["server"][1]
        # print(f'hostname:port : {self.hostname}:{self.port}')
        # self.daqserver_group_name = 'daq_messages'
        self.manage_group_name = "envdnet-manage"
        self.reg_win_group_name = "service_registry"

        # Join room groups
        await self.channel_layer.group_add(self.manage_group_name, self.channel_name)
        await self.channel_layer.group_add(self.reg_win_group_name, self.channel_name)

        await self.accept()

        # get current daq
        # TODO: add ability to key this with name, tags, project, etc
        # daq = envdaq.util.daq.get_daq()
        # cfg = ConfigurationUtility().get_config()
        # print(f'consumer:cfg = {cfg}')

        # await self.data_message({'message': 'hi'})
        await self.channel_layer.group_send(
            "envnet-manage",
            {
                'type': 'test',
                'message': 'hi again'
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.manage_group_name, self.channel_name
        )
        await self.channel_layer.group_discard(
            self.reg_win_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        print(text_data)
        # text_data_json = json.loads(text_data)

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f"ServiceRegistryConsumer error {e}")
            return

        # message = data["message"]
        # # print(f'999999 message: {message}')

        # if message["SUBJECT"] == "PING":
        #     # RegistrationManager.ping(message['BODY']['namespace']['daq_server'])
        #     RegistrationManager.ping(self.daqserver_namespace)

        # elif message["SUBJECT"] == "REGISTRATION":
        #     body = message["BODY"]
        #     if body["purpose"] == "ADD":
        #         # print('add')
        #         # print(f'add: {self.scope}')
        #         daq_namespace = body["namespace"]["daq_server"]
        #         # print(f'namespace: {self.daqserver_namespace}, {daq_namespace}')
        #         # registration = RegistrationManager.get(body['id'])
        #         # registration = RegistrationManager.get(daq_namespace, type="DAQServer")
        #         ui_reconfig_request = False
        #         registration = RegistrationManager.get(
        #             self.daqserver_namespace, type="DAQServer"
        #         )
        #         if registration:  # reg exists - UI running, unknown daq state
        #             # if daq_server has key, check against current registration
        #             if body["regkey"]:  # daq running (likely a reconnect)
        #                 # same: daq_server config takes precedence
        #                 if body["regkey"] == registration["regkey"]:
        #                     registration["config"] = body["config"]
        #                     # RegistrationManager.update(body['id'], registration)
        #                     # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
        #                     RegistrationManager.update(
        #                         self.daqserver_namespace, registration, type="DAQServer"
        #                     )

        #         else:  # no reg, no connection to daq since UI start
        #             if body["regkey"]:  # daq has been running
        #                 ui_reconfig_request = True
        #                 registration = {
        #                     "regkey": body["regkey"],
        #                     "config": body["config"],
        #                 }
        #                 # RegistrationManager.update(body['id'], registration)
        #                 # RegistrationManager.update(daq_namespace, registration, type="DAQServer")
        #                 RegistrationManager.update(
        #                     self.daqserver_namespace, registration, type="DAQServer"
        #                 )
        #             else:  # daq has started
        #                 registration = RegistrationManager.add(
        #                     # body['id'],
        #                     self.daqserver_namespace,
        #                     config=body["config"],
        #                     type="DAQServer",
        #                 )

        #         # print("before reply")
        #         reply = {
        #             "TYPE": "UI",
        #             "SENDER_ID": "DAQServerConsumer",
        #             "TIMESTAMP": dt_to_string(),
        #             "SUBJECT": "REGISTRATION",
        #             "BODY": {
        #                 "purpose": "SUCCESS",
        #                 "regkey": registration["regkey"],
        #                 "config": registration["config"],
        #                 "ui_reconfig_request": ui_reconfig_request,
        #             },
        #         }
        #         # print(f"reply: {reply}")
        #         # print(json.dumps(reply))
        #         await self.data_message({"message": reply})

        #         # body={
        #         #     "purpose": "ADD",
        #         #     "key": self.registration_key,
        #         #     "id": self.daq_id,
        #         #     "config": self.config,
        #         # },

        #     if body["purpose"] == "REMOVE":
        #         print("remove")
        #         # RegistrationManager.remove(body['id'])
        #         RegistrationManager.remove(self.daqserver_namespace, type="DAQServer")

        # elif message["SUBJECT"] == "CONFIG":
        #     body = message["BODY"]
        #     if body["purpose"] == "REQUEST":
        #         if body["type"] == "ENVDAQ_CONFIG":
        #             if "server_name" in body:
        #                 server_name = body["server_name"]
        #             cfg = await ConfigurationUtility().get_config(name=server_name)

        #             reply = {
        #                 "TYPE": "UI",
        #                 "SENDER_ID": "DAQServerConsumer",
        #                 "TIMESTAMP": dt_to_string(),
        #                 "SUBJECT": "CONFIG",
        #                 "BODY": {
        #                     "purpose": "REPLY",
        #                     "type": "ENVDAQ_CONFIG",
        #                     "config": cfg,
        #                 },
        #             }
        #         # print(f'reply: {reply}')
        #         await self.data_message({"message": reply})
        #     elif body["purpose"] == "SYNC":
        #         if body["type"] == "SYSTEM_DEFINITION":
        #             # TODO: add field to force sync option
        #             # send config data to syncmanager
        #             await SyncManager.sync_data(body["data"])
        # elif message["SUBJECT"] == "READY_STATE":
        #     # print('$$$$$$$ READY_STATE')
        #     if message["BODY"]["status"] == "READY":
        #         # print(f'___ READY TO GO ___: {message}')
        #         print("READY TO RUN:")
        #         print(f"    daq_server: {self.daqserver_namespace}")
        #         print(f"    UI Server: {self.hostname}:{self.port}")
        #         ws_origin = f"{self.hostname}:{self.port}"
                
        #         # TODO: add docker host to ws_origin
        #         PlotManager.get_server().start(add_ws_origin=ws_origin)

        # message = text_data_json['BODY']

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

class ManagementConsumer(AsyncConsumer):

    async def manage(self, message):
        print('start')
        print(message)
        try:
            command = message["command"]
            from setup.ui_server_conf import run_config
            if command == "INIT_ENVNET":
                try:
                    network = run_config["HOST"]["network"]
                except KeyError:
                    network = "default"

                await ServiceRegistry.start(network=network)
            elif command == "REGISTER_SERVICE":
                try:
                    config = {
                        "host": run_config["HOST"]["name"],
                        "port":  run_config["HOST"]["port"],
                        "service_list": {"envdsys_net": {}}
                    }
                    reg = await ServiceRegistry.register(config=config)
                    print(reg)
                except KeyError:
                    pass
        except KeyError:
            pass
