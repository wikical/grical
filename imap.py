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
from gridcalendar.events.models import Event
from django.conf import settings
import email
from django.core.mail import send_mail

class Mailbox:
    def __init__( self, name = 'INBOX' ):
        self.M = IMAP4( settings.IMAP_SERVER )
        self.M.login( settings.IMAP_LOGIN, settings.IMAP_PASSWD )
        self.M.select( name )

    def __iter__( self ):

        typ, data = self.M.search( None, 'ALL' )
        for nr in data[0].split():
            typ, data = self.M.fetch( nr, '(RFC822 UID BODY[TEXT])' )
            mail = email.message_from_string( data[0][1] )
            text = data[1][1]
            event = Event.parse_text( text )
            if type( event ) == Event :
                self.mv_mail( nr, 'saved' )
                yield event
            else:
                errors = event
                self.mv_mail( nr, 'errors' )
                subject = _( 'Validation error in: %s' % mail['Subject'] )
                message = '\n\n'.join( errors )
                to_email = mail['From']
                from_email = settings.DEFAULT_FROM_EMAIL
                if subject and message and from_email:
                    try:
                        send_mail( subject, message, from_email, to_email )
                    except:
                        pass


    def mv_mail( self, nr, mbox_name ):
        self.M.copy( nr, "INBOX.%s" % mbox_name )
        self.M.store( nr, '+FLAGS', '\\Deleted' )
        self.M.expunge()

    def __del__( self ):
        self.M.close()
        self.M.logout()

if __name__ == '__main__':
    m = Mailbox()
    for event in m:
        print event.title
