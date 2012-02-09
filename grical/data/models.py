#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# GPL {{{1
#############################################################################
# Copyright 2009-2012 Ivan F. Villanueva B. <ivan ät gridmind.org>
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

""" Models """

# imports {{{1
from django.contrib.gis.db import models
from django.utils.translation import ugettext as _

# DATA from
# https://en.wikipedia.org/wiki/List_of_sovereign_states_and_dependent_territories_by_continent_(data_file)

CONTINENTS = (
    ('AF', _('Africa')),
    ('AS', _('Asia')),
    ('EU', _('Europe')),
    ('NA', _('North America')),
    ('SA', _('South America')),
    ('OC', _('Oceania')),
    ('AN', _('Antarctica')))

# NOTE: the following countries are in more than one continent: AM AZ CY GE KZ RU TR UM
# TODO GEO:
# - Kazakhstan ( KZ, https://en.wikipedia.org/wiki/Kazakhstan ) should
# be removed from EU
# - RU should be devided in two parts
# - UM islands should be devided in at least two continents

CONTINENT_COUNTRIES = {

    'AF': ('AO', 'BF', 'BI', 'BJ', 'BW', 'CD', 'CF', 'CG', 'CI', 'CM', 'CV',
    'DJ', 'DZ', 'EG', 'EH', 'ER', 'ET', 'GA', 'GH', 'GM', 'GN', 'GQ', 'GW',
    'KE', 'KM', 'LR', 'LS', 'LY', 'MA', 'MG', 'ML', 'MR', 'MU', 'MW', 'MZ',
    'NA', 'NE', 'NG', 'RE', 'RW', 'SC', 'SD', 'SH', 'SL', 'SN', 'SO', 'ST',
    'SZ', 'TD', 'TG', 'TN', 'TZ', 'UG', 'YT', 'ZA', 'ZM', 'ZW'),

    'AN': ('AQ', 'BV', 'GS', 'HM', 'TF'),

    'AS': ('AE', 'AF', 'AM', 'AZ', 'BD', 'BH', 'BN', 'BT', 'CC', 'CN', 'CX',
    'CY', 'GE', 'HK', 'ID', 'IL', 'IN', 'IO', 'IQ', 'IR', 'JO', 'JP', 'KG',
    'KH', 'KP', 'KR', 'KW', 'KZ', 'LA', 'LB', 'LK', 'MM', 'MN', 'MO', 'MV',
    'MY', 'NP', 'OM', 'PH', 'PK', 'PS', 'QA', 'RU', 'SA', 'SG', 'SY', 'TH',
    'TJ', 'TL', 'TM', 'TR', 'TW', 'UZ', 'VN', 'YE'),

    'EU': ('AD', 'AL', 'AM', 'AT', 'AX', 'AZ', 'BA', 'BE', 'BG', 'BY', 'CH',
    'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FO', 'FR', 'GB', 'GE', 'GG',
    'GI', 'GR', 'HR', 'HU', 'IE', 'IM', 'IS', 'IT', 'JE', 'KZ', 'LI', 'LT',
    'LU', 'LV', 'MC', 'MD', 'ME', 'MK', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO',
    'RS', 'RU', 'SE', 'SI', 'SJ', 'SK', 'SM', 'TR', 'UA', 'VA'),

    'NA': ('AG', 'AI', 'AN', 'AW', 'BB', 'BL', 'BM', 'BS', 'BZ', 'CA',
    'CR', 'CU', 'DM', 'DO', 'GD', 'GL', 'GP', 'GT', 'HN', 'HT', 'JM',
    'KN', 'KY', 'LC', 'MF', 'MQ', 'MS', 'MX', 'NI', 'PA', 'PM', 'PR', 'SV',
    'TC', 'TT', 'UM', 'US', 'VC', 'VG', 'VI'),

    'OC': ('AS', 'AU', 'CK', 'FJ', 'FM', 'GU', 'KI', 'MH', 'MP', 'NC', 'NF',
    'NR', 'NU', 'NZ', 'PF', 'PG', 'PN', 'PW', 'SB', 'TK', 'TO', 'TV', 'UM',
    'VU', 'WF', 'WS'),

    'SA': ('AR', 'BO', 'BR', 'CL', 'CO', 'EC', 'FK', 'GF', 'GY', 'PE', 'PY',
    'SR', 'UY', 'VE')}

# TODO GEO: use this data for getting the country out of coordinates
class CountryBorder(models.Model): # {{{1
    """ contains multi polygons for each iso2 country code and for continent
    codes
    
    The data has been generated following the instructions on
    https://docs.djangoproject.com/en/1.3/ref/contrib/gis/tutorial/
    and dropping the non-needed columns from the database.

    """
    code = models.CharField(max_length=2)
    mpoly = models.MultiPolygonField()

    objects = models.GeoManager()

    class Meta:
        verbose_name_plural = "Country Borders"

    def __unicode__(self):
        return self.code

# TODO GEO: simplify the mpolys
class ContinentBorder(models.Model): # {{{1
    """ contains multi polygons for each continent code.

    The multi-polygons for the continents has been created with::

        from data.models import *
       
        for continent, countries in CONTINENT_COUNTRIES.items():
            p = CountryBorder.objects.get(code=countries[0]).mpoly
            for country in countries[1:]:
                p = p.union(CountryBorder.objects.get(code=country).mpoly)
            ContinentBorder.objects.create(code=continent, mpoly=p)

    Notice that ``union`` seems to be good enough on the original data.
    Example, being p1 the multi-polygon of Spain and p2 the multi-polygon of
    France, the union has less points that the addition of all points of both
    mutil-polygons::

        In : p1.num_points
        Out: 1655

        In : p2.num_points
        Out: 2007

        In : p = p1.union(p2)

        In : p.num_points
        Out: 3338

    >>> from grical.events.models import COUNTRIES
    >>> countries_keys = [t[0] for t in COUNTRIES]
    >>> countries_set = set()
    >>> for continent, countries in CONTINENT_COUNTRIES.items():
    ...     countries_set = countries_set.union(countries)
    ...     for country in countries:
    ...         assert country in countries_keys, country
    ...         coub = CountryBorder.objects.filter(code=country)
    ...         assert coub, 'country = ' + country
    ...         assert len(coub) == 1, 'len coub not 1'
    ...         coub = coub[0]
    ...         # FIXME GEO: con = ContinentBorder.objects.filter(mpoly__contains=coub.mpoly)
    ...         # assert con, 'con = ' + coub.code
    ...         # assert len(con) == 1, 'len con not 1'
    >>> # -1 because countries_keys contains WW for Word Wide:
    >>> countries_keys = len(countries_keys) - 1
    >>> assert countries_keys == CountryBorder.objects.all().count()
    >>> assert countries_keys == len(countries_set)

    >>> from django.contrib.gis.geos import Point
    >>> p = Point(-103.0, 41.2) # a point in the United States
    >>> con = ContinentBorder.objects.get(mpoly__contains = p)
    >>> cou = CountryBorder.objects.get(mpoly__contains = p)
    >>> assert con.code == 'NA', con
    >>> assert cou.code == 'US', cou

    >>> p = Point(-59.3, -9.0) # a point in Brazil
    >>> con = ContinentBorder.objects.get(mpoly__contains = p)
    >>> cou = CountryBorder.objects.get(mpoly__contains = p)
    >>> assert con.code == 'SA', con
    >>> assert cou.code == 'BR', cou

    >>> p = Point(10.3, 51.2) # a point in Germany
    >>> con = ContinentBorder.objects.get(mpoly__contains = p)
    >>> cou = CountryBorder.objects.get(mpoly__contains = p)
    >>> assert con.code == 'EU', con
    >>> assert cou.code == 'DE', cou
    """
    code = models.CharField(max_length = 2, choices = CONTINENTS)
    mpoly = models.MultiPolygonField()

    objects = models.GeoManager()

    class Meta:
        verbose_name_plural = "Continent Borders"

    def __unicode__(self):
        return self.code
