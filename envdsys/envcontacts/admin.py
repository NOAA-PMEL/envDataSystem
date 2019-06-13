from django.contrib import admin

# Register your models here.
from envcontacts.models import Person, Organization


admin.site.register(Person)
admin.site.register(Organization)
