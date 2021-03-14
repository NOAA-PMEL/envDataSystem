# from client.tcpport import TCPPortClient
import os
import sys
import asyncio
import json
import time
# from shared.data.message import Message
from datetime import datetime
from struct import pack, unpack
from struct import error as structerror


def get_cdp_command(cmd_type):

    start_byte = 27  # Esc char
    setup_command = 1
    data_command = 2

    adc_threshold = 60
    bin_count = 30

    upper_bin_th = [
        91, 111, 159, 190, 215, 243, 254, 272, 301, 355,
        382, 488, 636, 751, 846, 959, 1070, 1297, 1452, 1665,
        1851, 2016, 2230, 2513, 2771, 3003, 3220, 3424, 3660, 4095
    ]

    dof_reject = True
    sample_area = 0.264  # (mm^2)

    # universal start byte (Esc char)
    cmd = pack('<B', start_byte)

    if cmd_type == 'CONFIGURE':
        cmd += pack('<B', setup_command)
        cmd += pack('<H', adc_threshold)
        cmd += pack('<H', 0)  # unused
        cmd += pack('<H', bin_count)
        cmd += pack('<H', dof_reject)

        # unused bins
        for i in range(0, 5):
            cmd += pack('<H', 0)

        # upper bin thresholds
        for n in upper_bin_th:
            cmd += pack('<H', n)

        # fill last unused bins
        for n in range(0, 10):
            cmd += pack('<H', n)

    elif cmd_type == 'SEND_DATA':
        cmd += pack('B', data_command)

    else:
        return None

    checksum = 0
    for ch in cmd:
        checksum += ch

    cmd += pack('<H', checksum)
    return cmd


async def send_data(client):

    await asyncio.sleep(2)

    configure_cmd = get_cdp_command('CONFIGURE')
    send_data_cmd = get_cdp_command('SEND_DATA')
    first = True
    while True:
        if first:
            # await client.send(configure_cmd)
            cmd = {
                'return_packet_bytes': 4,
                'send_packet': configure_cmd,
            }
            first = False
        else:
            cmd = {
                'return_packet_bytes': 156,
                'send_packet': send_data_cmd,
            }
        print(f'client.send: {cmd}')
        await client.send(cmd)

        # await client.send(send_data_cmd)
        # await ok_to_send()

        # await asyncio.sleep(.1)

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
        # cmd = {
        #     'return_packet_bytes': 6,
        #     'send_packet': send_data_cmd,
        # }
        # await client.send(cmd)

        # print('send_data: {}'.format(message.to_json()))
        # # await client.send(json.dumps(msg))
        # # await client.send('rtclck\n')
        # await client.send('read\n')
        # await client.send('raw=2\n')
        # # await client.send_message(message)
        await asyncio.sleep(1)


async def read_data(client):

    First = True
    while True:
        # json_msg = await client.read()
        # msg = json.loads(json_msg)
        packet = await client.read()

        if First:
            ack_fmt = '<4B'
            try:
                data = unpack(ack_fmt, packet)
                print(f'data: {data}')
            except structerror:
                print(f'bad packet {packet}')
                # return None
            First = False
            # if data[0] == 6:
            #     self.scan_run_state = 'RUN'
            #     return None
        else:
            data_format = '<8HI5HI30IH'
            try:
                data = unpack(data_format, packet)
                print(f'data: {data}')
            except structerror:
                print(f'bad packet {packet}')
                # return None

        # print(f'response: {msg.decode()}')
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

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # print(BASE_DIR)
    # sys.path.append(os.path.join(BASE_DIR, 'envdsys/shared'))
    sys.path.append(os.path.join(BASE_DIR, "envdsys"))

    from client.tcpport import TCPPortClient
    from shared.data.message import Message

    kw = {
        'send_method': 'binary',
        'read_method': 'readbinary',
        # 'read_method': 'readuntil',
        # 'read_terminator': '\r'
        # 'read_terminator': '.'
        # 'read_method': 'readbytes',
        # 'read_num_bytes': 1,
        # 'decode_errors': 'ignore'
    }
    tcp = TCPPortClient(
        # host='moxa16chem2',
        # port=4016,
        address=('10.55.169.52', 24),
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
