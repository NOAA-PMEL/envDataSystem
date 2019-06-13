import abc
import asyncio


class DAQ(abc.ABC):

    def __init__(self, config):

        print('init DAQ')
        self.loop = asyncio.get_event_loop()
        self.config = config
        self.task_list = []

        self.name = None
        self.label = None

    def get_id(self):
        id = self.__class__.__name__
        if self.label is not None:
            id += ":"+self.label

        return id
