from json.decoder import JSONDecodeError
from django.db import models
from django.db.models.base import Model
from django.db.models.fields import reverse_related
from django.db.models.fields.related import ForeignKey
from django.utils.translation import gettext as _
from django.utils import timezone
import uuid
import json
from shared.data.namespace import Namespace

from shared.data.status import Status

# Create your models here.

# registration models (abstract inheritance?)
class Registration(models.Model):

    # TODO: overload save to update time field instead of rely on auto
    #       this will allow changing status without renewing age
    status = models.CharField(_("Status"), default="UNKNOWN", max_length=50)
    regkey = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(
        _("Created"), auto_now_add=True, blank=True, null=True
    )
    # updated = models.DateTimeField(_("Updated"), auto_now=True, blank=True, null=True)
    updated = models.DateTimeField(_("Updated"), auto_now_add=True, blank=True, null=True)
    # network = models.ForeignKey(
    #     "envnet.Network", on_delete=models.CASCADE
    # )

    def save(self, *args, **kwargs):
        do_update=False
        try: 
            # print(f'do update')
            do_update = kwargs.pop("do_update")
            self.updated = timezone.now()
        except KeyError:
            pass
        return super(Registration, self).save(*args, **kwargs)
    class Meta:
        # verbose_name = _("Registration")
        # verbose_name_plural = _("Registrations")
        abstract = True

    # def __str__(self):
    #     return self.name

    # def get_absolute_url(self):
    #     return reverse("Registration_detail", kwargs={"pk": self.pk})

    def get_age(self):
        # return number of seconds since last update
        return (timezone.now() - self.updated).total_seconds()


class ServiceRegistration(Registration):

    local_service = models.BooleanField(default=True)
    host = models.CharField(_("Host name"), max_length=100)
    port = models.IntegerField(_("Port number"))
    service_list = models.TextField(_("Services"), default="{}")
    # services_list = models.JSONField()
    network = models.ForeignKey(
        "envnet.Network", on_delete=models.CASCADE, blank=True, null=True
    )

    class Meta:
        verbose_name = _("Service Registration")
        verbose_name_plural = _("Service Registrations")

    def __str__(self):
        return f"{self.host}:{self.port}"
        # return self.name

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})

    def get_registration(self):
        network = ""
        if self.network:
            network = self.network.name
        reg = {
            "local_service": True,
            "network": network,
            "host": self.host,
            "port": self.port,
            "status": self.status,
            "regkey": f"{self.regkey}",
            "service_list": self.service_list,
        }
        # print(f"reg = {reg}")
        return reg

    def add_services(self, service_list):
        try:
            sl = json.loads(self.service_list)
        except JSONDecodeError:
            sl = {}
        if service_list:
            for name, val in service_list.items():
                if name not in sl:
                    sl[name] = val
            self.service_list = json.dumps(sl)

        self.save()

    def remove_services(self, service_list):
        try:
            sl = json.loads(self.service_list)
        except JSONDecodeError:
            sl = {}
        if service_list:
            for key in sl.keys():
                if key in list(service_list):
                    sl.pop(key)
            self.service_list = json.dumps(sl)

        self.save()

    def join_network(self, name):
        try:
            net = Network.objects.get(name=name)
        except Network.DoesNotExist:
            net = Network(name=name)
            net.activate()
        self.network = net
        self.save()

class DAQRegistration(Registration):

    # daq_list = models.TextField(_("DAQ List"))
    # eventually, namespace may be replaced with the Service object
    # reg_id = models.CharField(_("ID"), max_length=100, default="default")
    reg_id = models.JSONField(_("Reg ID"), default=dict)
    namespace = models.JSONField(_("Namespace"), blank=True, default=dict)
    daq_type = models.CharField(_("Type"), max_length=50, default=Namespace.DAQSERVER)
    # config = models.TextField(null=True, blank=True)
    config = models.JSONField("Configuration", blank=True, default=dict)
    # status = models.CharField(_("Status"), max_length=50, default="CONNECTED")
    status2 = models.JSONField(_("Status_JSON"), blank=True, default=dict)
    class Meta:
        verbose_name = _("DAQ Registration")
        verbose_name_plural = _("DAQ Registrations")

    def __str__(self):
        reg_id = self.reg_id
        # host = reg_id["host"]
        # ns = reg_id["namespace"]
        return f"{self.daq_type}:{reg_id['host']}:{reg_id['namespace']}"
        # return f"{self.reg_id}"

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})

    def get_registration(self):
        reg = {
            "reg_id": self.reg_id,
            # "reg_id2": self.reg_id2,
            "namespace": self.namespace,
            "daq_type": self.daq_type,
            "regkey": f"{self.regkey}",
            "config": self.config,
            # "config2": self.config2,
            "status": self.status,
            "age": self.get_age()
        }
        # print(f"reg = {reg}")
        return reg


# network model
class Network(models.Model):

    name = models.CharField(_("Name"), max_length=50)
    long_name = models.CharField(_("Long Name"), max_length=150, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    active = models.BooleanField(_("Active network"), default=False)

    # change to override save() instead of auto_ features:
    #  https://stackoverflow.com/questions/3429878/automatic-creation-date-for-django-model-form-objects
    created = models.DateTimeField(
        _("Created"), auto_now_add=True, blank=True, null=True
    )
    updated = models.DateTimeField(_("Updated"), auto_now=True, blank=True, null=True)
    # active = boolean?

    # registrations = models.ForeignKey(
    #     "envnet.ServiceRegistration",
    #     on_delete=models.CASCADE,
    #     # related_name="registrations",
    #     blank=True,
    #     null=True,
    # )

    class Meta:
        verbose_name = _("Network")
        verbose_name_plural = _("Networks")

    def __str__(self):
        return self.name

    def activate(self):
        self.active = True
        self.save()

    def deactivate(self):
        self.active = False
        self.save()

    # def add_registration(self, reg):
    #     # if reg not in self.registrations:
    #     # self.registrations.add(reg)
    #     self.save()

    # def get_absolute_url(self):
    #     return reverse_related("network_detail", kwargs={"pk": self.pk})
