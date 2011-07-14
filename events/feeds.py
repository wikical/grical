#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
# gpl {{{1
#############################################################################
# Copyright 2009-2011 Ivan Villanueva <ivan ät gridmind.org>
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
from django.contrib.gis.db.models import Q
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
        description = _( u'start: %(date)s' ) % \
                {'date': item.start.isoformat()}
        if item.upcoming != item.start:
            description += "    " +  _('upcoming: %(date)s') % \
                {'date': item.upcoming.isoformat()}
        return description
        # one could return the event as text with something like:
        # return '<!CDATA[' + item.as_text().replace('\n', '<br />') + ' ]]'

class UpcomingEventsFeed(EventsFeed): # {{{1
    """ Feed with the next `settings.FEED_SIZE` number of events,
    ordered by upcoming. """

    title = _(u"%(domain)s upcoming events feed") % \
            {'domain': SITE_DOMAIN,}
    link = "/r/upcoming"
    description = _("Next %(count)s upcoming events." \
            % {"count": FEED_SIZE}, )

    def items( self ):
        """ items """
        today = datetime.date.today()
        elist = Event.objects.filter(upcoming__gte=today ).order_by('upcoming')
        return elist[:FEED_SIZE]

class LastAddedEventsFeed(EventsFeed): # {{{1
    """ Feed with the last `settings.FEED_SIZE` added events """

    title = _(u"%(domain)s last added events feed") % \
            {'domain': SITE_DOMAIN,}
    link = "/r/upcoming"
    description = _("Last %(count)s added events." \
            % {"count": FEED_SIZE}, )

    def items( self ):
        """ items """
        elist = Event.objects.all().order_by('-creation_time')
        return elist[:FEED_SIZE]

class SearchEventsFeed(EventsFeed): # {{{1
    """ feed for the result of a search """
    
    def get_object(self, request, query):
        return query

    def title(self, obj):
        """ title """
        return _(u'%(domain)s search results for %(query)s') % \
                {'domain': SITE_DOMAIN, 'query': obj}

    def link(self, obj):
        """ return a link to a search with get http method """
        return reverse( 'search') + '?query=' + obj

    def description(self, obj):
        """ description """
        return _(u'%(domain)s search results for %(query)s') % \
                {'domain': SITE_DOMAIN, 'query': obj,}

    def items(self, obj):
        """ items """
        matches = Filter.matches( obj, FEED_SIZE )
        return matches


class GroupEventsFeed(EventsFeed): # {{{1
    """ feed with the events of a group """

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
        return _(u'events on %(domain)s for the group %(group_name)s')% \
                {'domain': SITE_DOMAIN, 'group_name': obj['group_name'],}

    def items(self, obj):
        """ items """
        return Event.objects.filter( calendar__group__id = obj['group_id'] )

