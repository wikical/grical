from django.conf.urls.defaults import *
from django.contrib import admin
#from tagging.views import tagged_object_list
from gridcalendar.events.models import Event

info_dict = {
    'queryset': Event.objects.all(),
#    'allow_empty': False,
}

urlpatterns = patterns('',
    (r'^simplified_submission/',               'events.views.simplified_submission'),
#
    (r'^edit/(?P<event_id>\d+)/$',             'events.views.edit'),
    (r'^edit_astext/(?P<event_id>\d+)/$',      'events.views.edit_astext'),
    (r'^view_astext/(?P<event_id>\d+)/$',      'events.views.view_astext'),
    (r'^(?P<object_id>\d+)/$',                 'django.views.generic.list_detail.object_detail', info_dict),
#
    (r'^filter/list/',                         'events.views.filter_list'),
    (r'^filter/save/',                         'events.views.filter_save'),
    (r'^filter/edit/(?P<filter_id>\d+)/',      'events.views.filter_edit'),
    (r'^filter/drop/(?P<filter_id>\d+)/',      'events.views.filter_drop'),
#
    (r'^list/user/(?P<username>\w+)/',         'events.views.list_user_events'),
    (r'^list/my/',                             'events.views.list_my_events'),
    (r'^list/tags/(?P<tag>[ \-\w]*)/$' ,       'events.views.list_tag'),
    (r'^list/search/',                         'events.views.list_search'),
# never reached because ../urls.py also has ^$ :
    (r'^$',                                    'django.views.generic.list_detail.object_list', info_dict),
)
