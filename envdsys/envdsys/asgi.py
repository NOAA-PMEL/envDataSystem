
"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
import django
# from channels.routing import get_default_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import envdaq.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "envdsys.settings")
# django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            envdaq.routing.websocket_urlpatterns
        )
    ),
   
})


# application = get_default_application()