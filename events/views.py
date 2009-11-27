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
    if (not event.public_edit) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
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

def edit_astext(request, event_id):
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
                        event.public_view = StringToBool(event_attr_dict['public_view'])
                        event.public_edit = StringToBool(event_attr_dict['public_edit'])
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
                        return HttpResponseRedirect('/')
#                    except Exception:
#                        return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("Syntax error, nothing was saved. Click the back button in your browser and try again.")}, context_instance=RequestContext(request))
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

##### views below present lists of events #####

def list_search_get(q):

# initialize a lookup dictionary, events instance and an od list:
        country_to_id_dict = dict((landtable[1][:].lower(), landtable[0]) for landtable in COUNTRIES)
        events = Event.objects.none()
        time_limiters = Q()
        sorting_dictionary = {}
        errormessage = ''

        for qpart in q.split(" "):
            if re.match("(dl:)?(\d\d\d\d\-\d\d\-\d\d|@)[+\-]?(\d)*(:(\d\d\d\d\-\d\d\-\d\d|@)[+\-]?(\d)*)?$", qpart):
###############################################################################
                tpart = qpart
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
                    errormessage = _("You have submitted an invalid search - one of your time ranges contain more then 2 elements")
                    search_dict = {'errormessage': errormessage, 'list_of_events': ''}
                    return search_dict

                if re.match('@', tpart_from) is not None:
                    divi = 1
                else:
                    divi = 10
                tpart_from_date = tpart_from[0:divi]
                tpart_from_diff = tpart_from[divi:]
                if re.search('^\d+-', tpart_from_diff) is not None:
                    errormessage = _("You have submitted an invalid search - you are trying to add or subtract more than one value from a 'from' date")
                    search_dict = {'errormessage': errormessage, 'list_of_events': ''}
                    return search_dict
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
                        errormessage = _("You have submitted an invalid search - you are trying to add or subtract more than one value from a 'to' date")
                        search_dict = {'errormessage': errormessage, 'list_of_events': ''}
                        return search_dict
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
                        errormessage = _("You have submitted an invalid search - one of your dates is in invalid format or is not a date at all")
                        search_dict = {'errormessage': errormessage, 'list_of_events': ''}
                        return search_dict

                tpart_from_final = tpart_from_date_valid + datetime.timedelta(days=tpart_from_diff)
                tpart_to_final   = tpart_to_date_valid   + datetime.timedelta(days=tpart_to_diff)

                if tpart_scope == 'start': time_limiters |= Q(start__range=(tpart_from_final,tpart_to_final))
                if tpart_scope == 'dl':    time_limiters |= Q(event_of_deadline__deadline__range=(tpart_from_final,tpart_to_final))
###############################################################################
            elif re.match("[\-\w]*$", qpart):
###############################################################################
                events_titl = Event.objects.none()
                if qpart.find(":") == -1 or re.match('titl:', qpart) is not None:
                    qpart_titl = re.sub('titl:', '', qpart, 1)
                    events_titl = Event.objects.filter(title__icontains=qpart_titl)
                    for iii in events_titl:
                        index = iii.id
                        sorting_dictionary[index]=sorting_dictionary.get(index,0)+1

                events_desc = Event.objects.none()
                if qpart.find(":") == -1 or re.match('desc:', qpart) is not None:
                    qpart_desc = re.sub('desc:', '', qpart, 1)
                    events_desc = Event.objects.filter(description__icontains=qpart_desc)
                    for iii in events_desc:
                        index = iii.id
                        sorting_dictionary[index]=sorting_dictionary.get(index,0)+1

                events_acro = Event.objects.none()
                if qpart.find(":") == -1 or re.match('acro:', qpart) is not None:
                    qpart_acro = re.sub('acro:', '', qpart, 1)
                    events_acro = Event.objects.filter(acro__iexact=qpart_acro)
                    for iii in events_acro:
                        index = iii.id
                        sorting_dictionary[index]=sorting_dictionary.get(index,0)+1

                events_land = Event.objects.none()
                if qpart.find(":") == -1 or re.match('land:', qpart) is not None:
                    qpart_land = re.sub('land:', '', qpart, 1)
                    try:
                        events_land = Event.objects.filter(country__iexact=country_to_id_dict[qpart_land])
                    except KeyError:
                        events_land = Event.objects.none()
                    for iii in events_land:
                        index = iii.id
                        sorting_dictionary[index]=sorting_dictionary.get(index,0)+1

                events_city = Event.objects.none()
                if qpart.find(":") == -1 or re.match('city:', qpart) is not None:
                    qpart_city = re.sub('city:', '', qpart, 1)
                    events_city = Event.objects.filter(city__iexact=qpart_city)
                    for iii in events_city:
                        index = iii.id
                        sorting_dictionary[index]=sorting_dictionary.get(index,0)+1

                events_tagg = Event.objects.none()
                if qpart.find(":") == -1 or re.match('tags:', qpart) is not None:
                    qpart_tagg = re.sub('tags:', '', qpart, 1)
                    events_tagg = TaggedItem.objects.get_union_by_model(Event, qpart_tagg)
                    for iii in events_tagg:
                        index = iii.id
                        sorting_dictionary[index]=sorting_dictionary.get(index,0)+1

                events = events | events_titl | events_desc | events_acro | events_land | events_city | events_tagg
###############################################################################
            else:
                errormessage = _("You have submitted an invalid search - check your query format and try again")
                search_dict = {'errormessage': errormessage, 'list_of_events': ''}
                return search_dict

# apply the filter to the search results
        events = events & Event.objects.filter(time_limiters)
        list_of_events = list(events)

# make the list of events unique
        list_of_events = list(set(list_of_events))
        list_of_events.sort(key=lambda x: sorting_dictionary[x.id], reverse=True)

        search_dict = {'errormessage': '', 'list_of_events': list_of_events}
        return search_dict

def list_search(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q'].lower()

        search_dict = list_search_get(q)

        if not search_dict['errormessage'] == '':
            return render_to_response('error.html', {'title': 'error', 'message_col1': search_dict['errormessage'] + ".", 'query': q}, context_instance=RequestContext(request))
        elif len(search_dict['list_of_events']) == 0:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("Your search didn't get any result") + ".", 'query': q},
                context_instance=RequestContext(request))
        else:
            return render_to_response('events/list_search.html',
                {'title': 'search results', 'events': search_dict['list_of_events'], 'query': q},
                context_instance=RequestContext(request))
    else:
        return render_to_response('error.html',
            {'title': 'error', 'message_col1': _("You have submitted a search with no content") + ".", 'query': q},
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
                        f = Filter.objects.all()
                        f = Filter.objects.filter(user=request.user)
                        index = len(f) + 1
                        filter = Filter()
                        filter.user = request.user
                        filter.query = q
                        filter.name = str(request.user) + "'s filter " + str(index)
                        filter.save()
                        return HttpResponseRedirect('/events/filter/edit/' + str(filter.id) + '/') ;
                    except Exception:
                        return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("An error has ocurred, nothing was saved. Click the back button in your browser and try again.")},
                            context_instance=RequestContext(request))
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
                return HttpResponseRedirect('/events/filter/list/')
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
    except filter.DoesNotExist:
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
            f = Filter.objects.all()
            f = Filter.objects.filter(user=request.user)
            return render_to_response('events/filter_list.html',
                {'title': 'list of my filters', 'filters': f},
                context_instance=RequestContext(request))

def filter_list(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
    else:
        f = Filter.objects.all()
        f = Filter.objects.filter(user=request.user)
        if len(f) == 0:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You do not have any filters configured") + "."},
                context_instance=RequestContext(request))
        else:
#            url = '/events/list/search/'
#            values = {'q' : q,}
#            fullurl = urllib.urlencode(values)

            flist = list(f)

            list_of_filters = list()

            for fff in flist:
                search_results = list_search_get(fff.query)['list_of_events']
                search_error = list_search_get(fff.query)['errormessage']
                fff_dict = dict()
                fff_dict['id'] = fff.id
                fff_dict['name'] = fff.name
                fff_dict['query'] = fff.query
                fff_dict['results'] = len(search_results)
                if search_error == '':
                    fff_len = len(search_results)
                    if fff_len <= 5:
                        show = fff_len
                    else:
                        show = 5
                    fff_dict['e'] = search_results[0:show]
                else:
                    fff_dict['errormessage'] = search_error

                list_of_filters.append(fff_dict)
                del fff_dict
                del search_error

            return render_to_response('events/filter_list.html',
                {'title': 'list of my filters', 'filters': list_of_filters},
                context_instance=RequestContext(request))

def list_user_events(request, username):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
            events = Event.objects.all()
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

