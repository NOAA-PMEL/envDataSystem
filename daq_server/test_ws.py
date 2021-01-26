import websockets
import asyncio
import json
import time
from client.client import WSClient
from shared.data.message import Message
from datetime import datetime


async def send_data(client):

    while True:
        body = 'fake message - {}'.format(datetime.utcnow().isoformat(timespec='seconds'))
        msg = {'message': body}
        message = Message(msgtype='Test', sender_id='me', subject='test', body=msg)
        # print('send_data: {}'.format(msg))
      
        print('send_data: {}'.format(message.to_json()))
        # await client.send(json.dumps(msg))
        await client.send_message(message)
        await asyncio.sleep(1)


async def read_data(client):

    while True:
        json_msg = await client.read()
        msg = json.loads(json_msg)
        print('read_loop: {}'.format(msg))


def shutdown(task_list):

    for t in task_list:
        t.cancel()

    asyncio.get_event_loop().stop()


async def heartbeat():

    while True:
        print('lub-dub')
        await asyncio.sleep(5)

if __name__ == '__main__':

    event_loop = asyncio.get_event_loop()

    # task = asyncio.ensure_future(heartbeat())

    ws_client = WSClient(uri='ws://localhost:8000/ws/data/lobby/')
    asyncio.ensure_future(read_data(ws_client))
    asyncio.ensure_future(send_data(ws_client))

    task_list = asyncio.Task.all_tasks()

    try:
        event_loop.run_until_complete(asyncio.wait(task_list))
        # event_loop.run_forever()
    except KeyboardInterrupt:
        print('closing client')
        ws_client.sync_close()
        # event_loop.run_until_complete(ws_client.close())
        shutdown(task_list)

        event_loop.run_forever()
    finally:

        print('closing event loop')
        event_loop.close()
