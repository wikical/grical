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
from django.shortcuts import ( render_to_response, get_object_or_404,
        get_list_or_404 )
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
from gridcalendar.settings import PROJECT_NAME

# FIXME: use everywhere when possible get_object_or_404 and get_list_or_404
def _error( request, errors ): # {{{1
    """ Returns a view with an error message whereas 'errors' must be a list or
    a unicode """
    if not isinstance(errors, list):
        assert (isinstance(errors, unicode))
        errors = [errors,]
    return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar - error" ),
                'form': get_event_form( request.user ),
                'messages_col1': errors
            },
            context_instance = RequestContext( request ) )

def help( request ): # {{{1
    """ Just returns the usage page including the RST documentation in the file
    USAGE.TXT
    
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('help')).status_code
    200
    """
    usage_text = open( settings.PROJECT_ROOT + '/USAGE.TXT', 'r' ).read()
    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    return render_to_response( 'help.html', {
            'title': _( 'GridCalendar - help' ),
            'usage_text': usage_text,
            'about_text': about_text,
            }, context_instance = RequestContext( request ) )

def legal_notice( request ): # {{{1
    """Just returns the legal notice page.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('legal_notice')).status_code
    200
    """
    return render_to_response( 'legal_notice.html', {
            'title': _( 'GridCalendar - legal notice' ),
            }, context_instance = RequestContext( request ) )

def event_new( request ): # {{{1
    """ Expects a filled simplified event form and redirects to `event_edit`

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('event_new')).status_code
    302
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
                    {'title': _( "GridCalendar" ), 'form': sef},
                    context_instance = RequestContext( request ) )
    else:
        return HttpResponseRedirect( reverse( 'main' ) )

def event_edit( request, event_id ): # {{{1
    """ view to edit an event as a form

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_new'),
    ...         kwargs={'event_id': e.id,}).status_code
    302
    """
    """ Complete web-form to edit an event. """
    event = get_object_or_404( Event, pk = event_id )
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
    """ View to create an event as text.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('event_new_raw')).status_code
    200
    """
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
                _( ''.join( ["You submitted an empty form, nothing was saved. ",
                    "Click the back button in your browser and try again."] )))
    else:
        templates = { 'title': _( "edit event as text" ), \
                'example': Event.example() }
        return render_to_response( 'event_new_raw.html', templates,
                context_instance = RequestContext( request ) )

def event_edit_raw( request, event_id ): # {{{1
    """ View to edit an event as text.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_edit_raw',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    # checks if the event exists
    event = get_object_or_404( Event, pk = event_id )
    # checks if the user is allowed to edit this event
    # public events can be edited by anyone, otherwise only by the submitter
    # and the group the event belongs to
    if ( not event.public ):
        if ( not request.user.is_authenticated() ):
            return _error( request,
                _( ''.join(['You need to be logged-in to be able to edit the ',
                    'private event with the number %(event_id)d. ',
                    'Please log in a try again.'] )) % {'event_id': event_id} )
        else:
            if not Event.is_event_viewable_by_user(
                    event_id, request.user.id ):
                return _error( request,
                    _( ''.join(['You are not allowed to edit the event with ',
                        'the number %s(event_id)d'] ) ) % \
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
            if isinstance(event, Event):
                return HttpResponseRedirect( 
                    reverse( 'event_show', kwargs = {'event_id': event_id} ) )
            else:
                return _error( request, event )
        else:
            return _error( request,
                _( ''.join( ['You submitted an empty form, nothing was saved.',
                    ' Click the back button in your browser and try again.'])))
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
    """ View that shows an event

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_show',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    event = get_object_or_404( Event, pk = event_id )
    if not Event.is_event_viewable_by_user( event_id, request.user.id ):
        return _error( request,
            _( "You are not allowed to view the event with the following \
            number" ) + ": " + str( event_id ) )
    else:
        templates = {'title': _( "view event detail" ), 'event': event }
        return render_to_response( 'event_show_all.html', templates,
                context_instance = RequestContext( request ) )

def event_show_raw( request, event_id ): # {{{1
    """ View that shows an event as text

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_show_raw',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    event = get_object_or_404( Event, pk = event_id )
    if not Event.is_event_viewable_by_user( event_id, request.user.id ):
        return _error( request,
            _( "You are not allowed to view the event with the following \
                    number:" ) + " " + str( event_id ) )
    else:
        event_textarea = event.as_text()
        templates = {
                'title': _( "view as text" ),
                'event_textarea': event_textarea,
                'event': event }
        return render_to_response( 'event_show_raw.html',
                templates, context_instance = RequestContext( request ) )

def search( request ): # {{{1
    """ View to get the data of a search query calling `list_events_search`

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('search')).status_code
    200
    """
    # FIXME: replace everything using something like the first example at
    # http://www.djangobook.com/en/1.0/chapter07/
    if 'query' in request.POST and request.POST['query']:
        return list_events_search ( request, request.POST['query'] )
        # return HttpResponseRedirect( 
        #         reverse( 'list_events_search',
        #         kwargs = {'query': request.POST['query'], } ) )
    else:
        return _error( request,
            _( u"A search request was submitted without a text" ) )

def list_events_search( request, query ): # {{{1
    """ View to show the results of a search query on the left column and
    related events on the right column.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('list_events_search',
    ...         kwargs={'query': 'abc',})).status_code
    200
    """
    search_result, related_events = Filter.matches(query, request.user)
    if len( search_result ) == 0:
        return render_to_response( 'error.html',
            {
                'title': _( "GridCalendar - no search results" ),
                'messages_col1': [
                        _(u'time: %(date_time)s') % {'date_time':
                            datetime.datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S'),},
                        _(u'search: %(query)s') % {'query':
                            query.decode("string_escape"),},
                        _(u"results: %(number)d") % {'number': 0,},],
                'query': query,
                'form': get_event_form( request.user ),
            },
            context_instance = RequestContext( request ) )
    else:
        return render_to_response( 'list_events_search.html',
            {
                'title': _( "search results" ),
                'messages_col1': [
                        _(u'time: %(date_time)s') % {'date_time':
                            datetime.datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S'),},
                        _(u'search: %(query)s') % {'query':
                            query.decode("string_escape"),},
                        _(u"results: %(number)d") % {'number':
                            len( search_result ),},],
                'events': search_result,
                'related_events': related_events,
                'query': query,
                'user_id': request.user.id,
                'hash': ExtendedUser.calculate_hash(request.user.id),
            },
            context_instance = RequestContext( request ) )

def list_events_search_hashed( request, query, user_id, hash ): # {{{1
    """ View to show the results of a search query with hashed authentification

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import ExtendedUser
    >>> u = User.objects.create_user('l_e_s_h', '0@example.com', 'p')
    >>> u = ExtendedUser.objects.get( pk = u.pk )
    >>> Client().get(reverse('list_events_search_hashed',
    ...         kwargs={'query': 'abcdef', 'user_id': u.id,
    ...         'hash': u.get_hash()})).status_code
    200
    """
    if ExtendedUser.calculate_hash(user_id) != hash:
        raise Http404
    search_result = Filter.matches(query, user_id)[0]
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
    """ Saves a new filter

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> u = User.objects.create_user('filter_save', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> client.get(reverse('filter_save'),
    ...         kwargs={'q': 'abcdef',}).status_code
    200
    """
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
    """ View to edit a filter

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Filter
    >>> u = User.objects.create_user('filter_edit', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> f, c = Filter.objects.get_or_create( name="test", user = u,
    ...         query="abcdef" )
    >>> client.get(reverse('filter_edit'),
    ...         kwargs={'filter_id': f.id,}).status_code
    200
    """
    efilter = get_object_or_404( Filter, pk = filter_id )
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
    """ Delete a filter if the user is the owner 

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Filter
    >>> u = User.objects.create_user('filter_drop', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> f, c = Filter.objects.get_or_create( name="test", user = u,
    ...         query="abcdef" )
    >>> client.get(reverse('filter_drop'),
    ...         kwargs={'filter_id': f.id,}).status_code
    200
    """
    efilter = get_object_or_404( Filter, pk = filter_id )
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
    """ View that lists the filters of the logged-in user

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Filter
    >>> u = User.objects.create_user('l_f_m', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> f, c = Filter.objects.get_or_create( name="test", user = u,
    ...         query="abcdef" )
    >>> client.get(reverse('list_filters_my')).status_code
    200
    """
    list_of_filters = Filter.objects.filter( user = request.user )
    if list_of_filters is None or len( list_of_filters ) == 0:
        return _error( request,
            _( "You do not have any filters configured" ) )
    else:
        return render_to_response( 'list_filters_my.html',
            {'title': _( u'list of my filters' ), 'filters': list_of_filters},
            context_instance = RequestContext( request ) )

# not used for now because of privacy concerns:
#def list_events_of_user( request, username ): # {{{1
#    """ View that lists the events of a user
#
#    >>> from django.test import Client
#    >>> from django.core.urlresolvers import reverse
#    >>> from django.contrib.auth.models import User
#    >>> u = User.objects.create_user('l_e_o_u', '0@example.com', 'p')
#    >>> e = Event.objects.create(
#    ...         title = 'test', tags = 'berlin',
#    ...         start = datetime.date.today(), user = u )
#    >>> client = Client()
#    >>> client.login(username = u.username, password = 'p')
#    True
#    >>> client.get(reverse('list_events_of_user',
#    ...         kwargs={'username': u.username,})).status_code
#    200
#    """
#    if ( ( not request.user.is_authenticated() ) or
#            ( request.user.id is None ) ):
#        try:
#            user = User.objects.get( username__exact = username )
#            useridtmp = user.id
#            events = Event.objects.filter( user = useridtmp ) # FIXME: what is this?
#            events = Event.objects.filter( public = True )
#            if len( events ) == 0:
#                return _error( request,
#                        _( "Your search didn't get any result" ) )
#            else:
#                return render_to_response( 'events/list_user.html',
#                    {'events': events, 'username': username},
#                    context_instance = RequestContext( request ) )
#        except User.DoesNotExist:
#            return _error( request, _( "User does not exist" ) )
#    else:
#        try:
#            user = User.objects.get( username__exact = username )
#            useridtmp = user.id
#            events = Event.objects.filter( user = useridtmp )
#            if len( events ) == 0:
#                return _error(
#                        request,
#                        _( "Your search didn't get any result" ) )
#            else:
#                return render_to_response( 'events/list_user.html',
#                    {'events': events, 'username': username},
#                    context_instance = RequestContext( request ) )
#        except User.DoesNotExist:
#            return _error( request, ( "User does not exist" ) )

@login_required
def list_events_my( request ): # {{{1
    """ View that lists the events the logged-in user is the owner of
 
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> u = User.objects.create_user('l_e_m', '0@example.com', 'p')
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today(), user = u )
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> client.get(reverse('list_events_my')).status_code
    200
    """
    events = Event.objects.filter( user = request.user )
    if len( events ) == 0:
        return _error( request, _( "Your search didn't get any result" ) )
    else:
        return render_to_response( 'list_events_my.html',
            {'title': _( "list my events" ), 'events': events},
            context_instance = RequestContext( request ) )

def list_events_tag( request, tag ): # {{{1
    """ returns a view with events having a tag
 
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('list_events_tag',
    ...         kwargs={'tag': 'berlin',})).status_code
    200
    >>> Client().get(reverse('list_events_tag',
    ...         kwargs={'tag': 'abcdef',})).status_code
    404
    """
    query_tag = get_object_or_404( Tag, name = tag )
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
    return render_to_response( 'settings.html',
            {
                'title': _( "%(username)s settings" ) % {'username':
                    request.user.username,},
            },
            context_instance = RequestContext( request ) )

# groups views {{{1

@login_required
def group_new(request): # {{{2
    """ View to create a new group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> u = User.objects.create_user('group_new', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> Client().get(reverse('group_new'))
    200
    """
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
    """ view that lists all groups of the logged-in user

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> u = User.objects.create_user('list_group_my', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> Client().get(reverse('list_groups_my'))
    200
    """
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
    user is the last member of the group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership
    >>> u1 = User.objects.create_user('group_quit_1', '0@example.com', 'p')
    >>> u2 = User.objects.create_user('group_quit_2', '0@example.com', 'p')
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m = Membership.objects.create(user = u1, group = g)
    >>> m = Membership.objects.create(user = u2, group = g)
    >>> client = Client()
    >>> client.login(username = u1.username, password = 'p')
    True
    >>> Client().get(reverse('group_quit',
    ...         kwargs={'group_id': g.id, 'sure': True})).status_code
    200
    """
    user = User(request.user)
    group = get_object_or_404( Group, id=group_id, membership__user=user )
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
    """ view to confirm of quiting a group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership
    >>> u1 = User.objects.create_user('group_quit_a_1', '0@example.com', 'p')
    >>> u2 = User.objects.create_user('group_quit_a_2', '0@example.com', 'p')
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m = Membership.objects.create(user = u1, group = g)
    >>> m = Membership.objects.create(user = u2, group = g)
    >>> client = Client()
    >>> client.login(username = u1.username, password = 'p')
    True
    >>> Client().get(reverse('group_quit_ask',
    ...         kwargs={'group_id': g.id,})).status_code
    200
    """
    return group_quit(request, group_id, False)

@login_required
def group_quit_sure(request, group_id):
    """ view to confirm of quiting a group being sure

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership
    >>> u1 = User.objects.create_user('group_quit_s_1', '0@example.com', 'p')
    >>> u2 = User.objects.create_user('group_quit_s_2', '0@example.com', 'p')
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m = Membership.objects.create(user = u1, group = g)
    >>> m = Membership.objects.create(user = u2, group = g)
    >>> client = Client()
    >>> client.login(username = u1.username, password = 'p')
    True
    >>> client.get(reverse('group_quit_ask',
    ...         kwargs={'group_id': g.id,})).status_code
    200
    """
    return group_quit(request, group_id, True)

@login_required
def group_add_event(request, event_id): # {{{2
    """ view to add an event to a group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership, Calendar
    >>> u = User.objects.create_user('group_add_event', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m = Membership.objects.create(user = u, group = g)
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today(), user = u )
    >>> m = Calendar.objects.create(user = u, event = e)
    >>> client().get(reverse('group_add_event',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {
                    'title': 'GridCalendar - error',
                    'messages_col1': [_(''.join_("You must be logged in to ",
                        "add an event to a group")),]
                },
                context_instance=RequestContext(request))
    event = get_object_or_404( Event, id = event_id )
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
                        'messages_col1': [_(''.join( ["This event is already ",
                            "in all groups that you are in, so you can't ",
                            "add it to any more groups."] )),]
                    },
                    context_instance=RequestContext(request))

def group_view(request, group_id): # {{{2
    """ lists everything about a group for members of the group, and the
    description and public events for everyone else

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership, Calendar
    >>> u1g = User.objects.create_user('groupview1', '0@example.com', 'p')
    >>> u2 = User.objects.create_user('groupview2', '0@example.com', 'p')
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m, c = Membership.objects.get_or_create(user = u1g, group = g)
    >>> public_e = Event.objects.create(
    ...         title = 'public group view', tags = 'group-view',
    ...         start = datetime.date.today(), user = u1g )
    >>> private_e = Event.objects.create( public = False,
    ...         title = 'private group view', tags = 'group-view',
    ...         start = datetime.date.today(), user = u1g )
    >>> m, c = Calendar.objects.get_or_create(group = g, event = public_e)
    >>> m, c = Calendar.objects.get_or_create(group = g, event = private_e)
    >>> client = Client()
    >>> response = client.get(reverse('group_view',
    ...         kwargs={'group_id': g.id,}))
    >>> response.status_code
    200
    >>> 'public group view' in response.content
    True
    >>> 'private group view' in response.content
    False
    >>> client.login(username = u2.username, password = 'p')
    True
    >>> response = client.get(reverse('group_view',
    ...         kwargs={'group_id': g.id,}))
    >>> response.status_code
    200
    >>> 'public group view' in response.content
    True
    >>> 'private group view' in response.content
    False
    >>> client.login(username = u1g.username, password = 'p')
    True
    >>> response = client.get(reverse('group_view',
    ...         kwargs={'group_id': g.id,}))
    >>> response.status_code
    200
    >>> 'public group view' in response.content
    True
    >>> 'private group view' in response.content
    True
    """
    group = get_object_or_404( Group, id = group_id )
    if ( request.user.is_authenticated() and 
                    Group.is_user_in_group(request.user, group) ):
        events = group.get_coming_events( limit = -1 )
    else:
        events = group.get_coming_public_events( limit = -1 )
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
                'events': events,
            },
            context_instance=RequestContext(request))

@login_required
def group_invite(request, group_id): # {{{2
    """ view to invite a user to a group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership, Calendar
    >>> u = User.objects.create_user('group_invite', '0@example.com', 'p')
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m, c = Membership.objects.get_or_create(user = u, group = g)
    >>> client().get(reverse('group_invite',
    ...         kwargs={'group_id': g.id,})).status_code
    200
    """
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {
                    'title': 'error',
                    'messages_col1': [_(''.join(["You must be logged in to ",
                        "invite someone to a group"])),]
                },
                context_instance=RequestContext(request))
    else:
        group = get_object_or_404(Group, id = group_id )
        if request.POST:
            username_dirty = request.POST['username']
            formdata = {'username': username_dirty,
                        'group_id': group_id}
            form = InviteToGroupForm(data=formdata)
            if form.is_valid():
                username = form.cleaned_data['username']
                user = get_object_or_404( User, username = username )
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
    # FIXME: create test (see source code for user-sign-up code
    invitation = GroupInvitation.objects.get(activation_key=activation_key)
    group_id = invitation.id
    group = get_object_or_404(Group, id = group_id )
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
    """ ical file for a search
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('list_events_search_ical',
    ...         kwargs={'query': 'berlin',})).status_code
    200
    """
    elist = Filter.matches( query, request.user )[0]
    return _ical_http_response_from_event_list( elist, query )

def ICalForEvent( request, event_id ): # {{{2
    """ ical file for an event
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_show_ical',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    event = get_object_or_404( Event, id = event_id )
    elist = [event,]
    elist = [eve for eve in elist if eve.is_viewable_by_user(request.user)]
    return _ical_http_response_from_event_list( elist, event.title )

def ICalForEventHash (request, event_id, user_id, hash): # {{{2
    """ 
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import ExtendedUser
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> u = User.objects.create_user('ICalForEventHash', '0@example.com', 'p')
    >>> u = ExtendedUser.objects.get( pk = u.pk )
    >>> Client().get(reverse('event_show_ical_hash',
    ...         kwargs={'event_id': e.id, 'user_id': u.id,
    ...         'hash': u.get_hash()})).status_code
    200
    """
    user = get_object_or_404( ExtendedUser, id = user_id )
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [_(u"hash authentification failed"),]
            },
            context_instance=RequestContext(request))
    event = get_object_or_404(Event, id = event_id )
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
    """ ical file for the result of a search with hash authentification

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import ExtendedUser
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> u = User.objects.create_user('ICalForSearchHash', '0@example.com', 'p')
    >>> u = ExtendedUser.objects.get( pk = u.pk )
    >>> Client().get(reverse('list_events_search_ical_hashed',
    ...         kwargs={'query': 'berlin', 'user_id': u.id,
    ...         'hash': u.get_hash()})).status_code
    200
    """
    user = get_object_or_404( ExtendedUser, id = user_id )
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [_(u"hash authentification failed"),]
            },
            context_instance=RequestContext(request))
    elist = Filter.matches( query, user_id )[0]
    return _ical_http_response_from_event_list( elist, query )

def ICalForGroup( request, group_id ): # {{{2
    """ return all public events with a date in the future in icalendar format
    belonging to a group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Event
    >>> from gridcalendar.events.models import Group, Membership, Calendar
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> u = User.objects.create_user('ICalForGroup', '0@example.com', 'p')
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m, c = Membership.objects.get_or_create(user = u, group = g)
    >>> ca, c = Calendar.objects.get_or_create(group = g, event = e)
    >>> client = Client()
    >>> client.login( username = u.username, password = 'p' )
    True
    >>> client.get(reverse('list_events_group_ical',
    ...         kwargs={'group_id': g.id,})).status_code
    200
    """
    group = get_object_or_404(Group, pk = group_id)
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
    belonging to a group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import ExtendedUser
    >>> from gridcalendar.events.models import Event
    >>> from gridcalendar.events.models import Group, Membership, Calendar
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> u = User.objects.create_user('ICalForGroupHash', '0@example.com', 'p')
    >>> u = ExtendedUser.objects.get( pk = u.pk )
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m = Membership.objects.get_or_create(user = u, group = g)
    >>> c = Calendar.objects.get_or_create(group = g, event = e)
    >>> Client().get(reverse('list_events_group_ical_hashed',
    ...         kwargs={'group_id': g.id, 'user_id': u.id,
    ...         'hash': u.get_hash()})).status_code
    200
    """
    user = get_object_or_404( ExtendedUser, id = user_id )
    if hash != user.get_hash():
        return render_to_response('error.html',
            {'title': 'error',
            'messages_col1': [_(u"hash authentification failed"),]
            },
            context_instance=RequestContext(request))
    group = get_object_or_404( Group, id = group_id )
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

def all_events_text ( request ):
    """ returns a text file with all events which the logged-in user can see,
    only public events if there is no logged-in user
    
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('all_events_text')).status_code
    200
    """
    if request.user.is_authenticated():
        user = request.user
        elist = Event.objects.filter(
                Q( user = user ) | Q( group__membership__user = user ) |
                Q( public = True ) )
    else:
        elist = Event.objects.filter( public = True )
    text = Event.list_as_text( elist )
    response = HttpResponse( text, mimetype = 'text/text;charset=UTF-8' )
    filename =  PROJECT_NAME + '_' + datetime.datetime.now().isoformat()+'.txt'
    response['Filename'] = filename
    response['Content-Disposition'] = 'attachment; filename=' + filename
    return response
