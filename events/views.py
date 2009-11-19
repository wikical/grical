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

from gridcalendar.events.models import Event, EventUrl, EventTimechunk, EventDeadline, SavedSearch, COUNTRIES
from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, EventFormAnonymous, SavedSearchForm

# notice that an anonymous user get a form without the 'public' field (simplified)

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
            return render_to_response('index.html', {'title': 'edit step 1', 'form': sef}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(request.get_host())

def getEventForm(user):
    """returns a simplied event form with or without the public field"""
    if user.is_authenticated():
        return SimplifiedEventForm()
    return SimplifiedEventFormAnonymous()

def edit(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter
    if (event.user is not None) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
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

def edit_astext(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter
    if (event.user is not None) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to edit the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
                if 'event_astext' in request.POST:
                    try:
                        t = request.POST['event_astext'].replace(": ", ":")
                        event_attr_list = t.splitlines()
                        event_attr_dict = dict(item.split(":",1) for item in event_attr_list)
                        event.acro        = event_attr_dict['acro']
                        event.title       = event_attr_dict['titl']
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
                        return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("Syntax error, nothing was saved. Click the back button in your browser and try again.")},
                    context_instance=RequestContext(request))
                else:
                    message = _("You submitted an empty form.")
                    return HttpResponse(message)
        else:
            event_textarea = generate_event_textarea(event)
            templates = {'title': 'edit event as text', 'event_textarea': event_textarea, 'event_id': event_id }
            return render_to_response('events/edit_astext.html', templates, context_instance=RequestContext(request))

def view_astext(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if (not event.public) and (event.user.id != request.user.id):
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

##### views below present lists of events #####

def list_search(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q'].lower()

        events = Event.objects.none()
        od = {}

# ... initialize a lookup dictionary
        country_to_id_dict = dict((t[1][:].lower(), t[0]) for t in COUNTRIES)

        for qpart in q.split(" "):

            events_titl = Event.objects.none()
            if qpart.find(":") == -1 or re.match('titl:', qpart) is not None:
                qpart_titl = re.sub('titl:', '', qpart, 1)
                events_titl = Event.objects.filter(title__icontains=qpart_titl)
                for iii in events_titl:
                    index = iii.id
                    od[index]=od.get(index,0)+1

            events_desc = Event.objects.none()
            if qpart.find(":") == -1 or re.match('desc:', qpart) is not None:
                qpart_desc = re.sub('desc:', '', qpart, 1)
                events_desc = Event.objects.filter(description__icontains=qpart_desc)
                for iii in events_desc:
                    index = iii.id
                    od[index]=od.get(index,0)+1

            events_acro = Event.objects.none()
            if qpart.find(":") == -1 or re.match('acro:', qpart) is not None:
                qpart_acro = re.sub('acro:', '', qpart, 1)
                events_acro = Event.objects.filter(acro__iexact=qpart_acro)
                for iii in events_acro:
                    index = iii.id
                    od[index]=od.get(index,0)+1

            events_land = Event.objects.none()
            if qpart.find(":") == -1 or re.match('land:', qpart) is not None:
                qpart_land = re.sub('land:', '', qpart, 1)
                try:
                    events_land = Event.objects.filter(country__iexact=country_to_id_dict[qpart_land])
                except KeyError:
                    events_land = Event.objects.none()
                for iii in events_land:
                    index = iii.id
                    od[index]=od.get(index,0)+1

            events_city = Event.objects.none()
            if qpart.find(":") == -1 or re.match('city:', qpart) is not None:
                qpart_city = re.sub('city:', '', qpart, 1)
                events_city = Event.objects.filter(city__iexact=qpart_city)
                for iii in events_city:
                    index = iii.id
                    od[index]=od.get(index,0)+1

            events_tagg = Event.objects.none()
            if qpart.find(":") == -1 or re.match('tags:', qpart) is not None:
                qpart_tagg = re.sub('tags:', '', qpart, 1)
                events_tagg = TaggedItem.objects.get_union_by_model(Event, qpart_tagg)
                for iii in events_tagg:
                    index = iii.id
                    od[index]=od.get(index,0)+1

            del iii
            events = events | events_titl | events_desc | events_acro | events_land | events_city | events_tagg

# if the "t" field is filled, create a filtering QuerySet for filtering the search results by date
        if 't' in request.GET and request.GET['t']:
            t = request.GET['t'].lower()
            ttt = Q()
            for tpart in t.split(" "):

                tpart_scope = 'start'
                if re.match('dl:', tpart) is not None:
                    tpart = re.sub('dl:', '', tpart, 1)
                    tpart_scope = 'dl'

                tpart_list = tpart.split(":")
                if len(tpart_list)==1:
                    tpart_from = tpart_list[0]
                    tpart_to = tpart_list[0]
                if len(tpart_list)==2:
                    tpart_from = tpart_list[0]
                    tpart_to = tpart_list[1]
                if len(tpart_list)>2:
                    return render_to_response('error.html',
                        {'title': 'error', 'message_col1': _("You have submitted an invalid search - one of your time ranges contain more then 2 elements") + ".", 'query': q, 'timequery': t},
                        context_instance=RequestContext(request))

                if re.match('@', tpart_from) is not None:
                    divi = 1
                else:
                    divi = 10
                tpart_from_date = tpart_from[0:divi]
                tpart_from_diff = tpart_from[divi:]
                if re.search('^\d+-', tpart_from_diff) is not None:
                    return render_to_response('error.html',
                        {'title': 'error', 'message_col1': _("You have submitted an invalid search - you are trying to add or subtract more than one value from a 'from' date") + ".", 'query': q, 'timequery': t},
                        context_instance=RequestContext(request))
                try:
                    tpart_from_diff = int(tpart_from_diff)
                except ValueError:
                    tpart_from_diff = 0

                if re.match('@', tpart_to) is not None:
                    divi = 1
                else:
                    divi = 10
                tpart_to_date = tpart_to[0:divi]
                tpart_to_diff = tpart_to[divi:]
                if re.search('^\d+-', tpart_to_diff) is not None:
                    return render_to_response('error.html',
                        {'title': 'error', 'message_col1': _("You have submitted an invalid search - you are trying to add or subtract more than one value from a 'to' date") + ".", 'query': q, 'timequery': t},
                        context_instance=RequestContext(request))
                try:
                    tpart_to_diff = int(tpart_to_diff)
                except ValueError:
                    tpart_to_diff = 0

                if tpart_from_date == '@':  tpart_from_date = datetime.date.today().strftime("%Y-%m-%d")
                if tpart_to_date   == '@':  tpart_to_date   = datetime.date.today().strftime("%Y-%m-%d")
                if tpart_from_date == '':   tpart_from_date = '0001-01-01'
                if tpart_to_date   == '':   tpart_to_date   = '9999-12-31'

                try:
                    tpart_from_date_valid  = datetime.datetime.strptime(tpart_from_date, "%Y-%m-%d")
                    tpart_to_date_valid    = datetime.datetime.strptime(tpart_to_date,   "%Y-%m-%d")
                except ValueError:
                    return render_to_response('error.html',
                        {'title': 'error', 'message_col1': _("You have submitted an invalid search - one of your dates is in invalid format or is not a date at all") + ".", 'query': q, 'timequery': t},
                        context_instance=RequestContext(request))

                tpart_from_final = tpart_from_date_valid + datetime.timedelta(days=tpart_from_diff)
                tpart_to_final   = tpart_to_date_valid   + datetime.timedelta(days=tpart_to_diff)

                if tpart_scope == 'start': ttt |= Q(start__range=(tpart_from_final,tpart_to_final))
                if tpart_scope == 'dl':    ttt |= Q(event_of_deadline__deadline__range=(tpart_from_final,tpart_to_final))

# apply the filter to the search results
            events = events & Event.objects.filter( ttt )
        else:
            t = ''

        list_of_events = list(events)

# make the list of events unique
        list_of_events = list(set(list_of_events))

        list_of_events.sort(key=lambda x: od[x.id], reverse=True)

        if len(events) == 0:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("Your search didn't get any result") + ".", 'query': q, 'timequery': t},
                context_instance=RequestContext(request))
        else:
            return render_to_response('events/list_search.html',
                {'title': 'search results', 'events': list_of_events, 'query': q, 'timequery': t},
                context_instance=RequestContext(request))
    else:
        return render_to_response('error.html',
            {'title': 'error', 'message_col1': _("You have submitted a search with no content") + ".", 'query': q, 'timequery': t},
            context_instance=RequestContext(request))

def filter_save(request):
    if 'q' in request.POST and request.POST['q']:
        q = request.POST['q'].lower()
    else:
        q = ''

    if 't' in request.POST and request.POST['t']:
        t = request.POST['t'].lower()
    else:
        t = ''

    if q == '' and t == '':
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
                        savedsearch = SavedSearch()
                        savedsearch.user = request.user
                        savedsearch.query_text = q
                        savedsearch.query_time = t
                        savedsearch.save()
                        return HttpResponseRedirect('/events/list/filter/edit/' + str(savedsearch.id) + '/') ;
                    except Exception:
                        assert False
                        return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("An error has ocurred, nothing was saved. Click the back button in your browser and try again.")},
                            context_instance=RequestContext(request))
    else:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You have submitted a GET request which is not a valid method for this function") + ".", 'query': q, 'timequery': t},
                context_instance=RequestContext(request))


def filter_edit(request, savedsearch_id):
    try:
        savedsearch = SavedSearch.objects.get(pk=savedsearch_id)
    except SavedSearch.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The saved search with the following number doesn't exist") + ": " + str(savedsearch_id)},
                    context_instance=RequestContext(request))
    if ((not request.user.is_authenticated()) or (savedsearch.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _('You are not allowed to edit the saved search with the following number') +
                ": " + str(savedsearch_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            ssf = SavedSearchForm(request.POST, instance=savedsearch)
            if ssf.is_valid() :
                ssf.save()
                return HttpResponseRedirect('/events/list/filter/list/')
            else:
                templates = {'title': 'edit event', 'form': ssf, 'savedsearch_id': savedsearch_id }
                return render_to_response('events/filter_edit.html', templates, context_instance=RequestContext(request))
        else:
            ssf = SavedSearchForm(instance=savedsearch)
            templates = {'title': 'edit event', 'form': ssf, 'savedsearch_id': savedsearch_id }
            return render_to_response('events/filter_edit.html', templates, context_instance=RequestContext(request))

def filter_drop(request, savedsearch_id):
    try:
        savedsearch = SavedSearch.objects.get(pk=savedsearch_id)
    except SavedSearch.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The saved search with the following number doesn't exist") + ": " + str(savedsearch_id)},
                    context_instance=RequestContext(request))
    if ((not request.user.is_authenticated()) or (savedsearch.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _('You are not allowed to delete the saved search with the following number') +
                ": " + str(savedsearch_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        if request.method == 'POST':
            assert False
        else:
            savedsearch.delete()
            f = SavedSearch.objects.all()
            f = SavedSearch.objects.filter(user=request.user)
            return render_to_response('events/filter_list.html',
                {'title': 'list of my filters', 'filters': f},
                context_instance=RequestContext(request))



def filter_list(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
    else:
        f = SavedSearch.objects.all()
        f = SavedSearch.objects.filter(user=request.user)
        if len(f) == 0:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You do not have any filters configured") + "."},
                context_instance=RequestContext(request))
        else:
#            url = '/events/list/search/'
#            values = {'q' : q,
#                't' : t,
#                }
#            fullurl = urllib.urlencode(values)

            return render_to_response('events/filter_list.html',
                {'title': 'list of my filters', 'filters': f},
                context_instance=RequestContext(request))





def list_user_events(request, username):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
            events = Event.objects.all()
            events = Event.objects.filter(user=useridtmp)
            events = Event.objects.filter(public=True)
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
            events = Event.objects.all()
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
        events = Event.objects.all()
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

