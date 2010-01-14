from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin, databrowse
from django.contrib.admin import site

from gridcalendar.events.models import Event, EventUrl, EventTimechunk, EventDeadline
from gridcalendar.groups.models import Group

from gridcalendar.groups.views import activate

from gridcalendar.feeds import FeedAllComingEvents, FeedGroupEvents
from gridcalendar.feeds import ICalForEvent, ICalForGroupAuth, ICalForGroupHash, ICalForFilterAuth, ICalForFilterHash, ICalForSearchAuth, ICalForSearchHash

#from tagging.views import tagged_object_list

databrowse.site.register(Event)
databrowse.site.register(EventUrl)
databrowse.site.register(EventTimechunk)
databrowse.site.register(EventDeadline)

admin.autodiscover()

rss_feeds = {
    'allcomingevents':  FeedAllComingEvents,
}

urlpatterns = patterns('',
    (r'^a/admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^a/admin/(.*)', admin.site.root),
    (r'^a/db/(.*)', databrowse.site.root),
)

urlpatterns += patterns('',
    (r'^a/accounts/', include('registration.urls')),
    (r'^a/accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
)

###############################################################################

urlpatterns += patterns('',
    (r'^$',                                                             'views.root'),
)

#urlpatterns += patterns('', # RSS feeds for list of events
#    (r'^e/(?P<url>.*)/rss/$',                                           'django.contrib.syndication.views.feed', {'feed_dict': rss_feeds}),
#)

###############################################################################

urlpatterns += patterns('', # events created by the user logged in
    (r'^p/events/$',                                                    'events.views.list_my_events'),
)

urlpatterns += patterns('', # events matching a filter
    (r'^f/(?P<filter_id>\d+)/ical/$',                                   ICalForFilterAuth()),
    (r'^f/(?P<filter_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',    ICalForFilterHash()),
    (r'^f/(?P<filter_id>\d+)/rss/$',                                    'rss.rss_for_filter_auth'),
    (r'^f/(?P<filter_id>\d+)/rss/(?P<user_id>\d+)/(?P<hash>\w+)/$',     'rss.rss_for_filter_hash'),
)

urlpatterns += patterns('', # events matching some query
    (r'^q/',                                                            'events.views.list_query'),
#
    (r'^s/(?P<query>.*)/ical/$',                                        ICalForSearchAuth()),
    (r'^s/(?P<query>.*)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',         ICalForSearchHash()),
    (r'^s/(?P<query>.*)/rss/$',                                         'rss.rss_for_search'),
    (r'^s/(?P<query>.*)/$',                                             'events.views.list_search'),
#
    (r'^t/(?P<tag>[ \-\w]*)/$' ,                                        'events.views.list_tag'),
)

urlpatterns += patterns('', # events in a group
    (r'^g/(?P<group_id>\d+)/ical/$',                                    ICalForGroupAuth()),
    (r'^g/(?P<group_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',     ICalForGroupHash()),
    (r'^g/(?P<group_id>\d+)/rss/$',                                     'rss.rss_for_group_auth'),
    (r'^g/(?P<group_id>\d+)/rss/(?P<user_id>\d+)/(?P<hash>\w+)/$',      'rss.rss_for_group_hash'),
    (r'^g/(?P<group_id>\d+)/$',                                         'groups.views.group'),
)

###############################################################################

urlpatterns += patterns('',
# list events created by a certain user (commented for now because of privacy concerns)
#   (r'^e/list/user/(?P<username>\w+)/$',                               'events.views.list_user_events'),
)

urlpatterns += patterns('', # views of a single event
    (r'^e/show/(?P<event_id>\d+)/$',                                    'events.views.show'),
    (r'^e/show/(?P<event_id>\d+)/raw/$',                                'events.views.view_astext'),
    (r'^e/show/(?P<event_id>\d+)/ical/$',                               ICalForEvent()),
)

###############################################################################

urlpatterns += patterns('',
# creating and editing events:
    (r'^e/new/$',                                   'events.views.simplified_submission'),
    (r'^e/edit/(?P<event_id>\d+)/$',                'events.views.edit'),
    (r'^e/edit/(?P<event_id>\d+)/raw/$',            'events.views.edit_raw'),
# settings
    (r'^p/settings/$', 'views.settings_page'),
# filter management:
    (r'^p/filters/$',                               'events.views.filter_list_view'),
    (r'^f/new/$',                                   'events.views.filter_save'),
    (r'^f/edit/(?P<filter_id>\d+)/$',               'events.views.filter_edit'),
    (r'^f/delete/(?P<filter_id>\d+)/$',             'events.views.filter_drop'),
# creating groups:
    (r'^g/new/$',                                   'groups.views.create'),
# adding a user to a group:
    (r'^g/invite/(?P<group_id>\d+)/$',              'groups.views.invite'),
    url(r'^g/invite/confirm/(?P<activation_key>\w+)/$',
                           activate,
                           name='invitation_activate'),
# leaving a group:
    (r'^g/quit/(?P<group_id>\d+)/$',                'groups.views.quit_group_ask'),
    (r'^g/quit/(?P<group_id>\d+)/confirm/$',        'groups.views.quit_group_sure'),
# adding events to groups:
    (r'^e/(?P<event_id>\d+)/group/$',               'groups.views.add_event'),
# list of groups:
    (r'^p/groups/$',                                'groups.views.list_my_groups'),
)

###############################################################################

urlpatterns += patterns('',
    #(r'^comments/', include('django.contrib.comments.urls')),
)


# see http://docs.djangoproject.com/en/1.0/howto/static-files/
if settings.DEBUG:
    urlpatterns += patterns('',
        ('^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
