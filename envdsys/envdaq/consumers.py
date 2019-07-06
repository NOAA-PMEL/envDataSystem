# envdaq/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import asyncio


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

        await self.data_message({'message': 'hi'})
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
        message = text_data_json['BODY']
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
