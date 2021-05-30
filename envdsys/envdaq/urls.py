from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("daqserver/<daq_host>/<daq_namespace>/", views.daqserver, name="daqserver"),
    # this needs to have a parameter for controller name
    # path('controller/', views.controller, name='controller'),
    path(
        # '<daq_namespace>/controller/<controller_namespace>/',
        "<daq_host>/<parent_namespace>/controller/<controller_namespace>/",
        views.daq_controller,
        name="daq_controller",
    ),
    # path('<daq_namespace>/<controller_namespace>/instrument/<instrument_namespace>/', views.instrument, name='instrument'),
    path(
        # '<parent_namespace>/instrument/<instrument_namespace>/', views.instrument, name='instrument'
        "<daq_host>/<parent_namespace>/instrument/<instrument_namespace>/",
        views.daq_instrument,
        name="daq_instrument",
    ),
    # path('interface/<interface_name>/', views.interface, name='interface'),
    # path('ifdevice/<ifdevice_name>/', views.ifdevice, name='ifdevice'),
]

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]
