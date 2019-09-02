from client.serialport import SerialPortClient
import asyncio
import json
import time
from data.message import Message
from datetime import datetime


async def send_data(client):

    # while True:
    #     body = 'fake message - {}'.format(datetime.utcnow().isoformat(timespec='seconds'))
    #     msg = {'message': body}
    #     message = Message(msgtype='Test', sender_id='me', subject='test', body=msg)
    #     # print('send_data: {}'.format(msg))
      
    #     print('send_data: {}'.format(message.to_json()))
    #     # await client.send(json.dumps(msg))
    #     await client.send_message(message)
    #     await asyncio.sleep(1)
    while True:
        body = 'read'
        msg = {'message': body}
        message = Message(msgtype='Test', sender_id='me',
                          subject='cmd', body=msg)
        # print('send_data: {}'.format(msg))

        print('send_data: {}'.format(message.to_json()))
        # await client.send(json.dumps(msg))
        # await client.send('rtclck\n')
        await client.send('read\n')
        # await asyncio.sleep(.1)
        await client.send('raw=2\n')
        # await client.send_message(message)
        await asyncio.sleep(2)


async def read_data(client):

    # while True:
    #     # json_msg = await client.read()
    #     # msg = json.loads(json_msg)
    #     msg = await client.read()
    #     print(f'read_loop: {datetime.utcnow()} {msg.rstrip()}')
    #     parse(msg)
    while True:
        # json_msg = await client.read()
        # msg = json.loads(json_msg)
        msg = await client.read()
        eol = len(msg.rstrip())
        print(f'read_loop: {datetime.utcnow()} {msg.rstrip()} {eol}')
        # parse(msg)


def parse(msg):
    data = msg.rstrip()
    # print(f'data: {data}')
    # get checksum
    step = data.split('*')
    checksum = step[1]
    step = step[0].split('T')
    tilt = step[1]
    step = step[0].split('R')
    roll = step[1]
    step = step[0].split('P')
    pitch = step[1]
    step = step[0].split('C')
    course = step[1]
    print(f'{course}, {pitch}, {roll}, {tilt}, {checksum}\n')

# async def run(serialport):
#     # output = OutputStream()
#     await serialport.open()

#     while True:
#         msg = await serialport.read()
#         # msg = await readq.get()
#         # print(f'run: {datetime.utcnow()}, {msg}')
#         # await asyncio.sleep(.1)


def shutdown(serialport):

    task = asyncio.ensure_future(serialport.close())
    asyncio.get_event_loop().run_until_complete(task)
    # asyncio.get_event_loop().close()


if __name__ == "__main__":

    kw = {
        'read_method': 'readuntil',
        'read_terminator': '\r',
        'baudrate': 38400,
    }
    sp = SerialPortClient(
        uri='/dev/ttyUSB0',
        **kw
    )

    loop = asyncio.get_event_loop()

    # asyncio.ensure_future(sp.open())
    asyncio.ensure_future(read_data(sp))
    asyncio.ensure_future(send_data(sp))
    # task = asyncio.ensure_future(output_to_screen())
    task_list = asyncio.Task.all_tasks()

    try:
        loop.run_until_complete(asyncio.wait(task_list))
        # event_loop.run_forever()
    except KeyboardInterrupt:
        print('closing client')
        tasks = asyncio.Task.all_tasks()
        for t in tasks:
            # print(t)
            t.cancel()
        # loop.run_until_complete(asyncio.wait(asyncio.ensure_future(output.close())))

        shutdown(sp)
        # loop.run_forever()

    finally:

        print('closing event loop')
        loop.close()
