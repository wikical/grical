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

def all_events_in_user_filters(user_id):
    """
    returns a list of dictionaries, which contain the filter name and a list of events
    """
    finlist = list()
    if (user_id is None):
        return None
    else:
        u = User.objects.get(id=user_id)
        filters = Filter.objects.filter(user=u)
        if len(filters) == 0:
            return None
        else:
            for f in filters:
                dle = {}
                dle['filter_name'] = f.name
                el = list()
                s = list_search_get(f.query)
                events = s['list_of_events']
                for e in events:
                    el.append(e)
                dle['el'] = el
                finlist.append(dle)
            return finlist

def events_with_user_filters(user_id):
    """
    returns a list of dictionaries, which contain 'event_id' and 'filter_id'
    """
    if (user_id is None):
        return None
    else:
        u = User.objects.get(id=user_id)
        filter_list = Filter.objects.filter(user=u)
        if len(filter_list) == 0:
            return None
        else:
            l = len(filter_list)
            finlist = list()
            for filter in filter_list:
                event_query = list_search_get(filter.query)
                if event_query['errormessage'] is not None:
                    return None
                else:
                    event_list = event_query['list_of_events']
                    for event in event_list:
                        event_dict = {}
                        event_dict['filter_id'] = filter.id
                        event_dict['event_id'] = event.id
                        finlist.append(event_dict)
            return finlist

def uniq_events_list(events_filters_list):
    """
    returns
    """
    l = list()
    for event in events_filters_list:
        id = event['event_id']
        if id not in l:
            l.append(id)
#    assert False
    return l


def filters_matching_event(events_filters_list, event_id):
    """
    returns
    """
    l = list()
    for event in events_filters_list:
        id = event['event_id']
        if event_id == id:
            f_dict = dict()
            f = Filter.objects.get(id=event['filter_id'])
            f_dict['id'] = f.id
            f_dict['user_id'] = f.user.id
            f_dict['name'] = f.name
            f_dict['query'] = f.query
            f_dict['hash'] = hashlib.sha256("%s!%s!%s" % (SECRET_KEY, f.id, f.user.id)).hexdigest()
            l.append(f_dict)
    return l

def user_filters_events_list(user_id):
    """
    returns
    """
    events_filters_list = events_with_user_filters(user_id)
    event_list = list()
    for event_id in uniq_events_list(events_filters_list):
        event_dict = {}
        event = Event.objects.get(id=event_id)
        event_dict['id'] = event.id
        event_dict['start'] = event.start
        event_dict['end'] = event.end
        event_dict['city'] = event.city
        event_dict['country'] = event.country
        event_dict['title'] = event.title
        event_dict['tags'] = event.tags
        event_dict['filters'] = filters_matching_event(events_filters_list, event.id)
        event_list.append(event_dict)
    return event_list[0:settings.MAX_EVENTS_ON_ROOT_PAGE]

def ip_country_events(ip_addr):
    g = GeoIP()
    country = g.country(ip_addr)['country_code']
    events = Event.objects.filter(Q(start__gte=datetime.now()) & Q(country=country))
    return events

def ip_continent_events(ip_addr):
    g = GeoIP()
    country = g.country(ip_addr)['country_code']
    continent = GeoIPup.country_continents.get(country, "N/A")
    other_countries_on_continent = list()
    for a in GeoIPup.country_continents.items():
        if a[1] == continent and not a[0] == country:
            other_countries_on_continent.append(a[0])

    events = Event.objects.filter(Q(start__gte=datetime.now()) & Q(country__in=other_countries_on_continent))
    return events

def landless_events():
    events = Event.objects.filter(Q(start__gte=datetime.now()) & Q(country=None))
    return events

def list_search_get(q):
        """
        This function takes a query entered into the search as an argument and returns a dictionary containing the "errormessage" and "list_of_events"
        """
# initialize a lookup dictionary, events instance and an od list:
        country_to_id_dict = dict((landtable[1][:].lower(), landtable[0]) for landtable in COUNTRIES)
        events = Event.objects.none()
        time_limiters = Q()
        sorting_dictionary = {}
        errormessage = None

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
                    tpart_from_date_valid  = datetime.strptime(tpart_from_date, "%Y-%m-%d")
                    tpart_to_date_valid    = datetime.strptime(tpart_to_date,   "%Y-%m-%d")
                except ValueError:
                        errormessage = _("You have submitted an invalid search - one of your dates is in invalid format or is not a date at all")
                        search_dict = {'errormessage': errormessage, 'list_of_events': ''}
                        return search_dict

                tpart_from_final = tpart_from_date_valid + timedelta(days=tpart_from_diff)
                tpart_to_final   = tpart_to_date_valid   + timedelta(days=tpart_to_diff)

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
                search_dict = {'errormessage': errormessage, 'list_of_events': None}
                return search_dict

# apply the filter to the search results
        events = events & Event.objects.filter(time_limiters)
        list_of_events = list(events)

# make the list of events unique
        list_of_events = list(set(list_of_events))
        list_of_events.sort(key=lambda x: sorting_dictionary[x.id], reverse=True)

        search_dict = {'errormessage': None, 'list_of_events': list_of_events}
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

