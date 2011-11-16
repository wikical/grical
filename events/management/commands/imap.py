#!/usr/bin/env python
# -*- coding: utf-8 -*-
# GPL {{{1
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2010,2011 Adam Beret Manczuk <beret@hipisi.org.pl>,
# Ivan Villanueva <iv@gridmind.org>
#
# This file is part of GridCalendar.
# 
# GridCalendar is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU Generevent.idal Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""recive events from imap mailbox""" # {{{1

# imports {{{1

import sys
from imaplib import IMAP4, IMAP4_SSL
import email
from email.header import decode_header
from email.parser import Parser as EmailParser
from smtplib import SMTPException
from StringIO import StringIO
# from base64 import b64decode
# from email.utils import parseaddr

# from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail.message import EmailMessage
from django.db import transaction, IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_str
from django.core.management.base import NoArgsCommand
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string

from reversion import revision

from gridcalendar.events.models import Event


#TODO: set the Django language to the first possible language the email sender
# accepts (from the Accept-Language header). If there is no such header use the
# first possible value of the Content-Language header. If not present default
# to English

class Command( NoArgsCommand ): # {{{1
    """ A management command which parses mails from imap server..
    """

    help = "Parses mails from settings.IMAP_SERVER"

    mailbox = None

    def __init__( self, *args, **kwargs ): # {{{2
        if settings.IMAP_SSL:
            self.mailbox = IMAP4_SSL( settings.IMAP_SERVER )
        else:
            self.mailbox = IMAP4( settings.IMAP_SERVER )
        self.mailbox.login( settings.IMAP_LOGIN, settings.IMAP_PASSWD )
        self.mailbox.select()
        super( Command, self ).__init__( *args, **kwargs )

    def get_list( self ): # {{{2
        '''
        get list of message's numbers in INBOX mailbox
        '''
        #TODO: think if this would work when the mailbox is changed while
        # this code is running
        typ, data = self.mailbox.search( None, 'ALL' )
        nr_list = data[0].split( ' ' )
        if len( nr_list ) == 1 and nr_list[0] == '':
            return []
        else:
            return nr_list

    def handle_noargs( self, **options ): # {{{2
        """ Executes the action. """
        self.parse()

    def parse( self ): # {{{2
        '''
        parse all mails from imap mailbox
        '''
        #re_charset = re.compile( r'charset=([^\s]*)', re.IGNORECASE )
        for number in self.get_list():
            typ, data = self.mailbox.fetch( number, '(RFC822 UID BODY[TEXT])' )
            if (data is None) or (len(data) < 1) or (data[0] is None) or \
                    (len(data[0]) < 2):
                continue
            mail = email.message_from_string( data[0][1] )
            text = u""
            msgobj = EmailParser().parse( StringIO( mail ), False )
            for part in msgobj.walk():
                if part.get_content_type() == "text/plain":
                    if part.get_content_charset():
                        text += unicode( 
                                    part.get_payload( decode = True ),
                                    part.get_content_charset(),
                                    'replace' )
            # extracs subject
            subject = ''
            if msgobj['Subject'] is not None:
                decodefrag = decode_header( msgobj['Subject'] )
                subj_fragments = []
                for string , enc in decodefrag:
                    if enc:
                        string = unicode( string , enc, 'replace' )
                        #s = unicode( s , enc ).encode( 'utf8', \
                        #                               'replace' )
                    subj_fragments.append( string )
                subject = u''.join( subj_fragments )
            # 'from' field of the email received (TODO: better 'reply-to'?)
            to_email = mail['From']
            # sender of our emails
            from_email = settings.DEFAULT_FROM_EMAIL
            try:
                sid = transaction.savepoint()
                with revision:
                    event, dates_times_list = Event.parse_text( text )
                    revision.add_meta( RevisionInfo,
                            as_text = smart_unicode( event.as_text() ) )
                for dates_times in dates_times_list:
                    with revision:
                        clone = event.clone( user = None,
                                except_models = [EventDate, EventSession],
                                **dates_times )
                        revision.add_meta( RevisionInfo,
                                as_text = smart_unicode( clone.as_text() ) )
                assert( type( event ) == Event )
                self.mv_mail( number, 'saved' )
                self.stdout.write( smart_str(
                        u'Successfully added new event: ' + event.title ) )
                message = render_to_string( 'mail/email_accepted_event.txt',
                        {'site_name': Site.objects.get_current().name,
                        'site_domain': Site.objects.get_current().domain,
                        'event': event,
                        'original_message': text,} )
                mail = EmailMessage( ''.join( subject.splitlines()),
                        message, from_email, ( to_email, ) )
                mail.send(fail_silently=False)
                transaction.savepoint_commit(sid)
            except (ValidationError, IntegrityError) as err:
                transaction.savepoint_rollback(sid)
                # error found, saving the message in the imap forder 'errors'
                self.mv_mail( number, 'errors' )
                # sending a notification email to the sender {{{3
                if msgobj['Subject'] is not None:
                    subject = \
                        _( u'Validation error in: %(old_email_subject)s' ) \
                        % { 'old_email_subject': \
                        subject.replace( '\n', ' ' ), }
                    subject = subject.replace( '\n', ' ' )
                else:
                    subject = _( u'Validation error' )
                # insert errors message into the email body
                if hasattr( err, 'message_dict' ):
                    # if hasattr(err, 'message_dict'), it looks like:
                    # {'url': [u'Enter a valid value.']}
                    message = render_to_string('mail/email_parsing_errors.txt',
                            {'site_name': Site.objects.get_current().name,
                            'site_domain': Site.objects.get_current().domain,
                            'original_message': text,
                            'errors_dict': err.message_dict})
                    #TODO: write to an error log file instead of stderr
                    self.stderr.write( smart_str(
                        u"Found errors in message with subject: %s\n\terrors: %s" \
                        % ( mail['Subject'], unicode(err.message_dict))))
                elif hasattr( err, 'messages' ):
                    message = render_to_string('mail/email_parsing_errors.txt',
                            {'site_name': Site.objects.get_current().name,
                            'site_domain': Site.objects.get_current().domain,
                            'original_message': text,
                            'errors_list': err.messages})
                    self.stderr.write( smart_str(
                        u"Found errors in message with subject: %s\n\terrors: %s" \
                        % ( mail['Subject'], unicode(err.messages))))
                elif hasattr( err, 'message' ):
                    message = render_to_string('mail/email_parsing_errors.txt',
                            {'site_name': Site.objects.get_current().name,
                            'site_domain': Site.objects.get_current().domain,
                            'original_message': text,
                            'errors_list': [err.message]})
                    self.stderr.write( smart_str(
                        u"Found errors in message with subject: %s\n\terrors: %s" \
                        % ( mail['Subject'], unicode(err.message))))
                else:
                    message = render_to_string('mail/email_parsing_errors.txt',
                            {'site_name': Site.objects.get_current().name,
                            'site_domain': Site.objects.get_current().domain,
                            'original_message': text,
                            'errors_list': []})
                    self.stderr.write( smart_str(
                        u"Found errors in message with subject: %s" \
                        % mail['Subject'] ))
                if subject and message and from_email:
                    mail = EmailMessage( subject, message, \
                                         from_email, ( to_email, ) )
                    msg = str( mail.message() )
                    try:
                        mail.send(fail_silently=False)
                        self.mailbox.append( 'IMAP.sent', None, None, \
                                       msg )
                    except SMTPException:
                        #TODO: write to an error log file instead of stderr
                        self.stderr.write(
                                'imap.py:ERR:smtplib.SMTPException')
                else:
                    #TODO: write to an error log file instead of stderr
                    self.stderr.write(
                            'imap.py:ERR:missing info for error email')

    def mv_mail( self, number, mbox_name ): # {{{2
        '''
        move message to internal mailbox
        @param number: message number in main mailbox
        @param mbox_name: internal mailbox name
        '''
        self.mailbox.copy( number, "INBOX.%s" % mbox_name )
        self.mailbox.store( number, '+FLAGS', '\\Deleted' )
        self.mailbox.expunge()

    def __del__( self, *args, **kwargs ): # {{{2
        if self.mailbox is not None:
            self.mailbox.close()
            self.mailbox.logout()

# setting stdout and stderr {{{1

try:
    getattr( Command, 'stdout' )
except AttributeError:
    Command.stdout = sys.stdout
try:
    getattr( Command, 'stderr' )
except AttributeError:
    Command.stderr = sys.stderr
