#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Variables belonging to settings which should be modified machine dependent.
"""
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


from settings import PROJECT_NAME

VERSION = 'alpha'

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
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'noreply@gridcalendar.net'
SERVER_EMAIL = 'noreply@gridcalendar.net'

EMAIL_SUBJECT_PREFIX = '[%s] ' % PROJECT_NAME
EMAIL_HOST = 'mail.ffii.org'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'llanueva'
EMAIL_HOST_PASSWORD = 'ffii1971'
EMAIL_USE_TLS = True

# see http://docs.djangoproject.com/en/dev/howto/error-reporting/
SEND_BROKEN_LINK_EMAILS = True


# ======================================================================
# database settings
# ======================================================================

# 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_ENGINE   = 'sqlite3'
# DB Name (or path to database file if using sqlite3)
DATABASE_NAME     = 'gridcalendar.sqlite'
DATABASE_USER     = ''                     # Not used with sqlite3.
DATABASE_PASSWORD = ''                     # Not used with sqlite3.
DATABASE_HOST     = ''                     # Not used with sqlite3.
DATABASE_PORT     = ''                     # Not used with sqlite3.

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(%3a@o3(oaz@1aa0o8qaw$zkij7apd)i84mvaua_f2dqa1lk+u'
