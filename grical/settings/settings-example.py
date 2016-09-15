DEBUG = False

from settings_base import *

SECRET_KEY = 'fiwj{34gj90gjdsg.s9t8t9sggejis0e94gjsd4#&bkd;k4lg$'

DATABASES = {
    'default': {
         'ENGINE': 'django.contrib.gis.db.backends.postgis',
         'ATOMIC_REQUESTS': True,
         'NAME': 'grical_db',
         'USER': 'grical_user',
         'PASSWORD': 'grical_password',
         'HOST': 'localhost',
         'PORT': 5432
     }
}

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

# ======================================================================
# imap settings for getting events as emails
# ======================================================================

IMAP_SERVER = 'localhost'
IMAP_LOGIN = ''
IMAP_PASSWD = ''
IMAP_PORT = 993
IMAP_SSL = True

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

EMAIL_HOST = '136.243.175.225'
EMAIL_HOST_USER = 'email_gridmind_org'
EMAIL_HOST_PASSWORD = 'veeWae4y'
EMAIL_USE_TLS = True
EMAIL_PORT = 587

# old:
#EMAIL_HOST = 'alpha.gridmind.org'
#EMAIL_PORT = 25
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_USE_TLS = False
