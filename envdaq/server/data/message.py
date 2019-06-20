import asyncio
from datetime import datetime
import json
import utilities.util


class Message():

    def __init__(self, type=None, sender_id=None, subject=None,
                 body=None, extra=None):
        self.prefix = 'MSG'
        self.signature = 'daq.data.message.Message'
        self.type = type
        # self.id = None # why was this missing? do we want it?
        self.timestamp = utilities.util.dt_to_string()
        self.sender_id = sender_id
        self.subject = subject
        self.body = body
        self.extra = extra

    def to_json(self):
        print(self.body)
        return json.dumps(self.to_dict())

    def to_dict(self):
        d = dict()
        d['SIGNATURE'] = self.signature
        d['TYPE'] = self.type
        d['TIMESTAMP'] = self.timestamp
        d['SENDER_ID'] = self.sender_id
        d['SUBJECT'] = self.subject
        d['BODY'] = self.body
        d['EXTRA'] = self.extra
        return d

    def from_json(self, json_msg):
        msg = json.loads(json_msg)

        self.signature = msg['SIGNATURE']
        self.type = msg['TYPE']
        self.timestamp = msg['TIMESTAMP']
        self.sender_id = msg['SENDER_ID']
        self.subject = msg['SUBJECT']
        self.body = msg['BODY']
        self.extra = msg['EXTRA']

# this may inherit JSONEncode at some point


class MessageBuffer():

    def __init__(self, config=None):
        self.config = config
        self.queue = asyncio.Queue(loop=asyncio.get_event_loop())

    def get_queue(self):
        return self.queue
