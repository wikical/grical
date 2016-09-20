DEBUG = True

from settings_base import *

SECRET_KEY = 'fiwj{34gj90gjdsg.s9t8t9sggejis0e94gjsd4#&bkd;k4lg$'

DATABASES = {
    # PostgreSQL settings
    # 'default': {
    #      'ENGINE': 'django.contrib.gis.db.backends.postgis',
    #      'ATOMIC_REQUESTS': True,
    #      'NAME': 'grical_db',
    #      'USER': 'grical_user',
    #      'PASSWORD': 'grical_password',
    #      'HOST': 'localhost',
    #      'PORT': 5432
    #  }
    #  sqlite3/spatialite settings
    'default': {
         'ENGINE': 'django.contrib.gis.db.backends.spatialite',
         'ATOMIC_REQUESTS': True,
         'NAME': os.path.join(os.path.dirname(PROGRAM_DIR), 'grical_db.sql'),
     }
}

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'

if DEBUG:
    # Won't show if not INTERNAL_IPS defined
    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2", "10.0.3.1", ]
    INSTALLED_APPS.insert(0, 'debug_toolbar')

if not DEBUG:
    for TEMPLATE in TEMPLATES:
        # When setting custom loaders setting, APP_DIRS should be False
        # or else exception will raise. See:
        # https://docs.djangoproject.com/en/1.8/ref/templates/api/
        TEMPLATE['APP_DIRS'] = False
        TEMPLATE['OPTIONS']['debug'] = False
        # https://docs.djangoproject.com/en/1.8/ref/templates/api/#django.template.loaders.cached.Loader
        TEMPLATE['OPTIONS']['loaders'] = [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ]

# This is to not flood console with DEBUG and INFO messages while running tests
# or in production
if (not DEBUG or TESTS_RUNNING) and 'handlers' in LOGGING and 'console' in LOGGING['handlers']:
    LOGGING['handlers']['console']['level'] = 'WARNING'
if (not DEBUG or TESTS_RUNNING) and 'loggers' in LOGGING and '' in LOGGING['loggers']:
    LOGGING['loggers']['']['level'] = 'WARNING'

# ======================================================================
# imap settings for getting events as emails
# ======================================================================

IMAP_SERVER = 'localhost'
IMAP_LOGIN = ''
IMAP_PASSWD = ''
IMAP_PORT = 993
IMAP_SSL = True

# =============================================================================
# celery
# =============================================================================

CELERY_APP = 'grical'

CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
"""
Read http://docs.celeryproject.org/en/latest/faq.html#isn-t-using-pickle-a-security-concern

Because we are passing instances in celery tasks we cannot avoid using
pickle. However we must ensure that our transporter (db / cache /
broker) is securely isolated and potential attackers cannot access
them.

"""
CELERY_TASK_SERIALIZER = 'pickle'
"""
See above
"""

CELERYD_TASK_TIME_LIMIT = 300
""" Something long enough for the tasks to complete. """

CELERY_IGNORE_RESULT = True
""" http://celery.readthedocs.org/en/latest/configuration.html#celery-ignore-result"""

CELERYD_TASK_SOFT_TIME_LIMIT = CELERYD_TASK_TIME_LIMIT * 0.9
""" This should be something less than CELERYD_TASK_TIME_LIMIT. Importers use
this value to stop importing and preparing next run. """
assert CELERYD_TASK_SOFT_TIME_LIMIT < CELERYD_TASK_TIME_LIMIT

# Following is useful for development, it can be totally omitted in production.

if TESTS_RUNNING or DEBUG:
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    BROKER_BACKEND = 'memory'
    BROKER_URL = 'django://'

# TODO: Confirm if these settings are useful for production / RabbitMQ as
# broker, most probably the configuration is done in celery configuration /
# daemon
# BROKER_HOST = "localhost"
# BROKER_PORT = 5672
# BROKER_USER = "guest"
# BROKER_PASSWORD = "guest"
# BROKER_VHOST = "/"

# ======================================================================
# geonames settings
# ======================================================================

# This is used for getting the coordinates from a location using the API of
# GeoNames.org. You need to register here http://www.geonames.org/login and
# then activate the use of the API in your account.
GEONAMES_USERNAME = 'ogai'
GEONAMES_URL = 'https://secure.geonames.net/'

# ======================================================================
# email and error-notify settings
# ======================================================================

# IMPORTANT FIXME
# Bellow are production settings for grical.org, they should leave from
# settings-example.py and kept elsewhere

ADMINS = (
	('stefanos', 'stefanos@gridmind.org'),
	('ivan', 'ivan@gridmind.org'),
)

MANAGERS = ADMINS

# used for messages sent. You can set it to None to avoid emails having the
# header reply-to
REPLY_TO = 'office@gridmind.org'

DEFAULT_FROM_EMAIL = 'noreply@grical.org'
SERVER_EMAIL = 'noreply@grical.org'
EMAIL_SUBJECT_PREFIX = '[GriCal.org]'

# FIXME IMPORTANT
# Following are production values for grical.org and prove to work, remove from
# example
# EMAIL_HOST = '136.243.175.225'
# EMAIL_HOST_USER = 'email_gridmind_org'
# EMAIL_HOST_PASSWORD = 'veeWae4y'
# EMAIL_USE_TLS = True
# EMAIL_PORT = 587

# old:
#EMAIL_HOST = 'alpha.gridmind.org'
#EMAIL_PORT = 25
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_USE_TLS = False
