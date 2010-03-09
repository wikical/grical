import os

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/a/accounts/login/'
LOGOUT_URL = '/a/accounts/logout/'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "context_processors.global_template_vars",
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

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/m/'

ADMIN_MEDIA_PREFIX = '/m/admin/'

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

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, "templates"),
)

INSTALLED_APPS = (
    'gridcal',
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
#    'dilla',
)

GEOIP_PATH = '/usr/share/GeoIP/'

try:
    from settings_local import *
except ImportError:
    pass

