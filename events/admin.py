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

from gridcalendar.events.models import Event, Group, EventUrl, EventSession, EventDeadline, Tag, Membership, Calendar
from django.contrib import admin

# Add related data in the admin views.
# Explained at
# http://docs.djangoproject.com/en/dev/ref/contrib/admin/#working-with-many-to-many-intermediary-models

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1

class CalendarInline(admin.TabularInline):
    model = Calendar
    extra = 1

class UrlInline(admin.StackedInline):
    model = EventUrl
    extra = 1

class SessionInline(admin.StackedInline):
    model = EventSession
    extra = 1

class DeadlineInline(admin.StackedInline):
    model = EventDeadline
    extra = 1

class EventAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """Saves the user logged-in as user (owner) of the event when adding a
        new Event"""
        if not change:
            obj.user = request.user
        obj.save()
    list_display = ('title', 'start', 'city', 'country')
    list_filters = ['start', 'country']
    search_fields = ['title', 'tags', 'country', 'city']
    date_hierarchy = 'start'
    inlines = [UrlInline, SessionInline, DeadlineInline, CalendarInline]

class GroupAdmin(admin.ModelAdmin):
    # FIXME: add the logged-in user in the group when saving a new group. See
    # save_model in EventAdmin
    inlines = (MembershipInline, CalendarInline,)

admin.site.register(Event, EventAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(EventUrl)
admin.site.register(EventSession)
admin.site.register(EventDeadline)
# admin.site.register(Tag)

