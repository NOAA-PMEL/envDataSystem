from django.apps import AppConfig


class EnvdaqConfig(AppConfig):
    name = 'envdaq'

    def ready(self) -> None:
        from envnet.registry.registry import ServiceRegistry 
        try:
            from setup.ui_server_conf import run_config
            host = run_config["HOST"]["name"]
        except KeyError:
            host = "localhost"
        
        try:
            from setup.ui_server_conf import run_config
            port = run_config["HOST"]["port"]
        except KeyError:
            port = "8000"

        local = True
        config = {
            "host": host,
            "port": port,
            "regkey": None,
            "service_list": {"envdsys_ui_server": {}},
        }
        registration = ServiceRegistry.register(local, config)
        print(registration)
        return super().ready()