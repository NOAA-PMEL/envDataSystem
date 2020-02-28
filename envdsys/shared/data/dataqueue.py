from datetime import datetime
from collections import OrderedDict
import asyncio
import json

class TestQueue():

    def __init__(self,queue):
        self.loop = asyncio.get_event_loop()
        self.my_queue = asyncio.Queue(loop=loop,maxsize=5)
        self.other_queue = queue
        self.q_list = [self.my_queue, self.other_queue]
        #self.q_list = [self.other_queue]
        asyncio.ensure_future(self.send_data())


    async def send_data(self):
        w = .1
        while True:
            x = datetime.utcnow()
            print('send_data {}'.format(x))
            await asyncio.sleep(w)
            for q in self.q_list:
                #print(q)
                q.put_nowait(x)
                #await q.put(x)
            w = w+.01
            print('w = {}'.format(w))
            if w > 2:
                w = 2

        #await queue.put(None)


async def produce(queue, n):
    for x in range(n):
        print('producing {}/{}'.format(x, n))
        await asyncio.sleep(1)
        item = str(x)
        await queue.put(item)

    await queue.put(None)

async def consume_my(qclass):
    while True:
        print("items in q = {}".format(qclass.my_queue.qsize()))
        item = await qclass.my_queue.get()
        #if (item is None):
        #    break

        print('consuming my_queue {}...'.format(item))
        await asyncio.sleep(1)

async def consume_other(queue):
    while True:
        print("items in q = {}".format(queue.qsize()))
        item = await queue.get()
        #if (item is None):
        #    break

        print('consuming other_queue {}...'.format(item))
        #await asyncio.sleep(1)


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)
    test = TestQueue(queue=queue)
    #prod = asyncio.ensure_future(produce(queue,10))
    cons_my = asyncio.ensure_future(consume_my(test))
    cons_other = asyncio.ensure_future(consume_other(queue))
    task_list = asyncio.Task.all_tasks()
    #print(task_list)
    loop.run_until_complete(asyncio.wait(task_list))
    loop.close()
