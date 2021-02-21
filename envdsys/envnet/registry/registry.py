from abc import abstractmethod
import asyncio
from typing import AsyncIterable

# from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async

from django.core.exceptions import MultipleObjectsReturned
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
        print("starting registry")
        try:
            net = Network.objects.get(name=network)
            net.activate()
        except Network.MultipleObjectsReturned:
            result = Network.objects.filter(name=network)
            for s in result:
                s.delete()
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
                if (
                    reg.get_age()
                    > ServiceRegistry.auto_clean_limit
                    # or "regkey" not in config
                    # or not config["regkey"]
                    # or config["regkey"] != srv.regkey
                ):
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
            print(f"2:{registration}")
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
                    reg.save()
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
            reg.save()
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
                reg.save()  # update modified time stamp

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
        regs = ServiceRegistration.objects.filter(network=ServiceRegistry.local_network)
        # regs = None
        # print(regs)
        # return regs
        for reg in regs:
            print(f"status: {reg}, age: {reg.get_age()}")
            # print(f"check status: {reg}")
            if reg.get_age() > ServiceRegistry.auto_clean_limit:
                print(f"removing registration for {reg} due to auto timeout")
                reg.delete()
            elif reg.get_age() > ServiceRegistry.disconnected_service_limit:
                reg.status = "DISCONNECTED"
                print(reg.status)
                # reg.save()

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
            print("tick")
            await asyncio.sleep(2)