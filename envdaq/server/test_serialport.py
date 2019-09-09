from client.serialport import SerialPortClient
import asyncio
import json
import time
from data.message import Message
from datetime import datetime

scan_state = 0
run_state = 'STOPPED'

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
    # while True:
    #     body = 'read'
    #     msg = {'message': body}
    #     message = Message(msgtype='Test', sender_id='me',
    #                       subject='cmd', body=msg)
    #     # print('send_data: {}'.format(msg))

    #     print('send_data: {}'.format(message.to_json()))
    #     # await client.send(json.dumps(msg))
    #     # await client.send('rtclck\n')
    #     await client.send('read\n')
    #     # await asyncio.sleep(.1)
    #     await client.send('raw=2\n')
    #     # await client.send_message(message)
    #     await asyncio.sleep(2)

    # one time for msems
    await start(client)


async def start(client):
    global run_state
    await client.send('sems_mode=2\n')
    # await client.send('all\n')
    run_state = 'RUNNING'


async def stop(client):
    global scan_state
    global run_state
    run_state = 'STOPPING'
    await client.send('sems_mode=0\n')
    while scan_state > 0:
        await asyncio.sleep(.1)
    run_state = 'STOPPED'


async def read_data(client):
    global scan_state
    global run_state
    # while True:
    #     # json_msg = await client.read()
    #     # msg = json.loads(json_msg)
    #     msg = await client.read()
    #     print(f'read_loop: {datetime.utcnow()} {msg.rstrip()}')
    #     parse(msg)
    # cnt = 0
    while True:
        # json_msg = await client.read()
        # msg = json.loads(json_msg)
        msg = await client.read()
        eol = len(msg.rstrip())
        # print(f'{msg.encode()}')
        print(f'read_loop: {datetime.utcnow()} {msg.rstrip()} {eol}')
        # parse(msg)
        scan_state = 999
        if run_state == 'STOPPING':
            parts = msg.split('=')
            if parts[0] == 'scan_state':
                scan_state = int(parts[1])
        # cnt += 1
        # if (cnt > 100):
        #     await stop(client)
        #     cnt = 0


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
    # global scan_state
    # task = asyncio.ensure_future(stop(serialport))
    # asyncio.get_event_loop().run_until_complete(task)
    # stop(serialport)
    # time.sleep(5)
    # task = asyncio.ensure_future(stop(serialport))
    # asyncio.get_event_loop.run_until_complete(task)
    # while scan_state > 0:
    #     time.sleep(.1)
    task = asyncio.ensure_future(serialport.close())
    asyncio.get_event_loop().run_until_complete(task)
    # asyncio.get_event_loop().close()


if __name__ == "__main__":

    kw = {
        # 'read_method': 'readuntil',
        # 'read_terminator': '\r',
        # 'baudrate': 230400,
        'baudrate': 115200,
        # 'baudrate': 38400,
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

        print('stopping msems')
        loop.run_until_complete(
            asyncio.wait(
                [
                    asyncio.ensure_future(
                        stop(sp)
                    )
                ]
            )
        )
        print('complete')
        # asyncio.ensure_future(stop(sp))


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
