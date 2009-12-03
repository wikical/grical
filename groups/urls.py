from django.conf.urls.defaults import *
from django.contrib import admin
from gridcalendar.groups.models import Group
from gridcalendar.groups.views import activate

info_dict = {
    'queryset': Group.objects.all(),
    'allow_empty': False,
}

urlpatterns = patterns('',
    url(r'^activate/(?P<activation_key>\w+)/$',
                           activate,
                           name='invitation_activate'),
    (r'^create/', 'gridcalendar.groups.views.create'),
    (r'^list/', 'gridcalendar.groups.views.list_my_groups'),
    (r'^quit/(?P<group_id>\d+)/(?P<sure>\d+)/$', 'gridcalendar.groups.views.quit_group'),
    (r'^add_event/(?P<event_id>\d+)/$', 'gridcalendar.groups.views.add_event'),
    (r'^(?P<group_id>\d+)/$', 'gridcalendar.groups.views.group'),
    (r'^invite/(?P<group_id>\d+)/$', 'gridcalendar.groups.views.invite'),
    #(r'^edit/(?P<event_id>\d+)/$', 'gridcalendar.groups.views.edit'),
    #(r'^search/', 'gridcalendar.groups.views.search'),
# never reached because ../urls.py also has ^$ :
    (r'^$', 'django.views.generic.list_detail.object_list', info_dict),
)
