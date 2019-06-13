from django.contrib import admin

# Register your models here.
from envdaq.models import ControllerDef, Controller
from envdaq.models import InstrumentMask, Measurement
# from envdaq.models import InstrumentMask, Measurement


admin.site.register(ControllerDef)
admin.site.register(Controller)
admin.site.register(InstrumentMask)
admin.site.register(Measurement)
