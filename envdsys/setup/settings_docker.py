"""
Django settings for envdsys project.

Generated by 'django-admin startproject' using Django 2.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = 'ji^o9qts3b6*2k47hu25zs!#0@(h$l9)i%ly(ct&0p29e#g!vp'


"""
Changed to generate/store SECRET_KEY locally following:
https://gist.github.com/ndarville/3452907
but has been modified to use newer functionality

This solution creates a file that stores the secret in a local file. If
your installation does not have persistent storage there is a solution that
utilizes an environment variable at the above link.
"""

try:
    SECRET_KEY
except NameError:
    # SECRET_FILE = os.path.join(BASE_DIR, 'secret.txt')
    SECRET_FILE = os.path.join(BASE_DIR, 'config', 'secret.txt')
    try:
        SECRET_KEY = open(SECRET_FILE).read().strip()
    except IOError:
        try:
            from django.core.management.utils import get_random_secret_key
            SECRET_KEY = get_random_secret_key()
            secret = open(SECRET_FILE, 'w')
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception('Please create a %s file with random characters \
            to generate your secret key!' % SECRET_FILE)


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ["ENVDSYS_UI_ALLOWED_HOSTS"].split(",")
# ALLOWED_HOSTS = [
#     'localhost',
#     '127.0.0.1',
# ]


# Application definition

INSTALLED_APPS = [
    # 'envdaq.apps.EnvdaqConfig',
    'channels',
    'envnet.apps.EnvnetConfig',
    'envdaq.apps.EnvdaqConfig',
    'envcontacts.apps.EnvcontactsConfig',
    'envinventory.apps.EnvinventoryConfig',
    'envtags.apps.EnvtagsConfig',
    'envdata.apps.EnvdataConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'envdsys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        #'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
           ],
        },
    },
]

WSGI_APPLICATION = 'envdsys.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         'NAME': os.path.join(BASE_DIR, 'db', 'db.sqlite3'),
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db', # set in docker-compose.yml
        # 'HOST': '127.0.0.1', # set in docker-compose.yml
        'PORT': 5432 # default postgres port
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    # 'path_to_static_directory/static/',
]

# STATIC_URL = '/static/'
STATIC_URL = '/staticfiles/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# use something like below for production server
# -------
# STATIC_URL = '/staticfiles/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# -------

# mysite/settings.py
# Channels
# ASGI_APPLICATION = 'envdsys.routing.application'
ASGI_APPLICATION = 'envdsys.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
            # "hosts": [('127.0.0.1', 6379)],
            # in case you run into over capacity errors
            # 'capacity': 1500,  # added due to over capacity bug
            # 'expiry': 10,      # workaround
        },
    },
}

DEFAULT_AUTO_FIELD='django.db.models.AutoField'

# Plot Server settings..use this?
# PLOT_SERVER = {
#     'server_id': ('localhost', 5001),
#     # 'default': {
#     #     'CONFIG': {
#     #         "hosts": [('localhost', 18001)]
#     #     }
#     # }
# }

# Plot Server settings..use this?
PLOT_SERVER = {
    'server_id': ('0.0.0.0', 5001, 'default'), # old default
    'hostname': os.environ["ENVDSYS_PLOT_SERVER_HOSTNAME"],
    'host': 'localhost',
    'ports': "5001:5011",  # allows for 10 servers
    'namespace': 'default' # default namespace
    #'server_id': ('10.55.169.61', 5001),
    # 'server_id': ('192.168.86.32', 5001),
    # 'default': {
    #     'CONFIG': {
    #         "hosts": [('localhost', 18001)]
    #     }
    # }
}

# Configure DataManager
#   ui_save_base_path: where UI Server will save data from daq_server(s). Make
#                       sure this is not the same as the daq_server folder if
#                       running on same host
#   ui_save_data: whether UI Server should save data (Default: False)
DATA_MANAGER = {
    'ui_save_base_path': '/data/envDataSystem/UIServer',
    'ui_save_data': os.environ["ENVDSYS_UI_DATA_SAVE"],
}
