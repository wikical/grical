#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
# gpl {{{1
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

# docs {{{1
""" views for RSS and Atom """

# TODO: validate with test iCal and RSS output using validations like e.g.
# http://arnout.engelen.eu/icalendar-validator/validate/

### imports {{{1
import vobject
import unicodedata
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.syndication.views import Feed, FeedDoesNotExist

import gridcalendar.settings as settings
from gridcalendar.events.models import Event, Filter, Group, Membership, \
        ExtendedUser
from gridcalendar.events.lists import list_search_get

class PublicUpcomingEventsFeed(Feed): # {{{1
    """ Feed with the next `settings.FEED_SIZE` number of events. """
    # TODO: use SITE instead of PROJECT_NAME
    title = _(u"%(site_url)s public events") % \
            {'site_url': settings.PROJECT_NAME,}
    link = "/r/upcoming"
    description = _("Next %(count)s upcoming events." \
            % {"count": settings.FEED_SIZE}, )

    def items( self ):
        """ items """
        today = datetime.date.today()
        elist = Event.objects.filter (public = True).filter(
                    Q(start__gte=today) |
                    Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today)
                ).distinct()[:settings.FEED_SIZE]
        elist = sorted(elist, key=Event.next_coming_date)
        return elist
        #elist = [eve for eve in elist if eve.is_viewable_by_user( request.user )]

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return item.get_absolute_url()

    def item_description(self, item):
        return _(u"start: %(date)s") % {'date': item.start.isoformat(), }
        # FIXME: add more info

#class FeedSearchEvents(Feed): # {{{1
#    """ Used for a feed for search results. """
#    title_template = 'rss/searchevents_title.html'
#    description_template = 'rss/searchevents_description.html'
#
#    def get_object(self, bits): # pylint: disable-msg=C0111
#        if len(bits) != 1:
#            raise ObjectDoesNotExist
#        query = bits[0]
#        return query
#
#    def title(self, obj): # pylint: disable-msg=C0111
#        return "events for search '%s'" % obj
#
#    def link(self, obj): # pylint: disable-msg=C0111
#        return '/s/' + obj + '/'
#
#    def description(self, obj): # pylint: disable-msg=C0111
#        return "events for search %s" % obj
#
#    def items(self, obj): # pylint: disable-msg=C0111
#        return list_search_get(obj)
#
#class FeedFilterEvents(Feed): # {{{1
#    """ Used for a feed for filter results. """
#    title_template = 'rss/filterevents_title.html'
#    description_template = 'rss/filterevents_description.html'
#
#    def get_object(self, bits): # pylint: disable-msg=C0111
#        if len(bits) != 1:
#            raise ObjectDoesNotExist
#        filter_id = bits[0]
#        return filter_id
#
#    def title(self, obj): # pylint: disable-msg=C0111
#        return "events for filter '%s'" % obj
#
#    def link(self, obj): # pylint: disable-msg=C0111
#        return '/f/' + obj + '/'
#
#    def description(self, obj): # pylint: disable-msg=C0111
#        return "events for filter %s" % obj
#
#    def items(self, obj): # pylint: disable-msg=C0111
#        events_filter = Filter.objects.get(id=obj)
#        list = list_search_get(events_filter.query)
#        return list
#
#class FeedGroupEvents(Feed): # {{{1
#    """ Used for a feed for events of a group """
#    title_template = 'rss/groupevents_title.html'
#    description_template = 'rss/groupevents_description.html'
#
#    def get_object(self, bits): # pylint: disable-msg=C0111
#        if len(bits) != 1:
#            raise ObjectDoesNotExist
#        group_id = bits[0]
#        return Group.objects.get(id=group_id)
#
#    def title(self, obj): # pylint: disable-msg=C0111
#        if obj is None:
#            return "You are not allowed to view this feed."
#        else:
#            return "events in group '%s'" % obj.name
#
#    def link(self, obj): # pylint: disable-msg=C0111
#        if obj is None:
#            return '/'
#        elif not obj:
#            raise FeedDoesNotExist
#        else:
#            return obj.get_absolute_url()
#
#    def description(self, obj):
#        """ feed description """
#        if obj is None: # pylint: disable-msg=C0111
#            return "You are not allowed to view this feed."
#        else:
#            return "events in group %s" % obj.name
#
#    def items(self, obj):
#        if obj is None: # pylint: disable-msg=C0111
#            return Event.objects.none()
#        else:
#            filter_list = Event.objects.filter(group=obj).order_by('start')
#            return filter_list[:settings.FEED_SIZE]
#
#    # does not work, because 'datetime.date' object has no attribute 'tzinfo'
#    #    def item_pubdate(self, item):
#    #        return item.start
#
