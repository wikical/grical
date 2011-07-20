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
""" event search functions """

# imports {{{1
import re
import datetime

from django.contrib.gis.db.models import Q
from django.contrib.gis.measure import D # D is a shortcut for Distance

from tagging.models import Tag, TaggedItem

from gridcalendar.events.utils import search_name
from gridcalendar import settings

# regexes {{{1
DATE_REGEX = re.compile( r'\b(\d\d\d\d)-(\d\d)-(\d\d)\b', re.UNICODE ) #{{{2
COORDINATES_REGEX = re.compile( #{{{2
        r'\s*([+-]?\s*\d+(?:\.\d*)?)\s*[,;:+| ]\s*([+-]?\s*\d+(?:\.\d*)?)' )
EVENT_REGEX = re.compile(r'(?:^|\s)=(\d+)\b', re.UNICODE) #{{{2
# regex.findall('=1234 aa =234 =34')
# ['1234', '234', '34']
GROUP_REGEX = re.compile(r'(?:^|\s)!([-\w]+)\b', re.UNICODE) #{{{2
TAG_REGEX = re.compile(r'(?:^|\s)#([-\w]+)\b', re.UNICODE) #{{{2
SPACE_REGEX = r = re.compile('\s+', re.UNICODE) #{{{2
# LOCATION_REGEX {{{2
# the regex start with @ and has 4 alternatives, examples:
# 52.1234,-0.1234+300km
# 52.1234,-0.1234,53.1234,-0.2345
# london+50mi
# berlin
LOCATION_REGEX = re.compile(r"""
        @(?:                    # loc regex starts with @
        (?:                     # four floats separated by ,
            ([+-]?\d+           #   [0] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
            ,
            ([+-]?\d+           #   [1] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
            ,
            ([+-]?\d+           #   [2] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
            ,
            ([+-]?\d+           #   [3] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
        )|(?:                   # or float,float+int and opt. a unit
            ([+-]?\d+           #   [4] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
            ,\s*                #   spaces because some people copy/paste
            ([+-]?\d+           #   [5] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
            \+(\d+)             #   [6] distance
            (km|mi)?            #   [7] optional unit
        )|(?:                   # or a name, +, distance and opt. unit
            ([^+]+)             #   [8] name
            \+(\d+)             #   [9] distance
            (km|mi)?            #   [10] optional unit
        )|(                     # or just a name
            .+                  #   [11]
        ))""", re.UNICODE | re.X )
# CITY_COUNTRY_RE : city, country (optional) #{{{2
CITY_COUNTRY_RE = re.compile(r'\s*([^,]+)(?:,\s*(.+))?')

def location_restriction( queryset, query ): #{{{1
    """ returns a tuple (a queryset an a string ) restricting ``queryset`` with
    the locations of ``query`` and removing them from ``query`` """
    for loc in LOCATION_REGEX.findall(query):
        if loc[11]:
            # name given, which can have a city, a comma and a country
            city, country = CITY_COUNTRY_RE.findall( loc[11] )[0]
            if not country:
                queryset = queryset.filter(
                    Q( city__iexact = city ) | Q(
                        country__iexact = city ) )
                    # TODO: use also translations of locations and
                    # alternative names
            else:
                queryset = queryset.filter(
                       city__iexact = city, country__iexact = country )
        elif loc[8]:
            point = search_name( loc[8] )
            if loc[10]:
                distance = {loc[10]: loc[9],}
            else:
                distance = { settings.DISTANCE_UNIT_DEFAULT: loc[9],}
            # example: ...filter(coordinates__distance_lte=(pnt, D(km=7)))
            queryset = queryset.filter( coordinates__distance_lte =
                    ( point, D( **distance ) ) )
        elif loc[4]:
            # coordinates given
            point = Point( float(loc[5]), float(loc[4]) )
            if loc[7]:
                distance = {loc[7]: loc[6],}
            else:
                distance = { settings.DISTANCE_UNIT_DEFAULT: loc[6],}
            queryset = queryset.filter( coordinates__distance_lte =
                    ( point, D( **distance ) ) )
        elif loc[0]:
            # We have 4 floats: longitude_west [0], longitude_east [1],
            # latitude_north [2], latitude_south [3]
            lng1 = float( loc[0] )
            lat1 = float( loc[3] )
            lng2 = float( loc[1] )
            lat2 = float( loc[2] )
            rectangle = Polygon( ((lng1, lat1), (lng2,lat1),
                (lng2,lat2), (lng1,lat2), (lng1, lat1)) )
            queryset = queryset.filter( coordinates__within = rectangle )
        else:
            pass
            # TODO: log error
        query = LOCATION_REGEX.sub("", query)
    return queryset, query

def dates_restriction( queryset, query, broad ): #{{{1
    dates = DATE_REGEX.findall( query )
    if dates:
        dates = [ datetime.date( int(year), int(month), int(day) ) for \
                year, month, day in dates ]
        sorted_dates = sorted( dates )
        date1 = sorted_dates[0] # first date
        date2 = sorted_dates[-1] # last date
        queryset = queryset.filter(
               Q( start__range = (date1, date2) )  |
               Q( end__range = (date1, date2) ) |
               Q(deadlines__deadline__range = (date1, date2) ) |
               Q( start__lt = date1, end__gt = date2 ) ) # range in-between
        # remove all dates (yyyy-mm-dd) from the query
        query = DATE_REGEX.sub("", query)
        queryset = queryset.distinct() # needed because deadlines query
    elif not broad:
        today = datetime.date.today()
        queryset = queryset.filter( upcoming__gte = today )
    return queryset, query

def words_restriction( queryset, words, broad, search_in_tags ): #{{{1
    q_filters = None
    for word in words:
        if not word:
            continue
        # NOTE: city needs to be icontains to find e.g. 'washington' in
        # 'Washington D.C.'
        # TODO: search toponims in other languages
        q_word_filters = \
                Q(title__icontains = word) | \
                Q(city__icontains = word) | \
                Q(country__iexact = word) | \
                Q(acronym__icontains = word)
        if search_in_tags:
            q_word_filters |= Q(tags__icontains = word)
        if broad:
            q_word_filters |= \
                    Q( address__icontains = word ) | \
                    Q( description__icontains = word ) | \
                    Q( urls__url_name__icontains = word ) | \
                    Q( urls__url__icontains = word ) | \
                    Q( deadlines__deadline_name__icontains = word ) | \
                    Q( sessions__session_name__icontains = word )
        if not q_filters:
            q_filters = q_word_filters
        else:
            q_filters &= q_word_filters # FIXME: events with partial words are matches, WTF
    return queryset.filter( q_filters )

def tags_restriction( queryset, query ): #{{{1
    tags = TAG_REGEX.findall(query)
    if tags:
        queryset = TaggedItem.objects.get_intersection_by_model(
                queryset, tags )
        query = TAG_REGEX.sub("", query)
    return queryset, query

def search_events( query, related = True ): #{{{1
    # doc {{{2
    """ returns a sorted (by :attr:`models.Event.upcoming`) list of
    distinct events matching ``query`` adding related events if
    *related* is True.

    It can throw a ``ValueError`` if for instance a day is out of range for
    a month in a date, e.g. 2011-04-31.

    If ``query`` evaluates to False, returns an empty QuerySet. E.g. when
    ``query`` is None or an empty string.

    If ``query`` contains `` | `` strings (space, pipe, space), they are
    consider as logical ``or``. Related events are found for each of these
    terms.

    If *related* is True and there is no special restriction (see below) it
    adds to the result events with related tags, but no more that the
    number of results. I.e. if the result contains two events, only a
    miximum of two more related events will be added. If the query contains
    a location term (marked with ``@``), only related events with the same
    location are added. If the query contains a time term (``yyyy-mm-dd``
    or ``yyyy-mm-dd yyyy-mm-dd``), only related events with the same time
    are added.

    Related events are not added if the query contains a group term (marked
    with ``!``), a tag term (marked with ``#``), or an event term (marked with
    ``=``).
    """
    # body {{{2
    # TODO: use .select_related in combination with .only to improve
    # TODO: add full indexing text on Event.description and comments. See
    # http://wiki.postgresql.org/wiki/Full_Text_Indexing_with_PostgreSQL
    # performance.
    from gridcalendar.events.models import Event
    result = Event.objects.none()
    if not query:
        return result
    terms = query.split(' | ')
    # broad search check
    broad_regex = re.compile(r'^\* +', re.UNICODE) # beginninig with * followed
                                                # by 1 ore more spaces
    # searching for each term
    for query in terms:
        groups_match = GROUP_REGEX.findall( query )
        tags_match = TAG_REGEX.findall( query )
        events_match = EVENT_REGEX.findall( query )
        if ( not related ) or groups_match or tags_match or events_match:
            related = False
        else:
            related = True
        if broad_regex.match( query ):
            broad = True
            query = broad_regex.sub("", query)
        else:
            broad = False
        queryset = Event.objects.all()
        # single events
        for event_id in events_match:
            queryset = queryset.filter( pk = event_id )
            broad = True # '=' show past events too
        query = EVENT_REGEX.sub("", query)
        # groups
        for group_name in GROUP_REGEX.findall( query ):
            queryset = queryset.filter(
                    calendar__group__name__iexact = group_name)
        query = GROUP_REGEX.sub("", query)
        # locations
        queryset, query = location_restriction( queryset, query )
        # tags
        queryset, query = tags_restriction( queryset, query )
        # dates
        queryset, query = dates_restriction( queryset, query, broad )
        if not query.strip():
            result = result | queryset
            continue
        # remaining unique words
        words_set = set( SPACE_REGEX.split( query ) )
        queryset_with_words_restriction = words_restriction(
                queryset, list( words_set ), broad, True )
        if not related:
            result = result | queryset_with_words_restriction
        else:
            related_tags = set()
            for tag in list( words_set ):
                try:
                    tag = Tag.objects.get( name = tag )
                    related_tags.update( Tag.objects.related_for_model(
                        tag, Event, counts = False ) )
                except Tag.DoesNotExist:
                    pass
            related_tags.difference_update( words_set )
            related_events = TaggedItem.objects.get_union_by_model(
                        queryset, # NOTE we use all the restrictions here
                        [ tag.name for tag in related_tags ] )
            result = result | related_events | queryset_with_words_restriction
    return result.order_by('upcoming').distinct()


# better old related algorithm but too slow {{{1
    #related_tags = sorted( used_tags, key = lambda t: t.count )
    #related_tags.reverse()
    # used_tags contains the count of all tags present in queryset,
    # example:
    # used_tags = Tag.objects.usage_for_queryset( queryset, counts=True )
    # [<Tag: linux>, <Tag: floss>, <Tag: foss>, <Tag: free-software>, ...
    # used_tags[0].count
    # 69
    #used_tags = sorted( used_tags, key = lambda t: t.count )
    #used_tags.reverse()
    # Now we will use related_for_model. Examples:
    # Tag.objects.related_for_model( used_tags[0:5], Event, counts=True )
    # [<Tag: open-source>, <Tag: freedom>, <Tag: ubuntu> ...
    # We will use the related tags to the 5 most used tags. TODO: 5 is best?
    # tags = list() # we save here the tags that we will use at the end
    # we save here the ids of the events already in queryset
    # present_ids = set( queryset.values_list( 'id', flat=True ) )
    #for nr_of_tags in [6,5,4,3,2,1]:
    #    related_tags = Tag.objects.related_for_model(
    #            used_tags[ 0 : nr_of_tags ], Event, counts = True )
    #    if len( related_tags ) == 0:
    #        continue
    #    related_tags = sorted( related_tags, key = lambda t: t.count )
    #    related_tags.reverse()
    #    # we now find events with 1 of the
    #    # tags, which are in 'restricted' but not in 'queryset'
    #    # TODO: try to find first events with many related_tags
    #    for tag in related_tags:
    #        restricted_with_tag = \
    #                TaggedItem.objects.get_by_model( restricted, tag )
    #        not_in_queryset = restricted_with_tag.exclude(
    #                id__in = present_ids )
    #        if not_in_queryset.exists():
    #            return not_in_queryset
    #return Event.objects.none()
