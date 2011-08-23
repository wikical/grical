#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009-2011 Ivan Villanueva <ivan ät gridmind.org>,
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
""" custom tags """

from django import template
from gridcalendar.events.models import Group, Calendar

register = template.Library()

# see http://docs.djangoproject.com/en/1.2/howto/custom-template-tags/
@register.inclusion_tag( 'groups/show_add_to_group.html', takes_context=True )
def show_add_to_group(context):
    """ custom tag to know and show (if needed) an "add to group" link when an
    event can be added to one or more of the groups of the logged-in user """
    user = context['user']
    event = context['event']
    if user is None or user.id is None:
        return {'show_add_to_group': False,}
    groups = Group.objects.filter(membership__user = user)
    if len(groups) < 1:
        return {'show_add_to_group': False,}
    for group in groups:
        times_event_in_group = Calendar.objects.filter( 
                event__id__exact = event.id,
                group__id__exact = group.id ).count()
        if times_event_in_group == 0:
            return {'show_add_to_group': True, 'event': event}
    return {'show_add_to_group': False,}

# The decorator above is equivalent to:
#register.inclusion_tag('groups/add_to_group_link.html', takes_context=True)(show_add_to_group )


