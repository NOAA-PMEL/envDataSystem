from django.contrib import admin

from envdatasystem.models import (
    # ControllerComponent,
    # ControllerComponentController,
    # ControllerComponentInstrument,
    # ControllerSystem,
    # DAQSystem,
    DataSystem,
    # InstrumentComponent,
    # InstrumentComponentInterface,
    # InstrumentSystem,
    Platform, # PlatformLocation,
    Project,
    # SSMInstrumentMap,
    # SSMPlatformLocationMap,
    SamplingSystem,
    SamplingSystemLocation,
    SamplingSystemController,
    SamplingSystemInstrument,
    # SamplingSystemMap,
    SamplingSystemSamplePoint,
    ProjectEvent,
    PlatformEvent,
    SamplePeriod,
    SamplingSystemDataset,
    SSDatasetEvent
)


# Register your models here.

admin.site.register(Project)
admin.site.register(Platform)
# admin.site.register(PlatformLocation)
admin.site.register(DataSystem)
admin.site.register(SamplingSystem)
admin.site.register(SamplingSystemLocation)
admin.site.register(SamplingSystemSamplePoint)
admin.site.register(SamplingSystemController)
admin.site.register(SamplingSystemInstrument)
# admin.site.register(DAQSystem)
# admin.site.register(ControllerSystem)
# admin.site.register(ControllerComponent)
# admin.site.register(ControllerComponentController)
# admin.site.register(ControllerComponentInstrument)
# admin.site.register(InstrumentSystem)
# admin.site.register(InstrumentComponent)
# admin.site.register(InstrumentComponentInterface)
# admin.site.register(SamplingSystemMap)
# admin.site.register(SSMPlatformLocationMap)
# admin.site.register(SSMInstrumentMap)
admin.site.register(ProjectEvent)
admin.site.register(PlatformEvent)
admin.site.register(SamplePeriod)
admin.site.register(SamplingSystemDataset)
admin.site.register(SSDatasetEvent)
