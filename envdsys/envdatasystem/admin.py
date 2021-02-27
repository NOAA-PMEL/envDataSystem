from django.contrib import admin

from envdatasystem.models import (
    DataSystem,
    Platform,
    Project,
    SamplingSystem,
    SamplingSystemLocation,
    SamplingSystemSamplePoint,
)


# Register your models here.

admin.site.register(Project)
admin.site.register(Platform)
admin.site.register(DataSystem)
admin.site.register(SamplingSystem)
admin.site.register(SamplingSystemLocation)
admin.site.register(SamplingSystemSamplePoint)
