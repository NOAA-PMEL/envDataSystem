# @Author: derek
# @Date:   2018-12-13T13:47:03-08:00
# @Last modified by:   derek
# @Last modified time: 2018-12-13T14:16:06-08:00

import sys
from daq.instrument import instrument


def path_name():
    print(sys.path)
    instrument.dir_name()
