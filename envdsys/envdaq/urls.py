from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
]

# urlpatterns = [
#     url(r'^$', views.index, name='index'),
# ]
