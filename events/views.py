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
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return render_to_response('index.html',
                    {'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter
    if (event.user is not None) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
        return render_to_response('index.html',
                {'form': getEventForm(request.user),
                'message_col1': _('You are not allowed to edit the event with the following number') +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            if request.user.is_authenticated():
                ef = EventForm(request.POST, instance=event)
            else:
                ef = EventFormAnonymous(request.POST, instance=event)
            if ef.is_valid():
                ef.save()
                # TODO: look in a thread for all users who wants to receive an email notification and send it
                return HttpResponseRedirect('/')
            else:
                return render_to_response('events/edit.html', {'form': ef}, context_instance=RequestContext(request))
        else:
            if request.user.is_authenticated():
                form = EventForm(instance=event)
            else:
                form = EventFormAnonymous(instance=event)
            return render_to_response('events/edit.html', {'form': form}, context_instance=RequestContext(request))

def simplified_submission(request):
    if request.method == 'POST':
        if request.user.is_authenticated():
            sef = SimplifiedEventForm(request.POST)
        else:
            sef = SimplifiedEventFormAnonymous(request.POST)

        if sef.is_valid():
            cd = sef.cleaned_data
            # create a new entry and saves the data
            if request.user.is_authenticated():
                public_value = public=cd['public']
            else:
                public_value = True
            e = Event(user_id=request.user.id, title=cd['title'], start=cd['start'],
                        tags=cd['tags'], public=public_value)
            e.save()
            return HttpResponseRedirect('/events/edit/' + str(e.id)) ;
            # TODO: look in a thread for all users who wants to receive an email notification and send it
        else:
            return render_to_response('index.html', {'form': sef}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(request.get_host())

def tag(request, tag_name):
#    try:
#        tag_by_name = Tag.objects.get(name=tag_name)
#    except:
#        return HttpResponse("There is no tag '%s'." % tag_name)
    t = get_object_or_404(Tag, name=tag_name)
    retrieved = TaggedItem.objects.get_by_model(Event, t)
    return render_to_response('events/events.html', {'events_list': retrieved})
    #return HttpResponse("Number of objects tagged with %s : %d." % (tag_name, len(retrieved)))

def id(request, event_id):
    e = get_object_or_404(Event, pk=event_id)
    return render_to_response('events/event.html', {'event': e})
    #return HttpResponse("You're looking at id %s." % id)

def search(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q']
        events = Event.objects.filter(name__icontains=q)
        if len(events) == 0:
            return render_to_response('index.html',
                {'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
        else:
            return render_to_response('search_results.html',
                {'events': events, 'query': q},
                context_instance=RequestContext(request))
    else:
        return render_to_response('index.html',
            {'message_col1': _("You have submitted a search with no content") + "."},
            context_instance=RequestContext(request))

