from django.apps import AppConfig

class EnvdatasystemConfig(AppConfig):
    name = 'envdatasystem'

    def ready(self):
        import envdatasystem.signals