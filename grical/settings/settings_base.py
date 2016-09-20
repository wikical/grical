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
import sys

PROGRAM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# specific GridCalendar settings {{{1
# =============================================================================

# Stop using the write database. When True, users cannot enter/modify data
READ_ONLY = os.path.exists(os.path.join(PROGRAM_DIR, "READ_ONLY"))

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

# generate version number from hg tip
try:
    from subprocess import Popen, PIPE
    proc = Popen(
            'cd %s ; hg tip --template ".{rev} {date|isodate}"' % PROGRAM_DIR,
            shell = True, stdin = PIPE, stdout = PIPE )
    tip = proc.communicate()[0]
except:
    tip = ""
from grical import VERSION as GRICAL_VERSION
VERSION = '.'.join((str(x) for x in GRICAL_VERSION)) + tip

# used to generate the PROID field of iCalendars, see
# http://tools.ietf.org/html/rfc5545
PRODID = '-//GridMind//NONSGML GridCalendar ' + VERSION + '//EN'

# imap settings for getting events as emails
IMAP_SERVER = ''
IMAP_LOGIN = ''
IMAP_PASSWD = ''
IMAP_SSL = False

# used for messages sent. You can set it to None to avoid emails having the
# header reply-to
REPLY_TO = None

EMAIL_HOST = 'localhost'
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# GeoIP, GEONAME and django-countries settings {{{1
# =============================================================================
# see # http://docs.djangoproject.com/en/dev/ref/contrib/gis/geoip/

GEOIP_PATH = '/usr/share/GeoIP'
GEONAMES_URL = 'http://api.geonames.org/'
GEONAMES_USERNAME = 'demo'

# Default value for distance unit, possible values are: 'km' and 'mi'
DISTANCE_UNIT_DEFAULT = 'km' # alternative: 'mi'

# events within this radius of the center of city are considered to be in the
# city. DISTANCE_UNIT_DEFAULT is the unit.
CITY_RADIUS = 50

# =============================================================================
# auth settings {{{1
# =============================================================================

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/a/accounts/login/'
LOGOUT_URL = '/a/accounts/logout/'
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-failure-view
CSRF_FAILURE_VIEW = 'grical.accounts.views.csrf_failure'

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
# application and middleware settings {{{1
# =============================================================================

# at the end additional applications are conditionaly added
INSTALLED_APPS = [
    'grical.accounts',
    'grical.data',
    'grical.events',
    'django.contrib.sites',
    'registration',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django_comments',
    'django.contrib.gis',
    'django_tables2',
    'grical.tagging',
    'reversion',
    'markup_deprecated', # used for rendering ReStructuredText
    'grical.contact_form',
    'oembed',
]

# at the end additional middleware are conditionaly added
MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    # NOTE next middleware not used because in events.views.edit_event (among
    # other places) sometimes we create many revisions.
    # 'reversion.middleware.RevisionMiddleware',
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
""" https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-MESSAGE_STORAGE """

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
""" https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-SESSION_ENGINE """

# =============================================================================
# TEMPLATES {{{1
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["/grical/templates",
                    os.path.join( PROGRAM_DIR, "templates"), ],
            # Put strings here, like "/home/html/django_templates" or
            # "C:/www/django/templates". Always use forward slashes,
            # even on Windows.  Don't forget to use absolute paths,
            # not relative paths. """
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.i18n',
                'django.core.context_processors.media',
                'django.core.context_processors.request',
                'django.core.context_processors.static',
                'grical.context_processors.global_template_vars',
            ],
        },
    },
]

# =============================================================================
# CACHE {{{1
# =============================================================================

TESTS_RUNNING = len(sys.argv) > 1 and sys.argv[1] in ('test', 'jenkins')

if TESTS_RUNNING:
    # Speed up tests, inspired on:
    # http://www.daveoncode.com/2013/09/23/effective-tdd-tricks-to-speed-up-django-tests-up-to-10x-faster/
    PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.MD5PasswordHasher',)

if TESTS_RUNNING:
    INSTALLED_APPS = INSTALLED_APPS + ['django.contrib.sessions',
            'grical.tagging.tests']


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
# Static files {{{1
# =============================================================================

STATIC_URL = "/m/"
STATIC_ROOT = ""
STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'compressor.finders.CompressorFinder',)

# IMPORTANT: If more than one dir, set the main grica static dir first in
# order for some development and testing functions to work properly
STATICFILES_DIRS = [os.path.join(PROGRAM_DIR, "static"), ]

# =============================================================================
# LOGGING {{{1
# =============================================================================

LOGGING = {
    "loggers": {
        "": {
            "level": "DEBUG",
            "propagate": False,
            "handlers": ["console", ],
        },
    },
    "handlers": {
        "console": {
            "formatter": "verbose",
            "class": "logging.StreamHandler",
            "level": "DEBUG",
        },
    },
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
}

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
ROOT_URLCONF = 'grical.urls'

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
    ( u'city', u'city' ),               # city
    ( u'town', u'city' ),
    ( u'country', u'country' ),         # country
    ( u'state', u'country' ),
    ( u'address', u'address' ),         # address ,
    ( u',', u'address' ),
    ( u'ad', u'address' ),
    ( u'addr', u'address' ),
    ( u'street', u'address' ),
    ( u'exact', u'exact' ),             # exact
    ( u'exact coordinates', u'exact' ),
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
