#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
# gpl {{{1
#############################################################################
# Copyright 2009, 2010 Ivan Villanueva <ivan ät gridmind.org>
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
from dateutil.relativedelta import relativedelta
import re
import sys
import time
import urllib
import urllib2
import httplib
from xml.etree.ElementTree import fromstring
from xml.parsers.expat import ExpatError

from django.contrib.gis.geos import Point
from django.contrib.gis.utils import GeoIP
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

from settings import GEONAMES_USERNAME

# TODO: avoid transgression of OpenStreetMap and Google terms of use. E.g.
# OpenStreetMap doesn't want more than one query per second
# Google Geocoding API is subject to a query limit of 2,500 geolocation
# requests per day. (Users of Google Maps API Premier may perform up to 100,000
# requests per day.)

def search_address( data, ip = None ): # {{{1
    """ uses nominatim.openstreetmap.org and a Google API to get the geo-data
    of the address ``data`` (unicode)

    It returns a dictionary with long addresses (formatted addresses) as keys
    and a dictionary as values. The later dictionary has the keys:
    ``longitude``, ``latitude``, ``postcode``, ``country`` and ``city``.

    >>> import math
    >>> result = search_address( u'c-base' )
    >>> len ( result )
    1
    >>> result = result.values()[0]
    >>> math.floor( float(result['longitude']) )
    13.0
    >>> math.floor( float(result['latitude']) )
    52.0
    >>> result = search_address( u'Malmöer Str. 6, Berlin, DE' )
    >>> len ( result )
    1
    >>> result = result.values()[0]
    >>> math.floor( float(result['longitude']) )
    13.0
    >>> math.floor( float(result['latitude']) )
    52.0
    >>> result = search_address( u'Kantstr. 6', ip = '85.179.47.148' )
    >>> len ( result )
    1
    """
    result_google = search_address_google( data )
    if result_google and len( result_google ) == 1:
        return result_google
    # result_google is not good enough, we try now OSM
    result_osm = search_address_osm( data )
    if result_osm and len( result_osm ) == 1:
        return result_osm
    # result_osm is not good enough either, we try now using the IP of the user
    # for geo-location
    if ip:
        geoip = GeoIP()
        # we try adding the country (from the IP) if not already given
        last_item = data[data.rfind(',')+1:].strip().upper()
        # TODO: include translations, GeoNames.org
        from models import COUNTRIES
        country_codes = [ val[0].upper() for val in COUNTRIES ]
        country_names = [ val[1].upper() for val in COUNTRIES ]
        country_code = None
        if ( last_item not in country_codes ) and \
                ( last_item not in country_names ):
            country_code = geoip.country_code_by_addr( ip )
            if country_code and country_code != '':
                data_extended = data + u", " + country_code
                # OpenStreetMap doesn't want more than one query per second
                time.sleep(1)
                result_osm = search_address_osm( data_extended )
                if result_osm and len( result_osm ) == 1:
                    return result_osm
                # OpenStreetMap couldn't help, we try Google again with the
                # country code
                result_google = search_address_google( data, country_code )
                if result_google and len( result_google ) == 1:
                    return result_google
        # the country didn't help. We try also the city.
        region_data = geoip.region_by_addr( ip )
        if region_data and region_data['city'].lower() not in data.lower():
            if country_code:
                data_extended = data + ', ' + region_data['city'] + ', ' + \
                    country_code
            else:
                data_extended = data + ', ' + region_data['city']
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

def search_address_google( data, country_code = None ): # {{{1
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
    # FIXME check response code, etc and return None if no address are given or
    # an error occur
    address = urllib.quote( data.encode('utf-8') )
    conn = httplib.HTTPConnection( "maps.googleapis.com" )
    if country_code:
        url_sufix = "//maps/api/geocode/xml?address=" + address + \
                "&sensor=false&region=" + country_code.lower()
    else:
        url_sufix = "//maps/api/geocode/xml?address=" + address + \
                "&sensor=false"
    conn.request( "GET", url_sufix )
    # TODO: there is a timeout? if not use a thread and stop it after some time
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
            elif 'postal_code' in types:
                pdic['postcode'] = component.findtext('long_name')
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
    return None

# TODO cache API searches and download the data of geonames to use when running
# out of allowed queries
def search_name( name ): # {{{1
    """ it uses the geonames API returning a ``Point`` with the most relevant
    location given e.g. ``London,GB``

    As of April 2011, the restrictions are 2000 queries per hour and 30.000 per day.
    See http://www.geonames.org/export/
    
    Example query:
    ``http://api.geonames.org/search?q=london,ca&maxRows=1&username=demo``

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
    
    >>> p = search_name( u'london,ca' )
    >>> unicode(p.x)
    u'-81.23304'
    >>> unicode(p.y)
    u'42.98339'
    """
    query = urllib.quote( name.encode('utf-8') )
    url = 'http://api.geonames.org/search?q=%s&maxRows=1&username=%s' % \
            ( query, GEONAMES_USERNAME )
    try:
        # FIXME: check for API limit reached
        response = urllib2.urlopen( url, timeout = 10 )
        if not response:
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
    except ( urllib2.HTTPError, urllib2.URLError, ExpatError,
            IndexError, AttributeError ) as err:
        # TODO: log the err
        return None
    return Point( lng, lat )

def search_address_osm( data ): # {{{1
    """ uses nominatim.openstreetmap.org to look up for ``data``.#{{{

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
    # FIXME check response code, etc and return None if no address are given or
    # an error occur#}}}
    address = urllib.quote( data.encode('utf-8') )
    params = ''.join( [
        '&format=xml',
        '&polygon=0',
        '&addressdetails=1',
        '&email=office@gridmind.org',
        '&limit=10', ] )
    conn = httplib.HTTPConnection( "nominatim.openstreetmap.org" )
    # see http://wiki.openstreetmap.org/wiki/Nominatim
    # TODO: include parameter accept-language according to user/browser
    url_sufix = "/search?q=" + address + params 
    conn.request( "GET", url_sufix )
    response = conn.getresponse()
    response_text = response.read()
    # FIXME: use a thread
    doc = fromstring( response_text )
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
        value = place.find('postcode')
        if value is not None:
            pdic['postcode'] = value.text
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
    return None

def validate_event_exists( value ):
    """ checks that there is an event with ``value`` as id """
    try:
        Event.objects.get( pk = value )
    except Event.DoesNotExist:
        raise ValidationError( _(u'An event with the number %(event_nr)s ' \
                'does not exists.') % {'event_nr': value,} )

def validate_year( value ):
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
    if value > datetime.date.today() + relativedelta( years = 2 ):
        raise ValidationError(
            _( u'%(year)s is more than two years in the future, ' \
                    'which is not allowed' ) % {'year': value.year,} )

def html_diff(old_as_text, new_as_text):
    """ returns a utf8 string containing the code of a html table showing
    differences of the utf8 parameters """
    old_as_text = old_as_text.splitlines()
    new_as_text = new_as_text.splitlines()
    return HtmlDiff( tabsize = 4 ).make_table( old_as_text, new_as_text )

def text_diff(old_as_text, new_as_text):
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

# only for testing:
if __name__ == "__main__": # {{{1
#    result = search_address_google(
#            sys.argv[1].decode( sys.getfilesystemencoding() ) )
    result = search_address( sys.argv[1].decode( sys.getfilesystemencoding() ) )
    print result

