import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from tagging.models import TaggedItem, Tag

from gridcalendar.events.models import Event
from gridcalendar.groups.models import Group

def all_events_in_user_groups(user_id, limit):
    """
    This function returns a list of dictionaries, which contain the group name and a list of events
    """
    finlist = list()
    if (user_id is None):
        return list()
    else:
        u = User.objects.get(id=user_id)
        groups = Group.objects.filter(membership__user=u)
        if len(groups) == 0:
            return list()
        else:
            for g in groups:
                dle = {}
                dle['group_name'] = g.name
                el = list()
                if limit > 0:
                    events = Event.objects.filter(group=g)[0:limit]
                else:
                    events = Event.objects.filter(group=g)
                for e in events:
                    el.append(e)
                dle['el'] = el
                finlist.append(dle)
            return finlist

