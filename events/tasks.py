#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# GPL {{{1
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

""" celery's tasks """

# imports {{{1
from celery.decorators import task

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache, get_cache
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

# NOTE: if tasks are supposed to use translations, you need to pass a language
# parameter to the celery task and add to it:
#     prev_language = translation.get_language()
#     language and translation.activate( language )
#     ...
#     translation.activate( prev_language )

# @task() def write_to_pipe( text ): # {{{1
@task()
def log_using_celery( text ):
    with open(settings.LOG_PIPE, 'a') as pipe:
        text = smart_str( text, encoding='utf-8', errors='ignore' )
        lines = text.splitlines()
        pipe.write( lines[0] + '\n' )
        lines = map( lambda line: '    %s\n' % line, lines[1:] )
        pipe.write( ''.join( lines ) )

@task() # save_in_caches {{{1
def save_in_caches( key, value, timeout = None ):
    cache_db = get_cache('db')
    if timeout:
        cache.set( key, value, timeout )
        cache_db.set( key, value, timeout )
    else:
        cache.set( key, value )
        cache_db.set( key, value )

# @task() def notify_users_when_wanted( event ): {{{1
@task()
def notify_users_when_wanted( event = None ):
    """ notifies users if *event* matches a filter of a user and the
    user wants to be notified for the matching filter """
    from gridcalendar.events.models import Event, Filter
    if isinstance(event, Event):
        pass
    elif isinstance(event, int) or isinstance(event, long):
        event = Event.objects.get(pk = event)
    else:
        event = Event.objects.get(pk = int(event))
    # TODO: the next code iterate throw all users but this is not workable
    # for a big number of users: implement a special data structure which
    # saves filters and can look up fast filters matching an event
    # TODO: show a diff of the changes
    users = User.objects.all()
    for user in users:
        user_filters = Filter.objects.filter( user = user ).filter(
                email = True)
        for fil in user_filters:
            if not fil.matches_event( event ):
                continue
            context = {
                'username': user.username,
                'event': event,
                'filter': fil,
                'site_name': Site.objects.get_current().name,
                'site_domain': Site.objects.get_current().domain, }
            # TODO: create the subject from a text template
            subject = _(u'filter match: ') + event.title
            # TODO: use a preferred language setting for users to send
            # emails to them in this language
            message = render_to_string( 'mail/event_notice.txt', context )
            from_email = settings.DEFAULT_FROM_EMAIL
            if subject and message and from_email and user.email:
                try:
                    if ( not settings.DEBUG ) or user.uername in \
                            settings.USERNAMES_TO_MAIL_WHEN_DEBUGGING:
                        send_mail( subject, message, from_email,
                            [user.email,], fail_silently = False )
                except (BadHeaderError, SMTPConnectError):
                    # FIXME: do something meaningfull, e.g. error log
                    pass
            else:
                # FIXME: do something meaningfull, e.g. error log
                pass

