# chat/routing.py
# from django.conf.urls import url
from django.urls import path
from . import consumers

# websocket_urlpatterns = [
#     url(r'^ws/envdaq/server/$', consumers.ServerConsumer),
#     url(r'^ws/envdaq/data_test/$', consumers.DataConsumer),
#     url(
#         r'^ws/envdaq/controller/(?P<controller_name>[^/]+)/$', 
#         consumers.ControllerConsumer
#         ),
# ]

websocket_urlpatterns = [
    path('ws/envdaq/daqserver/<daq_namespace>', consumers.DAQServerConsumer.as_asgi()),
    # path('ws/envdaq/data_test/', consumers.DataConsumer),
    path(
        'ws/envdaq/<daq_namespace>/controller/<controller_namespace>/',
        consumers.ControllerConsumer.as_asgi()
        ),
    path(
        'ws/envdaq/<daq_namespace>/<controller_namespace>/instrument/<instrument_namespace>/',
        consumers.InstrumentConsumer.as_asgi()
        ),
    path(
        'ws/envdaq/interface/<interface_name>/',
        consumers.InterfaceConsumer.as_asgi()
        ),
    path(
        'ws/envdaq/ifdevice/<ifdevice_name>/',
        consumers.IFDeviceConsumer.as_asgi()
        ),
    
]
