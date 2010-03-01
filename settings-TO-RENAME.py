# Django settings for gridcalendar project.
import os

dirname = os.path.dirname(globals()["__file__"])

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # !!!!!! REPLACE WITH YOUR USERNAME AND EMAIL !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    ('ogai', 'django@example.com'),
)

MANAGERS = ADMINS

# see http://docs.djangoproject.com/en/dev/howto/error-reporting/
SEND_BROKEN_LINK_EMAILS = True

DATABASE_ENGINE   = 'postgresql_psycopg2'  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME     = 'gridcalendar'         # DB Name (or path to database file if using sqlite3)
DATABASE_USER     = 'gridcalendar'         # Not used with sqlite3.
# !!!!!! replace with the DB password !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
DATABASE_PASSWORD = 'the_password'         # Not used with sqlite3.
DATABASE_HOST     = 'localhost'            # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT     = ''                     # Set to empty string for default. Not used with sqlite3.

# !!!!!! replace !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEFAULT_FROM_EMAIL = 'noreply@example.com'

LOGIN_REDIRECT_URL = '/'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "gridcalendar.context_processors.global_template_vars",
)

# for tagging application
# see http://django-tagging.googlecode.com/svn/trunk/docs/overview.txt
FORCE_LOWERCASE_TAGS = True

# for the registration application
ACCOUNT_ACTIVATION_DAYS = 10

# for RSS feeds
FEED_SIZE = 10

MAX_EVENTS_ON_ROOT_PAGE=20

DATE_FORMAT = 'Y-m-d'

INTERNAL_IPS = ('127.0.0.1',)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# This is used by the django.contrib.sites, which is needed by for instance the registration code we
# are using from a Debian package (upstream is:
# http://bitbucket.org/ubernostrum/django-registration/wiki/Home )
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
#MEDIA_ROOT = '/usr/local/django-projects/gridcalendar/'
MEDIA_ROOT = os.path.join(dirname, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = 'http://gridcalendar.net/media/'
MEDIA_URL = '/m/'

ADMIN_MEDIA_PREFIX = '/m/admin/'

# Make this unique, and don't share it with anybody.
# !!!!!!!!! REPLACE !!!!!!!!!!!!!!
SECRET_KEY = '(%3a@o3(oaz@1**0o8qaw$zkij7apd)i84mvau2_f2daa1lk+u'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'gridcalendar.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
	os.path.join(dirname, "templates"),
)

INSTALLED_APPS = (
    'gridcalendar.events',
    'gridcalendar.groups',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
#    'django.contrib.gis',
    'django.contrib.databrowse',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'tagging',
    'registration',
    'debug_toolbar',
)

GEOIP_PATH = '/usr/share/GeoIP/'
