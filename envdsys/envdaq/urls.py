from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('daqserver/<daq_id>', views.daqserver, name='daqserver'),
    # this needs to have a parameter for controller name
    # path('controller/', views.controller, name='controller'),
    path(
        'controller/<controller_alias_name>/',
        views.controller, name='controller'
    ),
    path('instrument/<instrument_name>/', views.instrument, name='instrument'),
    # path('interface/<interface_name>/', views.interface, name='interface'),
    # path('ifdevice/<ifdevice_name>/', views.ifdevice, name='ifdevice'),
]

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]
