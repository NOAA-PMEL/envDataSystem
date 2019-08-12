from django.db import models
from envtags.models import Tag


class DimensionDef(models.Model):
    name = models.CharField(max_length=50)
    time_dim = models.BooleanField(default=False)
    has_length = False
    unlimited_dim = models.BooleanField(default=False)
    length = models.PositiveSmallIntegerField(default=0)
    units = models.CharField(max_length=20, null=True)

    def set_unlimited(self, is_unlimited):
        self.unlimited_dim = is_unlimited
        self.has_length = not is_unlimited
        self.length = 0

    def set_length(self, length):
        if length > 0:
            self.has_length = True
            self.is_unlimited = False
            self.length = length
        else:
            self.set_unlimited(True)

# class Dimension(models.Model):


# Create your models here.
class VariableDef(models.Model):

    name = models.CharField(max_length=50)
    long_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    # TODO: Make units a class using cf/udunits
    units = models.CharField(max_length=20, null=True)
    source_type = models.CharField(max_length=30, null=True)
  
    data_type_choices = [('NUMERIC', 'NUMERIC'), ('TEXT', 'TEXT')]
    data_type = models.CharField(
        max_length=7,
        choices=data_type_choices,
        default='NUMERIC'
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='variable_tags',
    )

    def __str__(self):
        '''String representation of VariableDef object. '''
        return (f'{self.name} : {self.units}')

    # def __repr__(self):
    #     return (f'{self.manufacturer} : {self.model}')
