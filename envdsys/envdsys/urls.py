"""envdsys URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('envdaq/', include('envdaq.urls')),
    path('envtags/', include('envtags.urls')),
    path('admin/', admin.site.urls),
    path('envdsys/', include('django.contrib.auth.urls')),
    # path("", TemplateView.as_view(template_name='index.html'),name='index'),
    # eventually, this will be in its own "app" 
    # path('', include('envdaq.urls'))
]
