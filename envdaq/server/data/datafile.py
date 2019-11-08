#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import utilities.util
from data.message import Message

# from datetime import datetime
# from data.data import Data
import json
import os
# from utilities.timer import Timer


class DataFile():

    def __init__(
        self,
        base_path='./envdata/',
        save_interval=60,
        file_interval='day',
        config=None,
    ):

        self.base_path = base_path

        # unless specified, flush file every 60 sec
        self.save_interval = save_interval

        # allow for cases where we want hour files
        #   options: 'day', 'hour'
        self.file_interval = file_interval

        if config:
            self.setup(config)

        if self.base_path[-1] != '/':
            self.base_path += '/'

        self.save_now = True
        # if save_interval == 0:
        #     self.save_now = True

        self.current_file_name = ''

        self.data_buffer = asyncio.Queue()

        self.task_list = []
        self.loop = asyncio.get_event_loop()

        self.file = None

        self.format = {
            'SOURCE': 'envDataSystem',
            'VERSION': '1.0',
            'FORMAT': 'jsonl',
        }

    def setup(self, config):
        if 'base_path' in config:
            self.base_path = config['base_path']
        if 'save_interval' in config:
            self.save_interval = config['save_interval']
        if 'file_interval' in config:
            self.file_interval = config['file_interval']
       
    async def write_message(self, msg):
        # print(f'{msg.to_json()}')
        if msg.subject == 'DATA':
            await self.write(msg.body)
        # if 'body' in msg and 'DATA' in msg['body']:
        #     await self.write(msg['body']['DATA'])

    async def write(self, data):
        # add message to queue and return
        data['FILE_META'] = self.format
        # print(f'write: {data}')
        await self.data_buffer.put(data)
        # record =  dict()
        # record['FILE_META'] = self.format
        # record['RECORD'] = data

    async def __write(self):

        while True:

            data = await self.data_buffer.get()
            # print(f'datafile.__write: {data}')

            if data and ('DATA' in data):
                d_and_t = data['DATA']['DATETIME'].split('T')
                ymd = d_and_t[0]
                hour = d_and_t[1].split(':')[0]

                self.__open(ymd, hour=hour)

                if not self.file:
                    return

                json.dump(data, self.file)
                self.file.write('\n')

                if self.save_now:
                    self.file.flush()
                    if self.save_interval > 0:
                        self.save_now = False

    def __open(self, ymd, hour=None):

        fname = ymd
        if self.file_interval == 'hour':
            fname += '_' + hour
        fname += '.jsonl'

        if (
            self.file is not None and
            not self.file.closed and
            os.path.basename(self.file.name) == fname
        ):
            return

        # TODO: change to raise error so __write can catch it
        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path, exist_ok=True)
        except OSError as e:
            print(f'OSError: {e}')
            self.file = None
            return

        self.file = open(
            self.base_path+fname,
            mode='a',
        )

    def open(self):
        self.task_list.append(
            asyncio.ensure_future(self.save_file_loop())
        )
        self.task_list.append(
            asyncio.ensure_future(self.__write())
        )

    def close(self):

        for t in self.task_list:
            t.cancel()

        if self.file:
            try:
                self.file.flush()
                self.file.close()
                self.file = None
            except ValueError:
                print('file already closed')

    async def save_file_loop(self):

        while True:
            if self.save_interval > 0:
                await asyncio.sleep(
                    utilities.util.time_to_next(self.save_interval)
                )
                self.save_now = True
            else:
                self.save_now = True
                await asyncio.sleep(1)

# async def add_data(df):

#     while True:

#         entry = {
#             'DateTime': datetime.utcnow().isoformat(timespec='seconds'),
#             'Data': {'T': 25.0, 'RH': 60.0},
#         }
#         df.append(entry)
#         # print(df)

#         await asyncio.sleep(1)


# def shutdown():
#     df.close()
#     tasks = asyncio.Task.all_tasks()
#     for t in tasks:
#         t.cancel()
#     print("Tasks canceled")
#     asyncio.get_event_loop().stop()


# if __name__ == "__main__":

#     event_loop = asyncio.get_event_loop()

#     config = {
#         'base_path': '/home/horton/derek/tmp',
#         'instrument_class': 'env_sensor',
#         'instrument_name': 'THSMPS',
#         'write_freq': 2,
#     }

#     df = DataFile(config)

#     task = asyncio.ensure_future(add_data(df))
#     task_list = asyncio.Task.all_tasks()
# #
#     try:
#         event_loop.run_until_complete(asyncio.wait(task_list))
#         # event_loop.run_forever()
#     except KeyboardInterrupt:
#         print('closing client')
#         # client.close()
#         # event_loop.run_until_complete(client.wait_closed())

#         shutdown()
# #        for task in task_list:
# #            print("cancel task")
# #            task.cancel()
#         # server.close()
#         event_loop.run_forever()
#         # event_loop.run_until_complete(asyncio.wait(asyncio.ensure_future(shutdown)))

#     finally:

#         print('closing event loop')
#         event_loop.close()
