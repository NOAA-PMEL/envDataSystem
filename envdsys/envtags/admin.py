from django.contrib import admin

# Register your models here.
from envtags.models import Tag, Configuration


admin.site.register(Tag)
admin.site.register(Configuration)
