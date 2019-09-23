# envdaq/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import channels.db
import json
import asyncio
from envdaq.util.daq import ConfigurationUtility
import envdaq.util.util as time_util
from envdaq.util.sync_manager import SyncManager
from plots.plots import PlotManager


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
        text_data_json = json.loads(text_data)
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
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if (message['SUBJECT'] == 'DATA'):
            # print(f'controller data message')
            await self.channel_layer.group_send(
                self.controller_group_name,
                {
                    'type': 'controller_message',
                    'message': message
                }
            )

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
                print(f'message: {message}')
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
        print(f'data_message: {json.dumps(message)}')
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
        # print(f'name = {self.instrument_name}')
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
        data = json.loads(text_data)
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
            print(f'123123123 data: {message}')
            src_id = message['SENDER_ID']
            await PlotManager.update_data_by_source(src_id, data)

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
                print(f'consumer: {message}')
                await self.channel_layer.group_send(
                    self.instrument_group_name,
                    {
                        'type': 'instrument_message',
                        'message': msg
                    }
                )

            else:
                print(f'message: {message}')
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
        text_data_json = json.loads(text_data)
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
                print(f'message: {message}')
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
        print(f'interface_message: {json.dumps(message)}')
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

        text_data_json = json.loads(text_data)
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
                print(f'message: {message}')
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
        print(f'ifdevice_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class DAQServerConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.daqserver_group_name = 'daq_messages'

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
        data = json.loads(text_data)
        message = data['message']
        print(f'999999 message: {message}')

        if (message['SUBJECT'] == 'CONFIG'):
            body = message['BODY']
            if (body['purpose'] == 'REQUEST'):
                if (body['type'] == 'ENVDAQ_CONFIG'):
                    cfg = await ConfigurationUtility().get_config()

                    reply = {
                        'TYPE': 'GUI',
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
            print('$$$$$$$ READY_STATE')
            if message['BODY']['status'] == 'READY':
                print(f'___ READY TO GO ___: {message}')
                PlotManager.get_server().start()

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
        # print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
