from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin, databrowse
from django.contrib.admin import site

from gridcalendar.events.models import Event, EventUrl, EventTimechunk, EventDeadline
from gridcalendar.feeds import FeedAllComingEvents, FeedGroupEvents, ICalForEvent, ICalForGroup, ICalForFilter
from gridcalendar.groups.models import Group
from gridcalendar.groups.views import activate

#from tagging.views import tagged_object_list

databrowse.site.register(Event)
databrowse.site.register(EventUrl)
databrowse.site.register(EventTimechunk)
databrowse.site.register(EventDeadline)

admin.autodiscover()

feeds = {
    'allcomingevents': FeedAllComingEvents,
    'groupevents': FeedGroupEvents,
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
    (r'^$', 'views.root'),
)

urlpatterns += patterns('', # RSS feeds for list of events
    (r'^rss/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
)

urlpatterns += patterns('', # iCalendar feeds for list of events
    (r'^g/(?P<group_id>\d+)/ical/$',                ICalForGroup()),
    (r'^f/(?P<filter_id>\d+)/ical/$',               ICalForFilter()),
)

urlpatterns += patterns('', # HTML feeds for list of events
    (r'^e/list/user/(?P<username>\w+)/$',           'events.views.list_user_events'),
    (r'^p/events/$',                                'events.views.list_my_events'),
    (r'^e/list/tags/(?P<tag>[ \-\w]*)/$' ,          'events.views.list_tag'),
# list events in a group:
    (r'^g/(?P<group_id>\d+)/$',                     'groups.views.group'),
# searching
    (r'^q/',                                        'events.views.list_query'),
    (r'^s/(?P<query>.*)/$',                         'events.views.list_search'),
)

urlpatterns += patterns('', # views of a single event
    (r'^e/show/(?P<event_id>\d+)/raw/$',            'events.views.view_astext'),
    (r'^e/show/(?P<event_id>\d+)/$',                'events.views.show'),
    (r'^e/show/(?P<event_id>\d+)/ical/$',           ICalForEvent()),
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
