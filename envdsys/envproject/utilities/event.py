from django.db import models
from envtags.models import Tag
import uuid
from django.utils.timezone import now


class BaseEvent(models.Model):

    name = models.CharField(
        # verbose_name='Event Name',
        max_length=50,
        # blank=True
    )

    event_type = 'GENERIC'

    # description = models.TextField(blank=True)

    start_datetime = models.DateTimeField(
        verbose_name='Start DateTime',
        default=now,
        # null=True,
        # blank=True
    )
    stop_datetime = models.DateTimeField(
        verbose_name='Stop DateTime',
        null=True,
        blank=True
    )

    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        # related_name='event_tags',
        related_name='%(app_label)s_%(class)s_related',
        related_query_name="%(app_label)s_%(class)ss",
    )

    class Meta:
        abstract = True
