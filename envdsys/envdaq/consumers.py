# envdaq/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import channels.db
import json
import asyncio
import envdaq.util.daq




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

        cfg = await channels.db.database_sync_to_async(envdaq.util.daq.get_config)()
        print(f'consumer:cfg = {cfg}')

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
        print(f'data_message: {json.dumps(message)}')
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


class DAQConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.daq_group_name = 'daq_messages'

        # Join room group
        await self.channel_layer.group_add(
            self.daq_group_name,
            self.channel_name
        )

        await self.accept()

        # get current daq
        # TODO: add ability to key this with name, tags, project, etc
        # daq = envdaq.util.daq.get_daq()
        cfg = envdaq.util.daq.get_config()
        print(f'consumer:cfg = {cfg}')


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
            self.daq_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # print(text_data)
        text_data_json = json.loads(text_data)
        message = text_data_json['BODY']

        await self.channel_layer.group_send(
            self.data_group_name,
            {
                'type': 'data_message',
                'message': message
            }
        )

    # Receive message from room group
    async def data_message(self, event):
        message = event['message']
        # print(f'data_message: {json.dumps(message)}')
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
