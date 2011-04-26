#!/usr/bin/env python
# -*- coding: utf-8 -*-
# GPL {{{1
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2011 Ivan Villanueva <iv@gridmind.org>
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

# doc {{{1
""" updates :attr:`events.models.Event.upcoming` for all events with some date
in the future and :attr:`events.models.Event.upcoming` in the past """

# imports {{{1
import datetime
import sys
from django.contrib.gis.db.models import F, Q
from django.core.management.base import NoArgsCommand
from gridcalendar.events.models import Event, EventDeadline

class Command( NoArgsCommand ): # {{{1
    """ management command """
    # tests are in events.tests

    help = "Parses mails from settings.IMAP_SERVER"

    def handle_noargs( self, **options ): # {{{2
        """ Executes the action. """
        today = datetime.date.today()
        # we update events with one date in the future
        queryset = Event.objects.filter(
                Q( start__gte = today ) | Q( end__gte = today ) |
                Q( deadlines__deadline__gte = today ) )
        queryset = queryset.filter( upcoming__lt = today )
        for event in queryset.distinct():
            event.save()
        # update events with all dates in the past but
        # :attr:`events.models.Event.upcoming` is not
        # :attr:`events.models.Event.start`
        queryset = Event.objects.filter(
                Q( start__lt = today ) &
                ( Q( end__isnull = True ) | Q( end__lt = today ) ) &
                ( Q( deadlines__deadline__isnull = True ) |
                    Q( deadlines__deadline__lt = today ) ) &
                ~Q( upcoming = F( 'start' ) ) )
        for event in queryset.distinct():
            event.save()

# setting stdout and stderr {{{1
try:
    getattr( Command, 'stdout' )
except AttributeError:
    Command.stdout = sys.stdout
try:
    getattr( Command, 'stderr' )
except AttributeError:
    Command.stderr = sys.stderr
