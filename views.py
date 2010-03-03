from datetime import datetime

from django import forms
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from tagging.models import TaggedItem
from tagging.models import Tag

from gridcalendar.events.models import Event
from gridcalendar.groups.models import Group
from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous
from gridcalendar.events.lists import filter_list, all_events_in_user_filters, events_with_user_filters, user_filters_events_list, ip_country_events, ip_continent_events, landless_events, all_events_in_user_groups, uniq_events_list
from gridcalendar.events.lists import list_up_to_max_events_ip_country_events

def root(request):
    """
    Generates the root (^/$) view of the website
    """
    user_id = request.user.id

    if request.user.is_authenticated():
        event_form = SimplifiedEventForm()
    else:
        event_form = SimplifiedEventFormAnonymous()

    if request.user.is_authenticated():
        efl = events_with_user_filters(user_id)
        uel = uniq_events_list(efl)
        events = user_filters_events_list(user_id, efl)
    else:
        efl = list()
        uel = list()
        events = list()

#----------------------------------------

    ip_country_event_list = list()
    ip_continent_event_list = list()
    landless_event_list = list()

    if len(events) < settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len(events)
        #ip_country_event_list = ip_country_events(request.META.get('REMOTE_ADDR'), user_id, uel)[0:add_thismany]
        ip_country_event_list = list_up_to_max_events_ip_country_events(request.META.get('REMOTE_ADDR'), user_id, uel, add_thismany, 'country')
    else:
        ip_country_event_list = list()

    if len(events) + len(ip_country_event_list) < settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len(events) - len(ip_country_event_list)
        #ip_continent_event_list = ip_continent_events(request.META.get('REMOTE_ADDR'), user_id, uel)[0:add_thismany]
        ip_continent_event_list = list_up_to_max_events_ip_country_events(request.META.get('REMOTE_ADDR'), user_id, uel, add_thismany, 'continent')
    else:
        ip_continent_event_list = list()

    if len(events) + len(ip_country_event_list) + len(ip_continent_event_list) < settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len(events) - len(ip_country_event_list, uel) - len(ip_continent_event_list)
        #landless_event_list = landless_events(user_id, add_thismany)
        landless_event_list = list_up_to_max_events_ip_country_events(request.META.get('REMOTE_ADDR'), user_id, uel, add_thismany, 'landless')

    return render_to_response('root.html', {
            'title': 'Welcome to the CloudCalendar',
            'form': event_form,
            'events': events,

#            hash = hashlib.sha256("%s!%s!%s" % (SECRET_KEY, filter_id, request.user.id)).hexdigest()

            'ip_country_event_list': ip_country_event_list,
            'ip_continent_event_list': ip_continent_event_list,
            'landless_event_list': landless_event_list,

#            'group_events': all_events_in_user_groups(request.user.id, 5),
            'group_events': list(),
        }, context_instance=RequestContext(request))



# for this decorator, see
# http://docs.djangoproject.com/en/1.0/topics/auth/#the-login-required-decorator
@login_required
def settings_page(request):
    # user is logged in
    fl = filter_list(request.user.id)
    u = User(request.user)
    groups = Group.objects.filter(membership__user=u)
    return render_to_response('settings.html', {'title': 'settings', 'filter_list': fl, 'groups': groups}, context_instance=RequestContext(request))
