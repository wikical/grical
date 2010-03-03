import datetime
from time import strftime
import re

from django import forms
from django import http
from django.db.models import Q, Max
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from tagging.models import Tag, TaggedItem

from gridcalendar.events.functions import generate_event_textarea, StringToBool, getEventForm
from gridcalendar.events.lists import list_search_get, filter_list
from gridcalendar.events.models import Event, EventUrl, EventTimechunk, EventDeadline, Filter, COUNTRIES
from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, EventFormAnonymous, FilterForm

# notice that an anonymous user get a form without the 'public_view' field (simplified)

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
                public_view_value = public_view=cd['public_view']
            else:
                public_view_value = True
            e = Event(user_id=request.user.id, title=cd['title'], start=cd['start'],
                        tags=cd['tags'], public_view=public_view_value)
            e.save()
            return HttpResponseRedirect('/e/edit/' + str(e.id) + '/') ;
            # TODO: look in a thread for all users who wants to receive an email notification and send it
        else:
            return render_to_response('index.html', {'title': 'edit step 1', 'form': sef}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(request.get_host())

def edit(request, event_id):

    # check if the event exists
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))

    # check if the user is allowed to edit this event
    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter

    if (not event.public_edit):
        if (not request.user.is_authenticated()):
            return render_to_response('error.html',
                        {'title': 'error', 'form': getEventForm(request.user),
                        'message_col1': _('Users which are not logged-in are not allowed to edit the event with number') +
                        ": " + str(event_id) + ". " +
                        _("Please log-in and try again") + "."},
                        context_instance=RequestContext(request))
        else:
            if (event.user == None):
                if (event.user.id != request.user.id):
                    return render_to_response('error.html',
                        {'title': 'error', 'form': getEventForm(request.user),
                        'message_col1': _('You are not allowed to edit the event with the following number') +
                        ": " + str(event_id) + " " +
                        _("because you are not logged in with the right account") + "."},
                        context_instance=RequestContext(request))
            else:
                break



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
                return HttpResponseRedirect('/e/show/' + event_id + '/')
            else:
                templates = {'title': 'edit event', 'form': ef, 'formset_url': ef_url, 'formset_timechunk': ef_timechunk, 'formset_deadline': ef_deadline, 'event_id': event_id }
                return render_to_response('events/edit.html', templates, context_instance=RequestContext(request))
        else:
            if request.user.is_authenticated():
                ef = EventForm(instance=event)
            else:
                ef = EventFormAnonymous(instance=event)
            ef_url = EventUrlInlineFormSet(instance=event)
            ef_timechunk = EventTimechunkInlineFormSet(instance=event)
            ef_deadline = EventDeadlineInlineFormSet(instance=event)
            templates = {'title': 'edit event', 'form': ef, 'formset_url': ef_url, 'formset_timechunk': ef_timechunk, 'formset_deadline': ef_deadline, 'event_id': event_id }
            return render_to_response('events/edit.html', templates, context_instance=RequestContext(request))

def edit_raw(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter
    if (not event.public_edit) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
                if 'event_astext' in request.POST:
#                    try:
                        t = request.POST['event_astext'].replace(": ", ":")
                        event_attr_list = t.splitlines()
                        event_attr_dict = dict(item.split(":",1) for item in event_attr_list)

                        if re.match('\d\d\d\d\-\d\d\-\d\d$', event_attr_dict['endd']) is not None:
                            event_end = event_attr_dict['endd']
                        else:
                            event_end = None

                        if re.match('\d+\.\d*$', event_attr_dict['lati']) is not None:
                            event_lati = event_attr_dict['lati']
                        else:
                            event_lati = None

                        if re.match('\d+\.\d*$', event_attr_dict['long']) is not None:
                            event_long = event_attr_dict['long']
                        else:
                            event_long = None

                        if re.match('\d+$', event_attr_dict['tizo']) is not None:
                            event_tizo = event_attr_dict['tizo']
                        else:
                            event_tizo = None


                        event.acro        = event_attr_dict['acro']
                        event.title       = event_attr_dict['titl']
                        event.start       = event_attr_dict['date']
                        event.end         = event_end
                        event.tags        = event_attr_dict['tags']
                        event.public_view = StringToBool(event_attr_dict['view'])
                        event.public_edit = StringToBool(event_attr_dict['edit'])
                        event.city        = event_attr_dict['city']
                        event.address     = event_attr_dict['addr']
                        event.postcode    = event_attr_dict['code']
                        event.country     = event_attr_dict['land']
                        event.timezone    = event_tizo
                        event.latitude    = event_lati
                        event.longitude   = event_long
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
                        return HttpResponseRedirect('/e/show/' + event_id + '/')
#                    except Exception:
#                        return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("Syntax error, nothing was saved. Click the back button in your browser and try again.")}, context_instance=RequestContext(request))
                else:
                    message = _("You submitted an empty form.")
                    return HttpResponse(message)
        else:
            event_textarea = generate_event_textarea(event)
            templates = {'title': 'edit event as text', 'event_textarea': event_textarea, 'event_id': event_id }
            return render_to_response('events/edit_astext.html', templates, context_instance=RequestContext(request))

def show(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if (not event.public_view) and (event.user.id != request.user.id):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
        else:
            templates = {'title': 'view event detail', 'event': event }
            return render_to_response('events/show.html', templates, context_instance=RequestContext(request))

def view_astext(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if (not event.public_view) and (event.user.id != request.user.id):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
        else:
            event_textarea = generate_event_textarea(event)
            templates = {'title': 'view as text', 'event_textarea': event_textarea, 'event_id': event_id }
            return render_to_response('events/view_astext.html', templates, context_instance=RequestContext(request))

def list_query(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q'].lower()
        return http.HttpResponseRedirect('/s/' + q + '/')

#        search_dict = list_search_get(q)
#
#        if search_dict['errormessage'] is not None:
#            return render_to_response('error.html', {'title': 'error 1', 'message_col1': search_dict['errormessage'], 'query': q}, context_instance=RequestContext(request))
#        elif len(search_dict['list_of_events']) == 0:
#            return render_to_response('error.html',
#                {'title': 'error 2', 'message_col1': _("Your search didn't get any result") + ".", 'query': q},
#                context_instance=RequestContext(request))
#        else:
#            return render_to_response('events/list_search.html',
#                {'title': 'search results', 'events': search_dict['list_of_events'], 'query': q},
#                context_instance=RequestContext(request))
#    else:
#        return render_to_response('error.html',
#            {'title': 'error 3', 'message_col1': _("You have submitted a search with no content") + ".", 'query': q},
#            context_instance=RequestContext(request))

def list_search(request, query):
        q = query.lower()
        user_id = request.user.id

        try:
            search_result = list_search_get(q, user_id, 0)
        except ValueError, (errmsg):
            return render_to_response('error.html',
                {'title': 'error 1', 'message_col1': errmsg, 'query': q},
                context_instance=RequestContext(request))

        if len(search_result) == 0:
            return render_to_response('error.html',
                {'title': 'error 2', 'message_col1': _("Your search didn't get any result") + ".", 'query': q},
                context_instance=RequestContext(request))
        else:
            return render_to_response('events/list_search.html',
                {'title': 'search results', 'events': search_result, 'query': q},
                context_instance=RequestContext(request))

def filter_save(request):
    if 'q' in request.POST and request.POST['q']:
        q = request.POST['q'].lower()
    else:
        q = ''

    if q == '':
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are trying to save a search without any search terms") + "."},
                context_instance=RequestContext(request))
    elif (not request.user.is_authenticated()):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to save this search because you are not logged in") + "."},
                context_instance=RequestContext(request))
    elif request.method == 'POST':
                    try:
#                        f = Filter.objects.filter(user=request.user)
                        max = Filter.objects.aggregate(Max('id'))['id__max']
#                        index = len(f) + 1
                        filter = Filter()
                        filter.user = request.user
                        filter.query = q
#                        filter.name = str(request.user) + "'s filter " + str(index)
                        filter.name = str(request.user) + "'s filter " + str(max)
                        filter.save()
                        return HttpResponseRedirect('/f/edit/' + str(filter.id) + '/') ;
                    except Exception:
                        return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("An error has ocurred, nothing was saved. Click the back button in your browser and try again.")}, context_instance=RequestContext(request))
    else:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You have submitted a GET request which is not a valid method for this function") + ".", 'query': q},
                context_instance=RequestContext(request))

def filter_edit(request, filter_id):
    try:
        filter = Filter.objects.get(pk=filter_id)
    except filter.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The saved search with the following number doesn't exist") + ": " + str(filter_id)},
                    context_instance=RequestContext(request))
    if ((not request.user.is_authenticated()) or (filter.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _('You are not allowed to edit the saved search with the following number') +
                ": " + str(filter_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            ssf = FilterForm(request.POST, instance=filter)
            if ssf.is_valid() :
                ssf.save()
                return HttpResponseRedirect('/p/filters/')
            else:
                templates = {'title': 'edit event', 'form': ssf, 'filter_id': filter_id }
                return render_to_response('events/filter_edit.html', templates, context_instance=RequestContext(request))
        else:
            ssf = FilterForm(instance=filter)
            templates = {'title': 'edit event', 'form': ssf, 'filter_id': filter_id }
            return render_to_response('events/filter_edit.html', templates, context_instance=RequestContext(request))

def filter_drop(request, filter_id):
    try:
        filter = Filter.objects.get(pk=filter_id)
    except Filter.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The saved search with the following number doesn't exist") + ": " + str(filter_id)},
                    context_instance=RequestContext(request))
    if ((not request.user.is_authenticated()) or (filter.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _('You are not allowed to delete the saved search with the following number') +
                ": " + str(Filter_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            assert False
        else:
            filter.delete()
            return HttpResponseRedirect('/p/filters/')

def filter_list_view(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
    else:
        list_of_filters = filter_list(request.user.id)
        if len(list_of_filters) == 0:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You do not have any filters configured") + "."},
                context_instance=RequestContext(request))
        else:
            return render_to_response('events/filter_list.html',
                {'title': 'list of my filters', 'filters': list_of_filters},
                context_instance=RequestContext(request))

def list_user_events(request, username):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
            events = Event.objects.filter(user=useridtmp)
            events = Event.objects.filter(public_view=True)
            if len(events) == 0:
                return render_to_response('error.html',
                    {'title': 'error', 'message_col1': _("Your search didn't get any result") + "."},
                    context_instance=RequestContext(request))
            else:
                return render_to_response('events/list_user.html',
                    {'events': events, 'username': username},
                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("User does not exist") + "."},
                context_instance=RequestContext(request))
    else:
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
            events = Event.objects.filter(user=useridtmp)
            if len(events) == 0:
                return render_to_response('error.html',
                    {'title': 'error', 'message_col1': _("Your search didn't get any result") + "."},
                    context_instance=RequestContext(request))
            else:
                return render_to_response('events/list_user.html',
                    {'events': events, 'username': username},
                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("User does not exist") + "."},
                context_instance=RequestContext(request))

def list_my_events(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
    else:
        events = Event.objects.filter(user=request.user)
        if len(events) == 0:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
        else:
            return render_to_response('events/list_my.html',
                {'title': 'list my events', 'events': events},
                context_instance=RequestContext(request))

def list_tag(request, tag):
    from re import sub
    query_tag = Tag.objects.get(name=tag)
    events = TaggedItem.objects.get_by_model(Event, query_tag)
    events = events.order_by('-start')
    return render_to_response('events/list_tag.html', {'title': 'list by tag', 'events': events, 'tag': tag}, context_instance=RequestContext(request))

