"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
import django

# from django.conf.urls import url
# from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# django.setup()
django_asgi_app = get_asgi_application()

# from channels.routing import get_default_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter

# from django.core.asgi import get_asgi_application
import envdaq.routing
import envnet.routing

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "envdsys.settings")
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# django.setup()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            [
                URLRouter(envdaq.routing.websocket_urlpatterns),
                URLRouter(envnet.routing.websocket_urlpatterns),
            ]
        ),
        "channel": (
            ChannelNameRouter({
                **envnet.routing.channel_urlpatterns,
                **envdaq.routing.channel_urlpatterns,
            })
        )
        # "channel": ChannelNameRouter(
        #     {"test-manage": envnet.consumers.ManagementConsumer.as_asgi()}
        # ),
    }
)


# application = get_default_application()