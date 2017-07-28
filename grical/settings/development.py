#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2016 Stefanos Kozanis <stefanos ät wikical.com>
#
# This file is part of GriCal.
#
# GriCal is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# GriCal is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GriCal. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

# Set to False for production
DEBUG = True

from settings_base import *

SECRET_KEY = 'fiwj{34gj90gjdsg.s9t8t9sggejis0e94gjsd4#&bkd;k4lg$'

DATABASES = {
    # PostgreSQL settings for production
    # 'default': {
    #      'ENGINE': 'django.contrib.gis.db.backends.postgis',
    #      'ATOMIC_REQUESTS': True,
    #      'NAME': 'grical',
    #      'USER': 'grical',
    #      'PASSWORD': 'grical_password',
    #      'HOST': 'localhost',
    #      'PORT': 5432
    #  }
    #  sqlite3/spatialite settings for development
    'default': {
         'ENGINE': 'django.contrib.gis.db.backends.spatialite',
         'ATOMIC_REQUESTS': True,
         'NAME': os.path.join(os.path.dirname(PROGRAM_DIR), 'grical_db.sql'),
     }
}

if 'spatialite' in DATABASES['default']['ENGINE']:
    import platform
    if platform.dist()[2] in ('yakkety', 'xenial', 'wily'):
        # https://docs.djangoproject.com/en/1.10/ref/contrib/gis/install/spatialite/#installing-spatialite
        # It looks that this also applies to Django 1.8. For Ubuntu 14.04 following
        # line is not required
        SPATIALITE_LIBRARY_PATH = 'mod_spatialite'

if DEBUG:
    # debug toolabr won't show if not INTERNAL_IPS defined
    INTERNAL_IPS = ["127.0.0.1", "10.0.2.2", "10.0.3.1", ]
    INSTALLED_APPS.insert(0, 'debug_toolbar')
    MIDDLEWARE_CLASSES.append(
            'debug_toolbar.middleware.DebugToolbarMiddleware')

if not DEBUG:
    # Set cached template loaders for production
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
LOG_LEVEL = 'DEBUG'
if TESTS_RUNNING:
    LOG_LEVEL = 'WARNING'
elif not DEBUG:
    LOG_LEVEL = 'INFO'
if (not DEBUG or TESTS_RUNNING) and 'handlers' in LOGGING and 'console' in LOGGING['handlers']:
    LOGGING['handlers']['console']['level'] = LOG_LEVEL
if (not DEBUG or TESTS_RUNNING) and 'loggers' in LOGGING and '' in LOGGING['loggers']:
    LOGGING['loggers']['']['level'] = LOG_LEVEL

# =============================================================================
# imap settings for events submission by email
# =============================================================================

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

if TESTS_RUNNING or DEBUG:
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    BROKER_BACKEND = 'memory'
    BROKER_URL = 'django://'


# =============================================================================
# CACHE {{{1
# =============================================================================

# Following settings suitable for development:
CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        },
        "db": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
    }

# Following settings suitable for production:
# CACHES = {
#         'default': {
#             'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#             'LOCATION': '127.0.0.1:11211',
#             'TIMEOUT': 300, # 5 minutes
#             'KEY_PREFIX': 'production',
#         },
#         'db': {
#             'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
#             'LOCATION': 'cache',
#             'TIMEOUT': 60*60*24*31, # 31 days
#             'OPTIONS': {
#                 'MAX_ENTRIES': 100000
#             },
#         },
# }


# ======================================================================
# geonames settings
# ======================================================================

# This is used for getting the coordinates from a location using the API of
# GeoNames.org. You need to register here http://www.geonames.org/login and
# then activate the use of the API in your account.
GEONAMES_USERNAME = 'demo'
GEONAMES_URL = 'https://secure.geonames.net/'

# ======================================================================
# email and error-notify settings
# ======================================================================

ADMINS = (
	('admin1', 'admin1@example.com'),
	('admin2', 'admin2@example.com'),
)

MANAGERS = ADMINS

# used for messages sent. You can set it to None to avoid emails having the
# header reply-to
REPLY_TO = 'office@example.com'

DEFAULT_FROM_EMAIL = 'noreply@example.com'
SERVER_EMAIL = 'noreply@example.com'
EMAIL_SUBJECT_PREFIX = '[Example.com]'

# Set email backend to SMTP when in production:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Set also SMTP settings for production
# EMAIL_HOST = ''
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''
# EMAIL_USE_TLS = True
# EMAIL_PORT = 587
