#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
# GPL {{{1
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

""" Models """

# imports {{{1
import random
import re
from re import UNICODE
import hashlib
import threading
import datetime
from smtplib import SMTPConnectError
from itertools import chain

import vobject

from django.contrib.contenttypes.models import ContentType
from django.contrib.comments import Comment
from django.contrib.comments.signals import comment_was_posted
from django.contrib.sites.models import Site
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.utils.encoding import smart_str, smart_unicode
from django.contrib.gis.db import models
# http://docs.djangoproject.com/en/1.2/topics/db/queries/#filters-can-reference-fields-on-the-model
#from django.db.models import Q
from django.contrib.gis.db.models import Q
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D # ``D`` is a shortcut for ``Distance``
from django.db.models.signals import pre_save, post_save, post_delete
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site

from django.forms import ValidationError

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.db import transaction
# FIXME from gridcalendar.events.decorators import autoconnect

from tagging.fields import TagField
from tagging.models import Tag, TaggedItem
import reversion
from reversion import revision
from reversion.models import Version, Revision, VERSION_ADD, VERSION_DELETE

from utils import validate_year, search_name, text_diff

# COUNTRIES {{{1
# TODO: use instead a client library from http://www.geonames.org/ accepting
# names (in different languages) and codes like e.g. ES, es,  ESP, eSp, 724,
# España, etc. Name colisions in different languages needs to be checked.
# OR use python.django.countries
# TODO: use the language selected by the user in all APIs
COUNTRIES = (
    ( 'AF', _( u'Afghanistan' ) ),
    ( 'AX', _( u'Åland Islands' ) ),
    ( 'AL', _( u'Albania' ) ),
    ( 'DZ', _( u'Algeria' ) ),
    ( 'AS', _( u'American Samoa' ) ),
    ( 'AD', _( u'Andorra' ) ),
    ( 'AO', _( u'Angola' ) ),
    ( 'AI', _( u'Anguilla' ) ),
    ( 'AQ', _( u'Antarctica' ) ),
    ( 'AG', _( u'Antigua and Barbuda' ) ),
    ( 'AR', _( u'Argentina' ) ),
    ( 'AM', _( u'Armenia' ) ),
    ( 'AW', _( u'Aruba' ) ),
    ( 'AU', _( u'Australia' ) ),
    ( 'AT', _( u'Austria' ) ),
    ( 'AZ', _( u'Azerbaijan' ) ),
    ( 'BS', _( u'Bahamas' ) ),
    ( 'BH', _( u'Bahrain' ) ),
    ( 'BD', _( u'Bangladesh' ) ),
    ( 'BB', _( u'Barbados' ) ),
    ( 'BY', _( u'Belarus' ) ),
    ( 'BE', _( u'Belgium' ) ),
    ( 'BZ', _( u'Belize' ) ),
    ( 'BJ', _( u'Benin' ) ),
    ( 'BM', _( u'Bermuda' ) ),
    ( 'BT', _( u'Bhutan' ) ),
    ( 'BO', _( u'Bolivia, Plurinational State of' ) ),
    ( 'BA', _( u'Bosnia and Herzegovina' ) ),
    ( 'BW', _( u'Botswana' ) ),
    ( 'BV', _( u'Bouvet Island' ) ),
    ( 'BR', _( u'Brazil' ) ),
    ( 'IO', _( u'British Indian Ocean Territory' ) ),
    ( 'BN', _( u'Brunei Darussalam' ) ),
    ( 'BG', _( u'Bulgaria' ) ),
    ( 'BF', _( u'Burkina Faso' ) ),
    ( 'BI', _( u'Burundi' ) ),
    ( 'KH', _( u'Cambodia' ) ),
    ( 'CM', _( u'Cameroon' ) ),
    ( 'CA', _( u'Canada' ) ),
    ( 'CV', _( u'Cape Verde' ) ),
    ( 'KY', _( u'Cayman Islands' ) ),
    ( 'CF', _( u'Central African Republic' ) ),
    ( 'TD', _( u'Chad' ) ),
    ( 'CL', _( u'Chile' ) ),
    ( 'CN', _( u'China' ) ),
    ( 'CX', _( u'Christmas Island' ) ),
    ( 'CC', _( u'Cocos (Keeling) Islands' ) ),
    ( 'CO', _( u'Colombia' ) ),
    ( 'KM', _( u'Comoros' ) ),
    ( 'CG', _( u'Congo' ) ),
    ( 'CD', _( u'Congo, the Democratic Republic of the' ) ),
    ( 'CK', _( u'Cook Islands' ) ),
    ( 'CR', _( u'Costa Rica' ) ),
    ( 'CI', _( u'Côte d\'Ivoire' ) ),
    ( 'HR', _( u'Croatia' ) ),
    ( 'CU', _( u'Cuba' ) ),
    ( 'CY', _( u'Cyprus' ) ),
    ( 'CZ', _( u'Czech Republic' ) ),
    ( 'DK', _( u'Denmark' ) ),
    ( 'DJ', _( u'Djibouti' ) ),
    ( 'DM', _( u'Dominica' ) ),
    ( 'DO', _( u'Dominican Republic' ) ),
    ( 'EC', _( u'Ecuador' ) ),
    ( 'EG', _( u'Egypt' ) ),
    ( 'SV', _( u'El Salvador' ) ),
    ( 'GQ', _( u'Equatorial Guinea' ) ),
    ( 'ER', _( u'Eritrea' ) ),
    ( 'EE', _( u'Estonia' ) ),
    ( 'ET', _( u'Ethiopia' ) ),
    ( 'FK', _( u'Falkland Islands (Malvinas)' ) ),
    ( 'FO', _( u'Faroe Islands' ) ),
    ( 'FJ', _( u'Fiji' ) ),
    ( 'FI', _( u'Finland' ) ),
    ( 'FR', _( u'France' ) ),
    ( 'GF', _( u'French Guiana' ) ),
    ( 'PF', _( u'French Polynesia' ) ),
    ( 'TF', _( u'French Southern Territories' ) ),
    ( 'GA', _( u'Gabon' ) ),
    ( 'GM', _( u'Gambia' ) ),
    ( 'GE', _( u'Georgia' ) ),
    ( 'DE', _( u'Germany' ) ),
    ( 'GH', _( u'Ghana' ) ),
    ( 'GI', _( u'Gibraltar' ) ),
    ( 'GR', _( u'Greece' ) ),
    ( 'GL', _( u'Greenland' ) ),
    ( 'GD', _( u'Grenada' ) ),
    ( 'GP', _( u'Guadeloupe' ) ),
    ( 'GU', _( u'Guam' ) ),
    ( 'GT', _( u'Guatemala' ) ),
    ( 'GG', _( u'Guernsey' ) ),
    ( 'GN', _( u'Guinea' ) ),
    ( 'GW', _( u'Guinea-Bissau' ) ),
    ( 'GY', _( u'Guyana' ) ),
    ( 'HT', _( u'Haiti' ) ),
    ( 'HM', _( u'Heard Island and McDonald Islands' ) ),
    ( 'VA', _( u'Holy See (Vatican City State)' ) ),
    ( 'HN', _( u'Honduras' ) ),
    ( 'HK', _( u'Hong Kong' ) ),
    ( 'HU', _( u'Hungary' ) ),
    ( 'IS', _( u'Iceland' ) ),
    ( 'IN', _( u'India' ) ),
    ( 'ID', _( u'Indonesia' ) ),
    ( 'IR', _( u'Iran, Islamic Republic of' ) ),
    ( 'IQ', _( u'Iraq' ) ),
    ( 'IE', _( u'Ireland' ) ),
    ( 'IM', _( u'Isle of Man' ) ),
    ( 'IL', _( u'Israel' ) ),
    ( 'IT', _( u'Italy' ) ),
    ( 'JM', _( u'Jamaica' ) ),
    ( 'JP', _( u'Japan' ) ),
    ( 'JE', _( u'Jersey' ) ),
    ( 'JO', _( u'Jordan' ) ),
    ( 'KZ', _( u'Kazakhstan' ) ),
    ( 'KE', _( u'Kenya' ) ),
    ( 'KI', _( u'Kiribati' ) ),
    ( 'KP', _( u'Korea, Democratic People\'s Republic of' ) ),
    ( 'KR', _( u'Korea, Republic of' ) ),
    ( 'KW', _( u'Kuwait' ) ),
    ( 'KG', _( u'Kyrgyzstan' ) ),
    ( 'LA', _( u'Lao People\'s Democratic Republic' ) ),
    ( 'LV', _( u'Latvia' ) ),
    ( 'LB', _( u'Lebanon' ) ),
    ( 'LS', _( u'Lesotho' ) ),
    ( 'LR', _( u'Liberia' ) ),
    ( 'LY', _( u'Libyan Arab Jamahiriya' ) ),
    ( 'LI', _( u'Liechtenstein' ) ),
    ( 'LT', _( u'Lithuania' ) ),
    ( 'LU', _( u'Luxembourg' ) ),
    ( 'MO', _( u'Macao' ) ),
    ( 'MK', _( u'Macedonia, the former Yugoslav Republic of' ) ),
    ( 'MG', _( u'Madagascar' ) ),
    ( 'MW', _( u'Malawi' ) ),
    ( 'MY', _( u'Malaysia' ) ),
    ( 'MV', _( u'Maldives' ) ),
    ( 'ML', _( u'Mali' ) ),
    ( 'MT', _( u'Malta' ) ),
    ( 'MH', _( u'Marshall Islands' ) ),
    ( 'MQ', _( u'Martinique' ) ),
    ( 'MR', _( u'Mauritania' ) ),
    ( 'MU', _( u'Mauritius' ) ),
    ( 'YT', _( u'Mayotte' ) ),
    ( 'MX', _( u'Mexico' ) ),
    ( 'FM', _( u'Micronesia, Federated States of' ) ),
    ( 'MD', _( u'Moldova, Republic of' ) ),
    ( 'MC', _( u'Monaco' ) ),
    ( 'MN', _( u'Mongolia' ) ),
    ( 'ME', _( u'Montenegro' ) ),
    ( 'MS', _( u'Montserrat' ) ),
    ( 'MA', _( u'Morocco' ) ),
    ( 'MZ', _( u'Mozambique' ) ),
    ( 'MM', _( u'Myanmar' ) ),
    ( 'NA', _( u'Namibia' ) ),
    ( 'NR', _( u'Nauru' ) ),
    ( 'NP', _( u'Nepal' ) ),
    ( 'NL', _( u'Netherlands' ) ),
    ( 'AN', _( u'Netherlands Antilles' ) ),
    ( 'NC', _( u'New Caledonia' ) ),
    ( 'NZ', _( u'New Zealand' ) ),
    ( 'NI', _( u'Nicaragua' ) ),
    ( 'NE', _( u'Niger' ) ),
    ( 'NG', _( u'Nigeria' ) ),
    ( 'NU', _( u'Niue' ) ),
    ( 'NF', _( u'Norfolk Island' ) ),
    ( 'MP', _( u'Northern Mariana Islands' ) ),
    ( 'NO', _( u'Norway' ) ),
    ( 'OM', _( u'Oman' ) ),
    ( 'PK', _( u'Pakistan' ) ),
    ( 'PW', _( u'Palau' ) ),
    ( 'PS', _( u'Palestinian Territory, Occupied' ) ),
    ( 'PA', _( u'Panama' ) ),
    ( 'PG', _( u'Papua New Guinea' ) ),
    ( 'PY', _( u'Paraguay' ) ),
    ( 'PE', _( u'Peru' ) ),
    ( 'PH', _( u'Philippines' ) ),
    ( 'PN', _( u'Pitcairn' ) ),
    ( 'PL', _( u'Poland' ) ),
    ( 'PT', _( u'Portugal' ) ),
    ( 'PR', _( u'Puerto Rico' ) ),
    ( 'QA', _( u'Qatar' ) ),
    ( 'RE', _( u'Réunion' ) ),
    ( 'RO', _( u'Romania' ) ),
    ( 'RU', _( u'Russian Federation' ) ),
    ( 'RW', _( u'Rwanda' ) ),
    ( 'BL', _( u'Saint Barthélemy' ) ),
    ( 'SH', _( u'Saint Helena' ) ),
    ( 'KN', _( u'Saint Kitts and Nevis' ) ),
    ( 'LC', _( u'Saint Lucia' ) ),
    ( 'MF', _( u'Saint Martin (French part)' ) ),
    ( 'PM', _( u'Saint Pierre and Miquelon' ) ),
    ( 'VC', _( u'Saint Vincent and the Grenadines' ) ),
    ( 'WS', _( u'Samoa' ) ),
    ( 'SM', _( u'San Marino' ) ),
    ( 'ST', _( u'Sao Tome and Principe' ) ),
    ( 'SA', _( u'Saudi Arabia' ) ),
    ( 'SN', _( u'Senegal' ) ),
    ( 'RS', _( u'Serbia' ) ),
    ( 'SC', _( u'Seychelles' ) ),
    ( 'SL', _( u'Sierra Leone' ) ),
    ( 'SG', _( u'Singapore' ) ),
    ( 'SK', _( u'Slovakia' ) ),
    ( 'SI', _( u'Slovenia' ) ),
    ( 'SB', _( u'Solomon Islands' ) ),
    ( 'SO', _( u'Somalia' ) ),
    ( 'ZA', _( u'South Africa' ) ),
    ( 'GS', _( u'South Georgia and the South Sandwich Islands' ) ),
    ( 'ES', _( u'Spain' ) ),
    ( 'LK', _( u'Sri Lanka' ) ),
    ( 'SD', _( u'Sudan' ) ),
    ( 'SR', _( u'Suriname' ) ),
    ( 'SJ', _( u'Svalbard and Jan Mayen' ) ),
    ( 'SZ', _( u'Swaziland' ) ),
    ( 'SE', _( u'Sweden' ) ),
    ( 'CH', _( u'Switzerland' ) ),
    ( 'SY', _( u'Syrian Arab Republic' ) ),
    ( 'TW', _( u'Taiwan, Province of China' ) ),
    ( 'TJ', _( u'Tajikistan' ) ),
    ( 'TZ', _( u'Tanzania, United Republic of' ) ),
    ( 'TH', _( u'Thailand' ) ),
    ( 'TL', _( u'Timor-Leste' ) ),
    ( 'TG', _( u'Togo' ) ),
    ( 'TK', _( u'Tokelau' ) ),
    ( 'TO', _( u'Tonga' ) ),
    ( 'TT', _( u'Trinidad and Tobago' ) ),
    ( 'TN', _( u'Tunisia' ) ),
    ( 'TR', _( u'Turkey' ) ),
    ( 'TM', _( u'Turkmenistan' ) ),
    ( 'TC', _( u'Turks and Caicos Islands' ) ),
    ( 'TV', _( u'Tuvalu' ) ),
    ( 'UG', _( u'Uganda' ) ),
    ( 'UA', _( u'Ukraine' ) ),
    ( 'AE', _( u'United Arab Emirates' ) ),
    ( 'GB', _( u'United Kingdom' ) ),
    ( 'US', _( u'United States' ) ),
    ( 'UM', _( u'United States Minor Outlying Islands' ) ),
    ( 'UY', _( u'Uruguay' ) ),
    ( 'UZ', _( u'Uzbekistan' ) ),
    ( 'VU', _( u'Vanuatu' ) ),
    ( 'VE', _( u'Venezuela, Bolivarian Republic of' ) ),
    ( 'VN', _( u'Viet Nam' ) ),
    ( 'VG', _( u'Virgin Islands, British' ) ),
    ( 'VI', _( u'Virgin Islands, U.S.' ) ),
    ( 'WF', _( u'Wallis and Futuna' ) ),
    ( 'EH', _( u'Western Sahara' ) ),
    ( 'WW', _( u'worldwide' ) ),
    ( 'YE', _( u'Yemen' ) ),
    ( 'ZM', _( u'Zambia' ) ),
    ( 'ZW', _( u'Zimbabwe' ) ),
 )

# EXAMPLE {{{1
EXAMPLE = u"""acronym: GriCal
title: GridCalendar presentation
start: 2010-12-29
starttime: 10:00
end: 2010-12-30
endtime: 18:00
tags: calendar software open-source gridmind gridcalendar
urls:
    code    http://example.com
    web    http://example.org
address: Gleimstr. 6
postcode: 10439
city: Berlin
country: DE
coordinates: 52.55247, 13.40364
deadlines:
    2009-11-01    visitor tickets
    2010-10-01    call for papers
sessions:
    2010-12-29    10:00-11:00    first presentation
    2010-12-29    15:00-16:00    second presentation
    2010-12-30    15:00-16:00    third presentation
description:

GridCalendar will be presented"""

# TODO: add alters_data=True to all functions that do that.
# see http://docs.djangoproject.com/en/1.2/ref/templates/api/

# regexes {{{1
DATE_REGEX = re.compile( r'\b(\d\d\d\d)-(\d\d)-(\d\d)\b', UNICODE )
COORDINATES_REGEX = re.compile(
        r'\s*([+-]?\s*\d+(?:\.\d*)?)\s*[,;:+| ]\s*([+-]?\s*\d+(?:\.\d*)?)' )

class EventManager( models.GeoManager ): # {{{1
    """ manager for deserialization.

    See http://docs.djangoproject.com/en/1.3/topics/serialization/#deserialization-of-natural-keys
    """
    def get_by_natural_key(self, title, start):
        """ returns an event with a given ``title`` and ``start`` """
        return self.get( title = title, start = start )

class Event( models.Model ): # {{{1 pylint: disable-msg=R0904
    """ Event model """ # doc {{{2
    # fields {{{2
    objects = EventManager()
    user = models.ForeignKey( User, editable = False, related_name = "owner",
            blank = True, null = True, verbose_name = _( u'User' ) )
    """The user who created the event or null if AnonymousUser""" # pyling: disable-msg=W0105
    creation_time = models.DateTimeField(
            _( u'Creation time' ), editable = False, auto_now_add = True )
    """Time stamp for event creation""" # pyling: disable-msg=W0105
    modification_time = models.DateTimeField( _( u'Modification time' ),
            editable = False, auto_now = True )
    """Time stamp for event modification""" # pyling: disable-msg=W0105
    acronym = models.CharField( _( u'Acronym' ), max_length = 20, blank = True,
            null = True, help_text = _( u'Example: 26C3' ) )
    title = models.CharField( _( u'Title' ), max_length = 200, blank = False,
            help_text = _( u'Example: Demonstration against software patents' ) )
    start = models.DateField( _( u'Start date' ), blank = False,
            help_text = _( u"Example: 2010-08-25"),
            validators = [validate_year] )
    end = models.DateField( _( u'End date' ), null = True, blank = True,
            help_text = _( u"Example: 2010-08-26"),
            validators = [validate_year] )
    upcoming = models.DateField( _( u'Upcoming deadline or start' ),
            editable = False, db_index = True )
    starttime = models.TimeField( 
            _( u'Start time' ), blank = True, null = True )
    endtime = models.TimeField( 
            _( u'End time' ), blank = True, null = True )
    tags = TagField( _( u'Tags' ), blank = True, null = True,
        help_text = _( u''.join( [u"Tags are case insensitive. Only letters ",
            u"(these can be international, like: αöł), digits and hyphens (-)",
            u"are allowed. Tags are separated with spaces. Example: ",
            u"demonstration software-patents"] ) ) )
    country = models.CharField( _( u'Country' ), blank = True, null = True,
            max_length = 2, choices = COUNTRIES )
    city = models.CharField( 
            _( u'City' ), blank = True, null = True, max_length = 50 )
    postcode = models.CharField( _( u'Postcode' ), blank = True, null = True,
            max_length = 16 )
    address = models.CharField( _( u'Address' ), blank = True,
            null = True, max_length = 100, # TODO: increase to 200
            help_text = _( u'Complete address including city and country' ) )
    coordinates = models.PointField( _('Coordinates'),
            editable = False, blank=True, null=True )
    """ used for calculating events within a distance to a point """
    description = models.TextField(
            _( u'Description' ), blank = True, null = True )
    # old code before switching to postgis with the new geo field coordiantes
    # latitude = models.FloatField( _( u'Latitude' ), blank = True, null = True,
    #         help_text = _( u'In decimal degrees, not ' \
    #         u'degrees/minutes/seconds. Prefix with "-" for South, no sign ' \
    #         u'for North' ) )
    # longitude = models.FloatField( _( u'Longitude' ), blank = True, null = True,
    #         help_text = _( u'In decimal degrees, not ' \
    #             u'degrees/minutes/seconds. Prefix with "-" for West, no ' \
    #             u'sign for East' ) )

    # convienent properties {{{2
    # custom latitude and longitude properties which raise an error when
    # setting them when self.coordinates is not initialized
    # Custom latitude property
    def _get_latitude(self):
        if self.coordinates:
            return self.coordinates.y
        return None
    def _set_latitude(self, value): self.coordinates.y = value
    latitude = property(_get_latitude,_set_latitude)
    # Custom longitude property
    def _get_longitude(self):
        if self.coordinates:
            return self.coordinates.x
        return None
    def _set_longitude(self, value): self.coordinates.x = value
    longitude = property(_get_longitude,_set_longitude)

    # Meta {{{2
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        verbose_name = _( u'Event' )
        verbose_name_plural = _( u'Events' )
        unique_together = (('title', 'start'),)
        # get_latest_by = "start" #TODO: useful? see also # http://docs.djangoproject.com/en/1.3/ref/generic-views/#date-based-generic-views
        # needed for proper order of e.g. master_event.instances:
        ordering = ['upcoming'] # TODO: see sql queries because this may make
                                # everything too slot

    # methods {{{2
    def natural_key(self): # {{{3
        """ used for serialization.

        See http://docs.djangoproject.com/en/1.3/topics/serialization/#serialization-of-natural-keys
        """
        return ( self.title, self.start )

    def tags_separated_by_comma(self): #{{{3
        """ returns the list of tags separated by commas as unicode string """
        return self.tags.replace(' ',',')
    
    def color_nr(self, #{{{3
            days_colors = {84:9, 56:8, 28:7, 14:6, 7:5, 3:4, 2:3, 1:2, 0:1}):
        """ Returns a number according to
        :attr:`Event.upcoming`.

        For default parameter ``days_colors``:

        +------------------------------+---+
        | today                        | 0 |
        +------------------------------+---+
        | tomorrow                     | 1 |
        +------------------------------+---+
        | after tomorrow               | 2 |
        +------------------------------+---+
        | after after tomorrow         | 3 |
        +------------------------------+---+
        | more than 3 days             | 4 |
        +------------------------------+---+
        | more than 7 days             | 5 |
        +------------------------------+---+
        | more than 14 days            | 6 |
        +------------------------------+---+
        | more than 1 month  (28 days) | 7 |
        +------------------------------+---+
        | more than 3 month  (56 days) | 8 |
        +------------------------------+---+
        | more than 4 months (84 days) | 9 |
        +------------------------------+---+

        """
        today = datetime.date.today()
        upcoming = self.upcoming
        keys = days_colors.keys()
        keys.sort()
        keys.reverse()
        for days in keys:
            days_from_today = (upcoming - today).days
            if days_from_today >= days:
                return days_colors[days]
        # FIXME: include a different color-palette for past events:
        return 0

    def next_coming_date_or_start(self): #{{{3
        """ returns the next most proximate date of an event to today, which
        can be the start date, the end date or one of the deadlines; otherwise
        it returns the start date if all are in the past
        
        >>> from datetime import timedelta
        >>> today = datetime.date.today()
        >>> event = Event(title="test for n_c_d " + today.isoformat(),
        ...     start=timedelta(days=1)+today,
        ...     end=timedelta(days=2)+today,
        ...     tags="test")
        >>> event.save()
        >>> assert today + timedelta(days=1) == event.next_coming_date_or_start()
        >>> today = datetime.date.today()
        >>> event3 = Event(title="test 3 for n_c_d " + today.isoformat(),
        ...     start=timedelta(days=3)+today, tags="test")
        >>> event3.save()
        >>> event2 = Event(title="test 2 for n_c_d " + today.isoformat(),
        ...     start=timedelta(days = -1)+today,
        ...     end=timedelta(days=2)+today,
        ...     tags="test")
        >>> event2.save()
        >>> event1 = Event(title="test 1 for n_c_d " + today.isoformat(),
        ...     start=timedelta(days=2)+today, tags="test")
        >>> event1.save()
        >>> event1_deadline = EventDeadline(
        ...         event = event1, deadline_name = "test1",
        ...         deadline = today)
        >>> event1_deadline.save()
        >>> list_events = [event3, event2, event1]
        >>> sorted_list = sorted(list_events, key=Event.next_coming_date_or_start)
        >>> assert sorted_list[0] == event1
        >>> assert sorted_list[1] == event2
        >>> assert sorted_list[2] == event3
        >>> event.delete()
        >>> event1.delete()
        >>> event2.delete()
        >>> event3.delete()
        """
        # creates a list with all dates of the event (self)
        dates = []
        dates.append(self.start)
        if self.end:
            dates.append(self.end)
        deadlines = EventDeadline.objects.filter(event=self)
        if deadlines:
            for deadline in deadlines:
                dates.append(deadline.deadline)
        today = datetime.date.today()
        # creates a list of deltas of the dates to today
        deltas = map(lambda d: d - today, dates)
        # removes negative deltas from the past
        deltas = filter(lambda n: n.days >= 0, deltas)
        if len(deltas) > 0:
            # returns the smallest date
            return today + ( sorted(deltas)[0] )
        else:
            return self.start

    def next_deadline_names( self ): #{{{3
        """ return the name of the next deadline or None """
        date = self.next_coming_date_or_start()
        if date == self.start:
            return None
        deadlines = EventDeadline.objects.filter(
                event = self, deadline = date )
        if not deadlines:
            return None
        return ", ".join( [ d.deadline_name for d in deadlines ] )

    def icalendar( self, ical = None ): #{{{3
        """ returns an iCalendar object of the event entry or add it to 'ical'

        >>> events = Event.objects.filter( title='GridCalendar presentation',
        ...     start='2010-12-29' )
        >>> if events: events.delete()
        >>> event = Event.parse_text(EXAMPLE)
        >>> ical = event.icalendar()
        >>> ical = vobject.readOne(ical.serialize())
        >>> assert (ical.vevent.categories.serialize() == 
        ...  u'CATEGORIES:calendar,software,open-source,gridmind,gridcalendar\\r\\n')
        >>> event.delete()
        """
        if ical is None:
            ical = vobject.iCalendar()
            ical.add('METHOD').value = 'PUBLISH' # IE/Outlook needs this
            ical.add('PRODID').value = settings.PRODID
        vevent = ical.add('vevent')
        vevent.add('SUMMARY').value = self.title
        if self.starttime:
            vevent.add('DTSTART').value = datetime.datetime.combine(
                    self.start, self.starttime )
            # TODO: get tzinfo from city and country
        else:
            vevent.add('DTSTART').value = self.start
        if self.tags:
            vevent.add('CATEGORIES').value = self.tags.split(u' ')
        location = ""
        # rfc5545 specifies CRLF for new lines:
        if self.address:
            location = self.address + " "
        if self.postcode:
            location = location + self.postcode + " "
        if self.city:
            location = location + self.city + " "
        if self.country:
            location = location + self.country + " "
        vevent.add('LOCATION').value = location
        vevent.add('UID').value = \
                Site.objects.get_current().name + u'-' + \
                hashlib.md5(settings.PROJECT_ROOT).hexdigest() + u'-' \
                + unicode(self.id) + u'@' + \
                Site.objects.get_current().domain
        if self.end:
            if self.endtime:
                vevent.add('DTEND').value = datetime.datetime.combine(
                        self.end, self.endtime )
                # TODO: get tzinfo from city and country
            else:
                vevent.add('DTEND').value = self.end
        if self.description: vevent.add('DESCRIPTION').value = self.description
        # see rfc5545 3.8.7.2. Date-Time Stamp
        vevent.add('DTSTAMP').value = self.modification_time
        vevent.add('CLASS').value = 'PUBLIC'
        if self.coordinates:
            vevent.add('GEO').value = \
                unicode(self.coordinates.y) +u";"+ unicode(self.coordinates.x)
        # TODO: add deadlines. As VALARMs or there is something better in
        # rfc5545 ?
        # TODO: think of options for decentralization commented on
        # http://linuxwiki.de/Zentralkalender
        return ical

    # this is a workarround described at http://code.djangoproject.com/ticket/10227
    def _get_recurring( self ):
        """ returns the recurrence instance associated with ``self`` or None
        """
        try:
            return self._recurring
        except Recurrence.DoesNotExist:
            return None
    def _set_recurring( self, value ):
        self._recurring = value
    recurring = property( _get_recurring, _set_recurring )

    def clone( self, user, except_models = [], recurrence=True, **kwargs ):#{{{3
        """ Makes, saves and return a deep clone of the event as an 
        event of the user ``user``, and stores from which event the clone was
        made of in the table defined in :class:`Recurrence` (unless the
        parameter ``recurrence`` is False)

        Notice that because there cannot be two events with the same title and
        start date, either 'title' or 'start' must be used in **kwargs.

        If ``self`` has a master in :class:`Recurrence`, the master
        of the returned clone in :class:`Recurrence` will be set to the same
        master.
        
        This method makes a clone of all related objects, and relates them to
        the new created clone, except for the models in ``except_models``,
        which are ignored.

        ``kwargs`` can contain field names and values to replace in the clone
        the original of ``self``, e.g. ``{"start": today()}``

        >>> from events.models import Event
        >>> from django.utils.encoding import smart_str
        >>> import datetime
        >>> now_t = datetime.datetime.now().isoformat()
        >>> today = datetime.date.today()
        >>> today_t = today.isoformat()
        >>> user = User.objects.create( username = unicode(now_t) )
        >>> events = Event.objects.filter( title='GridCalendar presentation',
        ...     start='2010-12-29' )
        >>> if events: events.delete()
        >>> event = Event.parse_text(EXAMPLE)
        >>> clone = event.clone( user, start = today )
        >>> clone_text = clone.as_text()
        >>> clone_text = clone_text.replace(
        ...     today_t, event.start.isoformat(), 1 )
        >>> assert ( event.as_text() == clone_text )
        >>> event.delete()
        >>> clone.delete()
        """
        clone = Event()
        for field in self.get_simple_fields():
            if kwargs.has_key( field ):
                setattr( clone, field, kwargs[field] )
            else: 
                setattr( clone, field, getattr(self, field) )
        # Dealing now with :attr:`Event.description` which is not returned by
        # :meth:`Event.get_simple_fields` (see above)
        assert u'description' in [unicode(f.name) for f in Event._meta.fields]
        if kwargs.has_key( 'description' ):
            clone.description = kwargs['description']
        else:
            clone.description = self.description
        if recurrence and self.recurring:
            # we want to take into consideration recurrences AND self is a
            # recurrence of a serie
            if self.recurring.master == self:
                # self is the master of the recurrence: we make clone a new
                # recurrence of the serie
                self.recurrences.create( event = clone )
            else: # self is a recurrence of another master
                self.recurring.master.recurrences.create( event = clone )
        clone.user = user
        for key, value in kwargs.items():
            if key == 'user':
                continue
            setattr( clone, key, value )
        clone.save() # we need the id # TODO: ask in the ML if there is other option
        related_models = [EventDeadline, EventSession, EventUrl] # TODO: get the list automatically
        try: # because we need to delete the clone if something goes wrong
            new_objs = [] # list of new related objects
            # we now traverse all related models and its objects
            for model in ( related_models ):
                if model == Event or model in except_models:
                    continue
                # next line is not the proper thing to do hear because for
                # instance urls from clones of clone are also returned
                # for pk, obj in collected_objs[ model ].sub_objs.iteritems():
                assert hasattr( model, 'event' )
                for obj in model.objects.filter( event = self ):
                    # Notice that in order for the next line to work, we expect
                    # all models with a reference to Event have a method called
                    # ``clone`` with two parameters: an event (to reference to)
                    # and a user
                    new_obj =  obj.clone( clone, user ) 
                    if new_obj: # some clone methods return None,thus the check
                        new_objs.append( new_obj )
            # TODO: if DEBUG is False when running the tests, this code is not
            # executed. Make that this code is always executed when running the
            # tests
            if settings.DEBUG:
                # we check that there are no references to the old objects in
                # the new objects.
                field_keys = []
                for model in [mod.__class__ for mod in new_objs]:
                    for field in model._meta.fields: # pylint: disable-msg=W0212
                        if isinstance( field, models.ForeignKey ) and \
                                field.rel.to in related_models:
                            field_keys.append( field )
                for obj in new_objs:
                    for field_key in field_keys:
                        if hasattr( ojb, "%s_id" % field_key.name ):
                            field_key_value = getattr( obj, "%s_id" % field_key.name )
                            if field_key_value in collected_objs[field_key.rel.to]:
                                raise RuntimeError( str(field_key_value) + " " +
                                        str(field_key) )
        except:
            # something went wrong, we delete the objects
            for obj in new_objs:
                obj.delete()
            clone.delete() # this deletes also the entries in Recurrence
            raise
        return clone

    def set_tags( self, tags ): #{{{3
        "set tags"
        Tag.objects.update_tags( self, tags )

    def get_tags( self ): #{{{3
        "get tags"
        return Tag.objects.get_for_object( self )


    def __unicode__( self ): #{{{3
        return self.start.isoformat() + u" : " + self.title

    @models.permalink
    def get_absolute_url( self ): #{{{3
        "get URL of an event"
        return ( 'event_show_all', (), {'event_id': self.id,} )

    def save( self, *args, **kwargs ): #{{{3
        """ Marks an event as new or not (for :meth:`Event.post_save) and call
        the real 'save' function after updating :attr:`Event.upcoming`."""
        try:
            Event.objects.get( id = self.id )
            self.not_new = True # Event.post_save uses this
        except Event.DoesNotExist:
            pass
        self.upcoming = self.next_coming_date_or_start()
        # Call the "real" save() method:
        super( Event, self ).save( *args, **kwargs )

    @staticmethod # def post_save( sender, **kwargs ): {{{3
    def post_save( sender, **kwargs ):
        """ notify users if a filter of a user matches an event but only for
        new events.
        """
        # TODO: don't notify the user submitting the change
        event = kwargs['instance']
        if event.recurring:
            # this event is an instance of a serie of recurring events
            return
        # TODO: users might also want to be informed of changes
        # not_new is set by Event.save
        if hasattr(event, "not_new") and event.not_new:
            return
        # FIXME: implement a Queue, see comments on 
        # http://www.artfulcode.net/articles/threading-django/
        # Thing also that getting an Exception here shouldn't propagate to the
        # view.
        thread = threading.Thread(
                target = Filter.notify_users_when_wanted( event ),
                args = [ event, ] )
        thread.setDaemon(True)
        thread.start()

    @staticmethod # def example(): {{{3
    def example():
        """ returns an example of an event as unicode
        
        >>> from django.utils.encoding import smart_str
        >>> events = Event.objects.filter( title='GridCalendar presentation',
        ...     start='2010-12-29' )
        >>> if events: events.delete()
        >>> example = Event.example()
        >>> event = Event.parse_text(example)
        >>> assert (smart_str(example) == event.as_text())
        >>> text = example.replace(u'DE', u'Germany')
        >>> event.delete()
        >>> event = Event.parse_text(text)
        >>> assert (smart_str(example) == event.as_text())
        >>> text = text.replace(u'Germany', u'de')
        >>> event.delete()
        >>> event = Event.parse_text(text)
        >>> assert (smart_str(example) == event.as_text())
        >>> event.delete()
        """
        return EXAMPLE

    @staticmethod # def list_as_text( iterable ): {{{3
    def list_as_text( iterable ):
        """ returns an utf-8 string of all events in ``iterable`` """
        text = ''
        for event in iterable:
            text += '\nEVENT: BEGIN --------------------\n'
            text += event.as_text()
            text += '\nEVENT: END ----------------------\n'
        return text

    def as_text( self ): #{{{3
        """ Returns a unix multiline utf-8 string representation of the
        event."""
        # this code is tested with a doctest in the staticmethod example()
        to_return = u""
        for keyword in Event.get_priority_list():
            if keyword == u'title':
                to_return += keyword + u": " + self.title + u"\n"
            elif keyword == u'start':
                to_return += u''.join( [
                    keyword, u": ",
                    unicode(self.start.strftime( "%Y-%m-%d" )), u"\n"] )
            elif keyword == u'starttime':
                if self.starttime:
                    to_return += u''.join( [
                        keyword, u": ",
                        unicode(self.starttime.strftime( "%H:%M" )), u"\n"] )
            elif keyword == u'end':
                if self.end:
                    to_return += u''.join( [
                        keyword, u": ",
                        unicode(self.end.strftime( "%Y-%m-%d")),
                        u"\n"] )
            elif keyword == u'endtime':
                if self.endtime:
                    to_return += u''.join( [
                        keyword, u": ",
                        unicode(self.endtime.strftime( "%H:%M" )), u"\n"] )
            elif keyword == u'country':
                if self.country:
                    to_return += keyword + u": " + self.country + u"\n"
            elif keyword == u'coordinates':
                if self.coordinates:
                    to_return += u"coordinates: %s, %s\n" % (
                            unicode( self.coordinates.y ),
                            unicode( self.coordinates.x ) )
            elif keyword == u'acronym':
                if self.acronym:
                    to_return += keyword + u": " + self.acronym + u"\n"
            elif keyword == u'tags':
                if self.tags:
                    to_return += keyword + u": " + self.tags + u"\n"
            elif keyword == u'address':
                if self.address:
                    to_return += keyword + u": " + self.address + u"\n"
            elif keyword == u'city':
                if self.city:
                    to_return += keyword + u": " + self.city + u"\n"
            elif keyword == u'postcode':
                if self.postcode:
                    to_return += keyword + u": " +  self.postcode + u"\n"
            elif keyword == u'urls':
                urls = EventUrl.objects.filter( event = self.id )
                if urls and len( urls ) > 0:
                    to_return += u"urls:\n"
                    for url in urls:
                        to_return += u''.join( [
                                u"    ", url.url_name, u' ', url.url, u"\n"] )
            elif keyword == u'deadlines':
                deadlines = EventDeadline.objects.filter( event = self.id )
                if deadlines and len( deadlines ) > 0:
                    to_return += u"deadlines:\n"
                    for deadline in deadlines:
                        to_return += u"".join( [
                            u"    ",
                            unicode(deadline.deadline.strftime("%Y-%m-%d")),
                            u'    ',
                            deadline.deadline_name,
                            u"\n",
                            ] )
            elif keyword == u'sessions':
                sessions = EventSession.objects.filter( event = self.id )
                if sessions and len( sessions ) > 0:
                    to_return += u"sessions:\n"
                    for session in sessions:
                        to_return = u"".join( [
                            to_return,
                            u"    ",
                            unicode(
                                session.session_date.strftime("%Y-%m-%d")),
                            u"    ",
                            unicode(
                                session.session_starttime.strftime("%H:%M")),
                            "-",
                            unicode(
                                session.session_endtime.strftime( "%H:%M" )),
                            u"    ",
                            session.session_name,
                            u'\n'] )
            elif keyword == u'description':
                if self.description:
                    to_return += u'description:\n' + self.description
            else:
                raise RuntimeError('unexpected keyword: ' + keyword)
        return smart_str(to_return)

    @staticmethod # def get_fields( text ): {{{3
    def get_fields( text ):
        """ parse an event as unicode text and returns a tuple with two
        dictionaries, or raises a ValidationError.

        The first dictionary contains the names of simple fields as keys and
        its values as values.

        The second dictionary contains the names of complex fields as keys, and
        lists as values. The list contains all lines including the first one
        with the name of the field.

        >>> example = Event.example()
        >>> s,c = Event.get_fields(example)
        >>> s[u'acronym']
        u'GriCal'
        >>> s[u'address']
        u'Gleimstr. 6'
        >>> s[u'city']
        u'Berlin'
        >>> s[u'country']
        u'DE'
        >>> s[u'end']
        u'2010-12-30'
        >>> s[u'endtime']
        u'18:00'
        >>> s[u'coordinates']
        u'52.55247, 13.40364'
        >>> s[u'postcode']
        u'10439'
        >>> s[u'start']
        u'2010-12-29'
        >>> s[u'starttime']
        u'10:00'
        >>> s[u'tags']
        u'calendar software open-source gridmind gridcalendar'
        >>> s[u'title']
        u'GridCalendar presentation'
        >>> c[u'description'][2]
        u'GridCalendar will be presented'
        >>> c[u'deadlines'][1].replace(' ','')
        u'2009-11-01visitortickets'
        >>> c[u'deadlines'][2].replace(' ','')
        u'2010-10-01callforpapers'
        >>> c['deadlines'][3]
        Traceback (most recent call last):
            ...
        IndexError: list index out of range
        """
        if not isinstance(text, unicode):
            text = smart_unicode(text)
        simple_list = Event.get_simple_fields()
        complex_list = Event.get_complex_fields()
        simple_dic = {}  # to be returned, see docstring of this method
        complex_dic = {} # to be returned, see docstring of this method
        syns = Event.get_synonyms()
        current = None # current field being parsed
        lines = list() # lines belonging to current field
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*(.*?)\s*$")
        # group 1 is the name of the field, group 2 is the value
        empty_line_p = re.compile(r"^\s*$")
        line_counter = 0
        for line in text.splitlines():
            line_counter += 1
            if current and current == "description":
                if empty_line_p.match(line):
                    lines.append('')
                else:
                    lines.append(line)
                continue
            # empty lines, if not in 'description', are ignored
            if empty_line_p.match(line):
                continue
            field_m = field_p.match(line)
            if current: # a complex field is being processed
                if field_m: # new field, storing previous one and resetting
                    assert(len(lines) > 0)
                    complex_dic[current] = lines
                    current = None
                    lines = list()
                else:
                    if re.match(r"[^\s]", line[0]):
                        raise ValidationError(_(
                            "extra lines for %(field_name)s must start with " \
                            + "identation") % {'field_name': current,})
                    lines.append(line)
                    continue
            if (not current) and not field_m:
                raise ValidationError(_(
                        "line number %(number)d is wrong: %(line)s") % \
                                {'number': line_counter, 'line': line})
            if not syns.has_key(field_m.group(1).lower()):
                raise ValidationError(_(u"wrong field name: ") + field_m.group(1))
            if syns[field_m.group(1).lower()] in simple_list:
                simple_dic[ syns[field_m.group(1).lower()] ] = field_m.group(2)
                continue
            if not syns[field_m.group(1).lower()] in complex_list:
                raise RuntimeError("field %s was not in 'complex_list'" %
                        field_m.group(1))
            current = syns[field_m.group(1).lower()]
            lines.append(line)
        if current:
            complex_dic[current] = lines
        return simple_dic, complex_dic

    # parse_text {{{3
    @staticmethod
    @revision.create_on_success # see https://github.com/etianen/django-reversion/wiki/Low-Level-API
    @transaction.commit_on_success # see http://docs.djangoproject.com/en/1.3/topics/db/transactions/#controlling-transaction-management-in-views
    def parse_text( input_text_in, event_id = None, user_id = None ):
        # doc {{{4
        """It parses a text and saves it as a single event in the data base and
        return the event object, or doesn't save the event and raises a
        ValidationError or a Event.DoesNotExist or a User.DoesNotExist or a
        RuntimeError.

        It raises a ValidationError when the data is wrong, e.g. when a date is
        not valid. It raises and Event.DoesNotExist error when there is no
        event with ``event_id``. It raises a User.DoesNotExist when there is no
        user with ``user_id``.

        A text to be parsed as an event is of the form::

            title: a title
            tags: tag1 tag2 tag3
            start: 2020-01-30 10:00
            ...

        There are synonyms for the names of the fields, like e.g. 't' for
        'title'. See get_synonyms()

        The text for the field 'urls' is of the form::
            urls: web_url
                name1  name1_url
                name2  name2_url
                ...

        The idented lines are optional. If web_url is present, it will be saved
        with the url_name 'url'

        The text for the field 'deadlines' is of the form::

            deadlines: deadline_date
                deadline1_date deadline1_name 
                deadline2_date deadline2_name 
                ...

        The idented lines are optional. If deadline_date is present, it will be
        saved with the deadline_name 'deadline'

        The text for the field 'sessions' is of the form::

            sessions: session_date session_starttime-session_endtime
              session1_date session1_starttime-session1_endtime session1_name
              session2_date session2_starttime-session2_endtime session2_name
              ...

        The idented lines are optional. If session_date is present, it will be
        saved with the session_name 'session'

        """
        # code {{{4
        if not isinstance(input_text_in, unicode):
            input_text_in = smart_unicode(input_text_in)
        # test that the necessary fields are present
        simple_fields, complex_fields = Event.get_fields(input_text_in)
        for field in Event.get_necessary_fields():
            if not (simple_fields.has_key(field) or
                    complex_fields.has_key(field)):
                raise ValidationError(
                        _(u"The following necessary field is not present: ") +
                        smart_unicode(field))
        if user_id is not None:
            # the following line can raise a User.DoesNotExist
            user = User.objects.get(id = user_id)
        else:
            user = None
        revision.user = user
        # Check if the country is in Englisch (instead of the international
        # short two-letter form) and replace it. TODO: check in other
        # languages but taking care of colisions
        if simple_fields.has_key(u'country'):
            for names in COUNTRIES:
                long_name = names[1].lower()
                short_name = names[0].lower()
                parsed = simple_fields[u'country'].lower()
                if parsed == long_name or parsed == short_name:
                    simple_fields['country'] = names[0]
                    break
        # creates an event with a form
        from gridcalendar.events.forms import EventForm
        if event_id == None :
            event_form = EventForm( simple_fields )
        else:
            # the following line can raise an Event.DoesNotExist
            event = Event.objects.get( id = event_id )
            event_form = EventForm( simple_fields, instance = event )
        # processing description
        if complex_fields.has_key(u'description'):
            description = u"\n".join(complex_fields[u'description'])
            # remove the word 'description'
            event_form.data['description'] = description[13:]
            del complex_fields[u'description']
        # testing data
        if not event_form.is_valid():
            raise ValidationError(event_form.errors.as_text())
        # save the event from the form
        event = event_form.save()
        event.user = None
        # urls {{{5
        if complex_fields.has_key(u'urls'):
            urls = EventUrl.get_urls(
                    u'\n'.join(complex_fields[u'urls']) )
            event_urls = list() # stores EventURLs to be saved at the end
            for url_name, url in urls.items():
                try:
                    previous_event_url = EventUrl.objects.get(
                            event=event, url_name=url_name)
                except EventUrl.DoesNotExist:
                    event_url = EventUrl(event=event, url_name=url_name, url=url)
                    # see
                    # http://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects
                    event_url.full_clean()
                    event_urls.append(event_url)
                else:
                    previous_event_url.url = url
                    assert(previous_event_url.url_name == url_name)
                    assert(previous_event_url.event == event)
                    previous_event_url.full_clean()
                    event_urls.append(previous_event_url)
            assert(len(event_urls) == len(urls))
            # save all
            for event_url in event_urls:
                event_url.save()
            # delete old urls of the event which are not in ``text`` parameter
            event_urls = EventUrl.objects.filter(event=event)
            for event_url in event_urls:
                if not urls.has_key(event_url.url_name):
                    event_url.delete()
            del complex_fields[u'urls']
        # deadlines {{{5
        if complex_fields.has_key(u'deadlines'):
            deadlines = EventDeadline.get_deadlines(
                    u'\n'.join(complex_fields[u'deadlines']))
            event_deadlines = list() # stores EventDeadline instances to be saved
                                     # at the end
            for name, deadline in deadlines.items():
                try:
                    previous_event_deadline = EventDeadline.objects.get(
                            event=event, deadline_name=name)
                except EventDeadline.DoesNotExist:
                    event_deadline = EventDeadline(event=event, deadline_name=name,
                            deadline=deadline)
                    # see
                    # http://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects
                    event_deadline.full_clean()
                    event_deadlines.append(event_deadline)
                else:
                    previous_event_deadline.deadline = deadline
                    assert(previous_event_deadline.deadline_name == name)
                    assert(previous_event_deadline.event == event)
                    previous_event_deadline.full_clean()
                    event_deadlines.append(previous_event_deadline)
            assert(len(event_deadlines) == len(deadlines))
            # save all
            for event_deadline in event_deadlines:
                event_deadline.save()
            # delete old deadlines of the event which are not in ``text`` parameter
            event_deadlines = EventDeadline.objects.filter(event=event)
            for event_deadline in event_deadlines:
                if not deadlines.has_key(event_deadline.deadline_name):
                    event_deadline.delete()
            del complex_fields[u'deadlines']
        # sessions {{{5
        if complex_fields.has_key(u'sessions'):
            sessions = EventSession.get_sessions(
                    u'\n'.join(complex_fields[u'sessions']) )
            event_sessions = list() # stores EventSessions to be saved at the end
            for session in sessions:
                try:
                    # check if there is an EventSession with the same name
                    previous_event_session = EventSession.objects.get(
                            event = event, session_name = session.name)
                except EventSession.DoesNotExist:
                    event_session = EventSession(
                            event = event,
                            session_name = session.name,
                            session_date = session.date,
                            session_starttime = session.start,
                            session_endtime = session.end)
                    # see
                    # http://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects
                    event_session.full_clean()
                    event_sessions.append(event_session)
                else:
                    previous_event_session.session_date = session.date
                    previous_event_session.session_starttime = session.start
                    previous_event_session.session_endtime = session.end
                    previous_event_session.full_clean()
            # save all
            for event_session in event_sessions:
                event_session.save()
            # delete old sessions of the event which are not in ``text`` parameter
            event_sessions = EventSession.objects.filter(event=event)
            for event_session in event_sessions:
                found = False
                for session in sessions:
                    if session.name == event_session.session_name:
                        found = True
                        break
                if not found:
                    event_session.delete()
            del complex_fields[u'sessions']
        # recurring {{{5
        if complex_fields.has_key(u'recurring'):
            date_regex = re.compile(r"^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$")
            dates = list()
            for date in complex_fields[u'recurring'][1:]:
                matcher = date_regex.match(date)
                try:
                    if not matcher:
                        raise ValueError()
                    dates.append( datetime.date( int(matcher.group(1)),
                        int(matcher.group(2)), int(matcher.group(3)) ) )
                except ValueError: # raised by date() or by int()
                    raise ValidationError( _(
                        u'date not in iso format (yyyy-mm-dd): %(date)s') % \
                                {'date': date} )
                # we do not clone deadlines nor sessions, as they 
                # refer to the main event and not to the recurring events.
                # TODO: inform the user
                event.clone( user = user,
                        except_models = [EventDeadline, EventSession],
                        start = date, end = None )
            del complex_fields[u'recurring']
        # test and return event {{{5
        assert(len(complex_fields) == 0)
        revision.add_meta( RevisionInfo,
                as_text = smart_unicode( event.as_text() ) )
        return event

    @staticmethod # def get_complex_fields(): {{{3
    def get_complex_fields():
        """ returns a tuple of names of user-editable fields (of events) which
        can contain many lines in the input text representation of an Event.
        """
        return ("urls", "deadlines", "sessions", "recurring", "description",)

    @staticmethod # def get_simple_fields(): {{{3
    def get_simple_fields():
        """ returns a tuple of names of user-editable fields (of events) which
        have only one line in the input text representation of an Event.
        """ 
        field_names = [unicode(f.name) for f in Event._meta.fields]
        field_names.remove(u"id")
        field_names.remove(u"user")
        field_names.remove(u"creation_time")
        field_names.remove(u"modification_time")
        field_names.remove(u"description")
        field_names.remove(u"upcoming")
        return tuple(field_names)
 
    @staticmethod # def get_necessary_fields(): {{{3
    def get_necessary_fields():
        """ returns a tuple of names of the necessary filed fields of an event.
        """
        return (u"title", u"start", u"tags", u"urls")

    @staticmethod # def get_priority_list(): #{{{3
    def get_priority_list():
        """ returns a tuple of names of fields in the order they
        should appear when showing an event as a text, i.e. in the output text
        representation of an Event.
        
        Notice that 'recurring' can be present in the input text
        representation, but it is not present in the output text
        representation.
 
        >>> gpl_len = len(Event.get_priority_list())  # 16
        >>> gsf_len = len(Event.get_simple_fields())  # 12
        >>> gcf_len = len(Event.get_complex_fields()) #  5 recurring not in gpl
        >>> assert(gpl_len + 1 == gsf_len + gcf_len)
        >>> synonyms_values_set = set(Event.get_synonyms().values())
        >>> assert(gpl_len + 1  == len(synonyms_values_set))
        """
        return (u"acronym", u"title", u"start", u"starttime", u"end",
                u"endtime", u"tags", u"urls", u"address",
                u"postcode", u"city", u"country", u"coordinates",
                u"deadlines", u"sessions", u"description")
 
    @staticmethod # def get_synonyms(): {{{3
    def get_synonyms():
        """Returns a dictionay with names (strings) and the fields (strings)
        they refer.

        All values of the returned dictionary (except recurring, urls,
        sessions and deadlines) are names of fields of the Event class.

        >>> synonyms_values_set = set(Event.get_synonyms().values())
        >>> assert ('urls' in synonyms_values_set)
        >>> synonyms_values_set.remove('urls')
        >>> assert ('deadlines' in synonyms_values_set)
        >>> synonyms_values_set.remove('deadlines')
        >>> assert ('sessions' in synonyms_values_set)
        >>> synonyms_values_set.remove('sessions')
        >>> assert ('recurring' in synonyms_values_set)
        >>> synonyms_values_set.remove('recurring')
        >>> field_names = [f.name for f in Event._meta.fields]
        >>> field_names = set(field_names)
        >>> assert (field_names >= synonyms_values_set)
        """
        if settings.DEBUG:
            # ensure you don't override a key
            def add( dictionary, key, value ):
                """ assert that the key is not already there """
                assert( not dictionary.has_key( key ) )
                dictionary[key] = value
        else:
            def add( dictionary, key, value ):
                """ add a pair to the dictionary """
                dictionary[key] = value
        # NOTE: if you modify the following dictionary, update
        # http://code.gridcalendar.net/wiki/DataFormats
        # and the online documentation under e.g. gridcalendar.net/h/
        # TODO: implement a system for using translations for tags (maybe
        # related to a preferred language user-based)
        synonyms = {} # TODO: think of using translations instead of synonyms
        for (syn, field) in settings.SYNONYMS:
            add( synonyms, syn, field )
        return synonyms

    def groups_id_list( self ): #{{{3
        """ returns a list of ids of groups the event is member of """
        groups_id_list = list()
        for group in Group.objects.filter( events = self ):
            groups_id_list.append( group.id )
        return groups_id_list

    def add_to_group( self, group_id ): #{{{3
        """ add the event to a group """
        # TODO: make this more safe, e.g. accepting a user id and checking that
        # the user is member of the group
        group = Group.objects.get( id = group_id )
        cal_entry = Calendar( event = self, group = group )
        cal_entry.save()

    def remove_from_group( self, group_id ): #{{{3
        """ remove event from group """
        group = Group.objects.get( id = group_id )
        cal_entry = Calendar.objects.get( event = self, group = group )
        cal_entry.delete()

if not reversion.is_registered( Event ): # {{{1
    reversion.register( Event, format = "yaml", # TODO: use custom serializer
            follow=[ "urls_set", "sessions_set", "deadlines_set" ] )

class RevisionInfo( models.Model ): # {{{1
    """ used to store additional info in revisions """
    # see https://github.com/etianen/django-reversion/wiki/Low-Level-API
    revision = models.ForeignKey("reversion.Revision")
    as_text = models.TextField( blank = True, null = True )
    redirect = models.IntegerField( blank = True, null = True )
    reason = models.CharField( blank = True, null = True, max_length = 100 )
    """ event id used to redirect deleted events """

# Event post_save.connect {{{1
# see http://docs.djangoproject.com/en/1.2/topics/signals/
post_save.connect( Event.post_save, sender = Event, dispatch_uid="Event.post_save" )

class RecurrenceManager( models.Manager ): #{{{1
    def get_by_natural_key(self, event):
        return self.get( event = Event.get_by_natural_key( *event ) )

class Recurrence( models.Model ): #{{{1
    # doc {{{2
    """ stores which is the master of and event belonging to a serie of
    recurring events.

    - A master is the first event (or recurrence) of a serie of recurring
      events.
    - All recurring events of the serie should have the same master.
    - A master has itself as master.
    - An event, which have a master, cannot be itself a master of another event.

    If we have an event ``e``, we can check if it is a recurrence of a serie
    with::

        if e.recurring

    If we have an event ``e`` with a master (.e. ``e`` is a recurrence of a
    serie with ``m`` as master), we can get its master with::

        e.recurring.master

    For a master of a serie::

        e.recurring.master == e

    To get all recurrences of an event (``m``) which is a master::

        m.recurrences.all()

    The above code returns an empty list if there is no event with ``m`` as
    master.

    To count the number of recurrences (more efficient than retrieving them)::

        m.recurrences.count()

    If we have an event ``m``, we attach an instance (``e``) to a serie
    having ``m`` as master with::

        m.recurrences.create(event = e)

    >>> import datetime
    >>> e1 = Event.objects.create(title="Re1", start=datetime.date.today())
    >>> e2 = Event.objects.create(title="Re2", start=datetime.date.today())
    >>> e3 = Event.objects.create(title="Re3", start=datetime.date.today())
    >>> assert e1.recurring == None
    >>> assert e2.recurring == None
    >>> assert e3.recurring == None
    >>> r = e1.recurrences.create(event = e2)
    >>> r = e1.recurrences.create(event = e3)
    >>> assert e1.recurring
    >>> assert e2.recurring
    >>> assert e3.recurring
    >>> assert e1.recurring.master == e1
    >>> assert e2.recurring.master == e1
    >>> assert e3.recurring.master == e1
    >>> event_list = [r.event for r in e1.recurrences.all()]
    >>> assert e1 in event_list
    >>> assert e2 in event_list
    >>> assert e3 in event_list
    >>> e1.recurrences.count()
    3
    >>> e3.delete() ; e2.delete() ; e1.delete()
    """
    # note that it would be possible to just have an attribute ``master`` in
    # the class Event, but that would make impossible to use natural keys with
    # events, because natural keys don't work with self references. TODO:
    # discuss self referenced natural keys with the Django developers: it
    # should work.
    # attributes and methods {{{2
    event = models.OneToOneField( Event,
            primary_key = True,
            # workarround described at
            # http://code.djangoproject.com/ticket/10227
            related_name = '_recurring',
            verbose_name = _('event') )
            
    master = models.ForeignKey( Event,
            related_name = 'recurrences',
            verbose_name = _('master'), )

    objects = RecurrenceManager()

    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        verbose_name = _( u'Recurrence' )
        verbose_name_plural = _( u'Recurrences' )
        # see http://docs.djangoproject.com/en/1.3/ref/models/options/#order-with-respect-to
        # order_with_respect_to = 'master'

    def natural_key( self ):
        return self.event.natural_key()
    natural_key.dependencies = ['events.event']

    def save( self, *args, **kwargs ):
        """ Call the real 'save' function after checking that the master
        doesn't have a master itself, raising an AssertionError otherwise.

        The design of recurring events is that all events of a serie have the
        same master (the first event in the serie), thus it is not allowed to
        have a master with a different master itself.
        """
        # saving a new recurrence with an event (self.event) and its master
        # (self.master)
        if self.master.recurring:
            # master is an instance of a serie.
            if self.master.recurring.master == self.master :
                # master is the master of the serie
                pass # do nothing
            else:
                # master is part of a serie but it is not its master, which
                # means something went wrong or someone didn't understand how
                # recurrences work: ask for attention:
                raise RuntimeError()
            # Call the "real" save() method:
            super( Recurrence, self ).save( *args, **kwargs )
        else:
            # master is not part of a serie, so we save the recurrence and
            # additionaly a self reference to master.
            super( Recurrence, self ).save( *args, **kwargs )
            self_reference = Recurrence(
                    master = self.master,
                    event = self.master )
            super( Recurrence, self_reference ).save( *args, **kwargs )

class ExtendedUser(User): # {{{1
    """ Some aditional funtions to users
    
    It uses the django proxy-models approach, see
    http://docs.djangoproject.com/en/1.2/topics/db/models/#proxy-models

    The variable ``USER`` (a ``ExtendedUser`` instance) is available in the
    ``context`` for all views and templates

    >>> from events.models import Event, Group, Membership
    >>> now = datetime.datetime.now().isoformat()
    >>> user = User.objects.create(username = now)
    >>> group1 = Group.objects.create(name="group1 " + now)
    >>> m = Membership.objects.create(user=user, group=group1)
    >>> group2 = Group.objects.create(name="group2 " + now)
    >>> m = Membership.objects.create(user=user, group=group2)
    >>> euser = ExtendedUser.objects.get(id = user.id)
    >>> assert ( len( euser.get_groups() ) == 2 )
    >>> assert euser.has_groups()
    >>> f1 = Filter.objects.create(user = user, name = "f1", query = "query")
    >>> f2 = Filter.objects.create(user = user, name = "f2", query = "query")
    >>> assert ( len( euser.get_filters() ) == 2)
    >>> assert euser.has_filters()
    >>> event = Event(title="test for ExtendedUser " + now,
    ...         start=datetime.date.today(), tags="test")
    >>> event.save()
    >>> calendar = Calendar.objects.create(event = event, group = group2)
    >>> assert euser.has_groups_with_coming_events()
    """
    class Meta: # {{{2
        proxy = True

    def has_groups(self): # {{{2
        """ returns True if the user is at least member of a group, False
        otherwise """
        return Group.objects.filter( membership__user = self ).count() > 0

    def get_groups(self): # {{{2
        """ returns a queryset of the user's groups """
        return Group.objects.filter( membership__user = self )

    def has_filters(self): # {{{2
        """ returns True if the user has at least one filter, False
        otherwise """
        return Filter.objects.filter( user = self ).count() > 0

    def get_filters(self): # {{{2
        """ returns a queryset of the user's filters """
        return Filter.objects.filter( user = self )

    def has_groups_with_coming_events( self ): # {{{2
        """ returns True if at least one group of the user has a coming event
        (start, end or a deadline in the future)
        """
        for group in self.get_groups():
            if group.has_coming_events():
                return True
        return False

class EventUrlManager( models.Manager ): # {{{1
    def get_by_natural_key(self, url_name, event):
        return self.get(
                url_name = url_name,
                event = Event.objects.get_by_natural_key( *event ) )

class EventUrl( models.Model ): # {{{1
    """ stores urls of events
    
    Code example: getting all events with more than one url:
    >>> from gridcalendar.events.models import Event
    >>> from django.contrib.gis.db.models import Count
    >>> urls_numbers = Event.objects.annotate(Count('urls'))
    >>> gt1 = filter(lambda x: x.urls__count > 1, urls_numbers)
    """
    event = models.ForeignKey( Event, related_name = 'urls' )
    url_name = models.CharField( _( u'URL Name' ), blank = False, null = False,
            max_length = 80, help_text = _( 
            u"Example: information about accomodation" ) )
    url = models.URLField( _( u'URL' ), blank = False, null = False )

    objects = EventUrlManager()

    class Meta: # pylint: disable-msg=C0111
        ordering = ['url_name']
        unique_together = ( "event", "url_name" )

    def natural_key( self ):
        return ( self.url_name, self.event.natural_key() )
    natural_key.dependencies = ['events.event']

    def __unicode__( self ): # {{{2
        return self.url

    def clone( self, event, user ): # {{{2
        """ creates a copy of itself related to ``event`` """
        new = EventUrl( event = event, url_name = self.url_name, url = self.url )
        new.save()
        return new

    @staticmethod # def get_urls( text ): {{{2
    def get_urls( text ):
        """ validates text lines containing EventUrl entries, raising
        ValidationErrors if there are errors, otherwise it returns a dictionary
        with names and urls (both unicode objects).
        """
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*(.*?)\s*$")
        lines = text.splitlines()
        if (len(lines[0]) < 1):
            raise ValidationError(_(u"text was empty") )
        # test for default URL
        field_m = field_p.match(lines[0])
        if not field_m:
            raise ValidationError(
                    _(u"first line for urls is malformed: ") +
                    lines[0])
        syns = Event.get_synonyms()
        if syns[field_m.group(1).lower()] != u'urls':
            raise ValidationError(
                    _(u"first line for urls doesn't contain a \
                    synonym of 'urls' before the colon: ") + lines[0])
        urls = {} # keys are url-names, values are urls
        if field_m.group(2) != u'':
            urls['url'] = field_m.group(2) # default url
        if len(lines) > 1:
            field_p = re.compile(r"^\s+(.*)\s+(.+?)\s*$")
            for line in lines[1:]:
                field_m = field_p.match(line)
                if not field_m:
                    empty_line_p = re.compile("^\s*$")
                    if empty_line_p.match(line):
                        raise ValidationError(
                            _(u"an unexpected empty line was found."))
                    raise ValidationError(
                            _(u"the following line is malformed: ") + line)
                name = field_m.group(1)
                if urls.has_key( name ):
                    raise ValidationError(
                            _('found more than one url with the same name: ' \
                                    '%(name)s') % {'name': name} )
                urls[name] = field_m.group(2)
        # we now check each url using django.core.validators for the fields of
        # this class
        errors = []
        url_validators = EventUrl._meta.get_field_by_name('url')[0].validators
        url_name_validators = \
                EventUrl._meta.get_field_by_name('url_name')[0].validators
        for url_name, url in urls.items():
            for val in url_name_validators:
                try:
                    val(url_name)
                except ValidationError, e:
                    errors.append( _('Error in url name %(url_name)s') %
                            {'url_name': url_name,} )
                    errors.extend( e.messages )
            for val in url_validators:
                try:
                    val(url)
                except ValidationError, e:
                    errors.append( _('Error in url %(url)s') %
                            {'url': url,} )
                    errors.extend( e.messages )
        if errors:
            raise ValidationError( errors )
        return urls

if not reversion.is_registered( EventUrl ): # {{{1
    reversion.register(EventUrl, format = "yaml" )
    # see https://github.com/etianen/django-reversion/wiki/Low-Level-API

class EventDeadlineManager( models.Manager ): # {{{1
    def get_by_natural_key(self, deadline_name, event):
        return self.get(
                deadline_name = deadline_name,
                event = Event.objects.get_by_natural_key( *event ) )

class EventDeadline( models.Model ): # {{{1
    """ stores deadlines for events """
    event = models.ForeignKey( Event, related_name = 'deadlines' )
    deadline_name = models.CharField( 
            _( u'Deadline name' ), blank = False, null = False,
            max_length = 80, help_text = _( 
            "Example: call for papers deadline" ) )
    deadline = models.DateField( _( u'Deadline' ), blank = False, null = False,
            validators = [validate_year] )

    objects = EventDeadlineManager()

    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        ordering = ['deadline', 'deadline_name']
        unique_together = ( "event", "deadline_name" )

    def natural_key( self ):
        return ( self.deadline_name, self.event.natural_key() )
    natural_key.dependencies = ['events.event']
    
    def save( self, *args, **kwargs ): #{{{2
        """ calls :meth:`Event.save` to update :attr:`Event.upcoming` """
        # Call the "real" save() method:
        super( EventDeadline, self ).save( *args, **kwargs )
        self.event.save() # needed to update Event.upcoming in the DB

    def delete( self, *args, **kwargs ): #{{{2
        """ calls :meth:`Event.save` to update :attr:`Event.upcoming` """
        super( EventDeadline, self ).delete( *args, **kwargs )
        self.event.save() # needed to update Event.upcoming in the DB

    def __unicode__( self ): # {{{2
        return unicode( self.deadline ) + u'    ' + self.deadline_name

    def clone( self, event, user ): # {{{2
        """ creates a copy of itself related to ``event`` """
        new = EventDeadline( event = event, deadline_name = self.deadline_name,
                deadline = self.deadline )
        new.save()
        return new

    def save( self, *args, **kwargs ): #{{{3
        """ Call the real 'save' function after updating :attr:`Event.upcoming`
        """
        # Call the "real" save() method:
        super( EventDeadline, self ).save( *args, **kwargs )
        self.event.save() # needed to update :attr:`Event.upcoming`

    @staticmethod # def get_deadlines( text ): {{{2
    def get_deadlines( text ):
        """ validates text lines containing EventDeadline entries,
        raising ValidationErrors if there are errors, otherwise it returns a
        dictionary with names and dates. """
        # TODO: this code can be simplified using only the django validators
        if not isinstance(text, unicode):
            text = smart_unicode(text)
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*(.*?)\s*$")
        lines = text.splitlines()
        if (len(lines[0]) < 1):
            raise ValidationError(
                    _(u"text of first line for deadlines was empty"))
        # test for default deadline
        field_m = field_p.match(lines[0])
        if not field_m:
            raise ValidationError(
                    _(u"first line for deadlines is malformed: ") +
                    lines[0])
        syns = Event.get_synonyms()
        if syns[field_m.group(1).lower()] != u'deadlines':
            raise ValidationError(
                    _( ''.join(["first line for deadlines doesn't contain a ",
                    "synonym of 'deadlines' before the colon: %(line)s"]) ) %
                    {'line': lines[0],} )
        deadlines = {} # keys are names, values are dates
        errors = [] # we store here errors
        if field_m.group(2) != u'':
            date_p = re.compile(r"^(\d\d\d\d)-(\d\d)-(\d\d)$")
            date_m = date_p.match(field_m.group(2))
            if not date_m:
                raise ValidationError(
                        _(u"default deadline was not of the form " +
                        u"nnnn-nn-nn. It was: ") + field_m.group(2))
            # default deadline:
            try:
                deadlines['deadline'] = datetime.date(
                        int(date_m.group(1)), int(date_m.group(2)),
                        int(date_m.group(3)))
            except (TypeError, ValueError), e:
                errors.append(
                    _('The default deadline %(deadline)s is not correct') %
                    {'deadline': date_m.group(1) + '-' + date_m.group(2) + '-'
                        + date_m.group(3),} )
        if len(lines) > 1:
            field_p = re.compile(r"^\s+(\d\d\d\d)-(\d\d)-(\d\d)\s+(.*?)\s*$")
            for line in lines[1:]:
                field_m = field_p.match(line)
                if not field_m:
                    raise ValidationError(
                        _(u"the following line for a deadline is malformed: ")
                        + line)
                name = field_m.group(4)
                if deadlines.has_key( name ):
                    errors.append( _(u'the following deadline name appers ' \
                            'more than one: %(name)s') % {'name': name} )
                else:
                    try:
                        deadlines[ field_m.group(4) ] = datetime.date(
                                int(field_m.group(1)), int(field_m.group(2)),
                                int(field_m.group(3)))
                    except (TypeError, ValueError), e:
                        errors.append(
                            _("The deadline '%(deadline_name)s' is not " \
                                    "correct") % {'deadline_name':
                                        field_m.group(4),} )
        if errors:
            raise ValidationError( errors )
        # we now check each deadline using django.core.validators for the
        # fields of this class
        deadline_validators = EventDeadline._meta.get_field_by_name(
                'deadline')[0].validators
        deadline_name_validators = EventDeadline._meta.get_field_by_name(
                'deadline_name')[0].validators
        for deadline_name, deadline in deadlines.items():
            for val in deadline_name_validators:
                try:
                    val(deadline_name)
                except ValidationError, e:
                    errors.append(
                            _('Error in deadline name %(deadline_name)s') %
                            {'deadline_name': deadline_name,} )
                    errors.extend( e.messages )
            for val in deadline_validators:
                try:
                    val(deadline)
                except ValidationError, e:
                    errors.append( _('Error in deadline %(deadline)s') %
                            {'deadline': deadline,} )
                    errors.extend( e.messages )
        if errors:
            raise ValidationError( errors )
        return deadlines

if not reversion.is_registered( EventDeadline ): # {{{1
    reversion.register( EventDeadline, format = 'yaml' )
    # see https://github.com/etianen/django-reversion/wiki/Low-Level-API

class EventSessionManager( models.Manager ): # {{{1
    def get_by_natural_key(self, session_name, event):
        return self.get(
                session_name = session_name,
                event = Event.objects.get_by_natural_key( *event ) )

class EventSession( models.Model ): # {{{1
    """ stores sessions for events """
    # TODO: check when submitting that session_dates are within the limits of
    # start and end dates of the event.
    event = models.ForeignKey( Event, related_name = 'sessions' )
    session_name = models.CharField( 
            _( u'Session name' ), blank = False, null = False, max_length = 80,
            help_text = _( u"Example: day 2 of the conference" ) )
    session_date = models.DateField( 
            _( u'Session day' ), blank = False, null = False,
            validators = [validate_year] )
    session_starttime = models.TimeField( 
            _( u'Session start time' ), blank = False, null = False )
    session_endtime = models.TimeField( 
            _( u'Session end time' ), blank = False, null = False )

    objects = EventSessionManager()

    def natural_key( self ):
        return ( self.session_name, self.event.natural_key() )
    natural_key.dependencies = ['events.event']

    class Meta: # {{{2 pylint: disable-msg=C0111,W0232,R0903
        ordering = ['session_date', 'session_starttime']
        unique_together = ( "event", "session_name" )
        verbose_name = _( u'Session' )
        verbose_name_plural = _( u'Sessions' )

    def __unicode__( self ): # {{{2
        return unicode( self.session_date ) + u'    ' + \
                unicode( self.session_starttime ) + u'-' + \
                unicode( self.session_endtime ) + u'    ' + self.session_name

    def clone( self, event, user ): # {{{2
        """ creates a copy of itself related to ``event`` """
        new = EventSession( event = event, session_name = self.session_name,
                session_date = self.session_date,
                session_starttime = self.session_starttime,
                session_endtime = self.session_endtime )
        new.save()
        return new

    @staticmethod # def get_sessions( text ): {{{2
    def get_sessions( text ):
        """ validates text lines containing EventSession entries,
        raising ValidationErrors if there are errors, otherwise it returns a
        dictionary with session names as keys and Session instances as values.
        """
        # TODO: simplify this code using the sessions form to validate data.
        # The form  should include validation code that check for instance that
        # the start time is before the end time, etc. See
        # http://docs.djangoproject.com/en/1.2/ref/forms/api/#using-forms-to-validate-data
        if not isinstance(text, unicode):
            text = smart_unicode(text)
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*$", re.UNICODE)
        lines = text.splitlines()
        # test for first line
        field_m = field_p.match(lines[0])
        if not field_m:
            raise ValidationError(
                    _(u"first line for sessions is malformed"))
        syns = Event.get_synonyms()
        if syns[field_m.group(1).lower()] != u'sessions':
            raise ValidationError(
                    _(u"first line for sessions doesn't contain a " +
                    "synonym of 'sessions' before the colon"))
        if len ( lines ) < 2:
            raise ValidationError(
                    _(u"there is no sessions data") )
        # session's names as keys, Session instances as values
        sessions = dict()
        errors = list()
        field_p = re.compile(r"""
                ^\s+(\d\d\d\d)-(\d\d?)-(\d\d?)       # 1 2 3 date  parts
                \s+(\d\d?)(?::(\d\d?))?              # 4 5   time1 parts
                \s*[\s-]\s*(\d\d?)(?::(\d\d?))?      # 6 7   time2 parts
                \s+(.+?)\s*$""", re.UNICODE | re.X ) # 8     description
        for line in lines[1:]:
            field_m = field_p.match(line)
            if not field_m or not field_m.group(1) or not field_m.group(2) or \
                    not field_m.group(3) or not field_m.group(4) or \
                    not field_m.group(6) or not field_m.group(8) :
                errors.append(
                        _(u"the following session line is malformed: ") + line)
            else:
                name = field_m.group(8)
                if sessions.has_key(name):
                    errors.append( 
                        _(u'the following session name appers more than once:' \
                        ' %(name)s') % {'name': name} )
                else:
                    try:
                        sessions[name] = Session(
                            date = datetime.date(
                                int(field_m.group(1)),
                                int(field_m.group(2)),
                                int(field_m.group(3))),
                            start = datetime.time(
                                int(field_m.group(4)),
                                int(field_m.group(5) or 0)), # min. default: 0
                            end = datetime.time(
                                int(field_m.group(6)),
                                int(field_m.group(7) or 0)), # min. default: 0
                            name = name )
                    except (TypeError, ValueError, AttributeError), e:
                        errors.append(
                                _(u"time/date entry error in line: ") + line)
                    # TODO: use local time of event if present
        if errors:
            raise ValidationError( errors )
        # we now check each session using django.core.validators for the fields
        # of this class
        fvals = {} # validators
        fvals['name'] = EventSession._meta.get_field_by_name(
                'session_name')[0].validators
        fvals['date'] = EventSession._meta.get_field_by_name(
                'session_date')[0].validators
        fvals['start'] = EventSession._meta.get_field_by_name(
                'session_starttime')[0].validators
        fvals['end'] = EventSession._meta.get_field_by_name(
                'session_endtime')[0].validators
        for session in sessions.values():
            for field_name, vals in fvals.items():
                for val in vals:
                    try:
                        val( getattr(session, field_name) )
                    except ValidationError, e:
                        errors.append(
                            _(u"Error in the field '%(field_name)s' for the " \
                                    u"entry: %(session_entry)s") %
                            {'field_name': field_name,
                                'session_entry': unicode(session)} )
                        errors.extend( e.messages )
        if errors:
            raise ValidationError( errors )
        return sessions.values()

if not reversion.is_registered( EventSession ): # {{{1
    reversion.register(EventSession, format = 'yaml' )
    # see https://github.com/etianen/django-reversion/wiki/Low-Level-API

# class EventHistoryManager( models.Manager ): # {{{1
#     def get_by_natural_key(self, modification_time, username):
#         return self.get(
#                 modification_time = modification_time,
#                 user = User.objects.get( username = username ) )
# 
# class EventHistory( models.Model ): # {{{1
#     user = models.ForeignKey( User,
#             unique = False, verbose_name = _( u'User' ) )
#     event = models.ForeignKey( Event, unique = False,
#             verbose_name = _( u'Event' ), related_name = 'history' )
#     modification_time = models.DateTimeField( _( u'Modification time' ),
#             editable = False, auto_now = True )
#     as_text = models.TextField(
#             _( u'Event as text' ), blank = False, null = False )
#     objects = EventHistoryManager()
#     class Meta: # {{{2 pylint: disable-msg=C0111,W0232,R0903
#         unique_together = ( "user", "modification_time" )
#         verbose_name = _( u'History' )
#         verbose_name_plural = _( u'Histories' )
#         ordering = ['-modification_time']
#     def post_save_receiver(self, instance, created, **kwargs):
#         pass
#     def pre_delete_receiver(self, instance, **kwargs):
#         pass

class FilterManager( models.Manager ): # {{{1
    def get_by_natural_key(self, name, username):
        return self.get(
                name = name,
                user = User.objects.get( username = username ) )

class Filter( models.Model ): # {{{1
    """ search queries of users """
    # {{{2 attributes
    user = models.ForeignKey( User,
            unique = False, verbose_name = _( u'User' ) )
    modification_time = models.DateTimeField( _( u'Modification time' ),
            editable = False, auto_now = True )
    query = models.CharField( _( u'Query' ), max_length = 500, blank = False,
            null = False )
    name = models.CharField( 
            _( u'Name' ), max_length = 40, blank = False, null = False )
    email = models.BooleanField( _( u'Email' ), default = False, help_text =
            _(u'If set it sends an email to a user when a new event matches'))

    objects = FilterManager()

    class Meta: # {{{2 pylint: disable-msg=C0111,W0232,R0903
        unique_together = ( "user", "name" )
        verbose_name = _( u'Filter' )
        verbose_name_plural = _( u'Filters' )

    def natural_key( self ):
        return (self.name, self.user.username)
    natural_key.dependencies = ['auth.user']

    def __unicode__( self ): # {{{2
        return self.name

    @models.permalink
    def get_absolute_url( self ): # {{{2
        "get internal URL of an event"
        return ( 'filter_edit', (), {'filter_id': self.id,} )

    def upcoming_events( self, limit = 5 ): # {{{2
        """ return the next ``limit`` events matching ``self.query`` """
        return Filter.matches( self.query, self.user, related = False )

    def matches_event( self, event ): # {{{2
        """ return True if self.query matches the event, False otherwise.
        """
        return Filter.query_matches_event( self.query, event )

    @staticmethod # def query_matches_event( query, event ): # {{{2
    def query_matches_event( query, event ):
        # doc & doctests {{{3
        """ return True if the query matches the event, False otherwise.

        >>> from events.models import *
        >>> from datetime import timedelta
        >>> from time import time
        >>> time = str(time()).replace('.','')
        >>> now = datetime.datetime.now().isoformat()
        >>> today = datetime.date.today()
        >>> group = Group.objects.create(name="matchesevent" + time)
        >>> event = Event.objects.create(title="test for events " + now,
        ...     start=timedelta(days=-1)+today, tags="test")
        >>> event_deadline = EventDeadline(
        ...         event = event, deadline_name = "test",
        ...         deadline = today)
        >>> event_deadline.save()
        >>> calendar = Calendar.objects.create( group = group,
        ...     event = event )
        >>> calendar.save()
        >>> user = User.objects.create(username = now)
        >>> fil = Filter.objects.create(user=user, name=now, query='test')
        >>> assert fil.matches_event(event)
        >>> fil.query = today.isoformat()
        >>> assert fil.matches_event(event)
        >>> fil.query = ( timedelta(days=-1) + today ).isoformat()
        >>> assert fil.matches_event(event)
        >>> fil.query = '!' + group.name
        >>> assert fil.matches_event(event)
        >>> fil.query = '#test'
        >>> assert fil.matches_event(event)
        >>> fil.query = 'abcdef'
        >>> assert not fil.matches_event(event)
        """
        # body {{{3
        qset = Filter.matches_queryset(query, event.user).filter(pk = event.id)
        if len( qset ) > 0:
            return True
        return False
        # EFFICIENCY: a much more efficient way would be to check manually
        # everything here, but then every change in
        # :meth:`Filter.matches_queryset` would cause changes here and
        # comparing and adapting both methods would be very time consuming and
        # error-pround. We had such a long code here until charset
        # 336:e725aaa6a108

    @staticmethod # def matches( query, user, related = True ): {{{2
    def matches( query, user, related = True ):
        """ returns a sorted (by :attr:`Event.upcoming`) list of
        events matching ``query`` adding related events if
        *related* is True.
        
        If *related* is True it adds to the result events with related tags,
        but no more that the number of results. I.e. if the result contains two
        events, only a miximum of two more related events will be added. If the
        query contains a location term (marked with ``@``), only related events
        with the same location are added. If the query contains a time term
        (``yyyy-mm-dd`` or ``yyyy-mm-dd yyyy-mm-dd``), only related events with the
        same time are added.

        If the query contains a group term (marked with ``!``) or a tag term
        (marked with ``#``), no related events are added.

        If the query evaluates to False, an empty queryset (EmptyQuerySet) is
        returned.

        """
        if not query:
            return Event.objects.none()
        # TODO: return a queryset, not a list. See some ideas described in:
        # http://stackoverflow.com/questions/431628/how-to-combine-2-or-more-querysets-in-a-django-view
        queryset = Filter.matches_queryset(query, user)
        # creates a list of
        # related events with no more than the length of queryset and combines
        # both
        if related and ( query.find('!') == -1 ) and ( query.find('#') == -1 ) \
                and ( len( queryset ) > 0 ) :
            related_events = Filter.related_events( queryset, user, query )
            # chains both and sorts the result
            return sorted(
                    chain( queryset, related_events ),
                    key = lambda event: event.upcoming )
        return queryset.order_by('upcoming')

    @staticmethod # def related_events( queryset, user, query ): {{{2
    def related_events( queryset, user, query ):    
        """ returns a list of related events to *queryset* as a result of
        ``query``
        """
        limit = len ( queryset )
        # if the query has a location restriction, we save only related events
        # in the same location. Same applies for a time restriction
        constraint_query = u''
        if ( query.find('@') != -1 ):
            regex = re.compile('@\w+', UNICODE)
            constraint_query = u' '.join( regex.findall( query ) )
        regex = re.compile(r'\b\d\d\d\d-\d\d-\d\d\b', UNICODE)
        if regex.search( query ):
            dates = regex.findall( query )
            constraint_query += u' ' + u' '.join( dates )
            has_date_constraint = True
        else:
            has_date_constraint = False
        used_tags = Tag.objects.usage_for_queryset( queryset, counts=True )
        # note that according to the django-tagging documentation, counts refer
        # to all instances of the model Event, not only to the queryset
        # instances. TODO: change it
        used_tags = sorted( used_tags, key = lambda t: t.count )
        used_tags.reverse()
        related_events = set()
        # takes the 5 more used tags and find related tags to them and its
        # events, then with 4, and so on until limit events are found
        today = datetime.date.today()
        # TODO: calculate at which number to start, 5 is just a guess
        for nr_of_tags in [5,4,3,2,1]:
            related_tags = Tag.objects.related_for_model(
                    used_tags[ 0 : nr_of_tags ], Event, counts = True )
            related_tags = sorted( related_tags, key = lambda t: t.count )
            related_tags.reverse()
            for tag in related_tags:
                events = TaggedItem.objects.get_by_model(Event, tag)
                for event in events:
                    if event not in queryset:
                        if not has_date_constraint:
                            if event.upcoming < today:
                                continue
                        if (not constraint_query) or \
                                Filter.query_matches_event(
                                    constraint_query, event ):
                            related_events.add(event)
                            if len ( related_events ) >= limit:
                                return related_events
        return related_events

    def matches_count( self ): # {{{2
        """ returns the number of events which would be returned without
        *count* by :meth:`Filter.matches` """
        return Filter.matches_queryset( self.query, self.user ).count()

    @staticmethod # def matches_queryset( query, user ): {{{2
    def matches_queryset( query, user ):
        """ returns a queryset without touching the database, see
        :meth:`Filter.matches` 

        If ``query`` evaluates to False, returns an empty QuerySet. E.g. when
        ``query`` is None or an empty string.
        """
        if not query:
            return Event.objects.none()
        if user is None or isinstance(user, User):
            pass
        elif isinstance(user, AnonymousUser):
            user = None
        else:
            try:
                user = User.objects.get(id = int(user))
            except User.DoesNotExist:
                user = None
        # TODO: use the catche system for queries
        queryset = Event.objects.all()
        # groups
        regex = re.compile('!(\w+)', UNICODE)
        for group_name in regex.findall(query):
            queryset = queryset.filter(
                    calendar__group__name__iexact = group_name)
        query = regex.sub("", query)
        # locations
        # the regex start with @ and has 4 alternatives, examples:
        # 52.1234,-0.1234+300km
        # 52.1234,-0.1234,53.1234,-0.2345
        # london+50mi
        # berlin
        regex = re.compile(r"""
                @(?:                    # loc regex starts with @
                (?:                     # four floats separated by ,
                    ([+-]?\d+           # [0] one or more digits
                        (?:\.\d*)?)     # optionally . or . and decimals
                    ,
                    ([+-]?\d+           # [1] one or more digits
                        (?:\.\d*)?)     # optionally . or . and decimals
                    ,
                    ([+-]?\d+           # [2] one or more digits
                        (?:\.\d*)?)     # optionally . or . and decimals
                    ,
                    ([+-]?\d+           # [3] one or more digits
                        (?:\.\d*)?)     # optionally . or . and decimals
                )|(?:                   # or float,float+int and opt. a unit
                    ([+-]?\d+           # [4] one or more digits
                        (?:\.\d*)?)     # optionally . or . and decimals
                    ,\s*                # spaces because some people copy/paste
                    ([+-]?\d+           # [5] one or more digits
                        (?:\.\d*)?)     # optionally . or . and decimals
                    \+(\d+)             # [6] distance
                    (km|mi)?            # [7] optional unit
                )|(?:                   # or a name, +, distance and opt. unit
                    (\w+)               # [8] name
                    \+(\d+)             # [9] distance
                    (km|mi)?            # [10] optional unit
                )|(                     # or just a name
                    \w+                 # [11]
                ))""", re.UNICODE | re.X )
        for loc in regex.findall(query):
            if loc[11]:
                # name given
                queryset = queryset.filter(
                        # TODO: searching for 'Washington' doens't match
                        # 'Washington D.C.'. OTOH searching for 'us' would
                        # match 'Brussels' if 'city__icontains' were used
                        Q( city__iexact = loc[11] ) | Q(
                            country__iexact = loc[11] ) )
                        # TODO: use also translations of locations and
                        # alternative names
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
        query = regex.sub("", query)
        # tags
        regex = re.compile('#(\w+)', UNICODE)
        tags = regex.findall(query)
        if tags:
            queryset = TaggedItem.objects.get_intersection_by_model(
                    queryset, tags )
        query = regex.sub("", query)
        # broad search check
        broad_regex = re.compile('^\* +', UNICODE) # beginninig with * followed
                                                   # by 1 ore more spaces
        if broad_regex.match( query ):
            broad = True
            query = broad_regex.sub("", query)
        else:
            broad = False
        # dates
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
                    Q(deadlines__deadline__range = (date1, date2) ) )
            # remove all dates (yyyy-mm-dd) from the query
            query = DATE_REGEX.sub("", query)
        elif not broad:
            today = datetime.date.today()
            queryset = queryset.filter( upcoming__gte = today )
            # without using upcoming:
            # queryset = queryset.filter(
            #         Q(start__gte = date) | Q(end__gte = date) |
            #         Q(deadlines__deadline__gte = date) )
        # look for words
        regex = re.compile('([^!@#]\w+)', UNICODE)
        for word in regex.findall(query):
            word = word.strip()
            if not broad:
                queryset = queryset.filter(
                        Q(title__icontains = word) |
                        Q(tags__icontains = word) |
                        # e.g. 'washington' in 'Washington D.C.'
                        Q(city__icontains = word) | # TODO in other languages
                        Q(country__iexact = word) | # TODO in other languages
                        Q(acronym__icontains = word) )
            else: # broad search
                queryset = queryset.filter(
                        Q( title__icontains = word ) |
                        Q( tags__icontains = word ) |
                        Q( city__icontains = word ) |
                        Q( country__icontains = word ) |
                        Q( address__icontains = word ) |
                        Q( acronym__icontains = word ) |
                        Q( description__icontains = word ) |
                        Q( urls__url_name__icontains = word ) |
                        Q( urls__url__icontains = word ) |
                        Q( deadlines__deadline_name__icontains = word ) |
                        Q( sessions__session_name__icontains = word ) )
        # TODO: add full indexing text on Event.description and comments. See
        # http://wiki.postgresql.org/wiki/Full_Text_Indexing_with_PostgreSQL
        # remove duplicates
        queryset = queryset.distinct() # TODO: needed? we start with .all()
        return queryset

    @staticmethod # def notify_users_when_wanted( event ): {{{2
    def notify_users_when_wanted( event ):
        """ notifies users if *event* matches a filter of a user and the
        user wants to be notified for the matching filter and the user can see
        the event """
        if isinstance(event, Event):
            pass
        elif isinstance(event, int) or isinstance(event, long):
            event = Event.objects.get(pk = event)
        else:
            event = Event.objects.get(pk = int(event))
        # TODO: the next code iterate throw all users but this is not workable
        # for a big number of users: implement a special data structure which
        # saves filters and can look up fast filters matching an event
        # TODO: show a diff of the changes
        users = User.objects.all()
        for user in users:
            user_filters = Filter.objects.filter( user = user ).filter(
                    email = True)
            for fil in user_filters:
                if fil.matches_event(event):
                    context = {
                        'username': user.username,
                        'event': event,
                        'filter': fil,
                        'site_name': Site.objects.get_current().name,
                        'site_domain': Site.objects.get_current().domain, }
                    # TODO: create the subject from a text template
                    subject = _(u'filter match: ') + event.title
                    # TODO: use a preferred language setting for users to send
                    # emails to them in this language
                    message = render_to_string(
                            'mail/event_notice.txt', context )
                    from_email = settings.DEFAULT_FROM_EMAIL
                    if subject and message and from_email and user.email:
                        try:
                            send_mail( subject, message, from_email,
                                    [user.email,], fail_silently = False )
                        except (BadHeaderError, SMTPConnectError):
                            # FIXME: do something meaningfull, e.g. error log
                            pass
                    else:
                        # FIXME: do something meaningfull, e.g. error log
                        pass

class GroupManager( models.Manager ): # {{{1
    def get_by_natural_key(self, name):
        return self.get( name = name )

class Group( models.Model ): # {{{1
    """ groups of users and events
        
    >>> from django.contrib.auth.models import User
    >>> from events.models import Event, Group, Membership
    >>> from datetime import timedelta
    >>> now = datetime.datetime.now().isoformat()
    >>> today = datetime.date.today()
    >>> group = Group.objects.create(name="group " + now)
    >>> event = Event(title="test for events " + now,
    ...     start=timedelta(days=-1)+today, tags="test")
    >>> event.save()
    >>> event_deadline = EventDeadline(
    ...         event = event, deadline_name = "test",
    ...         deadline = today)
    >>> event_deadline.save()
    >>> calendar = Calendar.objects.create( group = group,
    ...     event = event )
    >>> assert ( len(group.get_coming_events()) == 1 )
    >>> assert ( group.has_coming_events() )
    >>> assert ( len(group.get_users()) == 0 )
    >>> user = User.objects.create(username = now)
    >>> membership = Membership.objects.create(group = group, user = user)
    >>> assert ( len(group.get_users()) == 1 )
    """
    # TODO test names with special characters including urls like grical.org/group_name
    name = models.CharField( _( u'Name' ), max_length = 80, unique = True,
            validators = [ RegexValidator(
                re.compile(r'.*[^0-9].*'),
                message = _(u'a group name must contain at least one ' \
                        'character which is not a number') ) ] )
            # the validation above is needed in order to show an event with the
            # short url e.g. grical.org/1234
    description = models.TextField( _( u'Description' ) )
    members = models.ManyToManyField( User, through = 'Membership',
            verbose_name = _( u'Members' ) )
    events = models.ManyToManyField( Event, through = 'Calendar',
            verbose_name = _( u'Events' ) )
    creation_time = models.DateTimeField(
            _( u'Creation time' ), editable = False, auto_now_add = True )
    modification_time = models.DateTimeField( _( u'Modification time' ),
            editable = False, auto_now = True )

    objects = GroupManager()

    class Meta: # {{{2 pylint: disable-msg=C0111,W0232,R0903
        ordering = ['name']
        verbose_name = _( u'Group' )
        verbose_name_plural = _( u'Groups' )

    def natural_key( self ):
        return (self.name,)

    def __unicode__( self ): # {{{2
        return self.name

    @models.permalink # def get_absolute_url( self ): {{{2
    def get_absolute_url( self ):
        "get internal URL of an event"
        return ( 'group_view', (), {'group_id': self.id,} )

    def is_member( self, user ): # {{{2
        """ returns True if *user* is a member of the group, False otherwise
        """
        if isinstance(user, int) or isinstance(user, long):
            try:
                user = User.objects.get(id = user)
            except User.DoesNotExist:
                return False
        elif isinstance(user, User):
            pass
        else:
            user = User.objects.get( id = int(user) )
        return Membership.objects.filter( group = self, user = user ).exists()

    def get_users( self ): # {{{2
        """ returns a queryset (which can be used as a list) of ExtendedUsers
        members of the group """
        return ExtendedUser.objects.filter( membership__group = self )

    @staticmethod # def is_user_in_group( user, group ): {{{2
    def is_user_in_group( user, group ):
        """ Returns True if *user* is in *group*, otherwise False.

        The parameters *user* and *group* can be an instance the classes User
        and Group or the id number.

        >>> from django.contrib.auth.models import User
        >>> from events.models import Event, Group, Membership
        >>> now = datetime.datetime.now().isoformat()
        >>> user1 = User.objects.create(username = "u1" + now)
        >>> user2 = User.objects.create(username = "u2" + now)
        >>> group1 = Group.objects.create(name="group1 " + now)
        >>> m = Membership.objects.create(user=user1, group=group1)
        >>> assert (Group.is_user_in_group(user1, group1))
        >>> assert (not Group.is_user_in_group(user2, group1))
        >>> assert (Group.is_user_in_group(user1.id, group1.id))
        >>> assert (not Group.is_user_in_group(user2.id, group1.id))
        """
        if isinstance(user, User):
            user_id = user.id
        elif isinstance(user, int) or isinstance(user, long):
            user_id = user
        elif isinstance(user, unicode) or isinstance(user, str):
            user_id = int(user)
        else:
            return False
        if isinstance(group, Group):
            group_id = group.id
        elif isinstance(group, int) or isinstance(group, long):
            group_id = group
        elif isinstance(group, unicode) or isinstance(group, str):
            group_id = int(group)
        else:
            return False
        times_user_in_group = Membership.objects.filter( 
                user__id__exact = user_id,
                group__id__exact = group_id )
        if times_user_in_group.count() > 0:
            assert( times_user_in_group.count() == 1 )
            return True
        else:
            return False

    # FIXME: implemnt __hash__ and __eq__ and probably __cmp__ to be able to
    # efficiently use a group as a key of a dictionary

    @staticmethod # def groups_of_user(user): {{{2
    def groups_of_user(user):
        """ Returns a list of groups the *user* is a member of.

        The parameter *user* can be an instance of User or the id number of a
        user.
        
        >>> from django.contrib.auth.models import User
        >>> from events.models import Event, Group, Membership
        >>> now = datetime.datetime.now().isoformat()
        >>> user1 = User.objects.create(username = "u1" + now)
        >>> user2 = User.objects.create(username = "u2" + now)
        >>> group12 = Group.objects.create(name="group12 " + now)
        >>> group2 = Group.objects.create(name="group2 " + now)
        >>> m1 = Membership.objects.create(user=user1, group=group12)
        >>> m2 = Membership.objects.create(user=user2, group=group12)
        >>> m3 = Membership.objects.create(user=user2, group=group2)
        >>> groups_of_user_2 = Group.groups_of_user(user2)
        >>> assert(len(groups_of_user_2) == 2)
        >>> assert(isinstance(groups_of_user_2, list))
        >>> assert(isinstance(groups_of_user_2[0], Group))
        >>> assert(isinstance(groups_of_user_2[1], Group))
        >>> groups_of_user_1 = Group.groups_of_user(user1)
        >>> assert(len(groups_of_user_1) == 1)

        """
        if ( user is None or type( user ) == AnonymousUser ):
            return list()
        if isinstance(user, User):
            pass
        elif isinstance(user, int) or isinstance(user, long):
            user = User.objects.get(id=user)
        elif isinstance(user, unicode) or isinstance(user, str):
            user = User.objects.get( id = int( user ) )
        else: raise TypeError(
                "'user' must be a User instance or an integer but it was " +
                str(user.__class__))
        return list(Group.objects.filter(membership__user=user))

    def get_coming_events(self, limit=5): # {{{2
        """ Returns a list of maximal *limit* events with at least one date
        in the future (start, end or deadline). If *limit* is -1 it
        returns all

        """
        today = datetime.date.today()
        events = Event.objects.filter( Q(calendar__group = self) & (
                    Q(start__gte=today) | Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today) ))
        events = events.distinct().order_by('upcoming')
        if limit == -1:
            return events
        else:
            return events[0:limit]

    def get_coming_events(self, limit=5): # {{{2
        """ Returns a list of maximal *limit* events with at least one
        date in the future (start, end or deadline). If *limit* is -1 it
        returns all
        """
        today = datetime.date.today()
        events = Event.objects.filter(
                Q(calendar__group = self) & Q(upcoming__gte=today) )
        # the code without using upcoming would be:
        #events = Event.objects.filter(
        #        Q(calendar__group = self) & (
        #            Q(start__gte=today) | Q(end__gte=today) |
        #            Q(deadlines__deadline__gte=today) ))
        events = events.distinct().order_by('upcoming') # TODO: needed?
        if limit == -1:
            return events
        else:
            return events[0:limit]

    def has_coming_events(self): # {{{2
        """ returns True if the group has coming events (with *start*, *end* or
        a *deadline* of an event of the group in the future)
        """
        today = datetime.date.today()
        return Event.objects.filter( Q(calendar__group = self) & (
                    Q(start__gte=today) | Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today) )).count() > 0

    def has_coming_events(self): # {{{2
        """ returns True if the group has coming events (with *start*,
        *end* or a *deadline* of an event of the group in the future)
        """
        today = datetime.date.today()
        return Event.objects.filter( Q(calendar__group = self) &
                Q(upcoming__gte=today) ).count() > 0
        # the code without using upcoming would be:
        # return Event.objects.filter(
        #         Q( calendar__group = self ) & (
        #             Q(start__gte=today) | Q(end__gte=today) |
        #             Q(deadlines__deadline__gte=today) )).count() > 0

    @staticmethod # def events_in_groups(groups, limit=5): {{{2
    def events_in_groups(groups, limit=5):
        """ Returns a dictionary whose keys are groups and its values are non
        empty lists of maximal *limit* events of the group with at least one
        date in the future
        
        FIXME: add test.
        """
        to_return = {}
        if not limit > 0:
            return to_return
        if len(groups) == 0:
            return to_return
        for group in groups:
            events = group.get_coming_events(limit)
            if len(events) > 0:
                to_return[group] = events
        return to_return

    @classmethod # def groups_for_add_event( cls, user, event ): {{{2
    def groups_for_add_event( cls, user, event ):
        """ returns a queryset (which can be used as a list) of groups to which
        *event* can be added by *user*.
        """
        if isinstance(event, Event):
            pass
        elif isinstance(event, int) or isinstance(event, long):
            event = Event.objects.get(pk = event)
        else:
            event = Event.objects.get(pk = int(event))
        groups = cls.objects.filter( members = user )
        groups = groups.exclude( events = event )
        return groups

class Membership( models.Model ): # {{{1
    """Relation between users and groups."""
    user = models.ForeignKey( 
            User,
            verbose_name = _( u'User' ),
            related_name = 'membership' ) # name of the reverse relationship
    # the name 'groups' instead of mygroups is not possible because the default
    # User model in django already has a relation called 'groups'
    group = models.ForeignKey( 
            Group,
            verbose_name = _( u'Group' ),
            related_name = 'membership' ) # name of the reverse relationship
    is_administrator = models.BooleanField( 
            _( u'Is administrator' ), default = True )
    """Not used at the moment. All members of a group are administrators.
    """ # pylint: disable-msg=W0105
    new_event_email = models.BooleanField(
            _( u'New event notification' ), default = True )
    """If True a notification email should be sent to the user when a new event
    is added to the group""" # pylint: disable-msg=W0105
    new_member_email = models.BooleanField( 
            _( u'New member notification' ), default = True )
    """If True a notification email should be sent to the user when a new
    member is added to the group""" # pylint: disable-msg=W0105
    date_joined = models.DateField( 
            _( u'date_joined' ), editable = False, auto_now_add = True )
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        unique_together = ( "user", "group" )
        verbose_name = _( u'Membership' )
        verbose_name_plural = _( u'Memberships' )

class Calendar( models.Model ): # {{{1
    """Relation between events and groups."""
    event = models.ForeignKey( Event, verbose_name = _( u'Event' ),
            related_name = 'calendar' )
    group = models.ForeignKey( 
            Group, verbose_name = _( u'Group' ), related_name = 'calendar' )
    date_added = models.DateField( 
            _( u'Date added' ), editable = False, auto_now_add = True )

    def clone( self, event, user ):
        """ groups are not copied when an event is cloned """
        return None

    # TODO: save who added it
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        unique_together = ( "event", "group" )
        verbose_name = _( u'Calendar' )
        verbose_name_plural = _( u'Calendars' )


# Next code is an adaptation of some code in python-django-registration
SHA1_RE = re.compile( '^[a-f0-9]{40}$' )
class GroupInvitationManager( models.Manager ): # {{{1
    """
    Custom manager for the :class:`GroupInvitation` model.

    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired Group Invitations.

    """
    def activate_invitation( self, activation_key ):
        """
        Validate an activation key and adds the corresponding
        *User* to the corresponding *Group* if valid.

        If the key is valid and has not expired, returns a dictionary
        with values *host*, *guest*, *group* after adding the
        user to the group.

        If the key is not valid or has expired, return ``False``.

        If the key is valid but the *User* is already in the group,
        return ``False``, but set it as administrator if the invitation
        set it but the user wasn't an administrator

        If the key is valid but the *host* is not an administrator of
        the group, return False.

        To prevent membership of a user who has been removed by a group
        administrator after his activation, the activation key is reset to the string
        *ALREADY_ACTIVATED*after successful activation.

        """
        # TODO: inform the user after all possible cases explained above

        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search( activation_key ):
            try:
                invitation = self.get( activation_key = activation_key )
            except self.model.DoesNotExist:
                return False

            # expiration_date = \
            #     datetime.timedelta( days = settings.ACCOUNT_ACTIVATION_DAYS )
            # assert ( invitation.issue_date + expiration_date >= datetime.date.today() )
            # assert not invitation.activation_key == invitation.ACTIVATED

            if not invitation.activation_key_expired():
                host = invitation.host
                guest = invitation.guest
                group = invitation.group
                as_administrator = invitation.as_administrator
                # check that the host is an administrator of the group
                h = Membership.objects.filter( user = host, group = group )
                if len( h ) == 0:
                    return False
                if not h[0].is_administrator:
                    return False
                # check if the user is already in the group and give him
                # administrator rights if he hasn't it but it was set in the
                # invitation
                member_list = \
                    Membership.objects.filter( user = guest, group = group )
                if not len( member_list ) == 0:
                    assert len( member_list ) == 1
                    if as_administrator and not member_list[0].is_administrator:
                        member_list[0].is_administrator = True
                        member_list[0].activation_key = self.model.ACTIVATED
                    return False
                else:
                    member = Membership( 
                            user = guest, group = group,
                            is_administrator = as_administrator )
                    member.activation_key = self.model.ACTIVATED
                    member.save()
                    return True
        return False

    def create_invitation( self, host, guest, group, as_administrator ):
        """
        Create a new invitation and email its activation key to the
        ``guest``.

        The activation key will be a
        SHA1 hash, generated from a combination of the ``User``'s
        name and a random salt.

        The activation email will make use of two templates:

        ``groups/invitation_email_subject.txt``
            This template will be used for the subject line of the
            email. It receives one context variable, ``site``, which
            is the currently-active
            ``django.contrib.sites.models.Site`` instance. Because it
            is used as the subject line of an email, this template's
            output **must** be only a single line of text; output
            longer than one line will be forcibly joined into only a
            single line.

        ``groups/invitation_email.txt``
            This template will be used for the body of the email. It
            will receive five context variables: ``activation_key``
            will be the user's activation key (for use in constructing
            a URL to activate the account), ``expiration_days`` will
            be the number of days for which the key will be valid,
            ``site`` will be the currently-active
            ``django.contrib.sites.models.Site`` instance,
            ``host`` will be the user name of the person inviting and
            ``group`` will be the name of the group.

        """
        salt = hashlib.sha1( str( random.random() ) ).hexdigest()[:5]
        activation_key = hashlib.sha1( salt + guest.username ).hexdigest()
        self.create( 
                host = host, guest = guest, group = group,
                as_administrator = as_administrator,
                activation_key = activation_key )

        current_site = Site.objects.get_current()

        subject = render_to_string( 'groups/invitation_email_subject.txt',
                { 'site_name': current_site.name,
                  'guest': guest.username,
                  'host': host.username,
                  'group': group.name, } )
        # Email subject *must not* contain newlines
        subject = ''.join( subject.splitlines() )

        message = render_to_string( 
                'groups/invitation_email.txt',
                { 'activation_key': activation_key,
                  'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                  'site_name': current_site.name,
                  'site_domain': current_site.domain,
                  'host': host.username,
                  'guest': guest.username,
                  'group': group.name, } )

        # we change the user-part of the sender to:
        # current_site.name group invitation
        # <group-invitation@host_part_of_DEFAULT_FROM_EMAIL>
        dfrom = settings.DEFAULT_FROM_EMAIL
        from_header = current_site.name + ' group invitation <' + \
                'group-invitation' + dfrom[ dfrom.find('@'): ] + '>'
        if settings.REPLY_TO:
            email = EmailMessage( subject, message, from_header,
                    [guest.email,],
                    list(), # BCC, TODO: think of logging or sending to somewhere
                    headers = {'Reply-To': settings.REPLY_TO,} )
        else:
            email = EmailMessage( subject, message, from_header,
                    [guest.email,],
                    list(), # BCC, TODO: think of logging or sending to somewhere
                    )
        email.send()

    def delete_expired_invitations( self ):
        """
        Remove expired instances of :class:`GroupInvitation`.

        Accounts to be deleted are identified by searching for
        instances of :class:`GroupInvitation` with expired activation
        keys.

        It is recommended that this method be executed regularly as
        part of your routine site maintenance; this application
        provides a custom management command which will call this
        method, accessible as ``manage.py cleanupgroupinvitation``.

        """
        for invitation in self.all():
            if invitation.activation_key_expired():
                invitation.delete()

class GroupInvitation( models.Model ): # {{{1
    """
    A simple class which stores an activation key for use during
    user group invitations.

    Generally, you will not want to interact directly with instances
    of this model; the provided manager includes methods
    for creating and activating invitations, as well as for cleaning
    out group invitations which have never been activated.

    """
    ACTIVATED = u"ALREADY_ACTIVATED"

    host = models.ForeignKey( 
            User, related_name = "host", verbose_name = _( u'host' ) )
    guest = models.ForeignKey( 
            User, related_name = "guest", verbose_name = _( u'host' ) )
    group = models.ForeignKey( 
            Group, verbose_name = _( u'group' ) )
    as_administrator = models.BooleanField( 
            _( u'as administrator' ), default = True )
    activation_key = models.CharField( 
            _( u'activation key' ), max_length = 40 )
    issue_date = models.DateField( 
            _( u'issue_date' ), editable = False, auto_now_add = True )

    # see http://docs.djangoproject.com/en/1.0/topics/db/managers/
    objects = GroupInvitationManager()

    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        # unique_together = ("host", "guest", "group")
        verbose_name = _( u'Group invitation' )
        verbose_name_plural = _( u'Group invitations' )

    def __unicode__( self ):
        return _( u"group invitation information for group %(group)s for user \
                %(guest)s from user %(host)s" % {"group":self.group,
                    "guest":self.guest, "host":self.host} )

    def activation_key_expired( self ):
        """
        Determine whether this :class:`GroupInvitation`'s activation
        key has expired, returning a boolean -- ``True`` if the key
        has expired.

        Key expiration is determined by a two-step process:

        1. If the user has already activated, the key will have been
           reset to the string ``ALREADY_ACTIVATED``. Re-activating is
           not permitted, and so this method returns ``True`` in this
           case.

        2. Otherwise, the date the user signed up is incremented by
           the number of days specified in the setting
           ``ACCOUNT_ACTIVATION_DAYS`` (which should be the number of
           days after signup during which a user is allowed to
           activate their account); if the result is less than or
           equal to the current date, the key has expired and this
           method returns ``True``.

        """
        expiration_date = \
            datetime.timedelta( days = settings.ACCOUNT_ACTIVATION_DAYS )
        return self.activation_key == self.ACTIVATED or \
               ( self.issue_date + expiration_date <= datetime.date.today() )
    # TODO: find out and explain here what this means:
    activation_key_expired.boolean = True

class Session: #{{{1
    def __init__(self, date=None, start=None, end=None, name=None):
        self.date = date
        self.start = start
        self.end = end
        self.name = name
    def __unicode__(self):
        return unicode(self.date.strftime( "%Y-%m-%d" )) + \
                " " + unicode(self.start.strftime( "%H:%M" )) + \
                " " + unicode(self.end.strftime( "%H:%M" )) + \
                " " + unicode(self.name)

# LOG to a pipe {{{1
# it is recommended in the Django documentation to connect to signals in
# models.py. That is why this code is here.
if settings.PIPE_TO_LOG_TO:
    def write_to_pipe( **kwargs ): # {{{2
        site = Site.objects.get_current().domain
        with open(settings.PIPE_TO_LOG_TO, 'a') as pipe:
            # comment {{{3
            if kwargs['sender'] == Comment:
                comment = kwargs['comment']
                pipe.write(
                    'http://%(site)s%(comment_url)s\n' \
                    '*** %(comment)s ***\n' % {
                        'site': site,
                        'comment_url': comment.get_absolute_url(),
                        'comment': smart_str( comment.comment,
                            encoding='ascii', errors='ignore' ) } )
            # event created/updated {{{3
            elif kwargs['sender'] == RevisionInfo:
                revision_info = kwargs['instance']
                revision = revision_info.revision
                event_content_type = ContentType.objects.get_for_model( Event )
                # in each revision there is only one version for an Event
                event_version = revision.version_set.get(
                        content_type = event_content_type )
                try:
                    event = Event.objects.get( pk = event_version.object_id )
                except Event.DoesNotExist:
                    # this happens when an event has been deleted
                    return
                event_url = event.get_absolute_url()
                # TODO: optimize the next code to hit the db less
                pipe.write(
                    'http://%(site)s%(event_url)s\n'  % {
                        'site': site, 'event_url': event_url } )
                revisions = [ version.revision for version in
                    Version.objects.get_for_object( event ) ]
                if len( revisions ) > 1:
                    diff = text_diff(
                            revisions[-2].revisioninfo_set.all()[0].as_text,
                            revisions[-1].revisioninfo_set.all()[0].as_text )
                    pipe.write( diff )
                    #pipe.write( ''.join( ['\n  ' + line for line in 
                    #    diff.splitlines() ] ) )
                else:
                    pipe.write( ''.join( ['\n  ' + line for line in 
                        event.as_text().splitlines() ] ) )
            # event deleted {{{3
            elif kwargs['sender'] == Event:
                event = kwargs['instance']
                deleted_url = reverse( 'event_deleted',
                        kwargs={'event_id': event.id,} )
                pipe.write( 'http://%(site)s%(deleted_url)s' % {
                    'site': site, 'deleted_url': deleted_url, } )
            #  Revision, used to log undeletions {{{3
            elif kwargs['sender'] == Version:
                version = kwargs['instance']
                # undeletions have version.type = VERSION_ADD and the version
                # before has version.type = VERSION_DELETE
                if not version.type == VERSION_ADD:
                    return
                event_content_type = ContentType.objects.get_for_model( Event )
                revision_list = Revision.objects.filter(
                       version__object_id = version.object_id,
                       version__content_type = event_content_type )
                revision_list = revision_list.order_by( '-date_created' )
                if len( revision_list ) < 2:
                    return
                previous = None
                for revision in revision_list:
                    if previous and previous == version.revision:
                        ver = revision.version_set.get(
                                content_type = event_content_type )
                        if ver.type == VERSION_DELETE:
                            history_url = reverse( 'event_history',
                                kwargs={'event_id': version.object_id,} )
                            pipe.write( 'http://%(site)s%(history_url)s' % {
                                'site': site, 'history_url': history_url, } )
                        return
                    previous = revision

    # signals connects {{{2
    post_save.connect( write_to_pipe , sender = RevisionInfo,
        weak = False, dispatch_uid = 'pipe_logger_revisioninfo' )
    comment_was_posted.connect( write_to_pipe, sender = Comment,
        weak = False, dispatch_uid = 'pipe_logger_comment' )
    post_delete.connect( write_to_pipe, sender = Event,
        weak = False, dispatch_uid = 'pipe_logger_event_deleted' )
    post_save.connect( write_to_pipe, sender = Version,
        weak = False, dispatch_uid = 'pipe_logger_undeleted' )
