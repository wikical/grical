#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2012 Ivan F. Villanueva B. <ivan ät wikical.com>
#
# This file is part of GriCal.
#
# GriCal is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# GriCal is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GriCal. If not, see <http://www.gnu.org/licenses/>.
#############################################################################
""" A management command which deletes expired group invitations from the
    database. """

from django.conf import settings
from django.core.management.base import BaseCommand
from grical.events.models import GroupInvitation

class Command(BaseCommand):
    """ A management command which deletes expired group invitations from the
    database.

    Calls ``GroupInvitation.objects.delete_expired_invitations()``, which
    contains the actual logic for determining which invitations are deleted.
    """

    help = "Delete expired group invitations from the database"

    def handle(self, *args, **options):
        """ Executes the action, or do nothing if settings.READ_ONLY is True.
        """
        if settings.READ_ONLY == True:
            return
        GroupInvitation.objects.delete_expired_invitations()
