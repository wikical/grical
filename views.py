from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render_to_response
from gridcalendar.events.models import Event
from tagging.models import TaggedItem
from tagging.models import Tag
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response

from django.template import RequestContext

from django.db.models import Q

from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous

def index(request):
    if request.user.is_authenticated():
        ev = SimplifiedEventForm()
# show all events
        coming_events = Event.objects.filter( Q(start__gte=datetime.now()) & ( Q(public=True) | Q(user=request.user)) )[:100]
        past_events   = Event.objects.filter( Q(start__lt=datetime.now()) & ( Q(public=True) | Q(user=request.user)) )[:100]
# show only events of this user
#       coming_events = Event.objects.filter(user=request.user).filter(start__gte=datetime.now())[:5]
    else:
        ev = SimplifiedEventFormAnonymous()
        coming_events = Event.objects.filter(start__gte=datetime.now()).exclude(public=False)[:100]
        past_events   = Event.objects.filter(start__lt=datetime.now()).exclude(public=False)[:100]
      # coming_events = Event.objects.all()
    return render_to_response('index.html', {'title': 'home', 'form': ev, 'coming_events': coming_events, 'past_events': past_events}, context_instance=RequestContext(request))

# for this decorator, see
# http://docs.djangoproject.com/en/1.0/topics/auth/#the-login-required-decorator
@login_required
def settings(request):
    # user is logged in
    return render_to_response('settings.html', {'title': 'settings'}, context_instance=RequestContext(request))
