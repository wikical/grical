from django.conf.urls.defaults import *
from django.contrib import admin
from gridcalendar.events.models import Event

info_dict = {
    'queryset': Event.objects.all(),
    'allow_empty': False,
}

urlpatterns = patterns('',
    #(r'^edit/(?P<event_id>\d+)/$', 'gridcalendar.groups.views.edit'),
    #(r'^search/', 'gridcalendar.groups.views.search'),
    #(r'^create/', 'gridcalendar.groups.views.create'),
    #(r'^(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', info_dict),
    # never reached because ../urls.py also has ^$ :
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict),
)
