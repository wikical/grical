import datetime
from time import strftime
import re

from django import forms
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from tagging.models import Tag, TaggedItem

from gridcalendar.gridcal.models import Event, EventUrl, EventTimechunk, EventDeadline, Filter, Group, Membership, COUNTRIES
from gridcalendar.gridcal.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, EventFormAnonymous, FilterForm

def getEventForm(user):
    """returns a simplied event form with or without the public field"""
    if user.is_authenticated():
        return SimplifiedEventForm()
    return SimplifiedEventFormAnonymous()

def generate_event_textarea(event):
    try:
         ee = event.end.strftime("%Y-%m-%d")
    except Exception:
         ee = ''

    if event.country is None:
        str_country = ''
    else:
        str_country = unicode(event.country)

    if event.timezone is None:
        str_timezone = ''
    else:
        str_timezone = str(event.timezone)

    if event.latitude is None:
        str_latitude = ''
    else:
        str_latitude = str(event.latitude)

    if event.longitude is None:
        str_longitude = ''
    else:
        str_longitude = str(event.longitude)

    t = ''
    t = t + 'acro: ' + unicode(event.acro) + '\n'
    t = t + 'titl: ' + unicode(event.title) + '\n'
    t = t + 'date: ' + event.start.strftime("%Y-%m-%d") + '\n'
    t = t + 'endd: ' + ee + '\n'
    t = t + 'tags: ' + unicode(event.tags) + '\n'
    t = t + 'view: ' + str(event.public_view) + '\n'
    t = t + 'edit: ' + str(event.public_edit) + '\n'
    t = t + 'city: ' + unicode(event.city) + '\n'
    t = t + 'addr: ' + unicode(event.address) + '\n'
    t = t + 'code: ' + unicode(event.postcode) + '\n'
    t = t + 'land: ' + str_country + '\n'
    t = t + 'tizo: ' + str_timezone + '\n'
    t = t + 'lati: ' + str_latitude + '\n'
    t = t + 'long: ' + str_longitude + '\n'

    eu = EventUrl.objects.filter(event=event.id)
    if len(eu) < 0:
        t = t + 'url: ' + '\n'
    else:
        for e in eu.all():
             t = t + 'url: ' + e.url_name + '|' + e.url + '\n'

    et = EventTimechunk.objects.filter(event=event.id)
    if len(et) < 0:
        t = t + 'time: ' + '\n'
    else:
        for e in et.all():
            t = t + 'time: ' + e.timechunk_name + '|' + str(e.timechunk_date) + '|' + str(e.timechunk_starttime) + '|' + str(e.timechunk_endtime) +'\n'

    ed = EventDeadline.objects.filter(event=event.id)
    if len(ed) < 0:
        t = t + 'dl: ' + '\n'
    else:
        for e in ed.all():
            t = t + 'dl: ' + e.deadline_name + '|' + str(e.deadline) + '\n'

    t = t + 'desc: ' + unicode(event.description) + '\n'
    return t

def StringToBool(s):
    if s is True or s is False:
        return s
    s = str(s).strip().lower()
    return not s in ['false','f','n','0','']

def is_user_in_group(user_id, group_id):
    if len(Membership.objects.filter(user__id__exact=user_id, group__id__exact=group_id)) == 1:
        return True
    else:
        return False


def is_event_viewable_by_user(event_id, user_id):
    event = Event.objects.get(id=event_id)
    if event.public_view:
        return True
    elif event.user == None:
        return True
    elif event.user.id == user_id:
        return True
    else:
        # iterating over all groups that the event belongs to
        for g in Group.objects.filter(events__id__exact=event_id):
            if is_user_in_group(user_id, g.id):
                return True
        return False

