#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 14:01:37 2018

@author: derek
"""
import asyncio
from datetime import datetime
from data.data import Data
import json
import os
from utilities.timer import Timer


class DataFile():

    def __init__(self, config):

        self.base_path = config['base_path']
        self.inst_class = config['instrument_class']
        self.inst_name = config['instrument_name']
        self.write_freq = config['write_freq']

        self.data = Data()

        self.task_list = []
        self.loop = asyncio.get_event_loop()

        interval = config['write_freq']
        self.save_timer = Timer(interval)
        self.save_timer.start()
        # self.start_timers()

        self.file = None

        task = asyncio.ensure_future(self.check_timer())
        self.task_list.append(task)

    def write(self):
        # check to see if there is data to save
        # determine proper file to save to
        if (self.data.size() > 0):

            buffer = self.data.get()
            path = self.base_path+'/'+self.inst_class+'/'+self.inst_name+'/'

            curr_ymd = ''

            for row in buffer:
                ymd = row['DateTime'].split('T')[0]

                if curr_ymd != ymd:
                    if self.file is not None:
                        #                    if self.file is not None or self.file.closed:
                        self.file.close()
                    if not os.path.exists(path):
                        os.makedirs(path, exist_ok=True)
#
                    fname = path+ymd+'.json'
                    # print(fname)
                    self.file = open(fname, 'a+')
                    curr_ymd = ymd
                # print(row)
                self.file.write(json.dumps(row)+'\n')
#                json.dump(row,self.file)
#
            self.file.close()

    def append(self, entry):
        self.data.append(entry)
        # print(self.data)

    def close(self):
        print('close')
        tasks = asyncio.Task.all_tasks()
        for t in self.task_list:
            t.cancel()
            tasks.remove(t)

        self.write()  # flush reamining data

    async def check_timer(self):
        #print('check timer')
        # self.save_timer.start()

        while True:
            # print(self.save_timer.elapsed_time)
            if self.save_timer.timer_done:
                #print('timer done')
                self.write()
                self.save_timer.resatart()

            await asyncio.sleep(1)


async def add_data(df):

    while True:

        entry = {
            'DateTime': datetime.utcnow().isoformat(timespec='seconds'),
            'Data': {'T': 25.0, 'RH': 60.0},
        }
        df.append(entry)
        # print(df)

        await asyncio.sleep(1)


def shutdown():
    df.close()
    tasks = asyncio.Task.all_tasks()
    for t in tasks:
        t.cancel()
    print("Tasks canceled")
    asyncio.get_event_loop().stop()


if __name__ == "__main__":

    event_loop = asyncio.get_event_loop()

    config = {
        'base_path': '/home/horton/derek/tmp',
        'instrument_class': 'env_sensor',
        'instrument_name': 'THSMPS',
        'write_freq': 2,
    }

    df = DataFile(config)

    task = asyncio.ensure_future(add_data(df))
    task_list = asyncio.Task.all_tasks()
#
    try:
        event_loop.run_until_complete(asyncio.wait(task_list))
        # event_loop.run_forever()
    except KeyboardInterrupt:
        print('closing client')
        # client.close()
        # event_loop.run_until_complete(client.wait_closed())

        shutdown()
#        for task in task_list:
#            print("cancel task")
#            task.cancel()
        # server.close()
        event_loop.run_forever()
        # event_loop.run_until_complete(asyncio.wait(asyncio.ensure_future(shutdown)))

    finally:

        print('closing event loop')
        event_loop.close()
