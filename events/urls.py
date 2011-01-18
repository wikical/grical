#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
# GPL {{{1
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
""" URLs """

# imports {{{1
from django.conf.urls.defaults import *

from gridcalendar.events import views
from gridcalendar.events.feeds import (
        PublicUpcomingEventsFeed, PublicSearchEventsFeed, HashSearchEventsFeed,
        PublicGroupEventsFeed, HashGroupEventsFeed )

# main url {{{1
urlpatterns = patterns('',            # pylint: disable-msg=C0103
    url(r'^$', views.main, name='main'),
    )

# ^e single event {{{1
urlpatterns += patterns('',                 # pylint: disable-msg=C0103
#    url(r'^e/new/$',
#        views.event_new,                name='event_new'),

    url(r'^e/new/raw/$',
        views.event_new_raw,            name='event_new_raw'),

    url(r'^e/edit/(?P<event_id>\d+)/$',
        views.event_edit,               name='event_edit'),

    url(r'^e/edit/(?P<event_id>\d+)/raw/$',
        views.event_edit_raw,           name='event_edit_raw'),

    url(r'^e/show/(?P<event_id>\d+)/$',
        views.event_show,               name='event_show'),

    url(r'^e/show/(?P<event_id>\d+)/raw/$',
        views.event_show_raw,           name='event_show_raw'),

    url(r'^e/show/(?P<event_id>\d+)/ical/$',
        views.ICalForEvent,             name='event_show_ical'),

    url(r'^e/show/(?P<event_id>\d+)/ical/(?P<user_id>\d+)/(?P<hashcode>\w+)/$',
        views.ICalForEventHash,  name='event_show_ical_hash'),

    url(r'^e/group/(?P<event_id>\d+)/$',
        views.group_add_event,      name='group_add_event'),
    )

# ^s searches urls {{{1
urlpatterns += patterns('',                 # pylint: disable-msg=C0103
    url(r'^s/$',
        views.search,              name='search'),

    url(r'^s/(?P<query>[^/]*)/$',
        views.list_events_search, name='list_events_search'),

    url(r'^s/(?P<query>[^/]*)/ical/$',
        views.ICalForSearch,      name='list_events_search_ical'),

    url(r'^s/(?P<query>[^/]*)/ical/(?P<user_id>\d+)/(?P<hashcode>\w+)/$',
        views.ICalForSearchHash,  name='list_events_search_ical_hashed'),

    url(r'^s/(?P<query>[^/]*)/rss/$',
        PublicSearchEventsFeed(), name='list_events_search_rss'),

    url(r'^s/(?P<query>[^/]*)/rss/(?P<user_id>\d+)/(?P<hashcode>\w+)/$',
        HashSearchEventsFeed(),  name='list_events_search_rss_hashed'),

    url(r'^s/(?P<query>[^/]*)/(?P<user_id>\d+)/(?P<hashcode>\w+)/$',
        views.list_events_search_hashed, name='list_events_search_hashed'),
    )

# ^t tags urls {{{1
urlpatterns += patterns('',                 # pylint: disable-msg=C0103
    url(r'^t/(?P<tag>[ \-\w]*)/$' ,
        views.list_events_tag,    name='list_events_tag'),
    )

# ^g groups urls {{{1
urlpatterns += patterns('', # pylint: disable-msg=C0103

    url(r'^g/(?P<group_id>\d+)/$',
        views.group_view,             name='group_view'),

    url(r'^(?P<group_name>\w{2,})/$', # TODO: accept all possible characters for group names
        views.group_name_view,        name='group_name_view'),

    url(r'^g/(?P<group_id>\d+)/ical/$',
        views.ICalForGroup,           name='list_events_group_ical'),

    url(r'^g/(?P<group_id>\d+)/ical/(?P<user_id>\d+)/(?P<hashcode>\w+)/$',
        views.ICalForGroupHash,       name='list_events_group_ical_hashed'),

    url(r'^g/(?P<group_id>\d+)/rss/$',
        PublicGroupEventsFeed(),      name='list_events_group_rss'),

    url(r'^g/(?P<group_id>\d+)/rss/(?P<user_id>\d+)/(?P<hashcode>\w+)/$',
        HashGroupEventsFeed(),        name='list_events_group_rss_hashed'),

    url(r'^g/new/$',
        views.group_new,              name='group_new'),

    url(r'^g/invite/(?P<group_id>\d+)/$',
        views.group_invite,           name='group_invite'),

    url(r'^g/invite/confirm/(?P<activation_key>\w+)/$',
        views.group_invite_activate,  name='group_invite_activate'),

    url(r'^g/quit/(?P<group_id>\d+)/$',
        views.group_quit,             name='group_quit'),

    url(r'^g/quit/(?P<group_id>\d+)/confirm/$',
        views.group_quit,
        kwargs = {'sure': True,},     name='group_quit_sure'),

    )
    # TODO: this should be a view with everything about the group for members
    # and not members; see also list_groups_my

# ^u user related urls {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103

    url(r'^u/events/$',
        views.list_events_my,           name='list_events_my'),

    url(r'^u/settings/$',
        views.settings_page,            name='settings'),

    url(r'^u/filters/$',
        views.list_filters_my,          name='list_filters_my'),

    url(r'^u/groups/$',
        views.list_groups_my,           name='list_groups_my'),
    )
    # not used for now because of privacy concerns:
    #   url(r'^e/list/user/(?P<username>\w+)/$',
    #       views.list_events_of_user,      name='list_events_of_user'),

# ^f filter management urls  {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103

    url(r'^f/new/$',
        views.filter_save,              name='filter_save'),

    url(r'^f/edit/(?P<filter_id>\d+)/$',
        views.filter_edit,              name='filter_edit'),

    url(r'^f/delete/(?P<filter_id>\d+)/$',
        views.filter_drop,              name='filter_drop'),
    )


# ^r rss main feed url {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103
     url(r'^r/upcoming/$',
         PublicUpcomingEventsFeed(), name='public_upcoming_events_rss'),
     )

# ^o output urls {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103
     url(r'^o/all/text/$',
         views.all_events_text, name='all_events_text'),
     )

# ^z tests
urlpatterns += patterns('',                     # pylint: disable-msg=C0103
     url(r'^z/$',
         views.test, name='test'),
     )
