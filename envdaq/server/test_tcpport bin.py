from client.tcpport import TCPPortClient
import asyncio
import json
import time
from data.message import Message
from datetime import datetime



async def send_data(client):

    while True:
        meas_cmd = '#WW44022C06\n'
        read_cmd = '#RR4406\n'
        # msg = {'message': body}
        # message = Message(msgtype='Test', sender_id='me',
        #                   subject='cmd', body=msg)
        # print('send_data: {}'.format(msg))
        # msg = Message(
        #     sender_id='me',
        #     msgtype='TEST',
        #     subject='SEND',
        #     body={
        #         'return_packet_bytes': 2,
        #         'send_packet': meas_cmd,
        #     }
        # )
        # cmd = {
        #     'return_packet_bytes': 2,
        #     'send_packet': meas_cmd,
        # }
        # print(f'send meas cmd: {meas_cmd}')
        await client.send(meas_cmd)
        # await ok_to_send()

        await asyncio.sleep(.1)

        # msg = Message(
        #     sender_id='me',
        #     msgtype='TEST',
        #     subject='SEND',
        #     body={
        #         'return_packet_bytes': 6,
        #         'send_packet': read_cmd,
        #     }
        # )
        # cmd = {
        #     'return_packet_bytes': 6,
        #     'send_packet': read_cmd,
        # }
        # print(f'read data cmd: {read_cmd}')
        await client.send(read_cmd)
 
        # print('send_data: {}'.format(message.to_json()))
        # # await client.send(json.dumps(msg))
        # # await client.send('rtclck\n')
        # await client.send('read\n')
        # await client.send('raw=2\n')
        # # await client.send_message(message)
        await asyncio.sleep(1)


async def read_data(client):

    while True:
        # json_msg = await client.read()
        # msg = json.loads(json_msg)
        msg = await client.read()
        print(f'response: {msg}')
        # if msg == 'OK':
        #     global send_ok = 'True'
        # eol = len(msg.rstrip())
        # print(f'read_loop: {datetime.utcnow()} {msg.rstrip()} {eol}')
        # parse(msg)

    # to parse:
    # hexdata = '0x60eace84e859'
    # >>> import binascii
    # >>> import struct
    # >>> unhexdata = binascii.unhexlify(hexdata[2:])
    # >>> data = struct.unpack('<6B', unhexdata)
    # >>> data
    # (96, 234, 206, 132, 232, 89)
    # >>> temp = data[0] * 256 + data[1]
    # >>> cTemp = -45 + (175 * temp / 65535.0)
    # >>> humidity = 100 * (data[3] * 256 + data[4]) / 65535.0
    # >>> cTemp
    # 21.25085831998169
    # >>> humidity
    # 51.917296101319906


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

# send_ok = False

if __name__ == "__main__":
    
    kw = {
        # 'send_method': 'binary',
        # 'read_method': 'readbinary',
        # 'read_method': 'readuntil',
        # 'read_terminator': '\r'
        # 'read_terminator': '.'
        # 'read_method': 'readbytes',
        # 'read_num_bytes': 1,
        'decode_errors': 'ignore'
    }
    tcp = TCPPortClient(
        # host='moxa16chem2',
        # port=4016,
        address=('10.55.169.52', 26),
        # read_method='readuntil',
        # read_terminator='\r'
        **kw
    )

    loop = asyncio.get_event_loop()

    # asyncio.ensure_future(tcp.open())
    asyncio.ensure_future(read_data(tcp))
    asyncio.ensure_future(send_data(tcp))
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

        shutdown(tcp)
        # loop.run_forever()

    finally:

        print('closing event loop')
        loop.close()
