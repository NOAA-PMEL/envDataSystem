
import os


def dir_name():
    print('here')
    print(__file__)
    print(os.path.dirname(os.path.abspath(__file__)))
