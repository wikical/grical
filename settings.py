#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009, 2010 Iván F. Villanueva B. <ivan ät gridmind.org>
#
# This file is part of GridCalendar.
# 
# GridCalendar is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################


import os

PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

try:
    from settings_local import *
except ImportError:
    pass


# =====================================================================
# specific GridCalendar settings
# =====================================================================

# for RSS feeds
FEED_SIZE = 10

MAX_EVENTS_ON_ROOT_PAGE=20


# ======================================================================
# auth settings
# ======================================================================

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/a/accounts/login/'
LOGOUT_URL = '/a/accounts/logout/'

# for tagging application
# see http://django-tagging.googlecode.com/svn/trunk/docs/overview.txt
FORCE_LOWERCASE_TAGS = True

# for the registration application
ACCOUNT_ACTIVATION_DAYS = 10

# ======================================================================
# application and middleware settings
# ======================================================================

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
# at the end of this section additional applications are conditionaly
# added

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)
# at the end of this section additional middleware are conditionaly
# added

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "context_processors.global_template_vars",
)
if DEBUG:
    TEMPLATE_CONTEXT_PROCESSORS += ("django.core.context_processors.debug",)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, "templates"),
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

# If possible install a utility for debugging, which is # called debug_toolbar
# und is availabe in Debian like systems as the package
# python-django-debug-toolbar
try:
    debug_toolbar.middleware.DebugToolbarMiddleware
except NameError:
    pass
else:
    if DEBUG:
        MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
        INSTALLED_APPS += ('debug_toolbar',)


# ======================================================================
# i18n and url settings
# ======================================================================

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
try: TIME_ZONE
except NameError: TIME_ZONE = 'Europe/Berlin'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
try: LANGUAGE_CODE
except NameError: LANGUAGE_CODE = 'en-us'

try: LANGUAGES
except NameError: LANGUAGES = (('en', 'English'),)

try: DATE_FORMAT
except NameError: DATE_FORMAT = 'Y-m-d'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# This is used by the django.contrib.sites, which is needed by for instance the registration code we
# are using from a Debian package (upstream is:
# http://bitbucket.org/ubernostrum/django-registration/wiki/Home )
try: SITE_ID
except NameError: SITE_ID = 1

# Absolute path to the directory that holds media.
try: MEDIA_ROOT
except NameError: MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
try: MEDIA_URL
except NameError: MEDIA_URL = '/m/'

try: ADMIN_MEDIA_PREFIX
except NameError: ADMIN_MEDIA_PREFIX = '/m/admin/'

try: ROOT_URLCONF
except NameError: ROOT_URLCONF = 'urls'

