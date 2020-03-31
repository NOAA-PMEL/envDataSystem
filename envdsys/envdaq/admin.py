from django.contrib import admin

# Register your models here.
from envdaq.models import ControllerDef, Controller
from envdaq.models import InstrumentAlias, Measurement
from envdaq.models import DAQServer  #, Configuration
# from envdaq.models import InstrumentMask, Measurement


admin.site.register(ControllerDef)
admin.site.register(Controller)
admin.site.register(InstrumentAlias)
admin.site.register(Measurement)
# admin.site.register(Configuration)

class DAQServerAdmin(admin.ModelAdmin):
    readonly_fields = ('uniqueID',)

admin.site.register(DAQServer, DAQServerAdmin)
