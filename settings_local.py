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

VERSION = 'alpha'

# absolute path to this directory
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
# the name of the directory
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

# ======================================================================
# debug settings
# ======================================================================

DEBUG = True
TEMPLATE_DEBUG = DEBUG
# http://docs.djangoproject.com/en/dev/ref/settings/#internal-ips
INTERNAL_IPS = ('127.0.0.1',)
if DEBUG:
    TEMPLATE_STRING_IF_INVALID = 'STRING_NOT_SET'

# ======================================================================
# cache settings
# ======================================================================
# http://docs.djangoproject.com/en/dev/topics/cache/

# CACHE_BACKEND = 'locmem://'
# CACHE_MIDDLEWARE_KEY_PREFIX = '%s_' % PROJECT_NAME
# CACHE_MIDDLEWARE_SECONDS = 600


# ======================================================================
# email and error-notify settings
# ======================================================================

ADMINS = (
    ('ogai', 'iv@gridmind.org'),
    ('miernik', 'ivan@miernik.name'),
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'GridCalendar Dev'
SERVER_EMAIL = 'error-notify@gridcalendar.net'

EMAIL_HOST = 'alpha.gridmind.org'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

# see http://docs.djangoproject.com/en/dev/howto/error-reporting/
SEND_BROKEN_LINK_EMAILS = True


# ======================================================================
# database settings
# ======================================================================

# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_ENGINE   = 'sqlite3'
# DB Name (or path to database file if using sqlite3)
DATABASE_NAME     = os.path.join(PROJECT_ROOT, 'gridcalendar.sqlite')
DATABASE_USER     = ''                     # Not used with sqlite3.
DATABASE_PASSWORD = ''                     # Not used with sqlite3.
DATABASE_HOST     = ''                     # Not used with sqlite3.
DATABASE_PORT     = ''                     # Not used with sqlite3.

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(%+a@o3aoaz@11a0o8paw$zkij7apd)i84mvaua_32dqb1lk_+'
