import datetime
import csv
from django.http import HttpResponse
from gridcalendar.events.models import Event, EventUrl, EventTimechunk, EventDeadline
from tagging.models import TaggedItem
from tagging.models import Tag
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from tagging.models import TaggedItem
from tagging.models import Tag

from django.forms.models import inlineformset_factory

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from django.contrib.sites.models import Site

from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, EventFormAnonymous

# notice that an anonymous user get a form without the 'public' field (simplified)

def getEventForm(user):
    """returns a simplied event form with or without the public field"""
    if user.is_authenticated():
        return SimplifiedEventForm()
    return SimplifiedEventFormAnonymous()

def edit(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
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
        EventUrlInlineFormSet       = inlineformset_factory(Event, EventUrl, extra=1)
        EventTimechunkInlineFormSet = inlineformset_factory(Event, EventTimechunk, extra=1)
        EventDeadlineInlineFormSet  = inlineformset_factory(Event, EventDeadline, extra=1)
        if request.method == 'POST':
            ef_url = EventUrlInlineFormSet(request.POST, instance=event)
            ef_timechunk = EventTimechunkInlineFormSet(request.POST, instance=event)
            ef_deadline = EventDeadlineInlineFormSet(request.POST, instance=event)
            if request.user.is_authenticated():
                ef = EventForm(request.POST, instance=event)
            else:
                ef = EventFormAnonymous(request.POST, instance=event)
            if ef.is_valid() & ef_url.is_valid() & ef_timechunk.is_valid() & ef_deadline.is_valid() :
                ef.save()
                ef_url.save()
                ef_timechunk.save()
                ef_deadline.save()
                # TODO: look in a thread for all users who wants to receive an email notification and send it
                return HttpResponseRedirect('/')
            else:
                templates = {'form': ef, 'formset_url': ef_url, 'formset_timechunk': ef_timechunk, 'formset_deadline': ef_deadline, 'event_id': event_id }
                return render_to_response('events/edit.html', templates, context_instance=RequestContext(request))
        else:
            if request.user.is_authenticated():
                ef = EventForm(instance=event)
            else:
                ef = EventFormAnonymous(instance=event)
            ef_url = EventUrlInlineFormSet(instance=event)
            ef_timechunk = EventTimechunkInlineFormSet(instance=event)
            ef_deadline = EventDeadlineInlineFormSet(instance=event)
            templates = {'form': ef, 'formset_url': ef_url, 'formset_timechunk': ef_timechunk, 'formset_deadline': ef_deadline, 'event_id': event_id }
            return render_to_response('events/edit.html', templates, context_instance=RequestContext(request))



def generate_event_textarea(event):

    try:
         ee = event.end.strftime("%Y-%m-%d")
    except Exception:
         ee = ''

    t = ''
    t = t + 'acro: ' + unicode(event.acro) + '\n'
    t = t + 'titl: ' + unicode(event.title) + '\n'
    t = t + 'date: ' + event.start.strftime("%Y-%m-%d") + '\n'
    t = t + 'endd: ' + ee + '\n'
    t = t + 'tags: ' + unicode(event.tags) + '\n'
    t = t + 'publ: ' + str(event.public) + '\n'

    t = t + 'city: ' + unicode(event.city) + '\n'
    t = t + 'addr: ' + unicode(event.address) + '\n'
    t = t + 'code: ' + unicode(event.postcode) + '\n'
    t = t + 'land: ' + unicode(event.country) + '\n'
    t = t + 'tizo: ' + str(event.timezone) + '\n'
    t = t + 'lati: ' + str(event.latitude) + '\n'
    t = t + 'long: ' + str(event.longitude) + '\n'

    eu = EventUrl.objects.filter(event=event.id)
    for e in eu.all():
         t = t + 'url: ' + e.url_name + '|' + e.url + '\n'

    et = EventTimechunk.objects.filter(event=event.id)
    for e in et.all():
         t = t + 'time: ' + e.timechunk_name + '|' + str(e.timechunk_date) + '|' + str(e.timechunk_starttime) + '|' + str(e.timechunk_endtime) +'\n'

    ed = EventDeadline.objects.filter(event=event.id)
    for e in ed.all():
         t = t + 'dl: ' + e.deadline_name + '|' + str(e.deadline) + '\n'

    t = t + 'desc: ' + unicode(event.description) + '\n'
    return t


def StringToBool(s):
    if s is True or s is False:
        return s
    s = str(s).strip().lower()
    return not s in ['false','f','n','0','']

def view_astext(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('index.html',
                    {'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if (not event.public) and (event.user.id != request.user.id):
        return render_to_response('index.html',
                {'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            return render_to_response('index.html',
                {'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
        else:
            event_textarea = generate_event_textarea(event)
            templates = { 'event_textarea': event_textarea, 'event_id': event_id }
            return render_to_response('events/view_astext.html', templates, context_instance=RequestContext(request))

def edit_astext(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('index.html',
                    {'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter
    if (event.user is not None) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
        return render_to_response('index.html',
                {'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
###############################################################################
        if request.method == 'POST':
            if request.user.is_authenticated():
#------------------------------------------------------------------------------
                if 'event_astext' in request.POST:
                    try:

                        t = request.POST['event_astext'].replace(": ", ":")
                        event_attr_list = t.splitlines()
                        event_attr_dict = dict(item.split(":",1) for item in event_attr_list)

                        event.acro        = event_attr_dict['acro']
                        event.title       = event_attr_dict['titl']
#                        event.start       = strptime(event_attr_dict['date'])
                        event.start       = event_attr_dict['date']
                        event.end         = event_attr_dict['endd']
                        event.tags        = event_attr_dict['tags']
                        event.public      = StringToBool(event_attr_dict['publ'])
                        event.city        = event_attr_dict['city']
                        event.address     = event_attr_dict['addr']
                        event.postcode    = event_attr_dict['code']
                        event.country     = event_attr_dict['land']
                        event.timezone    = event_attr_dict['tizo']
                        event.latitude    = event_attr_dict['lati']
                        event.longitude   = event_attr_dict['long']
                        event.description = event_attr_dict['desc']
                        EventUrl.objects.filter(event=event_id).delete()
                        EventTimechunk.objects.filter(event=event_id).delete()
                        EventDeadline.objects.filter(event=event_id).delete()
                        for textline in event_attr_list:
                            if textline[0:4] == 'url:':
                                line_attr_list = textline[4:].split("|",1)
                                eu = EventUrl(event=event, url_name=line_attr_list[0], url=line_attr_list[1])
                                eu.save(force_insert=True)
                            if textline[0:5] == 'time:':
                                line_attr_list = textline[5:].split("|",3)
                                et = EventTimechunk(event=event, timechunk_name=line_attr_list[0], timechunk_date=line_attr_list[1], timechunk_starttime=line_attr_list[2], timechunk_endtime=line_attr_list[3])
                                et.save(force_insert=True)
                            if textline[0:3] == 'dl:':
                                line_attr_list = textline[3:].split("|",1)
                                ed = EventDeadline(event=event, deadline_name=line_attr_list[0], deadline=line_attr_list[1])
                                ed.save(force_insert=True)
                        event.save()
                        return HttpResponseRedirect('/')
                    except Exception:
                        return render_to_response('error.html', {'form': getEventForm(request.user), 'message_col1': _("Syntax error, nothing was saved. Click the back button in your browser and try again.")},
                    context_instance=RequestContext(request))
                else:
                    message = _("You submitted an empty form.")
                    return HttpResponse(message)
#------------------------------------------------------------------------------
            else:
                return render_to_response('index.html',
                    {'form': getEventForm(request.user),
                    'message_col1': _('You are not allowed to edit the event with the following number') +
                    ": " + str(event_id) + ". " +
                    _("Maybe it is because you are not logged in with the right account") + "."},
                    context_instance=RequestContext(request))
###############################################################################
        else:
###############################################################################
            event_textarea = generate_event_textarea(event)
            templates = { 'event_textarea': event_textarea, 'event_id': event_id }
            return render_to_response('events/edit_astext.html', templates, context_instance=RequestContext(request))
###############################################################################

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
        events = Event.objects.filter(title__icontains=q)
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

def search_byuser(request, username):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
            events = Event.objects.all()
            events = Event.objects.filter(user=useridtmp)
            events = Event.objects.filter(public=True)
            if len(events) == 0:
                return render_to_response('index.html',
                    {'message_col1': _("Your search didn't get any result") + "."},
                    context_instance=RequestContext(request))
            else:
                return render_to_response('events_of_user.html',
                    {'events': events, 'username': username},
                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return render_to_response('index.html',
                {'message_col1': _("User does not exist") + "."},
                context_instance=RequestContext(request))
    else:
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
            events = Event.objects.all()
            events = Event.objects.filter(user=useridtmp)
            if len(events) == 0:
                return render_to_response('index.html',
                    {'message_col1': _("Your search didn't get any result") + "."},
                    context_instance=RequestContext(request))
            else:
                return render_to_response('events_of_user.html',
                    {'events': events, 'username': username},
                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return render_to_response('index.html',
                {'message_col1': _("User does not exist") + "."},
                context_instance=RequestContext(request))

def search_thisuser(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('index.html',
                {'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
    else:
        events = Event.objects.all()
        events = Event.objects.filter(user=request.user)
        if len(events) == 0:
            return render_to_response('index.html',
                {'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
        else:
            return render_to_response('my_events.html',
                {'events': events},
                context_instance=RequestContext(request))

