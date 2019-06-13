from django.contrib import admin

# Register your models here.
from envinventory.models import InstrumentDef, Instrument
# from envdaq.models import InstrumentMask, Measurement


admin.site.register(InstrumentDef)
admin.site.register(Instrument)
