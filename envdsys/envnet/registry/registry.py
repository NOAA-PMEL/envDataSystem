from abc import abstractmethod
import asyncio

from django.core.exceptions import MultipleObjectsReturned
from envnet.models import Network, ServiceRegistration, DAQRegistration


class ServiceRegistry:

    # number of seconds before daq_server is considered
    #   disconnected
    disconnected_limit = 10

    # number of seconds before daq_server is removed
    #   from registry
    auto_clean_limit = 600  # 10 minutes

    def start():
        pass
        # start broadcasting
        # start housekeeping checks

    # recieve from other servers
    #   add list of remote services

    @abstractmethod
    def register(local=True, config=None):
        if config:
            print(config["host"])
            try:
                # print(f'{config["HOST"]}, {config["PORT"]}')
                srv = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                if (
                    srv.get_age()
                    > ServiceRegistry.auto_clean_limit
                    # or "regkey" not in config
                    # or not config["regkey"]
                    # or config["regkey"] != srv.regkey
                ):
                    srv.delete()
                else:
                    registration = ServiceRegistry.update_registration(local, config)
                    return registration
            except ServiceRegistration.MultipleObjectsReturned:
                result = ServiceRegistration.objects.filter(
                    host=config["host"], port=config["port"]
                )
                for s in result:
                    s.delete()
            except ServiceRegistration.DoesNotExist:
                pass

            # create new Reg
            srv = ServiceRegistration(
                local_service=local,
                host=config["host"],
                port=config["port"],
                # service_list = config.service_list
            )
            srv.save()
            srv.add_services(config["service_list"])
            # srv.save()
            registration = srv.get_registration()
            return registration

    def update_registration(local=True, config=None):
        if config:
            try:
                # srv = ServiceRegistration.objects.get(regkey=config["regkey"])
                srv = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                if srv.get_age() > ServiceRegistry.auto_clean_limit:
                    srv.delete()
                elif srv.regkey in config and config["regkey"] != srv.regkey:
                    srv.delete()
                else:
                    srv.local_service = local
                    srv.host = config["host"]
                    srv.port = config["port"]
                    # srv.service_list = config.service_list
                    # srv.save()
                    srv.add_services(config["service_list"])
                    srv.save()
                    registration = srv.get_registration
                    return registration
            except ServiceRegistration.DoesNotExist:
                pass

            # create new Reg here don't want to pass back to add ang get caught in loop?
            srv = ServiceRegistration(
                local_service=local,
                host=config["host"],
                port=config["port"],
                # service_list = config.service_list
            )
            srv.add_services(config["service_list"])
            srv.save()
            registration = srv.get_registration()
            return registration

    def unregister(local=True, config=None):
        if config:
            try:
                srv = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                srv.delete()
            except ServiceRegistration.DoesNotExist:
                pass

    # def ping(local=True, regkey=None, config=None):
    def ping(local=True, config=None):
        # theoretically, we should not be pinging local here
        # if not regkey and config and (regkey in config):
        #     regkey = config["regkey"]
        # if regkey:
        if config:
            try:
                srv = ServiceRegistration.objects.get(
                    host=config["host"], port=config["port"]
                )
                # srv = ServiceRegistration.objects.get(regkey=config["regkey"])
                srv.save()  # update modified time stamp

            except ServiceRegistration.DoesNotExist:
                pass
