#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Django configuration file for testing, use it with
./manage.py test --settings=gridcalendar.settings_for_tests"""
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
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

from gridcalendar.settings import *

def _remove( item, tup ):
    if not item in tup:
        return tup
    index = tup.index( item )
    return tup[ : index] + tup[ index + 1 : ]

PIPE_TO_LOG_TO = False

INSTALLED_APPS = _remove( 'debug_toolbar', INSTALLED_APPS )

MIDDLEWARE_CLASSES = _remove(
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        MIDDLEWARE_CLASSES )

MIDDLEWARE_CLASSES = _remove(
        'gridcalendar.middlewares.ProfileMiddleware',
        MIDDLEWARE_CLASSES )

