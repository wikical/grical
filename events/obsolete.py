import hashlib
from datetime import datetime, timedelta
from time import strftime
import re

from django import forms
from django.conf import settings
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import GeoIP as GeoIPup
from django.contrib.gis.utils import GeoIP
from django.contrib.sites.models import Site

from tagging.models import Tag, TaggedItem

from gridcalendar.settings import SECRET_KEY
from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, EventFormAnonymous, FilterForm
from gridcalendar.events.models import Event, EventUrl, EventTimechunk, EventDeadline, Filter, COUNTRIES
from gridcalendar.groups.models import Group



#def list_events_user_is_allowed_to_see(userid):
#    l = list()
#
#    events_public = Event.objects.filter(public_view=True)
#    for e in events_public:
#        l.append(e.id)
#
#    events_user = Event.objects.filter(user__id=userid)
#    for e in events_user:
#        l.append(e.id)
#
#    for lod in all_events_in_user_groups(userid, -1):
#        for e in lod['el']:
#            l.append(e.id)
#
#    return l


