# -*- coding: utf-8 -*-

import hashlib, vobject

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.template import RequestContext

from django.contrib.auth.models import User
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist

import settings
from gridcalendar.events.models import Event, Filter, Group, Membership
from gridcalendar.events.lists import list_search_get
from gridcalendar.events.icalendar import ICalendarFeed, EVENT_ITEMS

class FeedAllComingEvents(Feed):
    title = "All coming events"
    link = "/"
    description = "All upcoming events."

    def items(self):
        return Event.objects.order_by('start')[:settings.FEED_SIZE]
        # FIXME: the above line seems to get all events into memory. Avoid!

class FeedSearchEvents(Feed):
    title_template = 'rss/searchevents_title.html'
    description_template = 'rss/searchevents_description.html'

    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        query = bits[0]
        return query

    def title(self, obj):
            return "events for search '%s'" % obj

    def link(self, obj):
            return '/s/' + obj + '/'

    def description(self, obj):
            return "events for search %s" % obj

    def items(self, obj):
            return list_search_get(obj)['list_of_events']

class FeedFilterEvents(Feed):
    title_template = 'rss/filterevents_title.html'
    description_template = 'rss/filterevents_description.html'

    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        filter_id = bits[0]
        return filter_id

    def title(self, obj):
            return "events for filter '%s'" % obj

    def link(self, obj):
            return '/f/' + obj + '/'

    def description(self, obj):
            return "events for filter %s" % obj

    def items(self, obj):
        f = Filter.objects.get(id=obj)
        l = list_search_get(f.query)['list_of_events']
        return l

class FeedGroupEvents(Feed):
    title_template = 'rss/groupevents_title.html'
    description_template = 'rss/groupevents_description.html'

    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        group_id = bits[0]
        return Group.objects.get(id=group_id)

    def title(self, obj):
        if obj is None:
            return "You are not allowed to view this feed."
        else:
            return "events in group '%s'" % obj.name

    def link(self, obj):
        if obj is None:
            return '/'
        elif not obj:
            raise FeedDoesNotExist
        else:
            return obj.get_absolute_url()

    def description(self, obj):
        if obj is None:
            return "You are not allowed to view this feed."
        else:
            return "events in group %s" % obj.name

    def items(self, obj):
        if obj is None:
            return Event.objects.none()
        else:
            return Event.objects.filter(group=obj).order_by('start')[:settings.FEED_SIZE]

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

    def items(self, query):
        l = list_search_get(query)['list_of_events']
        return l

    def item_uid(self, item):
        return str(item.id)

    def item_start(self, item):
        return item.start

    def item_end(self, item):
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
        if (hash == hashlib.sha256("%s!%s!%s" % (settings.SECRET_KEY, filter_id, user_id)).hexdigest()) and (len(Filter.objects.filter(id=filter_id).filter(user=u)) == 1):
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
                'message_col1': _("You are not allowed to fetch the iCalendar for the filter with the following number") +
                ": " + str(group_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
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
                'message_col1': _("You are not allowed to fetch the iCalendar for the filter with the following number") +
                ": " + str(filter_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))

class ICalForFilterHash(ICalForFilter):
    def __call__(self, request, filter_id, user_id, hash):
        cal = vobject.iCalendar()
        f = Filter.objects.filter(id=filter_id)
        u = User.objects.filter(id=user_id)
        if (hash == hashlib.sha256("%s!%s!%s" % (settings.SECRET_KEY, filter_id, user_id)).hexdigest()) and (len(Filter.objects.filter(id=filter_id).filter(user=u)) == 1):
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
                'message_col1': _("You are not allowed to fetch the iCalendar for the filter with the following number") +
                ": " + str(group_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
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
                'message_col1': _("You are not allowed to fetch the iCalendar for the group with the following number") +
                ": " + str(group_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))

class ICalForGroupHash(ICalForGroup):

    def __call__(self, request, group_id, user_id, hash):
        cal = vobject.iCalendar()
        g = Group.objects.filter(id=group_id)
        u = User.objects.filter(id=user_id)
        if (hash == hashlib.sha256("%s!%s!%s" % (settings.SECRET_KEY, group_id, user_id)).hexdigest()) and (len(Membership.objects.filter(group=g).filter(user=u)) == 1):
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
                'message_col1': _("You are not allowed to fetch the iCalendar for the group with the following number") +
                ": " + str(group_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
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

