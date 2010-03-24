# -*- coding: utf-8 -*-

from time import strftime
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q, Max
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site

from tagging.models import Tag, TaggedItem

from gridcalendar.events.models import Event, EventUrl, EventSession, EventDeadline, Filter, Group, COUNTRIES
from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, FilterForm, getEventForm
from gridcalendar.events.lists import filter_list, all_events_in_user_filters, events_with_user_filters, user_filters_events_list, all_events_in_user_groups, uniq_events_list, list_up_to_max_events_ip_country_events, list_search_get

# notice that an anonymous user get a form without the 'public' field (simplified)

def event_new(request):
    if request.method == 'POST':
        if request.user.is_authenticated():
            sef = SimplifiedEventForm(request.POST)
        else:
            sef = SimplifiedEventFormAnonymous(request.POST)

        if sef.is_valid():
            cd = sef.cleaned_data
            # create a new entry and saves the data
            if request.user.is_authenticated():
                public = cd['public']
            else:
                public = True
            e = Event(user_id=request.user.id, title=cd['title'], start=cd['start'],
                        tags=cd['tags'], public=public)
            e.save()
            return HttpResponseRedirect(reverse('event_edit', kwargs={'event_id': str(e.id)}))
            # TODO: look in a thread for all users who wants to receive an email notification and send it
        else:
            return render_to_response('index.html', {'title': 'edit step 1', 'form': sef}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('root'))

def event_edit(request, event_id, raw):
    # checks if the event exists
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))

    # checks if the user is allowed to edit this event
    # public events can be edited by anyone, otherwise only by the submitter
    # and the group the event belongs to
    if (not event.public):
        # events submitted by anonymous users cannot be non-public:
        assert (event.user != None)
        if (not request.user.is_authenticated()):
            return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _('You need to be logged-in to be able' +
                    ' to edit the event with the number:') +
                    " " + str(event_id) + "). " +
                    _("Please log-in and try again") + "."},
                    context_instance=RequestContext(request))
        else:
            if (not Event.is_event_viewable_by_user(event_id, request.user.id)):
                return render_to_response('error.html',
                        {'title': 'error', 'form': getEventForm(request.user),
                        'message_col1': _('You are not allowed to edit the' +
                        ' event with the number:') +
                        " " + str(event_id) },
                        context_instance=RequestContext(request))

    if (not raw):
        EventUrlInlineFormSet       = inlineformset_factory(Event, EventUrl, extra=1)
        EventSessionInlineFormSet   = inlineformset_factory(Event, EventSession, extra=1)
        EventDeadlineInlineFormSet  = inlineformset_factory(Event, EventDeadline, extra=1)
        if request.method == 'POST':
            ef_url      = EventUrlInlineFormSet(request.POST, instance=event)
            ef_session  = EventSessionInlineFormSet(request.POST, instance=event)
            ef_deadline = EventDeadlineInlineFormSet(request.POST, instance=event)
            ef = EventForm(request.POST, instance=event)
            if ef.is_valid() & ef_url.is_valid() & ef_session.is_valid() & ef_deadline.is_valid() :
                ef.save()
                ef_url.save()
                ef_session.save()
                ef_deadline.save()
                # TODO: look in a thread for all users who wants to receive an email notification and send it
                return HttpResponseRedirect(reverse('event_show', kwargs={'event_id': event_id}))
            else:
                templates = {'title': 'edit event', 'form': ef, 'formset_url': ef_url, 'formset_session': ef_session, 'formset_deadline': ef_deadline, 'event_id': event_id }
                return render_to_response('event_edit.html', templates, context_instance=RequestContext(request))
        else:
            ef = EventForm(instance=event)
            ef_url      = EventUrlInlineFormSet(instance=event)
            ef_session  = EventSessionInlineFormSet(instance=event)
            ef_deadline = EventDeadlineInlineFormSet(instance=event)
            templates = {'title': 'edit event', 'form': ef, 'formset_url': ef_url, 'formset_session': ef_session, 'formset_deadline': ef_deadline, 'event_id': event_id }
            return render_to_response('event_edit.html', templates, context_instance=RequestContext(request))
    elif (raw):
        if request.method == 'POST':
                if 'event_astext' in request.POST:
#                    try:
                        t = request.POST['event_astext'].replace(": ", ":")
                        #event_attr_list = t.splitlines()
                        #event_attr_dict = dict(item.split(":",1) for item in event_attr_list)

                        #if re.match('\d\d\d\d\-\d\d\-\d\d$', event_attr_dict['endd']) is not None:
                        #    event_end = event_attr_dict['endd']
                        #else:
                        #    event_end = None

                        #if re.match('\d+\.\d*$', event_attr_dict['lati']) is not None:
                        #    event_lati = event_attr_dict['lati']
                        #else:
                        #    event_lati = None

                        #if re.match('\d+\.\d*$', event_attr_dict['long']) is not None:
                        #    event_long = event_attr_dict['long']
                        #else:
                        #    event_long = None

                        #if re.match('\d+$', event_attr_dict['tizo']) is not None:
                        #    event_tizo = event_attr_dict['tizo']
                        #else:
                        #    event_tizo = None

                        #event.acronym     = event_attr_dict['acro']
                        #event.title       = event_attr_dict['titl']
                        #event.start       = event_attr_dict['date']
                        #event.end         = event_end
                        #event.tags        = event_attr_dict['tags']
                        #event.public      = StringToBool(event_attr_dict['publ'])
                        #event.city        = event_attr_dict['city']
                        #event.address     = event_attr_dict['addr']
                        #event.postcode    = event_attr_dict['code']
                        #event.country     = event_attr_dict['land']
                        #event.timezone    = event_tizo
                        #event.latitude    = event_lati
                        #event.longitude   = event_long
                        #event.description = event_attr_dict['desc']
                        #EventUrl.objects.filter(event=event_id).delete()
                        #EventSession.objects.filter(event=event_id).delete()
                        #EventDeadline.objects.filter(event=event_id).delete()
                        #for textline in event_attr_list:
                        #    if textline[0:4] == 'url:':
                        #        line_attr_list = textline[4:].split("|",1)
                        #        eu = EventUrl(event=event, url_name=line_attr_list[0], url=line_attr_list[1])
                        #        eu.save(force_insert=True)
                        #    if textline[0:5] == 'time:':
                        #        line_attr_list = textline[5:].split("|",3)
                        #        et = EventSession(event=event, session_name=line_attr_list[0], session_date=line_attr_list[1], session_starttime=line_attr_list[2], session_endtime=line_attr_list[3])
                        #        et.save(force_insert=True)
                        #    if textline[0:3] == 'dl:':
                        #        line_attr_list = textline[3:].split("|",1)
                        #        ed = EventDeadline(event=event, deadline_name=line_attr_list[0], deadline=line_attr_list[1])
                        #        ed.save(force_insert=True)
                        event.parse_text(t, event_id)
                        return HttpResponseRedirect(reverse('event_show', kwargs={'event_id': event_id}))
#                    except Exception:
#                        return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("Syntax error, nothing was saved. Click the back button in your browser and try again.")}, context_instance=RequestContext(request))
                else:
                    return render_to_response('error.html', {'title': 'error', 'form': getEventForm(request.user), 'message_col1': _("You submitted an empty form, nothing was saved. Click the back button in your browser and try again.")}, context_instance=RequestContext(request))
        else:
            event_textarea = event.as_text()
            templates = { 'title': 'edit event as text', 'event_textarea': event_textarea, 'event_id': event_id }
            return render_to_response('event_edit_raw.html', templates, context_instance=RequestContext(request))

def event_show(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if not Event.is_event_viewable_by_user(event_id, request.user.id):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to view the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        templates = {'title': 'view event detail', 'event': event }
        return render_to_response('event_show.html', templates, context_instance=RequestContext(request))

def event_show_raw(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': 'error', 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if not Event.is_event_viewable_by_user(event_id, request.user.id):
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to view the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        event_textarea = event.as_text()
        templates = {'title': 'view as text', 'event_textarea': event_textarea, 'event_id': event_id }
        return render_to_response('event_show_raw.html', templates, context_instance=RequestContext(request))

def query(request):
    if 'q' in request.GET and request.GET['q']:
        q = request.GET['q'].lower()
        return HttpResponseRedirect(reverse('list_events_search', kwargs={'query': q}))

def list_events_search(request, query):
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
            return render_to_response('list_events_search.html',
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
                        return HttpResponseRedirect(reverse('filter_edit', kwargs={'filter_id': filter.id}))
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
                return HttpResponseRedirect(reverse('list_filters_my'))
            else:
                templates = {'title': 'edit event', 'form': ssf, 'filter_id': filter_id }
                return render_to_response('filter_edit.html', templates, context_instance=RequestContext(request))
        else:
            ssf = FilterForm(instance=filter)
            templates = {'title': 'edit event', 'form': ssf, 'filter_id': filter_id }
            return render_to_response('filter_edit.html', templates, context_instance=RequestContext(request))

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
            return HttpResponseRedirect(reverse('list_filters_my'))

def list_filters_my(request):
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
            return render_to_response('filter_list_my.html',
                {'title': 'list of my filters', 'filters': list_of_filters},
                context_instance=RequestContext(request))

def list_events_of_user(request, username):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
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

def list_events_my(request):
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
            return render_to_response('list_events_my.html',
                {'title': 'list my events', 'events': events},
                context_instance=RequestContext(request))

def list_events_tag(request, tag):
    """ returns a view with events having a tag
    """
    from re import sub
    query_tag = Tag.objects.get(name=tag)
    events = TaggedItem.objects.get_by_model(Event, query_tag)
    events = events.order_by('-start')
    return render_to_response('list_events_tag.html', {'title': 'list by tag', 'events': events, 'tag': tag}, context_instance=RequestContext(request))

def root(request):
    user_id = request.user.id

    if request.user.is_authenticated():
        event_form = SimplifiedEventForm()
    else:
        event_form = SimplifiedEventFormAnonymous()

    if request.user.is_authenticated():
        efl = events_with_user_filters(user_id)
        uel = uniq_events_list(efl)
        events = user_filters_events_list(user_id, efl)
    else:
        efl = list()
        uel = list()
        events = list()

    ip_country_event_list = list()
    ip_continent_event_list = list()
    landless_event_list = list()

    if len(events) < settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len(events)
        ip_country_event_list = list_up_to_max_events_ip_country_events(request.META.get('REMOTE_ADDR'), user_id, uel, add_thismany, 'country')
    else:
        ip_country_event_list = list()

    if len(events) + len(ip_country_event_list) < settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len(events) - len(ip_country_event_list)
        ip_continent_event_list = list_up_to_max_events_ip_country_events(request.META.get('REMOTE_ADDR'), user_id, uel, add_thismany, 'continent')
    else:
        ip_continent_event_list = list()

    if len(events) + len(ip_country_event_list) + len(ip_continent_event_list) < settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len(events) - len(ip_country_event_list) - len(ip_continent_event_list)
        landless_event_list = list_up_to_max_events_ip_country_events(request.META.get('REMOTE_ADDR'), user_id, uel, add_thismany, 'landless')

    return render_to_response('root.html', {
            'title': 'Welcome to GridCalendar',
            'form': event_form,
            'events': events,
            'ip_country_event_list': ip_country_event_list,
            'ip_continent_event_list': ip_continent_event_list,
            'landless_event_list': landless_event_list,
            'group_events': all_events_in_user_groups(request.user.id, 5),
        }, context_instance=RequestContext(request))

# http://docs.djangoproject.com/en/1.0/topics/auth/#the-login-required-decorator
@login_required
def settings_page(request):
    # user is logged in
    fl = filter_list(request.user.id)
    u = User(request.user)
    groups = Group.objects.filter(membership__user=u)
    return render_to_response('settings.html', {'title': 'settings', 'filter_list': fl, 'groups': groups}, context_instance=RequestContext(request))
