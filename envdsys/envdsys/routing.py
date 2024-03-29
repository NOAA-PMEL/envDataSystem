# envdsys/routing.py
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import envdaq.routing
# import envnet.routing

application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        "websocket": AuthMiddlewareStack(
            URLRouter(envdaq.routing.websocket_urlpatterns)
            # URLRouter(envnet.routing.websocket_urlpatterns)
        ),
    }
)
