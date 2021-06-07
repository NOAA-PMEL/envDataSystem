from abc import abstractmethod
import asyncio
from os import name
from shutil import register_archive_format
from typing import AsyncIterable

# from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

from django.core.exceptions import MultipleObjectsReturned
from shared.data.status import Status
from shared.data.namespace import Namespace

# from daq.daq import DAQ
# from envdaq import data
from envnet.models import Network, ServiceRegistration, DAQRegistration


class ServiceRegistry:

    # number of seconds before daq_server is considered
    #   disconnected
    disconnected_service_limit = 60
    disconnected_daq_limit = 10

    # number of seconds before daq_server is removed
    #   from registry
    auto_clean_limit = 600  # 10 minutes

    local_network = None

    run_state = "STOPPED"

    # @staticmethod
    # async def start(network="default_network"):
    #     await ServiceRegistry.start_no_wait(network)

    async def start(network="default_network"):
        await ServiceRegistry.start_registry(network)
        # loop=asyncio.get_event_loop()
        # print(f"registry: {loop}")
        if ServiceRegistry.run_state != "RUNNING":
            asyncio.create_task(ServiceRegistry.check_status())
            ServiceRegistry.run_state = "RUNNING"
        # regs = await ServiceRegistry.get_all_registrations()
        # print(regs)
        # print(f"all reg: {ServiceRegistry.get_all_registrations()}")

    @staticmethod
    @database_sync_to_async
    def start_registry(network="default_network"):
        print("starting service registry")

        # deactivate all networks
        nets = Network.objects.all()
        for net in nets:
            net.deactivate()

        try:
            net = Network.objects.get(name=network)
            # net.activate()
        except Network.MultipleObjectsReturned:
            result = Network.objects.filter(name=network)
            for s in result:
                s.delete()
            net = Network(name=network)
            net.save()
        except Network.DoesNotExist:
            net = Network(name=network)
            # net = Network(name=network)
            net.save()
        net.activate()
        ServiceRegistry.local_network = net
        # asyncio.create_task(ServiceRegistry.check_status())
        # ServiceRegistry.run_state = "RUNNING"
        # start broadcasting
        # start housekeeping checks
        # if ServiceRegistry.run_state == "STOPPED":
        #     ServiceRegistry.start_checks()
        # ServiceRegistry.run_state = "RUNNING"
        # return net

    def start_checks():
        # loop = asyncio.get_event_loop()
        # task = asyncio.ensure_future(ServiceRegistry.check_status())
        # print(task)
        # loop.run_until_complete(task)
        asyncio.create_task(ServiceRegistry.check_status())

    # recieve from other servers
    #   add list of remote services

    @staticmethod
    async def register(local=True, config=None):
        reg = await ServiceRegistry.register_no_wait(local, config)
        if not reg:
            reg = await ServiceRegistry.update_registration(local, config)
        return reg

    @staticmethod
    @database_sync_to_async
    def register_no_wait(local=True, config=None):
        print(f"register service: {local}, {config}")
        if config:
            print(config["host"])
            try:
                # print(f'{config["HOST"]}, {config["PORT"]}')
                reg = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                if reg.get_age() > ServiceRegistry.auto_clean_limit:
                    reg.delete()
                else:
                    return None
                    # registration = ServiceRegistry.update_registration(local, config)
                    # print(f"1:{registration}")
                    # return registration
            except ServiceRegistration.MultipleObjectsReturned:
                result = ServiceRegistration.objects.filter(
                    host=config["host"], port=config["port"]
                )
                for s in result:
                    s.delete()
            except ServiceRegistration.DoesNotExist:
                pass

            network = "default"
            # if local:
            #     network = ServiceRegistry.local_network.name
            # else:
            #     try:
            #         network = config["network"]
            #     except KeyError:
            #         pass # defaults to "default"

            # create new Reg
            reg = ServiceRegistration(
                local_service=local,
                host=config["host"],
                port=config["port"],
                status="CONNECTED"
                # service_list = config.service_list
            )
            reg.save()
            reg.add_services(config["service_list"])
            reg.join_network(ServiceRegistry.get_network_name(local, config))
            registration = reg.get_registration()
            return registration

    @staticmethod
    async def update_registration(local=True, config=None):
        reg = await ServiceRegistry.update_registration_no_wait(local, config)
        return reg

    @staticmethod
    @database_sync_to_async
    def update_registration_no_wait(local=True, config=None):
        if config:

            network = "default"
            if local:
                network = ServiceRegistry.local_network.name
            else:
                try:
                    network = config["network"]
                except KeyError:
                    pass  # defaults to "default"

            try:
                # srv = ServiceRegistration.objects.get(regkey=config["regkey"])
                reg = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                if reg.get_age() > ServiceRegistry.auto_clean_limit:
                    reg.delete()
                elif reg.regkey in config and config["regkey"] != reg.regkey:
                    reg.delete()
                else:
                    reg.local_service = local
                    reg.host = config["host"]
                    reg.port = config["port"]
                    reg.status = "CONNECTED"
                    # srv.service_list = config.service_list
                    reg.save(do_update=True)
                    reg.add_services(config["service_list"])
                    # srv.save()
                    # if local:
                    #     ServiceRegistry.local_network.add_registration(srv)
                    reg.join_network(ServiceRegistry.get_network_name(local, config))
                    registration = reg.get_registration()
                    print(f"3:{registration}")
                    return registration
            except ServiceRegistration.DoesNotExist:
                pass

            # create new Reg here don't want to pass back to add ang get caught in loop?
            reg = ServiceRegistration(
                local_service=local,
                host=config["host"],
                port=config["port"],
                status="CONNECTED"
                # service_list = config.service_list
            )
            reg.add_services(config["service_list"])
            reg.save(do_update=True)
            reg.join_network(ServiceRegistry.get_network_name(local, config))
            registration = reg.get_registration()
            print(f"4:{registration}")
            return registration

    @staticmethod
    async def unregister(local=True, config=None):
        await ServiceRegistry.unregister_no_wait(local, config)

    @staticmethod
    @database_sync_to_async
    def unregister_no_wait(local=True, config=None):
        if config:
            try:
                srv = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                srv.delete()
            except ServiceRegistration.DoesNotExist:
                pass

    # def ping(local=True, regkey=None, config=None):
    @staticmethod
    async def ping(local=True, config=None):
        await ServiceRegistry.ping_no_wait(local, config)

    @staticmethod
    @database_sync_to_async
    def ping_no_wait(local=True, config=None):
        # theoretically, we should not be pinging local here
        # if not regkey and config and (regkey in config):
        #     regkey = config["regkey"]
        # if regkey:
        if config:
            try:
                reg = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                reg.status = "CONNECTED"
                # srv = ServiceRegistration.objects.get(regkey=config["regkey"])
                reg.save(do_update=True)  # update modified time stamp

            except ServiceRegistration.DoesNotExist:
                pass

    @staticmethod
    def get_network_name(local=True, config=None):
        if local:

            name = ServiceRegistry.local_network.name
        elif config:
            name = "default"
            try:
                name = config["network"]
            except KeyError:
                pass
        return name

    @staticmethod
    @database_sync_to_async
    def clean_registrations():
        # regs = database_sync_to_async(ServiceRegistration.objects.filter)(
        #     network=ServiceRegistry.local_network
        # )
        regs = ServiceRegistration.objects.filter(
            local_service=False, network=ServiceRegistry.local_network
        )
        # regs = None
        # print(regs)
        # return regs
        for reg in regs:
            # print(f"status: {reg}, age: {reg.get_age()}")
            # print(f"check status: {reg}")
            if reg.get_age() > ServiceRegistry.auto_clean_limit:
                print(f"removing registration for {reg} due to auto timeout")
                reg.delete()
            elif reg.get_age() > ServiceRegistry.disconnected_service_limit:
                reg.status = "DISCONNECTED"
                print(reg.status)
                reg.save()

    # @sync_to_async
    @staticmethod
    async def check_status():
        # print(tmp)
        print("check_status")
        while True:
            await ServiceRegistry.clean_registrations()
            # regs = await database_sync_to_async(ServiceRegistration.objects.filter(
            #     network=ServiceRegistry.local_network
            # ))
            # regs = await ServiceRegistry.get_all_registrations()
            # print(regs)
            # for reg in regs:
            #     print(f'check status: {reg.name}')
            #     if reg.get_age() > ServiceRegistry.auto_clean_limit:
            #         print(f"removing registration for {reg.name} due to auto timeout")
            #         reg.delete()
            #     elif reg.get_() > ServiceRegistry.disconnected_service_limit:
            #         reg.status = "DISCONNECTED"
            # print("tick")
            await asyncio.sleep(2)


class DAQRegistry:

    # number of seconds before daq_server is considered
    #   disconnected
    # disconnected_service_limit = 60
    disconnected_limit = 10

    # number of seconds before daq_server is removed
    #   from registry
    auto_clean_limit = 600  # 10 minutes

    local_network = None

    run_state = "STOPPED"

    # @staticmethod
    # async def start(network="default_network"):
    #     await ServiceRegistry.start_no_wait(network)

    @staticmethod
    async def start():
        print("starting daq registry")
        # await DAQRegistry.start_registry()
        # loop=asyncio.get_event_loop()
        # print(f"registry: {loop}")
        if DAQRegistry.run_state != "RUNNING":
            while not ServiceRegistry.local_network:
                print("waiting for service registry to spin up")
                await asyncio.sleep(0.5)
            DAQRegistry.local_network = ServiceRegistry.local_network
            await DAQRegistry.clear()
            asyncio.create_task(DAQRegistry.check_status())
            DAQRegistry.run_state = "RUNNING"
        # regs = await ServiceRegistry.get_all_registrations()
        # print(regs)
        # print(f"all reg: {ServiceRegistry.get_all_registrations()}")

    @staticmethod
    async def clear():
        await DAQRegistry.clear_no_wait()

    @staticmethod
    @database_sync_to_async
    def clear_no_wait():
        regs = DAQRegistration.objects.all()
        for reg in regs:
            reg.delete()

    # @staticmethod
    # @database_sync_to_async
    # def start_registry():
    #     print("starting registry")
    #     try:
    #         net = Network.objects.get(name=network)
    #         net.activate()
    #     except Network.MultipleObjectsReturned:
    #         result = Network.objects.filter(name=network)
    #         for s in result:
    #             s.delete()
    #     except Network.DoesNotExist:
    #         net = Network(name=network)
    #         # net = Network(name=network)
    #         net.save()
    #     net.activate()
    #     ServiceRegistry.local_network = net
    #     # asyncio.create_task(ServiceRegistry.check_status())
    #     # ServiceRegistry.run_state = "RUNNING"
    #     # start broadcasting
    #     # start housekeeping checks
    #     # if ServiceRegistry.run_state == "STOPPED":
    #     #     ServiceRegistry.start_checks()
    #     # ServiceRegistry.run_state = "RUNNING"
    #     # return net

    # def start_checks():
    #     # loop = asyncio.get_event_loop()
    #     # task = asyncio.ensure_future(ServiceRegistry.check_status())
    #     # print(task)
    #     # loop.run_until_complete(task)
    #     asyncio.create_task(DAQRegistry.check_status())

    # async def register(
    #     reg_id="default",
    #     reg_id2=None,
    #     namespace={},
    #     type="DAQServer",
    #     config={},
    #     config2={},
    # ):
    @staticmethod
    async def register(
        reg_id=Namespace().get_namespace_sig(),
        namespace=Namespace().to_dict(),
        type=Namespace.DAQSERVER,
        config=dict(),
    ):
        # if not reg_id2:
        #     reg_id2 = Namespace().get_namespace_sig()

        # registration = await DAQRegistry.register_no_wait(
        #     reg_id=reg_id,
        #     reg_id2=reg_id2,
        #     namespace=namespace,
        #     type=type,
        #     config=config,
        #     config2=config2,
        # )

        registration = await DAQRegistry.register_no_wait(
            reg_id=reg_id,
            namespace=namespace,
            type=type,
            config=config,
        )

        # if not registration:
        #     registration = await DAQRegistry.update_registration(namespace, type, config)
        return registration

    # @database_sync_to_async
    # def register_no_wait(
    #     reg_id="default",
    #     reg_id2=None,
    #     namespace={},
    #     type="DAQServer",
    #     config={},
    #     config2={},
    # ):
    @staticmethod
    @database_sync_to_async
    def register_no_wait(
        reg_id=Namespace().get_namespace_sig(),
        namespace=Namespace().to_dict(),
        type=Namespace.DAQSERVER,
        config=dict(),
    ):
        # print(f"register daq: {config}")
        # if config:
        # print(config["host"])

        # if not reg_id2:
        #     reg_id2 = Namespace().get_namespace_sig()

        try:
            # print(f'{config["HOST"]}, {config["PORT"]}')
            # registration = DAQRegistration.objects.get(reg_id2=reg_id2, daq_type=type)
            registration = DAQRegistration.objects.get(reg_id=reg_id, daq_type=type)
            if registration:
                registration.delete()
        except DAQRegistration.MultipleObjectsReturned:
            # result = DAQRegistration.objects.filter(reg_id2=reg_id2, daq_type=type)
            result = DAQRegistration.objects.filter(reg_id=reg_id, daq_type=type)
            for s in result:
                s.delete()
        except DAQRegistration.DoesNotExist:
            pass

        network = "default"
        # if local:
        #     network = ServiceRegistry.local_network.name
        # else:
        #     try:
        #         network = config["network"]
        #     except KeyError:
        #         pass # defaults to "default"

        # create new Reg
        # registration = DAQRegistration(
        #     reg_id=reg_id,
        #     reg_id2=reg_id2,
        #     namespace=namespace,
        #     daq_type=type,
        #     config=config,
        #     config2=config2,
        #     status="CONNECTED",
        # )
        status2 = Status()
        status2.set_connection_status(Status.CONNECTED)
        print(f"register: {reg_id}, {namespace}")
        registration = DAQRegistration(
            reg_id=reg_id,
            namespace=namespace,
            daq_type=type,
            config=config,
            status="CONNECTED",
            status2=status2.to_dict(),
        )
        registration.save()
        # TODO: update service definition to include this reg

        registration = registration.get_registration()
        return registration

    # @staticmethod
    # async def update_registration(
    #     reg_id="default",
    #     reg_id2=Namespace().get_namespace_sig(),
    #     namespace={},
    #     type="DAQServer",
    #     registration=None,
    # ):
    @staticmethod
    async def update_registration(
        reg_id=Namespace().get_namespace_sig(),
        namespace=Namespace().to_dict(),
        type=Namespace.DAQSERVER,
        config=dict(),
        registration=None,
    ):
        # reg = await DAQRegistry.update_registration_no_wait(
        #     reg_id=reg_id,
        #     reg_id2=reg_id2,
        #     namespace=namespace,
        #     type=type,
        #     registration=registration,
        # )
        reg = await DAQRegistry.update_registration_no_wait(
            reg_id=reg_id,
            namespace=namespace,
            type=type,
            registration=registration,
        )
        return reg

    # @staticmethod
    # @database_sync_to_async
    # def update_registration_no_wait(
    #     reg_id="default",
    #     reg_id2=Namespace().get_namespace_sig(),
    #     namespace={},
    #     type="DAQServer",
    #     registration=None,
    # ):
    @staticmethod
    @database_sync_to_async
    def update_registration_no_wait(
        reg_id=Namespace().get_namespace_sig(),
        namespace=Namespace().to_dict(),
        type=Namespace.DAQSERVER,
        config=dict(),
        registration=None,
    ):
        # if config:

        # network = "default"
        # if local:
        #     network = ServiceRegistry.local_network.name
        # else:
        #     try:
        #         network = config["network"]
        #     except KeyError:
        #         pass  # defaults to "default"

        try:
            # srv = ServiceRegistration.objects.get(regkey=config["regkey"])
            # reg = DAQRegistration.objects.get(reg_id2=reg_id2, daq_type=type)
            reg = DAQRegistration.objects.get(reg_id=reg_id, daq_type=type)
        except DAQRegistration.DoesNotExist:
            reg = None
            # if reg.get_age() > DAQRegistry.auto_clean_limit:
            #     reg.delete()
            # elif config and reg.regkey in config and config["regkey"] != reg.regkey:
            #     reg.delete()
            # else:
        config = {}
        # regkey = None
        if registration:
            config = registration["config"]
            # config2 = registration["config2"]
            # regkey = registration["regkey"]
        if not reg:
            # reg = DAQRegistration(
            #     reg_id2=reg_id2,
            #     namespace=namespace,
            #     daq_type=type,
            #     config=config,
            #     config2=config2,
            # )
            reg = DAQRegistration(
                reg_id=reg_id,
                namespace=namespace,
                daq_type=type,
                config=config,
            )
        if reg:
            # reg.reg_id2 = reg_id2
            reg.reg_id = reg_id
            reg.namespace = namespace
            reg.daq_type = type
            reg.config = config
            # reg.config2 = config2
            reg.status = "CONNECTED"
            
            status2 = Status()
            status2.set_connection_status(Status.CONNECTED)
            reg.status2 = status2.to_dict()
            # if regkey:
            #     reg.regkey = regkey

            # srv.service_list = config.service_list
            reg.save(do_update=True)
            # TODO: update service

            # reg.add_services(config["service_list"])
            # srv.save()
            # if local:
            #     ServiceRegistry.local_network.add_registration(srv)
            # reg.join_network(ServiceRegistry.get_network_name(local, config))
            return reg.get_registration()
            # print(f"3:{registration}")
            # return registration
        else:
            return None
        # # create new Reg here don't want to pass back to add ang get caught in loop?
        # reg = DAQRegistration(
        #     namespace=namespace, daq_type=type, config=config, status="CONNECTED"
        # )
        # reg.save()
        # # TODO: update service
        # registration = reg.get_registration()
        # # print(f"4:{registration}")
        # return registration

    # @staticmethod
    # async def unregister(
    #     reg_id="default", reg_id2=Namespace().get_namespace_sig(), type="DAQServer"
    # ):
    #     await DAQRegistry.unregister_no_wait(reg_id=reg_id, reg_id2=reg_id2, type=type)
    @staticmethod
    async def unregister(
        reg_id=Namespace().get_namespace_sig(), type=Namespace.DAQSERVER
    ):
        await DAQRegistry.unregister_no_wait(reg_id=reg_id, type=type)

    # @staticmethod
    # @database_sync_to_async
    # def unregister_no_wait(
    #     reg_id="default", reg_id2=Namespace().get_namespace_sig(), type="DAQServer"
    # ):
    @staticmethod
    @database_sync_to_async
    def unregister_no_wait(
        reg_id=Namespace().get_namespace_sig(), type=Namespace.DAQSERVER
    ):
        try:
            # print(f"unregister:{reg_id}")
            # reg = DAQRegistration.objects.get(reg_id2=reg_id2, daq_type=type)
            reg = DAQRegistration.objects.get(reg_id=reg_id, daq_type=type)
            # print(f"Unregistering: {reg}")
            reg.delete()
            # print(f"success")
        except DAQRegistration.DoesNotExist:
            # print(f"unregister: reg_id does not exist {reg_id}")
            pass

    # @staticmethod
    # async def get_registration(reg_id="default", reg_id2=Namespace().get_namespace_sig(), type="DAQServer"):
    #     registration = await DAQRegistry.get_registration_no_wait(reg_id=reg_id, reg_id2=reg_id2, type=type)
    #     return registration
    @staticmethod
    async def get_registration(
        reg_id=Namespace().get_namespace_sig(), type=Namespace.DAQSERVER
    ):
        # registration = await DAQRegistry.get_registration_no_wait(
        #     reg_id=reg_id, reg_id2=reg_id2, type=type
        # )
        registration = await DAQRegistry.get_registration_no_wait(
            reg_id=reg_id, type=type
        )
        return registration

    # @staticmethod
    # @database_sync_to_async
    # def get_registration_no_wait(
    #     reg_id="default", reg_id2=Namespace().get_namespace_sig(), type="DAQServer"
    # ):
    @staticmethod
    @database_sync_to_async
    def get_registration_no_wait(
         reg_id=Namespace().get_namespace_sig(), type=Namespace.DAQSERVER
   ):
        # theoretically, we should not be pinging local here
        # if not regkey and config and (regkey in config):
        #     regkey = config["regkey"]
        # if regkey:
        print(f"get_reg: {reg_id}")
        try:
            # reg = DAQRegistration.objects.get(reg_id2=reg_id2, daq_type=type)
            reg = DAQRegistration.objects.get(reg_id=reg_id, daq_type=type)
            # reg.status = "CONNECTED"
            # srv = ServiceRegistration.objects.get(regkey=config["regkey"])
            # reg.save(do_update=True)  # update modified time stamp
            return reg.get_registration()
        except DAQRegistration.DoesNotExist:
            pass

        return None

    # def ping(local=True, regkey=None, config=None):
    # @staticmethod
    # async def ping(
    #     reg_id="default", reg_id2=Namespace().get_namespace_sig(), type="DAQServer"
    # ):
    #     await DAQRegistry.ping_no_wait(reg_id, type)
    @staticmethod
    async def ping(
        reg_id=Namespace().get_namespace_sig(), type=Namespace.DAQSERVER
    ):
        await DAQRegistry.ping_no_wait(reg_id, type)

    # @staticmethod
    # @database_sync_to_async
    # def ping_no_wait(
    #     reg_id="default", reg_id2=Namespace().get_namespace_sig(), type="DAQServer"
    # ):
    @staticmethod
    @database_sync_to_async
    def ping_no_wait(
        reg_id=Namespace().get_namespace_sig(), type=Namespace.DAQSERVER
    ):
        # theoretically, we should not be pinging local here
        # if not regkey and config and (regkey in config):
        #     regkey = config["regkey"]
        # if regkey:
        try:
            # print(f"ping server reg: {reg_id}")
            # reg = DAQRegistration.objects.get(reg_id2=reg_id2, daq_type=type)
            reg = DAQRegistration.objects.get(reg_id=reg_id, daq_type=type)
            reg.status = "CONNECTED"
            status2 = Status().from_dict(reg.status2)
            status2.set_connection_status(Status.CONNECTED)
            reg.status2 = status2.to_dict()

            # srv = ServiceRegistration.objects.get(regkey=config["regkey"])
            reg.save(do_update=True)  # update modified time stamp
            # print(f"ping success")

        except DAQRegistration.DoesNotExist:
            pass

    @staticmethod
    async def get_registry(type=Namespace.DAQSERVER):
        return await DAQRegistry.get_registry_no_wait(type=type)

    @staticmethod
    @database_sync_to_async
    def get_registry_no_wait(type=Namespace.DAQSERVER):

        try:
            regs = DAQRegistration.objects.filter(daq_type=type)
            # print(f"regs: {regs}")

        except DAQRegistration.DoesNotexist:
            # TODO: return 404 ... lookup how
            pass
            regs = []

        daq_registration_map = {}
        if regs:
            for reg in regs:
                # id2 = reg.reg_id2
                print(f"reg: {reg}")
                daq_registration_map[f"{reg}"] = reg.get_registration()

        return daq_registration_map

    @staticmethod
    async def check_status():
        # print(tmp)
        print("check_status")
        while True:
            await DAQRegistry.clean_registrations()
            # regs = await database_sync_to_async(ServiceRegistration.objects.filter(
            #     network=ServiceRegistry.local_network
            # ))
            # regs = await ServiceRegistry.get_all_registrations()
            # print(regs)
            # for reg in regs:
            #     print(f'check status: {reg.name}')
            #     if reg.get_age() > ServiceRegistry.auto_clean_limit:
            #         print(f"removing registration for {reg.name} due to auto timeout")
            #         reg.delete()
            #     elif reg.get_() > ServiceRegistry.disconnected_service_limit:
            #         reg.status = "DISCONNECTED"
            # print("tick")
            await asyncio.sleep(2)

    @staticmethod
    @database_sync_to_async
    def clean_registrations():
        # regs = database_sync_to_async(ServiceRegistration.objects.filter)(
        #     network=ServiceRegistry.local_network
        # )
        # regs = DAQRegistration.objects.filter(
        #     local_service=False, network=ServiceRegistry.local_network
        # )
        regs = DAQRegistration.objects.all()
        # regs = None
        print(f"cleaning regs: {regs}")
        # return regs
        for reg in regs:
            print(f"status: {reg}, age: {reg.get_age()}")
            # print(f"check status: {reg}")
            if reg.get_age() > DAQRegistry.auto_clean_limit:
                print(f"removing registration for {reg} due to auto timeout")
                reg.delete()
            elif reg.get_age() > DAQRegistry.disconnected_limit:
                reg.status = "DISCONNECTED"
                status2 = Status().from_dict(reg.status2)
                status2.set_connection_status(Status.NOT_CONNECTED)
                print(reg.status)
                reg.save()
