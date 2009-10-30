import datetime
from django.http import HttpResponse
from cloudcalendar.events.models import Event
from tagging.models import TaggedItem
from tagging.models import Tag
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from tagging.models import TaggedItem
from tagging.models import Tag

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect

from cloudcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, EventFormAnonymous

# notice that an anonymous user get a form without the 'public' field (simplified)

def getEventForm(user):
    """returns a simplied event form with or without the public field"""
    if user.is_authenticated():
        return SimplifiedEventForm()
    return SimplifiedEventFormAnonymous()

def edit(request, event_id):
    pass
#    try:
#        event = Event.objects.get(id=event_id)
#    except Event.DoesNotExist:
#        return render_to_response('index.html',
#                    {'form': getEventForm(request.user),
#                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
#                    context_instance=RequestContext(request))
#    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter
#    if (event.user is not None) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
#        return render_to_response('index.html',
#                {'form': getEventForm(request.user),
#                'message_col1': _('You are not allowed to edit the event with the following number') +
#                ": " + str(event_id) + ". " +
#                _("Maybe it is because you are not logged in with the right account") + "."},
#                context_instance=RequestContext(request))
#    else:
#        if request.method == 'POST':
#            if request.user.is_authenticated():
#                ef = EventForm(request.POST, instance=event)
#            else:
#                ef = EventFormAnonymous(request.POST, instance=event)
#            if ef.is_valid():
#                ef.save()
#                # TODO: look in a thread for all users who wants to receive an email notification and send it
#                return HttpResponseRedirect('/')
#            else:
#                return render_to_response('events/edit.html', {'form': ef}, context_instance=RequestContext(request))
#        else:
#            if request.user.is_authenticated():
#                form = EventForm(instance=event)
#            else:
#                form = EventFormAnonymous(instance=event)
#            return render_to_response('events/edit.html', {'form': form}, context_instance=RequestContext(request))

def create(request):
    if not request.user.is_authenticated():
        return render_to_response('groups/no_authenticated.html', {}, context_instance=RequestContext(request))
    form = NewGroupForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            # TODO: notify all invited members of the group
            return HttpResponseRedirect(request.get_host())
        else:
            return render_to_response('groups/create.html', {'form': form}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(request.get_host())

def answer_invitation(request, group_id):
    """A user can accept or deny the invitation"""
    pass
