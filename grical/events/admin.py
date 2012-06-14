#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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

""" Django admin definitions file adding related data in the admin views.  See
http://docs.djangoproject.com/en/dev/ref/contrib/admin/#working-with-many-to-many-intermediary-models
"""

# NOTE: allowing to edit events (including deadlines, urls and sessions) is not
# possible at the moment in the admin because:
# - revisions would be very tricky to keep
# - the admin performs bulk updates which circunvent the delete and save
#   methods of the models

from django.contrib import admin
from grical.events.models import Group, Membership, Calendar

class MembershipInline(admin.TabularInline):
    """ Membership """
    model = Membership
    extra = 1

class CalendarInline(admin.TabularInline):
    """ Calendar """
    model = Calendar
    extra = 1

class GroupAdmin(admin.ModelAdmin): # pylint: disable-msg=R0904
    """ ModelAdmin for Groups """
    inlines = (MembershipInline, CalendarInline,)

admin.site.register(Group, GroupAdmin)
