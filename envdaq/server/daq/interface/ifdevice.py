from daq.daq import DAQ
import abc
import random
from utilities import util
import asyncio
from data.message import Message
# import abc


class IFDevice(DAQ):
# class IFDevice():

    # channel_map = {'default': 'default'}
    class_type = 'IFDEVICE'

    def __init__(self, config):
        super().__init__(config)

        self.config = config
        self.task_list = []

        # Message buffers
        #   to/from parent
        self.msg_send_buffer = None
        self.msg_rcv_buffer = None

    # @abc.abstractmethod
    def get_id(self):
        id = super().get_id()
        # id = 'tmp'
        return id

    def connect(self, msg=None):
        pass

    def start(self, msg=None):
        pass

    def stop(self, msg=None):
        pass

    def disconnect(self, msg=None):
        pass

    def handle(self, data, type=None):
        pass

    def handle2(self, data):
        pass

    # def get_channel_map():
    #    return IFDevice.channel_map


class DummyIFDevice(IFDevice):

    # IFDevice.channel_map['test'] = 'test'

    def __init__(self, config):
        super().__init__(config)

        # start dummy data loop
        task = asyncio.ensure_future(self.data_loop())
        self.task_list.append(task)

    # def get_id(self):
    #     return ('DummyIFDevice')

    async def data_loop(self):

        while True:

            data = '{},{},{},{}'.format(
                round(random.random()*2.0, 4),
                round(random.random()*10.0, 4),
                round(random.random()*5.0, 4),
                round(random.random()*20.0, 4)
            )
            # print('ifdevice: data = {}'.format(data))
            self.handle2(data)
            await asyncio.sleep(util.time_to_next(1))

    def handle2(self, data):

        out = {'DATA': data}
        # print(out)
        # msg = Message(subject='DATA', body=out)
        msg = Message(
            sender_id=self.get_id(),
            msgtype=IFDevice.class_type,
            subject='DATA',
            body=out
        )
        # print(msg.to_dict())
        # print(msg.to_json())
        self.msg_send_buffer.put_nowait(msg)
