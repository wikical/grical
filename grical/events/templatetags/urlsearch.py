#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2011 Ivan F. Villanueva B. <ivan ät wikical.com>
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
""" a custom tag to get the url of complex searches optionally specifying one
or more of the named parameters: tag, country, city, view """

import re

from django import template
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.encoding import smart_str
from django.utils.http import urlencode

register = template.Library()

data = ['query', 'city', 'country', 'tag', 'view']

# see http://docs.djangoproject.com/en/1.3/howto/custom-template-tags/
@register.tag
def urlsearch( parser, token ):
    bits = token.split_contents()
    kwarg_re = re.compile( r"(\w+)=(.*)" )
    asvar = None
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]
    if len( bits ) < 2:
        raise template.TemplateSyntaxError(
                "%r tag requires at least one positional argument" % bits[0] )
    bits = bits[1:]
    kwargs = {}
    for bit in bits:
        match = kwarg_re.match( bit )
        if not match:
            raise TemplateSyntaxError("Malformed arguments to url tag")
        name, value = match.groups()
        if not name in data:
            raise TemplateSyntaxError(
                    "Named argument '%s' is not supported" % name )
        kwargs[name] = parser.compile_filter( value )
    # kwargs is something like:
    # {u'city': <django.template.base.FilterExpression object at
    # 0x7f7e4f08f790>, u'country': <django.template.base.FilterExpression
    # object at 0x7f7e4f08f7d0>}
    return UrlSearchNode( kwargs, asvar )
# urlsearch.is_safe = True

class UrlSearchNode( template.Node ):
    def __init__(self, kwargs, asvar):
        self.kwargs = kwargs
        self.asvar = asvar
    def render( self, context ):
        kwargs = {}
        for k, v in self.kwargs.items():
            real_value = v.resolve( context )
            kwargs[ smart_str(k, 'ascii') ] = real_value
        if not kwargs.has_key('query'):
            kwargs['query'] = ''
        if kwargs.get('tag', False):
            kwargs['query'] += ' #' + unicode( kwargs['tag'] )
            del kwargs['tag']
        if kwargs.has_key('city'):
            if kwargs['city']:
                if kwargs.has_key('country'):
                    if kwargs['country']:
                        kwargs['query'] += \
                                ' @' + kwargs['city'] + ',' + kwargs['country']
                    else:
                        kwargs['query'] += ' @' + kwargs['city']
                    del kwargs['country']
                else:
                    kwargs['query'] += ' @' + kwargs['city']
            del kwargs['city']
        if kwargs.has_key('country'):
            if kwargs['country']:
                kwargs['query'] += ' @' + kwargs['country']
            del kwargs['country']
        # kwargs['query'] = enc( kwargs['query'].strip() )
        kwargs['query'] = kwargs['query'].strip()
        url = reverse( 'search' ) + '?' + \
                urlencode( kwargs ).replace('&','&amp;')
        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url
