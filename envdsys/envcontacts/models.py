from django.db import models

# Create your models here.

class Contact(models.Model):

    street_address = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    city = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )
    state = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )
    postal_code = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    country = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )

    website = models.URLField(null=True, blank=True)

    class Meta():
        abstract = True


class Person(Contact):

    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)

    organization = models.ForeignKey(
        'envcontacts.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    MOBILE = 'M'
    HOME = 'H'
    WORK = 'W'
    OTHER = 'O'
    PHONE_TYPE_CHOICES = {
        (MOBILE, 'Mobile'),
        (HOME, 'Home'),
        (WORK, 'Work'),
        (OTHER, 'Other'),
    }
    phone1 = models.CharField(max_length=15, null=True, blank=True)
    phone1_type = models.CharField(
        max_length=1,
        choices=PHONE_TYPE_CHOICES,
        default=MOBILE,
    )
    phone2 = models.CharField(max_length=15, null=True, blank=True)
    phone2_type = models.CharField(
        max_length=1,
        choices=PHONE_TYPE_CHOICES,
        default=MOBILE,
    )

    EMAIL_TYPE_CHOICES = {
        (HOME, 'Home'),
        (WORK, 'Work'),
        (OTHER, 'Other'),
    }
    email1 = models.EmailField(null=True, blank=True)
    email1_type = models.CharField(
        max_length=1,
        choices=EMAIL_TYPE_CHOICES,
        default=WORK,
    )
    email2 = models.EmailField(null=True, blank=True)
    email2_type = models.CharField(
        max_length=1,
        choices=EMAIL_TYPE_CHOICES,
        default=WORK,
    )

    class Meta():
        verbose_name_plural='People'

    def __str__(self):
        name = ''
        if self.last_name is not None:
            name = self.last_name
            if self.first_name is not None:
                name += ', ' + self.first_name
        elif self.first_name is not None:
            name = self.first_name

        return name

class Organization(Contact):

    name = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text='Enter short name for labels and ID',
        )
    long_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Enter full name of organization',
    )

    parent_org = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    MOBILE = 'M'
    HOME = 'H'
    WORK = 'W'
    OTHER = 'O'
    PHONE_TYPE_CHOICES = {
        (MOBILE, 'Mobile'),
        (HOME, 'Home'),
        (WORK, 'Work'),
        (OTHER, 'Other'),
    }
    phone = models.CharField(max_length=15, null=True, blank=True)

    email = models.EmailField(null=True, blank=True)

    def __str__(self):

        if self.name is not None:
            return self.name
        elif self.long_name is not None:
            return self.long_name

        return 'empty'



# class Organization(models.Model):
#
#     name = models.CharField(
#         max_length=50,
#     )
#
#     address = models.CharField(
#         max_length=100,
#         null=True,
#         blank=True,
#     )
#
#     website = models.URLField(null=True, blank=True)
#
#     phone = models.CharField(max_length=20, null=True, blank=True)
#
#     def __str__(self):
#         '''String representation of Organization object. '''
#         return self.name
#
#
# # class Manufacturer(Organization):
# #     pass
# #     # contacts from Person
# #
# #     # def __str__(self):
# #     #     '''String representation of Manufacturer object. '''
# #     #     return self.name
#
#
# # can we attach this to User?
# class Person(models.Model):
#
#     first_name = models.CharField(max_length=20)
#     last_name = models.CharField(max_length=20)
#
#     email = models.EmailField(null=True, blank=True)
#     phone = models.CharField(max_length=20)
#
#     class Meta:
#         verbose_name_plural = "People"
#
#     affiliation = models.ForeignKey(
#         'Organization',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True
#     )
#
#     def __str__(self):
#         '''String representation of Person object. '''
#         return f'{self.last_name},{self.first_name}'
