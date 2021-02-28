from django.db import models
from django.db.models.fields import IPAddressField
from django.db.models.fields.related import ForeignKey
from django.urls import reverse
from django.utils.translation import gettext as _
import uuid

from envtags.models import Tag

# Create your models here.


class DataSystem(models.Model):

    name = models.CharField(_("TmpName"), max_length=50, blank=True, null=True)

    project = models.ForeignKey(
        "envdatasystem.Project",
        verbose_name=_("Project"),
        on_delete=models.CASCADE,
        related_name="datasystems_project",
    )
    platform = models.ForeignKey(
        "envdatasystem.Platform",
        verbose_name=_("Platform"),
        on_delete=models.CASCADE,
        related_name="datasystems_platform",
    )

    sampling_system = models.ManyToManyField(
        "envdatasystem.SamplingSystemMap", verbose_name=_("Sampling System"), blank=True
    )
    # sampling_system
    # platform =

    class Meta:
        verbose_name = _("Data System")
        verbose_name_plural = _("Data Systems")

    def __str__(self):
        return f"{self.project}-{self.platform}"

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

    def __str__(self):
        """String representation of Platform object. """
        return self.name

    def __repr__(self):
        return f"{self.name} ({self.platform_id})"


class PlatformLocation(models.Model):

    platform = models.ForeignKey(
        "envdatasystem.Platform",
        verbose_name=_("Platform"),
        on_delete=models.CASCADE,
        related_name="platformlocation_platforms",
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
        related_name="platformlocation_parents",
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


class SamplingSystem(models.Model):

    name = models.CharField(_("Name"), max_length=50)
    long_name = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

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

    def __str__(self):
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

    def __str__(self):
        name = f"{self.sampling_system}-{self.name}"
        if self.parent:
            name = f"{self.parent}:{name}"
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

    def __str__(self):
        name = f"{self.sampling_system}-{self.name}"
        if self.parent:
            name = f"{self.parent}:{name}"
        return name

    def get_absolute_url(self):
        return reverse("SamplingSystemSamplePoint_detail", kwargs={"pk": self.pk})


class DAQSystem(models.Model):

    data_system = models.ForeignKey(
        "envdatasystem.DataSystem",
        verbose_name=_("Data System"),
        on_delete=models.CASCADE,
        related_name="daqsystem_datasystems",
    )
    name = models.CharField(_("Name"), max_length=50, null=True, blank=True)

    daq_host = models.GenericIPAddressField(
        _("DAQ Server address"),
        protocol="both",
        unpack_ipv4=False,
        null=True,
        blank=True,
    )
    daq_namespace = models.CharField(
        _("DAQ Namespace"), max_length=20, default="default"
    )
    daq_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # instrument map to SamplingSystem

    # model of the daq setup you want
    #   list of ControllerSystem?
    class Meta:
        verbose_name = _("DAQSystem")
        verbose_name_plural = _("DAQSystems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("DAQSystem_detail", kwargs={"pk": self.pk})


class ControllerSystem(models.Model):

    # TODO: at some point may want to abstract this to make daq OR parent be derived from
    #   the same object (parent: DAQParent, ControllerParent)?

    name = models.CharField(_("Name"), max_length=50)
    prefix = models.CharField(_("Prefix"), max_length=10, default="default")

    daq = models.ForeignKey(
        "envdatasystem.DAQSystem",
        verbose_name=_("DAQ System"),
        on_delete=models.CASCADE,
        related_name="controllersystem_daqs",
        null=True,
        blank=True,
    )
    parent_controller = models.ForeignKey(
        "envdatasystem.ControllerSystem",
        verbose_name=_("Parent Controller"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="controllersystem_parentcontrollers",
    )

    controller = models.ForeignKey(
        "envdaq.Controller",
        verbose_name=_("Controller"),
        on_delete=models.CASCADE,
        related_name="controllersystem_controllers",
    )

    # component
    # components = models.ForeignKey("envdatasystem.ComponentMap", verbose_name=_("Components"), on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = _("Controller System")
        verbose_name_plural = _("Controller Systems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("controllersystem_detail", kwargs={"pk": self.pk})


class ControllerComponent(models.Model):
    component_type_choices = [
        ("controller", "Controller"),
        ("instrument", "Instrument"),
    ]

    controller = models.ForeignKey(
        "envdatasystem.ControllerSystem",
        verbose_name=_("Controller"),
        on_delete=models.CASCADE,
        related_name="controllercomponent_controller",
    )
    name = models.CharField(_("Name"), max_length=50)

    type = models.CharField(
        _("Type"), max_length=50, choices=component_type_choices, default="instrument"
    )

    # primary =
    # instruments = models.ManyToManyField(
    #     "envdaq.InstrumentAlias",
    #     verbose_name=_("Instruments"),
    #     related_name="controllercomponent_instruments",
    # )
    # primary = models.ForeignKey(
    #     "envdaq.InstrumentAlias",
    #     verbose_name=_("Primary Instrument"),
    #     on_delete=models.CASCADE,
    #     related_name="controllercomponent_primary",
    # )

    class Meta:
        verbose_name = _("ControllerComponent")
        verbose_name_plural = _("ControllerComponents")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ControllerComponent_detail", kwargs={"pk": self.pk})


class ControllerComponentController(models.Model):

    component = models.ForeignKey(
        "envdatasystem.ControllerComponent",
        verbose_name=_("Component"),
        on_delete=models.CASCADE,
        related_name="controllercomponentcontroller_component",
    )
    controller = models.ForeignKey(
        "envdatasystem.ControllerSystem",
        verbose_name=_("Controller"),
        on_delete=models.CASCADE,
        related_name="controllercomponentcontroller_controller",
    )
    primary = models.BooleanField(_("Primary Component"), default=False)

    class Meta:
        verbose_name = _("ControllerComponent Controller")
        verbose_name_plural = _("ControllerComponent Controllers")

    def __str__(self):
        return f"controller-{self.component}-{self.controller}"

    def get_absolute_url(self):
        return reverse("controllercomponentcontroller_detail", kwargs={"pk": self.pk})

    # def get_component(self):

    #     component = None
    #     inst_list = self.instruments.all()
    #     if inst_list:
    #         component["INST_MAP"] = dict()
    #         ilist = []
    #         for inst in inst_list:
    #             ilist.append(inst)
    #         component["INST_MAP"]["LIST"] = ilist
    #         component["INST_MAP"]["PRIMARY"] = self.primary
    #     return component


class ControllerComponentInstrument(models.Model):

    component = models.ForeignKey(
        "envdatasystem.ControllerComponent",
        verbose_name=_("Component"),
        on_delete=models.CASCADE,
        related_name="controllercomponentinstrument_component",
    )
    instrument = models.ForeignKey(
        "envdatasystem.InstrumentSystem",
        verbose_name=_("Instrument"),
        on_delete=models.CASCADE,
        related_name="controllercomponentinstrument_instrument",
        # null=True,
        # blank=True,
    )
    primary = models.BooleanField(_("Primary Component"), default=False)

    class Meta:
        verbose_name = _("ControllerComponent Instrument")
        verbose_name_plural = _("ControllerComponent Instruments")

    def __str__(self):
        return f"instrument-{self.component}-{self.instrument}"

    def get_absolute_url(self):
        return reverse("controllercomponentinstrument_detail", kwargs={"pk": self.pk})


class InstrumentSystem(models.Model):

    name = models.CharField(_("Name"), max_length=50)
    prefix = models.CharField(_("Prefix"), max_length=10, default="default")

    controller = models.ForeignKey(
        "envdatasystem.ControllerSystem",
        verbose_name=_("Controller System"),
        on_delete=models.CASCADE,
        related_name="instrumentsystem_controller",
    )
    instrument = models.ForeignKey(
        "envinventory.Instrument",
        verbose_name=_("Instrument"),
        on_delete=models.CASCADE,
        related_name="instrumentsystem_instrument",
    )
    # components = models.ForeignKey("envdatasystem.ComponentMap", verbose_name=_("Components"), on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = _("Instrument System")
        verbose_name_plural = _("Instrument Systems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("instrumentsystem_detail", kwargs={"pk": self.pk})


class InstrumentComponent(models.Model):
    component_type_choices = [
        ("interface", "Interface"),
    ]

    Instrument = models.ForeignKey(
        "envdatasystem.InstrumentSystem",
        verbose_name=_("Controller"),
        on_delete=models.CASCADE,
        related_name="instrumentcomponent_instrument",
    )
    name = models.CharField(_("Name"), max_length=50)

    type = models.CharField(
        _("Type"), max_length=50, choices=component_type_choices, default="interface"
    )

    # interfaces = models.ManyToManyField(
    #     "envdaq.Interface",
    #     verbose_name=_("Interfaces"),
    #     related_name="instrumentcomponent_interface",
    # )
    # primary = models.ForeignKey(
    #     "envdaq.InstrumentAlias",
    #     verbose_name=_("Primary Instrument"),
    #     on_delete=models.CASCADE,
    #     related_name="controllercomponent_primary",
    # )

    class Meta:
        verbose_name = _("InstrumentComponent")
        verbose_name_plural = _("InstrumentComponents")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("InstrumentComponent_detail", kwargs={"pk": self.pk})

    # def get_component(self):

    #     component = None
    #     inst_list = self.instruments.all()
    #     if inst_list:
    #         component["INST_MAP"] = dict()
    #         ilist = []
    #         for inst in inst_list:
    #             ilist.append(inst)
    #         component["INST_MAP"]["LIST"] = ilist
    #         component["INST_MAP"]["PRIMARY"] = self.primary
    #     return component


class InstrumentComponentInterface(models.Model):

    component = models.ForeignKey(
        "envdatasystem.InstrumentComponent",
        verbose_name=_("Component"),
        on_delete=models.CASCADE,
        related_name="instrumentcomponentinterface_component",
    )
    # interface = models.ForeignKey("envdatasystem.InterfaceSystem", verbose_name=_("Interface"), on_delete=models.CASCADE, related_name="instrumentcomponentinterface_interface")
    interface = models.CharField(
        _("Interface"), max_length=100, default="default_interface"
    )
    primary = models.BooleanField(_("Primary Component"), default=False)

    class Meta:
        verbose_name = _("InstrumentComponent Interface")
        verbose_name_plural = _("InstrumentComponent Interfaces")

    def __str__(self):
        return f"{self.controller}-interface-{self.component}"

    def get_absolute_url(self):
        return reverse("instrumentcomponentinterface_detail", kwargs={"pk": self.pk})


# class ComponentMap(models.Model):
#     class Meta:
#         verbose_name = _("ComponentMap")
#         verbose_name_plural = _("ComponentMaps")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("ComponentMap_detail", kwargs={"pk": self.pk})


class SamplingSystemMap(models.Model):

    project = models.ForeignKey(
        "envdatasystem.Project",
        verbose_name=_("Project"),
        on_delete=models.CASCADE,
        related_name="ssm_project",
    )

    platform = models.ForeignKey(
        "envdatasystem.Platform",
        verbose_name=_("Platform"),
        on_delete=models.CASCADE,
        related_name="ssm_platform",
    )

    # TODO: delete all these databases to get rid of null,blank here
    sampling_system = models.ForeignKey(
        "envdatasystem.SamplingSystem",
        verbose_name=_("Sampling System"),
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Sampling System Map")
        verbose_name_plural = _("Sampling System Maps")

    def __str__(self):
        return f"{self.project}-{self.platform}-{self.sampling_system}"

    def get_absolute_url(self):
        return reverse("samplingsystemmap_detail", kwargs={"pk": self.pk})


class SSMPlatformLocationMap(models.Model):

    system_map = models.ForeignKey(
        "envdatasystem.SamplingSystemMap",
        verbose_name=_("System Map"),
        on_delete=models.CASCADE,
    )
    platform_location = models.ForeignKey(
        "envdatasystem.PlatformLocation",
        verbose_name=_("Platform Location"),
        on_delete=models.CASCADE,
    )
    ss_location = models.ForeignKey(
        "envdatasystem.SamplingSystemLocation",
        verbose_name=_("SS Location"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("SSMPlatform")
        verbose_name_plural = _("SSMPlatforms")

    def __str__(self):
        return f"{self.system_map}-{self.platform_location}-{self.ss_location}"

    def get_absolute_url(self):
        return reverse("SSMPlatform_detail", kwargs={"pk": self.pk})


class SSMInstrumentMap(models.Model):

    system_map = models.ForeignKey(
        "envdatasystem.SamplingSystemMap",
        verbose_name=_("System Map"),
        on_delete=models.CASCADE,
    )
    ss_location = models.ForeignKey(
        "envdatasystem.SamplingSystemLocation",
        verbose_name=_("SS Location"),
        on_delete=models.CASCADE,
    )
    ss_sample_point = models.ForeignKey(
        "envdatasystem.SamplingSystemSamplePoint",
        verbose_name=_("SS Sampling Point"),
        on_delete=models.CASCADE,
    )

    instrument = models.ForeignKey(
        "envdatasystem.InstrumentSystem",
        verbose_name=_("Instrument"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("SSMInstrumentMap")
        verbose_name_plural = _("SSMInstrumentMaps")

    def __str__(self):
        return f"{self.system_map}-{self.instrument}"

    def get_absolute_url(self):
        return reverse("SSMInstrumentMap_detail", kwargs={"pk": self.pk})
