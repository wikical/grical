#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
# gpl {{{1
#############################################################################
# Copyright 2009, 2010 Ivan Villanueva <ivan ät gridmind.org>
#
# This file is part of GridCalendar.
# 
# GridCalendar is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
# 
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

# docs {{{1
""" VIEWS """

# imports {{{1
import datetime
import vobject
import unicodedata

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from django.db.models import Max, Q
from django.forms import ValidationError
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from tagging.models import Tag, TaggedItem

from gridcalendar.events.decorators import login_required
from gridcalendar.events.forms import ( 
    SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, FilterForm,
    get_event_form, EventSessionForm, NewGroupForm, InviteToGroupForm,
    AddEventToGroupForm )
from gridcalendar.events.models import ( 
    Event, EventUrl, EventSession, EventDeadline, Filter, Group,
    Membership, GroupInvitation, ExtendedUser, Calendar)
from gridcalendar.events.lists import ( 
    filter_list, list_search_get )
from gridcalendar.settings import PROJECT_NAME

def _error( request, errors ): # {{{1
    """ Returns a view with an error message whereas 'errors' must be a list or
    a unicode """
    if not isinstance(errors, list):
        assert (isinstance(errors, unicode))
        errors = [errors,]
    return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar.net - error" ),
                'form': get_event_form( request.user ),
                'messages_col1': errors
            },
            context_instance = RequestContext( request ) )

def usage( request ): # {{{1
    """ Just returns the usage page including the RST documentation in the file
    USAGE.TXT"""
    usage_text = open( settings.PROJECT_ROOT + '/USAGE.TXT', 'r' ).read()
    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    return render_to_response( 'help.html', {
            'title': _( 'GridCalendar.net - help' ),
            'usage_text': usage_text,
            'about_text': about_text,
            }, context_instance = RequestContext( request ) )

def legal_notice( request ): # {{{1
    """Just returns the legal notice page."""
    return render_to_response( 'legal_notice.html', {
            'title': _( 'GridCalendar.net - legal notice' ),
            }, context_instance = RequestContext( request ) )

def event_new( request ): # {{{1
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

def event_edit( request, event_id ): # {{{1
    """ view to edit an event as a form """
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
        assert ( event.user != None and type ( event.user ) != AnonymousUser )
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

def event_new_raw( request ): # {{{1
    """ View to create an event as text. """
    if request.method == 'POST':
        if 'event_astext' in request.POST:
            event_textarea = request.POST['event_astext']
            try:
                Event.parse_text( event_textarea, None, request.user.id )
                # TODO: inform that the event was saved
                return HttpResponseRedirect( reverse( 'main' ) )
            except ValidationError as err:
                error_messages = []
                if hasattr( err, 'message_dict' ):
                    # if hasattr(err, 'message_dict'), it looks like:
                    # {'url': [u'Enter a valid value.']}
                    for field_name, error_message in err.message_dict.items():
                        error_messages.append(
                                field_name + ": " + error_message )
                elif hasattr( err, 'messages' ):
                    for message in err.messages:
                        error_messages.append( message )
                elif hasattr( err, 'message' ):
                    error_messages.append( err.message )
                templates = {
                        'title': _( "edit event as text" ),
                        'messages_col1': error_messages,
                        'event_textarea': event_textarea,
                        'example': Event.example() }
                return render_to_response(
                        'event_new_raw.html',
                        templates,
                        context_instance = RequestContext( request ) )
        else:
            return _error( request,
                _( ''.join( "You submitted an empty form, nothing was saved. ",
                    "Click the back button in your browser and try again." )))
    else:
        templates = { 'title': _( "edit event as text" ), \
                'example': Event.example() }
        return render_to_response( 'event_new_raw.html', templates,
                context_instance = RequestContext( request ) )

def event_edit_raw( request, event ): # {{{1
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
        if ( not request.user.is_authenticated() ):
            return _error( request,
                _( ''.join('You need to be logged-in to be able to edit the ',
                    'private event with the number %(event_id)d. ',
                    'Please log in a try again.' ) ) % {'event_id': event_id} )
        else:
            if not Event.is_event_viewable_by_user(
                    event_id, request.user.id ):
                return _error( request,
                    _( ''.join('You are not allowed to edit the event with ',
                        'the number %s(event_id)d' ) ) % \
                                {'event_id': event_id} )
    if request.method == 'POST':
        if 'event_astext' in request.POST:
            event_textarea = request.POST['event_astext']
            try:
                event = event.parse_text(
                        event_textarea, event_id, request.user.id )
            except ValidationError as err:
                # found a validation error with one or more errors
                error_messages = []
                if hasattr( err, 'message_dict' ):
                    # if hasattr(err, 'message_dict'), it looks like:
                    # {'url': [u'Enter a valid value.']}
                    for field_name, error_message in err.message_dict.items():
                        error_messages.append(
                                field_name + ": " + error_message )
                elif hasattr( err, 'messages' ):
                    for message in err.messages:
                        error_messages.append( message )
                elif hasattr( err, 'message' ):
                    error_messages.append( err.message )
                templates = {
                        'title': _( "edit event as text" ),
                        'event_textarea': event_textarea,
                        'event_id': event_id,
                        'messages_col1': error_messages,
                        'example': Event.example() }
                return render_to_response( 'event_edit_raw.html', templates,
                        context_instance = RequestContext( request ) )
            if type( event ) == type( errors ):
            #if no errors, parse_text returns event instance
                return HttpResponseRedirect( 
                    reverse( 'event_show', kwargs = {'event_id': event_id} ) )
            else:
            #else, parse_text return errors list
                return _error( request, errors )
        else:
            return _error( request,
                _( ''.join( 'You submitted an empty form, nothing was saved.',
                    ' Click the back button in your browser and try again.' )))
    else:
        event_textarea = event.as_text()
        templates = {
                'title': _( "edit event as text" ),
                'event_textarea': event_textarea,
                'event_id': event_id,
                'example': Event.example() }
        return render_to_response( 'event_edit_raw.html', templates,
                context_instance = RequestContext( request ) )

def event_show( request, event_id ): # {{{1
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

def event_show_raw( request, event_id ): # {{{1
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

def query( request ): # {{{1
    """ View to get the data of a search query calling `list_events_search` """
    # FIXME: replace everything using something like the first example at
    # http://www.djangobook.com/en/1.0/chapter07/
    if 'q' in request.GET and request.GET['q']:
        return HttpResponseRedirect( 
                reverse( 'list_events_search',
                kwargs = {'query': request.GET['q'], } ) )

def list_events_search( request, query ): # {{{1
    """ View to show the results of a search query """
    search_result = Filter.matches(query, request.user)
    if len( search_result ) == 0:
        return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar - no search results" ),
                'messages_col1': [_( u"Your search didn't get any result" ),],
                'query': query,
                'form': get_event_form( request.user ),
            },
            context_instance = RequestContext( request ) )
    else:
        return render_to_response( 'list_events_search.html',
            {
                'title': _( "search results" ),
                'events': search_result,
                'query': query,
                'user_id': request.user.id,
                'hash': ExtendedUser.calculate_hash(request.user.id),
            },
            context_instance = RequestContext( request ) )

def list_events_search_hashed( request, query, user_id, hash ): # {{{1
    """ View to show the results of a search query with hashed authentification
    """
    if ExtendedUser.calculate_hash(user_id) != hash:
        raise Http404
    search_result = Filter.matches(query, user_id)
    if len( search_result ) == 0:
        return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar - no search results" ),
                'messages_col1': [_( u"Your search didn't get any result" ),],
                'query': query,
                'form': get_event_form( request.user ),
            },
            context_instance = RequestContext( request ) )
    else:
        return render_to_response( 'list_events_search.html',
            {
                'title': _( "search results" ),
                'events': search_result,
                'query': query,
                'user_id': request.user.id,
                'hash': ExtendedUser.calculate_hash(request.user.id),
            },
            context_instance = RequestContext( request ) )

@login_required
def filter_save( request ): # {{{1
    """ Saves a new filter """
    if 'q' in request.POST and request.POST['q']:
        query_lowercase = request.POST['q'].lower()
    else:
        return _error( request,
            _( u"You are trying to save a search without any search terms" ) )
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
                    _( u"An error has ocurred, nothing was saved. Click the \
                    back button in your browser and try again." ) )
    else:
        return _error( request, _( "You have submitted a GET request " +
                        "which is not a valid method for saving a filter" ))

@login_required
def filter_edit( request, filter_id ): # {{{1
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
def filter_drop( request, filter_id ): # {{{1
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
def list_filters_my( request ): # {{{1
    """ View that lists the filters of the logged-in user """
    list_of_filters = Filter.objects.filter( user = request.user )
    if list_of_filters is None or len( list_of_filters ) == 0:
        return _error( request,
            _( "You do not have any filters configured" ) )
    else:
        return render_to_response( 'list_filters_my.html',
            {'title': _( u'list of my filters' ), 'filters': list_of_filters},
            context_instance = RequestContext( request ) )

def list_events_of_user( request, username ): # {{{1
    """ View that lists the events of a user """
    if ( ( not request.user.is_authenticated() ) or
            ( request.user.id is None ) ):
        try:
            user = User.objects.get( username__exact = username )
            useridtmp = user.id
            events = Event.objects.filter( user = useridtmp ) # FIXME: what is this?
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
def list_events_my( request ): # {{{1
    """ View that lists the events the logged-in user is the owner of """
    events = Event.objects.filter( user = request.user )
    if len( events ) == 0:
        return _error( request, _( "Your search didn't get any result" ) )
    else:
        return render_to_response( 'list_events_my.html',
            {'title': _( "list my events" ), 'events': events},
            context_instance = RequestContext( request ) )

def list_events_tag( request, tag ): # {{{1
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

def main( request ): # {{{1
    """ main view
    
    >>> from django.test import Client
    >>> c = Client()
    >>> r = c.get('/')
    >>> r.status_code # /
    200
    """
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
    today = datetime.date.today()
    elist = Event.objects.filter (
                Q(start__gte=today) |
                Q(end__gte=today) |
                Q(deadlines__deadline__gte=today) )
    if not request.user.is_authenticated():
        elist = elist.filter(public = True)
    else:
        elist = elist.filter(
                Q( user = request.user ) |
                Q( calendar__group__membership__user = request.user ) |
                Q( public = True ) )
    elist = elist.distinct()
    elist = sorted(elist, key=Event.next_coming_date_or_start)
    elist = elist[0:settings.MAX_EVENTS_ON_ROOT_PAGE]
    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    return render_to_response( 'base_main.html',
            {
                'title': _( "GridCalendar - the community Calendar" ),
                'form': event_form,
                'events': elist,
                'about_text': about_text,
            },
            context_instance = RequestContext( request ) )

@login_required
def settings_page( request ): # {{{1
    """ View to show the settings of a user """
    # user is logged in because of decorator
    list_of_filters = filter_list( request.user.id )
    user = User( request.user )
    groups = Group.objects.filter( membership__user = user )
    hashvalue = ExtendedUser.calculate_hash(user.id)
    return render_to_response( 'settings.html',
            {
                'title': _( "settings" ),
                'filter_list': list_of_filters,
                'groups': groups,
                'user_id': request.user.id,
                'hash': hashvalue
            },
            context_instance = RequestContext( request ) )

# groups views {{{1

@login_required
def group_new(request): # {{{2
    """ View to create a new group """
    if not request.user.is_authenticated():
        return render_to_response('groups/no_authenticated.html',
                {}, context_instance=RequestContext(request))
    if request.method == 'POST':
        form = NewGroupForm(request.POST)
        if form.is_valid():
            form.save()
            group_name = request.POST.get('name', '')
            new_group = Group.objects.get(name=group_name)
            new_membership = Membership(user=request.user, group=new_group)
            new_membership.save()
            # TODO: notify all invited members of the group
            return HttpResponseRedirect(reverse('list_groups_my'))
        else:
            return render_to_response('groups/create.html',
                    {'form': form}, context_instance=RequestContext(request))
    else:
        form = NewGroupForm()
        return render_to_response('groups/create.html',
                {'form': form}, context_instance=RequestContext(request))

@login_required
def list_groups_my(request): # {{{2
    """ view that lists all groups of the logged-in user """
    # Theoretically not needed because of the decorator:
    #if ((not request.user.is_authenticated()) or (request.user.id is None)):
    #    return render_to_response('error.html',
    #            {
    #                'title': 'error',
    #                'messages_col1': [_("You must be logged in to list your groups"),]
    #            },
    #            context_instance=RequestContext(request))
    #else:
    user = User(request.user)
    groups = Group.objects.filter(membership__user=user)
    if len(groups) == 0:
        return render_to_response('error.html',
            {
                'title': 'error',
                'messages_col1': [_("You are not a member of any group"),]
            },
            context_instance=RequestContext(request))
    else:
        return render_to_response('groups/list_my.html',
            {'title': 'list my groups', 'groups': groups},
            context_instance=RequestContext(request))

@login_required
def group_quit(request, group_id, sure): # {{{2
    """ remove the logged-in user from a group asking for confirmation if the
    user is the last member of the group """
    user = User(request.user)
    try:
        group = Group.objects.get(id=group_id, membership__user=user)
    except Group.DoesNotExist:
        return render_to_response('error.html',
                {
                    'title': 'error',
                    'messages_col1': [_( ''.join("There is no such group, ",
                        "or you are not a member of that group") ),]
                },
                context_instance=RequestContext(request))
    testsize = len(
            Membership.objects.filter(group=group).exclude(user=user))
    if (testsize > 0):
        membership = Membership.objects.get(user=request.user, group=group)
        membership.delete()
        return HttpResponseRedirect(reverse('list_groups_my'))
    elif (sure):
        membership = Membership.objects.get(user=request.user, group=group)
        membership.delete()
        group.delete()
        return HttpResponseRedirect(reverse('list_groups_my'))
    else:
        return render_to_response('groups/quit_group_confirm.html',
                # TODO: show the user a list of all private events which will
                # be lost for everyone
                {
                    'group_id': group_id,
                    'group_name': group.name
                },
                context_instance=RequestContext(request))
#        except:
#            return render_to_response('error.html', {'title': 'error',
#            'message_col1': _("Quitting group failed") + "."},
#            context_instance=RequestContext(request))

@login_required
def group_quit_ask(request, group_id): # {{{2
    """ view to confirm of quiting a group """
    return group_quit(request, group_id, False)

@login_required
def group_quit_sure(request, group_id):
    """ view to confirm of quiting a group being sure"""
    return group_quit(request, group_id, True)

@login_required
def group_add_event(request, event_id): # {{{2
    """ view to add an event to a group """
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {
                    'title': 'GridCalendar.net - error',
                    'messages_col1': [_(''.join_("You must be logged in to ",
                        "add an event to a group")),]
                },
                context_instance=RequestContext(request))
    event = Event.objects.get(id=event_id)
    user = User(request.user)
    if len(Group.groups_for_add_event(user, event)) > 0:
        if request.POST:
            form = AddEventToGroupForm(
                    data=request.POST, user=user, event=event)
            if form.is_valid():
                for group in form.cleaned_data['grouplist']:
                    if event.public:
                        event_for_group = event
                    else:
                        event_for_group = event.clone()
                    calentry = Calendar(event=event_for_group, group=group)
                    calentry.save()
                return HttpResponseRedirect(reverse('list_groups_my'))
            else:
                request.user.message_set.create(
                        message='Please check your data.')
        else:
            form = AddEventToGroupForm(user=user, event=event)
        context = dict()
        context['form'] = form
        return render_to_response('groups/add_event_to_group.html',
                context_instance=RequestContext(request, context))
    else:
        return render_to_response('error.html',
                    {
                        'title': 'error',
                        'messages_col1': [_(''.join("This event is already ",
                            "in all groups that you are in, so you can't ",
                            "add it to any more groups.")),]
                    },
                    context_instance=RequestContext(request))

def group_view(request, group_id): # {{{2
    """ view that lists everything about a group """
    group = Group.objects.get( id = group_id )
    events = Event.objects.filter(calendar__group = group)
    return render_to_response(
            'groups/group_view.html',
            {
                'title': _( u'%(project_name)s - group %(group_name)s' ) % \
                        {
                            'group_name': group.name,
                            'project_name': PROJECT_NAME,
                        },
                'group': group,
                'user_is_in_group': \
                    Group.is_user_in_group(request.user, group),
            },
            context_instance=RequestContext(request))

@login_required
def group_invite(request, group_id): # {{{2
    """ view to invite a user to a group """
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {
                    'title': 'error',
                    'messages_col1': [_(''.join("You must be logged in to ",
                        "invite someone to a group")),]
                },
                context_instance=RequestContext(request))
    else:
        group = Group.objects.get(id=group_id)
        if request.POST:
            username_dirty = request.POST['username']
            formdata = {'username': username_dirty,
                        'group_id': group_id}
            form = InviteToGroupForm(data=formdata)
            if form.is_valid():
                username = form.cleaned_data['username']
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return render_to_response('error.html',
                        {
                            'title': 'error',
                            'messages_col1': [_(''.join("There is no user ",
                                "with the username: %(username)s")) % \
                                        {'username': username,},]
                        },
                        context_instance=RequestContext(request))
                GroupInvitation.objects.create_invitation(host=request.user,
                        guest=user, group=group , as_administrator=True)
                return HttpResponseRedirect(reverse('list_groups_my'))
            else:
                request.user.message_set.create(
                        message='Please check your data.')
        else:
#            form = InviteToGroupForm(instance=invitation)
#            formdata = {
#                        'username': None,
#                        'group_id': group_id}
#            form = InviteToGroupForm(data=formdata)
            form = InviteToGroupForm()
        return render_to_response('groups/invite.html',
                {
                    'title': 'invite to group',
                    'group_id': group_id,
                    'form': form
                },
                context_instance=RequestContext(request))

def group_invite_activate(request, activation_key): # {{{2
    """ A user clicks on activation link """
    invitation = GroupInvitation.objects.get(activation_key=activation_key)
    group_id = invitation.id
    group = Group.objects.get(id = group_id)
    activation = GroupInvitation.objects.activate_invitation(activation_key)
    if activation:
        return render_to_response('groups/invitation_activate.html',
                {'title': _(u'invitation activated'), 'group': group},
                context_instance=RequestContext(request))
    else:
        return render_to_response('groups/invitation_activate_failed.html',
                {'title': 'activate invitation failed', 'group_id': group_id},
                context_instance=RequestContext(request))

# ical views {{{1
def ICalForSearch( request, query ): # {{{2
    elist = list_search_get(query) # FIXME: it can be too long
    elist = [eve for eve in elist if eve.is_viewable_by_user( request.user )]
    return _ical_http_response_from_event_list( elist, query )

def ICalForEvent( request, event_id ): # {{{2
    event = Event.objects.get( id = event_id )
    elist = [event,]
    elist = [eve for eve in elist if eve.is_viewable_by_user(request.user)]
    return _ical_http_response_from_event_list( elist, event.title )

def ICalForEventHash (request, event_id, user_id, hash): # {{{2
    user = ExtendedUser.objects.get(id = user_id)
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [_(u"hash authentification failed"),]
            },
            context_instance=RequestContext(request))
    event = Event.objects.get( id = event_id )
    if not event.is_viewable_by_user( user ):
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [
                _(u"user authentification for requested event failed"),]
            },
            context_instance=RequestContext(request))
    return _ical_http_response_from_event_list(
            [event,], event.title)
            

def ICalForSearchHash( request, query, user_id, hash ): # {{{2
    user = ExtendedUser.objects.get(id = user_id)
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [_(u"hash authentification failed"),]
            },
            context_instance=RequestContext(request))
    elist = list_search_get(query) # FIXME: it can be too long
    elist = [eve for eve in elist if eve.is_viewable_by_user( user_id )]
    return _ical_http_response_from_event_list( elist, query )

def ICalForGroup( request, group_id ): # {{{2
    """ return all public events with a date in the future in icalendar format
    belonging to a group """
    group = Group.objects.filter(id = group_id)
    elist = Event.objects.filter(calendar__group = group, public = True)
    today = datetime.date.today()
    elist = elist.filter (
                Q(start__gte=today) |
                Q(end__gte=today) |
                Q(deadlines__deadline__gte=today) ).distinct()
    elist = sorted(elist, key=Event.next_coming_date_or_start)
    return _ical_http_response_from_event_list( elist, group.name )

def ICalForGroupHash( request, group_id, user_id, hash ): # {{{2
    """ return all events with a date in the future in icalendar format
    belonging to a group """
    user = ExtendedUser.objects.get(id = user_id)
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [_(u"hash authentification failed"),]
            },
            context_instance=RequestContext(request))
    group = Group.objects.get(id = group_id)
    if not group.is_member(user_id):
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [_(u"not a member of the tried group"),]
            },
            context_instance=RequestContext(request))
    elist = Event.objects.filter(calendar__group = group)
    today = datetime.date.today()
    elist = elist.filter (
                Q(start__gte=today) |
                Q(end__gte=today) |
                Q(deadlines__deadline__gte=today) ).distinct()
    elist = sorted(elist, key=Event.next_coming_date_or_start)
    return _ical_http_response_from_event_list( elist, group.name )

def _ical_http_response_from_event_list( elist, filename ): # {{{2
    if len(elist) == 1:
        icalstream = elist[0].icalendar().serialize()
    else:
        ical = vobject.iCalendar()
        ical.add('METHOD').value = 'PUBLISH' # IE/Outlook needs this
        ical.add('PRODID').value = settings.PRODID
        for event in elist:
            event.icalendar(ical)
        icalstream = ical.serialize()
    response = HttpResponse( icalstream, 
            mimetype = 'text/calendar;charset=UTF-8' )
    filename = unicodedata.normalize('NFKD', filename).encode('ascii','ignore')
    filename = filename.replace(' ','_')
    if not filename[-4:] == '.ics':
        filename = filename + '.ics'
    response['Filename'] = filename  # IE needs this
    response['Content-Disposition'] = 'attachment; filename=' + filename
    return response

