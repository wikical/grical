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
""" event search functions """

# imports {{{1
import re
import datetime

from django.contrib.gis.db.models import Q
from django.contrib.gis.measure import D # D is a shortcut for Distance
from django.contrib.gis.geos import Point, Polygon
from django.conf import settings

from grical.tagging.models import Tag, TaggedItem

from grical.events.models import Event, EventDate
from grical.events.utils import search_name

# regexes {{{1
DATE_REGEX = re.compile( r'\b(\d\d\d\d)-(\d?\d)-(\d?\d)\b', re.UNICODE ) #{{{2
COORDINATES_REGEX = re.compile( #{{{2
        r'\s*([+-]?\s*\d+(?:\.\d*)?)\s*[,;:+| ]\s*([+-]?\s*\d+(?:\.\d*)?)' )
EVENT_REGEX = re.compile(r'(?:^|\s)=(\d+)\b', re.UNICODE) #{{{2
# regex.findall('=1234 aa =234 =34')
# ['1234', '234', '34']
GROUP_REGEX = re.compile(r'(?:^|\s)!([-\w]+)\b', re.UNICODE) #{{{2
TAG_REGEX = re.compile(r'(?:^|\s)#([-\w]+)\b', re.UNICODE) #{{{2
EXCLUSION_REGEX = re.compile(r'(?:^|\s)-([#@]?[-\w]+)\b', re.UNICODE) #{{{2
SPACE_REGEX = re.compile(r'\s+', re.UNICODE) #{{{2
# CONTINENT_REGEX {{{2
CONTINENT_REGEX = re.compile(r'(?:^|\s)@@(\w\w)\b', re.UNICODE) #{{{2
# LOCATION_REGEX {{{2
# the regex starts optionally with @ (in last 2 alternatives compulsory)
# and has 4 alternatives, examples:
# 52.1234,-0.1234+300km
# 52.1234,-0.1234,53.1234,-0.2345
# london+50mi
# berlin
LOCATION_REGEX = re.compile(r"""
        @?(?:                   # four floats separated by ,
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
        )|@?(?:                 # or float,float+int and opt. a unit
            ([+-]?\d+           #   [4] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
            ,\s*                #   spaces because some people copy/paste
            ([+-]?\d+           #   [5] one or more digits
                (?:\.\d*)?)     #   optionally . or . and decimals
            \s*[ +]             #   optionally spaces or +
            (\d+)               #   [6] distance (optional +)
            \s*                 #   optionally spaces
            (km|mi)?            #   [7] optional unit
        )|@(?:                 # or a name, +, distance and opt. unit
            ([^+]+)             #   [8] name
            \+(\d+)             #   [9] distance
            (km|mi)?            #   [10] optional unit
        )|@(                    # or just a name (@ is compulsory)
            .+                  #   [11]
        )""", re.UNICODE | re.X )
# CITY_COUNTRY_RE : city, country (optional) #{{{2
CITY_COUNTRY_RE = re.compile(r'\s*([^,]+)(?:,\s*(.+))?')

class GeoLookupError( Exception ): # {{{1
    """ exception raises when no coordinates can be looked up for a given name
    """
    pass
class ContinentLookupError( Exception ): # {{{1
    """ exception raises when no continent can be looked up for a given name
    """
    pass

def continent_restriction( queryset, query ): #{{{1
    """ returns a tuple (a queryset an a string ) restricting ``queryset`` with
    the continent of ``query`` and removing them from ``query`` """
    for loc in CONTINENT_REGEX.findall(query):
        from grical.data.models import (ContinentBorder,
                CONTINENT_COUNTRIES)
        continent = loc.upper()
        try:
            mpoly = ContinentBorder.objects.get(code=continent).mpoly
            # TODO: also use names in different languages using
            # data.models.CONTINENTS
            # Example: @@europa
        except ContinentBorder.DoesNotExist:
            raise ContinentLookupError()
        countries = CONTINENT_COUNTRIES[continent]
        if queryset.model == Event:
            queryset = queryset.filter(
                    Q(coordinates__contained = mpoly) |
                    Q(country__in = countries))
        else:
            queryset = queryset.filter(
                    Q(event__coordinates__contained = mpoly) |
                    Q(event__country__in = countries))
        query = CONTINENT_REGEX.sub("", query)
    return queryset, query

def exclusion( queryset, query ): #{{{1
    """ returns a tuple (a queryset an a string ) restricting ``queryset``
    excluding events if ``query`` contains expressions starting with ``-``
    """
    for word in EXCLUSION_REGEX.findall(query):
        if queryset.model == Event:
            if word[0] == '#':
                if len(word) == 1:
                    # it is only '-#', we exclude all tagged events
                    exclusion_q = Q(tags__isnull = False)
                else:
                    exclusion_q = Q(tags__icontains = word[1:])
            elif word[0] == '@':
                if len(word) == 1:
                    # it is only '-@', we exclude all located events
                    exclusion_q = \
                            Q(city__isnull = False) | \
                            Q(country__isnull = False) | \
                            Q(coordinates__isnull = False) | \
                            Q(address__isnull = False)
                else:
                    exclusion_q = \
                            Q(city__icontains = word[1:]) | \
                            Q(country__icontains = word[1:])
            else:
                exclusion_q = \
                    Q(title__icontains = word) | \
                    Q(city__icontains = word) | \
                    Q(country__iexact = word) | \
                    Q(acronym__icontains = word) | \
                    Q(tags__icontains = word)
        else:
            assert queryset.model == EventDate
            if word[0] == '#':
                if len(word) == 1:
                    # it is only '-#', we exclude all tagged events
                    exclusion_q = Q(event__tags__isnull = False)
                else:
                    exclusion_q = Q(event__tags__icontains = word[1:])
            elif word[0] == '@':
                if len(word) == 1:
                    # it is only '-@', we exclude all located events
                    exclusion_q = \
                            Q(event__city__isnull = False) | \
                            Q(event__country__isnull = False) | \
                            Q(event__coordinates__isnull = False) | \
                            Q(event__address__isnull = False)
                else:
                    exclusion_q = \
                            Q(event__city__icontains = word[1:]) | \
                            Q(event__country__icontains = word[1:])
            else:
                exclusion_q = \
                    Q(event__title__icontains = word) | \
                    Q(event__city__icontains = word) | \
                    Q(event__country__iexact = word) | \
                    Q(event__acronym__icontains = word) | \
                    Q(event__tags__icontains = word)
        queryset = queryset.exclude(exclusion_q)
        query = EXCLUSION_REGEX.sub("", query)
    return queryset, query

def location_restriction( queryset, query ): #{{{1
    """ returns a tuple (a queryset an a string ) restricting ``queryset`` with
    the locations of ``query`` and removing them from ``query`` """
    for loc in LOCATION_REGEX.findall(query):
        if loc[11]: # name or name,name
            # name given, which can have a city, a comma and a country
            city, country = CITY_COUNTRY_RE.findall( loc[11] )[0]
            if not country:
                if queryset.model == Event:
                    queryset = queryset.filter(
                        Q( city__iexact = city ) | Q(
                            country__iexact = city ) )
                        # TODO: use also translations of locations and
                        # alternative names
                else:
                    queryset = queryset.filter(
                        Q( event__city__iexact = city ) | Q(
                            event__country__iexact = city ) )
            else:
                result = search_name( city + ', ' + country )
                if result:
                    point = result.get('coordinates', None)
                else:
                    point = None
                distance = { settings.DISTANCE_UNIT_DEFAULT:
                        settings.CITY_RADIUS, }
                if queryset.model == Event:
                    if point:
                        # example: ...coordinates__distance_lte=(pnt, D(km=7)))
                        queryset = queryset.filter(
                           Q( city__iexact=city, country__iexact=country ) |
                           Q( coordinates__distance_lte =
                            ( point, D( **distance ) ) ) )
                    else:
                        queryset = queryset.filter(
                           city__iexact = city, country__iexact = country )
                else:
                    if point:
                        queryset = queryset.filter(
                           Q( event__city__iexact = city,
                               event__country__iexact = country ) |
                           Q( event__coordinates__distance_lte =
                                ( point, D( **distance ) ) ) )
                    else:
                        queryset = queryset.filter(
                           event__city__iexact = city,
                           event__country__iexact = country )
        elif loc[8]: # name + distance + optional unit
            result = search_name( loc[8] )
            if result:
                point = result.get('coordinates', None)
            else:
                point = None
            if not point:
                raise GeoLookupError()
            if loc[10]:
                distance = {loc[10]: loc[9],}
            else:
                distance = { settings.DISTANCE_UNIT_DEFAULT: loc[9],}
            # example: ...filter(coordinates__distance_lte=(pnt, D(km=7)))
            if queryset.model == Event:
                queryset = queryset.filter(
                        coordinates__distance_lte =
                            ( point, D( **distance ) ) )
            else:
                queryset = queryset.filter(
                        event__coordinates__distance_lte =
                            ( point, D( **distance ) ) )
        elif loc[4]:
            # coordinates given
            point = Point( float(loc[5]), float(loc[4]) )
            if loc[7]:
                distance = {loc[7]: loc[6],}
            else:
                distance = { settings.DISTANCE_UNIT_DEFAULT: loc[6],}
            if queryset.model == Event:
                queryset = queryset.filter(
                        coordinates__distance_lte =
                            ( point, D( **distance ) ) )
            else:
                queryset = queryset.filter(
                        event__coordinates__distance_lte =
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
            if queryset.model == Event:
                queryset = queryset.filter(
                        exact = True,
                        coordinates__within = rectangle )
            else:
                queryset = queryset.filter(
                        event__exact = True,
                        event__coordinates__within = rectangle )
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
        if queryset.model == Event:
            queryset = queryset.filter(
                    dates__eventdate_date__range = (date1, date2) )
        else:
            queryset = queryset.filter(
                    eventdate_date__range = (date1, date2) )
        # remove all dates (yyyy-mm-dd) from the query
        query = DATE_REGEX.sub("", query)
    elif not broad:
        today = datetime.date.today()
        if queryset.model == Event:
            queryset = queryset.filter( dates__eventdate_date__gte = today )
        else:
            queryset = queryset.filter( eventdate_date__gte = today )
    return queryset, query

def words_restriction( queryset, words, broad, search_in_tags ): #{{{1
    if not words:
        return queryset
    q_filters = None
    for word in words:
        if not word:
            continue
        # NOTE: city needs to be icontains to find e.g. 'washington' in
        # 'Washington D.C.'
        # TODO: search toponyms in other languages
        if queryset.model == Event:
            q_word_filters = \
                    Q(title__icontains = word) | \
                    Q(city__icontains = word) | \
                    Q(country__iexact = word) | \
                    Q(acronym__icontains = word)
        else:
            q_word_filters = \
                    Q(event__title__icontains = word) | \
                    Q(event__city__icontains = word) | \
                    Q(event__country__iexact = word) | \
                    Q(event__acronym__icontains = word)
        if search_in_tags:
            if queryset.model == Event:
                q_word_filters |= Q(tags__icontains = word)
            else:
                q_word_filters |= Q(event__tags__icontains = word)
        if broad:
            if queryset.model == Event:
                q_word_filters |= \
                        Q( address__icontains = word ) | \
                        Q( description__icontains = word ) | \
                        Q( urls__url_name__icontains = word ) | \
                        Q( urls__url__icontains = word ) | \
                        Q( dates__eventdate_name__icontains = word ) | \
                        Q( sessions__session_name__icontains = word )
            else:
                q_word_filters |= \
                        Q( event__address__icontains = word ) | \
                        Q( event__description__icontains = word ) | \
                        Q( event__urls__url_name__icontains = word ) | \
                        Q( event__urls__url__icontains = word ) | \
                        Q( event__dates__eventdate_name__icontains = word ) | \
                        Q( event__sessions__session_name__icontains = word )
        if not q_filters:
            q_filters = q_word_filters
        else:
            q_filters &= q_word_filters # FIXME: events with partial words are matches, WTF
    return queryset.filter( q_filters )

def tags_restriction( queryset, query ): #{{{1
    tags = TAG_REGEX.findall(query)
    if tags:
        if queryset.model == Event:
            queryset = TaggedItem.objects.get_intersection_by_model(
                    queryset, tags )
        else:
            # TODO: inefficient, improve:
            for tag in tags:
                queryset &= queryset.filter( event__tags__icontains = tag )
        query = TAG_REGEX.sub("", query)
    return queryset, query

def search_events( query, related = True, model = Event ): #{{{1
    # doc {{{2
    """ returns a sorted (by :attr:`models.Event.upcoming`) list of
    distinct events matching ``query`` adding related events if
    *related* is True.

    It can throw a ``ValueError`` if for instance a day is out of range for
    a month in a date, e.g. 2011-04-31. Also if for instance the location API
    didn't work.

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
    # TODO: add full indexing text on Event.description and comments. See
    # http://wiki.postgresql.org/wiki/Full_Text_Indexing_with_PostgreSQL
    # performance.
    assert ( model == Event ) | ( model == EventDate )
    result = model.objects.none()
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
        if model == EventDate:
            queryset = EventDate.objects.select_related().defer(
                'event__description', 'event__coordinates',
                'event__creation_time', 'event__modification_time',
                'event__address')
        else:
            queryset = Event.objects.all()
        # exclusion
        queryset, query = exclusion(queryset, query)
        # single events
        for event_id in events_match:
            if model == Event:
                queryset = queryset.filter( pk = event_id )
            else: # model is EventDate
                queryset = queryset.filter( event__pk = event_id )
            broad = True # '=' show past events too
        query = EVENT_REGEX.sub("", query)
        # groups
        for group_name in GROUP_REGEX.findall( query ):
            if model == Event:
                queryset = queryset.filter(
                        calendar__group__name__iexact = group_name)
            else: # model is EventDate
                queryset = queryset.filter(
                        event__calendar__group__name__iexact = group_name)
        query = GROUP_REGEX.sub("", query)
        # continents
        # NOTE: continent_restriction (@@) must be before (@) because of the
        # similar regexes
        queryset, query = continent_restriction( queryset, query )
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
        words = SPACE_REGEX.split( query )
        words_set = set(
                [ word for word in words if word and word[0] != '+' ] )
        queryset_with_words_restriction = words_restriction(
                queryset, list( words_set ), broad, True )
        if related and words_set and model == Event:
            # FIXME: make it also work for: model = EventDate
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
            partial_result = related_events | queryset_with_words_restriction
        else:
            partial_result = queryset_with_words_restriction
        words_strict = set(
            [ word[1:] for word in words if word and word[0] == '+' and
                len(word) > 1 ] )
        result = result | words_restriction(
                partial_result, words_strict, False, False )
    return result


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
