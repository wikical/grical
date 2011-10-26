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
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

import sys

from django.core.management.base import NoArgsCommand
from django.db import transaction
from django.utils.encoding import smart_unicode

from reversion.models import Version

from gridcalendar.events.models import Event, RevisionInfo

class Command( NoArgsCommand ): # {{{1
    """ management command """
    help = "add RevisionInfo provided there is only one version for each event"
    @transaction.commit_on_success # see http://docs.djangoproject.com/en/1.3/topics/db/transactions/#controlling-transaction-management-in-views
    def handle_noargs( self, **options ): # {{{2
        events = Event.objects.all()
        count = 0
        for event in events:
            version_list = Version.objects.get_for_object(event)
            assert version_list, 'event %d has no versions' % event.id
            assert len( version_list ) == 1, \
                    'event %d has more than one version' % event.id
            version = version_list[0]
            revision = version.revision
            infos = revision.revisioninfo_set.all()
            if not infos:
                RevisionInfo.objects.create( revision = revision, as_text =
                        smart_unicode( event.as_text() ) )
                count = count + 1
            else:
                assert len( infos ) == 1, \
                        'event %d has more than one RevisionInfo' % event.id
                assert infos[0].as_text == smart_unicode( event.as_text() ), \
                        'event %d has already a RevisionInfo' % event.id
        print "created %d RevisionInfo records" % count

# setting stdout and stderr {{{1
try:
    getattr( Command, 'stdout' )
except AttributeError:
    Command.stdout = sys.stdout
try:
    getattr( Command, 'stderr' )
except AttributeError:
    Command.stderr = sys.stderr
