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

""" Functions for RSS and iCal """

# TODO: validate with test iCal and RSS output using validations like e.g.
# http://arnout.engelen.eu/icalendar-validator/validate/

import hashlib, vobject

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.template import RequestContext

from django.contrib.auth.models import User
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist

import gridcalendar.settings as settings
from gridcalendar.events.models import Event, Filter, Group, Membership
from gridcalendar.events.lists import list_search_get
from gridcalendar.events.icalendar import ICalendarFeed, EVENT_ITEMS

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
        return list_search_get(obj)['list_of_events']

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
        list = list_search_get(events_filter.query)['list_of_events']
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

class ICalForSearch(ICalendarFeed):
    def __call__(self, request, query):
        cal = vobject.iCalendar()
        for item in self.items(query):
            event = cal.add('vevent')
            for vkey, key in EVENT_ITEMS:
                value = getattr(self, 'item_' + key)(item)
                if value:
                    event.add(vkey).value = value
        response = HttpResponse(cal.serialize())
        response['Content-Type'] = 'text/calendar'
        return response

    def items(self, query): # pylint: disable-msg=C0111
        list = list_search_get(query)['list_of_events']
        return list

    def item_uid(self, item): # pylint: disable-msg=C0111
        return str(item.id)

    def item_start(self, item): # pylint: disable-msg=C0111
        return item.start

    def item_end(self, item): # pylint: disable-msg=C0111
        return item.end

class ICalForSearchAuth(ICalForSearch):
    def __call__(self, request, query):
        cal = vobject.iCalendar()

        for item in self.items(query):
            event = cal.add('vevent')
            for vkey, key in EVENT_ITEMS:
                value = getattr(self, 'item_' + key)(item)
                if value:
                    event.add(vkey).value = value
        response = HttpResponse(cal.serialize())
        response['Content-Type'] = 'text/calendar'
        return response

class ICalForSearchHash(ICalForSearch):
    def __call__(self, request, query, user_id, hash):
        cal = vobject.iCalendar()
        f = Filter.objects.filter(id=filter_id)
        u = User.objects.filter(id=user_id)
        if (hash == hashlib.sha256(
                "%s!%s" % (settings.SECRET_KEY, user_id)).hexdigest()) and \
                (len(Filter.objects.filter(id=filter_id).filter(user=u)) == 1):
            for item in self.items(filter_id):
                event = cal.add('vevent')
                for vkey, key in EVENT_ITEMS:
                    value = getattr(self, 'item_' + key)(item)
                    if value:
                        event.add(vkey).value = value
            response = HttpResponse(cal.serialize())
            response['Content-Type'] = 'text/calendar'
            return response
        else:
            return render_to_response('error.html',
                {'title': 'error',
                'message_col1': ''.join([
                    _("You are not allowed to fetch the iCalendar for the " +
                        "filter with the following number:"), " ",
                    str(filter_id)])
                },
                context_instance=RequestContext(request))

class ICalForFilter(ICalendarFeed):
    def __call__(self, request, filter_id):
        cal = vobject.iCalendar()
        for item in self.items(filter_id):
            event = cal.add('vevent')
            for vkey, key in EVENT_ITEMS:
                value = getattr(self, 'item_' + key)(item)
                if value:
                    event.add(vkey).value = value
        response = HttpResponse(cal.serialize())
        response['Content-Type'] = 'text/calendar'
        return response

    def items(self, filter_id):
        f = Filter.objects.get(id=filter_id)
        l = list_search_get(f.query)['list_of_events']
        return l

    def item_uid(self, item):
        return str(item.id)

    def item_start(self, item):
        return item.start

    def item_end(self, item):
        return item.end

class ICalForFilterAuth(ICalForFilter):
    def __call__(self, request, filter_id):
        cal = vobject.iCalendar()
        f = Filter.objects.filter(id=filter_id)
        u = User.objects.filter(id=request.user.id)
        if (len(Filter.objects.filter(id=filter_id).filter(user=u)) == 1):
            for item in self.items(filter_id):
                event = cal.add('vevent')
                for vkey, key in EVENT_ITEMS:
                    value = getattr(self, 'item_' + key)(item)
                    if value:
                        event.add(vkey).value = value
            response = HttpResponse(cal.serialize())
            response['Content-Type'] = 'text/calendar'
            return response
        else:
            return render_to_response('error.html',
                {'title': 'error',
                'message_col1': ''.join([
                    _("You are not allowed to fetch the iCalendar for the " +
                        "filter with the following number:"), " ",
                    str(filter_id)])
                },
                context_instance=RequestContext(request))

class ICalForFilterHash(ICalForFilter):
    def __call__(self, request, filter_id, user_id, hash):
        cal = vobject.iCalendar()
        f = Filter.objects.filter(id=filter_id)
        u = User.objects.filter(id=user_id)
        if (hash == hashlib.sha256(
                "%s!%s" % (settings.SECRET_KEY, user_id)).hexdigest()) and \
                (len(Filter.objects.filter(id=filter_id).filter(user=u)) == 1):
            for item in self.items(filter_id):
                event = cal.add('vevent')
                for vkey, key in EVENT_ITEMS:
                    value = getattr(self, 'item_' + key)(item)
                    if value:
                        event.add(vkey).value = value
            response = HttpResponse(cal.serialize())
            response['Content-Type'] = 'text/calendar'
            return response
        else:
            return render_to_response('error.html',
                {'title': 'error',
                'message_col1': ''.join([
                    _("You are not allowed to fetch the iCalendar for the " +
                        "filter with the following number:"), " ",
                    str(group_id)])
                },
                context_instance=RequestContext(request))

class ICalForGroup(ICalendarFeed):
    def __call__(self, request, group_id):
        cal = vobject.iCalendar()
        for item in self.items(group_id):
            event = cal.add('vevent')
            for vkey, key in EVENT_ITEMS:
                value = getattr(self, 'item_' + key)(item)
                if value:
                    event.add(vkey).value = value
        response = HttpResponse(cal.serialize())
        response['Content-Type'] = 'text/calendar'
        return response

    def items(self, group_id):
        g = Group.objects.filter(id=group_id)
        return Event.objects.filter(group=g)

    def item_uid(self, item):
        return str(item.id)

    def item_start(self, item):
        return item.start

    def item_end(self, item):
        return item.end

class ICalForGroupAuth(ICalForGroup):
    def __call__(self, request, group_id):
        cal = vobject.iCalendar()
        g = Group.objects.filter(id=group_id)
        u = User.objects.filter(id=request.user.id)
        if (len(Membership.objects.filter(group=g).filter(user=u)) == 1):
            for item in self.items(group_id):
                event = cal.add('vevent')
                for vkey, key in EVENT_ITEMS:
                    value = getattr(self, 'item_' + key)(item)
                    if value:
                        event.add(vkey).value = value
            response = HttpResponse(cal.serialize())
            response['Content-Type'] = 'text/calendar'
            return response
        else:
            return render_to_response('error.html',
                {'title': 'error',
                'message_col1': ''.join([
                    _("You are not allowed to fetch the iCalendar for the " +
                        "group with the following number") +
                    str(group_id)])
                },
                context_instance=RequestContext(request))

class ICalForGroupHash(ICalForGroup):
    def __call__(self, request, group_id, user_id, hash):
        cal = vobject.iCalendar()
        g = Group.objects.filter(id=group_id)
        u = User.objects.filter(id=user_id)
        if (hash == hashlib.sha256(
                "%s!%s" % (settings.SECRET_KEY, user_id)).hexdigest()) and \
                (len(Membership.objects.filter(group=g).filter(user=u)) == 1):
            for item in self.items(group_id):
                event = cal.add('vevent')
                for vkey, key in EVENT_ITEMS:
                    value = getattr(self, 'item_' + key)(item)
                    if value:
                        event.add(vkey).value = value
            response = HttpResponse(cal.serialize())
            response['Content-Type'] = 'text/calendar'
            return response
        else:
            return render_to_response('error.html',
                {'title': 'error',
                'message_col1': ''.join([
                    _("You are not allowed to fetch the iCalendar for the " +
                        "group with the following number") +
                    str(group_id)])
                },
                context_instance=RequestContext(request))

class ICalForEvent(ICalendarFeed):
    def __call__(self, request, event_id):
        cal = vobject.iCalendar()
        for item in self.items(event_id):
            event = cal.add('vevent')
            for vkey, key in EVENT_ITEMS:
                value = getattr(self, 'item_' + key)(item)
                if value:
                    event.add(vkey).value = value
        response = HttpResponse(cal.serialize())
        response['Content-Type'] = 'text/calendar'
        return response

    def items(self, event_id):
        return Event.objects.filter(pk=event_id)

    def item_uid(self, item):
        return str(item.id)

    def item_start(self, item):
        return item.start

    def item_end(self, item):
        return item.end
