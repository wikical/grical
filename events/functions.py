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
from gridcalendar.feeds import ICalForEvent, ICalForGroup

def ical_for_event(request, event_id):
    return ICalForEvent(event_id)

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

def filter_list(user_id):
    u = User.objects.get(id=user_id)
    f = Filter.objects.filter(user=u)
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
    return list_of_filters


