from django.db import models
# from django.urls import reverse
import uuid
from envtags.models import Tag
from envproject.utilities.event import BaseEvent

# Create your models here.


class Platform(models.Model):

    name = models.CharField(max_length=50)
    long_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    platform_id = models.CharField(
        verbose_name='Identifier',
        max_length=20,
        default='default_id'
    )

    parent_platform = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    website = models.URLField(
        verbose_name='Platform Website',
        blank=True,
        null=True
    )

    # logo = models.ImageField(
    #     verbose_name='Logo Image',
    #     upload_to='projects/',
    #     blank=True,
    #     null=True
    # )

    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)

    class Meta:
        # verbose_name = 'DAQ Server
        verbose_name_plural = 'Platforms'

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='platform_tags',
    )

    # instrument_list = get_instruments()

    # def get_instruments(self):

    #     aliases = InstrumentAlias.objects.filter(
    #         controller=self
    #     )
    #     return aliases

    # inst_list = models.ManyToManyField(
    #     'InstrumentEntry',
    #     help_text='Select instruments to control'
    # )

    # inst_class = ManyToManyField(InstrumentClass)

    def __str__(self):
        '''String representation of Platform object. '''
        return self.name

    def __repr__(self):
        return (f'{self.name} ({self.platform_id})')


# class Project(models.Model):
class Project(BaseEvent):

    # override name field to change verbose name
    name = models.CharField(
        verbose_name='Short Name / Acronym',
        max_length=20,
        # blank=True
    )

    long_name = models.CharField(
        verbose_name='Long Name',
        max_length=200,
        blank=True
    )

    description = models.TextField(blank=True)

    event_type = 'PROJECT'

    website = models.URLField(
        verbose_name='Project Website',
        blank=True,
        null=True
    )

    logo = models.ImageField(
        verbose_name='Logo Image',
        upload_to='projects/',
        blank=True,
        null=True
    )

    platforms = models.ManyToManyField(
        Platform,
        blank=True,
        # related_name='event_tags',
        related_name='project_platforms',
    )

    class Meta:
        # verbose_name = 'DAQ Server
        verbose_name_plural = 'Projects'

    def get_tags(self):
        # tag_list = ''
        # for t in self.tags.all():
        #     tag_list += t + '; '
        return self.tags.all()

    def add_self_tag(self):

        try:
            tag = Tag.objects.get(name=self.name)
            if tag not in self.tags.all():
                self.tags.add(tag)
                # print('tag not in')
                # self.save()
                # print(f'tag = {tag}, tags = {self.tags.all()}')
        except Tag.DoesNotExist:
            tag = Tag(name=self.name)
            tag.save()
            self.tags.add(tag)
            # print('tag does not exist')
            # self.save()
            # print(f'tag = {tag}, tags = {self.tags.all()}')

    def save(self,  *args, **kwargs):

        super(Project, self).save(*args, **kwargs)

        self.add_self_tag()

    def __str__(self):
        '''String representation of Controller object. '''
        return self.name

    def __repr__(self):
        return (f'{self.name} ({self.long_name})')


class ProjectEvent(BaseEvent):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='projectevent_projects',
    )

    description = models.TextField(blank=True)

    def __str__(self):
        '''String representation of ProjectEvent object. '''
        return (f'{self.project.name}-{self.name}')

    def __repr__(self):
        return (f'{self.project}-{self.name}')


class ProjectPlatformEvent(BaseEvent):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='projectplatformevent_projects',
    )

    # this will be changed to ForeignKey
    # platform = models.CharField(
    #     max_length=50,
    #     null=True,
    #     blank=True
    # )
    # platform = models.ForeignKey(
    #     Platform,
    #     on_delete=models.CASCADE,
    #     related_name='projectplatformevent_platform',
    # )

    platforms = models.ManyToManyField(
        Platform,
        blank=True,
        # null=True,
        # related_name='event_tags',
        related_name='projectplatformevent_platforms',
    )

    description = models.TextField(blank=True)

    def __str__(self):
        '''String representation of ProjectPlatformEvent object. '''
        return (f'{self.project.name}-{self.name}')

    def __repr__(self):
        pforms = ''
        for p in self.platforms.all():
            if pforms == '':
                pforms += f'{p}'
            else:
                pforms += f',{p}'
        return (f'{self.project}-{pforms}-{self.name}')


# class ProjectDataSource(models.Model):

    # Project
    # Platform
    # Organization
    # Controller ??
