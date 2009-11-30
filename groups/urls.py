from django.conf.urls.defaults import *
from django.contrib import admin
from gridcalendar.groups.models import Group

info_dict = {
    'queryset': Group.objects.all(),
    'allow_empty': False,
}

urlpatterns = patterns('',
    (r'^create/', 'gridcalendar.groups.views.create'),
    (r'^list/', 'gridcalendar.groups.views.list_my_groups'),
    (r'^quit/(?P<group_id>\d+)/$', 'gridcalendar.groups.views.quit_group'),
    (r'^add_event/(?P<event_id>\d+)/$', 'gridcalendar.groups.views.add_event'),
    #(r'^edit/(?P<event_id>\d+)/$', 'gridcalendar.groups.views.edit'),
    #(r'^search/', 'gridcalendar.groups.views.search'),
    #(r'^(?P<object_id>\d+)/$', 'django.views.generic.list_detail.object_detail', info_dict),
# never reached because ../urls.py also has ^$ :
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict),
)
