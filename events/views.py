#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
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
from datetime import timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from docutils import core
from docutils import ApplicationError
from docutils.parsers.rst import roles, nodes
from docutils.parsers.rst.roles import set_classes
from docutils.writers.html4css1 import Writer
import re
import sys
import vobject
import unicodedata

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import Q
from django.contrib.sites.models import Site
from django.core import serializers
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.db import transaction, IntegrityError
from django.forms.models import inlineformset_factory, ModelForm
from django.http import ( HttpResponseRedirect, HttpResponse, Http404,
        HttpResponseForbidden, HttpResponseBadRequest )
from django.shortcuts import ( render_to_response, get_object_or_404,
        get_list_or_404 )
from django.template import RequestContext, Context, loader
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page

from tagging.models import Tag, TaggedItem
from reversion import revision
from reversion.models import Version, Revision

from gridcalendar.events.forms import ( 
    SimplifiedEventForm, EventForm, FilterForm, AlsoRecurrencesForm,
    CalendarForm,
    NewGroupForm, InviteToGroupForm, AddEventToGroupForm, DeleteEventForm )
from gridcalendar.events.models import ( 
    Event, EventUrl, EventSession, EventDate, Filter, Group,
    Membership, GroupInvitation, ExtendedUser, Calendar, RevisionInfo,
    add_start, add_end, add_upcoming )
from gridcalendar.events.utils import ( search_address, search_timezone,
        html_diff )
from gridcalendar.events.tables import EventTable
from gridcalendar.events.feeds import SearchEventsFeed
from gridcalendar.events.search import search_events

# TODO: check if this works with i18n
views = [_('table'), _('map'), _('boxes'), _('calendars'),]

@cache_page(60 * 15)
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

@cache_page(60 * 15)
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
    >>> e = Event.objects.create( title = 'ee_test', tags = 'berlin' )
    >>> e.startdate = datetime.date.today()
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
    if event.recurring:
        event_recurring = True
    else:
        event_recurring = False
    # TODO: when removing all fields of a row the expected behaviour is to
    # delete the entry, but the inlineformset shows an error telling that the
    # fields are required, change it. Notice that the user can delete with the
    # delete check box, but deleting all fields should also work.
    event_urls_factory = inlineformset_factory( 
            Event, EventUrl, extra = 4, can_delete = can_delete, )
    event_deadlines_factory = inlineformset_factory( 
            Event, EventDate, extra = 4, can_delete = can_delete, )
    event_sessions_factory = inlineformset_factory( 
            Event, EventSession, extra = 4, can_delete = can_delete, )
    if request.method == 'POST':
        try:
            event_form = EventForm( request.POST, instance = event )
            formset_url = event_urls_factory(
                    request.POST, instance = event )
            formset_deadline = event_deadlines_factory(
                    request.POST, instance = event )
            formset_session = event_sessions_factory(
                    request.POST, instance = event )
            if event_recurring:
                also_recurrences_form = AlsoRecurrencesForm( request.POST )
            else:
                also_recurrences_form = None
            # some spammers modify ManagementForm data in formsets which raises
            # a ValidationError with the message: 'ManagementForm data is
            # missing or has been tampered with'
        except ValidationError:
            messages.error( request, _('Internal data missing. No data ' \
                    'saved. If the error persists, please contact us.') )
            raise Http404
        if event_recurring:
            event_recurring_valid = also_recurrences_form.is_valid()
        else:
            event_recurring_valid = True
        if event_form.is_valid() and event_recurring_valid:
            event = event_form.save(commit = False)
            if formset_url.is_valid() & formset_session.is_valid() & \
                    formset_deadline.is_valid() :
                # FIXME: don't allow to save an event with missing basic
                # data like a URL
                if not event_form.cleaned_data.get( 'coordinates', False ):
                    event.coordinates = None
                with revision:
                    if request.user.is_authenticated():
                        revision.user = request.user
                    event.save()
                    event.startdate = event_form.cleaned_data['startdate']
                    if not event_form.cleaned_data.get( 'enddate', False ):
                        try:
                            end = EventDate.objects.get(event = event,
                                    eventdate_name = 'end')
                        except EventDate.DoesNotExist:
                            pass
                        else:
                            end.delete()
                    else:
                        event.enddate = event_form.cleaned_data['enddate']
                    formset_url.save()
                    formset_session.save()
                    formset_deadline.save()
                    revision.add_meta( RevisionInfo,
                            as_text = smart_unicode( event.as_text() ) )
                # add recurrences if the event is new and dates in the
                # calendars are marked
                if not event_id and 'recurrences' in request.POST:
                    for date_iso in request.POST.getlist('recurrences'):
                        # ignore same date as start
                        if date_iso == event.startdate.isoformat():
                            continue
                        # save recurrence
                        with revision:
                            if request.user.is_authenticated():
                                revision.user = request.user
                            # we do not clone dates nor sessions, as they 
                            # refer to the main event and not to the recurring
                            # events.TODO: inform the user
                            clone = event.clone( user = revision.user,
                                    except_models = [EventDate, EventSession],
                                    startdate = parse(date_iso).date() )
                            revision.add_meta( RevisionInfo,
                                    as_text = smart_unicode( clone.as_text() ) )
                # change recurrences if appropiate
                if event_recurring:
                    master = event.recurring.master
                    choice = also_recurrences_form.cleaned_data['choices']
                    if choice == 'this':
                        events = None
                    elif choice == 'past':
                        events = Event.objects.filter(
                                _recurring__master = master,
                                start__lt = event.startdate )
                    elif choice == 'future':
                        events = Event.objects.filter(
                                _recurring__master = master,
                                start__gt = event.startdate )
                    elif choice == 'all':
                        events = Event.objects.filter(
                                _recurring__master = master)
                        events = events.exclude( pk = event.pk )
                    else:
                        raise RuntimeError()
                    _change_recurrences( request.user, event, events )
                return HttpResponseRedirect( reverse( 'event_show_all',
                        kwargs = {'event_id': event.id} ) )
    else:
        event_form = EventForm( instance = event )
        formset_url = event_urls_factory( instance = event )
        formset_deadline = event_deadlines_factory( instance = event,
                queryset = EventDate.objects.filter(event = event).exclude(
                    eventdate_name__in = EventDate.reserved_names() ) )
        formset_session = event_sessions_factory( instance = event )
        if event_recurring:
            also_recurrences_form = AlsoRecurrencesForm()
        else:
            also_recurrences_form = None
    templates = {
            'title': 'edit event',
            'form': event_form,
            'formset_url': formset_url,
            'formset_session': formset_session,
            'formset_deadline': formset_deadline,
            'also_recurrences_form': also_recurrences_form,
            'event_id': event_id }
    # recurrences HTML-calendar
    if not event_id:
        # we show months from today to DEFAULT_RECURRING_DURATION_IN_DAYS
        months = []
        today = datetime.date.today()
        date = today
        end = today + timedelta( days =
                settings.DEFAULT_RECURRING_DURATION_IN_DAYS )
        while date <= end:
            months.append( mark_safe( smart_unicode(
                CalendarForm().formatmonth( date.year, date.month) ) ) )
            date = date + relativedelta( months=+1 )
        templates[ 'months' ] = months
    # add a warning message if the start date is in the past, which might be
    # a mistake
    if event_id and event.startdate < datetime.date.today():
        messages.warning(request, _('warning: the start date is in the past'))
    return render_to_response( 'event_edit.html', templates,
            context_instance = RequestContext( request ) )

# private because it doesn't deal with transactions
def _change_recurrences( user, event, events ): # {{{1
    """ modifies the events in ``events`` with the data of ``event`` except for
    ``start`` and ``end``, and including urls changes also. """
    if not events:
        return
    for rec in events:
        assert rec.recurring.master == event.recurring.master
        with revision:
            if user and user.is_authenticated():
                revision.user = user
            for field in Event.get_simple_fields():
                if field in ['startdate', 'enddate']:
                    continue
                if getattr(rec, field) != getattr(event, field):
                    setattr( rec, field, getattr( event, field ) )
            if rec.description != event.description:
                rec.description = event.description
            rec.save()
            rec_urls = rec.urls.all()
            event_urls = event.urls.all()
            for i in range( max( len(rec_urls), len(event_urls) ) ):
                if i < len( rec_urls ) and i < len( event_urls ):
                    changed = False
                    if rec_urls[i].url_name != event_urls[i].url_name:
                        rec_urls[i].url_name = event_urls[i].url_name
                        changed = True
                    if rec_urls[i].url != event_urls[i].url:
                        rec_urls[i].url = event_urls[i].url
                        changed = True
                    if changed:
                        rec_urls[i].save()
                elif i >= len( event_urls ):
                    rec_urls[i].delete()
                else:
                    assert i >= len( rec_urls )
                    EventUrl.objects.create(
                            event    = rec,
                            url_name = event_urls[i].url_name,
                            url      = event_urls[i].url )
            revision.add_meta( RevisionInfo,
                    as_text = smart_unicode( rec.as_text() ) )

def event_new_raw( request, template_event_id = None ): # {{{1
    """ View to create an event as text
    
    If a ``template_event_id`` is given, the preliminary text is the text form
    of the event with that id.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> Client().get(reverse('event_new_raw')).status_code
    200
    """
    if not request.method == 'POST':
        try:
            template_event = Event.objects.get( pk = template_event_id )
            templates = {
                    'title': _( "edit event as text" ),
                    'template': smart_unicode( template_event.as_text() ) }
        except Event.DoesNotExist:
            templates = { 'title': _( "edit event as text" ), }
        return render_to_response( 'event_new_raw.html', templates,
                context_instance = RequestContext( request ) )
    if not 'event_astext' in request.POST:
        messages.error( request, _(u"You submitted an empty form, " \
                "nothing has been saved. Click the back button in your " \
                "browser and try again.") )
        return main( request )
    event_textarea = request.POST['event_astext']
    try:
        sid = transaction.savepoint()
        with revision:
            if request.user.is_authenticated():
                revision.user = request.user
            event = Event.parse_text(event_textarea, None, request.user.id)
            revision.add_meta( RevisionInfo,
                    as_text = smart_unicode( event.as_text() ) )
        transaction.savepoint_commit(sid)
        messages.success( request, _( u'event saved' ) )
        return HttpResponseRedirect( 
            reverse( 'event_show_all', kwargs={'event_id': event.id} ))
    except ValidationError as err:
        transaction.savepoint_rollback(sid)
        # TODO: test that revision works here including invalidation
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
    except:
        transaction.savepoint_rollback(sid)
        raise

def event_edit_raw( request, event_id ): # {{{1
    """ View to edit an event as text.

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create( title = 'eer_test', tags = 'berlin' )
    >>> e.startdate = datetime.date.today()
    >>> transaction.commit()
    >>> Client().get(reverse('event_edit_raw',
    ...         kwargs={'event_id': e.id,})).status_code
    200
    >>> e.delete()
    """
    if isinstance( event_id, str ) or isinstance( event_id, unicode ):
        event_id = int( event_id )
    # checks if the event exists
    event = get_object_or_404( Event, pk = event_id )
    if event.recurring:
        event_recurring = True
    else:
        event_recurring = False
    if not request.method == 'POST':
        event_textarea = event.as_text()
        if event_recurring:
            also_recurrences_form = AlsoRecurrencesForm()
        else:
            also_recurrences_form = None
        templates = {
                'title': _( "edit event as text" ),
                'event_textarea': event_textarea,
                'also_recurrences_form': also_recurrences_form,
                'event_id': event_id,
                'example': Event.example() }
        return render_to_response( 'event_edit_raw.html', templates,
                context_instance = RequestContext( request ) )
    # request.method is POST
    if event_recurring:
        also_recurrences_form = AlsoRecurrencesForm( request.POST )
    else:
        also_recurrences_form = None
    if not 'event_astext' in request.POST:
        messages.error( request, 
                _(u'You submitted an empty form, nothing was saved. ' \
                'Click the back button in your browser and try again.') )
        return main( request )
    sid = transaction.savepoint()
    # TODO: test that this is working having a look at the db directly after
    # submitting without errors and with errors. Test that there is no
    # inconsistencies in the db for all cases:
    revision.start()
    if request.user.is_authenticated():
        revision.user = request.user
    event_textarea = request.POST['event_astext']
    try:
        if event_recurring and not also_recurrences_form.is_valid():
            raise ValidationError(_(u'Please select to which ' \
                    'recurring events changes should be applied'))
        event = event.parse_text(
                    event_textarea, event_id, request.user.id )
        if not event_recurring:
            events = None
        else:
            choice = also_recurrences_form.cleaned_data['choices']
            master = event.recurring.master
            if choice == 'this':
                events = None
            elif choice == 'past':
                events = Event.objects.filter(
                        _recurring__master = master,
                        start__lt = event.startdate )
            elif choice == 'future':
                events = Event.objects.filter(
                        _recurring__master = master,
                        start__gt = event.startdate )
            elif choice == 'all':
                events = Event.objects.filter(
                        _recurring__master = master)
                events = events.exclude( pk = event.pk )
            else:
                raise ValidationError( _(u'Unexpected value in recurring form') )
            _change_recurrences( request.user, event, events )
    except (ValidationError, IntegrityError) as err:
        revision.invalidate()
        transaction.savepoint_rollback(sid)
        if isinstance(err, ValidationError):
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
        elif isinstance(err, IntegrityError):
            # at least one date already exists
            # TODO: write a better error code
            messages.error( request, _(u'Changes not saved! It is not ' \
                    'possible to have more than one event in the database ' \
                    'with the same title and start date.') )
        else:
            raise
        templates = {
                'title': _( "edit event as text" ),
                'event_textarea': event_textarea,
                'also_recurrences_form': also_recurrences_form,
                'event_id': event_id,
                'example': Event.example() }
        return render_to_response( 'event_edit_raw.html', templates,
                context_instance = RequestContext( request ) )
    except:
        revision.invalidate()
        transaction.savepoint_rollback(sid)
        raise
    if isinstance(event, Event):
        # TODO: change messages to "eventS modified" if more than one was modified
        messages.success( request, _( u'event modifed' ) )
        revision.add_meta( RevisionInfo,
                as_text = smart_unicode( event.as_text() ) )
        revision.end()
        transaction.savepoint_commit(sid)
        return HttpResponseRedirect( 
            reverse('event_show_all', kwargs = {'event_id': event_id}))
    else:
        revision.invalidate()
        transaction.savepoint_rollback(sid)
        raise RuntimeError()

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
    >>> e = Event.objects.create( title = 'es_test', tags = 'berlin' )
    >>> e.startdate = datetime.date.today()
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
    title = ""
    if event.city:
        title += event.city
    if event.country:
        title += " (" + event.country + ")"
    # we put it in the cache in context_processors.py:
    current_site = cache.get( 'CURRENT_SITE', Site.objects.get_current().name )
    title += " - " + event.title + " | " + unicode(current_site)
    rst2html = None
    # recurring {{{2
    rec = event.recurring
    if rec:
        # doesn't work. TODO: why? maybe because using a relation ?
        #recurrences = Event.objects.defer('description', 'creation_time',
        #        'modification_time', 'starttime', 'endtime', 'tags', 'postcode',
        #        'address', 'coordinates')
        #recurrences = recurrences.filter( _recurring__master = rec.master)
        recurrences = Event.objects.filter( _recurring__master = rec.master)
        recurrences = add_start( recurrences ).order_by('start')
    else:
        recurrences = None
    if event.description: #{{{2
        # we try to parse the description as ReStructuredText with one
        # additional role to get event urls, e.g.: :e:`123`
        # we create a new RST role to interpret
        def event_reference_role(
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
    # templates {{{2
    templates = { 'title': title, 'event': event, 'recurrences': recurrences,
            'rst2html': rst2html }
    if 'oembed' in settings.INSTALLED_APPS:
        templates['load_oembed'] = True
    return render_to_response( 'event_show_all.html', templates,
            context_instance = RequestContext( request ) )

def event_show_raw( request, event_id ): # {{{1
    """ View that shows an event as text

    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> import datetime
    >>> e = Event.objects.create( title = 'esr_test', tags = 'berlin' )
    >>> e.startdate = datetime.date.today()
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
    key = 'revs_diffs_of_%d_v%d' % (event.id, event.version)
    revs_diffs = cache.get( key )
    if not revs_diffs:
        revisions = [ version.revision for version in
                Version.objects.get_for_object( event ) ]
        revisions.reverse()
        # we create a list of tuples with a revision and a string which is a html
        # diff to the previous revision (or None if it is not possible)
        revs_diffs = revisions_diffs( revisions )
        cache.set( key, revs_diffs, 2592000 )
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
    if event.recurring:
        event_recurring = True
    else:
        event_recurring = False
    if not request.method == "POST":
        form = DeleteEventForm()
        if event_recurring:
            also_recurrences_form = AlsoRecurrencesForm()
        else:
            also_recurrences_form = None
    else:
        form = DeleteEventForm( data = request.POST )
        if event_recurring:
            also_recurrences_form = AlsoRecurrencesForm( request.POST )
        else:
            also_recurrences_form = None
        if form.is_valid() and (
                (not event_recurring) or also_recurrences_form.is_valid() ):
            if not event_recurring:
                events = [event,]
            else:
                choice = also_recurrences_form.cleaned_data['choices']
                if choice == 'this':
                    events = [event,]
                elif choice == 'past':
                    events = Event.objects.filter(
                            _recurring__master = master,
                            start__lte = event.startdate )
                elif choice == 'future':
                    events = Event.objects.filter(
                            _recurring__master = master,
                            start__gte = event.startdate )
                elif choice == 'all':
                    events = Event.objects.filter(
                            _recurring__master = master)
                    events = events.exclude( pk = event.pk )
                else:
                    raise RuntimeError()
            for dele in events:
                with revision:
                    if request.user.is_authenticated():
                        revision.user = user
                    info_dict = {}
                    reason = form.cleaned_data['reason']
                    if reason:
                        info_dict['reason'] = reason
                    redirect = form.cleaned_data['redirect']
                    if redirect:
                        info_dict['redirect'] = redirect
                    info_dict['as_text'] = smart_unicode( dele.as_text() )
                    revision.add_meta( RevisionInfo, **info_dict )
                    dele.delete()
            messages.success( request, _('Event %(event_id)s deleted.') % \
                    {'event_id': event_id,} )
            return HttpResponseRedirect( reverse('main') )
    context = dict()
    context['form'] = form
    context['event'] = event
    return render_to_response('event_delete.html',
            {'also_recurrences_form': also_recurrences_form,},
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
@revision.create_on_success
def event_undelete( request, event_id ): # {{{1
    if request.user.is_authenticated():
        revision.user = request.user
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
        equal = Event.objects.get( title = title,
                dates__eventdate_name = start )
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
    ...         title = 's1_test', tags = 'berlin', city = 'prag' )
    >>> e1.startdate = datetime.date.today()
    >>> e2 = Event.objects.create(
    ...         title = 's2_test', tags = 'berlin', city = 'madrid' )
    >>> e2.startdate = datetime.date.today()
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
    query = request.GET.get('query', None)
    # view
    view = request.GET.get('view', 'boxes')
    # shows the homepage with a message if no query, except when view=json
    # because client expect json
    if (not query) and (view != 'json'):
        # When a client ask for json, html should not be the response
        # TODO: test what happens for empty query with json, xml and yaml
        messages.error( request, 
            _( u"A search was submitted without a query string" ) )
        return main( request )
    if view == 'rss': # {{{3
        return SearchEventsFeed()( request, query )
    if view == 'ical': # {{{3
        return ICalForSearch( request, query )
    # related {{{3
    try:
        related = bool(request.GET.get('related', True))
    except ValueError:
        related = True
    # search {{{3
    try:
        if view == 'boxes' or view == 'calendars':
            # for the view boxes and calendars we use EventDate model to get
            # each date of each event
            search_result = search_events( query, related, model = EventDate )
        else:
            search_result = search_events( query, related, model = Event )
            search_result = add_upcoming( search_result )
        search_result = add_start( search_result )
        search_result = add_end( search_result )
        search_result = search_result.distinct()
    except ValueError as err: # TODO: catch other errors
        # this can happen for instance when a date is malformed like 2011-01-32
        messages.error( request, 
                _( u"The search is malformed: %(error_message)s" ) %
                {'error_message': err.args[0]} )
        if view == 'boxes' or view == 'calendars':
            search_result = EventDate.objects.none()
        else:
            search_result = Event.objects.none()
    # order {{{3
    if view == 'boxes' or view == 'calendars':
        pass
    elif view == 'table':
        sort = request.GET.get( 'sort', 'upcoming' )
        # sanity check
        if sort not in ('upcoming', 'title', 'city', 'country',
                'start', 'end'):
            raise Http404
        # TODO: following line produces an error when sorting after something
        # else than upcoming. Fix it and change the table template
        # search_result = search_result.order_by( sort )
        search_result = search_result.order_by( 'upcoming' )
    else:
        search_result = search_result.order_by( 'upcoming' )
    # limit {{{3
    # views can have a max limit, which is stored in the dictionary
    # settings.views_max_limits
    # however, the user/api can specify a smaller limit
    limit = request.GET.get( 'limit', settings.DEFAULT_LIMIT )
    try:
        limit = int( limit )
        if limit <= 0 or limit > settings.DEFAULT_LIMIT:
            limit = settings.DEFAULT_LIMIT
    except ValueError:
        limit = settings.DEFAULT_LIMIT
    max_limit = settings.VIEWS_MAX_LIMITS.get( view, settings.DEFAULT_LIMIT )
    if limit > max_limit:
        limit = max_limit
    if view not in ('table', 'map', 'boxes', 'calendars'):
        search_result = search_result[0:limit]
        # for the others we use a paginator later on
    # views
    if view == 'json': # {{{3
        if 'jsonp' in request.GET and request.GET['jsonp']:
            jsonp = request.GET['jsonp']
        else:
            jsonp = None
        data = serializers.serialize(
                'json',
                search_result,
                fields=('title', 'upcoming', 'start', 'tags', 'coordinates'), #FIXME: start seems wrong
                indent = 2,
                ensure_ascii=False )
        if jsonp:
            data = jsonp + '(' + data + ')'
            mimetype = "application/javascript"
        else:
            mimetype = "application/json"
        return HttpResponse( mimetype = mimetype, content = data )
    if view in ('yaml', 'xml'): # {{{3
        data = serializers.serialize(
                view,
                search_result,
                indent = 2,
                fields=('title', 'upcoming', 'start', 'tags', 'coordinates') ) #FIXME: start seems wrong
        if view == 'xml':
            mimetype = "application/xml"
        else:
            mimetype = "application/x-yaml"
        return HttpResponse( mimetype = mimetype, content = data )
    # views table, map, boxes or calendars {{{3
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
    if view in ( 'boxes', 'map', 'calendars', 'table' ):
        # Make sure page request is an int. If not, deliver first page.
        try:
            page_nr = int(request.GET.get('page', '1'))
        except ValueError:
            page_nr = 1
        paginator = Paginator( search_result, limit)
        try:
            page = paginator.page( page_nr )
        except ( EmptyPage, InvalidPage ):
            page = paginator.page( paginator.num_pages )
        context['page'] = page
        if view == 'table':
            context['events_table'] = EventTable(
                    EventTable.convert( page.object_list ) )
            context['sort'] = sort
            # we use the Django paginator now. In the past for this view:
            #search_result_table.paginate(
            #        Paginator, limit, page = page_nr, orphans = 2 )
        if view == 'calendars':
            context['years_cals'] = \
                    EventsCalendar( page.object_list).years_cals()
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
    >>> e = Event.objects.create( title='lem_test', tags='berlin', user=u )
    >>> e.startdate = datetime.date.today()
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
        # {{{2
        event_form = SimplifiedEventForm( request.POST )
        if event_form.is_valid():
            with transaction.commit_manually():
                cleaned_data = event_form.cleaned_data
                # create a new entry and saves the data
                try:
                    event = Event(
                            user_id = request.user.id,
                            title = cleaned_data['title'],
                            tags = cleaned_data['tags'], )
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
                        timezone = search_timezone(
                                address['latitude'],
                                address['longitude'] )
                        if timezone:
                            event.timezone = timezone
                    else:
                        #FIXME: deal with more than one address, none or general
                        # coordinates like e.g. pointing to the center of
                        # city/country
                        event.address = cleaned_data['where']
                    with revision:
                        event.save()
                        event.startdate = cleaned_data['when']['startdate']
                        if cleaned_data['when'].has_key('enddate'):
                            event.enddate = cleaned_data['when']['enddate']
                        # create the url data
                        event.urls.create( url_name = "web",
                                url = cleaned_data['web'] )
                        if request.user.is_authenticated():
                            revision.user = request.user
                        revision.add_meta( RevisionInfo,
                                as_text = smart_unicode( event.as_text() ) )
                except:
                    transaction.rollback()
                    raise
                else:
                    transaction.commit()
                    messages.info( request, _( u'Event successfully saved. ' \
                            'Optionally you can add more information about the ' \
                            'event now.' ) )
                    # TODO: is redirect the proper way? or better submit to another
                    # view?
                    return HttpResponseRedirect( reverse( 'event_edit',
                            kwargs = {'event_id': str( event.id )} ) )
    else: # {{{2
        event_form = SimplifiedEventForm()
    # calculates events to show {{{2
    today = datetime.date.today()
    eventdates = EventDate.objects.select_related( depth=1 ).defer(
            'event__description', 'event__coordinates',
            'event__creation_time', 'event__modification_time',
            'event__postcode', 'event__address').filter(
            eventdate_date__gte = today )
    eventdates = add_start( eventdates )
    eventdates = add_end( eventdates )
    paginator = Paginator( eventdates, settings.MAX_EVENTS_ON_ROOT_PAGE,
            allow_empty_first_page = False )
    # Make sure page request is an int. If not, deliver first page.
    try:
        page_nr = int(request.GET.get('page', '1'))
    except ValueError:
        page_nr = 1
    # If page request (9999) is out of range, deliver last page of results.
    try:
        page = paginator.page( page_nr )
    except ( EmptyPage, InvalidPage ):
        page = paginator.page( paginator.num_pages )
    about_text = open( settings.PROJECT_ROOT + '/ABOUT.TXT', 'r' ).read()
    # We generate the response with a custom status code. Reason: our custom
    # handler404 and handler500 returns the main page with a custom error
    # message and we return also the proper html status code
    template = loader.get_template('base_main.html')
    context = RequestContext( request, dict =
            {
                'title': Site.objects.get_current().name,
                'form': event_form,
                'page': page,
                'reserved_names': EventDate.reserved_names(),
                'about_text': about_text,
            } )
    return HttpResponse(
            content = template.render( context ),
            mimetype="text/html",
            status = status_code )

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
    >>> e = Event.objects.create( title='gae_test', tags='berlin', user=u )
    >>> e.startdate = datetime.date.today()
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
    ...         title = 'event in group', tags = 'group-view', user =u1g )
    >>> e.startdate = datetime.date.today()
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
    >>> e = Event.objects.create( title = 'icfs_test', tags = 'berlin' )
    >>> e.startdate = datetime.date.today()
    >>> Client().get(reverse('search_ical',
    ...         kwargs={'query': 'berlin',})).status_code
    200
    """
    # TODO: add test checking that an event with two dates is not a duplicate
    try:
        elist = search_events( query ).distinct()
    except ValueError:
        # this can happen for instance when a date is malformed like 2011-01-32
        elist = Event.objects.none()
    domain = Site.objects.get_current().domain
    return _ical_http_response_from_event_list( elist, query,
            calname = domain + " " + query )

def ICalForEvent( request, event_id ): # {{{2
    """ ical file for an event
    >>> from django.test import Client
    >>> from django.core.urlresolvers import reverse
    >>> from gridcalendar.events.models import Event
    >>> e = Event( title = 'icfe_test', tags = 'berlin')
    >>> e.save()
    >>> e.startdate = datetime.date.today()
    >>> Client().get( reverse( 'event_show_ical',
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
    >>> e = Event.objects.create( title = 'icfg_test', tags = 'berlin' )
    >>> e.startdate = datetime.date.today()
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
    today = datetime.date.today()
    elist = Event.objects.filter( calendar__group = group,
            dates__eventdate_date__gte = today ).distinct()
    elist = add_upcoming( elist ).order_by('upcoming')
    domain = Site.objects.get_current().domain
    return _ical_http_response_from_event_list( elist, group.name,
           calname = domain + " " + "!" + group.name )

def _ical_http_response_from_event_list( elist, filename, calname = None ):#{{{2
    """ returns an ical file with the events in ``elist`` and the name
    ``filename`` """
    if len(elist) == 1:
        icalstream = elist[0].icalendar().serialize()
    else:
        ical = vobject.iCalendar()
        ical.add('METHOD').value = 'PUBLISH' # IE/Outlook needs this
        ical.add('PRODID').value = settings.PRODID
        if calname:
            ical.add('X-WR-CALNAME').value = calname
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

# def all_events_text ( request ): #{{{1
#     """ returns a text file with all events.
# 
#     >>> from django.test import Client
#     >>> from django.core.urlresolvers import reverse
#     >>> from gridcalendar.events.models import Event
#     >>> e = Event.objects.create(
#     ...         title = 'aet_test', tags = 'berlin',
#     ...         start = datetime.date.today() )
#     >>> Client().get(reverse('all_events_text')).status_code
#     200
#     """
#     # TODO: stream it, see https://code.djangoproject.com/ticket/7581
#     elist = Event.objects.all()
#     text = Event.list_as_text( elist )
#     response = HttpResponse( text, mimetype = 'text/text;charset=UTF-8' )
#     filename =  Site.objects.get_current().name + '_' + \
#             datetime.datetime.now().isoformat() + '.txt'
#     response['Filename'] = filename
#     response['Content-Disposition'] = 'attachment; filename=' + filename
#     return response

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
def bg_color(s):
    colour = [0, 0, 0]
    digit = 0
    for c in s:
        colour[digit] += ord(c)
        colour[digit] = colour[digit] % 256
        digit += 1
        digit = digit % 3
    return tuple(colour)
# from http://moinmo.in/MacroMarket/EventAggregator
def fg_color(colour):
    if sum(colour) / 3.0 > 127:
        return (0, 0, 0)
    else:
        return (255, 255, 255)

class EventsCalendar(HTMLCalendar): #TODO: use LocaleHTMLCalendar

    def years_cals( self ):
        years_cals = []
        for year in sorted( self._years_set ):
            html_code = mark_safe(
                    smart_unicode( self.formatyear( year, width = 1 ) ) )
            years_cals.append( ( year, html_code ) )
        return years_cals

    def __init__(self, eventdates, *args, **kwargs):
        # NOTE: ``eventdates`` is assumed to be sorted
        super(EventsCalendar, self).__init__(*args, **kwargs)
        # we generate an appropiate structure out of the eventdates:
        # (year,week_nr) -> event_id -> list_of_eventdates
        self.year_week_dic = {}
        self._years_set = set()
        for eventdate in eventdates:
            self._years_set.add( eventdate.eventdate_date.year )
            year_week = eventdate.eventdate_date.isocalendar()[0:2]
            if not self.year_week_dic.has_key( year_week ):
                eventdate_list = []
                eventdate_list.append( eventdate )
                event_id_dic = {}
                event_id_dic[ eventdate.event.id ] = eventdate_list
                self.year_week_dic[ year_week ] = event_id_dic
            else:
                event_id_idc = self.year_week_dic[ year_week ]
                if not event_id_dic.has_key( eventdate.event.id ):
                    eventdate_list = []
                    eventdate_list.append( eventdate )
                    event_id_idc[ eventdate.event.id ] = eventdate_list
                else:
                    event_id_dic[ eventdate.event.id ].append( eventdate )

    def formatyear(self, theyear, *args, **kwargs):
        months = []
        for month in range(1, 13):
            months.append( self.formatmonth( theyear, month, withyear=True ) )
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
        while date2 >= date1:
            if self.year_week_dic.has_key( date1.isocalendar()[0:2] ):
                return super(EventsCalendar, self).formatmonth(
                        year, month, *args, **kwargs )
            date1 = date1 + datetime.timedelta(days=1)
        return ""

    def formatweek( self, theweek, *args, **kwargs ):
        # get all events with days in this week
        days = [d for (d, wd) in theweek if d > 0] # d=0 -> not in month
        date1 = datetime.date( self.year, self.month, min( days ) )
        date2 = datetime.date( self.year, self.month, max( days ) )
        this_year_week = date1.isocalendar()[0:2]
        assert this_year_week == date2.isocalendar()[0:2]
        today = datetime.date.today()
        text = u''
        text += super(EventsCalendar, self).formatweek(
                theweek, *args, **kwargs )
        if not self.year_week_dic.has_key( this_year_week ):
            text += '\n<tr class="empty-row">'
            for day, weekday in theweek:
                if day == 0:
                    text += self.formatday( day, weekday )
                else:
                    text += '<td>&nbsp;</td>'
            text += '</tr>\n'
            return text
        for event_id, evdas in self.year_week_dic[this_year_week].items():
            event = evdas[0].event
            text += '\n<tr class="event-row">\n'
            bg = bg_color( evdas[0].event.title )
            fg = fg_color(bg)
            style = ' style="background-color: rgb(%d, %d, %d); ' \
                    'color: rgb(%d, %d, %d);" ' % (bg + fg)
            colspan = 0
            for day, weekday in theweek:
                if day == 0:
                    if colspan == 0:
                        text += self.formatday( day, weekday )
                    else:
                        # this happen if there is an event until the end of the
                        # month and the week has some days belonging to the next
                        # month (nodays)
                        text += u'<td class="event-rectangle" ' \
                            '%s colspan="%d"><a href="%s">%s</a></td>' % \
                            ( style, colspan, event.get_absolute_url(),
                                    event.title )
                        colspan = 0
                        text += self.formatday( day, weekday )
                    continue
                date = datetime.date( self.year, self.month, day )
                if filter(lambda d: d.eventdate_date == date, evdas ):
                    colspan += 1
                else:
                    if colspan > 0:
                        text += u'<td class="event-rectangle" ' \
                            '%s colspan="%d"><a href="%s">%s</a></td>' % \
                            ( style, colspan, event.get_absolute_url(),
                                    event.title )
                    #text += self.formatday( date.day, date.weekday() )
                    text += '<td class="%s">&nbsp;</td>' % \
                                            self.cssclasses[ date.weekday() ]
                    colspan = 0
            if colspan > 0:
                text += u'<td class="event-rectangle" ' \
                        '%s colspan="%d"><a href="%s">%s</a></td>' % \
                        ( style, colspan, event.get_absolute_url(),
                                event.title )
            text += '\n</tr>\n'
        return text
