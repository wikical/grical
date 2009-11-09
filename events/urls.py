from django.conf.urls.defaults import *
from django.contrib import admin
from gridcalendar.events.models import Event

info_dict = {
    'queryset': Event.objects.all(),
#    'allow_empty': False,
}

urlpatterns = patterns('',
    (r'^edit/(?P<event_id>\d+)/$', 'gridcalendar.events.views.edit'),
    (r'^edit_astext/(?P<event_id>\d+)/$', 'gridcalendar.events.views.edit_astext'),
    (r'^(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', info_dict),
    (r'^search/', 'events.views.search'),
    (r'^u/(?P<username>\w+)/', 'events.views.search_byuser'),
    (r'^user/(?P<username>\w+)/', 'events.views.search_byuser'),
    (r'^my/', 'events.views.search_thisuser'),
    (r'^simplified_submission/', 'events.views.simplified_submission'),
    # never reached because ../urls.py also has ^$ :
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict),
)
