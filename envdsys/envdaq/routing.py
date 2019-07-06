# chat/routing.py
from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/envdaq/data_test/$', consumers.DataConsumer),
]
