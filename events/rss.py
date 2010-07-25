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


import hashlib

from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.shortcuts import render_to_response

from django.contrib.syndication.views import feed
from django.contrib.auth.models import User

import settings

from gridcalendar.events.feeds import FeedAllComingEvents, FeedGroupEvents, FeedSearchEvents, FeedFilterEvents
from gridcalendar.events.forms import get_event_form
from gridcalendar.events.models import Group, Membership

def rss_for_search(request, query):
        f = feed(request = request, url = 's/' + query, feed_dict = {
            u's': FeedSearchEvents,
        })
        return f

#---------------------------

def rss_for_filter(request, filter_id):
        f = feed(request = request, url = 'f/' + filter_id, feed_dict = {
            u'f': FeedFilterEvents,
        })
        return f

def rss_for_filter_auth(request, filter_id):
        return rss_for_filter(request, filter_id)

def rss_for_filter_hash(request, filter_id, user_id, hash):
        return rss_for_filter(request, filter_id)

#---------------------------

def rss_for_group(request, group_id):
        f = feed(request = request, url = 'g/' + group_id, feed_dict = {
            u'g': FeedGroupEvents,
        })
        return f

def rss_for_group_auth(request, group_id):
        return rss_for_group(request, group_id)

def rss_for_group_hash(request, group_id, user_id, hash):
    g = Group.objects.filter(id=group_id)
    u = User.objects.filter(id=user_id)
    if (hash == hashlib.sha256("%s!%s" % (settings.SECRET_KEY, user_id)).hexdigest())\
     and (len(Membership.objects.filter(group=g).filter(user=u)) == 1):
        return rss_for_group(request, group_id)
    else:
        return render_to_response('error.html',
                {'title': 'error', 'form': get_event_form(request.user),
                'message_col1': _("You are not allowed to see this RSS feed") + "."},
                context_instance=RequestContext(request))


#---------------------------

