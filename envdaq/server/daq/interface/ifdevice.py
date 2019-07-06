from daq.daq import DAQ
import abc
import random
from utilities import util
import asyncio
from data.message import Message
# import abc


class IFDevice(DAQ):

    # channel_map = {'default': 'default'}
    class_type = 'IFDEVICE'

    def __init__(self, config):
        super().__init__(config)

        self.config = config
        self.task_list = []

        self.msg_buffer = None

    # @abc.abstractmethod
    def get_id(self):
        id = super().get_id()
        return id

    # @property
    # def msg_buffer(self):
    #     return self.msg_buffer
    #
    # @msg_buffer.setter
    # def msg_buffer(self, buf):
    #     self.msg_buffer = buf

    def connect(self, msg=None):
        pass

    def start(self, msg=None):
        pass

    def stop(self, msg=None):
        pass

    def disconnect(self, msg=None):
        pass

    @abc.abstractmethod
    def handle(self, data):
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
            self.handle(data)
            await asyncio.sleep(util.time_to_next(1))

    def handle(self, data):

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
        self.msg_buffer.put_nowait(msg)
