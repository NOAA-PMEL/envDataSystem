# Django : Transfer data from Sqlite to another database
[source](https://www.shubhamdipt.com/blog/django-transfer-data-from-sqlite-to-another-database/)

In order to achieve that, do the following steps in order :
- python manage.py dumpdata > db.json
- Change the database settings to new database such as of MySQL / PostgreSQL.
- python manage.py migrate
- python manage.py shell 
- Enter the following in the shell
  - from django.contrib.contenttypes.models import ContentType
  - ContentType.objects.all().delete()
- python manage.py loaddata db.json
