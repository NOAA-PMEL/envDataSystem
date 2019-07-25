from django.db import models
from django.urls import reverse
import uuid
from django.apps import apps
import json


# Create your models here.
class Configuration(models.Model):
    name = models.CharField(max_length=50)
    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)
    config = models.TextField(editable=True, null=True)

    def set_config(self, config):
        '''
        set config using dictionary
        '''
        if config is None:
            return ''

        entry = dict()
        entry['NAME'] = self.name

        try:
            entry['ENVDAQ'] = json.dumps(config)
            # json_config = json.dumps(config)
            # config = json.dumps(d)
        except ValueError:
            print('Error decoding config')
            entry['NAME'] = ''
        # entry = dict()
        # entry["NAME"] = self.name
        # entry["ENVDAQ"] = d
        self.config = json.dumps(entry)
        self.save()

    def set_config_json(self, json_config):
        
        if json_config is None:
            return ''

        try:
            config = json.loads()
        except ValueError:
            return ''
        
        self.set_config(config)

    def get_config(self):

        try:
            config = json.loads(self.config)
        except ValueError:
            print('Error decoding json config')
            config = ''
        # print(json_config)
        return config

    def get_config_json(self):
        return json.dumps(self.get_config())

    def __str__(self):
        '''String representation of Controller object. '''
        return self.name

    def __repr__(self):
        return (f'{self.name}.{self.uniqueID}')  


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

    name = models.CharField(max_length=50)
    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    class Meta:
        verbose_name = 'DAQ Server'
        verbose_name_plural = 'DAQ Servers'

    host = models.CharField(max_length=30, null=True)
    ip_address = models.GenericIPAddressField(null=True)
    port = models.IntegerField(null=True)

    configuration = models.ForeignKey(
        'Configuration',
        on_delete=models.CASCADE,
        related_name='configurations',
        null=True
    )

    # controller list : this will be on the controller side

    def __str__(self):
        '''String representation of Controller object. '''
        return self.name

    def __repr__(self):
        return (f'{self.name}.{self.uniqueID}')  

class ControllerDef(models.Model):

    name = models.CharField(max_length=30, help_text='Enter Controller type name')
    _class = models.CharField(max_length=30, help_text='Enter class name')
    _module = models.CharField(max_length=50, help_text='Enter module name')

    class Meta:
        verbose_name = 'Controller Definition'
        verbose_name_plural = 'Controller Definitions'

    def __str__(self):
        '''String representation of ControllerDef object. '''
        return self.name

    def __repr__(self):
        return (f'{self._module}.{self._class}')

    def get_absolute_url(self):
        return reverse('model-detail-view', args=[str(self.id)])


class Controller(models.Model):

    name = models.CharField(max_length=50)
    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    class Meta:
        # verbose_name = 'DAQ Server
        verbose_name_plural = 'Controllers'

    definition = models.ForeignKey(
        'ControllerDef',
        on_delete=models.CASCADE,
        related_name='controllers',
    )

    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)
    # inst_list = models.ManyToManyField(
    #     'InstrumentEntry',
    #     help_text='Select instruments to control'
    # )

    # inst_class = ManyToManyField(InstrumentClass)

    def __str__(self):
        '''String representation of Controller object. '''
        return self.name

    def __repr__(self):
        return (f'{self.name}.{self.uniqueID}')


# InstrumentRepresentation?
# class InstrumentEntry(models.Model):
class InstrumentMask(models.Model):
    '''
    Abstracted representation of an instrument object in Controller.
    InstrumentEntry belongs to Controller and is associated with an
    Instrument. The abstraction allows different types of a given
    class/type to be used and changed without changing the data stream for
    the user.
    '''

    name = models.CharField(
        max_length=30,
        help_text='Enter the name that describes what the instrument represents'
    )
    controller = models.ForeignKey(
        'Controller',
        on_delete=models.CASCADE,
        related_name='controllers',
    )
    instrument = models.ForeignKey(
        'envinventory.Instrument',
        on_delete=models.CASCADE,
        null=True,
        related_name='instruments',
    )
    # instrument = models.ForeignKey('Instrument', on_delete=models.CASCADE)

    def __str__(self):
        '''String representation of InstrumentMask object. '''
        return self.name


class Measurement(models.Model):

    name = models.CharField(max_length=20)
    long_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=100,null=True, blank=True)

    units = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='Enter units using UDUnits convention',
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

    '''
    auto generate tag based on type, name, etc to give unique tag for collection
    '''
    def create_tag():
        pass

class FieldProject(DataCollection):
    type = 'FIELD_PROJECT'

    # sub_projects = 

    # platforms = 


class Station(DataCollection):
    type = 'STATION'

    # location =
    # platform =

