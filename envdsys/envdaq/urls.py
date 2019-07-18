from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('server/', views.server, name='server'),
    # this needs to have a parameter for controller name
    # path('controller/', views.controller, name='controller'),
    path('controller/<controller_name>/', views.controller, name='controller'),
]

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]
