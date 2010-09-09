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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the Affero GNU Generevent.idal Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""recive events from imap mailbox"""


from imaplib import IMAP4
import email
import re
import sys
from email.Header import decode_header
from base64 import b64decode
from email.Parser import Parser as EmailParser
from email.utils import parseaddr

from StringIO import StringIO

from django.conf import settings
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext_lazy as _
from django.core.management.base import NoArgsCommand

from gridcalendar.events.models import Event

from subprocess import Popen, PIPE

from django import template

register = template.Library()

@register.filter
def html2text( value ):
    """
    Pipes given HTML string into the text browser W3M, which renders it.
    Rendered text is grabbed from STDOUT and returned.
    """
    try:
        cmd = "w3m -dump -T text/html -O ascii"
        proc = Popen( cmd, shell = True, stdin = PIPE, stdout = PIPE )
        return proc.communicate( str( value ) )[0]
    except OSError:
        # something bad happened, so just return the input
        return value


class Command( NoArgsCommand ):
    """ A management command which Parse mails from imap server..
    """

    help = "Parse mails from imap server"

    def __init__( self, *args, **kwargs ):
        self.mailbox = IMAP4( settings.IMAP_SERVER )
        self.mailbox.login( settings.IMAP_LOGIN, settings.IMAP_PASSWD )
        self.mailbox.select()
        super( Command, self ).__init__( *args, **kwargs )

    def get_list( self ):
        '''
        get list of message's numbers in main mailbox
        '''
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
        re_charset = re.compile( r'charset=([^\s]*)', re.IGNORECASE )
        for number in self.get_list():
            typ, data = self.mailbox.fetch( number, '(RFC822 UID BODY[TEXT])' )
            if data and len( data ) > 1:
                mail = email.message_from_string( data[0][1] )
                text = ""
                p = EmailParser()
                msgobj = p.parse( StringIO( mail ), False )
                for part in msgobj.walk():
                    if part.get_content_type() == "text/plain":
                        text += unicode( 
                                        part.get_payload( decode = True ),
                                        part.get_content_charset(),
                                        'replace'
                                        )
                event = Event.parse_text( text )
                if type( event ) == Event :
                    self.mv_mail( number, 'saved' )
                    self.stdout.write( 'Successfully add new event: %s\n' \
                                       % event.title )
                else:
                    errors = event
                    self.mv_mail( number, 'errors' )
                    if msgobj['Subject'] is not None:
                        decodefrag = decode_header( msgobj['Subject'] )
                        subj_fragments = []
                        for s , enc in decodefrag:
                            if enc:
                                s = unicode( s , enc ).encode( 'utf8', \
                                                               'replace' )
                            subj_fragments.append( s )
                        subject = ''.join( subj_fragments )
                        subject = _( 'Validation error in: %s' % \
                                 subject.replace( '\n', ' ' ) )
                        subject = subject.replace( '\n', ' ' )
                    else:
                        subject = _( 'Validation error' )
                    #insert errors message into mail
                    message = '\n'.join( map( \
                                            lambda x: \
                                                html2text( \
                                                    '\n'.join( x.messages ) ), \
                                            errors ) )
                    #add parsed text on the end of mail
                    message = "%s\n\n==== Orginal message ===\n%s" % \
                            ( message, text )
                    self.stderr.write( "Found errors in message %s: \n%s\n" % \
                                      ( mail['Subject'], message ) )
                    to_email = mail['From']
                    from_email = settings.DEFAULT_FROM_EMAIL
                    if subject and message and from_email:
                        mail = EmailMessage( subject, message, \
                                             from_email, ( to_email, ) )
                        msg = str( mail.message() )
                        mail.send()
                        self.mailbox.append( 'IMAP.sent', None, None, \
                                       msg )

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
except:
    Command.stdout = sys.stdout
try:
    getattr( Command, 'stderr' )
except:
    Command.stderr = sys.stderr
