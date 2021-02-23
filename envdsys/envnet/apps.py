from django.apps import AppConfig
from setup.ui_server_conf import run_config
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import os

class EnvnetConfig(AppConfig):
    name = 'envnet'

    def ready(self) -> None:
        run_main = None
        try:
            print(f"RUN_MAIN: {os.environ.get('RUN_MAIN')}")
            run_main = os.environ.get('RUN_MAIN')
        except:
            pass
        if run_main:
            print("init envnet")
            channel_layer = get_channel_layer()
            print(channel_layer)
            res = async_to_sync(channel_layer.send) (
                "envnet-manage",
                {
                    "type": "manage",
                    "command": "INIT_ENVNET"
                }
            )
            res = async_to_sync(channel_layer.send) (
                "envnet-manage",
                {
                    "type": "manage",
                    "command": "REGISTER_SERVICE"
                }
            )
            # print(res)
            print("sent init envnet")
        return super().ready()

    # def ready(self) -> None:
    #     try:
    #         network = run_config["HOST"]["network"]
    #     except KeyError:
    #         network = None

    #     from envnet.registry.registry import ServiceRegistry 
    #     ServiceRegistry.start(network=network)

    #     return super().ready()