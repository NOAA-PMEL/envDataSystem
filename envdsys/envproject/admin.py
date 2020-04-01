from django.contrib import admin

# Register your models here.
from envproject.models import Project, ProjectEvent  # , Configuration
from envproject.models import ProjectPlatformEvent, Platform
from envtags.models import Tag
# from envtags.models import Tag  #, Configuration


class EnvprojectAdmin(admin.ModelAdmin):
    # readonly_fields = ('get_tags', 'uniqueID')
    readonly_fields = ('uniqueID', 'event_type')
    # list_display = ('get_tags',)
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'start_datetime',
                'stop_datetime',
                'long_name',
                'description',
                'website',
                'logo',
                'platforms',
                # 'tags',
                # 'event_type',
                # 'uniqueID'
            )
        }),
        ('Extra', {
            'classes': ('collapse', ),
            'fields': ('tags', 'event_type', 'uniqueID')
        }),
    )

    def save_related(self, request, form, formsets, change):
        
        super().save_related(request, form, formsets, change)
        
        project = form.instance
        # try:
        #     tag = Tag.objects.get(name=project.name)
        #     project.tags.add(tag)
        #     # if tag not in self.tags.all():
        #     #     self.tags.add(tag)
        #     print('tag not in')
        #     #     self.save()
        #     #     print(f'tag = {tag}, tags = {self.tags.all()}')
        # except Tag.DoesNotExist:
        #     tag = Tag(name=self.name)
        #     tag.save()
        #     project.tags.add(tag)
        #     print('tag does not exist')
        #     # self.save()
        #     # print(f'tag = {tag}, tags = {self.tags.all()}')
        # print(f'project tags: {project.tags.all()}')
        project.save()

        # return super().save_related(request, form, formsets, change)


admin.site.register(Project, EnvprojectAdmin)
admin.site.register(ProjectEvent)
admin.site.register(ProjectPlatformEvent)
admin.site.register(Platform)
