#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import sys
import urllib
import httplib
from xml.etree.ElementTree import fromstring

def search_address( data ): # {{{1
    """ uses nominatim.openstreetmap.org to get the geo-data of the address
    ``data`` (unicode)

    It returns a dictionary with a long address as keys and a dictionary as
    values. The later dictionary has the keys: ``longitude``, ``latitude``,
    ``address``, ``postcode``, ``country`` and ``city``.

    >>> import math
    >>> result = search_address( u'Malmöer Str. 6, Berlin, DE' )
    >>> len ( result )
    1
    >>> result = result.values()[0]
    >>> math.floor( result['longitude'] )
    13
    >>> math.floor( result['latitude'] )
    52
    >>> result['postcode']
    10439
    >>> result['country']
    DE
    >>> result['city']
    Berlin
    >>> result['address']
    Malmöer Straße
    """
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
        value = place.find('road')
        if value is not None:
            pdic['address'] = value.text
        value = place.find('house')
        if value is not None:
            if pdic.has_key('address'):
                pdict['address'] += u' ' + value.text
            else:
                pdic['address'] = value.text
        value = place.find('city')
        if value is not None:
            pdic['city'] = value.text
        value = place.find('country_code')
        if value is not None:
            pdic['country'] = value.text.upper()
        value = place.find('postcode')
        if value is not None:
            pdic['postcode'] = value.text
        result[ place.get('display_name') ] = pdic
    return result

# only for testing:
if __name__ == "__main__": # {{{1
    result = search_address( sys.argv[1].decode( sys.getfilesystemencoding() ) )
    print result

