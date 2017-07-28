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
import math
import time
from unittest import skipIf

from django.conf import settings
from django.test import TestCase

from ..utils import (search_address, search_coordinates, search_address_google,
        search_address_osm)

class UtilsTestCase(TestCase):

    def test_search_coordinates(self):
        r = search_coordinates( 52.548972, 13.40932 )['address']
        assert 'Kopenhagener' in r and 'Berlin' in r, r

    @skipIf(settings.GEONAMES_USERNAME in ('', 'demo'),
                                "set GEONAMES_USERNAME to a valid value")
    def test_search_address(self):
        time.sleep(1)
        result = search_address( u'c-base' )
        self.assertEqual(len ( result ), 1)
        result = result.values()[0]
        self.assertEqual(math.floor( float(result['longitude']) ), 13.0)
        self.assertEqual(math.floor( float(result['latitude']) ), 52.0)
        time.sleep(1)
        result = search_address( u'Schivelbeiner Str. 22, Berlin, DE' )
        self.assertEqual(len ( result ), 1)
        result = result.values()[0]
        self.assertEqual(math.floor( float(result['longitude']) ), 13.0)
        self.assertEqual(math.floor( float(result['latitude']) ), 52.0)
        time.sleep(1)
        result = search_address( u'Kantstr. 6', ip = '85.179.47.148' )
        self.assertEqual(len ( result ), 1)

    def test_search_address_google(self):
        result = search_address_google( u'Malmöer Str. 6, Berlin, DE' )
        self.assertEqual(len ( result ), 1)
        result = result.values()[0]
        self.assertEqual(math.floor( float(result['longitude']) ), 13.0)
        self.assertEqual(math.floor( float(result['latitude']) ), 52.0)
        self.assertEqual(result['country'], 'DE')
        self.assertEqual(result['city'], 'Berlin')

    def test_search_address_osm(self):
        result = search_address_osm( u'c-base, Germany' )
        self.assertEqual(len ( result ), 1)
        result = result.values()[0]
        self.assertEqual(math.floor( float(result['longitude']) ), 13.0)
        self.assertEqual(math.floor( float(result['latitude']) ), 52.0)
        self.assertEqual(result['country'], 'DE')

