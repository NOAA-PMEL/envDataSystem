from daq.interface.ifdevice import IFDeviceFactory


class Managers():
    __managers = dict()
    # TODO: need a way to stop/shutdown gracefully

    @staticmethod
    def start():
        print('starting IFDeviceManager')
        Managers().__managers['IFDeviceManager'] = IFDeviceManager()
        print(f'start: {Managers().__managers["IFDeviceManager"]}')

    @staticmethod
    def get(mgr_type):
        print(f'mgr_type = {mgr_type}')
        if (len(Managers().__managers) == 0):
            Managers().start()
            print(len(Managers().__managers))
        print(f'get: {Managers().__managers["IFDeviceManager"]}')
        for k in Managers().__managers.keys():
            print(k)
        for k, v in Managers().__managers.items():
            print(f'k = {k}')
        print('get manager: {}'.format(mgr_type))
        print(Managers().__managers)
        print(Managers().__managers[mgr_type])
        return Managers().__managers[mgr_type]


class IFDeviceManager():

    def __init__(self):
        print('IFDeviceManger init')
        self.devmap = dict()

    def create(self, dev_type, config, **kwargs):
        print('IFDeviceManager.create()')
        # TODO: use config values to find module,class for type like factory?
        if (dev_type == 'DummyIFDevice'):
            print('create DummyIFDevice')
            # TODO: use different way to get id for lookup
            #       should not have to instantiate and del
            dev = IFDeviceFactory().create(config, **kwargs)
            # dev = DummyIFDevice(config, ui_config=None)
            print(f'dev = {dev}')
            id = dev.get_id()
            # TODO: why am I del dev here?
            if id in self.devmap:
                del dev
                dev = self.devmap[id]
            else:
                self.devmap[id] = dev
        else:

            dev = None

        print(f'devmap: {self.devmap}')
        # print(DummyIFDevice.get_channel_map())
        return dev
