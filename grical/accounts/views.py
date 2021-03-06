#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2016 Ivan F. Villanueva B. <ivan ät wikical.com>
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

# docs {{{1
""" VIEWS """

# imports {{{1
from django.contrib import messages
from django.contrib.sites.models import Site
from django.shortcuts import render
from django.utils.translation import ugettext as _

def csrf_failure(request, reason=""): # {{{1
    # TODO: log the reason (which is not intended to end users)
    messages.error( request, _('Error.') )
    return render(request, 'accounts/cookies_not_enabled.html', {
            'title': Site.objects.get_current().name + \
                    ' - ' + _( 'cookies not enabled' )})
