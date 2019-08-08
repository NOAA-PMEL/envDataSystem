from django.db import models
from envcontacts.models import Person, Organization
from envtags.models import Tag
import uuid
# Create your models here.


class InventoryDef(models.Model):

    name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    # TODO: Do I need an InventoryType? Instrument, Building, Platform, IT, etc?
    # inv_type = models.ManyToManyField('InventoryType', on_delete=models.SET_NULL)

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='inv_tags',
    )

    mfg = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # size, weight, cost
    length = models.CharField(
        max_length=20,
        help_text='Enter dimensional length (m)',
        null=True,
        blank=True,

    )
    width = models.CharField(
        max_length=20,
        help_text='Enter dimensional width (m)',
        null=True,
        blank=True,

    )
    height = models.CharField(
        max_length=20,
        help_text='Enter dimensional height (m)',
        null=True,
        blank=True,

    )

    weight = models.CharField(
        max_length=20,
        help_text='Enter weight (kg)',
        null=True,
        blank=True,

    )

    value = models.CharField(
        max_length=20,
        help_text='Enter value (USD)',
        null=True,
        blank=True,

    )

    class Meta():
        abstract = True

# class InventoryType(models.Model):
#
#     name = models.CharField(max_length=30)


class Inventory(models.Model):

    owner = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    contacts = models.ManyToManyField(
        Person,
        blank=True,
    )

    # Location will eventually be a model
    # location = models.CharField(max_length=100)

    class Meta():
        abstract = True


# Base class for Instrument, InterfaceDevice, Samplers? and ??
# class DeviceDef(models.Model):

class InstrumentDef(InventoryDef):

    model = models.CharField(
        max_length=50,
        help_text='Instrument model',
        # null=True,
        # blank=True
    )
    _class = models.CharField(
        max_length=30,
        help_text='Enter class name',
        null=True,
        blank=True
    )
    _module = models.CharField(
        max_length=100,
        help_text='Enter module name',
        null=True,
        blank=True
    )

    type = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'type': 'INSTRUMENT_TYPE'},
        related_name='inst_type'
    )
    # meas_list = models.ManyToManyField('Measurement', on_delete=models.SET_NULL)
    # measurements = models.ManyToManyField('Measurement')

    class Meta():
        verbose_name = 'Instrument Definition'
        verbose_name_plural = 'Instrument Definitions '

    def __str__(self):
        '''String representation of InstrumentDef object. '''
        return (f'{self.name} : {self.model}')

    # def __repr__(self):
    #     return (f'{self.manufacturer} : {self.model}')

    def update(self, definition):
        print(f'InstrumentDef.definition: {definition}')
        if definition and 'DEFINITION' in definition:
            self._module = definition['DEFINITION']['module']
            self._class = definition['DEFINITION']['name']
            # self.mfg = definition['DEFINITION']['mfg']
            self.model = definition['DEFINITION']['model']
            self.save()
            if 'tags' in definition['DEFINITION']:
                self.update_tags(definition['DEFINITION']['tags'])
            # self.save()

    def update_tags(self, tag_names):

        for tag_name in tag_names:
            print(f'tag_name: {tag_name}')
            try:
                tag = Tag.objects.get(name=tag_name)
            except Tag.DoesNotExist:
                tag = Tag(name=tag_name)
                tag.save()
            print(tag)
            self.tags.add(tag)

        self.save()
        print(f'instrumentdef: {self}')


class Instrument(Inventory):
    # name = models.CharField(max_length=30, help_text="Enter name for this instrument")
    nickname = models.CharField(max_length=50, null=True, default=None)
    definition = models.ForeignKey(
        'InstrumentDef',
        on_delete=models.CASCADE,
        # null=True,
        # blank=True
    )
    uniqueID = models.UUIDField(
        default=uuid.uuid1, editable=False, null=True, blank=True)
    # inst_list = models.ManyToManyField('Instrument', 'Select insruments to control')
    serial_number = models.CharField(
        max_length=30,
        help_text='Enter serial number',
        default='NA',
        null=True,
        blank=True)

    # quick and dirty test
    AVAILIBILITY_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('IN_USE', 'In use'),
        ('ON_LOAN', 'Out on loan'),
        ('MAINTENANCE', 'Out for maintenance')
    )
    status = models.CharField(
        max_length=20,
        choices=AVAILIBILITY_CHOICES,
        default='MAINTENANCE'
    )
    # inst_status = choices(MAINTENANCE, ON_LOAN, AVAILABLE, IN_USE)

    def __str__(self):
        '''String representation of Controller object. '''
        return (f'{self.definition} : {self.serial_number}')

    # def __repr__(self):
    #     return (f'{self.serial_number}_{self.uniqueID}')

#     type_text = models.CharField(max_length=100)
#     mfg_text = models.CharField(max_length=100)
#     sn_text = models.CharField(max_length=100)
#     signature_text = models.CharField(max_length=200)


# class Measurement(models.Model):
#
#     name = models.CharField(max_length=20)
#     long_name = models.CharField(max_length=100, null=True, blank=True)
#     description = models.CharField(max_length=100,null=True, blank=True)
#
#     units = models.CharField(
#         max_length=20,
#         null=True,
#         blank=True,
#         help_text='Enter units using UDUnits convention',
#     )

    # Tag? Type? _Class? How to classify things?
    # tags = models.ManyToMany('Tag')
