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
""" views for RSS """

# TODO: validate with test iCal and RSS output using validations like e.g.
# http://arnout.engelen.eu/icalendar-validator/validate/

### imports {{{1
import vobject
import unicodedata
import datetime

from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_list_or_404
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.core.urlresolvers import reverse

from gridcalendar.settings import FEED_SIZE, SITE_ID
from gridcalendar.events.models import Event, Filter, Group, Membership, \
        ExtendedUser
from gridcalendar.events.lists import list_search_get

site_domain = Site.objects.get(id = SITE_ID).domain

class EventsFeed(Feed): # {{{1

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.modification_time

    def item_description(self, item):
        return _('next coming date: %(date)s') % {'date':
                item.next_coming_date().isoformat()}
        # one could return the event as text with something like:
        # return '<!CDATA[' + item.as_text().replace('\n', '<br />') + ' ]]'

class PublicUpcomingEventsFeed(EventsFeed): # {{{1
    """ Feed with the next `settings.FEED_SIZE` number of public events,
    ordered by next coming date. """

    title = _(u"%(domain)s upcoming public events feed") % \
            {'domain': site_domain,}
    link = "/r/upcoming"
    description = _("Next %(count)s upcoming events." \
            % {"count": FEED_SIZE}, )

    def items( self ):
        """ items """
        today = datetime.date.today()
        elist = Event.objects.filter (public = True).filter(
                    Q(start__gte=today) |
                    Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today)
                ).distinct()
        return sorted( elist, key=Event.next_coming_date )[:FEED_SIZE]


class PublicSearchEventsFeed(EventsFeed): # {{{1
    
    def get_object(self, request, query):
        return query

    def title(self, obj):
        return _(u'%(domain)s search results') % {'domain': site_domain,}

    def link(self, obj):
        return reverse( 'list_events_search', kwargs = {'query': obj,} )

    def description(self, obj):
        return _(u'%(domain)s search results for %(query)s') % \
                {'domain': site_domain, 'query': obj,}

    def items(self, obj):
        return Filter.matches(
                obj['query'], None, FEED_SIZE )


class HashSearchEventsFeed(EventsFeed): # {{{1
    
    def get_object(self, request, query, user_id, hash):
        if hash != ExtendedUser.calculate_hash(user_id):
            raise Http404
        return {'query': query, 'user_id': user_id, 'hash': hash}

    def title(self, obj):
        return _(u'%(domain)s search results') % {'domain': site_domain,}

    def link(self, obj):
        return reverse( 'list_events_search_hashed', kwargs = obj )

    def description(self, obj):
        return _(u'%(domain)s search results for %(query)s') % \
                {'domain': site_domain, 'query': obj,}

    def items(self, obj):
        return Filter.matches(
                obj['query'], obj['user_id'], FEED_SIZE )


class PublicGroupEventsFeed(EventsFeed): # {{{1

    def get_object(self, request, group_id):
        group_name = Group.objects.get(id = group_id)
        if not group_name:
            raise Http404
        return {'group_id': group_id, 'group_name': group_name}

    def title(self, obj):
        return _(u'%(domain)s group %(group_name)s') % \
                {'domain': site_domain, 'group_name': obj['group_name']}

    def link(self, obj):
        return reverse( 'group_view', kwargs = {'group_id': obj['group_id'],} )

    def description(self, obj):
        group_name = Group.objects.get(id = obj).name
        return _(u'public events on %(domain)s for the group %(group_name)s') % \
                {'domain': site_domain, 'group_name': obj['group_name'],}

    def items(self, obj):
        return Event.objects.filter(public = True).filter(
                calendar__group__id = obj['group_id'] )

class HashGroupEventsFeed(EventsFeed): # {{{1

    def get_object(self, request, group_id, user_id, hash):
        group_name = Group.objects.get(id = group_id)
        if not group_name:
            raise Http404
        if hash != ExtendedUser.calculate_hash(user_id):
            raise Http404
        return { 'group_id': group_id,
                'group_name': group_name,
                'user_id': user_id }

    def title(self, obj):
        return _(u'%(domain)s group %(group_name)s') % \
                {'domain': site_domain, 'group_name': obj['group_name']}

    def link(self, obj):
        return reverse( 'group_view', kwargs = {'group_id': obj['group_id'],} )

    def description(self, obj):
        group_name = Group.objects.get( id = obj['group_id'] ).name
        return _(u'events on %(domain)s for the group %(group_name)s') % \
                {'domain': site_domain, 'group_name': obj['group_name'],}

    def items(self, obj):
        group = Group.objects.get( id = obj['group_id'] )
        if Group.is_user_in_group( obj['user_id'], obj['group_id'] ):
            return group.get_coming_events( limit = FEED_SIZE )
        else:
            return group.get_coming_public_events( limit = FEED_SIZE )

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
