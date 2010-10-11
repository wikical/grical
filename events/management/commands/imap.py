#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2010 Adam Beret Manczuk <beret@hipisi.org.pl>,
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

"""recive events from imap mailbox"""


import sys
from imaplib import IMAP4
import email
from email.header import decode_header
from email.parser import Parser as EmailParser
from smtplib import SMTPException
from StringIO import StringIO
# from base64 import b64decode
# from email.utils import parseaddr

# from django import template
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_str
from django.core.management.base import NoArgsCommand
from django.forms import ValidationError

from gridcalendar.events.models import Event


#TODO: set the Django language to the first possible language the email sender
# accepts (from the Accept-Language header). If there is no such header use the
# first possible value of the Content-Language header. If not present default
# to English

class Command( NoArgsCommand ):
    """ A management command which parses mails from imap server..
    """

    help = "Parse mails from settings.IMAP_SERVER"

    def __init__( self, *args, **kwargs ):
        # TODO: use IMAP4_SSL
        self.mailbox = IMAP4( settings.IMAP_SERVER )
        self.mailbox.login( settings.IMAP_LOGIN, settings.IMAP_PASSWD )
        self.mailbox.select()
        super( Command, self ).__init__( *args, **kwargs )

    def get_list( self ):
        '''
        get list of message's numbers in main mailbox
        '''
        #TODO: think if this would work when the mailbox is changed while
        # this code is running
        typ, data = self.mailbox.search( None, 'ALL' )
        nr_list = data[0].split( ' ' )
        if len( nr_list ) == 1 and nr_list[0] == '':
            return []
        else:
            return nr_list

    def handle_noargs( self, **options ):
        """ Executes the action. """
        self.parse()

    def parse( self ):
        '''
        parse all mails from imap mailbox
        '''
        #re_charset = re.compile( r'charset=([^\s]*)', re.IGNORECASE )
        for number in self.get_list():
            typ, data = self.mailbox.fetch( number, '(RFC822 UID BODY[TEXT])' )
            if (not data) or len( data ) < 1 :
                return
            mail = email.message_from_string( data[0][1] )
            text = u""
            msgobj = EmailParser().parse( StringIO( mail ), False )
            for part in msgobj.walk():
                if part.get_content_type() == "text/plain":
                    text += unicode( 
                                    part.get_payload( decode = True ),
                                    part.get_content_charset(),
                                    'replace'
                                    )
            try:
                event = Event.parse_text( text )
                assert( type( event ) == Event )
                self.mv_mail( number, 'saved' )
                self.stdout.write( smart_str(
                        u'Successfully added new event: ' + event.title ) )
            except ValidationError as error:
                # at the moment (Oct 11 2010) Event.parse_text returns only one
                # error message, but in the future it could return more
                errors = error.messages
                self.mv_mail( number, 'errors' )
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
                    subject = \
                        _( u'Validation error in: %(old_email_subject)s') \
                        % { 'old_email_subject': \
                        subject.replace( '\n', ' ' ), }
                    subject = subject.replace( '\n', ' ' )
                else:
                    subject = _( u'Validation error' )
                #insert errors message into mail
                # TODO: create the message from a template in
                # templates/mail
                message = '\n'.join( errors )
                #add parsed text on the end of mail
                message = "%s\n\n==== Original message ====\n%s" % \
                        ( message, text )
                #TODO: write to an error log file instead of stderr
                self.stderr.write( smart_str( \
                                _( "Found errors in message %s: \n%s\n" \
                                     % ( mail['Subject'], message ) ) ) )
                to_email = mail['From']
                from_email = settings.DEFAULT_FROM_EMAIL
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

        rest = self.get_list()
        if len( rest ) > 0 :
            return self.parse()

    def mv_mail( self, number, mbox_name ):
        '''
        move message to internal mailbox
        @param number: message number in main mailbox
        @param mbox_name: internal mailbox name
        '''
        self.mailbox.copy( number, "INBOX.%s" % mbox_name )
        self.mailbox.store( number, '+FLAGS', '\\Deleted' )
        self.mailbox.expunge()

    def __del__( self, *args, **kwargs ):
        self.mailbox.close()
        self.mailbox.logout()

try:
    getattr( Command, 'stdout' )
except AttributeError:
    Command.stdout = sys.stdout
try:
    getattr( Command, 'stderr' )
except AttributeError:
    Command.stderr = sys.stderr
