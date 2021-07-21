from django.db import models
from django.db.models.base import Model
from django.db.models.query_utils import Q

# from django.db.models.signals import post_save
# from django.dispatch import receiver
from django.db.models.fields import DateTimeField, IPAddressField, UUIDField
from django.db.models.fields.related import ForeignKey
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils import timezone
import uuid

from envtags.models import Tag
from shared.utilities.util import string_to_dt, dt_to_string

# Create your models here.


class DataSystem(models.Model):
    """
    Top level container for all things data for a logical group (e.g., a research group)
    """

    name = models.CharField(_("Name"), max_length=50, default="default")

    name_id = models.CharField(
        _("Name ID"),
        max_length=20,
        blank=True,
        null=True,
        help_text="Shortened version of name for use in id strings",
    )

    description = models.TextField(_("Description"), blank=True, null=True)

    projects = models.ManyToManyField(
        "envdatasystem.Project", verbose_name=_("Project List"), blank=True
    )

    # project = models.ForeignKey(
    #     "envdatasystem.Project",
    #     verbose_name=_("Project"),
    #     on_delete=models.CASCADE,
    #     related_name="datasystems_project",
    #     blank=True,
    #     null=True
    # )
    # platform = models.ForeignKey(
    #     "envdatasystem.Platform",
    #     verbose_name=_("Platform"),
    #     on_delete=models.CASCADE,
    #     related_name="datasystems_platform",
    #     blank=True,
    #     null=True
    # )

    # sampling_system = models.ManyToManyField(
    #     "envdatasystem.SamplingSystemMap", verbose_name=_("Sampling System"), blank=True
    # )
    # sampling_system
    # platform =

    class Meta:
        verbose_name = _("Data System")
        verbose_name_plural = _("Data Systems")

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("DataSystem_detail", kwargs={"pk": self.pk})


class Project(models.Model):

    name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)
    acronymn = models.CharField(max_length=50, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    website = models.URLField(verbose_name="Project Website", blank=True, null=True)

    logo = models.ImageField(
        verbose_name="Logo Image", upload_to="projects/", blank=True, null=True
    )

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")

    def get_platforms(self):
        platforms = []
        events = PlatformEvent.objects.select_related("platform").filter(project=self)
        for e in events:
            if e.platform and e.platform not in platforms:
                platforms.append(e.platform)
                
        return platforms

    # def get_sampling_systems(self):
    #     systems = []
    #     events = PlatformEvent.objects.select_related("sampling_system").filter(project=self)
    #     for e in events:
    #         if e.sampling_system and e.sampling_system not in systems:
    #             systems.append(e.sampling_system)
                
    #     return systems

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_detail", kwargs={"pk": self.pk})


class Platform(models.Model):

    name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    platform_id = models.CharField(
        verbose_name="Identifier", max_length=20, default="default_id"
    )

    STATION = "STATION"
    SHIP = "SHIP"
    AIRCRAFT = "AIRCRAFT"
    UAS = "UAS"
    MOORING = "MOORING"

    PLATFORM_TYPE_CHOICES = {
        (STATION, "Station/Lab"),
        (SHIP, "Ship"),
        (AIRCRAFT, "Aircraft"),
        (UAS, "UAS"),
        (MOORING, "Mooring"),
    }
    platform_type = models.CharField(
        _("Platform Type"),
        max_length=10,
        choices=PLATFORM_TYPE_CHOICES,
        default=STATION,
    )

    parent_platform = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="platforms",
    )

    website = models.URLField(verbose_name="Platform Website", blank=True, null=True)

    # logo = models.ImageField(
    #     verbose_name='Logo Image',
    #     upload_to='projects/',
    #     blank=True,
    #     null=True
    # )

    # uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    class Meta:
        # verbose_name = 'DAQ Server
        verbose_name = "Platform"
        verbose_name_plural = "Platforms"

    # tags = models.ManyToManyField(
    #     Tag,
    #     blank=True,
    #     related_name="platform_tags",
    # )

    def get_projects(self):
        projects = []
        events = PlatformEvent.objects.select_related("project").filter(platform=self)
        for e in events:
            if e.project and e.project not in projects:
                projects.append(e.project)
                
        return projects

    # def get_sampling_systems(self):
    #     systems = []
    #     events = PlatformEvent.objects.select_related("sampling_system").filter(platform=self)
    #     for e in events:
    #         if e.sampling_system and e.sampling_system not in systems:
    #             systems.append(e.sampling_system)
                
    #     return systems

    def __str__(self):
        """String representation of Platform object."""
        return self.name

    def __repr__(self):
        return f"{self.name} ({self.platform_id})"


class PlatformLocation(models.Model):

    platform = models.ForeignKey(
        "envdatasystem.Platform",
        verbose_name=_("Platform"),
        on_delete=models.CASCADE,
        related_name="platformlocations",
    )

    name = models.CharField(_("Name"), max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    parent = models.ForeignKey(
        # "envdatasystem.SamplingSystemLocation",
        "self",
        verbose_name=_("Parent Location"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="platformlocations_parent",
    )

    class Meta:
        verbose_name = _("Platform Location")
        verbose_name_plural = _("Platform Locations")

    def __str__(self):
        name = f"{self.platform}-{self.name}"
        if self.parent:
            name = f"{self.parent}:{name}"
        return name

    def get_absolute_url(self):
        return reverse("platformlocation_detail", kwargs={"pk": self.pk})


class VersionManager(models.Manager):
    def get_latest(self, **kwargs):
        return super().get_queryset().filter(**kwargs).order_by("-version_starttime")[0]

    def get_version(self, **kwargs):
        # print(f"dt: {dt}")
        try:
            dt_string = kwargs.pop("dt_string")
            # print(f"dt_string = {dt_string}")
            dt = string_to_dt(dt_string)
            # print(f"dt = {dt}")
            # return self.get_version(**kwargs)
            return (
                super()
                .get_queryset()
                .filter(version_starttime__lte=dt, version_stoptime__gt=dt, **kwargs)[0]
            )
        except KeyError:
            pass

        try:
            dt = kwargs.pop("dt")
            # print(f"dt = {dt}")
            return (
                super()
                .get_queryset()
                .filter(version_starttime__lte=dt, version_stoptime__gt=dt, **kwargs)[0]
            )
        except KeyError:
            pass

        return None


class SamplingSystem(models.Model):

    data_system = models.ForeignKey(
        "envdatasystem.DataSystem",
        verbose_name=_("Data System"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    name = models.CharField(_("Name"), max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    version_starttime = models.DateTimeField(
        _("Valid Start Time"), auto_now=False, auto_now_add=False, blank=True, null=True
    )
    version_stoptime = models.DateTimeField(
        _("Valid Start Time"), auto_now=False, auto_now_add=False, blank=True, null=True
    )
    objects = VersionManager()
    # locations = models.ManyToManyField(
    #     "envdatasystem.SamplingSystemLocation",
    #     verbose_name=_("sampling Locations"),
    #     blank=True,
    #     related_name="samplingsystems",
    # )
    # sample_points = models.ManyToManyField(
    #     "envdatasystem.SamplingSystemSamplePoint",
    #     verbose_name=_("Sampling Points"),
    #     blank=True,
    #     related_name="samplingsystems",
    # )

    class Meta:
        verbose_name = _("Sampling System")
        verbose_name_plural = _("Sampling Systems")

    def save(self, update_version=True, *args, **kwargs):
        ts = timezone.now()

        # saved = None
        if update_version:
            # orig = SamplingSystem.version.get_latest(self.name)
            try:
                orig = SamplingSystem.objects.get(pk=self.pk)
                orig.version_stoptime = ts
                orig.save(update_version=False)
            except SamplingSystem.DoesNotExist:
                pass

            self.pk = None
            self.version_starttime = timezone.now()
            # saved = super(SamplingSystem, self).save(*args, **kwargs)

            # # save all contollers and instruments to force latest
            # try:
            #     controllers = SamplingSystemController.objects.filter(sampling_system__name=self.name)
            #     for cont in controllers:
            #         cont.save()
            # except SamplingSystemController.DoesNotExist:
            #     pass

            # try:
            #     instruments = SamplingSystemInstrument.objects.filter(sampling_system__name=self.name)
            #     # print(f"instruments: {instruments}")
            #     for inst in instruments:
            #         inst.save()
            # except SamplingSystemInstrument.DoesNotExist:
            #     pass

            # try:
            #     datasets = SamplingSystemDataset.objects.filter(sampling_system__name=self.name)
            #     # print(f"instruments: {instruments}")
            #     for ds in datasets:
            #         ds.sync_sampling_system()
            # except SamplingSystemInstrument.DoesNotExist:
            #     pass

        return super(SamplingSystem, self).save(*args, **kwargs)

    def get_latest(self):
        return SamplingSystem.objects.get_latest(name=self.name)

    # def get_version_dt_string(self, dt_string):
    #     return SamplingSystem.objects.get_version_dtstring(self.name, dt_string)

    def get_version(self, dt=None, dt_string=None):
        if dt:
            return SamplingSystem.objects.get_version(name=self.name, dt=dt)
        elif dt_string:
            return SamplingSystem.objects.get_version(
                name=self.name, dt_string=dt_string
            )
        else:
            return None

    def get_projects(self):
        projects = []
        dsets = SamplingSystemDataset.objects.select_related("platform_event").filter(sampling_system=self)
        for ds in dsets:
            proj = ds.get_project()
            if proj and proj not in projects:
                projects.append(proj)
                
        return projects

    def get_platforms(self):
        platforms = []
        dsets = SamplingSystemDataset.objects.select_related("platform_event").filter(sampling_system=self)
        for ds in dsets:
            plat = ds.get_platform()
            if plat and plat not in platforms:
                platforms.append(plat)
                
        return platforms

    # basing this on event being current but relies on user maintaining start/stop times. if multiple, will
    #   return dataset based on most recent start_time of event
    def get_active_dataset(self):
        active = None
        dsets = SamplingSystemDataset.objects.select_related("platform_event").filter(sampling_system=self)
        for ds in dsets:
            if ds.platform_event.active():
                print(timezone.is_aware(ds.platform_event.start_datetime))
                if active and ds.platform_event.start_datetime > active.platform_event.start_datetime:
                    active = ds
                else:
                    active= ds
        return active

        # try:
        #     return SamplingSystemDataset.objects.get(sampling_system=self, current=True)
        # except SamplingSystem.DoesNotExist:
        #     return None
        # except SamplingSystem.MultipleObjectsReturned:
        #     ss = SamplingSystemDataset.objects.filter(sampling_system=self, current=True)[0]
        #     ss.sync_current()
        #     return self.get_current_dataset()

    def __str__(self):
        if self.version_stoptime:
            # start = self.version_starttime.strftime("%Y-%m-%dT%H:%M:%S")
            start = dt_to_string(self.version_starttime)
            # stop = self.version_stoptime.strftime("%Y-%m-%dT%H:%M:%S")
            stop = dt_to_string(self.version_stoptime)
            return f"{self.name}-{start}-{stop}"
        else:
            return self.name

    def get_absolute_url(self):
        return reverse("samplingsystem_detail", kwargs={"pk": self.pk})


class SamplingSystemLocation(models.Model):

    sampling_system = models.ForeignKey(
        "envdatasystem.SamplingSystem",
        verbose_name=_("Sampling System"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sslocations_samplingsystem",
    )

    name = models.CharField(_("Name"), max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    parent = models.ForeignKey(
        # "envdatasystem.SamplingSystemLocation",
        "self",
        verbose_name=_("Parent Location"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sslocations_parent",
    )

    class Meta:
        verbose_name = _("SS Sampling Location")
        verbose_name_plural = _("SS Sampling Locations")
        constraints = [
            models.CheckConstraint(
                check=(Q(sampling_system__isnull=False) & Q(parent__isnull=True))
                | (Q(sampling_system__isnull=True) & Q(parent__isnull=False)),
                name="oaoo_sampling_system_location",
            )
        ]

    def save(self, use_latest=True, *args, **kwargs):

        if use_latest:
            self.sampling_system = self.sampling_system.get_latest()

        return super(SamplingSystemLocation, self).save(*args, **kwargs)

    def sync_sampling_system(self):
        self.save()

    def __str__(self):
        name = f"{self.sampling_system}:{self.name}"
        if self.parent:
            name = f"{self.parent}-{self.name}"

        return name

    def get_absolute_url(self):
        return reverse("SamplingSystemLocation_detail", kwargs={"pk": self.pk})


class SamplingSystemSamplePoint(models.Model):

    sampling_system = models.ForeignKey(
        "envdatasystem.SamplingSystem",
        verbose_name=_("Sample System"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sssamplepoints_samplingsystem",
    )

    name = models.CharField(_("Name"), max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    parent = models.ForeignKey(
        # "envdatasystem.SamplingSystemSamplePoint",
        "self",
        verbose_name=_("Parent Sampling Point"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="samplepoint_parents",
    )

    class Meta:
        verbose_name = _("SS Sampling Point")
        verbose_name_plural = _("SS Sampling Points")
        constraints = [
            models.CheckConstraint(
                check=(Q(sampling_system__isnull=False) & Q(parent__isnull=True))
                | (Q(sampling_system__isnull=True) & Q(parent__isnull=False)),
                name="oaoo_sampling_system_sample_point",
            )
        ]

    def save(self, use_latest=True, *args, **kwargs):

        if self.sampling_system and use_latest:
            self.sampling_system = self.sampling_system.get_latest()

        return super(SamplingSystemSamplePoint, self).save(*args, **kwargs)

    def sync_sampling_system(self):
        self.save()

    def __str__(self):
        name = f"{self.sampling_system}:{self.name}"
        if self.parent:
            name = f"{self.parent}-{self.name}"
        return name

    def get_absolute_url(self):
        return reverse("SamplingSystemSamplePoint_detail", kwargs={"pk": self.pk})


class SamplingSystemController(models.Model):

    sampling_system = models.ForeignKey(
        "envdatasystem.SamplingSystem",
        verbose_name=_("Sampling System"),
        on_delete=models.CASCADE,
    )
    controller = models.ForeignKey(
        "envdaq.DAQController", verbose_name=_("Controller"), on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = _("SamplingSystemController")
        verbose_name_plural = _("SamplingSystemControllers")

    def save(self, use_latest=True, *args, **kwargs):

        if use_latest:
            self.sampling_system = self.sampling_system.get_latest()

        return super(SamplingSystemController, self).save(*args, **kwargs)

    def sync_sampling_system(self):
        self.save()

    def __str__(self):
        return f"{self.sampling_system}-{self.controller}"

    def get_absolute_url(self):
        return reverse("SamplingSystemController_detail", kwargs={"pk": self.pk})


class SamplingSystemInstrument(models.Model):

    sampling_system = models.ForeignKey(
        "envdatasystem.SamplingSystem",
        verbose_name=_("Sampling System"),
        on_delete=models.CASCADE,
    )
    instrument = models.ForeignKey(
        "envdaq.DAQInstrument", verbose_name=_("Instrument"), on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        "envdatasystem.SamplingSystemLocation",
        verbose_name=_("Location"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    sample_point = models.ForeignKey(
        "envdatasystem.SamplingSystemSamplePoint",
        verbose_name=_("Sample Point"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("SamplingSystemInstrument")
        verbose_name_plural = _("SamplingSystemInstruments")

    def save(self, use_latest=True, *args, **kwargs):

        if use_latest:
            self.sampling_system = self.sampling_system.get_latest()

        return super(SamplingSystemInstrument, self).save(*args, **kwargs)

    def sync_sampling_system(self):
        self.save()

    def __str__(self):
        return f"{self.sampling_system}-{self.instrument}"

    def get_absolute_url(self):
        return reverse("SamplingSystemInstrument_detail", kwargs={"pk": self.pk})


# class DAQSystem(models.Model):

#     data_system = models.ForeignKey(
#         "envdatasystem.DataSystem",
#         verbose_name=_("Data System"),
#         on_delete=models.CASCADE,
#         related_name="daqsystem_datasystems",
#     )
#     name = models.CharField(_("Name"), max_length=50, null=True, blank=True)

#     daq_host = models.GenericIPAddressField(
#         _("DAQ Server address"),
#         protocol="both",
#         unpack_ipv4=False,
#         null=True,
#         blank=True,
#     )
#     daq_namespace = models.CharField(
#         _("DAQ Namespace"), max_length=20, default="default"
#     )
#     daq_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

#     # instrument map to SamplingSystem

#     # model of the daq setup you want
#     #   list of ControllerSystem?
#     class Meta:
#         verbose_name = _("DAQSystem")
#         verbose_name_plural = _("DAQSystems")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("DAQSystem_detail", kwargs={"pk": self.pk})


# class ControllerSystem(models.Model):

#     # TODO: at some point may want to abstract this to make daq OR parent be derived from
#     #   the same object (parent: DAQParent, ControllerParent)?

#     name = models.CharField(_("Name"), max_length=50)
#     prefix = models.CharField(_("Prefix"), max_length=10, default="default")

#     daq = models.ForeignKey(
#         "envdatasystem.DAQSystem",
#         verbose_name=_("DAQ System"),
#         on_delete=models.CASCADE,
#         related_name="controllersystem_daqs",
#         null=True,
#         blank=True,
#     )
#     parent_controller = models.ForeignKey(
#         "envdatasystem.ControllerSystem",
#         verbose_name=_("Parent Controller"),
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name="controllersystem_parentcontrollers",
#     )

#     controller = models.ForeignKey(
#         "envdaq.Controller",
#         verbose_name=_("Controller"),
#         on_delete=models.CASCADE,
#         related_name="controllersystem_controllers",
#     )

#     # component
#     # components = models.ForeignKey("envdatasystem.ComponentMap", verbose_name=_("Components"), on_delete=models.CASCADE, null=True, blank=True)

#     class Meta:
#         verbose_name = _("Controller System")
#         verbose_name_plural = _("Controller Systems")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("controllersystem_detail", kwargs={"pk": self.pk})


# class ControllerComponent(models.Model):
#     component_type_choices = [
#         ("controller", "Controller"),
#         ("instrument", "Instrument"),
#     ]

#     controller = models.ForeignKey(
#         "envdatasystem.ControllerSystem",
#         verbose_name=_("Controller"),
#         on_delete=models.CASCADE,
#         related_name="controllercomponent_controller",
#     )
#     name = models.CharField(_("Name"), max_length=50)

#     type = models.CharField(
#         _("Type"), max_length=50, choices=component_type_choices, default="instrument"
#     )

#     # primary =
#     # instruments = models.ManyToManyField(
#     #     "envdaq.InstrumentAlias",
#     #     verbose_name=_("Instruments"),
#     #     related_name="controllercomponent_instruments",
#     # )
#     # primary = models.ForeignKey(
#     #     "envdaq.InstrumentAlias",
#     #     verbose_name=_("Primary Instrument"),
#     #     on_delete=models.CASCADE,
#     #     related_name="controllercomponent_primary",
#     # )

#     class Meta:
#         verbose_name = _("ControllerComponent")
#         verbose_name_plural = _("ControllerComponents")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("ControllerComponent_detail", kwargs={"pk": self.pk})


# class ControllerComponentController(models.Model):

#     component = models.ForeignKey(
#         "envdatasystem.ControllerComponent",
#         verbose_name=_("Component"),
#         on_delete=models.CASCADE,
#         related_name="controllercomponentcontroller_component",
#     )
#     controller = models.ForeignKey(
#         "envdatasystem.ControllerSystem",
#         verbose_name=_("Controller"),
#         on_delete=models.CASCADE,
#         related_name="controllercomponentcontroller_controller",
#     )
#     primary = models.BooleanField(_("Primary Component"), default=False)

#     class Meta:
#         verbose_name = _("ControllerComponent Controller")
#         verbose_name_plural = _("ControllerComponent Controllers")

#     def __str__(self):
#         return f"controller-{self.component}-{self.controller}"

#     def get_absolute_url(self):
#         return reverse("controllercomponentcontroller_detail", kwargs={"pk": self.pk})

#     # def get_component(self):

#     #     component = None
#     #     inst_list = self.instruments.all()
#     #     if inst_list:
#     #         component["INST_MAP"] = dict()
#     #         ilist = []
#     #         for inst in inst_list:
#     #             ilist.append(inst)
#     #         component["INST_MAP"]["LIST"] = ilist
#     #         component["INST_MAP"]["PRIMARY"] = self.primary
#     #     return component


# class ControllerComponentInstrument(models.Model):

#     component = models.ForeignKey(
#         "envdatasystem.ControllerComponent",
#         verbose_name=_("Component"),
#         on_delete=models.CASCADE,
#         related_name="controllercomponentinstrument_component",
#     )
#     instrument = models.ForeignKey(
#         "envdatasystem.InstrumentSystem",
#         verbose_name=_("Instrument"),
#         on_delete=models.CASCADE,
#         related_name="controllercomponentinstrument_instrument",
#         # null=True,
#         # blank=True,
#     )
#     primary = models.BooleanField(_("Primary Component"), default=False)

#     class Meta:
#         verbose_name = _("ControllerComponent Instrument")
#         verbose_name_plural = _("ControllerComponent Instruments")

#     def __str__(self):
#         return f"instrument-{self.component}-{self.instrument}"

#     def get_absolute_url(self):
#         return reverse("controllercomponentinstrument_detail", kwargs={"pk": self.pk})


# class InstrumentSystem(models.Model):

#     name = models.CharField(_("Name"), max_length=50)
#     prefix = models.CharField(_("Prefix"), max_length=10, default="default")

#     controller = models.ForeignKey(
#         "envdatasystem.ControllerSystem",
#         verbose_name=_("Controller System"),
#         on_delete=models.CASCADE,
#         related_name="instrumentsystem_controller",
#     )
#     instrument = models.ForeignKey(
#         "envinventory.Instrument",
#         verbose_name=_("Instrument"),
#         on_delete=models.CASCADE,
#         related_name="instrumentsystem_instrument",
#     )
#     # components = models.ForeignKey("envdatasystem.ComponentMap", verbose_name=_("Components"), on_delete=models.CASCADE, null=True, blank=True)

#     class Meta:
#         verbose_name = _("Instrument System")
#         verbose_name_plural = _("Instrument Systems")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("instrumentsystem_detail", kwargs={"pk": self.pk})


# class InstrumentComponent(models.Model):
#     component_type_choices = [
#         ("interface", "Interface"),
#     ]

#     Instrument = models.ForeignKey(
#         "envdatasystem.InstrumentSystem",
#         verbose_name=_("Instrument"),
#         on_delete=models.CASCADE,
#         # related_name="instrumentcomponent_instrument",
#     )
#     name = models.CharField(_("Name"), max_length=50, default="default")

#     type = models.CharField(
#         _("Type"), max_length=50, choices=component_type_choices, default="interface"
#     )

#     # interfaces = models.ManyToManyField(
#     #     "envdaq.Interface",
#     #     verbose_name=_("Interfaces"),
#     #     related_name="instrumentcomponent_interface",
#     # )
#     # primary = models.ForeignKey(
#     #     "envdaq.InstrumentAlias",
#     #     verbose_name=_("Primary Instrument"),
#     #     on_delete=models.CASCADE,
#     #     related_name="controllercomponent_primary",
#     # )

#     class Meta:
#         verbose_name = _("InstrumentComponent")
#         verbose_name_plural = _("InstrumentComponents")

#     def __str__(self):
#         return f"{self.Instrument}-{self.type}-{self.name}"

#     def get_absolute_url(self):
#         return reverse("InstrumentComponent_detail", kwargs={"pk": self.pk})

#     # def get_component(self):

#     #     component = None
#     #     inst_list = self.instruments.all()
#     #     if inst_list:
#     #         component["INST_MAP"] = dict()
#     #         ilist = []
#     #         for inst in inst_list:
#     #             ilist.append(inst)
#     #         component["INST_MAP"]["LIST"] = ilist
#     #         component["INST_MAP"]["PRIMARY"] = self.primary
#     #     return component


# class InstrumentComponentInterface(models.Model):

#     component = models.ForeignKey(
#         "envdatasystem.InstrumentComponent",
#         verbose_name=_("Component"),
#         on_delete=models.CASCADE,
#         # related_name="instrumentcomponentinterface_component",
#     )
#     interface = models.ForeignKey("envdaq.Interface", verbose_name="Interface", on_delete=models.CASCADE, blank=True, null=True)
#     # interface = models.ForeignKey("envdatasystem.InterfaceSystem", verbose_name=_("Interface"), on_delete=models.CASCADE, related_name="instrumentcomponentinterface_interface")
#     # interface = models.CharField(
#     #     _("Interface"), max_length=100, default="default_interface"
#     # )
#     primary = models.BooleanField(_("Primary Component"), default=False)

#     class Meta:
#         verbose_name = _("InstrumentComponent Interface")
#         verbose_name_plural = _("InstrumentComponent Interfaces")

#     def __str__(self):
#         return f"{self.component}-{self.interface}"

#     def get_absolute_url(self):
#         return reverse("instrumentcomponentinterface_detail", kwargs={"pk": self.pk})


# class ComponentMap(models.Model):
#     class Meta:
#         verbose_name = _("ComponentMap")
#         verbose_name_plural = _("ComponentMaps")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("ComponentMap_detail", kwargs={"pk": self.pk})


# class SamplingSystemMap(models.Model):

#     project = models.ForeignKey(
#         "envdatasystem.Project",
#         verbose_name=_("Project"),
#         on_delete=models.CASCADE,
#         related_name="ssm_project",
#     )

#     platform = models.ForeignKey(
#         "envdatasystem.Platform",
#         verbose_name=_("Platform"),
#         on_delete=models.CASCADE,
#         related_name="ssm_platform",
#     )

#     # TODO: delete all these databases to get rid of null,blank here
#     sampling_system = models.ForeignKey(
#         "envdatasystem.SamplingSystem",
#         verbose_name=_("Sampling System"),
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True
#     )

#     class Meta:
#         verbose_name = _("Sampling System Map")
#         verbose_name_plural = _("Sampling System Maps")

#     def __str__(self):
#         return f"{self.project}-{self.platform}-{self.sampling_system}"

#     def get_absolute_url(self):
#         return reverse("samplingsystemmap_detail", kwargs={"pk": self.pk})


# class SSMPlatformLocationMap(models.Model):

#     system_map = models.ForeignKey(
#         "envdatasystem.SamplingSystemMap",
#         verbose_name=_("System Map"),
#         on_delete=models.CASCADE,
#     )
#     platform_location = models.ForeignKey(
#         "envdatasystem.PlatformLocation",
#         verbose_name=_("Platform Location"),
#         on_delete=models.CASCADE,
#     )
#     ss_location = models.ForeignKey(
#         "envdatasystem.SamplingSystemLocation",
#         verbose_name=_("SS Location"),
#         on_delete=models.CASCADE,
#     )

#     class Meta:
#         verbose_name = _("SSMPlatform")
#         verbose_name_plural = _("SSMPlatforms")

#     def __str__(self):
#         return f"{self.system_map}-{self.platform_location}-{self.ss_location}"

#     def get_absolute_url(self):
#         return reverse("SSMPlatform_detail", kwargs={"pk": self.pk})


# class SSMInstrumentMap(models.Model):

#     system_map = models.ForeignKey(
#         "envdatasystem.SamplingSystemMap",
#         verbose_name=_("System Map"),
#         on_delete=models.CASCADE,
#     )
#     ss_location = models.ForeignKey(
#         "envdatasystem.SamplingSystemLocation",
#         verbose_name=_("SS Location"),
#         on_delete=models.CASCADE,
#     )
#     ss_sample_point = models.ForeignKey(
#         "envdatasystem.SamplingSystemSamplePoint",
#         verbose_name=_("SS Sampling Point"),
#         on_delete=models.CASCADE,
#     )

#     instrument = models.ForeignKey(
#         "envdatasystem.InstrumentSystem",
#         verbose_name=_("Instrument"),
#         on_delete=models.CASCADE,
#     )

#     class Meta:
#         verbose_name = _("SSMInstrumentMap")
#         verbose_name_plural = _("SSMInstrumentMaps")

#     def __str__(self):
#         return f"{self.system_map}-{self.instrument}"

#     def get_absolute_url(self):
#         return reverse("SSMInstrumentMap_detail", kwargs={"pk": self.pk})


class Event(models.Model):

    eventType = models.CharField(_("Event Type"), max_length=50, blank=True, null=True)

    name = models.CharField(_("Name"), max_length=50)
    description = models.TextField(_("Description"), blank=True, null=True)
    eventID = models.UUIDField(default=uuid.uuid1, editable=False)
    updated = models.DateTimeField(
        _("Updated"), auto_now_add=True, blank=True, null=True
    )

    start_datetime = models.DateTimeField(
        _("Start DateTime"), auto_now=False, auto_now_add=False
    )
    stop_datetime = models.DateTimeField(
        _("Stop DateTime"), auto_now=False, auto_now_add=False, blank=True, null=True
    )

    # parent = models.ForeignKey("envdatasystem.Event", verbose_name=_("Parent Event"), on_delete=models.CASCADE)

    tags = models.ManyToManyField("envtags.Tag", verbose_name=_("Tags"), blank=True)

    def save(self, *args, **kwargs):
        self.updated = timezone.now()
        return super(Event, self).save(*args, **kwargs)

    def active(self):
        dt = timezone.now()
        if dt >= self.start_datetime:
            if self.stop_datetime and dt >= self.stop_datetime:
                return False
            
            return True
        return False
            
    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        abstract = True

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Event_detail", kwargs={"pk": self.pk})


class ProjectEvent(Event):

    project = models.ForeignKey(
        "envdatasystem.Project",
        verbose_name=_("Project"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "envdatasystem.ProjectEvent",
        verbose_name=_("Parent Event"),
        on_delete=models.CASCADE,
        related_name="parent_project",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Project Event")
        verbose_name_plural = _("Project Events")
        constraints = [
            models.CheckConstraint(
                check=(Q(project__isnull=False) & Q(parent__isnull=True))
                | (Q(project__isnull=True) & Q(parent__isnull=False)),
                name="oaoo_project_parent_event",
            )
        ]

    def save(self, *args, **kwargs):
        self.eventType = __class__.__name__
        return super(ProjectEvent, self).save(*args, **kwargs)

    def get_project(self):
        if self.parent:
            return self.parent.get_project()
        else:
            return self.project

    def __str__(self):
        if self.project:
            return f"{self.project.name}-{self.name}"
        elif self.parent:
            return f"{self.parent}-{self.name}"
        else:
            return self.name

    def get_absolute_url(self):
        return reverse("projectevent_detail", kwargs={"pk": self.pk})


class PlatformEvent(Event):

    project = models.ForeignKey(
        "envdatasystem.Project",
        verbose_name=_("Project"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    platform = models.ForeignKey(
        "envdatasystem.Platform",
        verbose_name=_("Platform"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "envdatasystem.PlatformEvent",
        verbose_name=_("Parent Event"),
        on_delete=models.CASCADE,
        related_name="parent_events",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Platform Event")
        verbose_name_plural = _("Platform Events")
        constraints = [
            models.CheckConstraint(
                check=(Q(platform__isnull=False) & Q(parent__isnull=True))
                | (Q(platform__isnull=True) & Q(parent__isnull=False)),
                name="oaoo_platform_parent_event",
            )
        ]

    def save(self, *args, **kwargs):
        self.eventType = __class__.__name__
        # if self.parent:
        #     self.project = self.parent.project
        if self.project and self.parent:
            self.parent.project = self.project.save()
            self.project = None
        return super(PlatformEvent, self).save(*args, **kwargs)

    def get_platform(self):
        if not self.platform:
            return self.parent.get_platform()
        else:
            return self.platform

    def get_project(self):
        if not self.project:
            return self.parent.get_project()
        else:
            return self.project

    # return datasets attached to this event
    def get_datasets(self, include_children=True):
        pass

    def __str__(self):
        result = self.name
        if self.platform:
            if self.project:
                result = f"{self.platform.name}-{self.project}-{self.name}"
            else:
                result = f"{self.platform.name}-{self.name}"
        elif self.parent:
            result = f"{self.parent}-{self.name}"

        return result

    def get_absolute_url(self):
        return reverse("platformevent_detail", kwargs={"pk": self.pk})


class SamplePeriod(models.Model):

    project = models.ForeignKey(
        "envdatasystem.Project", verbose_name=_("Project"), on_delete=models.CASCADE
    )
    platform_event = models.ForeignKey(
        "envdatasystem.PlatformEvent",
        verbose_name=_("Platform Event"),
        on_delete=models.CASCADE,
    )
    sampling_systems = models.ManyToManyField(
        "envdatasystem.SamplingSystem", verbose_name=_("Sampling System(s)")
    )

    class Meta:
        verbose_name = _("SamplePeriod")
        verbose_name_plural = _("SamplePeriods")

    def __str__(self):
        ss_name = ""
        ss_list = self.sampling_systems.all()
        # print(ss_list)
        for ss in self.sampling_systems.all():
            print(ss.name)
            if ss_name:
                ss_name += f"-{ss.name}"
            else:
                ss_name += f"{ss.name}"
        return f"{self.project.name}:{self.platform_event}:{ss_name}"
        # return "test"

    def get_absolute_url(self):
        return reverse("SamplePeriod_detail", kwargs={"pk": self.pk})


# class SSDatasetManager(VersionManager):
    
#     def get_datasets(self, project=None, platform=None, platform_event=None):

#         if platform_event: # overrides other two
#             pass


#     def get_queryset(self):
#         return super().get_queryset().filter()


class SamplingSystemDataset(models.Model):

    # TODO hide this from user, set in save via platform_event
    project = models.ForeignKey(
        "envdatasystem.Project",
        verbose_name=_("Project"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    platform_event = models.ForeignKey(
        "envdatasystem.PlatformEvent",
        verbose_name=_("Platform Event"),
        on_delete=models.CASCADE,
    )
    sampling_system = models.ForeignKey(
        "envdatasystem.SamplingSystem",
        verbose_name=_("Sampling System"),
        on_delete=models.CASCADE,
    )

    # version_starttime = models.DateTimeField(
    #     _("Version Start Time"),
    #     auto_now=False,
    #     auto_now_add=False,
    #     blank=True,
    #     null=True,
    # )
    # version_stoptime = models.DateTimeField(
    #     _("Version Stop Time"),
    #     auto_now=False,
    #     auto_now_add=False,
    #     blank=True,
    #     null=True,
    # )

    # objects = VersionManager()

    current = models.BooleanField(_("Current Dataset"), default=True)

    class Meta:
        verbose_name = _("SamplingSystem Dataset")
        verbose_name_plural = _("SamplingSystem Datasets")

    def save(self, update_version=True, *args, **kwargs):

        self.project = self.platform_event.get_project()

        # start_ts = self.platform_event.start_datetime
        # stop_ts = None
        # if self.platform_event.stop_datetime:
        #     stop_ts = self.platform_event.stop_datetime
        # ts = timezone.now()

        # if update_version:
        #     # orig = SamplingSystem.version.get_latest(self.name)
        #     create_new = False
        #     try:
        #         orig = SamplingSystemDataset.objects.get(pk=self.pk)

        #         # check to see if fields have changed
        #         if (
        #             self.project != orig.project
        #             or self.platform_event != orig.platform_event
        #             or self.sampling_system != orig.sampling_system
        #         ):

        #             if orig.platform_event.stop_datetime:
        #                 orig.version_stoptime = orig.platform_event.stop_datetime
        #             else:
        #                 orig.version_stoptime = ts

        #             orig.current = False
        #             orig.save(update_version=False)
        #             create_new = True

        #     except SamplingSystemDataset.DoesNotExist:
        #         pass

        #     if create_new:
        #         self.pk = None
        #     self.version_starttime = start_ts
        #     if stop_ts:
        #         self.version_stoptime = stop_ts
        return super(SamplingSystemDataset, self).save(*args, **kwargs)

    def set_current(self, dt=None, dt_string=None, platform_event=None):
        ds = self.get_version(dt, dt_string, platform_event)
        if ds:
            ds.current = True
            ds.save(update_version=False)
        else:  # if no version criteria given will set self to current
            self.current = True
            self.save(update_version=False)

    # this is wrong...needs to be current for a sampling system. We should also have a way to get current
    #   datasets for a given project, platform and/or platform_event
    def get_current(self):

        # datasets = SamplingSystemDataset.objects.filter(project=self.project, current=True)
        # # platform = self.platform_event.get_platform()
        # for ds in datasets:
        #     if ds.platform_event.get_platform() == self.platform_event.get_platform():
        #         return ds
        # return None
        try:
            return SamplingSystemDataset.objects.get(
                project=self.project, sampling_system=self.sampling_system, current=True
            )
        except SamplingSystemDataset.DoesNotExist:
            return None

    def sync_current(self):
        pass

    # def get_latest(self):
    #     return SamplingSystemDataset.objects.get_latest(
    #         project=self.project, sampling_system=self.sampling_system
    #     )

    # def get_version(self, dt=None, dt_string=None, platform_event=None):
    #     if dt:
    #         return SamplingSystemDataset.objects.get_version(
    #             project=self.project, sampling_system=self.sampling_system, dt=dt
    #         )
    #     elif dt_string:
    #         return SamplingSystemDataset.objects.get_version(
    #             project=self.project,
    #             sampling_system=self.sampling_system,
    #             dt_string=dt_string,
    #         )
    #     elif platform_event:
    #         ds = SamplingSystemDataset.objects.filter(
    #             project=self.project,
    #             sampling_system=self.sampling_system,
    #             platform_event=platform_event,
    #         )[0]
    #         return ds.get_latest()
    #     else:
    #         return None

    # def sync_sampling_system(self):
    #     self.sampling_system = self.sampling_system.get_latest()
    #     self.save(update_version=False)

    def get_project(self):
        return self.platform_event.get_project()

    def get_platform(self):
        return self.platform_event.get_platform()

    def __str__(self):

        # proj_name = "NoProject"
        # if self.project:
        #     proj_name = self.project.name

        # # if self.version_stoptime:
        # if not self.current:
        #     # start = self.version_starttime.strftime("%Y-%m-%dT%H:%M:%S")
        #     start = dt_to_string(self.version_starttime)
        #     # stop = self.version_stoptime.strftime("%Y-%m-%dT%H:%M:%S")
        #     stop = dt_to_string(self.version_stoptime)
        #     return f"{self.sampling_system.name}-{proj_name}-{self.platform_event.name}-{start}-{stop}"
        # else:
        #     return (
        #         f"{proj_name}-{self.sampling_system.name} ({self.platform_event.name})"
        #     )

        return (
            f"{self.sampling_system.name}-{self.platform_event.name} ({self.project})"
        )

    def get_absolute_url(self):
        return reverse("DAQDataset_detail", kwargs={"pk": self.pk})


class SSDatasetEvent(Event):

    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True, null=True)
    dataset = models.ForeignKey(
        "envdatasystem.SamplingSystemDataset",
        verbose_name=_("Dataset"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        "envdatasystem.SSDatasetEvent",
        verbose_name=_("Parent"),
        on_delete=models.CASCADE,
        related_name="parent_dataset",
        blank=True,
        null=True,
    )

    tags = models.ManyToManyField("envtags.Tag", verbose_name=_("Tags"), blank=True)

    class Meta:
        verbose_name = _("SSDatasetEvent")
        verbose_name_plural = _("SSDatasetEvents")
        constraints = [
            models.CheckConstraint(
                check=(Q(dataset__isnull=False) & Q(parent__isnull=True))
                | (Q(dataset__isnull=True) & Q(parent__isnull=False)),
                name="oaoo_ss_dataset_event",
            )
        ]

    def save(self, *args, **kwargs):
        self.eventType = __class__.__name__
        return super(SSDatasetEvent, self).save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent}-{self.name}"
        else:
            return f"{self.dataset}-{self.name}"

    def get_absolute_url(self):
        return reverse("SSDatasetEvent_detail", kwargs={"pk": self.pk})
