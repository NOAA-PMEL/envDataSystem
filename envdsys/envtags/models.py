from django.db import models
import uuid
import json

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


class Configuration(models.Model):
    name = models.CharField(max_length=50)
    uniqueID = models.UUIDField(default=uuid.uuid1, editable=False)
    config = models.TextField(editable=True, null=True)

    def set_config(self, config):
        '''
        set config using dictionary
        '''
        if config is None:
            return ''

        entry = dict()
        entry['NAME'] = self.name

        try:
            entry['ENVDAQ'] = json.dumps(config)
            # json_config = json.dumps(config)
            # config = json.dumps(d)
        except ValueError:
            print('Error decoding config')
            entry['NAME'] = ''
        # entry = dict()
        # entry["NAME"] = self.name
        # entry["ENVDAQ"] = d
        self.config = json.dumps(entry)
        self.save()

    def set_config_json(self, json_config):

        if json_config is None:
            return ''

        try:
            config = json.loads()
        except ValueError:
            return ''

        self.set_config(config)

    def get_config(self):

        try:
            config = json.loads(self.config)
        except ValueError:
            print('Error decoding json config')
            config = ''
        # print(json_config)
        return config

    def get_config_json(self):
        return json.dumps(self.get_config())

    def __str__(self):
        '''String representation of Controller object. '''
        return self.name

    def __repr__(self):
        return (f'{self.name}.{self.uniqueID}')
