#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker ft=python
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
import re
import vobject
import unicodedata
from difflib import HtmlDiff, unified_diff

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site
from django.core import serializers
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import Max, Q
from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory, ModelForm
from django.http import ( HttpResponseRedirect, HttpResponse, Http404,
        HttpResponseForbidden, HttpResponseBadRequest )
from django.shortcuts import ( render_to_response, get_object_or_404,
        get_list_or_404 )
from django.template import RequestContext, Context, loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from tagging.models import Tag, TaggedItem
from reversion import revision
from reversion.models import Version

from gridcalendar.events.forms import ( 
    SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, FilterForm,
     NewGroupForm, InviteToGroupForm, AddEventToGroupForm, )
from gridcalendar.events.models import ( 
    Event, EventUrl, EventSession, EventDeadline, Filter, Group,
    Membership, GroupInvitation, ExtendedUser, Calendar, RevisionDiff )
from gridcalendar.events.utils import search_address
from gridcalendar.events.tables import EventTable

# TODO: check if this works with i18n
views = [_('table'), _('map'), _('boxes')]

def help_page( request ): # {{{1
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
            'title': Site.objects.get_current().name + " - " + _( 'help' ),
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
            'title': Site.objects.get_current().name + \
                    ' - ' + _( 'legal notice' ),
            }, context_instance = RequestContext( request ) )

def event_edit( request, event_id = None ): # {{{1
    """ view to edit or create an event as a form

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'ee_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_edit',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    >>> Client().get(reverse('event_new')).status_code
    200
    """
    # FIXME: create more tests above for e.g. trying to save a new event
    # without a URL
    if event_id and isinstance( event_id, int ):
        event_id = unicode( event_id )
    if event_id:
        event = get_object_or_404( Event, pk = event_id )
        can_delete = True
        old_as_text = event.as_text().splitlines()
    else:
        event = Event()
        can_delete = False
        old_as_text = None
    event_urls_factory = inlineformset_factory( 
            Event, EventUrl, extra = 4, can_delete = can_delete, )
    event_deadlines_factory = inlineformset_factory( 
            Event, EventDeadline, extra = 4, can_delete = can_delete, )
    event_sessions_factory = inlineformset_factory( 
            Event, EventSession, extra = 4, can_delete = can_delete, )
    if request.method == 'POST':
        event_form = EventForm( request.POST, instance = event )
        formset_url = event_urls_factory(
                request.POST, instance = event )
        formset_deadline = event_deadlines_factory(
                request.POST, instance = event )
        formset_session = event_sessions_factory(
                request.POST, instance = event )
        if event_form.is_valid():
            event = event_form.save(commit = False) # ! not saved in DB yet
            if formset_url.is_valid() & \
                    formset_session.is_valid() & formset_deadline.is_valid() :
                # FIXME: don't allow to save an event with missing basic data
                # like a URL
                event.save()
                formset_url.save()
                formset_session.save()
                formset_deadline.save()
                # we save diffs in revision if appropiate. See
                # https://github.com/etianen/django-reversion/wiki/Low-Level-API
                if old_as_text:
                    new_as_text = event.as_text().splitlines()
                    html_diff = HtmlDiff( tabsize = 4 ).make_table(
                            old_as_text, new_as_text )
                    text_diff = unified_diff(
                            old_as_text, new_as_text, n = 0, lineterm = "" )
                    # we now delete from the text diff all control lines TODO:
                    # when the description field of an event contains such
                    # lines, they will be deleted: avoid it.
                    text_diff = [line for line in text_diff if not
                            re.match(r"^---\s*$", line) and not
                            re.match(r"^\+\+\+\s*$", line) and not
                            re.match(r"^@@.*@@$", line)]
                    text_diff = '\n'.join( text_diff )
                    revision.add_meta( RevisionDiff,
                            html_diff = html_diff, text_diff = text_diff )
                return HttpResponseRedirect( 
                        reverse('event_show', kwargs = {'event_id': event.id}))
    else:
        event_form = EventForm( instance = event )
        formset_url = event_urls_factory( instance = event )
        formset_deadline = event_deadlines_factory( instance = event )
        formset_session = event_sessions_factory( instance = event )
    templates = {
            'title': 'edit event',
            'form': event_form,
            'formset_url': formset_url,
            'formset_session': formset_session,
            'formset_deadline': formset_deadline,
            'event_id': event_id }
    # add a warning message if the start date is in the past, which is probably
    # a mistake
    if event_id and event.start < datetime.date.today():
        templates['messages'] = [ _('warning: the start date is in the past') ]
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
                event = Event.parse_text(event_textarea, None, request.user.id)
                # TODO: inform that the event was saved
                return HttpResponseRedirect( 
                        reverse( 'event_show', kwargs={'event_id': event.id} ))
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
                        'error_messages': error_messages,
                        'event_textarea': event_textarea, }
                return render_to_response(
                        'event_new_raw.html',
                        templates,
                        context_instance = RequestContext( request ) )
        else:
            return main( request, error_messages =
                _( ''.join( ["You submitted an empty form, nothing was saved. ",
                "Click the back button in your browser and try again."])) )
    else:
        templates = { 'title': _( "edit event as text" ), }
        return render_to_response( 'event_new_raw.html', templates,
                context_instance = RequestContext( request ) )

def event_edit_raw( request, event_id ): # {{{1
    """ View to edit an event as text.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'eer_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_edit_raw',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    if isinstance( event_id, str ) or isinstance( event_id, unicode ):
        event_id = int( event_id )
    # checks if the event exists
    event = get_object_or_404( Event, pk = event_id )
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
                        if isinstance(error_message, list):
                            error_message = " ; ".join(error_message)
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
                        'error_messages': error_messages,
                        'example': Event.example() }
                return render_to_response( 'event_edit_raw.html', templates,
                        context_instance = RequestContext( request ) )
            if isinstance(event, Event):
                return HttpResponseRedirect( 
                    reverse( 'event_show', kwargs = {'event_id': event_id} ) )
            else:
                return main( request, error_messages = event )
        else:
            return main( request, error_messages = 
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
    ...         title = 'es_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_show',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    if isinstance(event_id, str) or isinstance(event_id, unicode):
        event_id = int(event_id)
    # TODO: use here and in other places:
    #   Event.objects.select_related( depth = 2 ).get(pk = event_id)
    #   See # http://docs.djangoproject.com/en/1.3/ref/models/querysets/#select-related
    #   This will increase performance and allow for custom error messages
    #   instead of a general 404
    event = get_object_or_404( Event, pk = event_id )
    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    title = unicode(event.upcoming)
    if event.city:
        title += " " + event.city
    if event.country:
        title += " (" + event.country + ")"
    title += " - " + event.title + " | " + Site.objects.get_current().name
    templates = {
            'title': title,
            'event': event,
            'about_text': about_text,
            }
    return render_to_response( 'event_show_all.html', templates,
            context_instance = RequestContext( request ) )

def event_show_raw( request, event_id ): # {{{1
    """ View that shows an event as text

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'esr_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_show_raw',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    event = get_object_or_404( Event, pk = event_id )
    event_textarea = event.as_text()
    templates = {
            'title': _( "view as text" ),
            'event_textarea': event_textarea,
            'event': event }
    return render_to_response( 'event_show_raw.html',
            templates, context_instance = RequestContext( request ) )

def event_history( request, event_id ): # {{{1
    """ show the history of an event """
    # TODO: tests including one that checks that a revision has only one
    # element in its revisiondiff_set
    event = get_object_or_404( Event, pk = event_id )
    revisions = [ version.revision for version in
            Version.objects.get_for_object( event ) ]
    revisions.reverse()
    templates = {
            'title': _( "History of event %(event_nr)s" ) % \
                    {'event_nr': str(event.id)},
            'event': event,
            'revisions': revisions }
    return render_to_response( 'event_history.html',
            templates, context_instance = RequestContext( request ) )

def search( request, query = None, view = 'boxes' ): # {{{1
    """ View to get the data of a search query.

    Notice that ``query`` and ``view`` can be a GET value in ``request``, or a
    parameter value, which can be passed in the URL. GET value has preference.

    ``request`` can also have a ``limit`` value, which if present limits the
    number of events returned. If ``limit`` is not present, or it is not a
    valid positive integer, some defaults are used for each kind of view.

    ``request`` can also have a ``related`` value, which activates or
    deactivates the inclusion of related events. Notice that some search
    options like '@' (for places) produces no related events. If the value
    cannot be converted to Boolean, or it is not present, we fall back to True.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> e1 = Event.objects.create(
    ...         title = 's1_test', tags = 'berlin',
    ...         start = datetime.date.today())
    >>> e2 = Event.objects.create(
    ...         title = 's2_test', tags = 'berlin',
    ...         start = datetime.date.today())
    >>> Client().get(reverse('search_query',
    ...         kwargs={'query': 'test',})).status_code
    200
    >>> Client().get(reverse('search_query_view',
    ...         kwargs={'query': 'test', 'view': 'table'})).status_code
    200
    >>> Client().get(reverse('search_query_view',
    ...         kwargs={'query': 'test', 'view': 'map'})).status_code
    200
    """
    # query
    if 'query' in request.GET and request.GET['query']:
        query = request.GET['query']
        if query.find('/') != -1:
            return main( request, error_messages = 
                _( u"A search with the character '/' was submitted, but it " \
                        "is not allowed" ) )
            # the character / cannot be allowed because Django won't be able to
            # create a URL for the ical result of the search. For a discussion,
            # see http://stackoverflow.com/questions/3040659/how-can-i-receive-percent-encoded-slashes-with-django-on-app-engine
    # view
    if 'view' in request.GET and request.GET['view']:
        view = request.GET['view']
    # shows the homepage with a message if no query, except when view=json
    # because client expect json
    if (not query) and (view != 'json'):
        return main( request, error_messages = 
            _( u"A search was submitted without a query string" ) )
    # limit
    if 'limit' in request.GET and request.GET['limit']:
        try:
            limit = int( request.GET['limit'] )
            if limit <= 0:
                limit = None
        except ValueError:
            limit = None
    else:
        limit = None
    # related
    try:
        related = bool(request.GET.get('related', True))
    except ValueError:
        related = True
    # search
    # TODO: limit the number of search results. Think of malicious users
    # getting millions of events from the past
    search_result = Filter.matches(query, request.user, related)
    if limit:
        search_result = search_result[0:limit]
    # views
    if view != 'json':
        # variables to be passed to the templates
        context = dict()
        context['views'] = views
        context['current_view'] = view
        context['title'] = \
            _( "%(project_name)s - %(view)s search results for: %(query)s" ) \
                % { 'project_name': Site.objects.get_current().name,
                    'query': query,
                    'view': view }
        context['user_id'] = request.user.id
        context['query'] = query
        if len( search_result ) == 0:
            context['no_results'] = True
            context['heading'] = _( u"Search for: %(query)s" ) % \
                    {'query': query}
        elif len( search_result ) == 1:
            context['heading'] = \
                    _("One event found searching for: %(query)s") \
                    % { 'query': query, }
        else:
            context['heading'] = \
                    _("%(number)d events found searching for: %(query)s") \
                        % { 'number': len ( search_result ), 'query': query }
    if view == 'boxes' or view == 'map':
        if view == 'map':
            # map-view works only with maximum 10 events
            paginator = Paginator( search_result, 10)
        else:
            paginator = Paginator( search_result, 100)
        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        # If page request (9999) is out of range, deliver last page of results.
        try:
            context['events'] = paginator.page( page )
        except ( EmptyPage, InvalidPage ):
            context['events'] = paginator.page( paginator.num_pages )
    elif view == 'table':
        sort = request.GET.get( 'sort', 'upcoming' )
        page = int( request.GET.get( 'page', '1' ) )
        search_result = EventTable.convert( search_result )
        search_result_table = EventTable( search_result, order_by = sort )
        if settings.DEBUG:
            search_result_table.paginate(
                    Paginator, 10, page = page, orphans = 2 )
        else:
            search_result_table.paginate(
                    Paginator, 50, page = page, orphans = 2 )
        context['events_table'] = search_result_table
        context['sort'] = sort
    elif view == 'json':
        if 'jsonp' in request.GET and request.GET['jsonp']:
            jsonp = request.GET['jsonp']
        else:
            jsonp = None
        data = serializers.serialize(
                'json',
                search_result,
                fields=('title', 'upcoming', 'start', 'tags', 'coordinates'),
                indent = 2,
                ensure_ascii=False )
        if jsonp:
            data = jsonp + '(' + data + ')'
            mimetype = "application/javascript"
        else:
            mimetype = "application/json"
        return HttpResponse( mimetype = mimetype, content = data )
    elif view in ('yaml', 'xml'):
        data = serializers.serialize(
                view,
                search_result,
                indent = 2,
                fields=('title', 'upcoming', 'start', 'tags', 'coordinates') )
        if view == 'xml':
            mimetype = "application/xml"
        else:
            mimetype = "application/x-yaml"
        return HttpResponse( mimetype = mimetype, content = data )
    else:
        raise Http404
    return render_to_response( 'search.html',
            context,
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
        return main( request, error_messages = 
            _( u"You are trying to save a search without any query text" ) )
    if request.method == 'POST':
        maximum = Filter.objects.filter(user = request.user).count() + 1
        efilter = Filter()
        efilter.user = request.user
        efilter.query = query_lowercase
        efilter.name = _( u"%(username)s's filter %(number)s" ) % \
                {'username':request.user.username, 'number': str(maximum)}
        # the above code has the problem that the name might already been
        # used by the same user. We check it:
        taken = Filter.objects.filter(
                user = request.user, name = efilter.name ).count()
        while taken:
            efilter.name += "'"
            taken = Filter.objects.filter(
                    user = request.user, name = efilter.name ).count()
        efilter.save()
        return HttpResponseRedirect( reverse(
            'filter_edit', kwargs = {'filter_id': efilter.id} ) )
    elif request.method == 'GET':
        return main( request, error_messages =
                _( ''.join(['You have submitted a GET request which is not ',
                'a valid method for saving a filter']) ))

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
    >>> client.get(reverse('filter_edit',
    ...         kwargs={'filter_id': f.id,})).status_code
    200
    """
    if isinstance( filter_id, str ) or isinstance ( filter_id, unicode ):
        filter_id = int ( filter_id )
    efilter = get_object_or_404( Filter, pk = filter_id )
    if efilter.user.id != request.user.id:
        return main( request, error_messages =
                _( ''.join(['You are not allowed to edit the filter with the ',
                    'number %(filter_id)d']) ) % {'filter_id': filter_id,} )
    if request.method == 'POST':
        ssf = FilterForm( request.POST, instance = efilter )
        if ssf.is_valid():
            assert request.user.id == ssf.cleaned_data['user'].id
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
                'title': 'edit filter',
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
    >>> client.get( reverse ( 'filter_drop',
    ...         kwargs={'filter_id': f.id,} ) ).status_code
    302
    """
    if isinstance( filter_id, str ) or isinstance ( filter_id, unicode ):
        filter_id = int (filter_id )
    efilter = get_object_or_404( Filter, pk = filter_id )
    if ( ( not request.user.is_authenticated() ) or \
            ( efilter.user.id != request.user.id ) ):
        return main( request, error_messages =
                _(''.join(['You are not allowed to delete the filter with the ',
                    'number %(filter_id)d']) ) % {'filter_id': filter_id,} )
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
        return main( request, error_messages = 
            _( "You do not have any filters" ) )
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
#    ...         title = 'lefu_test', tags = 'berlin',
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
    ...         title = 'lem_test', tags = 'berlin',
    ...         start = datetime.date.today(), user = u )
    >>> client = Client()
    >>> client.login(username = u.username, password = 'p')
    True
    >>> client.get(reverse('list_events_my')).status_code
    200
    """
    events = get_list_or_404( Event, user = request.user )
    return render_to_response( 'list_events_my.html',
            {'title': _( "my events" ), 'events': events},
            context_instance = RequestContext( request ) )

def list_events_tag( request, tag ): # {{{1
    """ returns a view with events having a tag
 
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> e = Event.objects.create(
    ...         title = 'let_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('list_events_tag',
    ...         kwargs={'tag': 'berlin',})).status_code
    200
    >>> Client().get(reverse('list_events_tag',
    ...         kwargs={'tag': 'list-events-tag',})).status_code
    404
    """
    query_tag = get_object_or_404( Tag, name = tag )
    events = TaggedItem.objects.get_by_model( Event, query_tag )
    events = events.order_by( '-start' ) # FIXME: order by next_date
    return render_to_response( 'list_events_tag.html',
            {
                'title': _( "list by tag" ),
                'events': events,
                'tag': tag
            },
            context_instance = RequestContext( request ) )

def list_events_location( request, location ): # {{{1
    """ returns a view with events having a location
 
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> e = Event.objects.create(
    ...         title = 'lel_test', tags = 'test',
    ...         city = 'Berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('list_events_location',
    ...         kwargs={'location': 'berlin',})).status_code
    200
    >>> Client().get(reverse('list_events_location',
    ...         kwargs={'location': 'list-events-location',})).status_code
    200
    """
    # FIXME: create a function in the manager of events to return events by
    # location and change the code everywhere using Event.objects.location()
    return search( request, query = '@'+location, view = 'table' )

def main( request, messages=None, error_messages=None, status_code=200 ):# {{{1
    """ main view
    
    >>> from django.test import Client
    >>> c = Client()
    >>> r = c.get('/')
    >>> r.status_code # /
    200
    """
    # convert messages to a list if necessary
    if messages and not hasattr(messages,'__iter__'):
        messages = [messages,]
    # convert error_messages to a list if necessary
    if error_messages and not hasattr(error_messages,'__iter__'):
        error_messages = [error_messages,]
    # processes the event form
    if request.method == 'POST':
        if request.user.is_authenticated():
            event_form = SimplifiedEventForm( request.POST )
        else:
            event_form = SimplifiedEventFormAnonymous( request.POST )
        if event_form.is_valid():
            cleaned_data = event_form.cleaned_data
            # create a new entry and saves the data
            event = Event( user_id = request.user.id,
                      title = cleaned_data['title'],
                      start = cleaned_data['when']['start_date'],
                      tags = cleaned_data['tags'], )
            # TODO simplified with for set_something(Event, ..., ...)
            if cleaned_data['when'].has_key('end_date'):
                event.end = cleaned_data['when']['end_date']
            if cleaned_data['when'].has_key('start_time'):
                event.starttime = cleaned_data['when']['start_time']
            if cleaned_data['when'].has_key('end_time'):
                event.endtime = cleaned_data['when']['end_time']
            addresses = search_address( cleaned_data['where'] )
            # TODO simplified with for set_something(Event, ..., ...)
            if addresses and len( addresses ) == 1:
                address = addresses.values()[0]
                event.address = addresses.keys()[0]
                if address.has_key( 'longitude' ) and \
                        address.has_key( 'latitude' ):
                    event.coordinates = Point(
                            float( address['longitude'] ),
                            float( address['latitude'] ) )
                if address.has_key( 'country' ):
                    event.country = address['country']
                if address.has_key( 'postcode' ):
                    event.postcode = address['postcode']
                if address.has_key( 'city' ):
                    event.city = address['city']
            else:
                #FIXME: deal with more than one address or none
                event.address = cleaned_data['where']
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
    # calculates events to show
    today = datetime.date.today()
    elist = Event.objects.filter( upcoming__gte = today )
    # TODO: a lot of queries are issued for getting the tags of each event. Can
    # it be optimized?
    elist = elist[0:settings.MAX_EVENTS_ON_ROOT_PAGE]
    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    # Generate the response with a custom status code. Rationale: our custom
    # handler404 and 500 returns the main page with a custom error message and
    # we want to return the proper html status code
    template = loader.get_template('base_main.html')
    context = RequestContext( request, dict =
            {
                'title': Site.objects.get_current().name,
                'form': event_form,
                'events': elist,
                'about_text': about_text,
                'messages': messages,
                'error_messages': error_messages,
            } )
    return HttpResponse(
            content = template.render( context ),
            mimetype="text/html",
            status = status_code )
    # Before the custom status code it was:
    # return render_to_response( 'base_main.html',
    #        {
    #            'title': Site.objects.get_current().name,
    #            'form': event_form,
    #            'events': elist,
    #            'about_text': about_text,
    #            'messages': messages,
    #            'error_messages': error_messages,
    #        },
    #        context_instance = RequestContext( request ) )

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
    >>> Client().get(reverse('group_new')).status_code
    302
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
    >>> Client().get(reverse('list_groups_my')).status_code
    302
    """
    # TODO: test also if the user has group(s)
    user = User(request.user)
    groups = Group.objects.filter(membership__user=user)
    if len(groups) == 0:
        return main( request, error_messages = 
            _("You are not a member of any group") )
    else:
        return render_to_response('groups/list_my.html',
            {'title': 'list my groups', 'groups': groups},
            context_instance=RequestContext(request))

@login_required
def group_quit(request, group_id, sure = False ): # {{{2
    """ remove the logged-in user from a group asking for confirmation if the
    user is the last member of the group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership
    >>> u1 = User.objects.create_user('group_quit_1', '0@example.com', 'p')
    >>> u2 = User.objects.create_user('group_quit_2', '0@example.com', 'p')
    >>> g = Group.objects.create(name = 'group_quit')
    >>> m = Membership.objects.create(user = u1, group = g)
    >>> m = Membership.objects.create(user = u2, group = g)
    >>> Membership.objects.filter(group = g).count()
    2
    >>> client = Client()
    >>> client.login(username = u1.username, password = 'p')
    True
    >>> client.get(reverse('group_quit',
    ...         kwargs={'group_id': g.id,})).status_code
    302
    >>> Membership.objects.filter(group = g).count()
    1
    """
    # TODO: add a test for the case when the user is the last one.
    user = User(request.user)
    group = get_object_or_404( Group, id = group_id, membership__user = user )
    other_members = Membership.objects.filter( group = group).exclude(
            user = user ).count()
    if ( other_members > 0 ):
        membership = Membership.objects.get(user = request.user, group =group)
        membership.delete()
        # TODO: show a message saying that the the user is no longer member of
        # the group. Inform other members (or alternatively show a message in
        # the groups page)
        return HttpResponseRedirect(reverse('list_groups_my'))
    elif (sure):
        membership = Membership.objects.get(user = request.user, group = group)
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
    ...         title = 'gae_test', tags = 'berlin',
    ...         start = datetime.date.today(), user = u )
    >>> m = Calendar.objects.create(group = g, event = e)
    >>> client.get(reverse('group_add_event',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    if isinstance(event_id, str) or isinstance(event_id, unicode):
        event_id = int(event_id)
    event = get_object_or_404( Event, id = event_id )
    user = request.user
    if len(Group.groups_for_add_event(user, event)) > 0:
        if request.POST:
            form = AddEventToGroupForm(
                    data=request.POST, user=user, event=event)
            if form.is_valid():
                # TODO: if event is part of a serie, ask to copy all
                # events in the serie
                for group in form.cleaned_data['grouplist']:
                    calentry = Calendar(event = event, group=group)
                    calentry.save()
                return HttpResponseRedirect(reverse('list_groups_my'))
            else:
                request.user.message_set.create(
                        message='Please check your data.')
        else:
            form = AddEventToGroupForm(user=user, event=event)
        context = dict()
        context['form'] = form
        context['event'] = event
        return render_to_response('groups/add_event_to_group.html',
                context_instance=RequestContext(request, context))
    else:
        return main(request, messages = 
                _(''.join( ['The event %(event_id)d is already in all the ',
                    'groups that you are in'] )) % {'event_id': event_id,} )

def group_name_view(request, group_name): # {{{2
    """ lists everything about a group for members of the group, or the
    description and events for everyone else. """
    group = get_object_or_404(Group, name__iexact = group_name)
    return group_view( request, group.id )

def group_view(request, group_id): # {{{2
    """ lists everything about a group for members of the group, and the
    description and events for everyone else

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Group, Membership, Calendar
    >>> u1g = User.objects.create_user('groupview1', '0@example.com', 'p')
    >>> g, c = Group.objects.get_or_create(name = 'test')
    >>> m, c = Membership.objects.get_or_create(user = u1g, group = g)
    >>> e = Event.objects.create(
    ...         title = 'event in group', tags = 'group-view',
    ...         start = datetime.date.today(), user = u1g )
    >>> m, c = Calendar.objects.get_or_create(group = g, event = e)
    >>> client = Client()
    >>> response = client.get(reverse('group_view',
    ...         kwargs={'group_id': g.id,}))
    >>> response.status_code
    200
    >>> 'event in group' in response.content
    True
    """
    group = get_object_or_404( Group, id = group_id )
    if ( request.user.is_authenticated() and 
                    Group.is_user_in_group(request.user, group) ):
        events = group.get_coming_events( limit = -1 )
    else:
        events = group.get_coming_events( limit = -1 )
    return render_to_response(
            'groups/group_view.html',
            {
                'title': _( u'%(project_name)s - group %(group_name)s' ) % \
                        {
                            'group_name': group.name,
                            'project_name': Site.objects.get_current().name,
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
    >>> client.get(reverse('group_invite',
    ...         kwargs={'group_id': g.id,})).status_code
    200
    """
    group = get_object_or_404(Group, id = group_id )
    if not Membership.objects.filter(
            user = request.user, group = group).exists():
        return main( request, error_messages =
            _( ''.join(["Your have tried to add a member to the group ",
        "'%(group_name)s', but you are yourself not a member of it"]) ) % \
        {'group_name': group.name,} )
    if request.POST:
        username_dirty = request.POST['username']
        # TODO think of malicious manipulations of these fields:
        formdata = {'username': username_dirty,
                    'group_id': group_id}
        form = InviteToGroupForm(data=formdata)
        if form.is_valid():
            guest = get_object_or_404(
                    User, username = form.cleaned_data['username'] )
            GroupInvitation.objects.create_invitation( host = request.user,
                    guest = guest, group = group , as_administrator = True )
            return HttpResponseRedirect(reverse('list_groups_my'))
    else:
        form = InviteToGroupForm()
    return render_to_response('groups/invite.html',
            {
                'title': 'invite to group',
                'group_id': group_id,
                'form': form,
            },
            context_instance=RequestContext(request))

def group_invite_activate(request, activation_key): # {{{2
    """ A user clicks on activation link """
    # FIXME: create test (see source code for user-sign-up code
    invitation = get_object_or_404(
            GroupInvitation, activation_key=activation_key )
    activation = GroupInvitation.objects.activate_invitation( activation_key )
    group = get_object_or_404(Group, id = invitation.group.id )
    if activation:
        return render_to_response('groups/invitation_activate.html',
                {'title': _(u'invitation activated'), 'group': group},
                context_instance=RequestContext(request))
    else:
        return render_to_response('groups/invitation_activate_failed.html',
                {'title': 'activate invitation failed', 'group': group},
                context_instance=RequestContext(request))

# ical views {{{1
def ICalForSearch( request, query ): # {{{2
    """ ical file for a search
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'icfs_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('search_ical',
    ...         kwargs={'query': 'berlin',})).status_code
    200
    """
    elist = Filter.matches( query, request.user )
    return _ical_http_response_from_event_list( elist, query )

def ICalForEvent( request, event_id ): # {{{2
    """ ical file for an event
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'icfe_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_show_ical',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    """
    event = get_object_or_404( Event, id = event_id )
    elist = [event,]
    return _ical_http_response_from_event_list( elist, event.title )

def ICalForGroup( request, group_id ): # {{{2
    """ return all events with a date in the future in icalendar format
    belonging to a group

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from django.contrib.auth.models import User
    >>> from gridcalendar.events.models import Event
    >>> from gridcalendar.events.models import Group, Membership, Calendar
    >>> e = Event.objects.create(
    ...         title = 'icfg_test', tags = 'berlin',
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
    elist = Event.objects.filter( calendar__group = group )
    today = datetime.date.today()
    elist = elist.filter ( upcoming__gte = today )
    elist = elist.distinct().order_by('upcoming') # TODO: needed?
    return _ical_http_response_from_event_list( elist, group.name )

def _ical_http_response_from_event_list( elist, filename ): # {{{2
    """ returns an ical file with the events in ``elist`` and the name
    ``filename`` """
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

def all_events_text ( request ): #{{{1
    """ returns a text file with all events.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> e = Event.objects.create(
    ...         title = 'aet_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('all_events_text')).status_code
    200
    """
    elist = Event.objects.all()
    text = Event.list_as_text( elist )
    response = HttpResponse( text, mimetype = 'text/text;charset=UTF-8' )
    filename =  Site.objects.get_current().name + '_' + \
            datetime.datetime.now().isoformat() + '.txt'
    response['Filename'] = filename
    response['Content-Disposition'] = 'attachment; filename=' + filename
    return response

def handler404(request): #{{{1
    """ custom 404 handler """
    return main( request, error_messages = 
            _("An object couldn't be retrieved. Check the URL"),
            status_code = 404)

def handler500(request): #{{{1
    """ custom 500 handler """
    return main( request, error_messages = 
            _(''.join(['We are very sorry but an error has ocurred. We have ',
                'been automatically informed and will fix it in no time, ',
                'because we care'])),
            status_code = 500 )
