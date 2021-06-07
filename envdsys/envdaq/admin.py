from django.contrib import admin

# Register your models here.
# from envdaq.models import ControllerComponent, ControllerDef, Controller, DAQController, DAQInstrument, DAQServerConfig, InstrumentComponent, Interface, InterfaceComponent, InterfaceDef
from envdaq.models import ControllerDef, Controller, DAQController, DAQInstrument, DAQServerConfig, Interface, InterfaceComponent, InterfaceDef
from envdaq.models import InstrumentAlias, Measurement
from envdaq.models import DAQServer  #, Configuration
# from envdaq.models import InstrumentMask, Measurement


admin.site.register(DAQController)
admin.site.register(DAQInstrument)
# admin.site.register(ControllerComponent)
# admin.site.register(InstrumentComponent)
admin.site.register(ControllerDef)
admin.site.register(Controller)
admin.site.register(InterfaceDef)
admin.site.register(Interface)
admin.site.register(InterfaceComponent)
admin.site.register(InstrumentAlias)
admin.site.register(Measurement)
# admin.site.register(Configuration)

class DAQServerAdmin(admin.ModelAdmin):
    readonly_fields = ('uniqueID',)

admin.site.register(DAQServer, DAQServerAdmin)
admin.site.register(DAQServerConfig)
