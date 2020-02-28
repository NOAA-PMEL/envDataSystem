from datetime import datetime
from collections import OrderedDict
import json

class DataBuffer():
    """
This is class used to buffer DAQ data and allows
listening instruments access data by timestamp. The Buffer
size can be specified by number elements

Attributes:
    buf_size: number of elements to store

    """
    def __init__(self,buf_size=60):

        self.buf_size = buf_size
        self.buffer = OrderedDict()

    def append(self, key, dat):

        #stamp = dt.timestamp()
        self.buffer[key] = dat

        while (len(self.buffer) > self.buf_size):
            self.buffer.popitem(last=False)

        print(len(self.buffer))
        # deltimes = []
        # for k, v in self.buffer.items():
        #     if (k < (stamp - self.buf_size)):
        #         deltimes.append(k)
        #     else:
        #         break
        #
        # for t in deltimes:
        #     del self.buffer[t]

    def get(self, key):
        return self.buffer[key]


if __name__ == "__main__":

    import time

    buf = DataBuffer(buf_size=10)

    for x in range(50):

        ts = datetime.utcnow()
        tstr = ts.isoformat(timespec='seconds')
        buf.append(ts,tstr)
        el = buf.get(ts)
        print(el)
        time.sleep(1)
