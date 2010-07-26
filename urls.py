#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Main urls definition file. """
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009, 2010 Iván F. Villanueva B. <ivan ät gridmind.org>
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
# FITNESS FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

from django.conf import settings
from django.conf.urls.defaults import patterns, include, url, include
from django.contrib import admin, databrowse
from django.conf.urls.defaults import * # pylint: disable-msg=W0401,W0614,W0614
# previous pylint directive is needed because of a bug in Django:
# http://code.djangoproject.com/ticket/5350

# databrowse.site.register(Event)
# databrowse.site.register(Group)
# databrowse.site.register(EventUrl)
# databrowse.site.register(EventSession)
# databrowse.site.register(EventDeadline)

admin.autodiscover()

urlpatterns = patterns('', # pylint: disable-msg=C0103
    (r'^a/admin/doc/', include('django.contrib.admindocs.urls')),
    #(r'^a/admin/(.*)', admin.site.root),
    (r'^a/admin/', admin.site.urls),
    (r'^a/db/(.*)', databrowse.site.root),
    (r'^a/accounts/', include('registration.urls')),
    (r'^a/accounts/logout/$',
        'django.contrib.auth.views.logout', {'next_page': '/'}),
)

urlpatterns += patterns('',
        url(r'^h/help/', 'gridcalendar.events.views.usage', name="help"),
        url(r'^h/legal_notice/', 'gridcalendar.events.views.legal_notice',
                name="legal_notice"),
)

#urlpatterns += patterns('',
#    (r'^comments/', include('django.contrib.comments.urls')),
#)

urlpatterns += patterns('',
    (r'', include('events.urls')),
)

# see http://docs.djangoproject.com/en/1.0/howto/static-files/
if settings.DEBUG:
    urlpatterns += patterns('',
        (
            '^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True},
        ),
    )
