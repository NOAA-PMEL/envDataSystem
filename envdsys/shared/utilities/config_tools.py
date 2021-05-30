import json
import hashlib


def get_hashkey(config):
    """
    Return a hash string used as key for a given config

    Argument:
        config: dictionary containing configuration

    Return:
        string | None
    """

    if config:
        
        try:
            input = json.dumps(config, sort_keys=True)
            m = hashlib.md5(input.encode("utf-8"))
            return m.hexdigest()
        except TypeError:
            print(f"unable to hash config")
            # return None

        return None

