from settings_base import *

DEBUG = False
TEMPLATE_DEBUG = False
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
# debug settings
# ======================================================================

TEMPLATE_DEBUG = DEBUG

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

# see http://docs.djangoproject.com/en/dev/howto/error-reporting/
SEND_BROKEN_LINK_EMAILS = True

# ======================================================================
# LOG PIPE
# ======================================================================

# If this value is not False, events changes will be logged to this pipe
# Make sure it is writtable
LOG_PIPE = '/tmp/gricallogpipe'
# LOG_PIPE = False
# the group id. Should be group id of the proccess running Django
LOG_PIPE_GID = 33

# ======================================================================
# IRC
# ======================================================================

# to log events changes ( see LOG_PIPE ) to a IRC channel, run the script
# irclogger.py

IRC_NETWORK = 'irc.freenode.net'
IRC_PORT = 6667
IRC_CHANNEL = '#gridcalendar'
IRC_NICK = 'gricalrobot'
IRC_NAME = 'grical.org log robot'
