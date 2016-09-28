#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2016 Stefanos Kozanis <stefanos ät wikical.com>
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
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

def only_if_write_enabled(func):
    """decorator for view functions that disable the view and redirects to the
    main page if ``settings.READ_ONLY`` is True
    """
    def closure(request, *args, **kwargs):
        if settings.READ_ONLY:
            messages.info(request, _("Currently it is not possible to enter" \
                    " or edit any data. Please wait a few minutes and then " \
                    "try again."))
            return HttpResponseRedirect(reverse('main'))
        return func( request, *args, **kwargs )

    return closure
