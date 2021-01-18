import abc
import pkgutil
# import sys
import importlib
import inspect
# from daq.controller.controller import Controller#, ControllerFactory
# from daq.controller.controller import ControllerFactory, Controller
# from daq.controller.controller import Controller
# from daq.interface.ifdevice import IFDeviceFactory
from daq.controller.controller import Controller
from daq.instrument.instrument import Instrument
from daq.interface.ifdevice import IFDevice


class SysManager():
    _managers = dict()
    # TODO: need a way to stop/shutdown gracefully

    @staticmethod
    def start():
        # print('starting IFDeviceManager')
        # Managers().__managers['IFDeviceManager'] = IFDeviceManager()
        SysManager._managers['ControllerManager'] = ControllerManager()
        SysManager._managers['InstrumentManager'] = InstrumentManager()
        # print(f'start: {Managers().__managers["IFDeviceManager"]}')
        print(f'sysmanager {SysManager._managers}')

    @staticmethod
    def get(mgr_type):
        # print(f'mgr_type = {mgr_type}')
        if (len(SysManager._managers) == 0):
            SysManager().start()
            # print(len(Managers().__managers))
        # print(f'get: {Managers().__managers["IFDeviceManager"]}')
        # for k in Managers().__managers.keys():
        #     print(k)
        # for k, v in Managers().__managers.items():
        #     print(f'k = {k}')
        # print('get manager: {}'.format(mgr_type))
        # print(Managers().__managers)
        # print(Managers().__managers[mgr_type])
        return SysManager().__managers[mgr_type]

    @staticmethod
    def get_definitions_all():
        sys_def = dict()
        sys_def['SYSTEM_DEFINITIONS'] = dict()
        for name, manager in SysManager._managers.items():
            # print(f'name, manager: {name}, {manager}')
            definition = manager.get_sys_definitions()
            # print(f'definition: {definition}')
            for def_name, def_value in definition.items():
                # print(f'def_name, def_value: {def_name}, {def_value}')
                sys_def['SYSTEM_DEFINITIONS'][def_name] = def_value

        return sys_def


class DAQManager(abc.ABC):

    def __init__(self):
        self.daq_map = dict()
        # self.update()
        # print(f'definitions: {self.get_sys_definitions()}')

    @abc.abstractmethod
    def update(self, force_new=False):
        pass

    def get_entry(self, id):
        if id in self.daq_map:
            return self.daq_map[id]
        return None

    def get_all(self):
        return self.daq_map

    @abc.abstractmethod
    def get_sys_definitions(self, update=True):
        pass

    def collect_classes(self, module_list, cls):

        cls_list = []
        for mod in module_list:
            cls_list = self._explore_package(mod, cls, cls_list)
            # print(f'collect_classes: {mod} :: {cls_list}')
        return cls_list

    def _get_subclasses(self, module_name, cls):
        subcls = []
        mod = importlib.import_module(module_name)
        # print(f'mod: {mod}')
        for name, data in inspect.getmembers(mod, inspect.isclass):
            # print('{} : {!r}'.format(name, data))
            # print(f'issubbclass: {issubclass(data, cls)}')
            # print(f'inspect: {inspect.isabstract(data)}')
            try:
                if (
                    issubclass(data, cls) and
                    not inspect.isabstract(data)  # and
                    # cls.INSTANTIABLE
                ):
                    # print(f'istantiable: {data.INSTANTIABLE}')
                    if data.INSTANTIABLE:
                        # print('!!!found : {} : {!r}'.format(name, data))
                        subcls.append(data)
                    # print(data)
            except Exception as e:
                print(f'subclass except: {e}')

        return subcls

    def _explore_package(self, module_name, cls, subs):

        mod = importlib.import_module(module_name)
        # print(f'explore')
        for sub_module in pkgutil.iter_modules(mod.__path__):
            # print(sub_module)
            importer, sub_module_name, ispkg = sub_module
            # print('sub_module: '+sub_module_name+' ('+str(ispkg)+')')

            # sub_module.is_package
            # importlib.import_module(qname)
            qname = module_name + "." + sub_module_name
            # print(f'qname = {qname}')
            if ispkg:
                self._explore_package(qname, cls, subs)
            else:
                # submod = importlib.import_module(qname)
                for subcls in self._get_subclasses(qname, cls):
                    if subcls not in subs:
                        subs.append(subcls)
                # print('Look for subclass in: ' + qname)
                # print(inspect.getmodulename(qname))
                # pass
                # print(f'subs: {subs}')

        return subs


class ControllerManager(DAQManager):

    def __init__(self):
        # print('@@@@@@@@@@@2ControllerManager init')
        super().__init__()

    def update(self, force_new=False):
        # get all available controllers in system
        # print('******update')
        controller_list = []
        controller_list = self.collect_classes(['daq.controller'], Controller)
        # self._explore_package('daq.controller', 'Controller', controller_list)
        # print(f'controller list: {controller_list}')
        # pass

        for controller in controller_list:
            self.daq_map[controller.__name__] = controller

        # print(f'controller_map: {self.daq_map}')

    def get_sys_definitions(self, update=True):
        if update:
            self.update()
        print(f'get_sys_def: {self.daq_map}')
        definitions = dict()
        definitions['CONTROLLER_SYS_DEFS'] = dict()
        for k, controller in self.daq_map.items():
            # print(f'controller is {controller}')
            definitions['CONTROLLER_SYS_DEFS'][k] = controller.get_definition()

        return definitions


class InstrumentManager(DAQManager):

    def __init__(self):
        # print('@@@@@@@@@@@2InstrumentManager init')
        super().__init__()

    def update(self, force_new=False):
        # get all available controllers in system
        # print('******update')
        instrument_list = []
        instrument_list = self.collect_classes(['daq.instrument'], Instrument)
        # self._explore_package('daq.controller', 'Controller', controller_list)
        # print(f'instrument list: {instrument_list}')
        # pass

        for instrument in instrument_list:
            self.daq_map[instrument.__name__] = instrument

        # print(f'instrument_map: {self.daq_map}')

    def get_sys_definitions(self, update=True):
        if update:
            self.update()
        # print(f'get_sys_def: {self.daq_map}')
        definitions = dict()
        definitions['INSTRUMENT_SYS_DEFS'] = dict()
        for k, instrument in self.daq_map.items():
            # print(f'instrument is {instrument}')
            definitions['INSTRUMENT_SYS_DEFS'][k] = instrument.get_definition()

        return definitions


class IFDeviceManager(DAQManager):

    def __init__(self):
        # print('@@@@@@@@@@@2InstrumentManager init')
        super().__init__()

    def update(self, force_new=False):
        # get all available controllers in system
        # print('******update')
        ifdevice_list = []
        ifdevice_list = self.collect_classes(
            ['daq.interface'], IFDevice
        )
        # self._explore_package('daq.controller', 'Controller', controller_list)
        # print(f'instrument list: {instrument_list}')
        # pass

        for ifdevice in ifdevice_list:
            self.daq_map[ifdevice.__name__] = ifdevice

        # print(f'ifdevice_map: {self.daq_map}')

    def get_sys_definitions(self, update=True):
        if update:
            self.update()
        # print(f'get_sys_def: {self.daq_map}')
        definitions = dict()
        definitions['IFDEVICE_SYS_DEFS'] = dict()
        for k, ifdevice in self.daq_map.items():
            # print(f'ifdevice is {ifdevice}')
            definitions['IFDEVICE_SYS_DEFS'][k] = ifdevice.get_definition()

        return definitions
