from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # this needs to have a parameter for controller name
    path('controller/', views.controller, name='controller'),
]

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]
