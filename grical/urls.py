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
""" Main urls definition file. """
# imports {{{1
from django.conf import settings
import django.contrib.auth.views as auth_views
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls import * # pylint: disable-msg=W0401,W0614,W0614
# previous pylint directive is needed because of a bug in Django:
# http://code.djangoproject.com/ticket/5350

from grical.events import views

# registrations {{{1
admin.autodiscover()

# handler404 and handler500 {{{1
handler404 = views.handler404
handler500 = views.handler500

# patterns for administrations, db and accounts {{{1
urlpatterns = [ 
    url( r'^a/admin/doc/', include( 'django.contrib.admindocs.urls' ) ),
    #(r'^a/admin/(.*)', admin.site.root),
    url( r'^a/admin/', admin.site.urls ),
    url( r'^a/accounts/', include( 'registration.backends.default.urls' ) ),
    url( r'^a/accounts/logout/$',
        auth_views.logout, {'next_page': '/'} ),
 ]

# comments / feedback
# see http://docs.djangoproject.com/en/1.3/ref/contrib/comments/
urlpatterns += [
        url(r'^c/comments/', include('django_comments.urls')),
        url(r'^c/feedback/', include('grical.contact_form.urls')),
 ]

# h pattern for help and legal_notice {{{1
urlpatterns += [
        url( r'^h/help/', views.help_page,
            name = "help" ),
        url( r'^h/legal_notice/', views.legal_notice,
            name = "legal_notice" ),
 ]

# include events.urls {{{1
urlpatterns += [
    url( r'', include( 'grical.events.urls' ) ),
 ]

# see https://docs.djangoproject.com/en/dev/howto/static-files/#serving-static-files-in-development
urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls))
    ]
