#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79

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

""" Irc logger script """

# imports {{{1

import irclib
import os
import time
import thread

from django.core.management import setup_environ
import settings
setup_environ( settings )

# FIXME: avoid loosing the conection to freenet because of Excess Flood

# code {{{1

# creates the pipe and set appropiate permissions
if not os.path.exists( settings.LOG_PIPE ):
    os.mkfifo( settings.LOG_PIPE )
os.chmod( settings.LOG_PIPE, 0660 )
os.chown( settings.LOG_PIPE, os.geteuid(), settings.LOG_PIPE_GID )
# Create an IRC object
# irclib.DEBUG = settings.DEBUG
irclib.DEBUG = True
irc = irclib.IRC()
# Creates a irc server object, connects and joins the channel
server = irc.server()
server.connect(
        settings.IRC_NETWORK, settings.IRC_PORT,
        settings.IRC_NICK, ircname = settings.IRC_NAME )
server.join( settings.IRC_CHANNEL )
# Jump into an infinite loop in a separate thread
thread.start_new_thread( irc.process_forever, tuple() )
# loop reading pipe
with open( settings.LOG_PIPE, 'r' ) as pipe:
    while True:
        for line in pipe.readlines():
            if line and line.strip():
                try:
                    server.privmsg ( settings.IRC_CHANNEL, line )
                except irclib.ServerNotConnectedError:
                    server.connect(
                            settings.IRC_NETWORK, settings.IRC_PORT,
                            settings.IRC_NICK, ircname = settings.IRC_NAME )
                    server.join( settings.IRC_CHANNEL )
                    server.privmsg ( settings.IRC_CHANNEL, line )
            time.sleep( 0.5 )
        time.sleep( 1 )
