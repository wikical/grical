from django.conf.urls.defaults import *
from django.contrib import admin
from cloudcalendar.events.models import Event

info_dict = {
    'queryset': Event.objects.all(),
    'allow_empty': False,
}

urlpatterns = patterns('',
    #(r'^edit/(?P<event_id>\d+)/$', 'cloudcalendar.groups.views.edit'),
    #(r'^search/', 'cloudcalendar.groups.views.search'),
    #(r'^create/', 'cloudcalendar.groups.views.create'),
    #(r'^(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', info_dict),
    # never reached because ../urls.py also has ^$ :
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict),
)
