#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
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
from gridcalendar.events.feeds import PublicUpcomingEventsFeed

# main url {{{1
urlpatterns = patterns('',            # root url {{{1 pylint: disable-msg=C0103
    url(r'^$', views.main, name='main'),
    )

# urls for managing single event {{{1
urlpatterns += patterns('',                 # pylint: disable-msg=C0103
    url(r'^e/new/$',
        views.event_new,                name='event_new'),
    url(r'^e/new/raw/$',
        views.event_new_raw,            name='event_new_raw'),
    url(r'^e/edit/(?P<event_id>\d+)/$',
        views.event_edit,               name='event_edit'),
    url(r'^e/edit/(?P<event>\d+)/raw/$',
        views.event_edit_raw,           name='event_edit_raw'),
    url(r'^e/show/(?P<event_id>\d+)/$',
        views.event_show,               name='event_show'),
    url(r'^e/show/(?P<event_id>\d+)/raw/$',
        views.event_show_raw,           name='event_show_raw'),
    url(r'^e/show/(?P<event_id>\d+)/ical/$',
        views.ICalForEvent,             name='event_show_ical'),
    url(r'^e/show/(?P<event_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',
        views.ICalForEventHash,  name='event_show_ical_hash'),
    )

# urls for managing searches {{{1
urlpatterns += patterns('',                 # pylint: disable-msg=C0103
    url(r'^q/',
        views.query,              name='query'),
    url(r'^s/(?P<query>.*)/ical/$',
        views.ICalForSearch,      name='list_events_search_ical'),
    url(r'^s/(?P<query>.*)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',
        views.ICalForSearchHash,  name='list_events_search_ical_hashed'),
    url(r'^s/(?P<query>.*)/rss/$',
        views.rss_for_search,       name='list_events_search_rss'),
    url(r'^s/(?P<query>.*)/$',
        views.list_events_search, name='list_events_search'),
    url(r'^t/(?P<tag>[ \-\w]*)/$' ,
        views.list_events_tag,    name='list_events_tag'),
    )

# events in a group {{{1
urlpatterns += patterns('', # pylint: disable-msg=C0103
    url(r'^g/(?P<group_id>\d+)/ical/$',
        views.ICalForGroup,       name='list_events_group_ical'),
    url(r'^g/(?P<group_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',
        views.ICalForGroupHash,       name='list_events_group_ical_hashed'),
    url(r'^g/(?P<group_id>\d+)/rss/$',
        views.rss_for_group_auth,         name='list_events_group_rss'),
    url(r'^g/(?P<group_id>\d+)/rss/(?P<user_id>\d+)/(?P<hash>\w+)/$',
        views.rss_for_group_hash,         name='list_events_group_rss_hashed'),
    url(r'^g/(?P<group_id>\d+)/$',
        views.group_view, name='group_view'),
    # TODO: this should be a view with everything about the group for members
    # and not members; see also list_groups_my
    )

# user related {{{1
urlpatterns += patterns('', #  pylint: disable-msg=C0103
    url(r'^p/events/$',
        views.list_events_my,           name='list_events_my'),
# not used for now because of privacy concerns:
#   url(r'^e/list/user/(?P<username>\w+)/$',
#       views.list_events_of_user,      name='list_events_of_user'),
    )

# TODO: put everything together 

# preferences {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103
    url(r'^p/settings/$',
        views.settings_page,            name='settings'),
    url(r'^p/filters/$',
        views.list_filters_my,          name='list_filters_my'),
    url(r'^p/groups/$',
        views.list_groups_my,    name='list_groups_my'),
    )

# filter management:  {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103
    url(r'^f/new/$',
        views.filter_save,              name='filter_save'),
    url(r'^f/edit/(?P<filter_id>\d+)/$',
        views.filter_edit,              name='filter_edit'),
    url(r'^f/delete/(?P<filter_id>\d+)/$',
        views.filter_drop,              name='filter_drop'),
    )

# groups {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103
    url(r'^g/new/$',
        views.group_new,         name='group_new'),
    url(r'^g/invite/(?P<group_id>\d+)/$',
        views.group_invite,      name='group_invite'),
    url(r'^g/invite/confirm/(?P<activation_key>\w+)/$',
        views.group_invite_activate, name='group_invite_activate'),
    url(r'^g/quit/(?P<group_id>\d+)/$',
        views.group_quit_ask,    name='group_quit_ask'),
    url(r'^g/quit/(?P<group_id>\d+)/confirm/$',
        views.group_quit_sure,   name='group_quit_sure'),
    url(r'^e/group/(?P<event_id>\d+)/$',
        views.group_add_event,   name='group_add_event'),
    )

# rss feeds {{{1
urlpatterns += patterns('',                     # pylint: disable-msg=C0103
     url(r'^r/upcoming/$',
         PublicUpcomingEventsFeed(), name='public_upcoming_events_rss'),
     )
