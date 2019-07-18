# chat/routing.py
from django.conf.urls import url
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
    path('ws/envdaq/daq/', consumers.DAQConsumer),
    path('ws/envdaq/data_test/', consumers.DataConsumer),
    path(
        'ws/envdaq/controller/<controller_name>/',
        consumers.ControllerConsumer
        ),
]
