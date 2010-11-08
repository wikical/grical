#!/usr/bin/env python
# -*- coding: utf-8 -*-
# GPL {{{1
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
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

import vobject

from django.core.mail import send_mail, BadHeaderError
from django.utils.encoding import smart_str, smart_unicode
from django.db import models
# http://docs.djangoproject.com/en/1.2/topics/db/queries/#filters-can-reference-fields-on-the-model
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sites.models import Site
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.db.models.query import CollectedObjects
from django.db.models.signals import pre_save, post_save
from gridcalendar.events.signals import user_auth_signal
# FIXME from gridcalendar.events.decorators import autoconnect

from tagging.fields import TagField
from tagging.models import Tag, TaggedItem

# COUNTRIES {{{1
# TODO: use instead a client library from http://www.geonames.org/ accepting
# names (in different languages) and codes like e.g. ES, es,  ESP, eSp, 724,
# España, etc. Name colisions in different languages needs to be checked.
# OR use python.django.countries
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
end: 2010-12-30
tags: calendar software open-source gridmind gridcalendar
urls:
    code    http://example.com
    web    http://example.com
public: True
address: Gleimstr. 6
postcode: 10439
city: Berlin
country: DE
latitude: 52.55247
longitude: 13.40364
deadlines:
    2009-11-01    visitor tickets
    2010-10-01    call for papers
timezone: 60
sessions:
    2010-12-29    10:00-11:00    first presentation
    2010-12-29    15:00-16:00    second presentation
    2010-12-30    15:00-16:00    third presentation
description:

GridCalendar will be presented

"""

# FIXME: check this class
#class EventManager( models.Manager ):# {{{1 pylint: disable-msg=R0904
#    """let event can show only public models for all
#    and private model only for group members and owner"""
#
#    _user = False
#
#    @classmethod
#    def set_auth_user( cls, sender, user, **kwargs ):# pylint: disable-msg=W0613
#        "set _user value after auth"
#        cls.set_user( user )
#
#    @classmethod
#    def set_user( cls, user ):
#        "set user for queries"
#        if type( user ) != AnonymousUser:
#            cls._user = user
#        else:
#            cls._user = False
#
#    @classmethod
#    def get_user( cls ):
#        "get user for queries"
#        return cls._user
#
#    def get_query_set( self ):
#        user = self.get_user()
#
#        if user:
#            if user.is_staff():
#                return super( EventManager, self ).get_query_set()
#            groups = Group.objects.filter( membership__user = user )
#            query_set = super( EventManager, self ).get_query_set().filter(
#                    Q( public = True ) |
#                    Q( user = user ) |
#                    Q( calendar__group__in = groups ) )
#        else:
#            query_set = super( EventManager, self )\
#            .get_query_set().filter( public = True )
#        return query_set
#
#user_auth_signal.connect( EventManager.set_auth_user )

class Event( models.Model ): # {{{1 pylint: disable-msg=R0904
    """ Event model """
    # fields {{{2
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
            help_text = _( u'Example: Demostration in Munich against software \
                patents organised by the German association FFII e.V.' ) )
    start = models.DateField( _( u'Start' ), blank = False,
            help_text = _( u"Example: 2006-10-25"))
    end = models.DateField( _( u'End' ), null = True, blank = True )
    tags = TagField( _( u'Tags' ), blank = True, null = True,
        help_text = _( u"Tags are case in-sensitive. Only letters (these can \
        be international, like: αöł), digits and hyphens (-) are allowed. \
        Tags are separated with spaces." ) )
    public = models.BooleanField( _( u'Public' ), default = True,
        help_text = _( u"A public event can be seen and edited by anyone, \
        otherwise only by the members of selected groups" ) )
    country = models.CharField( _( u'Country' ), blank = True, null = True,
            max_length = 2, choices = COUNTRIES )
    city = models.CharField( 
            _( u'City' ), blank = True, null = True, max_length = 50 )
    postcode = models.CharField( _( u'Postcode' ), blank = True, null = True,
            max_length = 16 )
    address = models.CharField( _( u'Street address' ), blank = True,
            null = True, max_length = 100 )
    latitude = models.FloatField( _( u'Latitude' ), blank = True, null = True,
            help_text = _( u"In decimal degrees, not \
            degrees/minutes/seconds. Prefix with \"-\" for South, no sign for \
            North." ) )
    longitude = models.FloatField( _( u'Longitude' ), blank = True, null = True,
            help_text = _( u"In decimal degrees, not \
                degrees/minutes/seconds. Prefix with \"-\" for West, no sign \
                for East." ) )
    timezone = models.SmallIntegerField( 
            _( u'Timezone' ), blank = True, null = True,
            help_text = _( u"Minutes relative to UTC (e.g. -60 means UTC-1)" ) )
    description = models.TextField(
            _( u'Description' ), blank = True, null = True )

    clone_of = models.ForeignKey( 'self', \
                               editable = False, \
                               blank = True, \
                               null = True )
    " Relation to orginal object, or null if this is orginal "# pylint: disable-msg=W0105,C0301

#    objects = EventManager() # {{{2

    # Meta {{{2
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        verbose_name = _( u'Event' )
        verbose_name_plural = _( u'Events' )

    # methods {{{2

    def next_coming_date_or_start(self): #{{{3
        """ returns the next most proximate date of an event to today, which
        can be the start date, the end date or one of the deadlines; or the
        start date if all are in the past
        
        >>> from datetime import timedelta
        >>> today = datetime.date.today()
        >>> event = Event(title="test for n_c_d " + today.isoformat(),
        ...     start=timedelta(days=1)+today,
        ...     end=timedelta(days=2)+today,
        ...     tags="test")
        >>> assert today + timedelta(days=1) == event.next_coming_date_or_start()

        >>> from datetime import timedelta
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

    def icalendar( self, ical = None ): #{{{3
        """ returns an iCalendar object of the event entry or add it to 'ical'

        >>> event = Event.parse_text(EXAMPLE)
        >>> ical = event.icalendar()
        >>> ical = vobject.readOne(ical.serialize())
        >>> assert (ical.vevent.categories.serialize() == 
        ...  u'CATEGORIES:calendar,software,open-source,gridmind,gridcalendar\\r\\n')
        """
        if ical is None:
            ical = vobject.iCalendar()
            ical.add('METHOD').value = 'PUBLISH' # IE/Outlook needs this
            ical.add('PRODID').value = settings.PRODID
        vevent = ical.add('vevent')
        vevent.add('SUMMARY').value = self.title
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
                settings.PROJECT_NAME + u'-' + \
                hashlib.md5(settings.PROJECT_ROOT).hexdigest() + u'-' \
                + unicode(self.id) + u'@' + \
                settings.HOST_IP
        if self.end:
            vevent.add('DTEND').value = self.end
        if self.description: vevent.add('DESCRIPTION').value = self.description
        # see rfc5545 3.8.7.2. Date-Time Stamp
        vevent.add('DTSTAMP').value = self.modification_time
        if self.public:
            vevent.add('CLASS').value = 'PUBLIC'
        else: vevent.add('CLASS').value = 'PRIVATE'
        if self.latitude and self.longitude:
            vevent.add('GEO').value = \
                unicode(self.latitude) + u";" + unicode(self.longitude)
        # TODO: add deadlines. As VALARMs or there is something better in
        # rfc5545 ?
        return ical

    def clone( self, public = False ): #{{{3
        """
        Make, save and return clone of object.
        Also make copy of all related objects,
        and relate then to clone.
        Set in clone relation to orginal.
        """
        orginal_pk = self.pk
        collected_objs = CollectedObjects()
        self._collect_sub_objects( collected_objs )
        related_models = collected_objs.keys()
        new = None
        # Traverse the related models in reverse deletion order.    
        for model in reversed( related_models ):
            # Find all field keys on `model` that point to a `related_model`.
            field_keys = []
            for field in model._meta.fields:# pylint: disable-msg=W0212
                if isinstance( field, models.ForeignKey ) \
                and field.rel.to in related_models:
                    field_keys.append( field )
            # Replace each `sub_obj` with a duplicate.
            sub_obj = collected_objs[model]
            for pk_val, obj in sub_obj.iteritems():# pylint: disable-msg=W0612
                for field_key in field_keys:
                    field_key_value = getattr( obj, "%s_id" % field_key.name )
                    if field_key_value in collected_objs[field_key.rel.to]:
                        dupe_obj = \
                        collected_objs[field_key.rel.to][field_key_value]
                        setattr( obj, field_key.name, dupe_obj )
                # Duplicate the object and save it.
                obj.id = None
                if new is None:
                    new = obj
                    new.clone_of_id = orginal_pk
                    new.public = public
                    new.save()
                else:
                    obj.save()
        return new

    def get_clones( self ): #{{{3
        "get all clones of event"
        clones = Event.objects.filter( clone_of = self )
        return clones

    @classmethod
    def set_user( cls, user ): # classmethod {{{3
        "set user context for class"
        cls.objects.set_user( user )

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
        "get internal URL of an event"
        #return '/e/show/' + str(self.id) + '/'
        #return (reverse('event_show', kwargs ={'event_id': str(self.id)}))
        return ( 'event_show', (), { 'event_id': self.id } )

#    def pre_save( self ):
#        old_event = None
#        old = None
#        if self.pk != None:
#            try:
#                old_event = Event.objects.get( pk = self.pk )
#                old = old_event.as_text()
#                user = Event.objects.get_user()
#                history = EventHistory( \
#                        event = old_event,
#                        user = user if user else None, \
#                        new = None, \
#                        old = old )
#                history.save()
#            except Event.DoesNotExist:
#                pass

    def save( self, *args, **kwargs ): #{{{3
        """ Call the real 'save' function after checking that a private event
        has an owner, and that the public field is not changed ever after
        creation """
        # It is not allowed to have a non-public event without owner:
        assert not ( ( self.public == False ) and ( 
            self.user == None  or self.user.id == None ) )
        # checks that the public field is not changed if the Event already
        # exists
        try:
            old_event = Event.objects.get( id = self.id )
            # It is not allowed to modify the 'public' field:
            assert ( self.public == old_event.public )
        except Event.DoesNotExist:
            pass
        # Call the "real" save() method:
        super( Event, self ).save( *args, **kwargs )

    @staticmethod
    def post_save( sender, **kwargs ): #{{{3
        """ notify users if a filter of a user matches the event. """
        # FIXME: implement a Queue, see comments on 
        # http://www.artfulcode.net/articles/threading-django/
        thread = threading.Thread(
                target=Filter.notify_users_when_wanted( kwargs['instance'] ),
                args=[ kwargs['instance'], ] )
        thread.setDaemon(True)
        thread.start()
#       #FIXME: save history
#        try:
#            new_event = Event.objects.get( pk = self.pk )
#            new = new_event.as_text()
##            date = EventHistory.objects.latest( 'date' )
#            try:
#                date = EventHistory.objects.filter( event = new_event )\
#                .latest( 'date' )
#                history = EventHistory.objects.get( event = new_event, \
#                                                     date = date )
#                history.new = new
#
#            except EventHistory.DoesNotExist:
#                user = Event.objects.get_user()
#                history = EventHistory( \
#                                        event = new_event,
#                                        user = Event.objects.get_user() \
#                                        if Event.objects.get_user() \
#                                        else None, \
#                                        new = new, old = None )
#            history.save()
#        except Event.DoesNotExist:
#            pass

    @staticmethod
    def example(): #{{{3
        """ returns an example of an event as unicode
        
        >>> from django.utils.encoding import smart_str
        >>> text = Event.example()
        >>> event = Event.parse_text(text)
        >>> assert (smart_str(text) == event.as_text())
        >>> # test also that it works when using an English name for the
        >>> # country
        >>> text = text.replace(u'DE', u'Germany')
        >>> event = Event.parse_text(text)
        >>> text = text.replace(u'Germany', u'DE')
        >>> assert (smart_str(text) == event.as_text())
        """
        return EXAMPLE

    @staticmethod
    def list_as_text( iterable ): #{{{3
        """ returns an utf-8 string of all events in `iterable` """
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
            elif keyword == u'end':
                if self.end:
                    to_return += u''.join( [
                        keyword, u": ",
                        unicode(self.end.strftime( "%Y-%m-%d")), u"\n"] )
            elif keyword == u'country':
                if self.country:
                    to_return += keyword + u": " + self.country + u"\n"
            elif keyword == u'timezone':
                if self.timezone:
                    to_return += keyword + u": " + unicode(self.timezone)+u"\n"
            elif keyword == u'latitude':
                if self.latitude:
                    to_return += keyword + u": " + unicode(self.latitude)+u"\n"
            elif keyword == u'longitude':
                if self.longitude:
                    to_return += keyword + u": " + unicode(self.longitude)+u"\n"
            elif keyword == u'acronym':
                if self.acronym:
                    to_return += keyword + u": " + self.acronym + u"\n"
            elif keyword == u'tags':
                if self.tags:
                    to_return += keyword + u": " + self.tags + u"\n"
            elif keyword == u'public':
                # FIXME: it makes no sense to show this field, think how to
                # handle the public field
                if self.public:
                    to_return += keyword + u": " + unicode(self.public) + u"\n"
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
            # the groups an event belong to are not shown for privacy of the
            # groups and because the list can be too long
            # elif keyword == 'groups' and self.event_in_groups:
            #     calendars = Calendar.objects.filter( event = self.id )
            #     if len( calendars ) > 0:
            #         to_return += keyword + ":"
            #         for calendar in calendars:
            #             to_return += ' "' + str( calendar.group.name ) + '"'
            #         to_return += '\n'
            elif keyword == u'groups':
                pass
            elif keyword == u'description':
                if self.description:
                    to_return += u'description:\n' + self.description
            else:
                raise RuntimeError('unexpected keyword: ' + keyword)
        return smart_str(to_return)

    @staticmethod
    def get_fields( text ): #{{{3
        """ parse an event as unicode text and returns a tuple with two
        dictionaries, or raises a ValidationError.

        The first dictionary contains the names of simple fields as keys and
        its values as values.

        The second dictionary contains the names of complex fields as keys, and
        lists as values. The list contains all lines including the first one.

        >>> example = Event.example()
        >>> s,c = Event.get_fields(example)
        >>> assert(s[u'acronym'] ==  u'GriCal')
        >>> assert(s[u'address'] ==  u'Gleimstr. 6')
        >>> assert(s[u'city'] ==  u'Berlin')
        >>> assert(s[u'country'] ==  u'DE')
        >>> assert(s[u'end'] ==  u'2010-12-30')
        >>> assert(s[u'latitude'] ==  u'52.55247')
        >>> assert(s[u'longitude'] ==  u'13.40364')
        >>> assert(s[u'postcode'] ==  u'10439')
        >>> assert(s[u'public'] ==  u'True')
        >>> assert(s[u'start'] ==  u'2010-12-29')
        >>> assert(s[u'tags'] ==  u'calendar software open-source gridmind gridcalendar')
        >>> assert(s[u'timezone'] ==  u'60')
        >>> assert(s[u'title'] ==  u'GridCalendar presentation')
        >>> assert(c[u'deadlines'][1].replace(' ','') == u'2009-11-01visitortickets')
        >>> assert(c[u'deadlines'][2].replace(' ','') == u'2010-10-01callforpapers')
        >>> c['deadlines'][3]
        Traceback (most recent call last):
            ...
        IndexError: list index out of range

        """
        if not isinstance(text, unicode):
            text = smart_unicode(text)
        # MacOS uses \r, and Windows uses \r\n - convert it all to Unix \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
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
        for line in text.split('\n'):
            line_counter += 1
            if current and current == "description":
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
                simple_dic[ syns[field_m.group(1).lower()]] = field_m.group(2)
                continue
            if not syns[field_m.group(1).lower()] in complex_list:
                raise RuntimeError("field %s was not in 'complex_list'" %
                        field_m.group(1))
            current = syns[field_m.group(1).lower()]
            lines.append(line)
        if current:
            complex_dic[current] = lines
        return simple_dic, complex_dic

    @classmethod
    def parse_text( cls, input_text_in, event_id = None, user_id = None ): #{{{3
        # doc {{{4
        """It parses a text and saves it as a single event in the data base and
        return the event object, or doesn't save the event and raises a
        ValidationError or a Event.DoesNotExist when there is no event with
        `event_id`)

        It raises a ValidationError when the data is wrong, e.g. when a date is
        not valid. It raises and Event.DoesNotExist error when there is no
        event with `event_id`

        A text to be parsed as an event is of the form::

            title: a title
            tags: tag1 tag2 tag3
            start: 2020-01-30
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

        The text for the field 'groups' is of the form::

            groups: group1 group2 ...

        """
        # code {{{2
        if not isinstance(input_text_in, unicode):
            input_text_in = smart_unicode(input_text_in)
        if user_id is not None:
            # the following line can raise a User.DoesNotExist
            user = User.objects.get(id = user_id)
        # test that the necessary fields are present
        simple_fields, complex_fields = Event.get_fields(input_text_in)
        for field in Event.get_necessary_fields():
            if not (simple_fields.has_key(field) or
                    complex_fields.has_key(field)):
                raise ValidationError(
                        _(u"The following necessary field is not present: ") +
                        smart_unicode(field))
        # Check if the country is in Englisch (instead of the international
        # short two-letter form) and replace it. TODO: check in other
        # languages.
        if simple_fields.has_key(u'country'):
            for names in COUNTRIES:
                if names[1].lower().encode('utf-8') == \
                simple_fields[u'country'].lower().encode('utf-8'):
                    simple_fields['country'] = names[0]
                    break
        # creates an event with a form
        # FIXME: process field 'public' now because it is not in EventForm
        from gridcalendar.events.forms import EventForm
        if event_id == None :
            event_form = EventForm( simple_fields )
        else:
            # the following line can raise an Event.DoesNotExist
            event = Event.objects.get( id = event_id )
            if user_id is not None:
                if not event.is_viewable_by_user(user_id):
                    raise RuntimeError(
                        _(u'the event is not viewable by the user'))
            event_form = EventForm( simple_fields, instance = event )
        if event_form.is_valid():
            event = event_form.save()
            event_id = event.id
            if (user_id is not None) and (event.user == None):
                event.user = user
        else:
            raise ValidationError(event_form.errors.as_text())
        # processing complex fields if present
        try:
            if complex_fields.has_key(u'urls'):
                EventUrl.parse_text(event,
                        u'\n'.join(complex_fields[u'urls']))
                del complex_fields[u'urls']
            if complex_fields.has_key(u'deadlines'):
                EventDeadline.parse_text(event,
                        u'\n'.join(complex_fields[u'deadlines']))
                del complex_fields[u'deadlines']
            if complex_fields.has_key(u'sessions'):
                EventSession.parse_text(event,
                        u'\n'.join(complex_fields[u'sessions']))
                del complex_fields[u'sessions']
            if complex_fields.has_key(u'description'):
                description = u"\n".join(complex_fields[u'description'])
                # remove the word 'description'
                event.description = description[13:]
                del complex_fields[u'description']
            assert(len(complex_fields) == 0)
        except ValidationError as error:
            Event.objects.get( id = event_id ).delete()
            raise error
        return event

    @staticmethod
    def get_complex_fields(): #{{{3
        """ returns a tuple of names of user-editable fields (of events) which
        can contain many lines in the input text representation of an Event.
        """
        return ("urls", "deadlines", "sessions", "description",)

    @staticmethod
    def get_simple_fields(): #{{{3
        """ returns a tuple of names of user-editable fields (of events) which
        have only one line in the input text representation of an Event.
        
        Notice that 'groups' can be present in the input text representation,
        but it is not present (for privacy reasons) in the output text
        representation.
        """ 
        field_names = [unicode(f.name) for f in Event._meta.fields]
        field_names.append(u"groups")
        field_names.remove(u"id")
        field_names.remove(u"user")
        field_names.remove(u"creation_time")
        field_names.remove(u"modification_time")
        field_names.remove(u"clone_of")
        field_names.remove(u"description")
        return tuple(field_names)
 
    @staticmethod
    def get_necessary_fields(): #{{{3
        """ returns a tuple of names of the necessary filed fields of an event.
        """
        return (u"title", u"start", u"tags", u"urls")

    @staticmethod
    def get_priority_list(): #{{{3
        """ returns a tuple of names of fields in the order they
        should appear when showing an event as a text, i.e. in the output text
        representation of an Event.
        
        Notice that 'groups' can be present in the input text representation,
        but it is not present (for privacy reasons) in the output text
        representation.
 
        >>> gpl_len = len(Event.get_priority_list())
        >>> gsf_len = len(Event.get_simple_fields())
        >>> gcf_len = len(Event.get_complex_fields())
        >>> assert(gpl_len + 1 == gsf_len + gcf_len)
        >>> synonyms_values_set = set(Event.get_synonyms().values())
        >>> assert(gpl_len + 1 == len(synonyms_values_set))
 
        """
        return (u"acronym", u"title", u"start", u"end", u"tags", u"urls",
            u"public", u"address", u"postcode", u"city", u"country", u"latitude",
            u"longitude", u"deadlines", u"timezone", u"sessions", u"description")
 
    @staticmethod
    def get_synonyms(): #{{{3
        """Returns a dictionay with names (strings) and the fields (strings)
        they refer.

        All values of the returned dictionary (except groups, urls and
        sessions) are names of fields of the Event class.

        >>> synonyms_values_set = set(Event.get_synonyms().values())
        >>> assert ('groups' in synonyms_values_set)
        >>> synonyms_values_set.remove('groups')
        >>> assert ('urls' in synonyms_values_set)
        >>> synonyms_values_set.remove('urls')
        >>> assert ('deadlines' in synonyms_values_set)
        >>> synonyms_values_set.remove('deadlines')
        >>> assert ('sessions' in synonyms_values_set)
        >>> synonyms_values_set.remove('sessions')
        >>> field_names = [f.name for f in Event._meta.fields]
        >>> field_names = set(field_names)
        >>> assert(len(synonyms_values_set) == 14)
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
        synonyms = {}
        add( synonyms, u'ti', u'title' )
        add( synonyms, u'title', u'title' )       # title
        add( synonyms, u'titl', u'title' )
        add( synonyms, u'start', u'start' )       # start
        add( synonyms, u'st', u'start' )
        add( synonyms, u'starts', u'start' )
        add( synonyms, u'date', u'start' )
        add( synonyms, u'da', u'start' )
        add( synonyms, u'start date', u'start' )
        add( synonyms, u'start-date', u'start' )
        add( synonyms, u'start_date', u'start' )
        add( synonyms, u'sd', u'start' )
        add( synonyms, u'tags', u'tags' )        # tags
        add( synonyms, u'ta', u'tags' )
        add( synonyms, u'tag', u'tags' )
        add( synonyms, u'subjects', u'tags' )
        add( synonyms, u'subject', u'tags' )
        add( synonyms, u'su', u'tags' )
        add( synonyms, u'subj', u'tags' )
        add( synonyms, u'end', u'end' )         # end
        add( synonyms, u'en', u'end' )
        add( synonyms, u'ends', u'end' )
        add( synonyms, u'finish', u'end' )
        add( synonyms, u'finishes', u'end' )
        add( synonyms, u'fi', u'end' )
        add( synonyms, u'enddate', u'end' )
        add( synonyms, u'end date', u'end' )
        add( synonyms, u'end-date', u'end' )
        add( synonyms, u'end_date', u'end' )
        add( synonyms, u'ed', u'end' )
        add( synonyms, u'endd', u'end' )
        add( synonyms, u'acronym', u'acronym' )     # acronym
        add( synonyms, u'ac', u'acronym' )
        add( synonyms, u'acro', u'acronym' )
        add( synonyms, u'public', u'public' )      # public
        add( synonyms, u'pu', u'public' )
        add( synonyms, u'open', u'public' )
        add( synonyms, u'op', u'public' )
        add( synonyms, u'country', u'country' )     # country
        add( synonyms, u'co', u'country' )
        add( synonyms, u'coun', u'country' )
        add( synonyms, u'nation', u'country' )
        add( synonyms, u'nati', u'country' )
        add( synonyms, u'na', u'country' )
        add( synonyms, u'city', u'city' )        # city
        add( synonyms, u'ci', u'city' )
        add( synonyms, u'town', u'city' )
        add( synonyms, u'to', u'city' )
        add( synonyms, u'postcode', u'postcode' )    # postcode
        add( synonyms, u'po', u'postcode' )
        add( synonyms, u'zip', u'postcode' )
        add( synonyms, u'zi', u'postcode' )
        add( synonyms, u'code', u'postcode' )
        add( synonyms, u'address', u'address' )     # address
        add( synonyms, u'ad', u'address' )
        add( synonyms, u'addr', u'address' )
        add( synonyms, u'street', u'address' )
        add( synonyms, u'latitude', u'latitude' )    # latitude
        add( synonyms, u'lati', u'latitude' )
        add( synonyms, u'la', u'latitude' )
        add( synonyms, u'longitude', u'longitude' )   # longitude
        add( synonyms, u'lo', u'longitude' )
        add( synonyms, u'long', u'longitude' )
        add( synonyms, u'timezone', u'timezone' )    # timezone
        add( synonyms, u'tz', u'timezone' )
        add( synonyms, u'description', u'description' ) # description
        add( synonyms, u'de', u'description' )
        add( synonyms, u'desc', u'description' )
        add( synonyms, u'des', u'description' )
        add( synonyms, u'info', u'description' )
        add( synonyms, u'infos', u'description' )
        add( synonyms, u'in', u'description' )
        add( synonyms, u'groups', u'groups' )      # groups (*)
        add( synonyms, u'gr', u'groups' )
        add( synonyms, u'group', u'groups' )
        add( synonyms, u'urls', u'urls' )        # urls (*)
        add( synonyms, u'ur', u'urls' )
        add( synonyms, u'url', u'urls' )
        add( synonyms, u'web', u'urls' )
        add( synonyms, u'webs', u'urls' )
        add( synonyms, u'we', u'urls' )
        add( synonyms, u'deadlines', u'deadlines' )  # deadlines (*)
        add( synonyms, u'deadline', u'deadlines' )
        add( synonyms, u'dl', u'deadlines' )
        add( synonyms, u'sessions', u'sessions' )    # sessions (*)
        add( synonyms, u'se', u'sessions' )
        add( synonyms, u'session', u'sessions' )
        add( synonyms, u'times', u'sessions' )
        add( synonyms, u'time', u'sessions' )
        # (*) can have multi-lines and are not simple text fields
        return synonyms

    def is_viewable_by_user(self, user): #{{{3
        """ returns true if `user` can see `event` """
        return Event.is_event_viewable_by_user(self, user)

    @staticmethod
    def is_event_viewable_by_user( event, user ): #{{{3
        """ returns true if `user` can see `event` """
        # checking `event` parameter
        if event is None:
            raise  TypeError("`event` parameter was None")
        if isinstance(event, Event):
            pass
        elif isinstance(event, int):
            event = Event.objects.get(pk=event)
        elif isinstance(event, unicode) or isinstance(event, str):
            event = Event.objects.get( pk = int(event) )
        else:
            raise TypeError(
                "'event' must be an Event or an integer but it was: " +
                str(event.__class__))
        if event.public:
            return True
        # checking `user` parameter
        if user is None:
            return event.public
        if isinstance(user, User):
            pass
        elif isinstance(user, int):
            user = User.objects.get(pk=user)
        elif isinstance(user, unicode) or isinstance(user, str):
            user = User.objects.get( pk = int(user) )
        else: raise TypeError(
                "'user' must be a User or an integer but it was: " +
                str(user.__class__))
        if not user.is_authenticated():
            return event.public
        if event.user.id == user.id:
            return True
        # iterating over all groups that the event belongs to
        for group in Group.objects.filter( events__id__exact = event.id ):
            if Group.is_user_in_group( user.id, group.id ):
                return True
        return False

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

# post_save.connect {{{1
# see http://docs.djangoproject.com/en/1.2/topics/signals/
post_save.connect( Event.post_save, sender = Event, dispatch_uid="Event.post_save" )

class ExtendedUser(User): # {{{1
    """ Some aditional funtions to users
    
    It uses the django proxy-models approach, see
    http://docs.djangoproject.com/en/1.2/topics/db/models/#proxy-models

    The variable USER (a ExtendedUser instance) is available in the `context`
    for all views and templates

    >>> from events.models import Event, Group, Membership
    >>> now = datetime.datetime.now().isoformat()
    >>> user = User.objects.create(username = "user " + now)
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
    class Meta:
        proxy = True

    def get_hash(self):
        """ return the hash code to authenticate by url """
        return ExtendedUser.calculate_hash(self.id)

    @staticmethod
    def calculate_hash(user_id):
        """ returns the identification hash of the user or None """
        if user_id is None:
            return None
        return hashlib.sha256(
                "%s!%s" % (settings.SECRET_KEY, user_id)).hexdigest()

    def has_groups(self):
        """ returns True if the user is at least member of a group, False
        otherwise """
        return Group.objects.filter( membership__user = self ).count() > 0

    def get_groups(self):
        """ returns a queryset of the user's groups """
        return Group.objects.filter( membership__user = self )

    def has_filters(self):
        """ returns True if the user has at least one filter, False
        otherwise """
        return Filter.objects.filter( user = self ).count() > 0

    def get_filters(self):
        """ returns a queryset of the user's filters """
        return Filter.objects.filter( user = self )

    def has_groups_with_coming_events( self ):
        """ returns True if at least one group of the user has a coming event
        (start, end or a deadline in the future)
        """
        for group in self.get_groups():
            if group.has_coming_events():
                return True
        return False

class EventUrl( models.Model ): # {{{1
    """ stores urls of events
    
    Code example: getting all events with more than one url:
    >>> from gridcalendar.events.models import Event
    >>> from django.db.models import Count
    >>> urls_numbers = Event.objects.annotate(Count('urls'))
    >>> gt1 = filter(lambda x: x.urls__count > 1, urls_numbers)
    """
    event = models.ForeignKey( Event, related_name = 'urls' )
    url_name = models.CharField( _( u'URL Name' ), blank = False, null = False,
            max_length = 80, help_text = _( 
            u"Example: information about accomodation" ) )
    url = models.URLField( _( u'URL' ), blank = False, null = False )
    class Meta: # pylint: disable-msg=C0111
        ordering = ['url_name']
        unique_together = ( "event", "url_name" )
    def __unicode__( self ):
        return self.url

    @staticmethod
    def parse_text(event, text):
        """ validates and saves text lines containing EventUrl entries, raising
        ValidationErrors if there are errors

        It also removes all previous EventUrls for `event` if no errors occur.

        >>> now = datetime.datetime.now().isoformat()
        >>> event = Event(title="test for parse_text in EventUrl" + now,
        ...         start=datetime.date(2020, 1, 1), tags="test")
        >>> event.save()
        >>> event_url = EventUrl(event=event,
        ...         url_name="test", url="http://example.com")
        >>> event_url.save()
        >>> text = u"urls:\\n    test1 http://example.com\\n    test2 http://example.com"
        >>> EventUrl.parse_text(event, text)
        >>> event_urls = EventUrl.objects.filter(event=event)
        >>> assert(len(event_urls) == 2)
        >>> text = u"urls:\\n    test3 http://example.com"
        >>> EventUrl.parse_text(event, text)
        >>> event_urls = EventUrl.objects.filter(event=event)
        >>> assert(len(event_urls) == 1)
        >>> assert(event_urls[0].url_name == u'test3')
        >>> text = u"web: http://example.com "
        >>> EventUrl.parse_text(event, text)
        >>> event_urls = EventUrl.objects.filter(event=event)
        >>> assert(len(event_urls) == 1)
        >>> assert(event_urls[0].url_name == u'url')
        """
        if isinstance(event, Event):
            pass
        elif isinstance(event, int):
            event = Event.objects.get(pk = event)
        else:
            event = Event.objects.get(pk = int(event))
        text = smart_unicode(text)
        # MacOS uses \r, and Windows uses \r\n - convert it all to Unix \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*(.*?)\s*$")
        lines = text.split('\n')
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
                urls[ field_m.group(1) ] = field_m.group(2)
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
        # delete old urls of the event which are not in `text` parameter
        # TODO: save history
        event_urls = EventUrl.objects.filter(event=event)
        for event_url in event_urls:
            if not urls.has_key(event_url.url_name):
                event_url.delete()

class EventDeadline( models.Model ): # {{{1
    """ stores deadlines for events """
    event = models.ForeignKey( Event, related_name = 'deadlines' )
    deadline_name = models.CharField( 
            _( u'Deadline name' ), blank = False, null = False,
            max_length = 80, help_text = _( 
            "Example: call for papers deadline" ) )
    deadline = models.DateField( _( u'Deadline' ), blank = False, null = False )
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        ordering = ['deadline', 'deadline_name']
        unique_together = ( "event", "deadline_name" )
    def __unicode__( self ):
        return unicode( self.deadline ) + u'    ' + self.deadline_name

    @staticmethod
    def parse_text(event, text):
        """ validates and saves text lines containing EventDeadline entries,
        raising ValidationErrors if there are errors

        It also removes all previous EventDeadlines for `event` if no errors
        occur.

        >>> now = datetime.datetime.now().isoformat()
        >>> event = Event(title="test for parse_text in EventDeadline " + now,
        ...         start=datetime.date(2020, 1, 1), tags="test")
        >>> event.save()
        >>> event_deadline = EventDeadline(
        ...         event = event, deadline_name = "test1",
        ...         deadline = datetime.date(2020,1,1))
        >>> event_deadline.save()
        >>> text = u"deadlines:\\n    2010-01-02 test1\\n    2010-02-02 test2"
        >>> EventDeadline.parse_text(event, text)
        >>> event_deadlines = EventDeadline.objects.filter(event=event)
        >>> assert(len(event_deadlines) == 2)
        >>> text = u"deadlines:\\n    2010-03-03 test3"
        >>> EventDeadline.parse_text(event, text)
        >>> event_deadlines = EventDeadline.objects.filter(event=event)
        >>> assert(len(event_deadlines) == 1)
        >>> assert(event_deadlines[0].deadline_name == u'test3')
        """
        if isinstance(event, Event):
            pass
        elif isinstance(event, int):
            event = Event.objects.get(pk = event)
        else:
            event = Event.objects.get(pk = int(event))
        text = smart_unicode(text)
        # MacOS uses \r, and Windows uses \r\n - convert it all to Unix \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*(.*?)\s*$")
        lines = text.split('\n')
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
                    _(u"first line for deadlines doesn't contain a \
                    synonym of 'deadlines' before the colon: ") + lines[0])
        deadlines = {} # keys are names, values are dates
        if field_m.group(2) != u'':
            date_p = re.compile(r"^(\d\d\d\d)-(\d\d)-(\d\d)$")
            date_m = date_p.match(field_m.group(2))
            if not date_m:
                raise ValidationError(
                        _(u"default deadline was not of the form " +
                        u"nnnn-nn-nn. It was: ") + field_m.group(2))
            # default deadline:
            deadlines['deadline'] = datetime.date(
                    int(date_m.group(1)), int(date_m.group(2)),
                    int(date_m.group(3)))
        if len(lines) > 1:
            field_p = re.compile(r"^\s+(\d\d\d\d)-(\d\d)-(\d\d)\s+(.*?)\s*$")
            for line in lines[1:]:
                field_m = field_p.match(line)
                if not field_m:
                    raise ValidationError(
                        _(u"the following line for a deadline is malformed: ")
                        + line)
                deadlines[ field_m.group(4) ] = datetime.date(
                        int(field_m.group(1)), int(field_m.group(2)),
                        int(field_m.group(3)))
        event_deadlines = list() # stores EventDeadlines to be saved at the end
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
        # delete old deadlines of the event which are not in `text` parameter
        event_deadlines = EventDeadline.objects.filter(event=event)
        for event_deadline in event_deadlines:
            if not deadlines.has_key(event_deadline.deadline_name):
                event_deadline.delete()

class EventSession( models.Model ): # {{{1
    """ stores sessions for events """
    # TODO: check when submitting that session_dates are within the limits of
    # start and end dates of the event.
    event = models.ForeignKey( Event, related_name = 'sessions' )
    session_name = models.CharField( 
            _( u'Session name' ), blank = False, null = False, max_length = 80,
            help_text = _( u"Example: day 2 of the conference" ) )
    session_date = models.DateField( 
            _( u'Session day' ), blank = False, null = False )
    session_starttime = models.TimeField( 
            _( u'Session start time' ), blank = False, null = False )
    session_endtime = models.TimeField( 
            _( u'Session end time' ), blank = False, null = False )
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        ordering = ['session_date', 'session_starttime']
        unique_together = ( "event", "session_name" )
        verbose_name = _( u'Session' )
        verbose_name_plural = _( u'Sessions' )
    def __unicode__( self ):
        return unicode( self.session_date ) + u'    ' + \
                unicode( self.session_starttime ) + u'-' + \
                unicode( self.session_endtime ) + u'    ' + self.session_name

    @staticmethod
    def parse_text(event, text):
        """ validates and saves text lines containing EventSession entries,
        raising ValidationErrors if there are errors

        It also removes all previous EventSessions for `event` if no errors
        occur.

        Example::

            sessions:
                2009-01-01 10:00-16:00 first day
                2009-01-01 11:00-12:00 speech about GridCalendar

        >>> import datetime
        >>> now = datetime.datetime.now().isoformat()
        >>> event = Event(title="test for parse_text in EventSession " + now,
        ...         start=datetime.date(2020, 1, 1), tags="test")
        >>> event.save()
        >>> event_session = EventSession(
        ...     event=event, session_name="test1",
        ...     session_date = datetime.date(2010,1,1),
        ...     session_starttime = datetime.time(0,0),
        ...     session_endtime = datetime.time(1,0))
        >>> event_session.save()
        >>> text = u"sessions:\\n    2010-01-02 11:00-12:00 test1\\n"
        >>> text = text +      "    2010-01-03 12:00-13:00 test2"
        >>> EventSession.parse_text(event, text)
        >>> event_sessions = EventSession.objects.filter(event=event)
        >>> assert(len(event_sessions) == 2)
        >>> text = u"sessions:\\n    2010-01-02 13:00-14:00 test1"
        >>> EventSession.parse_text(event, text)
        >>> event_sessions = EventSession.objects.filter(event=event)
        >>> assert(len(event_sessions) == 1)
        >>> assert(event_sessions[0].session_name == u'test1')
        """
        if isinstance(event, Event):
            pass
        elif isinstance(event, int):
            event = Event.objects.get(pk = event)
        else:
            event = Event.objects.get(pk = int(event))
        text = smart_unicode(text)
        # MacOS uses \r, and Windows uses \r\n - convert it all to Unix \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*(.*?)\s*$")
        lines = text.split('\n')
        # test for default deadline
        field_m = field_p.match(lines[0])
        if not field_m:
            raise ValidationError(
                    _(u"first line for sessions is malformed"))
        syns = Event.get_synonyms()
        if syns[field_m.group(1).lower()] != u'sessions':
            raise ValidationError(
                    _(u"first line for sessions doesn't contain a " +
                    "synonym of 'sessions' before the colon"))
        class Session:
            def __init__(self, date=None, start=None, end=None, name=None):
                self.date = date
                self.start = start
                self.end = end
                self.name = name
        sessions = list()
        if field_m.group(2) != u'': # default session
            times_p = re.compile(r"^(\d\d):(\d\d)-(\d\d):(\d\d)\s*$")
            times_m = times_p.match(field_m.group(2))
            if not times_m:
                raise ValidationError(
                        _(u'default session data is not of the ' +
                        'form nn:nn-nn:nn It was: ') + field_m.group(2))
            try:
                sessions.append(Session(
                    date = event.start,
                    start = datetime.time(
                        int(times_m.group(1)),
                        int(times_m.group(2))),
                    end =  datetime.time(
                        int(times_m.group(3)),
                        int(times_m.group(4))),
                    name = 'time'))
                # TODO: use local time of event if present
            except ValueError:
                raise ValidationError(
                        _(u"a time entry was wrong for: ") + field_m.group(2))
        if len(lines) > 1:
            field_p = re.compile(
                    r"^\s+(\d\d\d\d)-(\d\d)-(\d\d)\s+(\d\d):(\d\d)-(\d\d):(\d\d)\s+(.*?)\s*$")
                    #      1          2      3        4      5      6      7       8
            for line in lines[1:]:
                field_m = field_p.match(line)
                if not field_m:
                    raise ValidationError(
                            _(u"the following line is malformed: ") + line)
                try:
                    sessions.append(Session(
                        date = datetime.date(
                            int(field_m.group(1)),
                            int(field_m.group(2)),
                            int(field_m.group(3))),
                        start = datetime.time(
                            int(field_m.group(4)),
                            int(field_m.group(5))),
                        end = datetime.time(
                            int(field_m.group(6)),
                            int(field_m.group(7))),
                        name = field_m.group(8)))
                except ValueError:
                    raise ValidationError(
                            _(u"a time/date entry was wrong for line: ") + line)
                # TODO: use local time of event if present
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
        # delete old sessions of the event which are not in `text` parameter
        # TODO: save history
        event_sessions = EventSession.objects.filter(event=event)
        for event_session in event_sessions:
            found = False
            for session in sessions:
                if session.name == event_session.session_name:
                    found = True
                    break
            if not found:
                event_session.delete()

class EventHistory( models.Model ): # {{{1
    """ keeps history of changes (editions) on an event """
    event = models.ForeignKey( Event )
    user = models.ForeignKey( User, unique = False, \
                            verbose_name = _( u'User' ), \
                            blank = True, null = True )
    date = models.DateTimeField( _( u'Creation time' ), editable = False,
            auto_now_add = True )
    """Time stamp when the change was done""" # pyling: disable-msg=W0105
    old = models.TextField( _( u'Old data' ), blank = True, null = True )
    """the event as text before the change""" # pyling: disable-msg=W0105
    new = models.TextField( _( u'New data' ), blank = True, null = True )
    """ the event as text after the change """ # pyling: disable-msg=W0105

class Filter( models.Model ): # {{{1
    """ search queries of users """
    # {{{2 attributes
    user = models.ForeignKey(
            User, unique = False, verbose_name = _( u'User' ) )
    modification_time = models.DateTimeField( _( u'Modification time' ),
            editable = False, auto_now = True )
    query = models.CharField( _( u'Query' ), max_length = 500, blank = False,
            null = False )
    name = models.CharField( 
            _( u'Name' ), max_length = 40, blank = False, null = False )
    email = models.BooleanField( _( u'Email' ), default = False, help_text =
            _(u'If set it sends an email to a user when a new event matches'))

    class Meta: # {{{2 pylint: disable-msg=C0111,W0232,R0903
        unique_together = ( "user", "name" )
        verbose_name = _( u'Filter' )
        verbose_name_plural = _( u'Filters' )

    def __unicode__( self ): # {{{2
        return self.name

    @models.permalink
    def get_absolute_url( self ): # {{{2
        """ django utility ofr url look-up """
        return ( 'filter_edit', (), { 'filter_id': self.id } )

    def upcoming_events( self, limit = 5 ): # {{{2
        """ return the next `limit` events matching `self.query` """
        return Filter.matches( self.query, self.user, limit )[0]

    def matches_event( self, event ):
        """ return True if the query matches the event, False otherwise 
        
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
        >>> user = User.objects.create(username = "user " + now)
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
        # IMPORTANT: this code must be in accordance with
        # `Filter.matches_queryset`
        query = self.query
        # dates
        date_regex = re.compile('\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*', UNICODE)
        # FIXME: e.g. a2010-01-01 shouldn't work
        dates = date_regex.findall( query )
        if dates:
            dates = [ datetime.date( int(year), int(month), int(day) ) for \
                    year, month, day in dates ]
            sorted_dates = sorted( dates )
            date1 = sorted_dates[0] # first date
            date2 = sorted_dates[-1] # last date
            if not (event.start >= date1 and event.start <= date2):
                if not ( event.end and
                        event.end >= date1 and event.end <= date2):
                    matches = False
                    for dea in EventDeadline.objects.filter(event = event):
                        if (dea.deadline >= date1 and dea.deadline <= date2):
                            matches = True
                            break
                    if not matches:
                        return False
            # remove all dates (yyyy-mm-dd) from the query
            query = date_regex.sub("", query)
            # if there is nothing more in the query, returns True because the
            # dates matched
            if query == "":
                return True
        else:
            today = datetime.date.today()
            if not ( event.start >= today or
                    ( event.end and event.end <= today ) or
                    Event.objects.filter(deadlines__deadline__gte = today) ):
                return False
        # groups
        group_regex = re.compile('\s*!([\w-]+)\s*', UNICODE)
        for name in group_regex.findall(query):
            if not Group.objects.filter( Q( name__iexact = name ) &
                    Q( calendar__event = event ) ).exists():
                return False
        # remove all groups (!group_name) from the query
        query = group_regex.sub("", query)
        # if there is nothing more in the query, returns True because the
        # groups matched
        if query == "":
            return True
        # locations
        loc_regex = re.compile('\s*@([\w-]+)\s*', UNICODE)
        for loc_name in loc_regex.findall(query):
            matches = False
            if event.city and event.city.lower() == loc_name.lower():
                matches = True
            # FIXME: search for two-letters country and for name country
            # TODO: use also translations of locations
            if event.country and event.country.lower() == loc_name.lower():
                matches = True
            if not matches:
                return False
        # remove all locations (@location) from the query
        query = loc_regex.sub("", query)
        # if there is nothing more in the query, returns True because the
        # query matched
        if query == "":
            return True
        # tags
        tag_regex = re.compile('\s*#([\w-]+)\s*', UNICODE)
        for tag in tag_regex.findall(query):
            if not tag in event.tags:
                return False
        # remove all tags (#tag_name) from the query
        query = tag_regex.sub("", query)
        # if there is nothing more in the query, returns True because the
        # tags matched
        if query == "":
            return True
        # look for words
        regex = re.compile('([^!@#]\w+)', UNICODE)
        matches = False
        for word in regex.findall(query):
            word = word.lower()
            if ( event.title.lower().find(word) != -1 or
                    event.tags.lower().find(word) != -1 or
                    ( event.city and event.city.lower() == word ) or
                    ( event.country and event.country.lower() == word ) or
                    ( event.acronym and event.acronym.lower() == word ) ):
                matches = True
                break
        return matches

    # FIXME: add a parameter include_related=False and change the call to this
    # elsewhere
    @staticmethod
    def matches( query, user, limit = 100 ): # {{{2
        """ returns a sorted (`Event.next_coming_date_or_start`) list of `limit`
        events matching `query` viewable by `user` and a list of related events
        viewable by `user` (i.e. it returns a tuple with two lists)
        
        - one or more dates in isoformat (yyyy-mm-dd) restrict the query to events with
          dates from the the lowest to the highest, or to one day if there is
          only one date
        - If there is no date in the query only future events are showed
        - Single words are looked in `title`, `tags`, `city`, `country` and
          `acronym` with or
        - Tags (#tag) restrict the query to events with these tags
        - Locations (@location) restrict the query to events having these
          location in `city` or `country`
        - Groups (!group) restrict the query to events of the group

          """
        queryset = Filter.matches_queryset(query, user)
        # sort the list touching the database. FIXME: use a field for each
        # event storing the unix time of the next coming event
        # if there are millions of events
        search_result = sorted(queryset, key=Event.next_coming_date_or_start)
        search_result = search_result[0:limit]
        # creates a list of maximal `limit` related events
        used_tags = Tag.objects.usage_for_queryset( queryset, counts=True )
        # note that according to the django-tagging documentation, counts refer
        # to all instances of the model Event, not only to the queryset
        # instances
        used_tags = sorted( used_tags, key = lambda t: t.count )
        used_tags.reverse()
        related_events = set()
        # takes the 5 more used tags and find related tags to them and its
        # events, then with 4, and so on until 100 events are found
        today = datetime.date.today()
        for nr_of_tags in [5,4,3,2,1]:
            if len( related_events ) >= limit:
                break
            related_tags = Tag.objects.related_for_model(
                    used_tags[ 0 : nr_of_tags ], Event, counts = True )
            related_tags = sorted( related_tags, key = lambda t: t.count )
            related_tags.reverse()
            for tag in related_tags:
                if len( related_events ) >= limit:
                    break
                events = TaggedItem.objects.get_by_model(Event, tag)
                for event in events:
                    if ( event.next_coming_date_or_start() >= today and
                            event.is_viewable_by_user( user ) and
                            event not in search_result ):
                        related_events.add(event)
                        # TODO: if the query has no tag restriction, what to
                        # do? include events with the same tags?
        # sort the related_events
        related_events = sorted( related_events,
                key=Event.next_coming_date_or_start )
        # take the first `limit` 
        return search_result, related_events[0:limit]

    def matches_count( self ): # {{{2
        """ returns the number of events which would be returned without
        `count` by `Filter.matches` """
        return Filter.matches_queryset( self.query, self.user ).count()

    @staticmethod
    def matches_queryset( query, user ): # {{{2
        """ returns a queryset without touching the database, see `Filter.matches` """
        # IMPORTANT: this code must be in accordance with
        # `Filter.matches_event`
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
        # TODO: implement it less restrictive, i.e. also showing later events
        # with only some of the specified tags
        queryset = Event.objects.all()
        # if no user get only public events
        if user is None or user.id is None:
            queryset = queryset.filter(public = True)
        # groups
        regex = re.compile('!(\w+)', UNICODE)
        for group_name in regex.findall(query):
            queryset = queryset.filter(calendar__group__name__iexact = group_name)
        # locations
        regex = re.compile('@(\w+)', UNICODE)
        for loc_name in regex.findall(query):
            queryset = queryset.filter(
                    Q( city__iexact = loc_name ) | Q( country__iexact = loc_name ) )
                    # TODO: use also translations of locations
        # tags
        regex = re.compile('#(\w+)', UNICODE)
        tags = regex.findall(query)
        if tags:
            queryset = TaggedItem.objects.get_intersection_by_model(
                    queryset, tags )
        # dates
        date_regex = re.compile('\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*', UNICODE)
        # FIXME: e.g. a2010-01-01 shouldn't work
        dates = date_regex.findall( query )
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
            query = date_regex.sub("", query)
        else:
            date = datetime.date.today()
            queryset = queryset.filter(
                    Q(start__gte = date) | Q(end__gte = date) |
                    Q(deadlines__deadline__gte = date) )
        # look for words
        regex = re.compile('([^!@#]\w+)', UNICODE)
        for word in regex.findall(query):
            queryset = queryset.filter(
                    Q(title__icontains = word) |
                    Q(tags__icontains = word) |
                    Q(city__iexact = word) |
                    Q(country__iexact = word) |
                    Q(acronym__iexact = word) )
        # TODO: add full indexing text on Event.description and comments. See
        # http://wiki.postgresql.org/wiki/Full_Text_Indexing_with_PostgreSQL
        # remove duplicates
        queryset = queryset.distinct()
        # filter events the user cannot see
        if user is not None and user.id is not None:
            queryset = queryset.filter( 
                    Q( user = user ) | 
                    Q( calendar__group__membership__user = user ) |
                    Q( public = True ) )
        return queryset

    @staticmethod
    def notify_users_when_wanted(event): # {{{2
        """ notifies users if `event` matches a filter of a user and the
        user wants to be notified for the matching filter and the user can see
        the event """
        if isinstance(event, Event):
            pass
        elif isinstance(event, int):
            event = Event.objects.get(pk = event)
        else:
            event = Event.objects.get(pk = int(event))
        # TODO: the next code iterate throw all users but this is not workable
        # for a big number of users: implement a special data structure which
        # saves filters and can look up fast filters matching an event
        users = User.objects.all()
        for user in users:
            if not event.is_viewable_by_user(user):
                continue
            user_filters = Filter.objects.filter( user = user ).filter(
                    email = True)
            for fil in user_filters:
                if fil.matches_event(event):
                    context = {
                        'name': user.username,
                        'event': event,
                        'filter': fil,
                        'site': settings.PROJECT_NAME, }
                    # TODO: create the subject from a text template
                    subject = _(u'filter match: ') + event.title
                    # TODO: use a preferred language setting for users to send
                    # emails to them in this language
                    message = render_to_string(
                            'mail/event_notice.txt', context )
                    from_email = settings.DEFAULT_FROM_EMAIL
                    if subject and message and from_email and user.email:
                        try:
                            send_mail(subject, message, from_email,
                                    [user.email,])
                        except BadHeaderError:
                            # TODO: do something meanfull
                            pass
                    break

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
    >>> user = User.objects.create(username = "user " + now)
    >>> membership = Membership.objects.create(group = group, user = user)
    >>> assert ( len(group.get_users()) == 1 )
    """
    # FIXME: groups only as lowerDeadlines case ascii (case insensitive).
    # Validate everywhere including save method.
    name = models.CharField( _( u'Name' ), max_length = 80, unique = True )
    description = models.TextField( _( u'Description' ) )
    members = models.ManyToManyField( User, through = 'Membership',
            verbose_name = _( u'Members' ) )
    events = models.ManyToManyField( Event, through = 'Calendar',
            verbose_name = _( u'Events' ) )
    creation_time = models.DateTimeField(
            _( u'Creation time' ), editable = False, auto_now_add = True )
    modification_time = models.DateTimeField( _( u'Modification time' ),
            editable = False, auto_now = True )

    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        ordering = ['name']
        verbose_name = _( u'Group' )
        verbose_name_plural = _( u'Groups' )

    def __unicode__( self ):
        return self.name

    @models.permalink
    def get_absolute_url( self ):
        "get internal URL of an event"
        return ( 'group_view', (), { 'group_id': self.id } )

    def is_member( self, user ):
        """ returns True if `user` is a member of the group, False otherwise
        """
        if isinstance(user, int):
            user = User.objects.get(id = user)
        elif isinstance(user, User):
            pass
        else:
            user = User.objects.get( id = int(user) )
        if Membership.objects.get( group = self, user = user ):
            return True
        else:
            return False

    def get_users( self ):
        """ returns a queryset (which can be used as a list) of ExtendedUsers
        members of the group """
        return ExtendedUser.objects.filter( membership__group = self )

    @staticmethod
    def is_user_in_group( user, group ):
        """ Returns True if `user` is in `group`, otherwise False.

        The parameters `user` and `group` can be an instance the classes User
        and Group or the id number.

        >>> from django.contrib.auth.models import User
        >>> from events.models import Event, Group, Membership
        >>> now = datetime.datetime.now().isoformat()
        >>> user1 = User.objects.create(username = "user1 " + now)
        >>> user2 = User.objects.create(username = "user2 " + now)
        >>> group1 = Group.objects.create(name="group1 " + now)
        >>> m = Membership.objects.create(user=user1, group=group1)
        >>> assert (Group.is_user_in_group(user1, group1))
        >>> assert (not Group.is_user_in_group(user2, group1))
        >>> assert (Group.is_user_in_group(user1.id, group1.id))
        >>> assert (not Group.is_user_in_group(user2.id, group1.id))
        """
        if isinstance(user, User):
            user_id = user.id
        elif isinstance(user, int):
            user_id = user
        elif isinstance(user, unicode) or isinstance(user, str):
            user_id = int(user)
        else:
            return False
        if isinstance(group, Group):
            group_id = group.id
        elif isinstance(group, int):
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

    @staticmethod
    def groups_of_user(user):
        """ Returns a list of groups the `user` is a member of.

        The parameter `user` can be an instance of User or the id number of a
        user.
        
        >>> from django.contrib.auth.models import User
        >>> from events.models import Event, Group, Membership
        >>> now = datetime.datetime.now().isoformat()
        >>> user1 = User.objects.create(username = "user1 " + now)
        >>> user2 = User.objects.create(username = "user2 " + now)
        >>> group12 = Group.objects.create(name="group12 " + now)
        >>> group2 = Group.objects.create(name="group2 " + now)
        >>> m1 = Membership.objects.create(user=user1, group=group12)
        >>> m2 = Membership.objects.create(user=user2, group=group12)
        >>> m3 = Membership.objects.create(user=user2, group=group2)
        >>> groups_of_user_2 = Group.groups_of_user(user2.id)
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
        elif isinstance(user, int):
            user = User.objects.get(id=user)
        elif isinstance(user, unicode) or isinstance(user, str):
            user = User.objects.get( id = int( user ) )
        else: raise TypeError(
                "'user' must be a User instance or an integer but it was " +
                str(user.__class__))
        return list(Group.objects.filter(membership__user=user))

    def get_coming_events(self, limit=5):
        """ Returns a list of maximal `limit` events with at least one date
        in the future (start, end or deadline). If `limit` is -1 it
        returns all

        """
        today = datetime.date.today()
        events = Event.objects.filter( Q(calendar__group = self) & (
                    Q(start__gte=today) | Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today) )).distinct()
        # next line touches the date base, but notice that the number of future
        # events of a group shouldn't be big
        if limit == -1:
            return sorted(events, key=Event.next_coming_date_or_start)
        else:
            return sorted(events, key=Event.next_coming_date_or_start)[0:limit]

    def get_coming_public_events(self, limit=5):
        """ Returns a list of maximal `limit` public events with at least one
        date in the future (start, end or deadline). If `limit` is -1 it
        returns all
        """
        today = datetime.date.today()
        events = Event.objects.filter(
                Q(public = True) & Q(calendar__group = self) & (
                    Q(start__gte=today) | Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today) )).distinct()
        # next line touches the date base, but notice that the number of future
        # events of a group shouldn't be big
        if limit == -1:
            return sorted(events, key=Event.next_coming_date_or_start)
        else:
            return sorted(events, key=Event.next_coming_date_or_start)[0:limit]

    def has_coming_events(self):
        """ returns True if the group has coming events (with `start`, `end` or
        a `deadline` of an event of the group in the future)
        """
        today = datetime.date.today()
        return Event.objects.filter( Q(calendar__group = self) & (
                    Q(start__gte=today) | Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today) )).count() > 0

    def has_coming_public_events(self):
        """ returns True if the group has coming public events (with `start`,
        `end` or a `deadline` of an event of the group in the future)
        """
        today = datetime.date.today()
        return Event.objects.filter(
                Q( public = True ) & Q( calendar__group = self ) & (
                    Q(start__gte=today) | Q(end__gte=today) |
                    Q(deadlines__deadline__gte=today) )).count() > 0

    @staticmethod
    def events_in_groups(groups, limit=5):
        """ Returns a dictionary whose keys are groups and its values are non
        empty lists of maximal `limit` events of the group with at least one
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

    @classmethod
    def groups_for_add_event( cls, user, event ):
        """ return groups for event to add.
        
        FIXME: what is this? check """
        if isinstance(event, Event):
            pass
        elif isinstance(event, int):
            event = Event.objects.get(pk = event)
        else:
            event = Event.objects.get(pk = int(event))
        if event.clone_of:
            event = event.clone_of
        groups = cls.objects.filter( members = user )
        groups = groups.exclude( events = event )
        groups = groups.exclude( events__in = event.get_clones() )
        return groups

class Membership( models.Model ): # {{{1
    """Relation between users and groups."""
    user = models.ForeignKey( 
            User,
            verbose_name = _( u'User' ),
            related_name = 'membership' )
    # the name 'groups' instead of mygroups is not possible because the default
    # User model in django already has a relation called 'groups'
    group = models.ForeignKey( 
            Group,
            verbose_name = _( u'Group' ),
            related_name = 'membership' )
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
    # TODO: save who added it
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        unique_together = ( "event", "group" )
        verbose_name = _( u'Calendar' )
        verbose_name_plural = _( u'Calendars' )


# Next code is an adaptation of some code in python-django-registration
SHA1_RE = re.compile( '^[a-f0-9]{40}$' )
class GroupInvitationManager( models.Manager ): # {{{1
    """
    Custom manager for the ``GroupInvitation`` model.

    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired Group Invitations.

    """
    def activate_invitation( self, activation_key ):
        """
        Validate an activation key and adds the corresponding
        ``User`` to the corresponding ``Group`` if valid.

        If the key is valid and has not expired, returns a dictionary
        with values ``host``, ``guest``, ``group`` after adding the
        user to the group.

        If the key is not valid or has expired, return ``False``.

        If the key is valid but the ``User`` is already in the group,
        return ``False``, but set it as administrator if the invitation
        set it but the user wasn't an administrator

        If the key is valid but the ``host`` is not an administrator of
        the group, return False.

        To prevent membership of a user who has been removed by a group
        administrator after his activation, the activation key is reset to the string
        ``ALREADY_ACTIVATED`` after successful activation.

        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search( activation_key ):
            try:
                invitation = self.get( activation_key = activation_key )
            except self.model.DoesNotExist:
                return False
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
            ``group`` will be the name of the gropu.

        """
        salt = hashlib.sha1( str( random.random() ) ).hexdigest()[:5]
        activation_key = hashlib.sha1( salt + guest.username ).hexdigest()
        self.create( 
                host = host, guest = guest, group = group,
                as_administrator = as_administrator,
                activation_key = activation_key )

        current_site = Site.objects.get_current()

        subject = render_to_string( 'groups/invitation_email_subject.txt',
                                   { 'site': current_site } )
        # Email subject *must not* contain newlines
        subject = ''.join( subject.splitlines() )

        message = render_to_string( 
                'groups/invitation_email.txt',
                { 'activation_key': activation_key,
                  'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                  'site': current_site,
                  'host': host.username,
                  'group': group.name, } )

        send_mail(
                subject, message, settings.DEFAULT_FROM_EMAIL, [guest.email] )


    def delete_expired_invitations( self ):
        """
        Remove expired instances of ``GroupInvitation``.

        Accounts to be deleted are identified by searching for
        instances of ``GroupInvitation`` with expired activation
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
            _( u'as administrator' ), default = False )
    activation_key = models.CharField( 
            _( u'activation key' ), max_length = 40 )

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
        Determine whether this ``GroupInvitation``'s activation
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
               ( self.guest.date_joined + \
                       expiration_date <= datetime.datetime.now() )
    # TODO: find out and explain here what this means:
    activation_key_expired.boolean = True


# TODO: add setting info to users. See the auth documentation because there is
# a method for adding fields to User. E.g.
#   - interesting locations
#   - interesting tags
#   - hidden: location and tags clicked before


#TODO: events comment model. Check for already available django comment module


# Was a Miernik idea but he doesn't remember what is the advantage of using a
# custom field for countries in the Event model:
# class CountryField(models.CharField):
#     def __init__(self, *args, **kwargs):
#         kwargs.setdefault('max_length', 2)
#         kwargs.setdefault('choices', COUNTRIES)
#         super(CountryField, self).__init__(*args, **kwargs)
#     def get_internal_type(self):
#         return "CharField"


# old code for parsing events as text using forms
#        event_data = {}
#        synonyms = Event.get_synonyms()
#        event_url_data_list = list()
#        event_deadline_data_list = list()
#        event_session_data_list = list()
#        event_groups_req_names_list = list() # list of group names
#        field_pattern = re.compile( 
#                r"^[^\s:]+[ \t]*:.*(?:\n(?:[ \t])+.+)*", re.MULTILINE )
#        parts_pattern = re.compile( 
#                r"^([^\t:]+[ \t]*)[ \t]*:[ \t]*(.*)((?:\n(?:[ \t])+.+)*)",
#                re.MULTILINE )
        # group 0 is the text before the colon
        # group 1 is the text after the colon
        # group 2 are all indented lines
#
#        for field_data in fields_data:
#            try:
#                parts = ( field_data[0], field_data[2], field_data[3] )
#                try:
#                    field_name = synonyms[parts[0].replace( '\n', '' )]
#                except KeyError:
#                    raise ValidationError( _( 
#                            "you used an invalid field name %s'" % \
#                            field_data[0] ) )
#                try:
#                    if parts[1] and parts[2]:
#                        # for mixed data after colon and in indented lines
#                        new_parts = ( parts[0],
#                                     '',
#                                     "%s%s" % parts[1:] )
#                        parts = new_parts
#                    if field_name == 'urls':
#                        #event_url_index = 0
#                        if not parts[1] == '':
#                            event_url_data = {}
#                            event_url_line_parts = \
#                                        filter( lambda x: x, \
#                                        parts[1].strip().replace( '\t', ' ' )\
#                                        .split( " " ) )
#                            if len( event_url_line_parts ) == 1:
#                                event_url_data['url_name'] = u'url'
#                            else:
#                                event_url_data['url_name'] = \
#                                ' '.join( event_url_line_parts[:-1] )
#                            event_url_data['url'] = \
#                            event_url_line_parts[-1].strip()
#                            event_url_data_list.append( event_url_data )
#                            #event_url_index += 1
#                        if not parts[2] == '':
#                            for event_url_line in parts[2].splitlines():
#                                if not event_url_line == '':
#                                    event_url_line_parts = \
#                                        filter( lambda x: x, \
#                                        event_url_line.strip().\
#                                        replace( '\t', ' ' )\
#                                        .split( " " ) )
#                                    event_url_data = {}
#                                    if len( event_url_line_parts ) == 1:
#                                        event_url_data['url_name'] = u'url'
#                                    else:
#                                        event_url_data['url_name'] = \
#                                        ' '.join( event_url_line_parts[:-1] )
#                                    event_url_data['url'] = \
#                                            event_url_line_parts[-1].strip()
#                                    event_url_data_list.\
#                                    append( event_url_data )
#                                    #event_url_index += 1
#
#                    # TODO: accept deadlines like:
#                    #       2010-02-10 Submission of invited session proposals
#                    elif field_name == 'deadlines':
#                        #event_deadline_index = 0
#                        if not parts[1] == '':
#                            event_deadline_data = {}
#                            event_deadline_line_parts = \
#                                        filter( lambda x: x, \
#                                        parts[1].strip().replace( '\t', ' ' )\
#                                        .split( " " ) )
#                            if len( event_deadline_line_parts ) == 1:
#                                event_deadline_data['deadline_name'] = \
#                                u'deadline'
#                            else:
#                                event_deadline_data['deadline_name'] = \
#                                ' '.join( event_deadline_line_parts[1:] )
#                            event_deadline_data['deadline'] = \
#                                        event_deadline_line_parts[0].strip()
#                            event_deadline_data_list.\
#                            append( event_deadline_data )
#                            #event_deadline_index += 1
#                        if not parts[2] == '':
#                            for event_deadline_line in parts[2].splitlines():
#                                if not event_deadline_line == '':
#                                    event_deadline_data = {}
#                                    event_deadline_line_parts = \
#                                            filter( lambda x: x, \
#                                            event_deadline_line.\
#                                            strip().replace( '\t', ' ' )\
#                                            .split( " " ) )
#                                    event_deadline_data['deadline_name'] = \
#                                    ' '.join( event_deadline_line_parts[1:] )\
#                                        .strip()
#                                    event_deadline_data['deadline'] = \
#                                        event_deadline_line_parts[0].strip()
#                                    event_deadline_data_list\
#                                    .append( event_deadline_data )
#                                    #event_deadline_index += 1
#
#                    elif field_name == 'sessions':
#                        #event_session_index = 0
#                        if not parts[1] == '':
#                            event_session_data = {}
#
#                            event_session_line_parts = \
#                                            filter( lambda x: x, \
#                                            parts[1].\
#                                            strip().replace( '\t', ' ' )\
#                                            .split( " " ) )
#                            if len( event_session_line_parts ) < 3:
#                                event_session_data['session_name'] = u'session'
#                            else:
#                                event_session_data['session_name'] = \
#                                    ' '.join( event_session_line_parts[2:] ).\
#                                    strip()
#                            event_session_data['session_date'] = \
#                                    event_session_line_parts[0].strip()
#                            event_session_str_times_parts = \
#                                    event_session_line_parts[1].split( "-", 1 )
#                            event_session_data['session_starttime'] = \
#                                    event_session_str_times_parts[0].strip()
#                            event_session_data['session_endtime'] = \
#                                    event_session_str_times_parts[1].strip()
#                            event_session_data_list.\
#                            append( event_session_data )
#                            #event_session_index += 1
#                        if not parts[2] == '':
#                            for event_session_line in parts[2].splitlines():
#                                if not event_session_line == '':
#                                    event_session_data = {}
#                                    event_session_line_parts = \
#                                            filter( lambda x: x, \
#                                            event_session_line.\
#                                            strip().replace( '\t', ' ' )\
#                                            .split( " " ) )
#                                    event_session_data['session_name'] = \
#                                    ' '.join( event_session_line_parts[2:] )\
#                                        .strip()
#                                    event_session_data['session_date'] = \
#                                            event_session_line_parts[0].strip()
#                                    event_session_str_times_parts = \
#                                            event_session_line_parts[1]\
#                                            .split( "-", 1 )
#                                    event_session_data['session_starttime'] = \
#                                    event_session_str_times_parts[0].strip()
#                                    event_session_data['session_endtime'] = \
#                                    event_session_str_times_parts[1].strip()
#                                    event_session_data_list\
#                                    .append( event_session_data )
#                                    #event_session_index += 1
#
#                    elif field_name == 'groups':
#                        event_groups_req_names_list = \
#                            [p for p in re.split( "( |\\\".*?\\\"|'.*?')", \
#                            parts[1] ) if p.strip()]
#
#                    elif field_name == 'description':
#                        event_data['description'] = field_data[1]
#                    elif field_name == 'country':
#                        country = parts[1]
#                        countries = [x[0] for x in COUNTRIES]
#                        if not country in countries:
#                            countries_dict = dict( [( x[1].lower(), x[0] ) \
#                                                    for x in COUNTRIES] )
#                            country = country.lower()
#                            if country in countries_dict:
#                                country = countries_dict[country]
#                            else:
#                                raise ValidationError( _( 
#                                "no '%s' country in countres list" % \
#                                parts[0] ) )
#                        event_data['country'] = country
#                    else:
#                        if not parts[2] == '':
#
#                            raise ValidationError( _( 
#                                "field '%s' doesn't accept subparts" % \
#                                parts[0] ) )
#                        if parts[0] == '':
#                            raise \
#                            ValidationError\
#                            ( _( "a left part of a colon is empty" ) )
#                        if not synonyms.has_key( parts[0] ):
#                            raise \
#                            ValidationError( _( "keyword %s unknown" % \
#                                                parts[0] ) )
#                        event_data[synonyms[parts[0]]] = parts[1]
#                except IndexError:
#                    raise \
#                    ValidationError( _( "Validation error in %s" % \
#                                        field_data[1] ) )
#            except ValidationError, error:
#                errors.append( error )
#        # at this moment we have event_data, event_url_data_list,
#        # event_deadline_data_list and event_session_data_list
#
#        if not errors:
#
#            from gridcalendar.events.forms import ( EventForm, EventUrlForm,
#                EventDeadlineForm, EventSessionForm )
#
#            try:
#
#                if ( event_id == None ):
#                    event_form = EventForm( event_data )
#                else:
#                    try:
#                        event = Event.objects.get( id = event_id )
#                    except Event.DoesNotExist:
#                        raise ValidationError( \
#                                    _( "event '%s' doesn't exist" % \
#                                       event_id ) )
#                    event_form = EventForm( event_data, instance = event )
#
#                if event_form.is_valid():
#                    event = event_form.save()
#                    final_event_id = event.id
#                else:
#                    raise \
#                    ValidationError( _( \
#                                "there is an error: %s" % \
#                                        event_form.errors ) )
#            except ValidationError, error:
#                errors.append( error )
#
#        # now we will create forms out of the lists of URLs, deadlines and
#        # sessions, and check if these forms are valid
#        if not errors:
#            event_url_data_list2 = list()
#            for event_url_data in event_url_data_list:
#                event_url_data['event'] = final_event_id
#                event_url_data_list2.append( event_url_data )
#            try:
#
#                for event_url_data in event_url_data_list2:
#                    try:
#                        event_url = EventUrl.objects.get( 
#                            Q( event = event_url_data['event'] ),
#                            Q( url_name__exact = event_url_data['url_name'] ) )
#                        event_url_form = \
#                                EventUrlForm( event_url_data, instance = \
#                                              event_url )
#                    except EventUrl.DoesNotExist:
#                        event_url_form = EventUrlForm( event_url_data )
#                    if not event_url_form.is_valid():
#                        if ( event_id == None ):
#                            Event.objects.get( id = final_event_id ).delete()
#                        raise ValidationError( _( 
#                        "There is an error in the input data for URLs: %s" %
#                            event_url_form.errors ) )
#            except ValidationError, error:
#                errors.append( error )
#
#        if not errors:
#            event_deadline_data_list2 = list()
#            for event_deadline_data in event_deadline_data_list:
#                event_deadline_data['event'] = final_event_id
#                event_deadline_data_list2.append( event_deadline_data )
#            try:
#                for event_deadline_data in event_deadline_data_list2:
#                    try:
#                        event_deadline = EventDeadline.objects.get( 
#                                Q( event = event_deadline_data['event'] ),
#                                Q( deadline_name__exact = \
#                                    event_deadline_data['deadline_name'] ) )
#                        event_deadline_form = EventDeadlineForm( 
#                                event_deadline_data, instance = \
#                                event_deadline )
#                    except EventDeadline.DoesNotExist:
#                        event_deadline_form = \
#                        EventDeadlineForm( event_deadline_data )
#                    if not event_deadline_form.is_valid():
#                        if ( event_id == None ):
#                            Event.objects.get( id = final_event_id ).delete()
#                        raise ValidationError( _( 
#                    "There is an error in the input data in the deadlines: %s"
#                            % event_deadline_form.errors ) )
#
#            except ValidationError, error:
#                errors.append( error )
#
#        if not errors:
#
#            event_session_data_list2 = list()
#            for event_session_data in event_session_data_list:
#                event_session_data['event'] = final_event_id
#                event_session_data_list2.append( event_session_data )
#            try:
#                for event_session_data in event_session_data_list2:
#                    try:
#                        event_session = EventSession.objects.get( 
#                                Q( event = event_session_data['event'] ),
#                                Q( session_name__exact = \
#                                        event_session_data['session_name'] ) )
#                        event_session_form = EventSessionForm( 
#                                event_session_data, instance = event_session )
#                    except EventSession.DoesNotExist:
#                        event_session_form = \
#                        EventSessionForm( event_session_data )
#                    if not event_session_form.is_valid():
#                        if ( event_id == None ):
#                            Event.objects.get( id = final_event_id ).delete()
#                        raise ValidationError( _( 
#                    "There is an error in the input data in the sessions: %s" %
#                            event_session_form.errors ) )
#            except ValidationError, error:
#                errors.append( error )
#
#
#        if not errors:
#
#            if ( event_id == None ):
#                pass
#            else:
#                EventUrl.objects.filter( event = event_id ).delete()
#                EventDeadline.objects.filter( event = event_id ).delete()
#                EventSession.objects.filter( event = event_id ).delete()
#                event_form.save()
#
#            for event_url_data in event_url_data_list2:
#                event_url_form = EventUrlForm( event_url_data )
#                event_url_form.save()
#
#            for event_deadline_data in event_deadline_data_list2:
#                event_deadline_form = EventDeadlineForm( event_deadline_data )
#                event_deadline_form.save()
#
#            for event_session_data in event_session_data_list2:
#                event_session_form = EventSessionForm( event_session_data )
#                event_session_form.save()
#
#            if event_id:
#                event_groups_cur_id_list = event.groups_id_list()
#            else:
#                event_groups_cur_id_list = list()
#            event_groups_req_id_list = list()
#            try:
#                for group_name_quoted in event_groups_req_names_list:
#                    group_name = group_name_quoted.strip( '"' )
#                    try:
#                        group = Group.objects.get( name = group_name )
#                    except Group.DoesNotExist:
#                        raise ValidationError( _( 
#                        "Group: %(group_name)s does not exist, enter a valid \
#                        group name." % {"group_name":group_name} ) )
#                    event_groups_req_id_list.append( group.id )
#                    if group.id not in event_groups_cur_id_list:
#                        if user_id is None or not \
#                        group.is_user_in_group( user_id, group.id ):
#                            raise ValidationError( _( 
#                            "You are not a member of group: %(group_name)s so \
#                            you can not add any event to it." %
#                            {"group_name":group.name} ) )
#                        event.add_to_group( group.id )
#                for group_id in event_groups_cur_id_list:
#                    if group_id not in event_groups_req_id_list:
#                        if user_id is None or \
#                                not group.is_user_in_group( user_id, group_id ):
#                            group = Group.objects.get( id = group_id )
#                            raise ValidationError( _( "You are not a \
#                            member of group: %(group_name)s so you can not \
#                            remove an event from it." % \
#                            {"group_name":group.name} ) )
#                        event.remove_from_group( group_id )
#            except Exception, error:
#                errors.append( error )
#        if errors:
#            return errors
#        else:
#            return event

