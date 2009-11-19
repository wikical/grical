from django.conf.urls.defaults import *
from django.contrib import admin
#from tagging.views import tagged_object_list
from gridcalendar.events.models import Event

info_dict = {
    'queryset': Event.objects.all(),
#    'allow_empty': False,
}

urlpatterns = patterns('',
    (r'^simplified_submission/',          'events.views.simplified_submission'),
#
    (r'^edit/(?P<event_id>\d+)/$',        'events.views.edit'),
    (r'^edit_astext/(?P<event_id>\d+)/$', 'events.views.edit_astext'),
    (r'^view_astext/(?P<event_id>\d+)/$', 'events.views.view_astext'),
    (r'^(?P<object_id>\d+)/$',            'django.views.generic.list_detail.object_detail', info_dict),
#
    (r'^list/search/',                     'events.views.list_search'),
    (r'^list/search_save/',                'events.views.save_search'),
    (r'^list/search_save_edit/(?P<savedsearch_id>\d+)/',  'events.views.saved_search_edit'),
#
    (r'^list/user/(?P<username>\w+)/',     'events.views.list_user'),
    (r'^list/my/',                         'events.views.list_my'),
    (r'^list/tags/(?P<tag>[ \-\w]*)/$' ,  'events.views.list_tag'),
# never reached because ../urls.py also has ^$ :
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict),
)
