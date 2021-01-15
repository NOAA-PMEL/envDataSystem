# envdaq/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import channels.db
import json
import asyncio
from envdaq.util.daq import ConfigurationUtility
# import envdaq.util.util as time_util
import shared.utilities.util as time_util
from envdaq.util.sync_manager import SyncManager
from plots.plots import PlotManager
from envdaq.util.registration import RegistrationManager


class DataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.data_group_name = 'data_test'
        self.data_win_group_name = 'data_test_win'

        # Join room group
        await self.channel_layer.group_add(
            self.data_group_name,
            self.channel_name
        )

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
        await self.channel_layer.group_discard(
            self.data_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # print(text_data)
        # await self.data_message({'message': 'hi again'})
        try:
            text_data_json = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f'DataConsumer error {e}')
            return
        # message = text_data_json['BODY']
        message = text_data_json['message']
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
            self.data_group_name,
            {
                'type': 'data_message',
                'message': message
            }
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
        message = event['message']
        # print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class ControllerConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.controller_name = (
            self.scope['url_route']['kwargs']['controller_name']
        )
        self.controller_group_name = (
            'controller_{}'.format(self.controller_name)
        )
        print(f'name = {self.controller_name}')
        # Join room group
        await self.channel_layer.group_add(
            self.controller_group_name,
            self.channel_name
        )

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.controller_group_name,
            self.channel_name
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

        # print(text_data)
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f'ControllerConsumer error {e}')
            print(f'text_data: {text_data}')
            return

        message = data['message']

        if (message['SUBJECT'] == 'DATA'):
            # print(f'controller data message')
            await self.channel_layer.group_send(
                self.controller_group_name,
                {
                    'type': 'controller_message',
                    'message': message
                }
            )
            src_id = message['SENDER_ID']
            await PlotManager.update_data_by_source(src_id, data)

        elif (message['SUBJECT'] == 'CONFIG'):
            body = message['BODY']
            # if (body['purpose'] == 'REQUEST'):
            #     if (body['type'] == 'ENVDAQ_CONFIG'):
            #         # do we ever get here?
            #         cfg = await ConfigurationUtility().get_config()

            #         reply = {
            #             'TYPE': 'GUI',
            #             'SENDER_ID': 'DAQServerConsumer',
            #             'TIMESTAMP': time_util.dt_to_string(),
            #             'SUBJECT': 'CONFIG',
            #             'BODY': {
            #                 'purpose': 'REPLY',
            #                 'type': 'ENVDAQ_CONFIG',
            #                 'config': cfg,
            #             }
            #         }
            #     # print(f'reply: {reply}')
            #     await self.data_message({'message': reply})
            if (body['purpose'] == 'SYNC'):
                if (body['type'] == 'CONTROLLER_INSTANCE'):
                    # TODO: add field to force sync option
                    # send config data to syncmanager
                    await SyncManager.sync_controller_instance(body['data'])
                    PlotManager.add_apps(body['data'])
                    
        elif message['SUBJECT'] == 'RUNCONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'ControllerConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'RUNCONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {
                        'type': 'controller_message',
                        'message': msg
                    }
                )

        elif message['SUBJECT'] == 'CONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'ControllerConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'CONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {
                        'type': 'controller_message',
                        'message': msg
                    }
                )
        elif message['SUBJECT'] == 'STATUS':
            if message['BODY']['purpose'] == 'REQUEST':
                print(f'status request: {message}')
                body = message['BODY']
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'ControllerConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'STATUS',
                    'BODY': body
                }
                print(f'controller request: status {msg}')
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {
                        'type': 'controller_message',
                        'message': msg
                    }
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.controller_group_name,
                    {
                        'type': 'controller_message',
                        'message': message
                    }
                )

    # Receive message from room group
    async def controller_message(self, event):
        message = event['message']
        # print(f' --3434-- controller_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    # Receive message from room group
    async def requested_message(self, event):
        message = event['message']
        # print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class InstrumentConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.instrument_name = (
            self.scope['url_route']['kwargs']['instrument_name']
        )
        self.instrument_group_name = (
            'instrument_{}'.format(self.instrument_name)
        )
        print(f'name = {self.instrument_name}')
        # Join room group
        await self.channel_layer.group_add(
            self.instrument_group_name,
            self.channel_name
        )

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.instrument_group_name,
            self.channel_name
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
        #         'type': 'instrument_message',
        #         'message': message
        #     }
        # )

        # print(text_data)
        # text_data_json = json.loads(text_data)
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f'InstrumentConsumer error {e}')
            print(f'text_data: {text_data}')
            return

        message = data['message']
        # print(f'message: {message}')
        if (message['SUBJECT'] == 'DATA'):
            # print(f'data message')
            await self.channel_layer.group_send(
                self.instrument_group_name,
                {
                    'type': 'instrument_message',
                    'message': message
                }
            )
            # print(f'123123123 data: {message}')
            src_id = message['SENDER_ID']
            await PlotManager.update_data_by_source(src_id, data)

            # print(f'message ***111***: {message}')
            if (
                'BODY' in message and
                'DATA_REQUEST_LIST' in message['BODY']
            ):
                # TODO: make this a utility function
                for dr in message['BODY']['DATA_REQUEST_LIST']:
                    if dr['class'] == 'CONTROLLER':
                        group_name = f'controller_{dr["alias"]["name"]}'
                        await self.channel_layer.group_send(
                            group_name.replace(' ', ''),
                            {
                                'type': 'controller_message',
                                'message': message
                            }
                        )

            # if 'alias' in message['BODY']:
            #     alias_name = message['BODY']['alias']['name']
                # alias_name = message.BODY.alias.name
                # print(f'alias: {alias_name}')
                # await PlotManager.update_data_by_key(alias_name, data)

        elif (message['SUBJECT'] == 'CONFIG'):
            body = message['BODY']
            # if (body['purpose'] == 'REQUEST'):
            #     if (body['type'] == 'ENVDAQ_CONFIG'):
            #         # do we ever get here?
            #         cfg = await ConfigurationUtility().get_config()

            #         reply = {
            #             'TYPE': 'GUI',
            #             'SENDER_ID': 'DAQServerConsumer',
            #             'TIMESTAMP': time_util.dt_to_string(),
            #             'SUBJECT': 'CONFIG',
            #             'BODY': {
            #                 'purpose': 'REPLY',
            #                 'type': 'ENVDAQ_CONFIG',
            #                 'config': cfg,
            #             }
            #         }
            #     # print(f'reply: {reply}')
            #     await self.data_message({'message': reply})
            if (body['purpose'] == 'SYNC'):
                if (body['type'] == 'INSTRUMENT_INSTANCE'):
                    # TODO: add field to force sync option
                    # send config data to syncmanager
                    await SyncManager.sync_instrument_instance(body['data'])
                    PlotManager.add_apps(body['data'])
        elif message['SUBJECT'] == 'RUNCONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'InstrumentConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'RUNCONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {
                        'type': 'instrument_message',
                        'message': msg
                    }
                )

        elif message['SUBJECT'] == 'CONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'InstrumentConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'CONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {
                        'type': 'instrument_message',
                        'message': msg
                    }
                )

        elif message['SUBJECT'] == 'STATUS':
            if message['BODY']['purpose'] == 'REQUEST':
                body = message['BODY']
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'InstrumentConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'STATUS',
                    'BODY': body
                }
                # print(f'consumer: {message}')
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {
                        'type': 'instrument_message',
                        'message': msg
                    }
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {
                        'type': 'instrument_message',
                        'message': message
                    }
                )

                # await self.instrument_message(
                #     {'message': msg}
                # )
                # print(f'msg: {msg}')

    # Receive message from room group
    async def instrument_message(self, event):
        message = event['message']
        # print(f'instrument_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class InterfaceConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.interface_name = (
            self.scope['url_route']['kwargs']['interface_name']
        )
        self.interface_group_name = (
            'interface_{}'.format(self.interface_name)
        )
        print(f'name = {self.interface_name}')
        # Join room group
        await self.channel_layer.group_add(
            self.interface_group_name,
            self.channel_name
        )

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.interface_group_name,
            self.channel_name
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
            print(f'InterfaceConsumer error {e}')
            return

        message = text_data_json['message']

        # Send message to room group
        # await self.channel_layer.group_send(
        #     self.interface_group_name,
        #     {
        #         'type': 'interface_message',
        #         'message': message
        #     }
        # )

        if (message['SUBJECT'] == 'DATA'):
            # print(f'controller data message')
            await self.channel_layer.group_send(
                self.interface_group_name,
                {
                    'type': 'interface_message',
                    'message': message
                }
            )

        elif (message['SUBJECT'] == 'CONFIG'):
            body = message['BODY']
            if (body['purpose'] == 'REQUEST'):
                pass
                # if (body['type'] == 'ENVDAQ_CONFIG'):
                #     # do we ever get here?
                #     cfg = await ConfigurationUtility().get_config()

                #     reply = {
                #         'TYPE': 'GUI',
                #         'SENDER_ID': 'InterfaceConsumer',
                #         'TIMESTAMP': time_util.dt_to_string(),
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
        
        elif message['SUBJECT'] == 'RUNCONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'InterfaceConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'RUNCONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {
                        'type': 'interface_message',
                        'message': msg
                    }
                )

        elif message['SUBJECT'] == 'CONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'InterfaceConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'CONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {
                        'type': 'interface_message',
                        'message': msg
                    }
                )
        elif message['SUBJECT'] == 'STATUS':
            if message['BODY']['purpose'] == 'REQUEST':
                print(f'status request: {message}')
                body = message['BODY']
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'InterfaceConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'STATUS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {
                        'type': 'interface_message',
                        'message': msg
                    }
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.interface_group_name,
                    {
                        'type': 'interface_message',
                        'message': message
                    }
                )

    # Receive message from room group
    async def interface_message(self, event):
        message = event['message']
        # print(f'interface_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class IFDeviceConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.ifdevice_name = (
            self.scope['url_route']['kwargs']['ifdevice_name']
        )
        self.ifdevice_group_name = (
            'ifdevice_{}'.format(self.ifdevice_name)
        )
        print(f'name = {self.ifdevice_name}')
        # Join room group
        await self.channel_layer.group_add(
            self.ifdevice_group_name,
            self.channel_name
        )

        await self.accept()

        # TODO: request config from controller?

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.ifdevice_group_name,
            self.channel_name
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
            print(f'IFDeviceConsumer error {e}')
            return

        message = text_data_json['message']

        # await self.channel_layer.group_send(
        #     self.ifdevice_group_name,
        #     {
        #         'type': 'ifdevice_message',
        #         'message': message
        #     }
        # )

        if (message['SUBJECT'] == 'DATA'):
            # print(f'controller data message')
            await self.channel_layer.group_send(
                self.ifdevice_group_name,
                {
                    'type': 'ifdevice_message',
                    'message': message
                }
            )

        elif (message['SUBJECT'] == 'CONFIG'):
            body = message['BODY']
            if (body['purpose'] == 'REQUEST'):
                pass
                # if (body['type'] == 'ENVDAQ_CONFIG'):
                #     # do we ever get here?
                #     cfg = await ConfigurationUtility().get_config()

                #     reply = {
                #         'TYPE': 'GUI',
                #         'SENDER_ID': 'InterfaceConsumer',
                #         'TIMESTAMP': time_util.dt_to_string(),
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
        
        elif message['SUBJECT'] == 'RUNCONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'IFDeviceConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'RUNCONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {
                        'type': 'ifdevice_message',
                        'message': msg
                    }
                )

        elif message['SUBJECT'] == 'CONTROLS':
            print(f'message: {message}')
            body = message['BODY']
            if body['purpose'] == 'REQUEST':
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'IFDeviceConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'CONTROLS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {
                        'type': 'ifdevice_message',
                        'message': msg
                    }
                )
        elif message['SUBJECT'] == 'STATUS':
            if message['BODY']['purpose'] == 'REQUEST':
                print(f'status request: {message}')
                body = message['BODY']
                msg = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'IFDeviceConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'STATUS',
                    'BODY': body
                }
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {
                        'type': 'ifdevice_message',
                        'message': msg
                    }
                )

            else:
                # print(f'message: {message}')
                await self.channel_layer.group_send(
                    self.ifdevice_group_name,
                    {
                        'type': 'ifdevice_message',
                        'message': message
                    }
                )

    # Receive message from room group
    async def ifdevice_message(self, event):
        message = event['message']
        # print(f'ifdevice_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class DAQServerConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        print(f'scope: {self.scope}')
        try:
            self.daqserver_name = (
                self.scope['url_route']['kwargs']['daq_id']
            )
            self.daqserver_group_name = (
                f"daqserver_{self.scope['url_route']['kwargs']['daq_id']}_messages"
            )
        except KeyError:
            self.daqserver_name = "default"
            self.daqserver_group_name = "daq_default_messages"

        # self.server_name = (
        #     self.scope['url_route']['kwargs']['server_name']
        # )
        self.hostname = self.scope['server'][0]
        self.port = self.scope['server'][1]
        # print(f'hostname:port : {self.hostname}:{self.port}')
        # self.daqserver_group_name = 'daq_messages'

        # Join room group
        await self.channel_layer.group_add(
            self.daqserver_group_name,
            self.channel_name
        )

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
            self.daqserver_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # print(text_data)
        # text_data_json = json.loads(text_data)

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            print(f'DAQServerConsumer error {e}')
            return
        
        message = data['message']
        # print(f'999999 message: {message}')

        if (message['SUBJECT'] == 'PING'):
            RegistrationManager.ping(message['BODY']['id'])
    
        elif (message['SUBJECT'] == 'REGISTRATION'):
            body = message['BODY']
            if (body['purpose'] == 'ADD'):
                # print('add')
                print(f'add: {self.scope}')
                registration = RegistrationManager.get(body['id'])
                if registration:  # reg exists - UI running, unknown daq state
                    # if daq_server has key, check against current registration
                    if body['regkey']:  # daq running (likely a reconnect)
                        # same: daq_server config takes precedence
                        if body['regkey'] == registration['regkey']:
                            registration['config'] = body['config']
                            RegistrationManager.update(body['id'], registration)
                    
                else:  # no reg, no connection to daq since UI start
                    if body['regkey']:  # daq has been running
                        registration = {
                            "regkey": body['regkey'],
                            "config": body['config'],
                        }
                        RegistrationManager.update(body['id'], registration)
                    else:  # daq has started
                        registration = RegistrationManager.add(
                            body['id'],
                            config=body['config']
                        )

                # print("before reply")
                reply = {
                    'TYPE': 'UI',
                    'SENDER_ID': 'DAQServerConsumer',
                    'TIMESTAMP': time_util.dt_to_string(),
                    'SUBJECT': 'REGISTRATION',
                    'BODY': {
                        'purpose': 'SUCCESS',
                        'regkey': registration['regkey'],
                        'config': registration['config'],
                    }
                }
                print(f"reply: {reply}")
                print(json.dumps(reply))
                await self.data_message({'message': reply})

                # body={
                #     "purpose": "ADD",
                #     "key": self.registration_key,
                #     "id": self.daq_id, 
                #     "config": self.config,
                # },

            if (body['purpose'] == 'REMOVE'):
                print('remove')
                RegistrationManager.remove(body['id'])

        elif (message['SUBJECT'] == 'CONFIG'):
            body = message['BODY']
            if (body['purpose'] == 'REQUEST'):
                if (body['type'] == 'ENVDAQ_CONFIG'):
                    if 'server_name' in body:
                        server_name = body['server_name']
                    cfg = await ConfigurationUtility().get_config(
                        name=server_name
                    )

                    reply = {
                        'TYPE': 'UI',
                        'SENDER_ID': 'DAQServerConsumer',
                        'TIMESTAMP': time_util.dt_to_string(),
                        'SUBJECT': 'CONFIG',
                        'BODY': {
                            'purpose': 'REPLY',
                            'type': 'ENVDAQ_CONFIG',
                            'config': cfg,
                        }
                    }
                # print(f'reply: {reply}')
                await self.data_message({'message': reply})
            elif (body['purpose'] == 'SYNC'):
                if (body['type'] == 'SYSTEM_DEFINITION'):
                    # TODO: add field to force sync option
                    # send config data to syncmanager
                    await SyncManager.sync_data(body['data'])
        elif message['SUBJECT'] == 'READY_STATE':
            # print('$$$$$$$ READY_STATE')
            if message['BODY']['status'] == 'READY':
                print(f'___ READY TO GO ___: {message}')
                print(f'hostname: {self.hostname}')
                ws_origin = f'{self.hostname}:{self.port}'

                # PlotManager.get_server().start(
                #     add_ws_origin=ws_origin
                # )

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
        message = event['message']
        print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
