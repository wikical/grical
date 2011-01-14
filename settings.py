#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Django configuration file """
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009, 2010 Ivan Villanueva <ivan ät gridmind.org>
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

import os

# See how settings_local.py should look like at the end of this file
try:
    from settings_local import * # pylint: disable-msg=W0401,W0614
except ImportError:
    pass # FIXME: check that the whole thing is runable without settings_local

try:
    DEBUG
except NameError:
    DEBUG = False

# =============================================================================
# specific GridCalendar settings
# =============================================================================

# for RSS feeds
FEED_SIZE = 50

# TODO: use a user parameter and a button to show the next ones
MAX_EVENTS_ON_ROOT_PAGE = 20

# used to generate the PROID field of iCalendars, see
# http://tools.ietf.org/html/rfc5545
PRODID =  '-//GridMind//NONSGML GridCalendar ' + VERSION + '//EN'

# =============================================================================
# GeoIP settings, see
# http://docs.djangoproject.com/en/dev/ref/contrib/gis/geoip/
# =============================================================================

GEOIP_PATH = '/usr/share/GeoIP'

# =============================================================================
# test settings
# =============================================================================

TEST_CHARSET = 'utf-8'

# =============================================================================
# charset settings
# =============================================================================

DEFAULT_CHARSET = 'utf-8'

# =============================================================================
# auth settings
# =============================================================================

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/a/accounts/login/'
LOGOUT_URL = '/a/accounts/logout/'

# =============================================================================
# localization settings
# =============================================================================

try:
    SHORT_DATETIME_FORMAT
except NameError:
    SHORT_DATETIME_FORMAT = 'Y-m-d H:M'
try:
    SHORT_DATE_FORMAT
except NameError:
    SHORT_DATE_FORMAT = 'Y-m-d'
try:
    TIME_FORMAT
except NameError:
    TIME_FORMAT = 'H:M'
try:
    DATE_FORMAT
except NameError:
    DATE_FORMAT = 'Y-m-d'

# =============================================================================
# for the tagging application
# =============================================================================
# see http://django-tagging.googlecode.com/svn/trunk/docs/overview.txt

FORCE_LOWERCASE_TAGS = True

# =============================================================================
# for the registration application
# =============================================================================

ACCOUNT_ACTIVATION_DAYS = 10

# =============================================================================
# application and middleware settings
# =============================================================================

# at the end additional applications are conditionaly added
INSTALLED_APPS = (
    'gridcalendar.events',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.databrowse',
    'django.contrib.admindocs',
    'django.contrib.comments',
    'tagging',
    'registration',
    'django.contrib.markup', # used for rendering ReStructuredText
 )
if DEBUG:
    INSTALLED_APPS += ( 'debug_toolbar', )

# at the end additional middleware are conditionaly added
MIDDLEWARE_CLASSES = (
    # see http://docs.djangoproject.com/en/1.2/ref/contrib/csrf/
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
 )
if DEBUG:
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware', )
    MIDDLEWARE_CLASSES += (
        'gridcalendar.middlewares.ProfileMiddleware', )

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
        # 'TAG': 'div',
    }

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "context_processors.global_template_vars",
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

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
 )

# =============================================================================
# i18n and url settings
# =============================================================================

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

################################
# example of a settings_local.py
################################
#
# import os
#
# VERSION = 'alpha'
#
# # Make this unique, and don't share it with anybody.
# SECRET_KEY = 'a$#ba$@(AJIOEAanb.;p;ki))(*&^4556breqnape#$3q23422'
#
# # absolute path to this directory
# PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
#
# # ===========================================================================
# # imap settings for getting events as emails
# # ===========================================================================
# IMAP_SERVER = 'your_imap_server'
# IMAP_LOGIN = 'your_imap_login'
# IMAP_PASSWD = 'your_imap_password'
#
# # ===========================================================================
# # debug settings
# # ===========================================================================
#
# DEBUG = True
# TEMPLATE_DEBUG = DEBUG
# # http://docs.djangoproject.com/en/dev/ref/settings/#internal-ips
# INTERNAL_IPS = ('127.0.0.1',)
# if DEBUG:
#     TEMPLATE_STRING_IF_INVALID = 'STRING_NOT_SET'
#
# # ===========================================================================
# # cache settings
# # ===========================================================================
# # http://docs.djangoproject.com/en/dev/topics/cache/
#
# # CACHE_BACKEND = 'locmem://'
# # CACHE_MIDDLEWARE_KEY_PREFIX = '%s_' % PROJECT_NAME
# # CACHE_MIDDLEWARE_SECONDS = 600
#
#
# # ===========================================================================
# # email and error-notify settings
# # ===========================================================================
#
# ADMINS = (
#     ('your_name', 'your_mail'),
# )
#
# MANAGERS = ADMINS
#
# DEFAULT_FROM_EMAIL = 'noreply@example.com'
# SERVER_EMAIL = 'noreply@example.com'
#
# EMAIL_HOST = 'your_smtp_email'
# EMAIL_PORT = 25
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''
# EMAIL_USE_TLS = False
#
# # see http://docs.djangoproject.com/en/dev/howto/error-reporting/
# SEND_BROKEN_LINK_EMAILS = True
#
#
# # ===========================================================================
# # database settings
# # ===========================================================================
#
# # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
# DATABASE_ENGINE   = 'sqlite3'
# # DB Name (or path to database file if using sqlite3)
# DATABASE_NAME     = os.path.join(PROJECT_ROOT, 'gridcalendar.sqlite')
# DATABASE_USER     = ''                     # Not used with sqlite3.
# DATABASE_PASSWORD = ''                     # Not used with sqlite3.
# DATABASE_HOST     = ''                     # Not used with sqlite3.
# DATABASE_PORT     = ''                     # Not used with sqlite3.
