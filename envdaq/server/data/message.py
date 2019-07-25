import asyncio
# from datetime import datetime
import json
import utilities.util


class Message():

    def __init__(self, msgtype=None, sender_id=None, subject=None,
                 body=None, extra=None):
        self.prefix = 'message'
        # self.signature = 'daq.data.message.Message'
        self.type = msgtype
        # self.id = None # why was this missing? do we want it?
        self.timestamp = utilities.util.dt_to_string()
        self.sender_id = sender_id
        self.subject = subject
        self.body = body
        self.extra = extra

        # print('Message.init()')

    def update(self, msgtype=None, sender_id=None, subject=None,
               body=None, extra=None):
        if msgtype is not None:
            self.type = msgtype
        if sender_id is not None:
            self.sender_id = sender_id
        if subject is not None:
            self.subject = subject
        if body is not None:
            self.body = body
        if extra is not None:
            self.extra = extra

        self.timestamp = utilities.util.dt_to_string()

    def to_json(self):
        # print(self.body)
        return json.dumps(self.to_dict())

    def to_dict(self):
        d = dict()
        # d['SIGNATURE'] = self.signature
        d['TYPE'] = self.type
        d['TIMESTAMP'] = self.timestamp
        d['SENDER_ID'] = self.sender_id
        d['SUBJECT'] = self.subject
        d['BODY'] = self.body
        d['EXTRA'] = self.extra

        # added prefix to label the message for websockets
        return {self.prefix: d}

    def from_json(self, json_msg):
        # print(f'json_msg: {json_msg}')
        pkg = json.loads(json_msg)
        # print(pkg['message'])
        if self.prefix in pkg:
            msg = pkg[self.prefix]
            # print(f'from_json: {msg}')
            # if 'SIGNATURE' in msg:
            #     self.signature = msg['SIGNATURE']
            if 'TYPE' in msg:
                self.type = msg['TYPE']
            if 'TIMESTAMP' in msg:
                self.timestamp = msg['TIMESTAMP']
            if 'SENDER_ID' in msg:
                self.sender_id = msg['SENDER_ID']
            if 'SUBJECT' in msg:
                self.subject = msg['SUBJECT']
            if 'BODY' in msg:
                self.body = msg['BODY']
                # print(f'****from_json:body = {self.body}')
            if 'EXTRA' in msg:
                self.extra = msg['EXTRA']

            # print('****done with from_json')
            # print(self.to_json())
        # print(f'from_json: {self.to_json()}')

# this may inherit JSONEncode at some point


class MessageBuffer():

    def __init__(self, config=None):
        self.config = config
        self.queue = asyncio.Queue(loop=asyncio.get_event_loop())

    def get_queue(self):
        return self.queue
