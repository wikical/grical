#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
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

""" views for RSS, Atom and iCal """

# TODO: validate with test iCal and RSS output using validations like e.g.
# http://arnout.engelen.eu/icalendar-validator/validate/

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
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist

import gridcalendar.settings as settings
from gridcalendar.events.models import Event, Filter, Group, Membership, \
        ExtendedUser
from gridcalendar.events.lists import list_search_get

class FeedAllComingEvents(Feed):
    """ Feed with the next `settings.FEED_SIZE` number of events. """
    title = _(u"Upcoming events")
    link = "/"
    description = _("Next %(count)d upcoming events." % {"count":
        settings.FEED_SIZE})
    def items(self):
        """ items """
        return Event.objects.order_by('start')[:settings.FEED_SIZE]

class FeedSearchEvents(Feed):
    """ Used for a feed for search results. """
    title_template = 'rss/searchevents_title.html'
    description_template = 'rss/searchevents_description.html'

    def get_object(self, bits): # pylint: disable-msg=C0111
        if len(bits) != 1:
            raise ObjectDoesNotExist
        query = bits[0]
        return query

    def title(self, obj): # pylint: disable-msg=C0111
        return "events for search '%s'" % obj

    def link(self, obj): # pylint: disable-msg=C0111
        return '/s/' + obj + '/'

    def description(self, obj): # pylint: disable-msg=C0111
        return "events for search %s" % obj

    def items(self, obj): # pylint: disable-msg=C0111
        return list_search_get(obj)

class FeedFilterEvents(Feed):
    """ Used for a feed for filter results. """
    title_template = 'rss/filterevents_title.html'
    description_template = 'rss/filterevents_description.html'

    def get_object(self, bits): # pylint: disable-msg=C0111
        if len(bits) != 1:
            raise ObjectDoesNotExist
        filter_id = bits[0]
        return filter_id

    def title(self, obj): # pylint: disable-msg=C0111
        return "events for filter '%s'" % obj

    def link(self, obj): # pylint: disable-msg=C0111
        return '/f/' + obj + '/'

    def description(self, obj): # pylint: disable-msg=C0111
        return "events for filter %s" % obj

    def items(self, obj): # pylint: disable-msg=C0111
        events_filter = Filter.objects.get(id=obj)
        list = list_search_get(events_filter.query)
        return list

class FeedGroupEvents(Feed):
    """ Used for a feed for events of a group """
    title_template = 'rss/groupevents_title.html'
    description_template = 'rss/groupevents_description.html'

    def get_object(self, bits): # pylint: disable-msg=C0111
        if len(bits) != 1:
            raise ObjectDoesNotExist
        group_id = bits[0]
        return Group.objects.get(id=group_id)

    def title(self, obj): # pylint: disable-msg=C0111
        if obj is None:
            return "You are not allowed to view this feed."
        else:
            return "events in group '%s'" % obj.name

    def link(self, obj): # pylint: disable-msg=C0111
        if obj is None:
            return '/'
        elif not obj:
            raise FeedDoesNotExist
        else:
            return obj.get_absolute_url()

    def description(self, obj):
        """ feed description """
        if obj is None: # pylint: disable-msg=C0111
            return "You are not allowed to view this feed."
        else:
            return "events in group %s" % obj.name

    def items(self, obj):
        if obj is None: # pylint: disable-msg=C0111
            return Event.objects.none()
        else:
            filter_list = Event.objects.filter(group=obj).order_by('start')
            return filter_list[:settings.FEED_SIZE]

    # does not work, because 'datetime.date' object has no attribute 'tzinfo'
    #    def item_pubdate(self, item):
    #        return item.start

def _ical_http_response_from_event_list( elist, filename ): # {{{1
    if len(elist) == 1:
        icalstream = elist[0].icalendar().serialize()
    else:
        ical = vobject.iCalendar()
        ical.add('METHOD').value = 'PUBLISH' # IE/Outlook needs this
        ical.add('PRODID').value = settings.PRODID
        for event in elist:
            event.icalendar(ical)
        icalstream = ical.serialize()
    response = HttpResponse( icalstream, 
            mimetype = 'text/calendar;charset=UTF-8' )
    filename = unicodedata.normalize('NFKD', filename).encode('ascii','ignore')
    filename = filename.replace(' ','_')
    if not filename[-4:] == '.ics':
        filename = filename + '.ics'
    response['Filename'] = filename  # IE needs this
    response['Content-Disposition'] = 'attachment; filename=' + filename
    return response

def ICalForSearch( request, query ): # {{{1
    elist = list_search_get(query) # FIXME: it can be too long
    elist = [eve for eve in elist if eve.is_viewable_by_user( request.user )]
    return _ical_http_response_from_event_list( elist, query )

def ICalForEvent( request, event_id ): # {{{1
    event = Event.objects.get( id = event_id )
    elist = [event,]
    elist = [eve for eve in elist if eve.is_viewable_by_user(request.user)]
    return _ical_http_response_from_event_list( elist, event.title )

def ICalForEventHash (request, event_id, user_id, hash):
    user = ExtendedUser.objects.get(id = user_id)
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'message_col1': _(u"hash authentification failed")
            },
            context_instance=RequestContext(request))
    event = Event.objects.get( id = event_id )
    if not event.is_viewable_by_user( user ):
        return render_to_response('error.html',
            {'title': 'error',
            'message_col1':
                _(u"user authentification for requested event failed")
            },
            context_instance=RequestContext(request))
    return _ical_http_response_from_event_list(
            [event,], event.title)
            

def ICalForSearchHash( request, query, user_id, hash ): # {{{1
    user = ExtendedUser.objects.get(id = user_id)
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'message_col1': _(u"hash authentification failed")
            },
            context_instance=RequestContext(request))
    elist = list_search_get(query) # FIXME: it can be too long
    elist = [eve for eve in elist if eve.is_viewable_by_user( user_id )]
    return _ical_http_response_from_event_list( elist, query )

def ICalForGroup( request, group_id ): # {{{1
    """ return all public events with a date in the future in icalendar format
    belonging to a group """
    group = Group.objects.filter(id = group_id)
    elist = Event.objects.filter(calendar__group = group, public = True)
    today = datetime.date.today()
    elist = elist.filter (
                Q(start__gte=today) |
                Q(end__gte=today) |
                Q(deadlines__deadline__gte=today) ).distinct()
    elist = sorted(elist, key=Event.next_coming_date)
    return _ical_http_response_from_event_list( elist, group.name )

def ICalForGroupHash( request, group_id, user_id, hash ): # {{{1
    """ return all events with a date in the future in icalendar format
    belonging to a group """
    user = ExtendedUser.objects.get(id = user_id)
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'message_col1': _(u"hash authentification failed")
            },
            context_instance=RequestContext(request))
    group = Group.objects.get(id = group_id)
    if not group.is_member(user_id):
        return render_to_response('error.html',
            {'title': 'error',
            'message_col1': _(u"not a member of the tried group")
            },
            context_instance=RequestContext(request))
    elist = Event.objects.filter(calendar__group = group)
    today = datetime.date.today()
    elist = elist.filter (
                Q(start__gte=today) |
                Q(end__gte=today) |
                Q(deadlines__deadline__gte=today) ).distinct()
    elist = sorted(elist, key=Event.next_coming_date)
    return _ical_http_response_from_event_list( elist, group.name )
