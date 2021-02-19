from django.apps import AppConfig


class EnvnetConfig(AppConfig):
    name = 'envnet'

    def ready(self) -> None:
        from envnet.registry.registry import ServiceRegistry 
        ServiceRegistry.start()
        
        return super().ready()