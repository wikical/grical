#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker ft=python
# gpl {{{1
#############################################################################
# Copyright 2009-2011 Ivan Villanueva <ivan ät gridmind.org>
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
import calendar
from calendar import HTMLCalendar # TODO use LocaleHTMLCalendar
import datetime
from docutils import core
from docutils import ApplicationError
from docutils.parsers.rst import roles, nodes
from docutils.parsers.rst.roles import set_classes
from docutils.writers.html4css1 import Writer
import re
import vobject
import unicodedata

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import Max, Q
from django.contrib.sites.models import Site
from django.core import serializers
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db.models import Max, Min
from django.db.models.query import QuerySet
from django.forms.models import inlineformset_factory, ModelForm
from django.http import ( HttpResponseRedirect, HttpResponse, Http404,
        HttpResponseForbidden, HttpResponseBadRequest )
from django.shortcuts import ( render_to_response, get_object_or_404,
        get_list_or_404 )
from django.template import RequestContext, Context, loader
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from tagging.models import Tag, TaggedItem
from reversion import revision
from reversion.models import Version, Revision

from gridcalendar.events.forms import ( 
    SimplifiedEventForm, EventForm, FilterForm,
     NewGroupForm, InviteToGroupForm, AddEventToGroupForm, DeleteEventForm )
from gridcalendar.events.models import ( 
    Event, EventUrl, EventSession, EventDeadline, Filter, Group,
    Membership, GroupInvitation, ExtendedUser, Calendar, RevisionInfo )
from gridcalendar.events.utils import search_address, html_diff
from gridcalendar.events.tables import EventTable
from gridcalendar.events.feeds import SearchEventsFeed
from gridcalendar.events.search import search_events

# TODO: check if this works with i18n
views = [_('table'), _('map'), _('boxes'), _('calendars'),]

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
    # without a URL; and deleting some urls, deadlines and sessions
    if event_id and isinstance( event_id, int ):
        event_id = unicode( event_id )
    if event_id:
        event = get_object_or_404( Event, pk = event_id )
        can_delete = True
    else:
        event = Event()
        can_delete = False
    # TODO: when removing all fields of a row the expected behaviour is to
    # delete the entry, but the inlineformset shows an error telling that the
    # fields are required, change it. Notice that the user can delete with the
    # delete check box, but deleting all fields should also work.
    event_urls_factory = inlineformset_factory( 
            Event, EventUrl, extra = 4, can_delete = can_delete, )
    event_deadlines_factory = inlineformset_factory( 
            Event, EventDeadline, extra = 4, can_delete = can_delete, )
    event_sessions_factory = inlineformset_factory( 
            Event, EventSession, extra = 4, can_delete = can_delete, )
    if request.method == 'POST':
        # revision.user = request.user # done by the reversion middleware
        try:
            event_form = EventForm( request.POST, instance = event )
            formset_url = event_urls_factory(
                    request.POST, instance = event )
            formset_deadline = event_deadlines_factory(
                    request.POST, instance = event )
            formset_session = event_sessions_factory(
                    request.POST, instance = event )
            # some spammers modify ManagementForm data in formsets which raises
            # a ValidationError with the message: 'ManagementForm data is
            # missing or has been tampered with'
        except ValidationError:
            messages.error( request, _('Internal data missing. No data ' \
                    'saved. If the error persists, please contact us.') )
            raise Http404
        else:
            if event_form.is_valid():
                event = event_form.save(commit = False)
                if formset_url.is_valid() & formset_session.is_valid() & \
                        formset_deadline.is_valid() :
                    # FIXME: don't allow to save an event with missing basic
                    # data like a URL
                    if not event_form.cleaned_data.get( 'coordinates', False ):
                        event.coordinates = None
                    event.save()
                    formset_url.save()
                    formset_session.save()
                    formset_deadline.save()
                    revision.add_meta( RevisionInfo,
                            as_text = smart_unicode( event.as_text() ) )
                    return HttpResponseRedirect( reverse( 'event_show_all',
                            kwargs = {'event_id': event.id} ) )
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
        messages.warning(request, _('warning: the start date is in the past'))
    return render_to_response( 'event_edit.html', templates,
            context_instance = RequestContext( request ) )

def event_new_raw( request, template_event_id = None ): # {{{1
    """ View to create an event as text
    
    If a ``template_event_id`` is given, the preliminary text is the text form
    of the event with that id.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('event_new_raw')).status_code
    200
    """
    if request.method == 'POST':
        # revision.user = request.user # done by the reversion middleware
        if 'event_astext' in request.POST:
            event_textarea = request.POST['event_astext']
            try:
                event = Event.parse_text(event_textarea, None, request.user.id)
                messages.success( request, _( u'event saved' ) )
                revision.add_meta( RevisionInfo,
                        as_text = smart_unicode( event.as_text() ) )
                return HttpResponseRedirect( 
                    reverse( 'event_show_all', kwargs={'event_id': event.id} ))
            except ValidationError as err:
                if hasattr( err, 'message_dict' ):
                    # if hasattr(err, 'message_dict'), it looks like:
                    # {'url': [u'Enter a valid value.']}
                    for field_name, error_message in err.message_dict.items():
                        messages.error( request,
                                field_name + ": " + ', '.join(error_message) )
                elif hasattr( err, 'messages' ):
                    for message in err.messages:
                        messages.error( request, message )
                elif hasattr( err, 'message' ):
                    messages.error( request, err.message )
                templates = {
                        'title': _( "edit event as text" ),
                        'event_textarea': event_textarea, }
                return render_to_response(
                        'event_new_raw.html',
                        templates,
                        context_instance = RequestContext( request ) )
        else:
            messages.error( request, _(u"You submitted an empty form, " \
                    "nothing has been saved. Click the back button in your " \
                    "browser and try again.") )
            return main( request )
    else:
        try:
            template_event = Event.objects.get( pk = template_event_id )
            templates = {
                    'title': _( "edit event as text" ),
                    'template': smart_unicode( template_event.as_text() ) }
        except Event.DoesNotExist:
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
        # revision.user = request.user # done by the reversion middleware
        if 'event_astext' in request.POST:
            event_textarea = request.POST['event_astext']
            try:
                event = event.parse_text(
                            event_textarea, event_id, request.user.id )
            except ValidationError as err:
                # found a validation error with one or more errors
                if hasattr( err, 'message_dict' ):
                    # if hasattr(err, 'message_dict'), it looks like:
                    # {'url': [u'Enter a valid value.']}
                    for field_name, error_message in err.message_dict.items():
                        if isinstance(error_message, list):
                            error_message = " ; ".join(error_message)
                        messages.error( request,
                                field_name + ": " + error_message )
                elif hasattr( err, 'messages' ):
                    for message in err.messages:
                        messages.error( request, message )
                elif hasattr( err, 'message' ):
                    messages.error( request, err.message )
                templates = {
                        'title': _( "edit event as text" ),
                        'event_textarea': event_textarea,
                        'event_id': event_id,
                        'example': Event.example() }
                return render_to_response( 'event_edit_raw.html', templates,
                        context_instance = RequestContext( request ) )
            if isinstance(event, Event):
                messages.success( request, _( u'event modifed' ) )
                revision.add_meta( RevisionInfo,
                        as_text = smart_unicode( event.as_text() ) )
                return HttpResponseRedirect( 
                    reverse('event_show_all', kwargs = {'event_id': event_id}))
            else:
                messages.error( request, event )
                return main( request )
        else:
            messages.error( request, 
                    _(u'You submitted an empty form, nothing was saved. ' \
                    'Click the back button in your browser and try again.') )
            return main( request )
    else:
        event_textarea = event.as_text()
        templates = {
                'title': _( "edit event as text" ),
                'event_textarea': event_textarea,
                'event_id': event_id,
                'example': Event.example() }
        return render_to_response( 'event_edit_raw.html', templates,
                context_instance = RequestContext( request ) )

def event_does_not_exist( request, event_id, redirect_url ): # {{{1
    """ if event_id was deleted it shows event redirection or deleted page,
    otherwise raises 404 """
    try:
        deleted_version = Version.objects.get_deleted_object(
                Event, object_id = event_id )
    except Version.DoesNotExist:
        raise Http404
    revision_meta = deleted_version.revision.revisioninfo_set.all()
    assert( len( revision_meta ) == 1 )
    redirect = revision_meta[0].redirect
    if redirect:
        messages.info( request,
                _( u'redirected from deleted event %(event_nr)s' ) % \
                        {'event_nr': event_id} )
        return HttpResponseRedirect( reverse( redirect_url,
            kwargs = {'event_id': redirect,} ) )
    else:
        messages.info( request,
            _('You have tried to access an event which has been deleted.'))
        return HttpResponseRedirect( reverse(
            'event_deleted', kwargs = { 'event_id': event_id } ) )

def event_show_all( request, event_id ): # {{{1
    """ View that shows an event.

    It interprets the ``description`` field as ReStructuredText if there are
    not errors or warnings from docutils.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create(
    ...         title = 'es_test', tags = 'berlin',
    ...         start = datetime.date.today() )
    >>> Client().get(reverse('event_show_all',
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
    try:
        event = Event.objects.get( pk = event_id )
    except Event.DoesNotExist:
        return event_does_not_exist( request, event_id, 'event_show_all' )
    # about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    title = unicode(event.upcoming)
    if event.city:
        title += " " + event.city
    if event.country:
        title += " (" + event.country + ")"
    title += " - " + event.title + " | " + Site.objects.get_current().name
    rst2html = None
    if event.description:
        # we try to parse the description as ReStructuredText with one
        # additional role to get event urls, e.g.: :e:`123`
        # we create a new RST role to interpret
        def event_reference_role( # {{{2
                role, rawtext, text, lineno, inliner, options={}, content=[] ):
            # hacked using the example at
            # http://docutils.sourceforge.net/docs/howto/rst-roles.html
            try:
                referentiated_event = Event.objects.get( pk = int(text) )
            except ValueError:
                msg = inliner.reporter.error(
                        _(u"The role ':e:' must be followed by a number") )
                prb = inliner.problematic(rawtext, rawtext, msg)
                return [prb], [msg]
            except Event.DoesNotExist:
                msg = inliner.reporter.error(
                        _(u'No event with the number %(event_nr)s') %
                            {'event_nr': text} )
                prb = inliner.problematic(rawtext, rawtext, msg)
                return [prb], [msg]
            set_classes( options )
            node = nodes.reference( rawtext, referentiated_event.title,
                    refuri = referentiated_event.get_absolute_url(),
                    **options )
            return [node], []
        roles.register_local_role('e', event_reference_role)
        # workaround for Django bug https://code.djangoproject.com/ticket/6681
        # 'title-reference' is the default in docutils
        roles.DEFAULT_INTERPRETED_ROLE = 'title-reference'
        try:
            rst2html = core.publish_parts(
                source = event.description,
                writer = Writer(),
                settings_overrides = {'input_encoding': 'unicode', 'output_encoding': 'unicode'},
                )['html_body']
        except ( ApplicationError, AttributeError ) as err:
            # it happens when there is a severe RST syntax error. Text example
            # that produces such an error:
            # //////////////
            # Open Call 2011
            # \\\\\\\\\\\\\\\
            messages.error( request, _( u'the event description cannot be ' \
                'rendered using ReStructuredText syntax. The error is:' ) +
                err.message )
            # TODO: get the translated message if there is one in docutils
            rst2html = None
        #if '<div class="system-message">' in rst2html:
        #    # there is a rst syntax error/warning
        #    # TODO: inform the user that the description couldn't be
        #    # rendered as rst and provide a link that shows the errors/warnings
        #    rst2html = None
    templates = { 'title': title, 'event': event, 'rst2html': rst2html }
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
    try:
        event = Event.objects.get( pk = event_id )
    except Event.DoesNotExist:
        return event_does_not_exist( request, event_id, 'event_show_raw' )
    event_textarea = event.as_text()
    templates = {
            'title': _( "view as text" ),
            'event_textarea': event_textarea,
            'event': event }
    return render_to_response( 'event_show_raw.html',
            templates, context_instance = RequestContext( request ) )

def revisions_diffs( revisions ): # {{{1
    """ from a list of revisions create a list of tuples with a revision and a
    html text of the diff """
    revisions_diffs = []
    previous = None
    for revision in revisions:
        if previous:
            try:
                # TODO: the code below is hitting the db all the time: optimize
                # using above something like: revisions_infos =
                # RevisionInfo.objects.select_related(depth = 3).filter(...
                old_as_text = previous.revisioninfo_set.all()[0].as_text
                new_as_text = revision.revisioninfo_set.all()[0].as_text
                revisions_diffs.append( ( revision,
                    html_diff( new_as_text, old_as_text ) ) )
            except:
                revisions_diffs.append( (revision, None) )
        else:
            revisions_diffs.append( (revision, None) )
        previous = revision
    return revisions_diffs

def event_history( request, event_id ): # {{{1
    """ show the history of an event """
    # TODO: tests including one that checks that a revision has only one
    # element in its revisioninfo_set
    # TODO: undeleted events history is confusing, fix it
    try:
        event = Event.objects.get( pk = event_id )
    except Event.DoesNotExist:
        return event_does_not_exist( request, event_id, 'event_history' )
    revisions = [ version.revision for version in
            Version.objects.get_for_object( event ) ]
    revisions.reverse()
    # we create a list of tuples with a revision and a string which is a html
    # diff to the previous revision (or None if it is not possible)
    revs_diffs = revisions_diffs( revisions )
    templates = {
            'title': _( "History of event %(event_nr)s" ) % \
                    {'event_nr': str(event.id)},
            'event': event,
            'revisions_diffs': revs_diffs }
    return render_to_response( 'event_history.html',
            templates, context_instance = RequestContext( request ) )

@login_required
def event_revert( request, revision_id, event_id ): # {{{1
    event = get_object_or_404( Event, pk = event_id )
    revision = get_object_or_404( Revision, pk = revision_id )
    # we check that the event is a version of the revision (a revision in
    # django-reversion consists of one or more versions, which are changes to
    # an object of the database, e.g. an event object or a EventUrl object)
    assert unicode(event.id) in [ version.object_id for version in
            revision.version_set.all() ]
    revision.revert()
    messages.success( request, _(u'event has been reverted') )
    return HttpResponseRedirect( reverse(
            'event_show_all', kwargs = {'event_id': event.id,} ) )

@login_required
def event_delete( request, event_id ):
    event = get_object_or_404( Event, pk = event_id )
    user = request.user
    if request.method == "POST":
        form = DeleteEventForm( data = request.POST )
        if form.is_valid():
            # revision.user = user # done by the reversion middleware
            info_dict = {}
            reason = form.cleaned_data['reason']
            if reason:
                info_dict['reason'] = reason
            redirect = form.cleaned_data['redirect']
            if redirect:
                info_dict['redirect'] = redirect
            info_dict['as_text'] = smart_unicode( event.as_text() )
            revision.add_meta( RevisionInfo, **info_dict )
            event.delete()
            messages.success( request, _('Event %(event_id)s deleted.') % \
                    {'event_id': event_id,} )
            return HttpResponseRedirect( reverse('main') )
    else:
        # TODO: if event is part of a serie, ask to delete only this event,
        # also all futures events, also all past events or all
        form = DeleteEventForm()
    context = dict()
    context['form'] = form
    context['event'] = event
    return render_to_response('event_delete.html',
            context_instance = RequestContext( request, context) )

def event_deleted( request, event_id ): # {{{1
    """ inform the user the event has been deleted, show a link of a redirect
    if present and, if the user is authenticated, allow undeleting the event.
    """
    try:
        deleted_version = Version.objects.get_deleted_object( Event,
                object_id = event_id )
    except Version.DoesNotExist:
        raise Http404
    # checking if the event is realy deleted
    if Event.objects.filter( pk = event_id ).exists():
        messages.info( request, _('You have tried to access a deleted event' \
                ' which is not deleted. See below.') )
        return HttpResponseRedirect( reverse(
            'event_history', kwargs = {'event_id': event_id} ) )
    revision = deleted_version.revision
    revisioninfos = revision.revisioninfo_set.all()
    # a revision should have only one revisioninfo (design constraint)
    # TODO check this constranint with a post_save signal in revisioninfo
    assert len( revisioninfos ) == 1
    revisioninfo = revisioninfos[0]
    # we now get all revisions to show the history also
    revisions = [ version.revision for version in
            Version.objects.get_for_object_reference( Event, event_id ) ]
    revisions.reverse()
    revs_diffs = revisions_diffs( revisions )
    templates = {
            'title': _( "deleted event %(event_nr)s" ) % \
                    {'event_nr': deleted_version.object_id,},
            'revision': revision,
            'revisioninfo': revisioninfo,
            'username': revision.user.username,
            'deleted_version': deleted_version,
            'event_id': event_id,
            'revisions_diffs': revs_diffs }
    return render_to_response( 'event_deleted.html',
            templates, context_instance = RequestContext( request ) )

@login_required
def event_undelete( request, event_id ): # {{{1
    try:
        deleted_version = Version.objects.get_deleted_object( Event,
                object_id = event_id )
    except Version.DoesNotExist:
        raise Http404
    # TODO ask the user for a reason for the undeletion
    deleted_revision = deleted_version.revision
    revisioninfos = deleted_revision.revisioninfo_set.all()
    # a revision should have only one revisioninfo (design constraint)
    # TODO check this constranint with a post_save signal in revisioninfo
    assert len( revisioninfos ) == 1
    revisioninfo = revisioninfos[0]
    # we check if there is an event with the same name and start date
    # TODO test when there is one
    as_text = revisioninfo.as_text
    simple_fields = Event.get_fields( as_text )[0]
    title = simple_fields['title']
    start = simple_fields['start']
    try:
        equal = Event.objects.get( title = title, start = start )
    except Event.DoesNotExist:
        deleted_revision.revert()
        revision.add_meta( RevisionInfo, as_text = as_text )
        equal = False
    if not equal:
        messages.info( request, _('Event has been successfully undeleted.') )
        return HttpResponseRedirect( reverse(
            'event_show_all', kwargs = {'event_id': event_id} ) )
    messages.error( request, _( 'Undelete operation not possible' ) )
    templates = {
            'title': _( "undelete event %(event_nr)s" ) % \
                        {'event_nr': deleted_version.object_id,},
            'as_text': as_text,
            'event_id': event_id,
            'title': title,
            'start': start,
            'equal': equal,}
    return render_to_response( 'event_undelete_error.html',
            templates, context_instance = RequestContext( request ) )

def search( request, query = None, view = 'boxes' ): # {{{1
    # doc {{{2
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
    ...         title = 's1_test', tags = 'berlin', city = 'prag',
    ...         start = datetime.date.today())
    >>> e2 = Event.objects.create(
    ...         title = 's2_test', tags = 'berlin', city = 'madrid',
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
    >>> Client().get(reverse('search_query_view',
    ...         kwargs={'query': 'test', 'view': 'calendars'})).status_code
    200
 
    >>> Client().get(reverse('search'), {'query': '#berlin',}).status_code
    200
    >>> response = Client().get(reverse('search'), {'query': '#berlinn',})
    >>> response = response.content
    >>> assert 'There are no events for this search currently' in response

    >>> Client().get(reverse('search'), {'query': '@madrid',}).status_code
    200
    >>> response = Client().get(reverse('search'), {'query': '@madridd',})
    >>> response = response.content
    >>> assert 'There are no events for this search currently' in response

    >>> e1.delete()
    >>> e2.delete()
    """
    # function body {{{2
    # query
    if 'query' in request.GET and request.GET['query']:
        query = request.GET['query']
    # view
    if 'view' in request.GET and request.GET['view']:
        view = request.GET['view']
    # shows the homepage with a message if no query, except when view=json
    # because client expect json
    if (not query) and (view != 'json'):
        # When a client ask for json, html should not be the response
        # TODO: test what happens for empty query with json, xml and yaml
        messages.error( request, 
            _( u"A search was submitted without a query string" ) )
        return main( request )
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
    try:
        search_result = search_events( query, related )
    except ValueError as err: # TODO: catch other errors
        # this can happen for instance when a date is malformed like 2011-01-32
        messages.error( request, 
                _( u"The search is malformed: %(error_message)s" ) %
                {'error_message': err.args[0]} )
        search_result = Event.objects.none()
    if limit:
        search_result = search_result[0:limit]
    # views
    if view == 'json':
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
    if view in ('yaml', 'xml'):
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
    if view == 'rss':
        return SearchEventsFeed()( request, query )
    if view == 'ical':
        return ICalForSearch( request, query )
    # variables to be passed to the html templates
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
    if isinstance(search_result, QuerySet):
        n_events = search_result.count()
    else:
        n_events = len( search_result )
    context['number_of_events_found'] = n_events
    if n_events == 0:
        return render_to_response( 'search.html',
                context,
                context_instance = RequestContext( request ) )
    if view == 'table':
        sort = request.GET.get( 'sort', 'upcoming' )
        page = int( request.GET.get( 'page', '1' ) )
        # The next line was used in the past when using
        # django_tables.MemoryTable. Now we use ModelTable.
        #search_result = EventTable.convert( search_result )
        search_result_table = EventTable( search_result, order_by = sort )
        search_result_table.paginate(
                Paginator, 50, page = page, orphans = 2 )
        context['events_table'] = search_result_table
        context['sort'] = sort
    elif view == 'boxes' or view == 'map':
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
    elif view == 'calendars':
        # TODO: use pagination
        if isinstance( search_result, QuerySet ):
            first_year = search_result[0].upcoming.year
            last_year_start = search_result.latest('start').start.year
            last_year_end = search_result.filter( end__isnull = False )
            if last_year_end:
                last_year_end = last_year_end.latest('end').end.year
            else:
                last_year_end = 0
            last_year_deadline = search_result.filter(
                    deadlines__deadline__isnull = False)
            if last_year_deadline:
                last_year_deadline = \
                        last_year_deadline.latest( 'deadlines__deadline' )
                last_year_deadline =  \
                    last_year_deadline.deadlines.all().latest(
                        'deadline').deadline.year
            else:
                last_year_deadline = 0
            last_year = max(
                    last_year_start, last_year_end, last_year_deadline )
        else:
            # first year
            first_year = search_result[0].upcoming.year
            last_year = first_year
            for event in search_result:
                if event.start.year > last_year:
                    last_year = event.start.year
                if event.end and event.end.year > last_year:
                    last_year = event.end.year
                for deadline in event.deadlines.iterator():
                    if deadline.deadline > last_year:
                        last_year = deadline.deadline
        years_cals = []
        events_cal = EventsCalendar( search_result )
        for year in range( first_year, last_year + 1 ):
            years_cals.append( (
                year,
                mark_safe( smart_unicode(
                    events_cal.formatyear( year, width=1 ) ) ) ) )
        context['years_cals'] = years_cals
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
        messages.error( request, 
            _( u"You are trying to save a search without any query text" ) )
        return main( request )
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
        messages.error( request, 
                _(u'You have submitted a GET request which is not ' \
                'a valid method for saving a filter') )
        return main( request )

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
        messages.error( request, 
                _(u'You are not allowed to edit the filter with the ' \
                'number %(filter_id)d') % {'filter_id': filter_id,} )
        return main( request )
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
        messages.error( request,
                _(u'You are not allowed to delete the filter with the ' \
                'number %(filter_id)d') % {'filter_id': filter_id,} )
        return main( request )
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
        messages.error( request, _( "You do not have any filters" ) )
        return main( request )
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

def main( request, status_code=200 ):# {{{1
    """ main view
    
    >>> from django.test import Client
    >>> c = Client()
    >>> r = c.get('/')
    >>> r.status_code # /
    200
    """
    # processes the event form, but not if status_code is 404 or 500 because
    # request can contain POST data coming from another form
    if (not status_code == 404) and (not status_code == 500) and \
            request.method == 'POST':
        # revision.user = request.user # done by the reversion middleware
        event_form = SimplifiedEventForm( request.POST )
        if event_form.is_valid():
            cleaned_data = event_form.cleaned_data
            # create a new entry and saves the data
            event = Event( user_id = request.user.id,
                      title = cleaned_data['title'],
                      start = cleaned_data['when']['start'],
                      tags = cleaned_data['tags'], )
            if cleaned_data['when'].has_key('end'):
                event.end = cleaned_data['when']['end']
            if cleaned_data['when'].has_key('starttime'):
                event.starttime = cleaned_data['when']['starttime']
            if cleaned_data['when'].has_key('endtime'):
                event.endtime = cleaned_data['when']['endtime']
            addresses = search_address( cleaned_data['where'] )
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
                #FIXME: deal with more than one address, none or general
                # coordinates like e.g. pointing to the center of city/country
                event.address = cleaned_data['where']
            event.save()
            # create the url data
            event.urls.create( url_name = "web", url = cleaned_data['web'] )
            revision.add_meta( RevisionInfo,
                    as_text = smart_unicode( event.as_text() ) )
            messages.info( request, _( u'Event successfully saved. ' \
                    'Optionally you can add more information about the ' \
                    'event now.' ) )
            return HttpResponseRedirect( reverse( 'event_edit',
                    kwargs = {'event_id': str( event.id )} ) )
    else:
        event_form = SimplifiedEventForm()
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
        messages.error( request,
            _("You are not a member of any group") )
        return main( request )
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
        if request.method == "POST":
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
                raise RuntimeError()
        else:
            form = AddEventToGroupForm(user=user, event=event)
        context = dict()
        context['form'] = form
        context['event'] = event
        return render_to_response('groups/add_event_to_group.html',
                context_instance=RequestContext(request, context))
    else:
        messages.info( request,
                _(u'The event %(event_id)d is already in all the ' \
                'groups that you are in') % {'event_id': event_id,} )
        return main(request )

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
        messages.error( request,
                _(u"Your have tried to add a member to the group " \
                "'%(group_name)s', but you are yourself not a member " \
                "of it" ) % {'group_name': group.name,} )
        return main( request )
    if request.method == "POST":
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
    elist = search_events( query )
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
    messages.error( request,
            _(u"An object couldn't be retrieved. Check the URL") )
    return main( request, status_code = 404 )

def handler500( request ): #{{{1
    """ custom 500 handler """
    messages.error( request,
            _( u'We are very sorry but an error has ocurred. We have been ' \
            'automatically informed and will fix it as soon as possible. ' ) )
    return main( request, status_code = 500 )

# from http://moinmo.in/MacroMarket/EventAggregator
def getColour(s):
    colour = [0, 0, 0]
    digit = 0
    for c in s:
        colour[digit] += ord(c)
        colour[digit] = colour[digit] % 256
        digit += 1
        digit = digit % 3
    return tuple(colour)
# from http://moinmo.in/MacroMarket/EventAggregator
def getBlackOrWhite(colour):
    if sum(colour) / 3.0 > 127:
        return (0, 0, 0)
    else:
        return (255, 255, 255)

class EventsCalendar(HTMLCalendar): #TODO: use LocaleHTMLCalendar

    def __init__(self, events, *args, **kwargs):
        super(EventsCalendar, self).__init__(*args, **kwargs)
        self.events = events

    def formatyear(self, theyear, *args, **kwargs):
        months = []
        for month in range(1, 13):
            months.append( self.formatmonth( theyear, month, withyear=False ) )
        return ''.join( months )

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>' # day outside month
        else:
            today = datetime.date.today()
            if ( day, self.month, self.year ) == \
                    ( today.day, today.month, today.year ):
                return '<td class="%s today">%d</td>' % \
                        (self.cssclasses[weekday], day)
            else:
                return '<td class="%s">%d</td>' % \
                        (self.cssclasses[weekday], day)

    def formatmonth(self, year, month, *args, **kwargs):
        # we save year and month for their use in formatweek
        self.year, self.month = year, month
        # we format month only if there are events in the month
        date1 = datetime.date( year, month, 1 )
        date2 = datetime.date( year, month,
                calendar.monthrange( year, month )[1] )
        today = datetime.date.today()
        if isinstance( self.events, QuerySet ):
            events = self.events.filter(
                Q( start__range = (date1, date2) )  |
                Q( end__range = (date1, date2) ) |
                Q(deadlines__deadline__range = (date1, date2),
                    deadlines__deadline__gte = today) |
                Q( start__lt = date1, end__gt = date2 ) ) # range in-between
            if events:
                return super(EventsCalendar, self).formatmonth(
                        year, month, *args, **kwargs )
        else:
            for eve in self.events:
                if ( eve.start >= date1 and eve.start <= date2 ) or \
                        ( eve.end and eve.end >= date1 and eve.end <= date2 ):
                    return super(EventsCalendar, self).formatmonth(
                            year, month, *args, **kwargs )
                for deadline in eve.deadlines.iterator():
                    if deadline.deadline >=date1 and \
                            deadline.deadline <=date2 and \
                            deadline.deadline >= today:
                        return super(EventsCalendar, self).formatmonth(
                                year, month, *args, **kwargs )
        return ""

    def formatweek( self, theweek, *args, **kwargs ):
        # get all events with days in this week
        days = [d for (d, wd) in theweek if d > 0] # d=0 -> not in month
        date1 = datetime.date( self.year, self.month, min( days ) )
        date2 = datetime.date( self.year, self.month, max( days ) )
        today = datetime.date.today()
        if isinstance( self.events, QuerySet ):
            events = self.events.filter(
                Q( start__range = (date1, date2) )  |
                Q( end__range = (date1, date2) ) |
                Q(deadlines__deadline__range = (date1, date2),
                    deadlines__deadline__gte = today) |
                Q( start__lt = date1, end__gt = date2 ) ) # range in-between
        else:
            events = []
            for eve in self.events:
                if ( eve.start >= date1 and eve.start <= date2 ) or \
                        ( eve.end and eve.end >= date1 and eve.end <= date2 ):
                    events.append( eve )
                    continue
                for deadline in eve.deadlines.iterator():
                    # exclude deadlines in the past
                    if deadline.deadline < datetime.date.today():
                        continue
                    if deadline.deadline >=date1 and deadline.deadline <=date2:
                        events.append( eve )
        text = u''
        text += super(EventsCalendar, self).formatweek(
                theweek, *args, **kwargs )
        if not events:
            text += '\n<tr class="empty-row">'
            for day, weekday in theweek:
                if day == 0:
                    text += self.formatday( day, weekday )
                else:
                    text += '<td>&nbsp;</td>'
            text += '</tr>\n'
        for eve in events:
            text += '\n<tr class="event-row">\n'
            bg = getColour( eve.title )
            fg = getBlackOrWhite(bg)
            style = ' style="background-color: rgb(%d, %d, %d); ' \
                    'color: rgb(%d, %d, %d);" ' % (bg + fg)
            colspan = 0
            for day, weekday in theweek:
                if day == 0:
                    if colspan == 0:
                        text += self.formatday( day, weekday )
                    else:
                        # this happen if there is an event until the end of the
                        # month and the week has some days belonging the next
                        # month (nodays)
                        text += u'<td class="event-rectangle" ' \
                            '%s colspan="%d"><a href="%s">%s</a></td>' % \
                            (style, colspan, eve.get_absolute_url(), eve.title)
                        colspan = 0
                        text += self.formatday( day, weekday )
                    continue
                date = datetime.date( self.year, self.month, day )
                if eve.contains( date ): # TODO: is this hitting the DB too much?
                    colspan += 1
                else:
                    if colspan > 0:
                        text += u'<td class="event-rectangle" ' \
                            '%s colspan="%d"><a href="%s">%s</a></td>' % \
                            (style, colspan, eve.get_absolute_url(), eve.title)
                    #text += self.formatday( date.day, date.weekday() )
                    text += '<td class="%s">&nbsp;</td>' % \
                                            self.cssclasses[ date.weekday() ]
                    colspan = 0
            if colspan > 0:
                text += u'<td class="event-rectangle" ' \
                        '%s colspan="%d"><a href="%s">%s</a></td>' % \
                        (style, colspan, eve.get_absolute_url(), eve.title)
            text += '\n</tr>\n'
        return text
