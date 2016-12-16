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

""" Django configuration file """

# imports {{{1
import os
import sys

PROGRAM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================
# specific Grical settings {{{1
# =============================================================================

# Stop using the write database. When True, users cannot enter/modify data
READ_ONLY = os.path.exists(os.path.join(PROGRAM_DIR, "READ_ONLY"))
"""
If ``True``, Grical works in read only mode, i.e. no new
events can be added and existing events cannot be edited. This can
be useful in emergencies, for example when your server is
overloaded. By default, it is set to ``True`` if a file named
READ_ONLY exists in the Grical program directory.
"""

# limits for number of events/dates
DEFAULT_LIMIT = 50
VIEWS_MAX_LIMITS = {
    'map': 10,
    'calendars': 100,
}
# for RSS feeds
FEED_SIZE = DEFAULT_LIMIT
"""
When a user searches for events, results are paginated, and
:data:`DEFAULT_LIMIT` events are shown on each page. The user can
specify pagination with fewer (but not more) events on each page.
The default for :data:`DEFAULT_LIMIT` is 50.

Different limits can be specified for different view modes using
:data:`VIEWS_MAX_LIMITS`. For example, to set a default limit of 40
for table and 20 for map::

  VIEWS_MAX_LIMITS = {
     'table': 40,
     'map': 20,
  }

For view modes for which :data:`VIEWS_MAX_LIMITS` does not specify
anything, :data:`DEFAULT_LIMIT` is used. The default for
:data:`VIEWS_MAX_LIMITS` is 10 for map, 100 for calendars.

:data:`MAX_EVENTS_ON_ROOT_PAGE` is the same for the root page. The
default is 20.

Finally, FEED_SIZE is the limit for feeds. The default is 50.
"""

# dates thereafter from now are not allowed
MAX_DAYS_IN_FUTURE = 1095 # 3 years: 365 * 3
"""
It is allowed to specify dates only up to this number of days in
the future. The default is 1095, or 3 years.
"""

DEFAULT_RECURRING_DURATION_IN_DAYS = 365
"""
When defining recurrent events, the user selects the days on a
calendar displayed. This setting specifies how long that calendar
is, in days from the start of the event. The default is 365.
"""
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
PRODID = '-//GridMind//NONSGML Grical ' + VERSION + '//EN'
"""
When exporting to iCalendar format, this setting specifies the
PRODID, the identifier of the product that created the object. See
RFC5545_ for details. The default is
:samp:`-//GridMind//NONSGML Grical {XXXX}//EN`, where
*XXXX* the Grical version.
"""

# imap settings for getting events as emails
IMAP_SERVER = ''
IMAP_LOGIN = ''
IMAP_PASSWD = ''
IMAP_SSL = False
"""
In Grical new events can be created by email. These emails
must arrive at an IMAP account, to which Grical logs on and
reads the emails. These settings specify the IMAP account
information. There is no default.
"""

# used for messages sent. You can set it to None to avoid emails having the
# header reply-to
REPLY_TO = None
"""
When automatically sending emails, the Django DEFAULT_FROM_EMAIL_
setting is used as the sender; :data:`REPLY_TO` can be used to
specify a Reply-To address. The default is ``None``, which means no
Reply-To header will be added.
"""

EMAIL_HOST = 'localhost'
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# GeoIP, GEONAME and django-countries settings {{{1
# =============================================================================
# see # http://docs.djangoproject.com/en/dev/ref/contrib/gis/geoip/

GEOIP_PATH = '/usr/share/GeoIP'
"""
The directory where the GeoIP databases are installed. The default
is :file:`/usr/share/GeoIP`.
"""
GEONAMES_URL = 'http://api.geonames.org/'
GEONAMES_USERNAME = 'demo'
"""
The Geonames_ database can find names of locations given their
co-ordinates. You can create an account on Geonames and set these
settings to access the database. In that case, you should also
configure your Geonames account to accept a passwordless login from
the IP of your Grical server. Grical will then use
these settings to logon to Geonames. The default
:data:`GEONAMES_URL` is http://api.geonames.org/, and the default
:data:`GEONAMES_USERNAME` is "demo".
"""

# Default value for distance unit, possible values are: 'km' and 'mi'
DISTANCE_UNIT_DEFAULT = 'km' # alternative: 'mi'
"""The default unit of distance; can be km or mi. The default is km."""

# events within this radius of the center of city are considered to be in the
# city. DISTANCE_UNIT_DEFAULT is the unit.
CITY_RADIUS = 50
"""
Events within this radius from the center of the city are
considered to be in the city. The unit is
:data:`DISTANCE_UNIT_DEFAULT`. The default is 50.
"""

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
    'compressor',
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
"""
A list of event model attribute synonyms that can be used when
submitting events by email or in text format. For example, the
title of the event can be specified as :samp:`title: {your event's
title}`, but also "ti", "titl" and "`" can be used in place of
"title". See the default definition of :data:`SYNONYMS` in
:file:`settings_base.py` for more information.
"""
# (*) can have multi-lines and are not simple text fields
# TODO: add all translations available
