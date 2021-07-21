from django.db.models.signals import post_save
from django.dispatch import receiver

from envdatasystem.models import (
    SamplingSystem,
    SamplingSystemController,
    SamplingSystemInstrument,
    SamplingSystemLocation,
    SamplingSystemSamplePoint,
    SamplingSystemDataset,
)

@receiver(post_save, sender=SamplingSystem)
def sync_sampling_system_version(sender, instance, **kwargs):
    print(f"{sender}, {instance}")
    try:
        controllers = SamplingSystemController.objects.filter(sampling_system__name=instance.name)
        for cont in controllers:
            cont.sync_sampling_system()
    except SamplingSystemController.DoesNotExist:
        pass

    try:
        instruments = SamplingSystemInstrument.objects.filter(sampling_system__name=instance.name)
        for inst in instruments:
            print(f"inst: {inst}")
            inst.sync_sampling_system()
    except SamplingSystemInstrument.DoesNotExist:
        pass

    try:
        locations = SamplingSystemLocation.objects.filter(sampling_system__name=instance.name)
        for loc in locations:
            loc.sync_sampling_system()
    except SamplingSystemLocation.DoesNotExist:
        pass

    try:
        points = SamplingSystemSamplePoint.objects.filter(sampling_system__name=instance.name)
        for point in points:
            point.sync_sampling_system()
    except SamplingSystemSamplePoint.DoesNotExist:
        pass

    try:
        datasets = SamplingSystemDataset.objects.filter(sampling_system__name=instance.name)
        for ds in datasets:
            ds.sync_sampling_system()
    except SamplingSystemDataset.DoesNotExist:
        pass

# TODO fix this to allow multiple current datasets for a given platform event
@receiver(post_save, sender=SamplingSystemDataset)
def sync_current_dataset(sender, instance, **kwargs):
    # if instance is current it is the "new" current
    if instance.current:
        project = instance.project
        platform = instance.platform_event.get_platform()
        ss = instance.sampling_system

        try:
            # datasets = sender.objects.filter(project=project, platform_event__platform = platform).exclude(pk=instance.pk)
            datasets = sender.objects.filter(project=project).exclude(pk=instance.pk)
            for ds in datasets:
                # print(f"ds: {ds}")
                ds.current = False
                ds.save(update_version=False)
        except sender.DoesNotExist:
            pass
