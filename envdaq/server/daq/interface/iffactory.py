
class DummyIFDeviceManager():

    def __init__(self):
        devmap = {}
        pass

    def create(self, ifconfig):
        pass

class InterfaceFactory():

    @staticmethod
    def create(config):
        type = config['IFTYPE']
        pass
