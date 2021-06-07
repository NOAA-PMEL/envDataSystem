from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path('ws/net/serviceregistry', consumers.ServiceRegistryConsumer.as_asgi()),
    path('ws/net/daqregistry', consumers.DAQRegistryConsumer.as_asgi()),
    # path('ws/envdaq/data_test/', consumers.DataConsumer),
]

channel_urlpatterns = {
    'envnet-manage': consumers.ManagementConsumer.as_asgi(),
}
