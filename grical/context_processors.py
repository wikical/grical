# -*- encoding: utf-8 -*-
""" Adds variables to all templates """
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009-2011 Ivan Villanueva <ivan ät gridmind.org>
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


# This file is needed for example for:
# return render_to_response( ... , context_instance=RequestContext(request))

# TODO: think of (also) using TEMPLATE_CONTEXT_PROCESSORS =
# ('django.core.context_processors.request',)

from django.contrib.sites.models import Site
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

from grical.events.models import Event, Group
from grical.events.models import ExtendedUser

def global_template_vars(request):
    """
    Adds variables to all templates.

    It uses memcached to minimize hitting the db.
    """
    def get_user():
        if request.user.is_authenticated():
            return ExtendedUser.objects.get( id = request.user.id )
        else:
            return None
    vars_funcs = {
            'SITE_NAME':    lambda: Site.objects.get_current().name,
            'SITE_DOMAIN':  lambda: Site.objects.get_current().domain,
            'USERS_NR':     lambda: User.objects.count(),
            'EVENTS_NR':    lambda: Event.objects.count(),
            'GROUPS_NR':    lambda: Group.objects.count(), }
            # protocol  (computed below)
    vars_dic = cache.get_many( vars_funcs.keys() )
    if not vars_dic:
        vars_dic = {}
        # we get the values
        for key, func in vars_funcs.items():
            vars_dic[ key ] = func()
        # we put the values in the cache
        cache.set_many( vars_dic )
    # we add protocol
    if request.is_secure():
        vars_dic['PROTOCOL'] = "https"
    else:
        vars_dic['PROTOCOL'] = "http"
    vars_dic['VERSION'] = settings.VERSION
    vars_dic['MEDIA_URL'] = settings.MEDIA_URL
    # TODO: think on the trick to get the user out of a signed Django-1.4 cookie
    vars_dic['USER'] = get_user()
    vars_dic['READ_ONLY'] = settings.READ_ONLY
    # return
    return vars_dic
