#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
#############################################################################
# Copyright 2009-2011 Ivan Villanueva <ivan ät gridmind.org>
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

# See how settings_local.py should look like at the end of this file
try:
    from settings_local import * # pylint: disable-msg=W0401,W0614
except ImportError:
    pass # TODO: check that the whole thing is runable without settings_local

try:
    DEBUG
except NameError:
    DEBUG = False

# =============================================================================
# specific GridCalendar settings {{{1
# =============================================================================

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

# =============================================================================
# GeoIP and GEONAME settings {{{1
# =============================================================================
# see # http://docs.djangoproject.com/en/dev/ref/contrib/gis/geoip/

GEOIP_PATH = '/usr/share/GeoIP'
try:
    GEONAMES_URL
except NameError:
    GEONAMES_URL = 'http://api.geonames.org/'
try:
    GEONAMES_USERNAME
except NameError:
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

try:
    SHORT_DATETIME_FORMAT
except NameError:
    SHORT_DATETIME_FORMAT = 'Y-m-d H:i'
try:
    SHORT_DATE_FORMAT
except NameError:
    SHORT_DATE_FORMAT = 'Y-m-d'
try:
    TIME_FORMAT
except NameError:
    TIME_FORMAT = 'H:i'
try:
    DATE_FORMAT
except NameError:
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
)
if DEBUG:
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware', )
MIDDLEWARE_CLASSES += (
    # see http://docs.djangoproject.com/en/1.2/ref/contrib/csrf/
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
if DEBUG:
    MIDDLEWARE_CLASSES += (
        'gridcalendar.middlewares.ProfileMiddleware', )

# see http://docs.djangoproject.com/en/1.3/ref/contrib/messages/
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

# https://docs.djangoproject.com/en/dev/topics/http/sessions/
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# used by python-django-debug-toolbar
if DEBUG:
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        # 'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel', # shows passwords !!!
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
    )

    # don't show the toolbar if the profiler
    #   gridcalendar.middlewares.ProfileMiddleware
    # is used, which happens when adding ?profile=1 to the request
    def custom_show_toolbar(request):
        if request.REQUEST.get('profile', False):
            return False
        return True

    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
        #'EXTRA_SIGNALS': ['myproject.signals.MySignal'],
        'HIDE_DJANGO_SQL': True,
        #'TAG': 'div',
    }

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

if DEBUG:
    # List of callables that know how to import templates from various sources.
    # without the cached loader:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.load_template_source',
        'django.template.loaders.app_directories.load_template_source',
    )
else:
    # for the cached loader all tags must be thread-safe, see
    # http://docs.djangoproject.com/en/dev/howto/custom-template-tags/#template-tag-thread-safety
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
if DEBUG:
    CACHES['default']['KEY_PREFIX'] = 'debug'
else:
    CACHES['default']['KEY_PREFIX'] = 'production'

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

# see http://docs.djangoproject.com/en/1.2/ref/settings/#append-slash
APPEND_SLASH = True

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
try:
    TIME_ZONE
except NameError:
    TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
try:
    LANGUAGE_CODE
except NameError:
    LANGUAGE_CODE = 'en-us'

try:
    LANGUAGES
except NameError:
    LANGUAGES = ( ( 'en', 'English' ), )

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# TODO: use USE_L10N
# see http://docs.djangoproject.com/en/dev/ref/settings/?from=olddocs#use-l10n
# Notice also that when set to True, settings like TIME_FORMAT are not used
USE_L10N = False

# This is used by the django.contrib.sites, which is needed by for instance the
# registration code we are using from a Debian package (upstream is:
# http://bitbucket.org/ubernostrum/django-registration/wiki/Home )
try:
    SITE_ID
except NameError:
    SITE_ID = 1

# Absolute path to the directory that holds media.
try:
    MEDIA_ROOT
except NameError:
    MEDIA_ROOT = os.path.join( PROJECT_ROOT, "media" )

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
try:
    MEDIA_URL
except NameError:
    MEDIA_URL = '/m/'

try:
    ADMIN_MEDIA_PREFIX
except NameError:
    ADMIN_MEDIA_PREFIX = '/m/admin/'

try:
    ROOT_URLCONF
except NameError:
    ROOT_URLCONF = 'urls'

try:
    REPLY_TO
except NameError:
    REPLY_TO = None

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
    ( u'country', u'country' ),         # country \
    ( u'\\', u'country' ),
    ( u'co', u'country' ),
    ( u'coun', u'country' ),
    ( u'nation', u'country' ),
    ( u'nati', u'country' ),
    ( u'na', u'country' ),
    ( u'city', u'city' ),               # city /
    ( u'/', u'city' ),
    ( u'ci', u'city' ),
    ( u'town', u'city' ),
    ( u'to', u'city' ),
    ( u'postcode', u'postcode' ),       # postcode .
    ( u'.', u'postcode' ),
    ( u'po', u'postcode' ),
    ( u'zip', u'postcode' ),
    ( u'zi', u'postcode' ),
    ( u'code', u'postcode' ),
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
