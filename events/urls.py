# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *

from gridcalendar.events import views, views_groups, rss, feeds
#from events.feeds import ICalForEvent, ICalForGroupAuth, ICalForGroupHash, ICalForFilterAuth, ICalForFilterHash, ICalForSearchAuth, ICalForSearchHash

urlpatterns = patterns('',
    url(r'^$',                                                          views.root,                         name='root'),
)

urlpatterns += patterns('', # views of a single event
    url(r'^e/new/$',                                                    views.event_new,                    name='event_new'),
    url(r'^e/new/raw/$',                                                views.event_new_raw,                name='event_new_raw'),
    url(r'^e/edit/(?P<event_id>\d+)/$',                                 views.event_edit,                   name='event_edit'),
    url(r'^e/edit/(?P<event_id>\d+)/raw/$',                             views.event_edit_raw,               name='event_edit_raw'),
    url(r'^e/show/(?P<event_id>\d+)/$',                                 views.event_show,                   name='event_show'),
    url(r'^e/show/(?P<event_id>\d+)/raw/$',                             views.event_show_raw,               name='event_show_raw'),
    url(r'^e/show/(?P<event_id>\d+)/ical/$',                            feeds.ICalForEvent(),               name='event_show_ical'),
)

urlpatterns += patterns('', # events matching a filter
    url(r'^f/(?P<filter_id>\d+)/ical/$',                                feeds.ICalForFilterAuth(),          name='list_events_filter_ical'),
    url(r'^f/(?P<filter_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$', feeds.ICalForFilterHash(),          name='list_events_filter_ical_hashed'),
    url(r'^f/(?P<filter_id>\d+)/rss/$',                                 rss.rss_for_filter_auth,            name='list_events_filter_rss'),
    url(r'^f/(?P<filter_id>\d+)/rss/(?P<user_id>\d+)/(?P<hash>\w+)/$',  rss.rss_for_filter_hash,            name='list_events_filter_rss_hashed'),
)

urlpatterns += patterns('', # events matching some query
    url(r'^q/',                                                         views.query,                        name='query'),
    url(r'^s/(?P<query>.*)/ical/$',                                     feeds.ICalForSearchAuth(),          name='list_events_search_ical'),
    url(r'^s/(?P<query>.*)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',      feeds.ICalForSearchHash(),          name='list_events_search_ical_hashed'),
    url(r'^s/(?P<query>.*)/rss/$',                                      rss.rss_for_search,                 name='list_events_search_rss'),
    url(r'^s/(?P<query>.*)/$',                                          views.list_events_search,           name='list_events_search'),
    url(r'^t/(?P<tag>[ \-\w]*)/$' ,                                     views.list_events_tag,              name='list_events_tag'),
)

urlpatterns += patterns('', # events in a group
    url(r'^g/(?P<group_id>\d+)/ical/$',                                 feeds.ICalForGroupAuth(),           name='list_events_group_ical'),
    url(r'^g/(?P<group_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',  feeds.ICalForGroupHash(),           name='list_events_group_ical_hashed'),
    url(r'^g/(?P<group_id>\d+)/rss/$',                                  rss.rss_for_group_auth,             name='list_events_group_rss'),
    url(r'^g/(?P<group_id>\d+)/rss/(?P<user_id>\d+)/(?P<hash>\w+)/$',   rss.rss_for_group_hash,             name='list_events_group_rss_hashed'),
    url(r'^g/(?P<group_id>\d+)/$',                                      views_groups.list_events_group,     name='list_events_group'),
)

urlpatterns += patterns('',
    url(r'^p/events/$',                                                 views.list_events_my,               name='list_events_my'),
# commented for now because of privacy concerns:
#   url(r'^e/list/user/(?P<username>\w+)/$',                            views.list_events_of_user,          name='list_events_of_user'),
)

urlpatterns += patterns('', # preferences
    url(r'^p/settings/$',                                               views.settings_page,                name='settings'),
    url(r'^p/filters/$',                                                views.list_filters_my,              name='list_filters_my'),
    url(r'^p/groups/$',                                                 views_groups.list_groups_my,        name='list_groups_my'),
)

urlpatterns += patterns('', # filter management:
    url(r'^f/new/$',                                                    views.filter_save,                  name='filter_save'),
    url(r'^f/edit/(?P<filter_id>\d+)/$',                                views.filter_edit,                  name='filter_edit'),
    url(r'^f/delete/(?P<filter_id>\d+)/$',                              views.filter_drop,                  name='filter_drop'),
)

urlpatterns += patterns('', # groups
    url(r'^g/new/$',                                                    views_groups.group_new,             name='group_new'),
    url(r'^g/invite/(?P<group_id>\d+)/$',                               views_groups.group_invite,          name='group_invite'),
    url(r'^g/invite/confirm/(?P<activation_key>\w+)/$',                 views_groups.group_invite_activate, name='group_invite_activate'),
    url(r'^g/quit/(?P<group_id>\d+)/$',                                 views_groups.group_quit_ask,        name='group_quit_ask'),
    url(r'^g/quit/(?P<group_id>\d+)/confirm/$',                         views_groups.group_quit_sure,       name='group_quit_sure'),
    url(r'^e/group/(?P<event_id>\d+)/$',                                views_groups.group_add_event,       name='group_add_event'),
)
