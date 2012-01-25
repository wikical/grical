#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
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
""" utilities """

# imports {{{1
from difflib import HtmlDiff, unified_diff
import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
import httplib
import json
import re
import sys
import time
import urllib
import urllib2
from xml.etree.ElementTree import fromstring
from xml.parsers.expat import ExpatError

from django.core.cache import cache, get_cache
from django.core.mail import mail_admins
from django.contrib.gis.geos import Point
from django.contrib.gis.utils import GeoIP
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from django.conf import settings

from gridcalendar.events.tasks import save_in_caches

# TODO: avoid transgression of OpenStreetMap and Google terms of use. E.g.
# OpenStreetMap doesn't want more than one query per second
# Google Geocoding API is subject to a query limit of 2,500 geolocation
# requests per day. (Users of Google Maps API Premier may perform up to 100,000
# requests per day.)

# TODO: count and avoid transgressions of the geonames terms of use, which
# seems to be 2000 credits hourly

def search_coordinates( lat, lon ): # {{{1
    # doc {{{2
    """ returns a dictionary with the keys 'address', 'city' and 'country'
    using the nominatim API.
    
    Example of a query::

        http://nominatim.openstreetmap.org/reverse?format=json&lat=52.5487429714954&lon=-1.81602098644987&zoom=18&addressdetails=1

    Result::

        {u'address':{
                  u'city': u'City of Birmingham',
                  u'country': u'United Kingdom',
                  u'country_code': u'gb',
                  u'county': u'West Midlands',
                  u'house_number': u'137',
                  u'postcode': u'B72 1LH',
                  u'road': u'Pilkington Avenue',
                  u'state': u'England',
                  u'state_district': u'West Midlands',
                  u'suburb': u'Castle Vale'},
         u'display_name': u'137, Pilkington Avenue, Castle Vale, City of Birmingham, West Midlands, England, B72 1LH, United Kingdom',
         u'lat': u'52.5487800131654',
         u'licence': u'Data Copyright OpenStreetMap Contributors, Some Rights Reserved. CC-BY-SA 2.0.',
         u'lon': u'-1.81626922291265',
         u'osm_id': u'90394420',
         u'osm_type': u'way',
         u'place_id': u'2061235282'}


    Another example::

        http://nominatim.openstreetmap.org/reverse?format=json&lat=52.553984&lon=13.406737&zoom=18&addressdetails=1

    Result::

        { "place_id":"4440878",
          "licence":"Data Copyright OpenStreetMap Contributors, Some Rights Reserved. CC-BY-SA 2.0.",
          "osm_type":"node",
          "osm_id":"431391169",
          "lat":"52.55382",
          "lon":"13.4064759",
          "display_name":"Racket-Profis, Bornholmer Straße, Prenzlauer Berg, Pankow, Städt. Kita Kreuzgraben 13, Berlin, Stadt, Pankow, Berlin, 10439",
          "address":{
                "shop":"Racket-Profis",
                "road":"Bornholmer Straße",
                "suburb":"Prenzlauer Berg",
                "city_district":"Pankow",
                "city":"Städt. Kita Kreuzgraben 13",
                "county":"Berlin, Stadt",
                "region":"Pankow",
                "state":"Berlin",
                "boundary":"10439",
                "country_code":"de"}}

    >>> r = search_coordinates( 52.548972, 13.40932 )['address']
    >>> assert 'Kopenhagener' in r and 'Berlin' in r, r
    """
    # body {{{2
    response_text = ""
    try:
        lat = float( lat )
        lon = float( lon )
        conn = httplib.HTTPConnection( "nominatim.openstreetmap.org",
                timeout=10 )
        params = '&format=json' + \
                 '&zoom=18' + \
                 '&addressdetails=1' + \
                 '&email=' + settings.ADMINS[0][1] + \
                 '&lat=' + str(lat) + \
                 '&lon=' + str(lon)
        url_sufix = "/reverse?" + params
        conn.request( "GET", url_sufix )
        conn.sock.settimeout( 10.0 )
        response = conn.getresponse()
        response_text = response.read()
        dic = json.loads( response_text )
        # TODO: use other APIs like
        # http://www.geonames.org/export/reverse-geocoding.html
        # when the response is not satisfactory
        # TODO: Take care that not more than one query per second is sent to
        # OSM because of the terms of use (maybe using celery)
        to_return = dict()
        to_return['address'] = dic.get('display_name', None)
        if dic.has_key('address'):
            address = dic['address']
            # city
            if address.has_key('city'):
                to_return['city'] = address['city']
            else:
                to_return['city'] = None
            # country
            if address.has_key('country_code'):
                to_return['country'] = address['country_code'].upper()
            else:
                to_return['country'] = None
        else:
            to_return['city'] = None
            to_return['country'] = None
        return to_return
    except:
        return None

def search_address( data, ip = None ): # {{{1
    """ uses nominatim.openstreetmap.org and a Google API to get the geo-data
    of the address ``data`` (unicode)

    It returns a dictionary with long addresses (formatted addresses) as keys
    and a dictionary as values. The later dictionary has the keys:
    ``longitude``, ``latitude``, ``country`` and ``city``.

    >>> import math
    >>> import time
    >>> time.sleep(1)
    >>> result = search_address( u'c-base' )
    >>> len ( result )
    1
    >>> result = result.values()[0]
    >>> math.floor( float(result['longitude']) )
    13.0
    >>> math.floor( float(result['latitude']) )
    52.0
    >>> time.sleep(1)
    >>> result = search_address( u'Schivelbeiner Str. 22, Berlin, DE' )
    >>> len ( result )
    1
    >>> result = result.values()[0]
    >>> math.floor( float(result['longitude']) )
    13.0
    >>> math.floor( float(result['latitude']) )
    52.0
    >>> time.sleep(1)
    >>> result = search_address( u'Kantstr. 6', ip = '85.179.47.148' )
    >>> len ( result )
    1
    """
    # TODO the returned addresses must be sorted by relevance (the output of
    # the external APIs already provides a relevance number)
    result_osm = search_address_osm( data )
    if result_osm and len( result_osm ) == 1:
        return result_osm
    # result_osm is not good enough, we try now Google
    result_google = search_address_google( data )
    if result_google and len( result_google ) == 1:
        return result_google
    # result_google is not good enough either, we try now using the IP of the
    # user for geo-location
    if ip:
        geoip = GeoIP()
        # we try adding the country (from the IP) if not already given
        last_item = data[data.rfind(',')+1:].strip().upper()
        # TODO GEO: include translations, GeoNames.org
        from gridcalendar.events.models import COUNTRIES
        country_codes = [ val[0].upper() for val in COUNTRIES ]
        country_names = [ val[1].upper() for val in COUNTRIES ]
        country_code = None
        if ( last_item not in country_codes ) and \
                ( last_item not in country_names ):
            country_code = geoip.country_code_by_addr( ip )
            if country_code:
                data_extended = data + u", " + country_code
                # OpenStreetMap doesn't want more than one query per second
                time.sleep(1)
                result_osm = search_address_osm( data_extended )
                if result_osm and len( result_osm ) == 1:
                    return result_osm
                # OpenStreetMap couldn't help, we try Google again with the
                # country code
                result_google = search_address_google( data_extended )
                if result_google and len( result_google ) == 1:
                    return result_google
        # the country didn't help. We try also the city.
        region_data = geoip.region_by_addr( ip )
        if region_data:
            city = smart_unicode(region_data['city'], encoding='ISO-8859-1')
            if city.lower() not in data.lower():
                if country_code:
                    data_extended = data + ', ' + city + ', ' + country_code
                else:
                    data_extended = data + ', ' + city
                # we try again with Google
                result_google = search_address_google( data_extended )
                if result_google and len( result_google ) == 1:
                    return result_google
                # we try again with OSM
                time.sleep(1)
                result_osm = search_address_osm( data_extended )
                if result_osm and len( result_osm ) == 1:
                    return result_osm
    # nothing worked out :( we return the smaller of both, otherwise None
    if result_osm:
        if result_google:
            if len( result_google ) < len( result_osm ):
                return result_google
            return result_osm
        return result_osm
    if result_google:
        return result_google
    return None

def search_country_code( name ): #{{{1
    """ returns the country code uppercase of a country code or of a country
    name accepting different languages
    """
    # next line needed because len(django_countries.fields.Country) produces an
    # error, and `name` can be of that type
    if not name:
        return None
    name = unicode( name )
    if len( name ) == 2:
        return name.upper()
    from gridcalendar.events.models import COUNTRIES
    for code_country in COUNTRIES:
        if code_country[1].lower == name.lower():
            return code_country[0]
    # TODO GEO: before using an external API check for translations already
    # done for the package django_countries
    result = search_name( name )
    if result:
        return result['country']
    return None

def search_address_google(data): # {{{1
    """ loop up using The Google Geocoding API

    Returns the same as ``search_address_osm``

    See:
    
    - http://code.google.com/apis/maps/documentation/geocoding/
    - http://code.google.com/intl/en/apis/maps/documentation/geocoding/

    Example of a XML returned by the Google API::

        <?xml version="1.0" encoding="UTF-8"?>
        <GeocodeResponse>
         <status>OK</status>
         <result>
          <type>street_address</type>
          <formatted_address>Malmöer Straße 6, 10439 Berlin, Germany</formatted_address>
          <address_component>
           <long_name>6</long_name>
           <short_name>6</short_name>
           <type>street_number</type>
          </address_component>
          <address_component>
           <long_name>Malmöer Straße</long_name>
           <short_name>Malmöer Straße</short_name>
           <type>route</type>
          </address_component>
          <address_component>
           <long_name>Berlin</long_name>
           <short_name>Berlin</short_name>
           <type>sublocality</type>
           <type>political</type>
          </address_component>
          <address_component>
           <long_name>Berlin</long_name>
           <short_name>Berlin</short_name>
           <type>locality</type>
           <type>political</type>
          </address_component>
          <address_component>
           <long_name>Berlin</long_name>
           <short_name>Berlin</short_name>
           <type>administrative_area_level_2</type>
           <type>political</type>
          </address_component>
          <address_component>
           <long_name>Berlin</long_name>
           <short_name>Berlin</short_name>
           <type>administrative_area_level_1</type>
           <type>political</type>
          </address_component>
          <address_component>
           <long_name>Germany</long_name>
           <short_name>DE</short_name>
           <type>country</type>
           <type>political</type>
          </address_component>
          <address_component>
           <long_name>10439</long_name>
           <short_name>10439</short_name>
           <type>postal_code</type>
          </address_component>
          <geometry>
           <location>
            <lat>52.5510500</lat>
            <lng>13.4041300</lng>
           </location>
           <location_type>ROOFTOP</location_type>
           <viewport>
            <southwest>
             <lat>52.5479024</lat>
             <lng>13.4009824</lng>
            </southwest>
            <northeast>
             <lat>52.5541976</lat>
             <lng>13.4072776</lng>
            </northeast>
           </viewport>
          </geometry>
         </result>
        </GeocodeResponse>

    >>> import math
    >>> result = search_address_google( u'Malmöer Str. 6, Berlin, DE' )
    >>> len ( result )
    1
    >>> result = result.values()[0]
    >>> math.floor( float(result['longitude']) )
    13.0
    >>> math.floor( float(result['latitude']) )
    52.0
    >>> result['country']
    'DE'
    >>> result['city']
    'Berlin'
    """
    try:
        address = urllib.quote( data.encode('utf-8') )
        conn = httplib.HTTPConnection( "maps.googleapis.com", timeout=10 )
        url_sufix = "//maps/api/geocode/xml?address=" + address + \
                    "&sensor=false"
        conn.request( "GET", url_sufix )
        conn.sock.settimeout( 10.0 )
        response = conn.getresponse()
        response_text = response.read()
        doc = fromstring( response_text )
        # a dictionary with a display_name as unicode keys and values as
        # dictionaries of field names and values
        result = dict()
        status = doc.findtext('status')
        if ( not status ) or status != 'OK':
            return None
        # we suppose we get results with type = street_address
        # TODO find out what else there is and how it looks like
        for place in doc.findall('result'):
            pdic = dict() # place dict
            value = place.findtext('geometry/location/lat')
            if value:
                pdic['latitude'] = value
            value = place.findtext('geometry/location/lng')
            if value:
                pdic['longitude'] = value
            for component in place.findall('address_component'):
                types = [value.text for value in component.findall('type')]
                if 'locality' in types:
                    pdic['city'] = component.findtext('long_name')
                elif 'country' in types:
                    pdic['country'] = component.findtext('short_name').upper()
            value = place.findtext('formatted_address')
            if value:
                if len( value ) > len( data ):
                    result[value] = pdic
                else:
                    result[ data ] = pdic
            else:
                result[ data ] = pdic
        if len( result ) > 0:
            return result
    except:
        pass
    return None

def search_timezone( lat, lng, use_cache = True ): # {{{1
    """ it uses the geonames API returning the name of the timezone (according
    to olson).

    See http://www.geonames.org/export/web-services.html
    """
    # TODO: add settings options to use the primium server ws.geonames.net and
    # token (auth setting in geonames.org)
    if use_cache:
        cache_value = None
        cache_key =  'search_timezone__' + str(lat) + "_" + str(lng)
        db_cache = get_cache('db')
        # we try the memcached cache (see settings.CACHES)
        if cache.has_key( cache_key ):
            cache_value = cache.get( cache_key )
        # we try the db cache
        elif db_cache.has_key( cache_key ):
            cache_value = db_cache.get( cache_key )
        if cache_value:
            # we want to be sure that it is saved in all caches
            save_in_caches.delay( cache_key, cache_value )
            return cache_value
    url = settings.GEONAMES_URL + 'timezone?lat=%s&lng=%s&username=%s' % \
            ( str(lat), str(lng), settings.GEONAMES_USERNAME )
    try:
        # FIXME: check for API limit reached
        response = urllib2.urlopen( url, timeout = 10 )
        if not response:
            if use_cache:
                save_in_caches.delay( cache_key, None, timeout = 300 )
            return None
        response_text = response.read()
        doc = fromstring( response_text ) # can raise a ExpatError
        timezone = doc.findall( 'timezone' )[0]
        timezoneId = timezone.find('timezoneId').text
    except ( urllib2.HTTPError, urllib2.URLError, ExpatError,
            IndexError, AttributeError ) as err:
        # TODO: log the err
        if use_cache:
            save_in_caches.delay( cache_key, None, timeout = 300 )
        return None
    if not timezoneId:
        if use_cache:
            save_in_caches.delay( cache_key, None, timeout = 300 )
        return None
    from models import TIMEZONES
    found = False
    for group in TIMEZONES:
        for tup in group[1]:
            if tup[0] == timezoneId:
                found = True
                break
    if not found:
        # TODO: log the error
        if use_cache:
            save_in_caches.delay( cache_key, None, timeout = 300 )
        return None
    if use_cache:
        # we save it fast in memcached before saving it slowly in all caches
        cache.set( cache_key, timezoneId )
        save_in_caches.delay( cache_key, timezoneId )
        # TODO: test that we recognize the timezoneId and log if not
    return timezoneId

# TODO cache API searches and download the data of geonames to use when running
# out of allowed queries
def search_name( name, use_cache = True ): # {{{1
    """ it uses the geonames API returning a dictionary with:

    - 'coordinates': a ``Point`` with the most relevant location given e.g.
      ``London,GB``
    - 'city'
    - 'country'

    As of April 2011, the restrictions are 2000 queries per hour and 30.000 per day.
    See http://www.geonames.org/export/
    
    Example query::

        http://api.geonames.org/search?q=london,ca&maxRows=1&username=demo

    Result::

        <geonames style="MEDIUM">
          <totalResultsCount>44</totalResultsCount>
          <geoname>
            <toponymName>London</toponymName>
            <name>London</name>
            <lat>42.98339</lat>
            <lng>-81.23304</lng>
            <geonameId>6058560</geonameId>
            <countryCode>CA</countryCode>
            <countryName>Canada</countryName>
            <fcl>P</fcl>
            <fcode>PPL</fcode>
          </geoname>
        </geonames>

    Another example with German names of city and country 
    (München = Munich, Deutschland = Germany)::

        http://api.geonames.org/search?q=M%C3%BCnchen,Deutschland&maxRows=1&username=demo

    Result::

        <geonames style="MEDIUM">
          <totalResultsCount>97</totalResultsCount>
          <geoname>
            <toponymName>München</toponymName>
            <name>Munich</name>
            <lat>48.13743</lat>
            <lng>11.57549</lng>
            <geonameId>2867714</geonameId>
            <countryCode>DE</countryCode>
            <countryName>Germany</countryName>
            <fcl>P</fcl>
            <fcode>PPLA</fcode>
          </geoname>
        </geonames>
    """
    query = urllib.quote( name.encode('utf-8'), safe=',' )
    if use_cache:
        cache_value = None
        cache_key =  'search_name__' +  query
        db_cache = get_cache('db')
        # we try the memcached cache (see settings.CACHES)
        if cache.has_key( cache_key ):
            cache_value = cache.get( cache_key )
        elif db_cache.has_key( cache_key ):
            # we try the db cache
            cache_value = db_cache.get( cache_key )
        if cache_value:
            # we want to be sure that it is saved in all caches
            save_in_caches.delay( cache_key, cache_value )
            return cache_value
    url = settings.GEONAMES_URL + 'search?q=%s&maxRows=1&username=%s' % \
            ( query, settings.GEONAMES_USERNAME )
    try:
        response_text = None
        response = urllib2.urlopen( url, timeout = 10 )
        if not response:
            if use_cache:
                save_in_caches.delay( cache_key, None, timeout = 300 )
            return None
        response_text = response.read()
        doc = fromstring( response_text ) # can raise a ExpatError
        geonames = doc.findall( 'geoname' )
        # if no geoname, genonames is None and when trying to get geonames[0] a
        # IndexError is raised
        # if no lat, no text and an AttributeError is raised:
        lat = float( geonames[0].find('lat').text )
        # if no lng, no text and an AttributeError is raised:
        lng = float( geonames[0].find('lng').text )
        city = geonames[0].find('name').text
        country = geonames[0].find('countryCode').text
    except ( urllib2.HTTPError, urllib2.URLError, ExpatError,
            IndexError, AttributeError ) as err:
        if use_cache:
            save_in_caches.delay( cache_key, None, timeout = 300 )
        if response_text and 'the daily limit of' in response_text:
            mail_admins(
                'URGENT: geonames limit reached',
                'time: %s\nsearch query: %s\nresponse:\n%s' % \
                    ( str(datetime.datetime.now()), name, response_text ) )
        else:
            mail_admins(
                'error in search_name',
                'time: %s\nsearch query: %s\nerror: %s' % \
                    ( str(datetime.datetime.now()), name, str(err) ) )
        return None
    coordinates = Point( lng, lat )
    to_return = dict( (
        ('coordinates', coordinates),
        ('city', city),
        ('country', country) ) )
    if use_cache:
        # we save it fast in memcached before saving it slowly in all caches
        cache.set( cache_key, to_return )
        save_in_caches.delay( cache_key, to_return )
    return to_return

def search_address_osm( data ): # {{{1
    """ uses nominatim.openstreetmap.org to look up for ``data``.

    Example of a query::

        http://nominatim.openstreetmap.org/search?q=
        Gleimstr.+60,+Berlin,+10439,+DE&format=xml&addressdetails=1

    Example of the response::

        <searchresults timestamp="Thu, 08 Dec 11 11:18:13 -0500"
                attribution="Data Copyright OpenStreetMap Contributors, Some
                Rights Reserved. CC-BY-SA 2.0."
                querystring="Gleimstr. 60, Berlin, 10439, DE" polygon="false"
                exclude_place_ids="12347262"
                more_url="http://open.mapquestapi.com/nominatim/v1/search?
                    format=xml&exclude_place_ids=12347262&accept-language=
                    en-us,en;q=0.5&addressdetails=1&q=Gleimstr.+60%2C+
                    Berlin%2C+10439%2C+DE">
            <place place_id="12347262" osm_type="node" osm_id="1023766671"
                    place_rank="30"
                    boundingbox="52.5368559265,52.5568597412,13.3921701813,
                            13.4121711349"
                    lat="52.5468563" lon="13.4021706"
                    display_name="60, Gleimstraße, Prenzlauer
                            Berg, Pankow, Berlin, Berlin, Stadt, Pankow,
                            Berlin, 10437"
                    class="place" type="house">
                <house_number>60</house_number>
                <road>Gleimstraße</road>
                <suburb>Prenzlauer Berg</suburb>
                <city_district>Pankow</city_district>
                <city>Berlin</city>
                <county>Berlin, Stadt</county>
                <region>Pankow</region>
                <state>Berlin</state>
                <boundary>10437</boundary>
                <postcode>10437</postcode>
                <country_code>de</country_code>
            </place>
        </searchresults>

    See ``search_address``

    >>> import math
    >>> result = search_address_osm( u'c-base' )
    >>> len ( result )
    1
    >>> result = result.values()[0]
    >>> math.floor( float(result['longitude']) )
    13.0
    >>> math.floor( float(result['latitude']) )
    52.0
    >>> result['country']
    'DE'
    """
    # NOTE: unfortunately the API doesn't seem very consistent when looking up
    # cities. See the output of e.g.:
    # http://nominatim.openstreetmap.org/search?q=Munich,+DE&format=xml&addressdetails=1
    # http://nominatim.openstreetmap.org/search?q=München,+DE&format=xml&addressdetails=1
    # TODO: better use the json format (instead of xml) and the json library:
    # import json ; data = json.loads( response_text )
    try:
        address = urllib.quote( data.encode('utf-8') )
        params = '&format=xml' \
            '&polygon=0' \
            '&addressdetails=1' \
            '&email=' + settings.ADMINS[0][1] + \
            '&limit=10'
        conn = httplib.HTTPConnection( "nominatim.openstreetmap.org",
                timeout=10 )
        # see http://wiki.openstreetmap.org/wiki/Nominatim
        # TODO: include parameter accept-language according to user/browser
        url_sufix = "/search?q=" + address + params 
        conn.request( "GET", url_sufix )
        conn.sock.settimeout( 10.0 )
        response = conn.getresponse()
        response_text = response.read()
        doc = fromstring( response_text ) # can throw a ExpatError
        # a dictionary with a display_name as unicode keys and values as
        # dictionaries of field names and values
        result = dict()
        for place in doc.findall('place'):
            pdic = dict() # place dict
            value = place.get('lon')
            if value is not None:
                pdic['longitude'] = value
            value = place.get('lat')
            if value is not None:
                pdic['latitude'] = value
            value = place.find('city')
            if value is not None:
                pdic['city'] = value.text
            value = place.find('country_code')
            if value is not None:
                pdic['country'] = value.text.upper()
            value = place.get('display_name')
            if value:
                if len( value ) > len( data ):
                    result[value] = pdic
                else:
                    result[ data ] = pdic
            else:
                result[ data ] = pdic
        if len( result ) > 0:
            return result
    except:
        pass
    return None

def validate_event_exists( value ): # {{{1
    """ checks that there is an event with ``value`` as id """
    from gridcalendar.events.models import Event
    try:
        Event.objects.get( pk = value )
    except Event.DoesNotExist:
        raise ValidationError( _(u'An event with the number %(event_nr)s ' \
                'does not exists.') % {'event_nr': value,} )

def validate_tags_chars( value ): # {{{1
    """ it validates that tag characters are only international letters, spaces
    and hyphen """
    if re.search("[^ \-\w]|_", value, re.UNICODE):
        raise ValidationError(_(u"Punctuation marks are not allowed, " \
                "tags are separated by spaces and can contain only " \
                "letters and hyphens (-)"))

def validate_year( value ): # {{{1
    """ it validates ``value.year`` newer than 1900 and less than 2 years from
    now.
    
    ``date`` and ``datetime`` have this property.

    Event dates which are more than two years in the future are very likely to
    be a human mistake entering the data.

    This validator is needed because some functions like datetime.strftime()
    raise a ValueError when the year is older than 1900. See the discussion at
    http://bugs.python.org/issue1777412
    """
    if value.year <= 1900:
        raise ValidationError(
            _( u'%(year)s is before 1900, which is not allowed' ) % \
                    {'year': value.year,} )
    if value > datetime.date.today() + relativedelta( years = 4 ):
        raise ValidationError(
            _( u'%(year)s is more than four years in the future, ' \
                    'which is not allowed' ) % {'year': value.year,} )

def html_diff(old_as_text, new_as_text): # {{{1
    """ returns a utf8 string containing the code of a html table showing
    differences of the utf8 parameters """
    old_as_text = old_as_text.splitlines()
    new_as_text = new_as_text.splitlines()
    table = HtmlDiff( tabsize = 4 ).make_table( old_as_text, new_as_text )
    return table.replace( '&nbsp;', ' ' ).replace( ' nowrap="nowrap"', '' )

def text_diff(old_as_text, new_as_text): # {{{1
    """ returns a unicode string containing a diff text showing
    differences of the utf8 parameters """
    old_as_text = smart_unicode( old_as_text ).splitlines()
    new_as_text = smart_unicode( new_as_text ).splitlines()
    text_diff = unified_diff(
            old_as_text, new_as_text, n = 0, lineterm = "" )
    # we now delete from the text diff all control lines
    # TODO: when the description field of an event contains such lines,
    # they will be deleted: avoid it.
    text_diff = [line for line in text_diff if not
            re.match(r"^---\s*$", line) and not
            re.match(r"^\+\+\+\s*$", line) and not
            re.match(r"^@@.*@@$", line)]
    text_diff = u'\n'.join( text_diff )
    return text_diff


class GermanParserInfo(parser.parserinfo): # {{{1
    """Enable German dates for the parser of dateutils

    >>> parser.parse('20. Dezember 2001',
    ...     parserinfo=GermanParserInfo())
    datetime.datetime(2001, 12, 20, 0, 0)
    """
    # Code originally from https://bitbucket.org/miracle2k/pyutils/ under the
    # BSD license
    JUMP = [" ", ".", ",", ";", "-", "/", "'",
            "am", "an", "bis", "in", "im", "Uhr",
            "der", "den", "dem", "des", "das", "die", "um" ]
    PERTAIN = ["von", "vom"]
    AMPM = [("Morgen", "morgens", "vormittags", "Vormittag"),
            ("abend", "abends", "nachmittag", "nachmittags")]
    WEEKDAYS = [("Mo", "Montag"),
                ("Di", "Dienstag"),
                ("Mi", "Mittwoch"),
                ("Do", "Donnerstag"),
                ("Fr", "Freitag"),
                ("Sa", "Samstag"),
                ("So", "Sonntag")]
    MONTHS   = [("Jan", "Januar"),
                ("Feb", "Februar"),
                # the dateutil library works with iso-8859-1 encoding
                # TODO: contact the author to modify it, because many languages
                # cannot be encoded in iso-8859-1
                (u"Mär".encode('iso-8859-1', 'replace'),
                    u"März".encode('iso-8859-1', 'replace'),
                    "Maerz", "Marz", "Mar", "Mrz"),
                ("Apr", "April"),
                ("Mai", "Mai"),
                ("Jun", "Juni"),
                ("Jul", "Juli"),
                ("Aug", "August"),
                ("Sep", "Sept", "September"),
                ("Okt", "Oktober"),
                ("Nov", "November"),
                ("Dez", "Dezember")]
    HMS = [("h", "Stunde", "Stunden"),
           ("m", "Minute", "Minuten"),
           ("s", "Sekunde", "Sekunden")]

    def __init__(self, dayfirst=True, yearfirst=False):
        # for german dates, set ``dayfirst`` by default
        super(GermanParserInfo, self).__init__(dayfirst=dayfirst, yearfirst=yearfirst)

    def weekday(self, name):
        """
        We need to reimplement this, as German weekdays in shortform
        are only two characters long, and the superclass implementation
        has a hardcoded requirement of at least 3.
        """
        if len(name) >= 2:
            try:
                return self._weekdays[name.lower()]
            except KeyError:
                pass
        return None


class SpanishParserInfo(parser.parserinfo): # {{{1
    """Enable Spanish dates for the parser of dateutils

    >>> parser.parse('20 de diciembre del 2001',
    ...     parserinfo=SpanishParserInfo())
    datetime.datetime(2001, 12, 20, 0, 0)
    """
    # Code originally from https://bitbucket.org/miracle2k/pyutils/ under the
    # BSD license
    JUMP = [" ", ".", ",", ";", "-", "/", "'",
            "a", "la", "las", "el", "del", "de", "y"]
    WEEKDAYS = [("L", "lunes"),
                ("M", "martes"),
                # the dateutil library works with iso-8859-1 encoding
                # TODO: contact the author to modify it, because many languages
                # cannot be encoded in iso-8859-1
                ("X", "miercoles",
                    u"miércoles".encode('iso-8859-1', 'replace')),
                ("J", "jueves"),
                ("V", "viernes"),
                ("S", "sabado",
                    u"sábado".encode('iso-8859-1', 'replace')),
                ("D", "domingo")]
    MONTHS   = [("ENE", "enero"),
                ("FEB", "febrero"),
                ("MAR", "marzo"),
                ("ABR", "abril"),
                ("MAY", "mayo"),
                ("JUN", "junio"),
                ("JUL", "julio"),
                ("AGO", "agosto"),
                ("SET", "septiembre"),
                ("OCT", "octubre"),
                ("NOV", "noviembre"),
                ("DIC", "diciembre")]
    HMS = [("h", "hora", "horas"),
           ("m", "minuto", "minutos"),
           ("s", "segundo", "segundos")]

    def __init__(self, dayfirst=True, yearfirst=False):
        # for Spanish dates, set ``dayfirst`` by default
        super(SpanishParserInfo, self).__init__(dayfirst=dayfirst, yearfirst=yearfirst)

    def weekday(self, name):
        """
        We need to reimplement this, as Spanish weekdays in shortform
        are only one character long, and the superclass implementation
        has a hardcoded requirement of at least 3.
        """
        if len(name) >= 1:
            try:
                return self._weekdays[name.lower()]
            except KeyError:
                pass
        return None
