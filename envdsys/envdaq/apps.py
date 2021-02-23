from django.apps import AppConfig
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import os

class EnvdaqConfig(AppConfig):
    name = "envdaq"

    def ready(self) -> None:
        run_main = None
        try:
            print(f"RUN_MAIN: {os.environ.get('RUN_MAIN')}")
            run_main = os.environ.get('RUN_MAIN')
        except:
            pass
        if run_main:
            print("init envdaq")
            channel_layer = get_channel_layer()
            print(channel_layer)
            res = async_to_sync(channel_layer.send)(
                "envdaq-manage", {"type": "manage", "command": "REGISTER_SERVICE"}
            )
            res = async_to_sync(channel_layer.send)(
                "envdaq-manage", {"type": "manage", "command": "INIT_ENVDAQ"}
            )
            # print(res)
            print("sent init envdaq")
        return super().ready()

    # def ready(self) -> None:
    #     from envnet.registry.registry import ServiceRegistry
    #     try:
    #         from setup.ui_server_conf import run_config
    #         host = run_config["HOST"]["name"]
    #     except KeyError:
    #         host = "localhost"

    #     try:
    #         from setup.ui_server_conf import run_config
    #         port = run_config["HOST"]["port"]
    #     except KeyError:
    #         port = "8000"

    #     local = True
    #     config = {
    #         "host": host,
    #         "port": port,
    #         "regkey": None,
    #         "service_list": {"envdsys_ui_server": {}},
    #     }
    #     registration = ServiceRegistry.register(local, config)
    #     # print(registration)
    #     return super().ready()