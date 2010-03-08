from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin, databrowse
from django.contrib.admin import site

from gridcal.models import Event, EventUrl, EventTimechunk, EventDeadline, Group
from gridcal.views_groups import activate

from gridcal.feeds import FeedAllComingEvents, FeedGroupEvents
from gridcal.feeds import ICalForEvent, ICalForGroupAuth, ICalForGroupHash, ICalForFilterAuth, ICalForFilterHash, ICalForSearchAuth, ICalForSearchHash

#from tagging.views import tagged_object_list

databrowse.site.register(Event)
databrowse.site.register(EventUrl)
databrowse.site.register(EventTimechunk)
databrowse.site.register(EventDeadline)

admin.autodiscover()

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
    (r'^$',                                                             'gridcal.views.root'),
)

###############################################################################

urlpatterns += patterns('', # views of a single event
    (r'^e/show/(?P<event_id>\d+)/$',                                    'gridcal.views.show'),
    (r'^e/show/(?P<event_id>\d+)/raw/$',                                'gridcal.views.view_astext'),
    (r'^e/show/(?P<event_id>\d+)/ical/$',                               ICalForEvent()),
)

###############################################################################

urlpatterns += patterns('', # events created by the user logged in
    (r'^p/events/$',                                                    'gridcal.views.list_my_events'),
)

urlpatterns += patterns('', # events matching a filter
    (r'^f/(?P<filter_id>\d+)/ical/$',                                   ICalForFilterAuth()),
    (r'^f/(?P<filter_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',    ICalForFilterHash()),
    (r'^f/(?P<filter_id>\d+)/rss/$',                                    'gridcal.rss.rss_for_filter_auth'),
    (r'^f/(?P<filter_id>\d+)/rss/(?P<user_id>\d+)/(?P<hash>\w+)/$',     'gridcal.rss.rss_for_filter_hash'),
)

urlpatterns += patterns('', # events matching some query
    (r'^q/',                                                            'gridcal.views.list_query'),
#
    (r'^s/(?P<query>.*)/ical/$',                                        ICalForSearchAuth()),
    (r'^s/(?P<query>.*)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',         ICalForSearchHash()),
    (r'^s/(?P<query>.*)/rss/$',                                         'gridcal.rss.rss_for_search'),
    (r'^s/(?P<query>.*)/$',                                             'gridcal.views.list_search'),
#
    (r'^t/(?P<tag>[ \-\w]*)/$' ,                                        'gridcal.views.list_tag'),
)

urlpatterns += patterns('', # events in a group
    (r'^g/(?P<group_id>\d+)/ical/$',                                    ICalForGroupAuth()),
    (r'^g/(?P<group_id>\d+)/ical/(?P<user_id>\d+)/(?P<hash>\w+)/$',     ICalForGroupHash()),
    (r'^g/(?P<group_id>\d+)/rss/$',                                     'gridcal.rss.rss_for_group_auth'),
    (r'^g/(?P<group_id>\d+)/rss/(?P<user_id>\d+)/(?P<hash>\w+)/$',      'gridcal.rss.rss_for_group_hash'),
    (r'^g/(?P<group_id>\d+)/$',                                         'gridcal.views_groups.group'),
)

###############################################################################

urlpatterns += patterns('',
# list events created by a certain user (commented for now because of privacy concerns)
#   (r'^e/list/user/(?P<username>\w+)/$',                               'gridcal.views.list_user_events'),
)

###############################################################################

urlpatterns += patterns('',
# creating and editing events:
    (r'^e/new/$',                                   'gridcal.views.simplified_submission'),
    url(r'^e/edit/(?P<event_id>\d+)/$',             'gridcal.views.edit', {'raw': False}, name="event_edit"),
    url(r'^e/edit/(?P<event_id>\d+)/raw/$',         'gridcal.views.edit', {'raw': True}, name="event_edit_raw"),
# settings
    (r'^p/settings/$',                              'gridcal.views.settings_page'),
# filter management:
    (r'^p/filters/$',                               'gridcal.views.filter_list_view'),
    (r'^f/new/$',                                   'gridcal.views.filter_save'),
    (r'^f/edit/(?P<filter_id>\d+)/$',               'gridcal.views.filter_edit'),
    (r'^f/delete/(?P<filter_id>\d+)/$',             'gridcal.views.filter_drop'),
# creating groups:
    (r'^g/new/$',                                   'gridcal.views_groups.create'),
# adding a user to a group:
    (r'^g/invite/(?P<group_id>\d+)/$',              'gridcal.views_groups.invite'),
    url(r'^g/invite/confirm/(?P<activation_key>\w+)/$',
                           activate,
                           name='invitation_activate'),
# leaving a group:
    (r'^g/quit/(?P<group_id>\d+)/$',                'gridcal.views_groups.quit_group_ask'),
    (r'^g/quit/(?P<group_id>\d+)/confirm/$',        'gridcal.views_groups.quit_group_sure'),
# adding events to groups:
    (r'^e/group/(?P<event_id>\d+)/$',               'gridcal.views_groups.add_event'),
# list of groups:
    (r'^p/groups/$',                                'gridcal.views_groups.list_my_groups'),
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
