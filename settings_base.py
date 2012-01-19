#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
#############################################################################
# Copyright 2009-2011 Ivan Villanueva <ivan ät gridmind.org>
# Copyright 2012      Antonis Christofides <anthony ät itia.ntua.gr>
#
# This file is part of GridCalendar.
#
# GridCalendar is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

""" Django configuration file """

# imports {{{1
import os
import djcelery

DEBUG = False

# =============================================================================
# specific GridCalendar settings {{{1
# =============================================================================

# Stop using the write database. When True, users cannot enter/modify data
READ_ONLY = os.path.exists(os.path.join(PROJECT_ROOT, "READ_ONLY"))

# limits for number of events/dates
DEFAULT_LIMIT = 50
VIEWS_MAX_LIMITS = {
    'map': 10,
    'calendars': 100,
}
# for RSS feeds
FEED_SIZE = DEFAULT_LIMIT

# dates thereafter from now are not allowed
MAX_DAYS_IN_FUTURE = 1095 # 3 years: 365 * 3

DEFAULT_RECURRING_DURATION_IN_DAYS = 365
assert ( DEFAULT_RECURRING_DURATION_IN_DAYS <= MAX_DAYS_IN_FUTURE )
# TODO: inform the user who introduced the event that recurring events are
# going to expire before it happens

# TODO: use a user parameter and a button to show the next ones
MAX_EVENTS_ON_ROOT_PAGE = 20

# used to generate the PROID field of iCalendars, see
# http://tools.ietf.org/html/rfc5545
PRODID = '-//GridMind//NONSGML GridCalendar ' + VERSION + '//EN'

REPLY_TO = None

# generate version number from hg tip
try:
    proc = Popen(
            'cd %s ; hg tip --template ".{rev} {date|isodate}"' % PROJECT_ROOT,
            shell = True, stdin = PIPE, stdout = PIPE )
    tip = proc.communicate()[0]
except:
    tip = ""
VERSION = '0.9' + tip

# =============================================================================
# GeoIP, GEONAME and django-countries settings {{{1
# =============================================================================
# see # http://docs.djangoproject.com/en/dev/ref/contrib/gis/geoip/

GEOIP_PATH = '/usr/share/GeoIP'
GEONAMES_URL = 'http://api.geonames.org/'
GEONAMES_USERNAME = 'demo'

# =============================================================================
# test settings {{{1
# =============================================================================

TEST_CHARSET = 'utf-8'

# =============================================================================
# charset settings {{{1
# =============================================================================

DEFAULT_CHARSET = 'utf-8'

# =============================================================================
# auth settings {{{1
# =============================================================================

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/a/accounts/login/'
LOGOUT_URL = '/a/accounts/logout/'
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-failure-view
CSRF_FAILURE_VIEW = 'accounts.views.csrf_failure'

# =============================================================================
# localization settings {{{1
# =============================================================================

SHORT_DATETIME_FORMAT = 'Y-m-d H:i'
SHORT_DATE_FORMAT = 'Y-m-d'
TIME_FORMAT = 'H:i'
DATE_FORMAT = 'Y-m-d D'

# =============================================================================
# for the tagging application {{{1
# =============================================================================
# see http://django-tagging.googlecode.com/svn/trunk/docs/overview.txt

FORCE_LOWERCASE_TAGS = True

# =============================================================================
# for the registration application {{{1
# =============================================================================

ACCOUNT_ACTIVATION_DAYS = 10

# =============================================================================
# reporting {{{1
# =============================================================================

# see http://docs.djangoproject.com/en/dev/howto/error-reporting/
SEND_BROKEN_LINK_EMAILS = True

# =============================================================================
# application and middleware settings {{{1
# =============================================================================

# at the end additional applications are conditionaly added
INSTALLED_APPS = (
    'gridcalendar.accounts',
    'gridcalendar.data',
    'gridcalendar.events',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.databrowse',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'django.contrib.gis',
    'tagging',
    'registration',
    'reversion',
    'django.contrib.markup', # used for rendering ReStructuredText
    'contact_form',
    'djcelery',
    'oembed',
 )
if DEBUG:
    INSTALLED_APPS = ( 'debug_toolbar', ) + INSTALLED_APPS

# at the end additional middleware are conditionaly added
MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # NOTE: everything below the TransactionMiddleware is managed by it ,with
    # the exception of CacheMiddleware, UpdateCacheMiddleware, and
    # FetchFromCacheMiddleware; as explained in the Dajngo documentation:
    # https://docs.djangoproject.com/en/1.3/topics/db/transactions/
    'django.middleware.transaction.TransactionMiddleware',
    # NOTE next middleware not used because in events.views.edit_event (among
    # other places) sometimes we create many revisions.
    # 'reversion.middleware.RevisionMiddleware',
 )

# see http://docs.djangoproject.com/en/1.3/ref/contrib/messages/
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

# https://docs.djangoproject.com/en/dev/topics/http/sessions/
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'context_processors.global_template_vars',
 )
# http://docs.djangoproject.com/en/dev/ref/templates/api/#django-core-context-processors-debug
#if DEBUG:
#    TEMPLATE_CONTEXT_PROCESSORS += ( "django.core.context_processors.debug", )

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join( PROJECT_ROOT, "templates" ),
 )

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

# =============================================================================
# CACHE {{{1
# =============================================================================

CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
            'TIMEOUT': 300, # 5 minutes
            'KEY_PREFIX': 'production',
        }, #TODO: use also the hot spare server
        'db': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache',
            'TIMEOUT': 60*60*24*31, # 31 days
            'OPTIONS': {
                'MAX_ENTRIES': 100000
            },
        },
}

# =============================================================================
# celery
# =============================================================================

# http://django-celery.readthedocs.org/en/latest/getting-started/first-steps-with-django.html
# TODO: create a proper user for production
djcelery.setup_loader()
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"
# TODO: documentation says that a Django DB can be used instead of RabbitMQ as
# message-broker[1], but although tables are created for django-celery after
# syncdb command, the connection-error [2] is fixed after installing RabiitMQ.
# Ask in the ml or irc
# [1] http://django-celery.readthedocs.org/en/latest/introduction.html
# [2] http://stackoverflow.com/questions/7483728/django-celery-consumer-connection-error-111-when-running-python-manage-py-cel

# =============================================================================
# i18n and url settings {{{1
# =============================================================================

APPEND_SLASH = True
TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'en-us'
LANGUAGES = ( ( 'en', 'English' ), )
USE_I18N = True
USE_L10N = False

SITE_ID = 1
MEDIA_ROOT = os.path.join( PROJECT_ROOT, "media" )
MEDIA_URL = '/m/'
ADMIN_MEDIA_PREFIX = '/m/admin/'
ROOT_URLCONF = 'urls'

# field names and synonyms/translations {{{1
SYNONYMS = (
    ( u'title', u'title' ),             # title `
    ( u'`', u'title' ),
    ( u'ti', u'title' ),
    ( u'titl', u'title' ),
    ( u'startdate', u'startdate' ),             # startdate [
    ( u'start', u'startdate' ),
    ( u'[', u'startdate' ),
    ( u'st', u'startdate' ),
    ( u'starts', u'startdate' ),
    ( u'date', u'startdate' ),
    ( u'da', u'startdate' ),
    ( u'start date', u'startdate' ),
    ( u'start-date', u'startdate' ),
    ( u'start_date', u'startdate' ),
    ( u'sd', u'startdate' ),
    ( u'starttime', u'starttime' ),     # starttime {
    ( u'{', u'starttime' ),
    ( u'time', u'starttime' ),
    ( u'start_time', u'starttime' ),
    ( u'start time', u'starttime' ),
    ( u'startime', u'starttime' ),
    ( u'endtime', u'endtime' ),         # endtime }
    ( u'}', u'endtime' ),
    ( u'end_time', u'endtime' ),
    ( u'end time', u'endtime' ),
    ( u'tags', u'tags' ),               # tags #
    ( u'#', u'tags' ),
    ( u'ta', u'tags' ),
    ( u'tag', u'tags' ),
    ( u'subjects', u'tags' ),
    ( u'subject', u'tags' ),
    ( u'su', u'tags' ),
    ( u'subj', u'tags' ),
    ( u'enddate', u'enddate' ),                 # enddate ]
    ( u'end', u'enddate' ),
    ( u']', u'enddate' ),
    ( u'en', u'enddate' ),
    ( u'ends', u'enddate' ),
    ( u'finish', u'enddate' ),
    ( u'finishes', u'enddate' ),
    ( u'fi', u'enddate' ),
    ( u'end date', u'enddate' ),
    ( u'end-date', u'enddate' ),
    ( u'end_date', u'enddate' ),
    ( u'ed', u'enddate' ),
    ( u'endd', u'enddate' ),
    ( u'timezone', u'timezone' ),         # timezone ^
    ( u'tz', u'timezone' ),
    ( u'acronym', u'acronym' ),         # acronym ^
    ( u'^', u'acronym' ),
    ( u'ac', u'acronym' ),
    ( u'acro', u'acronym' ),
    ( u'address', u'address' ),         # address ,
    ( u',', u'address' ),
    ( u'ad', u'address' ),
    ( u'addr', u'address' ),
    ( u'street', u'address' ),
    ( u'coordinates', u'coordinates' ), # coordinates |
    ( u'|', u'coordinates' ),
    ( u'point', u'coordinates' ),
    ( u'points', u'coordinates' ),
    ( u'coordinate', u'coordinates' ),
    ( u'coor', u'coordinates' ),
    ( u'coo', u'coordinates' ),
    ( u'position', u'coordinates' ),
    ( u'description', u'description' ), # description %
    ( u'%', u'description' ),
    ( u'de', u'description' ),
    ( u'desc', u'description' ),
    ( u'des', u'description' ),
    ( u'info', u'description' ),
    ( u'infos', u'description' ),
    ( u'in', u'description' ),
    ( u'urls', u'urls' ),               # urls _ (*)
    ( u'_', u'urls' ),
    ( u'ur', u'urls' ),
    ( u'url', u'urls' ),
    ( u'web', u'urls' ),
    ( u'webs', u'urls' ),
    ( u'we', u'urls' ),
    ( u'dates', u'dates' ),             # dates ; (*)
    ( u'deadlines', u'dates' ),
    ( u';', u'dates' ),
    ( u'deadline', u'dates' ),
    ( u'dl', u'dates' ),
    ( u'ds', u'dates' ),
    ( u'sessions', u'sessions' ),       # sessions ? (*),
    ( u'?', u'sessions' ),
    ( u'se', u'sessions' ),
    ( u'session', u'sessions' ),
    ( u'recurrences', u'recurrences' ),     # recurrences : (*),
    ( u':', u'recurrences' ),
    ( u'recurring', u'recurrences' ),
    ( u'recurrings', u'recurrences' ),
    ( u'clone', u'recurrences' ),
    ( u'clones', u'recurrences' ),
    ( u'repetition', u'recurrences' ),
    ( u'repetitions', u'recurrences' ),
)
# (*) can have multi-lines and are not simple text fields
# TODO: add all translations available
