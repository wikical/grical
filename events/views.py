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

""" VIEWS """

import hashlib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.forms import ValidationError
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from django.contrib.auth.models import User
from gridcalendar.events.decorators import login_required

from gridcalendar.settings_local import SECRET_KEY

from tagging.models import Tag, TaggedItem

from gridcalendar.events.models import ( 
    Event, EventUrl, EventSession, EventDeadline, Filter, Group )
from gridcalendar.events.forms import ( 
    SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, FilterForm,
    get_event_form, EventSessionForm )
from gridcalendar.events.lists import ( 
    filter_list, events_with_user_filters,
    user_filters_events_list, all_events_in_user_groups, uniq_events_list,
    list_up_to_max_events_ip_country_events, list_search_get )
#from django.shortcuts import render_to_response
#from django.http import HttpResponseRedirect
#from django import forms
#from django.conf import settings
#import captcha
#
#class ContactForm( forms.Form ):
#    message = forms.CharField()
#
#def contact( request ):
#    if request.method == 'POST':
#        # Check the captcha
#        check_captcha = captcha.submit( \
#                    request.POST['recaptcha_challenge_field'], \
#                    request.POST['recaptcha_response_field'], \
#                    settings.RECAPTCHA_PRIVATE_KEY, \
#                    request.META['REMOTE_ADDR'] )
#        if check_captcha.is_valid is False:
#            # Captcha is wrong show a error ...
#            return HttpResponseRedirect( '/url/error/' )
#        form = ContactForm( request.POST )
#        if form.is_valid():
#            # Do form processing here...
#            return HttpResponseRedirect( '/url/on_success/' )
#    else:
#        form = ContactForm()
#        html_captcha = captcha.displayhtml( settings.RECAPTCHA_PUB_KEY )
#    return render_to_response( 'contact.html', {'form': form, \
#                                               'html_captcha': html_captcha} )

# notice that an anonymous user get a form without the 'public' field
# (simplified form)

def _error( request, text ):
    """ Returns a view with the front page and an error message """
    return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar.net - error" ),
                'form': get_event_form( request.user ),
                'message_col1': text
            },
            context_instance = RequestContext( request ) )

def _errors( request, texts ):
    """ Returns a view with the front page and an error message """
    text = "<ul>"
    for msg in texts:
        text += "<li>%s</li>" % msg
    text += "</ul>"
    return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar.net - error" ),
                'form': get_event_form( request.user ),
                'message_col1': text
            },
            context_instance = RequestContext( request ) )

def usage( request ):
    """ Just returns the usage page including the RST documentation in the file
    USAGE.TXT"""
    usage_text = open( settings.PROJECT_ROOT + '/USAGE.TXT', 'r' ).read()
    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    return render_to_response( 'help.html', {
            'title': _( 'GridCalendar.net - help' ),
            'usage_text': usage_text,
            'about_text': about_text,
            }, context_instance = RequestContext( request ) )

def legal_notice( request ):
    """Just returns the legal notice page."""
    return render_to_response( 'legal_notice.html', {
            'title': _( 'GridCalendar.net - legal notice' ),
            }, context_instance = RequestContext( request ) )

def event_new( request ):
    """ Expects a filled simplified event form and redirects to `event_edit`
    """
    if request.method == 'POST':
        if request.user.is_authenticated():
            sef = SimplifiedEventForm( request.POST )
        else:
            sef = SimplifiedEventFormAnonymous( request.POST )
        if sef.is_valid():
            cleaned_data = sef.cleaned_data
            # create a new entry and saves the data
            if request.user.is_authenticated():
                public = cleaned_data['public']
            else:
                public = True
            event = Event(
                        user_id = request.user.id,
                        title   = cleaned_data['title'],
                        start   = cleaned_data['start'],
                        tags    = cleaned_data['tags'],
                        public  = public )
            event.save()
            return HttpResponseRedirect( reverse( 'event_edit',
                    kwargs = {'event_id': str( event.id )} ) )
            # TODO: look in a thread for all users who wants to receive an
            # email notification and send it
        else:
            return render_to_response( 'base_main.html',
                    {'title': _( "GridCalendar.net" ), 'form': sef},
                    context_instance = RequestContext( request ) )
    else:
        return HttpResponseRedirect( reverse( 'main' ) )

def event_edit( request, event_id ):
    event_id = int(event_id)
    """ Complete web-form to edit an event. """
    # checks if the event exists
    try:
        event = Event.objects.get( pk = event_id )
    except Event.DoesNotExist:
        return _error( request, ''.join( 
                _( "The event with the following number doesn't exist" ), ": ",
                str( event_id ) ), )

    # checks if the user is allowed to edit this event
    # public events can be edited by anyone, otherwise only by the submitter
    # and the group the event belongs to
    if not event.public :
        # events submitted by anonymous users cannot be non-public:
        assert ( event.user != None )
        if ( not request.user.is_authenticated() ):
            return _error( request,
                _( 'You need to be logged-in to be able to edit the event \
                with the number:' ) + " " + str( event_id ) +
                _( "Please log-in and try again" ) + "." )
        else:
            if ( not Event.is_event_viewable_by_user(
                    event_id, request.user.id ) ):
                return _error( request,
                    _( 'You are not allowed to edit the event with the \
                        number:' ) + " " + str( event_id ) )
    event_urls_factory = inlineformset_factory( 
            Event, EventUrl, extra = 4 )
    evetn_deadlines_factory = inlineformset_factory( 
            Event, EventDeadline, extra = 4 )
    event_sessions_factory = inlineformset_factory( 
            Event, EventSession, extra = 4, form = EventSessionForm )
    if request.method == 'POST':
        formset_url = \
                event_urls_factory( request.POST, instance = event )
        formset_deadline = \
                evetn_deadlines_factory( request.POST, instance = event )
        formset_session = \
                event_sessions_factory( request.POST, instance = event )
        event_form = \
                EventForm( request.POST, instance = event )
        if event_form.is_valid() & formset_url.is_valid() & \
                formset_session.is_valid() & formset_deadline.is_valid() :
            # TODO: use the session middleware to commit as an atom
            event_form.save()
            formset_url.save()
            formset_session.save()
            formset_deadline.save()
            # TODO: look in a thread for all users who wants to receive an
            # email notification and send it
            return HttpResponseRedirect( 
                    reverse( 'event_show', kwargs = {'event_id': event_id} ) )
        else:
            templates = {
                    'title': 'edit event',
                    'form': event_form,
                    'formset_url': formset_url,
                    'formset_session': formset_session,
                    'formset_deadline': formset_deadline,
                    'event_id': event_id }
            return render_to_response( 'event_edit.html', templates,
                    context_instance = RequestContext( request ) )
    else:
        event_form = EventForm( instance = event )
        formset_url = event_urls_factory( instance = event )
        formset_deadline = evetn_deadlines_factory( instance = event )
        formset_session = event_sessions_factory( instance = event )
        templates = {
                'title': 'edit event',
                'form': event_form,
                'formset_url': formset_url,
                'formset_session': formset_session,
                'formset_deadline': formset_deadline,
                'event_id': event_id }
        return render_to_response( 'event_edit.html', templates,
                context_instance = RequestContext( request ) )

def event_new_raw( request ):
    """ View to create an event as text. """
    if request.method == 'POST':
        if 'event_astext' in request.POST:
            event_textarea = request.POST['event_astext']
            try:
                Event.parse_text( event_textarea, None, request.user.id )
                # TODO: inform that the event was saved
                return HttpResponseRedirect( reverse( 'main' ) )
            except ValidationError, error:
                return _error( request, error )
        else:
            return _error( request,
                _( "You submitted an empty form, nothing was saved. Click the \
                back button in your browser and try again." ) )
    else:
        templates = { 'title': _( "edit event as text" ), \
                'example': Event.example() }
        return render_to_response( 'event_new_raw.html', templates,
                context_instance = RequestContext( request ) )

def event_edit_raw( request, event ):
    """ View to edit an event as text. """
    if isinstance(event, Event):
        event_id = event.id
    elif isinstance(event, int):
        event_id = event
    else:
        event_id = int(event)
    # checks if the event exists
    try:
        event = Event.objects.get( pk = event_id )
    except Event.DoesNotExist:
        return _error( request,
            _( u"The event with the number $(number)d doesn't exist." ) %
            {'number': str(event_id),})
    # checks if the user is allowed to edit this event
    # public events can be edited by anyone, otherwise only by the submitter
    # and the group the event belongs to
    if ( not event.public ):
        # events submitted by anonymous users cannot be non-public:
        assert ( event.user != None )
        if ( not request.user.is_authenticated() ):
            return _error( request,
                _( 'You need to be logged-in to be able to edit the event \
                    with the number:' ) + " " + str( event_id ) + ". " +
                _( "Please log-in and try again" ) + "." )
        else:
            if ( not Event.is_event_viewable_by_user(
                    event_id, request.user.id ) ):
                return _error( request,
                    _( 'You are not allowed to edit the event with the \
                    number:' ) + " " + str( event_id ) )
    if request.method == 'POST':
        if 'event_astext' in request.POST:
            event_textarea = request.POST['event_astext']
            errors = event.parse_text(
                    event_textarea, event_id, request.user.id )
            if type( event ) == type( errors ):
            #if no errors, parse_text returns event instance
                return HttpResponseRedirect( 
                    reverse( 'event_show', kwargs = {'event_id': event_id} ) )
            else:
            #else, parse_text return errors list
                return _errors( request, errors )
        else:
            return _error( request,
                _( "You submitted an empty form, nothing was saved. Click the \
                back button in your \ browser and try again." ) )
    else:
        event_textarea = event.as_text()
        templates = {
                'title': _( "edit event as text" ),
                'event_textarea': event_textarea,
                'event_id': event_id,
                'example': Event.example() }
        return render_to_response( 'event_edit_raw.html', templates,
                context_instance = RequestContext( request ) )

def event_show( request, event_id ):
    """ View that shows an event """
    event_id = int(event_id)
    try:
        event = Event.objects.get( pk = event_id )
    except Event.DoesNotExist:
        return _error( request,
            _( "The event with the following number doesn't exist" ) + ": " +
            str( event_id ) )
    if not Event.is_event_viewable_by_user( event_id, request.user.id ):
        return _error( request,
            _( "You are not allowed to view the event with the following \
            number" ) + ": " + str( event_id ) )
    else:
        templates = {'title': _( "view event detail" ), 'event': event }
        return render_to_response( 'event_show_all.html', templates,
                context_instance = RequestContext( request ) )

def event_show_raw( request, event_id ):
    """ View that shows an event as text """
    event_id = int(event_id)
    try:
        event = Event.objects.get( pk = event_id )
    except Event.DoesNotExist:
        return _error( request,
            _( "The event with the following number doesn't exist" ) + ": " +
            str( event_id ) )
    if not Event.is_event_viewable_by_user( event_id, request.user.id ):
        return _error( request,
            _( "You are not allowed to view the event with the following \
                    number:" ) + " " + str( event_id ) )
    else:
        event_textarea = event.as_text()
        templates = {
                'title': _( "view as text" ),
                'event_textarea': event_textarea,
                'event_id': event_id }
        return render_to_response( 'event_show_raw.html',
                templates, context_instance = RequestContext( request ) )

def query( request ):
    """ View to get the data of a search query calling `list_events_search` """
    # FIXME: replace everything using something like the first example at
    # http://www.djangobook.com/en/1.0/chapter07/
    if 'q' in request.GET and request.GET['q']:
        query_lowercase = request.GET['q'].lower()
        return HttpResponseRedirect( 
                reverse( 'list_events_search',
                kwargs = {'query': query_lowercase} ) )

def list_events_search( request, query ):
    """ View to show the results of a search query """
    query_lowercase = query.lower()
    user_id = request.user.id
    try:
        search_result = list_search_get( query_lowercase, user_id, 0 )
    except ValueError, ( errmsg ):
        return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar - search error" ),
                'message_col1': errmsg,
                'query': query_lowercase,
                'form': get_event_form( request.user )
            },
            context_instance = RequestContext( request ) )

    if len( search_result ) == 0:
        return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar - no search results" ),
                'message_col1': _( "Your search didn't get any result" ),
                'query': query,
                'form': get_event_form( request.user ),
            },
            context_instance = RequestContext( request ) )
    else:
        return render_to_response( 'list_events_search.html',
            {
                'title': _( "search results" ),
                'events': search_result,
                'query': query
            },
            context_instance = RequestContext( request ) )

@login_required
def filter_save( request ):
    """ Saves a new filter """
    if 'q' in request.POST and request.POST['q']:
        query_lowercase = request.POST['q'].lower()
    else:
        return _error( request,
            _( "You are trying to save a search without any search terms" ) )
    if request.method == 'POST':
        try:
            maximum = Filter.objects.aggregate( Max( 'id' ) )['id__max']
            efilter = Filter()
            efilter.user = request.user
            efilter.query = query_lowercase
            efilter.name = str( request.user ) + "'s filter " + str( maximum )
            efilter.save()
            return HttpResponseRedirect( reverse(
                'filter_edit', kwargs = {'filter_id': efilter.id} ) )
        except Exception:
            return _error( request,
                    _( "An error has ocurred, nothing was saved. Click the \
                    back button in your browser and try \ again." ) )
    else:
        return render_to_response( 'error.html',
                {
                    'title': _( "GridCalendar - error" ),
                    'message_col1': _( "You have submitted a GET request which \
                        is not a valid method for searching" ),
                    'query': query_lowercase
                },
                context_instance = RequestContext( request ) )

@login_required
def filter_edit( request, filter_id ):
    """ View to edit a filter """
    try:
        efilter = Filter.objects.get( pk = filter_id )
    except efilter.DoesNotExist:
        return _error( request,
                _( "The saved search with the following number doesn't exist:" )
                + " " + str( filter_id ) )
    if ( ( not request.user.is_authenticated() ) or \
            ( efilter.user.id != request.user.id ) ):
        return _error( 'error.html',
                _( 'You are not allowed to edit the saved search with the \
                        following number:' ) + " " + str( filter_id ) )
    else:
        if request.method == 'POST':
            ssf = FilterForm( request.POST, instance = efilter )
            if ssf.is_valid() :
                ssf.save()
                return HttpResponseRedirect( reverse( 'list_filters_my' ) )
            else:
                templates = {
                        'title': 'edit event',
                        'form': ssf,
                        'filter_id': filter_id }
                return render_to_response(
                        'filter_edit.html',
                        templates,
                        context_instance = RequestContext( request ) )
        else:
            ssf = FilterForm( instance = efilter )
            templates = {
                    'title': 'edit event',
                    'form': ssf,
                    'filter_id': filter_id }
            return render_to_response( 'filter_edit.html',
                    templates, context_instance = RequestContext( request ) )

@login_required
def filter_drop( request, filter_id ):
    """ Delete a filter if the user is the owner """
    try:
        efilter = Filter.objects.get( pk = filter_id )
    except Filter.DoesNotExist:
        return _error(
            request,
            _( "The saved search with the following number doesn't exist:" ) +
                str( filter_id ) )
    if ( ( not request.user.is_authenticated() ) or \
            ( efilter.user.id != request.user.id ) ):
        return _error( request,
                _( 'You are not allowed to delete the saved search with the \
                    following number:' ) + " " + str( filter_id ) )
    else:
        if request.method == 'POST':
            assert False
        else:
            efilter.delete()
            return HttpResponseRedirect( reverse( 'list_filters_my' ) )

@login_required
def list_filters_my( request ):
    """ View that lists the filters of the logged-in user """
    if ( ( not request.user.is_authenticated() ) or
            ( request.user.id is None ) ):
        return _error( request,
                _( "Your search didn't get any result" ) )
    else:
        list_of_filters = filter_list( request.user.id )
        if len( list_of_filters ) == 0:
            return _error( request,
                _( "You do not have any filters configured" ) )
        else:
            return render_to_response( 'list_filters_my.html',
                {'title': 'list of my filters', 'filters': list_of_filters},
                context_instance = RequestContext( request ) )

def list_events_of_user( request, username ):
    """ View that lists the events of a user """
    if ( ( not request.user.is_authenticated() ) or
            ( request.user.id is None ) ):
        try:
            user = User.objects.get( username__exact = username )
            useridtmp = user.id
            events = Event.objects.filter( user = useridtmp )
            events = Event.objects.filter( public = True )
            if len( events ) == 0:
                return _error( request,
                        _( "Your search didn't get any result" ) )
            else:
                return render_to_response( 'events/list_user.html',
                    {'events': events, 'username': username},
                    context_instance = RequestContext( request ) )
        except User.DoesNotExist:
            return _error( request, _( "User does not exist" ) )
    else:
        try:
            user = User.objects.get( username__exact = username )
            useridtmp = user.id
            events = Event.objects.filter( user = useridtmp )
            if len( events ) == 0:
                return _error(
                        request,
                        _( "Your search didn't get any result" ) )
            else:
                return render_to_response( 'events/list_user.html',
                    {'events': events, 'username': username},
                    context_instance = RequestContext( request ) )
        except User.DoesNotExist:
            return _error( request, ( "User does not exist" ) )

@login_required
def list_events_my( request ):
    """ View that lists the events the logged-in user is the owner of """
    if ( ( not request.user.is_authenticated() ) or
            ( request.user.id is None ) ):
        return _error( request, _( "Your search didn't get any result" ) )
    else:
        events = Event.objects.filter( user = request.user )
        if len( events ) == 0:
            return _error( request, _( "Your search didn't get any result" ) )
        else:
            return render_to_response( 'list_events_my.html',
                {'title': _( "list my events" ), 'events': events},
                context_instance = RequestContext( request ) )

def list_events_tag( request, tag ):
    """ returns a view with events having a tag """
    query_tag = Tag.objects.get( name = tag )
    events = TaggedItem.objects.get_by_model( Event, query_tag )
    events = events.order_by( '-start' )
    return render_to_response( 'list_events_tag.html',
            {
                'title': _( "list by tag" ),
                'events': events,
                'tag': tag
            },
            context_instance = RequestContext( request ) )

def main( request ):
    """ main view
    
    >>> from django.test import Client
    >>> c = Client()
    >>> r = c.get('/')
    >>> r.status_code # /
    200
    """
    user_id = request.user.id
    if request.method == 'POST':
        if request.user.is_authenticated():
            event_form = SimplifiedEventForm( request.POST )
        else:
            event_form = SimplifiedEventFormAnonymous( request.POST )
        if event_form.is_valid():
            cleaned_data = event_form.cleaned_data
            # create a new entry and saves the data
            if request.user.is_authenticated():
                public = cleaned_data['public']
            else:
                public = True
            event = Event( user_id = request.user.id,
                      title = cleaned_data['title'],
                      start = cleaned_data['start'],
                      tags = cleaned_data['tags'],
                      public = public )
            event.save()
            # create the url data
            event.urls.create( url_name = "web", url = cleaned_data['web'] )
            return HttpResponseRedirect( reverse( 'event_edit',
                    kwargs = {'event_id': str( event.id )} ) )
    else:
        if request.user.is_authenticated():
            event_form = SimplifiedEventForm()
        else:
            event_form = SimplifiedEventFormAnonymous()

    if request.user.is_authenticated():
        efl = events_with_user_filters( user_id )
        uel = uniq_events_list( efl )
        events = user_filters_events_list( user_id, efl )
    else:
        efl = list()
        uel = list()
        events = list()

    ip_country_event_list = list()
    ip_continent_event_list = list()
    landless_event_list = list()

    if len( events ) < settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len( events )
        ip_country_event_list = list_up_to_max_events_ip_country_events( 
                request.META.get( 'REMOTE_ADDR' ),
                user_id, uel, add_thismany, 'country' )
    else:
        ip_country_event_list = list()

    if ( len( events ) + len( ip_country_event_list ) ) < \
            settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len( events ) - \
                len( ip_country_event_list )
        ip_continent_event_list = list_up_to_max_events_ip_country_events( 
                request.META.get( 'REMOTE_ADDR' ), user_id, uel, add_thismany,
                'continent' )
    else:
        ip_continent_event_list = list()

    if ( len( events ) + len( ip_country_event_list ) + \
            len( ip_continent_event_list ) ) < \
                settings.MAX_EVENTS_ON_ROOT_PAGE :
        add_thismany = settings.MAX_EVENTS_ON_ROOT_PAGE - len( events ) - \
                len( ip_country_event_list ) - len( ip_continent_event_list )
        landless_event_list = list_up_to_max_events_ip_country_events( 
                request.META.get( 'REMOTE_ADDR' ), user_id, uel, add_thismany,
                'landless' )

    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    return render_to_response( 'base_main.html',
            {
                'title': _( "Welcome to GridCalendar" ),
                'form': event_form,
                'events': events,
                'ip_country_event_list': ip_country_event_list,
                'ip_continent_event_list': ip_continent_event_list,
                'landless_event_list': landless_event_list,
                'group_events': all_events_in_user_groups( request.user.id, 5 ),
                'about_text': about_text,
            },
            context_instance = RequestContext( request ) )

# http://docs.djangoproject.com/en/1.0/topics/auth/#the-login-required-decorator
@login_required
def settings_page( request ):
    """ View to show the settings of a user """
    # user is logged in because of decorator
    list_of_filters = filter_list( request.user.id )
    user = User( request.user )
    groups = Group.objects.filter( membership__user = user )
    hashvalue = hashlib.sha256( 
            "%s!%s" % ( SECRET_KEY, request.user.id ) ).hexdigest()
    return render_to_response( 'settings.html',
            {
                'title': _( "settings" ),
                'filter_list': list_of_filters,
                'groups': groups,
                'user_id': request.user.id,
                'hash': hashvalue
            },
            context_instance = RequestContext( request ) )
