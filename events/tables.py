#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker ft=python
# gpl {{{1
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

# docs {{{1

""" Events tables """

# imports {{{1
from django.utils.translation import ugettext as _

from django_tables import MemoryTable, Column

# TODO: MemoryTable is not scalable, change it to a queryset table
class EventTable(MemoryTable): # {{{1
    upcoming = Column( verbose_name = _( u"upcoming") )
    start = Column( verbose_name = _( u"start date" ) )
    city = Column( verbose_name = _( u"city" ), default = '' )
    country = Column( verbose_name = _( "country" ), default = '' )
    title = Column( verbose_name = _( "title" ) )
    tags = Column(
            verbose_name = _( "tags" ), sortable = False, default = '' )
    id = Column( sortable = False, visible = False )

    @staticmethod
    def convert(event_list): # {{{2
        """ converts a list of events to a list of dictionaries.

        See http://elsdoerfer.name/docs/django-tables/#indices-and-tables
        """
        lis = list()
        for event in event_list:
            dic = dict()
            dic['upcoming'] = \
                    event.upcoming
            dic['start'] = event.start
            if event.city:
                dic['city'] = event.city
            if event.country:
                dic['country'] = event.country
            dic['title'] = event.title
            dic['tags'] = event.tags
            dic['id'] = event.id
            lis.append( dic )
        return lis
