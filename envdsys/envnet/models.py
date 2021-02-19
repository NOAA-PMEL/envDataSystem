from json.decoder import JSONDecodeError
from django.db import models
from django.db.models.base import Model
from django.db.models.fields import reverse_related
from django.utils.translation import gettext as _
from django.utils import timezone
import uuid
import json

# Create your models here.

# registration models (abstract inheritance?)
class Registration(models.Model):

    local_service = models.BooleanField(default=True)
    host = models.CharField(_("Host name"), max_length=100)
    port = models.IntegerField(_("Port number"))
    regkey = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(_("Created"), auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(_("Updated"), auto_now=True, blank=True, null=True)

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

    service_list = models.TextField(_("Services"), default="{}")

    class Meta:
        verbose_name = _("Service Registration")
        verbose_name_plural = _("Service Registrations")

    def __str__(self):
        return f"{self.host}:{self.port}"
        # return self.name

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})

    def get_registration(self):
        reg = {
            "local_service": True,
            "host": self.host,
            "port": self.port,
            "regkey": self.regkey,
            "service_list": self.service_list
        }
        return reg

    def add_services(self, service_list):
        try:
            sl = json.loads(self.service_list)
        except JSONDecodeError:
            sl = {}
        if service_list:
            for name,val in service_list.items():
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

class DAQRegistration(Registration):

    # daq_list = models.TextField(_("DAQ List"))
    daq_type = models.CharField(_("Type"), max_length=50, default="DAQServer")
    config = models.TextField(null=True, blank=True)
    status = models.CharField(_("Status"), max_length=50, default="CONNECTED")

    class Meta:
        verbose_name = _("DAQ List")
        verbose_name_plural = _("DAQ Lists")

    def __str__(self):
        return f"DAQ-{self.host}:{self.port}"
        # return self.name

    # def get_absolute_url(self):
    #     return reverse("_detail", kwargs={"pk": self.pk})


# network model
class Network(models.Model):

    name = models.CharField(_("Name"), max_length=50)
    long_name = models.CharField(_("Long Name"), max_length=150, null=True, blank=True)
    description = models.TextField(_("Description"), null=True, blank=True)

    # change to override save() instead of auto_ features:
    #  https://stackoverflow.com/questions/3429878/automatic-creation-date-for-django-model-form-objects
    created = models.DateTimeField(_("Created"), auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(_("Updated"), auto_now=True, blank=True, null=True)
    # active = boolean?

    class Meta:
        verbose_name = _("Network")
        verbose_name_plural = _("Networks")

    def __str__(self):
        return self.name

    # def get_absolute_url(self):
    #     return reverse_related("network_detail", kwargs={"pk": self.pk})
