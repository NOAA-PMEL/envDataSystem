import serial
from struct import *
import math

packet = bytearray()
# packet.append(1B)
# packet.append(02)
# packet.append(1D00)

ser = serial.Serial(
    'COM15',
    57600,
    timeout=1
)
print(ser.name)
# ser.write(packet)
send_data = pack('<B', 27)
send_data += pack('B', 2)
checksum = 0
for ch in send_data:
    checksum += ch
send_data += pack('<H', checksum)
print(f'send_data: {send_data.hex()}, {checksum}')

# # ser.write(bytes.fromhex('1B021D00'))
# ser.write(send_data)
# retpacket = ser.read(156)
# # print(retpacket)
# # print(retpacket.hex())
# # struct_format = '<IIIIIIIILIIIIILLLLLLLLLLLLLLLLLLLLLLLLI'
# struct_format = '<8HI5HI30IH'
# print(calcsize(struct_format))
# data = unpack(struct_format, retpacket)
# size = calcsize(struct_format)
# print(f'data[{size}] = {data}')
# # ser.flush()
# # ser.close()

# print(f'laser current = {data[0]*0.061}')
# print(f'dump spot monitor = {5*data[1]/4095}')
# v = 5*data[2]/4095
# degC = 1 / ( ((math.log( (5/v) -1))/3750) + 1/298) - 273
# print(f'wing temp = {degC}')
# v = 5*data[3]/4095
# degC = 1 / ( ((math.log( (5/v) -1))/3750) + 1/298) - 273
# print(f'laser temp = {degC}')
# print(f'size baseline = {5*data[4]/4095}')
# print(f'qual baseline = {5*data[5]/4095}')
# print(f'5v monitor = {(5*data[6]/4095)*2}')
# # print(f'control board temp = {(data[7]*0.06401)-50}')
# v = 5*data[7]/4095
# degC = 1 / ( ((math.log( (5/v) -1))/3750) + 1/298) - 273
# print(f'control board temp = {degC}')

# print(f'reject DOF = {data[8]}')

# ser.flush()

# send config
cfg = pack('<B', 27)
cfg += pack('<B', 1)
cfg += pack('<H', 60)
cfg += pack('<H', 0)
cfg += pack('<H', 30)
cfg += pack('<H', True)

for i in range(0,5):
    cfg += pack('<H', 0)

#Thresholds=<30>91,111,159,190,215,243,254,272,301,355,382,488,636,751,846,959,1070,1297,1452,1665,1851,2016,2230,2513,2771,3003,3220,3424,3660,4095
bin_th = [
    91,111,159,190,215,243,254,272,301,355,
    382,488,636,751,846,959,1070,1297,1452,1665,
    1851,2016,2230,2513,2771,3003,3220,3424,3660,4095
]
for n in bin_th:
    cfg += pack('<H', n)
    # print({cfg.hex()})

for n in range(0,10):
    cfg += pack('<H', n)

checksum = 0
for ch in cfg:
    checksum += ch

cfg += pack('<H', checksum)
ser.write(cfg)
retpacket = ser.read(4)
print(f'retpacket: {retpacket}')
ser.flush()

reread = True
if reread:
    ser.write(send_data)
    retpacket = ser.read(156)
    # print(retpacket)
    # print(retpacket.hex())
    # struct_format = '<IIIIIIIILIIIIILLLLLLLLLLLLLLLLLLLLLLLLI'
    struct_format = '<8HI5HI30IH'
    print(calcsize(struct_format))
    data = unpack(struct_format, retpacket)
    size = calcsize(struct_format)
    print(f'data[{size}] = {data}')
    # ser.flush()
    # ser.close()

    print(f'laser current = {data[0]*0.061}')
    print(f'dump spot monitor = {5*data[1]/4095}')
    v = 5*data[2]/4095
    degC = 1 / ( ((math.log( (5/v) -1))/3750) + 1/298) - 273
    print(f'wing temp = {degC}')
    v = 5*data[3]/4095
    degC = 1 / ( ((math.log( (5/v) -1))/3750) + 1/298) - 273
    print(f'laser temp = {degC}')
    print(f'size baseline = {5*data[4]/4095}')
    print(f'qual baseline = {5*data[5]/4095}')
    print(f'5v monitor = {(5*data[6]/4095)*2}')
    # print(f'control board temp = {(data[7]*0.06401)-50}')
    v = 5*data[7]/4095
    degC = 1 / ( ((math.log( (5/v) -1))/3750) + 1/298) - 273
    print(f'control board temp = {degC}')

    print(f'reject DOF = {data[8]}')

ser.flush()
ser.close()
