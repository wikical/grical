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

### imports {{{1
import datetime

from django.contrib.sites.models import Site
from django.http import Http404
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

from gridcalendar.settings import FEED_SIZE, SITE_ID
from gridcalendar.events.models import ( Event, Filter, Group,
        ExtendedUser )

SITE_DOMAIN = Site.objects.get(id = SITE_ID).domain

class EventsFeed(Feed): # {{{1
    """ rss feed for a list of events """

    def item_title(self, item):
        return item.title

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        """ uses the modification_time of the event """
        return item.modification_time

    def item_description(self, item):
        return _('next coming date: %(date)s') % {'date':
                item.next_coming_date_or_start().isoformat()}
        # one could return the event as text with something like:
        # return '<!CDATA[' + item.as_text().replace('\n', '<br />') + ' ]]'

class PublicUpcomingEventsFeed(EventsFeed): # {{{1
    """ Feed with the next `settings.FEED_SIZE` number of public events,
    ordered by next coming date. """

    title = _(u"%(domain)s upcoming public events feed") % \
            {'domain': SITE_DOMAIN,}
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
        return sorted( elist, key=Event.next_coming_date_or_start )[:FEED_SIZE]


class PublicSearchEventsFeed(EventsFeed): # {{{1
    """ feed for the result of a search for AnonymousUser """
    
    def get_object(self, request, query):
        return query

    def title(self, obj):
        """ title """
        return _(u'%(domain)s search results') % {'domain': SITE_DOMAIN,}

    def link(self, obj):
        """ return a link to a search with get http method """
        # TODO: if the search query is '#tag' if won't work, fix it
        return reverse( 'list_events_search', kwargs = {'query': obj,} )

    def description(self, obj):
        """ description """
        return _(u'%(domain)s search results for %(query)s') % \
                {'domain': SITE_DOMAIN, 'query': obj,}

    def items(self, obj):
        """ items """
        matches, related = Filter.matches( obj, None, FEED_SIZE )
        # if matches are less than FEED_SIZE, it adds some events from
        # related matches
        if len( matches ) < FEED_SIZE:
            to_take = FEED_SIZE - len( related )
            matches += related[0:to_take]
        return matches


class HashSearchEventsFeed(EventsFeed): # {{{1
    """ feed for the result of a search with hash authentification """
    
    def get_object(self, request, query, user_id, hashcode):
        if hashcode != ExtendedUser.calculate_hash(user_id):
            raise Http404
        return {'query': query, 'user_id': user_id, 'hash': hashcode}

    def title(self, obj):
        """ title """
        return _(u'%(domain)s search results') % {'domain': SITE_DOMAIN,}

    def link(self, obj):
        """ link """
        return reverse( 'list_events_search_hashed', kwargs = obj )

    def description(self, obj):
        """ description """
        return _(u'%(domain)s search results for %(query)s') % \
                {'domain': SITE_DOMAIN, 'query': obj,}

    def items(self, obj):
        """ items """
        matches, related = Filter.matches(
                obj['query'], obj['user_id'], FEED_SIZE )
        # if matches are less than FEED_SIZE, it adds some events from
        # related matches
        if len( matches ) < FEED_SIZE:
            to_take = FEED_SIZE - len( related )
            matches += related[0:to_take]
        return matches


class PublicGroupEventsFeed(EventsFeed): # {{{1
    """ feed with the public events of a group """

    def get_object(self, request, group_id):
        group_name = Group.objects.get(id = group_id)
        if not group_name:
            raise Http404
        return {'group_id': group_id, 'group_name': group_name}

    def title(self, obj):
        """ title """
        return _(u'%(domain)s group %(group_name)s') % \
                {'domain': SITE_DOMAIN, 'group_name': obj['group_name']}

    def link(self, obj):
        """ link """
        return reverse( 'group_view', kwargs = {'group_id': obj['group_id'],} )

    def description(self, obj):
        """ description """
        return _(u'public events on %(domain)s for the group %(group_name)s')% \
                {'domain': SITE_DOMAIN, 'group_name': obj['group_name'],}

    def items(self, obj):
        """ items """
        return Event.objects.filter(public = True).filter(
                calendar__group__id = obj['group_id'] )

class HashGroupEventsFeed(EventsFeed): # {{{1
    """ feed with the events of a group with hash authentification """
    # FIXME write a text for it

    def get_object(self, request, group_id, user_id, hashcode):
        group_name = Group.objects.get(id = group_id)
        if not group_name:
            raise Http404
        if hashcode != ExtendedUser.calculate_hash(user_id):
            raise Http404
        return { 'group_id': group_id,
                'group_name': group_name,
                'user_id': user_id }

    def title(self, obj):
        """ title """
        return _(u'%(domain)s group %(group_name)s') % \
                {'domain': SITE_DOMAIN, 'group_name': obj['group_name']}

    def link(self, obj):
        """ link """
        return reverse( 'group_view', kwargs = {'group_id': obj['group_id'],} )

    def description(self, obj):
        """ description """
        return _(u'events on %(domain)s for the group %(group_name)s') % \
                {'domain': SITE_DOMAIN, 'group_name': obj['group_name'],}

    def items(self, obj):
        """ items """
        group = Group.objects.get( id = obj['group_id'] )
        if Group.is_user_in_group( obj['user_id'], obj['group_id'] ):
            return group.get_coming_events( limit = FEED_SIZE )
        else:
            return group.get_coming_public_events( limit = FEED_SIZE )

