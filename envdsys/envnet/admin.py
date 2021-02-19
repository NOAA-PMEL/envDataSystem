from django.contrib import admin

# Register your models here.

from envnet.models import DAQRegistration, Network, ServiceRegistration

admin.site.register(Network)
admin.site.register(ServiceRegistration)
admin.site.register(DAQRegistration)
