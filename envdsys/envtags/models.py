from django.db import models

# Create your models here.


# TODO: This may eventually be replaced by taggit or some other 3rd party app
class Tag(models.Model):

    name = models.CharField(max_length=30)
    type = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        default=None,
    )

    def __str__(self):
        return self.name
