from django.db import models
from django.urls import reverse
import uuid
from django.apps import apps


# Create your models here.

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

    name = models.CharField(max_length=30, help_text="Enter name for this controller")
    definition = models.ForeignKey(
        'ControllerDef',
        on_delete=models.CASCADE,
        related_name='controllers',
    )

    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)
    # inst_list = models.ManyToManyField('InstrumentEntry', help_text='Select instruments to control')

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
