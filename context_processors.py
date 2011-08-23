# -*- coding: utf-8 -*-
""" Adds variables to all templates """
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009-2011 Ivan Villanueva <ivan ät gridmind.org>
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


# This file is needed for example for:
# return render_to_response( ... , context_instance=RequestContext(request))

# TODO: think of (also) using TEMPLATE_CONTEXT_PROCESSORS =
# ('django.core.context_processors.request',)

from django.contrib.sites.models import Site
from django.conf import settings
from django.contrib.auth.models import User
from gridcalendar.events.models import Event, Group

from events.models import ExtendedUser

def global_template_vars(request):
    """ Adds variables to all templates. """
    current_site = Site.objects.get_current()
    if request.is_secure():
        protocol = "https"
    else:
        protocol = "http"
    if request.user.is_authenticated():
        user = ExtendedUser.objects.get( id = request.user.id )
    else:
        user = None
    users_nr = User.objects.count()
    events_nr = Event.objects.count()
    groups_nr = Group.objects.count()
    return {
            'PROTOCOL': protocol,
            'DOMAIN': current_site.domain,
            'MEDIA_URL': settings.MEDIA_URL,
            'USER': user,
            'VERSION': settings.VERSION,
            'USERS_NR': users_nr,
            'EVENTS_NR': events_nr,
            'GROUPS_NR': groups_nr,
            }
