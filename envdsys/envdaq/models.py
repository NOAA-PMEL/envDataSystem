import hashlib
from django.db.models.query_utils import Q
from django.utils.translation import gettext as _
from django.db import models
from django.db.models.base import Model
from django.urls import reverse
from django.core.exceptions import ValidationError
import uuid
from django.apps import apps
import json
import time
from shared.data.namespace import Namespace
from envtags.models import Tag, Configuration
from envinventory.models import Instrument


# Create your models here.
# class Configuration(models.Model):
#     name = models.CharField(max_length=50)
#     uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)
#     config = models.TextField(editable=True, null=True)

#     def set_config(self, config):
#         '''
#         set config using dictionary
#         '''
#         if config is None:
#             return ''

#         entry = dict()
#         entry['NAME'] = self.name

#         try:
#             entry['ENVDAQ'] = json.dumps(config)
#             # json_config = json.dumps(config)
#             # config = json.dumps(d)
#         except ValueError:
#             print('Error decoding config')
#             entry['NAME'] = ''
#         # entry = dict()
#         # entry["NAME"] = self.name
#         # entry["ENVDAQ"] = d
#         self.config = json.dumps(entry)
#         self.save()

#     def set_config_json(self, json_config):

#         if json_config is None:
#             return ''

#         try:
#             config = json.loads()
#         except ValueError:
#             return ''

#         self.set_config(config)

#     def get_config(self):

#         try:
#             config = json.loads(self.config)
#         except ValueError:
#             print('Error decoding json config')
#             config = ''
#         # print(json_config)
#         return config

#     def get_config_json(self):
#         return json.dumps(self.get_config())

#     def __str__(self):
#         '''String representation of Controller object. '''
#         return self.name

#     def __repr__(self):
#         return (f'{self.name}.{self.uniqueID}')


# class Configurable(models.Model):
#     name = models.CharField(max_length=50)

#     uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

#     # json string with configuration information. At some point
#     #   can change to a jsonfield but for now make it a TextField
#     #   that is not editable and do en/decoding separately
#     config = models.TextField(editable=False, null=True)

#     class Meta:
#         abstract = True
#         verbose_name = ''
#         verbose_name_plural = ''

#     def add_config(self, json_config):
#         '''
#         Add JSON config information to a configurable model. JSON will
#         be encoded and stored as a string the database.
#         '''
#         if json_config is None:
#             return

#         try:
#             config = json.loads(json_config)
#         except ValueError:
#             print('Error encoding json config')
#             config = ''

#         self.config = config

#     def get_config(self):
#         '''
#         Get JSON config information from a configurable model. Stored value
#         will be decoded and returned as json
#         '''

#         try:
#             json_config = json.dumps(self.config)
#         except ValueError:
#             print('Error encoding json config')
#             json_config = ''

#         return json_config

#     def add_name_details(self):
#         pass

#     # this needs to be done in the inhertited classes for now
#     # def add_name_details(
#     #     self,
#     #     help_text=None,
#     #     max_length=50,
#     #     verbose_name=None,
#     #     verbose_name_plural=None
#     # ):
#     #     if help_text is not None:
#     #         self.name.help_text = help_text
#     #     if max_length is not None:
#     #         self.name.max_length = max_length

#     #     if verbose_name is not None:
#     #         self.Meta().verbose_name = verbose_name
#     #     if verbose_name_plural is not None:
#     #         self.Meta().verbose_name_plural = verbose_name_plural
#     #     self.save()

#     def __str__(self):
#         '''String representation of Controller object. '''
#         return self.name

#     def __repr__(self):
#         return (f'{self.name}.{self.uniqueID}')


class DAQServer(models.Model):

    name = models.CharField(max_length=50, default=uuid.uuid1)
    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    class Meta:
        verbose_name = "DAQ Server"
        verbose_name_plural = "DAQ Servers"

    host = models.CharField(
        max_length=30, default="localhost", help_text="hostname or ip address"
    )
    # ip_address = models.GenericIPAddressField(null=True)
    # port = models.IntegerField(null=True)

    autoenable = models.BooleanField(_("Auto Enable"), default=False)

    namespace = models.CharField(
        _("Namespace"), max_length=100, default="localhost-default"
    )
    namespace2  = models.JSONField(_("NamespaceJSON"), blank=True, default=dict)

    configuration = models.ForeignKey(
        "envtags.Configuration",
        on_delete=models.CASCADE,
        related_name="configurations",
        null=True,
    )

    daq_config = models.ForeignKey(
        "envdaq.DAQServerConfig",
        verbose_name="DAQServer Config",
        on_delete=models.CASCADE,
        null=True,
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="daqserver_tags",
    )

    # controller list : this will be on the controller side

    def __str__(self):
        """String representation of Controller object. """
        return f"{self.host}:{self.name}"

    # def __repr__(self):
    #     return f"{self.name}.{self.uniqueID}"

    def get_config(self):
        config = dict()

        # add server specific config
        config["NAME"] = self.name
        config["namespace"] = self.get_namespace().to_dict()
        config["uri"] = self.host
        config["autoenable_daq"] = self.autoenable
        envdaq_config = dict()
        envdaq_config["namespace"] = self.get_namespace().to_dict()

        # get all controller configs
        controllers = DAQController.objects.filter(server=self)
        # print(f"{controllers}")
        cont_list = dict()
        for cont in controllers:
            # print(f"cont: {cont.get_config()}")
            cont_list[cont.name] = cont.get_config()

        # print(f"{cont_list}")
        envdaq_config["CONT_LIST"] = cont_list
        config["ENVDAQ_CONFIG"] = envdaq_config

        # self.daq_config = config
        return config

    def save(self, *args, **kwargs):
        self.update_namespace()
        # self.update_config()
        super(DAQServer, self).save(*args, **kwargs)

    def get_namespace(self):
        ns = Namespace(name=self.name, host=self.host, ns_type=Namespace.DAQSERVER)
        return ns

    def update_namespace(self):
        ns = self.get_namespace()
        self.namespace = ns.get_namespace()
        self.namespace2 = ns.get_namespace_sig()
        # pass

class DAQController(models.Model):

    help_parent = "Must select either a Server or a Parent Controller"
    server = models.ForeignKey(
        "envdaq.DAQServer",
        verbose_name=_("DAQ Server"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=help_parent
    )
    parent_controller = models.ForeignKey(
        "envdaq.DAQController",
        verbose_name=_("Parent Controller"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=help_parent
    )

    controller_def = models.ForeignKey(
        "envdaq.ControllerDef", verbose_name=_("Controller"), on_delete=models.CASCADE
    )
    name_help = "Short, descriptive name to be used as id in urls, paths, etc (<b>no whitespace</b>)"
    name = models.CharField(_("Name"), max_length=50, help_text=name_help)
    long_name = models.CharField(_("Long Name"), max_length=100, null=True, blank=True)
    prefix = models.CharField(_("Prefix"), max_length=30, default="default")
    # label_help = "use if using more than one of this type of controller on this server"
    # label = models.CharField(
    #     _("Label"), max_length=50, null=True, blank=True, help_text=label_help
    # )

    namespace = models.CharField(
        _("Namespace"), max_length=100, default=uuid.uuid1
    )
    namespace2  = models.JSONField(_("NamespaceJSON"), blank=True, default=dict)

    component = models.CharField(_("Component Name"), max_length=100, default="default")
    primary_component = models.BooleanField(_("Primary Component"), default=False)
    # component = models.ForeignKey(
    #     "envdaq.ControllerComponent",
    #     verbose_name=_("Component"),
    #     on_delete=models.CASCADE,
    #     blank=True,
    #     null=True,
    #     related_name="controller_components",
    # )
    measurement_sets = models.JSONField(_("Measurement Sets"), blank=True, default=dict)

    class Meta:
        verbose_name = _("DAQ Controller")
        verbose_name_plural = _("DAQ Controllers")

        constraints = [
            models.CheckConstraint(
                check=(
                    Q(server__isnull=False) & 
                    Q(parent_controller__isnull=True)
                ) | (
                    Q(server__isnull=True) & 
                    Q(parent_controller__isnull=False)
                ),
                name='one_and_only_one_parent',
            )
        ]

    def __str__(self):
        parent = "MISSING_PARENT"
        if self.server:
            parent = f"{self.server}"
        elif self.parent_controller:
            parent = f"{self.parent_controller}"

        return f"{parent}-{self.controller_def}-{self.name}"

    def get_absolute_url(self):
        return reverse("DAQController_detail", kwargs={"pk": self.pk})

    def get_config(self):
        config = dict()

        config["ALIAS"] = {
            "name": self.name,
            "prefix": self.prefix
        }
        config["namespace"] = self.get_namespace().to_dict()

        config["CONTROLLER"] = self.controller_def.get_config()

        contconfig = dict()
        contconfig["LABEL"] = self.long_name # ?

        contconfig["component"] = {
            "name": self.component,
            "primary": self.primary_component
        }

        # # add search for child_controllers - not implemented yet
        child_controllers = DAQController.objects.filter(parent_controller=self)
        ch_cont_list = dict()
        ch_cont_map = dict()
        for ch_cont in child_controllers:
            ch_cont_list[ch_cont.name] = ch_cont.get_config()
            if ch_cont.component not in ch_cont_map:
                ch_cont_map[ch_cont.component] = {
                    "LIST": [],
                    "PRIMARY": False
                }
            ch_cont_map[ch_cont.component]["LIST"].append(ch_cont.name)
            ch_cont_map[ch_cont.component]["PRIMARY"] = ch_cont.primary_component
            
        instruments = DAQInstrument.objects.filter(controller=self)
        inst_list = dict()
        inst_map = dict()
        for inst in instruments:
            inst_list[inst.name] = inst.get_config()
            if inst.component not in inst_map:
                inst_map[inst.component] = {
                    "LIST": [],
                    "PRIMARY": None
                }
            inst_map[inst.component]["LIST"].append(inst.name)
            if inst.primary_component:
                inst_map[inst.component]["PRIMARY"] = inst.name
        print(f"inst_map: {inst_map}")
        contconfig["INST_LIST"] = inst_list
        contconfig["INST_MAP"] = inst_map
        contconfig["AUTO_START"] = False
        config["CONTCONFIG"] = contconfig

        return config

    def clean(self):
        cleaned_data = super(DAQController, self).clean()
        print(f'server, parent: {self.server}, {self.parent_controller}')
        if not self.server and not self.parent_controller:
    #     # if not self.cleaned_data.get("server") and not self.cleaned_data.get(
    #     #     "parent_controller"
    #     # ):  # This will check for None or Empty
            raise ValidationError (
                {"Missing Parent": "Server or Parent Controller need to have a value"}
            )
        return cleaned_data

    def save(self, *args, **kwargs):
        self.update_namespace()
        super(DAQController, self).save(*args, **kwargs)

    def get_namespace(self):
        # ns = Namespace(name=self.name, host=self.host, ns_type=Namespace.DAQSERVER)
        if self.server:
            parent_ns = self.server.get_namespace()
        elif self.parent_controller:
            parent_ns = self.parent_controller.get_namespace()
        else:
            return None
        ns = Namespace(name=self.name, ns_type=Namespace.CONTROLLER, parent_ns=parent_ns)
        # print(f"ns::: {ns.to_dict()}")
        return ns

    def update_namespace(self):
        # if self.server:
        #     parent_ns = self.server.namespace
        # elif self.parent_controller:
        #     parent_ns = self.parent_controller.namespace
        # else:
        #     return
        # ns = Namespace(
        #     name=self.name,
        #     ns_type=Namespace.CONTROLLER,
        #     parent_ns=parent_ns,
        # )
        ns = self.get_namespace()
        print(f'ns: {ns.to_dict()}')
        if ns:
            self.namespace = ns.get_namespace()
            self.namespace2 = ns.get_namespace_sig()


class DAQInstrument(models.Model):

    controller = models.ForeignKey(
        "envdaq.DAQController", verbose_name=_("Controller"), on_delete=models.CASCADE
    )
    instrument = models.ForeignKey(
        "envinventory.Instrument",
        verbose_name=_("Instrument"),
        on_delete=models.CASCADE,
    )

    name = models.CharField(_("Name"), max_length=50)
    prefix = models.CharField(_("Prefix"), max_length=20, blank=True, null=True)
    long_name = models.CharField(_("Long Name"), max_length=100, blank=True, null=True)

    namespace = models.CharField(
        _("Namespace"), max_length=100, default=uuid.uuid1
    )

    component = models.CharField(_("Component Name"), max_length=100, default="default")
    primary_component = models.BooleanField(_("Primary Component"), default=False)

    measurement_sets = models.JSONField(_("Measurement Sets"), blank=True, default=dict)

    # # component = models.ForeignKey(
    # #     "envdaq.InstrumentComponent",
    # #     verbose_name=_("Component"),
    # #     on_delete=models.CASCADE,
    # #     blank=True,
    # #     null=True,
    # #     related_name="instrument_components",
    # # )
    # primary_component = models.BooleanField(_("Primary component"), default=True)

    class Meta:
        verbose_name = _("DAQ Instrument")
        verbose_name_plural = _("DAQ Instruments")

    def __str__(self):
        return f"{self.controller}-{self.name}"

    def get_absolute_url(self):
        return reverse("daqinstrument_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        self.update_namespace()
        super(DAQInstrument, self).save(*args, **kwargs)

    def get_namespace(self):
        # ns = Namespace(name=self.name, host=self.host, ns_type=Namespace.DAQSERVER)
        parent_ns = self.controller.get_namespace()
        ns = Namespace(name=self.name, ns_type=Namespace.INSTRUMENT, parent_ns=parent_ns)
        # print(f"ns::: {ns.to_dict()}")
        return ns

    def update_namespace(self):
        ns = self.get_namespace()
        # print(f'ns: {ns.to_dict()}')
        if ns:
            self.namespace = ns.get_namespace()

    def get_config(self):
        config = dict()

        config["ALIAS"] = {
            "name": self.name,
            "prefix": self.prefix
        }
        config["namespace"] = self.get_namespace().to_dict()

        inst_config = self.instrument.get_config()
        config["INSTRUMENT"] = inst_config["INSTRUMENT"]
        # contconfig = dict()
        # contconfig["LABEL"] = self.long_name # ?

        inst_config["INSTCONFIG"]["component"] = {
            "name": self.component,
            "primary": self.primary_component
        }

        # add search for child_controllers - not implemented yet
        # child_controllers = DAQController.objects.filter(parent_controller=self)
        interfaces = InterfaceComponent.objects.filter(instrument=self)
        print(f"interfaces: {interfaces}")
        iface_list = dict()
        for iface in interfaces:
            iface_list[iface.interface.name] = iface.get_config()

        inst_config["INSTCONFIG"]["IFACE_LIST"] = iface_list
        config["INSTCONFIG"] = inst_config["INSTCONFIG"]

        # contconfig["INST_LIST"] = inst_list
        # config["CONTCONFIG"] = contconfig

        return config

        # name:
        #   alias
        #   instrument
        #   instconfig
        #       description
        #       iface_list
        #           ifconfig



# class ControllerComponent(models.Model):

#     parent = models.ForeignKey("envdaq.DAQController", verbose_name=_("Parent Controller"), on_delete=models.CASCADE)
#     component = models.CharField(_("Component Name"), max_length=100, default="default")
#     controller = models.ForeignKey("envdaq.Interface", verbose_name=_("Interface"), on_delete=models.CASCADE)
#     primary = models.BooleanField(_("Primary Component"), default=False)

#     # controller_def = models.ForeignKey(
#     #     "envdaq.ControllerDef",
#     #     verbose_name=_("ControllerDef"),
#     #     on_delete=models.CASCADE,
#     # )
#     # component_type = "Controller"
#     # name = models.CharField(_("Name"), max_length=50)
#     # # primary = models.BooleanField(_("Primary"), default=False)

#     class Meta:
#         verbose_name = _("Controller Component")
#         verbose_name_plural = _("Controller Components")

#     def __str__(self):
#         return f"controller_def-controller-{self.name}"

#     def get_absolute_url(self):
#         return reverse("controllercomponent_detail", kwargs={"pk": self.pk})


# class InstrumentComponent(models.Model):

#     parent = models.ForeignKey("envdaq.DAQController", verbose_name=_("Parent Controller"), on_delete=models.CASCADE)
#     component = models.CharField(_("Component Name"), max_length=100, default="default")
#     controller = models.ForeignKey("envdaq.Interface", verbose_name=_("Interface"), on_delete=models.CASCADE)
#     primary = models.BooleanField(_("Primary Component"), default=False)

#     # controller_def = models.ForeignKey(
#     #     "envdaq.ControllerDef",
#     #     verbose_name=_("ControllerDef"),
#     #     on_delete=models.CASCADE,
#     # )
#     # component_type = "Instrument"
#     # name = models.CharField(_("Name"), max_length=50)
#     # # primary = models.BooleanField(_("Primary"), default=False)

#     class Meta:
#         verbose_name = _("Instrument Component")
#         verbose_name_plural = _("Instrument Components")

#     def __str__(self):
#         return f"controller_def-instrument-{self.name}"

#     def get_absolute_url(self):
#         return reverse("instrumentcomponent_detail", kwargs={"pk": self.pk})


class ControllerDef(models.Model):

    name = models.CharField(max_length=30, help_text="Enter Controller type name")
    _class = models.CharField(max_length=30, help_text="Enter class name")
    _module = models.CharField(max_length=50, help_text="Enter module name")

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="controllerdef_tags",
    )

    component_map = models.TextField("Component Map", default=json.dumps(dict()))

    class Meta:
        verbose_name = "Controller Definition"
        verbose_name_plural = "Controller Definitions"

    def __str__(self):
        """String representation of ControllerDef object. """
        return self.name

    def __repr__(self):
        return f"{self._module}.{self._class}"

    def get_absolute_url(self):
        return reverse("model-detail-view", args=[str(self.id)])

    def update(self, definition):
        # print(f'definition: {definition}')
        if definition and "DEFINITION" in definition:
            self._module = definition["DEFINITION"]["module"]
            self._class = definition["DEFINITION"]["name"]
            try:
                self.component_map = definition["DEFINITION"]["component_map"]
            except KeyError:
                self.component_map = json.dumps(dict())
            print(self.component_map)
            self.save()

    def get_config(self):
        config = {
            "MODULE": self._module,
            "CLASS": self._class
        }
        return config

class Controller(models.Model):

    name = models.CharField(max_length=50)
    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    alias_name = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        # verbose_name = 'DAQ Server
        verbose_name_plural = "Controllers"

    definition = models.ForeignKey(
        "ControllerDef",
        on_delete=models.CASCADE,
        related_name="controllers",
    )

    # uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="controller_tags",
    )

    # instrument_list = get_instruments()

    measurement_config = models.OneToOneField(
        # Configuration,
        "envtags.Configuration",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    def get_instruments(self):

        aliases = InstrumentAlias.objects.filter(controller=self)
        return aliases

    # inst_list = models.ManyToManyField(
    #     'InstrumentEntry',
    #     help_text='Select instruments to control'
    # )

    # inst_class = ManyToManyField(InstrumentClass)

    def __str__(self):
        """String representation of Controller object. """
        return self.alias_name

    def __repr__(self):
        return f"{self.alias_name}.{self.uniqueID}"

    def update_instruments(self, config):
        max_tries = 5
        # print(f'***********update_instruments: {config}')
        if config and ("instrument_meta" in config):
            for name, meta in config["instrument_meta"].items():
                # print(f'name, meta: {name}, {meta}')
                if "alias" not in meta:
                    print(f"alias not defined in {name}...skipping")
                    continue
                # print(f'alias: {meta["alias"]}')
                alias_cfg = meta["alias"]
                # TODO: make this more elegant with some sort of state variable
                #       that tracks while instruments are being configured
                tries = 0
                while tries < max_tries:
                    try:
                        # print(Instrument.objects.all())
                        inst = Instrument.objects.get(
                            definition__name=meta["NAME"],
                            serial_number=meta["SERIAL_NUMBER"],
                        )
                        # print(f'111update_inst: {inst}')

                        try:
                            # print(f"try: {alias_cfg['name']}")
                            alias = InstrumentAlias.objects.get(
                                name=alias_cfg["name"],
                                # label=meta['LABEL'],
                                controller=self,
                            )
                            alias.instrument = inst
                            # print(f'alias: {alias}->{inst}')
                            # alias.prefix = meta_prefix
                            alias.save()
                            tries = max_tries
                        except InstrumentAlias.DoesNotExist:
                            # print(f"create new: {alias_cfg['name']}")
                            alias = InstrumentAlias(
                                name=alias_cfg["name"],
                                label=meta["LABEL"],
                                instrument=inst,
                                controller=self,
                                prefix=alias_cfg["prefix"],
                            )
                            # print(f'alias: {alias}->{inst}')
                            alias.save()
                            tries = max_tries
                    except Instrument.DoesNotExist:
                        tries += 1
                        if tries == max_tries:
                            print(
                                f"Instrument {name} does not exist. "
                                "Can't create alias"
                            )
                        else:
                            print(f"Waiting for instrument db to populate")
                            time.sleep(0.5)
                # pass

    def update_measurements(self, config):
        if config:
            try:
                cfg = Configuration.objects.get(
                    name=(f"{self}_controller_measurement_sets")
                )
                cfg.config = json.dumps(config)
                cfg.save()
                self.measurement_config = cfg
                self.save()

            except Configuration.DoesNotExist:
                # c = config.loads(config)
                # c_json = config.dumps(c)
                cfg = Configuration(
                    name=(f"{self}_controller_measurement_sets"),
                    config=json.dumps(config),
                )
                cfg.save()
                print(f"cfg: {cfg}")
                self.measurement_config = cfg
                self.save()


# InstrumentRepresentation?
# class InstrumentEntry(models.Model):
class InstrumentAlias(models.Model):
    """
    Abstracted representation of an instrument object in Controller.
    InstrumentMask belongs to Controller and is associated with an
    Instrument. The abstraction allows different types of a given
    class/type to be used and changed without changing the data stream for
    the user.
    """

    name = models.CharField(
        max_length=30,
        help_text="Enter the name that describes "
        "what the instrument represents "
        "and can be used as header text (i.e., no spaces)",
    )

    label = models.CharField(
        max_length=30,
        null=True,
        help_text="Label for plots, tables, etc. "
        "A more pleasing version of name. "
        "Defaults to name if left blank",
    )
    controller = models.ForeignKey(
        "Controller",
        on_delete=models.CASCADE,
        related_name="controllers",
    )
    instrument = models.ForeignKey(
        "envinventory.Instrument",
        on_delete=models.CASCADE,
        null=True,
        related_name="instruments",
    )
    prefix = models.CharField(
        max_length=30,
        help_text="Short prefix to add to all "
        "measurements and signals. If blank, will "
        "use <name>",
        null=True,
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="instrumentalias_tags",
    )

    class Meta:
        verbose_name = "Instrument Alias"
        verbose_name_plural = "Instrument Aliases"

    # instrument = models.ForeignKey('Instrument', on_delete=models.CASCADE)

    def __str__(self):
        """String representation of InstrumentMask object. """
        return self.name


class InterfaceDef(models.Model):

    name = models.CharField(max_length=30, help_text="Enter Interface type name")
    _module = models.CharField(max_length=50, help_text="Enter module name")
    _class = models.CharField(max_length=30, help_text="Enter class name")

    interface_types = [
        ("SerialPort", "Serial"),
        ("TCPPort", "TCP"),
        ("I2C", "I2C"),
        ("A2D", "A/D"),
        ("D2A", "D/A"),
        ("GPIO", "GPIO"),
        ("DUMMY", "DUMMY")
    ]
    type = models.CharField(max_length=15, choices=interface_types, default="TCPPort")

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="interfacedef_tags",
    )

    # component_map = models.TextField("Component Map", default=json.dumps(dict()))
    class Meta:
        verbose_name = "Interface Definition"
        verbose_name_plural = "Interface Definitions"

    def __str__(self):
        """String representation of InterfaceDef object. """
        return self.name

    def __repr__(self):
        return f"{self._module}.{self._class}"

    def get_absolute_url(self):
        return reverse("model-detail-view", args=[str(self.id)])

    # def get_config(self):
    #     config = {
    #         "INTERFACE": {
    #             "MODULE": self._module,
    #             "CLASS": self._class
    #         }
    #     }

    #     return ("INTERFACE", config)

    def get_config(self):

        config = {
            "MODULE": self._module,
            "CLASS": self._class
            }

        return (config)


    # def update(self, definition):
    #     # print(f'definition: {definition}')
    #     if definition and 'DEFINITION' in definition:
    #         self._module = definition['DEFINITION']['module']
    #         self._class = definition['DEFINITION']['name']
    #         try:
    #             self.component_map = definition["DEFINITION"]["component_map"]
    #         except KeyError:
    #             self.component_map = json.dumps(dict())
    #         print(self.component_map)
    #         self.save()


class Interface(models.Model):

    name = models.CharField(max_length=50)
    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)
    uri_help_text = "In the form of <em>host</em>:<em>path</em> where host is name or ip address and path is port number, device path, etc"
    uri = models.CharField(
        "URI", max_length=100, default="localhost:10001", help_text=uri_help_text
    )
    # host_name = models.CharField("Host Name", max_length=50, null=True, blank=True)
    # host_ip = models.GenericIPAddressField(
    #     "Host IP", protocol="both", unpack_ipv4=False, null=True, blank=True
    # )
    # alias_name = models.CharField(max_length=50, null=True, blank=True)

    # host_port = models.IntegerField("Host Port", blank=True, null=True)
    # host_path = models.CharField(
    #     "Host Path/Device", max_length=50, null=True, blank=True
    # )

    config = models.JSONField("Configuration", blank=True, default=dict)

    class Meta:
        # verbose_name = 'DAQ Server
        verbose_name_plural = "Interfaces"

    definition = models.ForeignKey(
        "InterfaceDef",
        on_delete=models.CASCADE,
        related_name="interfaces",
    )

    # uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="interface_tags",
    )

    # instrument_list = get_instruments()

    # measurement_config = models.OneToOneField(
    #     # Configuration,
    #     "envtags.Configuration",
    #     null=True,
    #     blank=True,
    #     on_delete=models.CASCADE,
    # )

    # def get_instruments(self):

    #     aliases = InstrumentAlias.objects.filter(controller=self)
    #     return aliases

    # inst_list = models.ManyToManyField(
    #     'InstrumentEntry',
    #     help_text='Select instruments to control'
    # )

    # inst_class = ManyToManyField(InstrumentClass)

    def __str__(self):
        """String representation of Controller object. """
        return self.name

    def __repr__(self):
        return f"{self.name}-{self.uri}"

    def get_config(self):
        config = dict()
        config["INTERFACE"] = self.definition.get_config()
        ifconfig = dict()

        config["IFCONFIG"] = {
            "LABEL": self.name,
            "URI": self.uri,
            # "SERIAL_NUMBER": self.serial_number,
            # "PROPERTY_NUMBER": "NEED_TO_IMPLEMENT"
        }

        return config
        
class InterfaceComponent(models.Model):

    instrument = models.ForeignKey("envdaq.DAQInstrument", verbose_name=_("Instrument"), on_delete=models.CASCADE)
    component = models.CharField(_("Component Name"), max_length=100, default="default")
    interface = models.ForeignKey("envdaq.Interface", verbose_name=_("Interface"), on_delete=models.CASCADE)


    class Meta:
        verbose_name = _("Interface Component")
        verbose_name_plural = _("Interface Components")

    def __str__(self):
        return f"{self.instrument}-{self.component}-{self.interface}"

    def get_absolute_url(self):
        return reverse("interfacecomponent_detail", kwargs={"pk": self.pk})

    def get_config(self):
        config = dict()

        iface_config = self.interface.get_config()
        config["INTERFACE"] = iface_config["INTERFACE"]

        # add component name
        iface_config["IFCONFIG"]["component"] = self.component
        config["IFCONFIG"] = iface_config["IFCONFIG"]

        # config["ALIAS"] = {
        #     "name": self.name,
        #     "prefix": self.prefix
        # }
        # config["namespace"] = self.get_namespace().to_dict()

        # inst_config = self.instrument.get_config()
        # config["INSTRUMENT"] = inst_config["INSTRUMENT"]
        # contconfig = dict()
        # contconfig["LABEL"] = self.long_name # ?

        # add search for child_controllers - not implemented yet
        # child_controllers = DAQController.objects.filter(parent_controller=self)
        # interfaces = Interface.objects.filter(instrument=self)
        # iface_list = dict()
        # for iface in interfaces:
        #     iface_list[iface.interface.name] = iface.get_config()

        # inst_config["INSTCONFIG"]["IFACE_LIST"] = iface_list()
        # config["INSTCONFIG"] = inst_config["INSTCONFIG"]

        # contconfig["INST_LIST"] = inst_list
        # config["CONTCONFIG"] = contconfig

        return config


class Measurement(models.Model):

    name = models.CharField(max_length=20)
    long_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)

    units = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Enter units using UDUnits convention",
    )

    # Tag? Type? _Class? How to classify things?
    # tags = models.ManyToMany('Tag')


class DataCollection(models.Model):
    name = models.CharField(max_length=50)
    name.help_text = "test"
    long_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=300, null=True, blank=True)
    type = None

    # start_time =
    # stop_time =

    # controller_list =

    class Meta:
        abstract = True

    """
    auto generate tag based on type, name, etc to give unique tag for collection
    """

    def create_tag():
        pass


class FieldProject(DataCollection):
    type = "FIELD_PROJECT"

    # sub_projects =

    # platforms =


class Station(DataCollection):
    type = "STATION"

    # location =
    # platform =


class BaseConfig(models.Model):

    name = models.CharField("Name", max_length=50)
    type = None
    config = models.JSONField("JSON Config", blank=True, default=dict)

    class Meta:
        abstract = True
        verbose_name = "baseconfig"
        verbose_name_plural = "baseconfigs"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("configuration_detail", kwargs={"pk": self.pk})

    def get_id(self):
        """
        Return a hash string used as key for a given config

        Return:
            string | None
        """

        id = None
        if self.config:
            try:
                # ensure best id by sorting keys
                # cfg = self.config
                # print(f'type: {type(self.config)}')
                input = json.dumps(self.config, sort_keys=True)
                # # input = json.dumps(self.config, sort_keys=True)
                m = hashlib.md5(input.encode("utf-8"))
                id = m.hexdigest()
            except TypeError as e:
                print(f"unable to hash config: {e}")
                # return None

            return id

    def verify_same_by_id(self, comp_id):

        id = self.get_id()
        if comp_id and id:
            return comp_id == id
        return False

    def verify_same(self, comp_config):

        if comp_config:
            return self.verify_same_by_id(comp_config.get_id())

        return False


class DAQServerConfig(BaseConfig):

    type = "DAQServerConfig"
    options = models.JSONField("Options", blank=True, default=dict)

    class Meta:
        verbose_name = "DAQServerConfig"
        verbose_name_plural = "DAQServerConfigs"

    def __str__(self):
        return f"{self.type}-{self.name}"

    def get_absolute_url(self):
        return reverse("daqserverconfig_detail", kwargs={"pk": self.pk})
