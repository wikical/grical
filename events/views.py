#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009, 2010 Iván F. Villanueva B. <ivan ät gridmind.org>
#
# This file is part of GridCalendar.
# 
# GridCalendar is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################


import hashlib
from time import strftime
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q, Max
from django.forms import ValidationError
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site

from settings import SECRET_KEY

from tagging.models import Tag, TaggedItem

from gridcalendar.events.models import Event, EventUrl, EventSession, EventDeadline, Filter, Group, COUNTRIES
from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, FilterForm, getEventForm
from gridcalendar.events.lists import filter_list, all_events_in_user_filters, events_with_user_filters, user_filters_events_list, all_events_in_user_groups, uniq_events_list, list_up_to_max_events_ip_country_events, list_search_get

# notice that an anonymous user get a form without the 'public' field (simplified)

def help(request):
    """Just returns the help page including documentation in the file USAGE.TXT"""
    usage_text = open(settings.PROJECT_ROOT + '/USAGE.TXT','r').read()
    about_text = open(settings.PROJECT_ROOT + '/ABOUT.TXT','r').read()
    return render_to_response('help.html', {
            'title': 'GridCalendar.net - help',
            'usage_text': usage_text,
            'about_text': about_text,
            }, context_instance=RequestContext(request))

def legal_notice(request):
    """Just returns the legal notice page."""
    return render_to_response('legal_notice.html', {
            'title': 'GridCalendar.net - legal notice',
            }, context_instance=RequestContext(request))

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
            return render_to_response('index.html', {'title': _("edit step 1"), 'form': sef}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('root'))

def event_edit(request, event_id):
    # checks if the event exists
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': _("error"), 'form': getEventForm(request.user),
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
                    {'title': _("error"), 'form': getEventForm(request.user),
                    'message_col1': _('You need to be logged-in to be able' +
                    ' to edit the event with the number:') +
                    " " + str(event_id) + "). " +
                    _("Please log-in and try again") + "."},
                    context_instance=RequestContext(request))
        else:
            if (not Event.is_event_viewable_by_user(event_id, request.user.id)):
                return render_to_response('error.html',
                        {'title': _("error"), 'form': getEventForm(request.user),
                        'message_col1': _('You are not allowed to edit the' +
                        ' event with the number:') +
                        " " + str(event_id) },
                        context_instance=RequestContext(request))

    EventUrlInlineFormSet       = inlineformset_factory(Event, EventUrl, extra=4)
    EventDeadlineInlineFormSet  = inlineformset_factory(Event, EventDeadline, extra=4)
    EventSessionInlineFormSet   = inlineformset_factory(Event, EventSession, extra=4)
    if request.method == 'POST':
        formset_url      = EventUrlInlineFormSet(request.POST, instance=event)
        formset_deadline = EventDeadlineInlineFormSet(request.POST, instance=event)
        formset_session  = EventSessionInlineFormSet(request.POST, instance=event)
        event_form = EventForm(request.POST, instance=event)
        if event_form.is_valid() & formset_url.is_valid() & formset_session.is_valid() & formset_deadline.is_valid() :
            # TODO: use the session middleware to commit as an atom
            event_form.save()
            formset_url.save()
            formset_session.save()
            formset_deadline.save()
            # TODO: look in a thread for all users who wants to receive an email notification and send it
            return HttpResponseRedirect(reverse('event_show', kwargs={'event_id': event_id}))
        else:
            templates = {'title': 'edit event', 'form': event_form, 'formset_url': formset_url, 'formset_session': formset_session, 'formset_deadline': formset_deadline, 'event_id': event_id }
            return render_to_response('event_edit.html', templates, context_instance=RequestContext(request))
    else:
        event_form = EventForm(instance=event)
        formset_url      = EventUrlInlineFormSet(instance=event)
        formset_deadline = EventDeadlineInlineFormSet(instance=event)
        formset_session  = EventSessionInlineFormSet(instance=event)
        templates = {'title': 'edit event', 'form': event_form, 'formset_url': formset_url, 'formset_session': formset_session, 'formset_deadline': formset_deadline, 'event_id': event_id }
        return render_to_response('event_edit.html', templates, context_instance=RequestContext(request))

def event_new_raw(request):
    if request.method == 'POST':
            if 'event_astext' in request.POST:
                event_textarea = request.POST['event_astext']
                try:
                    Event.parse_text(event_textarea, None, request.user.id)
                    return HttpResponseRedirect(reverse('root'))
                except ValidationError, error:
                    return render_to_response('error.html',
                        {'title': _("validation error"), 'message_col1': error, 'form': getEventForm(request.user)},
                        context_instance=RequestContext(request))
            else:
                return render_to_response('error.html', {'title': _("error"),
                    'form': getEventForm(request.user),
                    'message_col1': _("You submitted an empty form, nothing was saved. Click the back button in your browser and try again.")},
                    context_instance=RequestContext(request))
    else:
        templates = { 'title': _("edit event as text") }
        return render_to_response('event_new_raw.html', templates, context_instance=RequestContext(request))

def event_edit_raw(request, event_id):
    # checks if the event exists
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': _("error"), 'form': getEventForm(request.user),
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
                    {'title': _("error"), 'form': getEventForm(request.user),
                    'message_col1': _('You need to be logged-in to be able' +
                    ' to edit the event with the number:') +
                    " " + str(event_id) + "). " +
                    _("Please log-in and try again") + "."},
                    context_instance=RequestContext(request))
        else:
            if (not Event.is_event_viewable_by_user(event_id, request.user.id)):
                return render_to_response('error.html',
                        {'title': _("error"), 'form': getEventForm(request.user),
                        'message_col1': _('You are not allowed to edit the' +
                        ' event with the number:') +
                        " " + str(event_id) },
                        context_instance=RequestContext(request))
    if request.method == 'POST':
            if 'event_astext' in request.POST:
                event_textarea = request.POST['event_astext']
                try:
                    event.parse_text(event_textarea, event_id, request.user.id)
                    return HttpResponseRedirect(reverse('event_show', kwargs={'event_id': event_id}))
                except ValidationError, error:
                    return render_to_response('error.html',
                        {'title': _("validation error"), 'message_col1': error, 'form': getEventForm(request.user)},
                        context_instance=RequestContext(request))
            else:
                return render_to_response('error.html', {'title': _("error"),
                    'form': getEventForm(request.user),
                    'message_col1': _("You submitted an empty form, nothing was saved. Click the back button in your browser and try again.")},
                    context_instance=RequestContext(request))
    else:
        event_textarea = event.as_text()
        templates = { 'title': _("edit event as text"), 'event_textarea': event_textarea, 'event_id': event_id }
        return render_to_response('event_edit_raw.html', templates, context_instance=RequestContext(request))

def event_show(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': _("error"), 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if not Event.is_event_viewable_by_user(event_id, request.user.id):
        return render_to_response('error.html',
                {'title': _("error"), 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to view the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        templates = {'title': _("view event detail"), 'event': event }
        return render_to_response('event_show.html', templates, context_instance=RequestContext(request))

def event_show_raw(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return render_to_response('error.html',
                    {'title': _("error"), 'form': getEventForm(request.user),
                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
                    context_instance=RequestContext(request))
    if not Event.is_event_viewable_by_user(event_id, request.user.id):
        return render_to_response('error.html',
                {'title': _("error"), 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to view the event with the following number") +
                ": " + str(event_id) + ". " +
                _("Maybe it is because you are not logged in with the right account") + "."},
                context_instance=RequestContext(request))
    else:
        event_textarea = event.as_text()
        templates = {'title': _("view as text"), 'event_textarea': event_textarea, 'event_id': event_id }
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
                {'title': _("error"), 'message_col1': errmsg, 'query': q},
                context_instance=RequestContext(request))

        if len(search_result) == 0:
            return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("Your search didn't get any result") + ".", 'query': q},
                context_instance=RequestContext(request))
        else:
            return render_to_response('list_events_search.html',
                {'title': _("search results"), 'events': search_result, 'query': q},
                context_instance=RequestContext(request))

@login_required
def filter_save(request):
    if 'q' in request.POST and request.POST['q']:
        q = request.POST['q'].lower()
    else:
        q = ''

    if q == '':
        return render_to_response('error.html',
                {'title': _("error"), 'form': getEventForm(request.user),
                'message_col1': _("You are trying to save a search without any search terms") + "."},
                context_instance=RequestContext(request))
    elif (not request.user.is_authenticated()):
        return render_to_response('error.html',
                {'title': _("error"), 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to save this search because you are not logged in") + "."},
                context_instance=RequestContext(request))
    elif request.method == 'POST':
                    try:
                        max = Filter.objects.aggregate(Max('id'))['id__max']
                        filter = Filter()
                        filter.user = request.user
                        filter.query = q
                        filter.name = str(request.user) + "'s filter " + str(max)
                        filter.save()
                        return HttpResponseRedirect(reverse('filter_edit', kwargs={'filter_id': filter.id}))
                    except Exception:
                        return render_to_response('error.html', {'title': _("error"), 'form': getEventForm(request.user), 'message_col1': _("An error has ocurred, nothing was saved. Click the back button in your browser and try again.")}, context_instance=RequestContext(request))
    else:
            return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("You have submitted a GET request which is not a valid method for this function") + ".", 'query': q},
                context_instance=RequestContext(request))

@login_required
def filter_edit(request, filter_id):
    try:
        filter = Filter.objects.get(pk=filter_id)
    except filter.DoesNotExist:
        return render_to_response('error.html',
                    {'title': _("error"), 'form': getEventForm(request.user),
                    'message_col1': _("The saved search with the following number doesn't exist") + ": " + str(filter_id)},
                    context_instance=RequestContext(request))
    if ((not request.user.is_authenticated()) or (filter.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': _("error"), 'form': getEventForm(request.user),
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

@login_required
def filter_drop(request, filter_id):
    try:
        filter = Filter.objects.get(pk=filter_id)
    except Filter.DoesNotExist:
        return render_to_response('error.html',
                    {'title': _("error"), 'form': getEventForm(request.user),
                    'message_col1': _("The saved search with the following number doesn't exist") + ": " + str(filter_id)},
                    context_instance=RequestContext(request))
    if ((not request.user.is_authenticated()) or (filter.user.id != request.user.id)):
        return render_to_response('error.html',
                {'title': _("error"), 'form': getEventForm(request.user),
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

@login_required
def list_filters_my(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
    else:
        list_of_filters = filter_list(request.user.id)
        if len(list_of_filters) == 0:
            return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("You do not have any filters configured") + "."},
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
                    {'title': _("error"), 'message_col1': _("Your search didn't get any result") + "."},
                    context_instance=RequestContext(request))
            else:
                return render_to_response('events/list_user.html',
                    {'events': events, 'username': username},
                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("User does not exist") + "."},
                context_instance=RequestContext(request))
    else:
        try:
            u = User.objects.get(username__exact=username)
            useridtmp = u.id
            events = Event.objects.filter(user=useridtmp)
            if len(events) == 0:
                return render_to_response('error.html',
                    {'title': _("error"), 'message_col1': _("Your search didn't get any result") + "."},
                    context_instance=RequestContext(request))
            else:
                return render_to_response('events/list_user.html',
                    {'events': events, 'username': username},
                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("User does not exist") + "."},
                context_instance=RequestContext(request))

@login_required
def list_events_my(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
    else:
        events = Event.objects.filter(user=request.user)
        if len(events) == 0:
            return render_to_response('error.html',
                {'title': _("error"), 'message_col1': _("Your search didn't get any result") + "."},
                context_instance=RequestContext(request))
        else:
            return render_to_response('list_events_my.html',
                {'title': _("list my events"), 'events': events},
                context_instance=RequestContext(request))

def list_events_tag(request, tag):
    """ returns a view with events having a tag
    """
    from re import sub
    query_tag = Tag.objects.get(name=tag)
    events = TaggedItem.objects.get_by_model(Event, query_tag)
    events = events.order_by('-start')
    return render_to_response('list_events_tag.html', {'title': _("list by tag"), 'events': events, 'tag': tag}, context_instance=RequestContext(request))

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

    about_text = open(settings.PROJECT_ROOT + '/ABOUT.TXT','r').read()

    return render_to_response('root.html', {
            'title': _("Welcome to GridCalendar"),
            'form': event_form,
            'events': events,
            'ip_country_event_list': ip_country_event_list,
            'ip_continent_event_list': ip_continent_event_list,
            'landless_event_list': landless_event_list,
            'group_events': all_events_in_user_groups(request.user.id, 5),
            'about_text': about_text,
        }, context_instance=RequestContext(request))

# http://docs.djangoproject.com/en/1.0/topics/auth/#the-login-required-decorator
@login_required
def settings_page(request):
    # user is logged in
    fl = filter_list(request.user.id)
    u = User(request.user)
    groups = Group.objects.filter(users_in_group__user=u)
    hash = hashlib.sha256("%s!%s" % (SECRET_KEY, request.user.id)).hexdigest()
    return render_to_response('settings.html', { 'title': _("settings"), 'filter_list': fl, 'groups': groups, 'user_id': request.user.id, 'hash': hash }, context_instance=RequestContext(request))
