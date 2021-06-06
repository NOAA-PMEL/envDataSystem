from datetime import datetime
import pytz
import time
import math

isofmt = '%Y-%m-%dT%H:%M:%SZ'


def time_to_next(sec):
    now = time.time()
    delta = sec - (math.fmod(now, sec))
    return delta


def get_timestamp():
    return pytz.utc.localize(datetime.utcnow())


def dt_to_string(dt=None, format=isofmt):
    if dt is None:
        dt = get_timestamp()
    return datetime.strftime(dt, format)


def string_to_dt(dt_string, format=isofmt):
    dt = datetime.strptime(dt_string, format)
    return pytz.utc.localize(dt)


if __name__ == "__main__":

    dt = get_timestamp()
    print(dt)
    time.sleep(1)
    print(get_timestamp())
    time.sleep(1)

    print(dt_to_string(dt=dt))

    print(string_to_dt(dt_to_string(dt=dt)))
