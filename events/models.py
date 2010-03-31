#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009, 2010 Iván F. Villanueva B. <ivan ät gridmind.org>
#
# This file is part of GridCalendar.
# 
# GridCalendar is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################


import datetime
import random
import re
import hashlib

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.forms import ValidationError
from django.forms.models import inlineformset_factory
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from tagging.models import Tag
from tagging.fields import TagField
from tagging import register

COUNTRIES = (
    ('AF', _(u'Afghanistan')),
    ('AX', _(u'Åland Islands')),
    ('AL', _(u'Albania')),
    ('DZ', _(u'Algeria')),
    ('AS', _(u'American Samoa')),
    ('AD', _(u'Andorra')),
    ('AO', _(u'Angola')),
    ('AI', _(u'Anguilla')),
    ('AQ', _(u'Antarctica')),
    ('AG', _(u'Antigua and Barbuda')),
    ('AR', _(u'Argentina')),
    ('AM', _(u'Armenia')),
    ('AW', _(u'Aruba')),
    ('AU', _(u'Australia')),
    ('AT', _(u'Austria')),
    ('AZ', _(u'Azerbaijan')),
    ('BS', _(u'Bahamas')),
    ('BH', _(u'Bahrain')),
    ('BD', _(u'Bangladesh')),
    ('BB', _(u'Barbados')),
    ('BY', _(u'Belarus')),
    ('BE', _(u'Belgium')),
    ('BZ', _(u'Belize')),
    ('BJ', _(u'Benin')),
    ('BM', _(u'Bermuda')),
    ('BT', _(u'Bhutan')),
    ('BO', _(u'Bolivia, Plurinational State of')),
    ('BA', _(u'Bosnia and Herzegovina')),
    ('BW', _(u'Botswana')),
    ('BV', _(u'Bouvet Island')),
    ('BR', _(u'Brazil')),
    ('IO', _(u'British Indian Ocean Territory')),
    ('BN', _(u'Brunei Darussalam')),
    ('BG', _(u'Bulgaria')),
    ('BF', _(u'Burkina Faso')),
    ('BI', _(u'Burundi')),
    ('KH', _(u'Cambodia')),
    ('CM', _(u'Cameroon')),
    ('CA', _(u'Canada')),
    ('CV', _(u'Cape Verde')),
    ('KY', _(u'Cayman Islands')),
    ('CF', _(u'Central African Republic')),
    ('TD', _(u'Chad')),
    ('CL', _(u'Chile')),
    ('CN', _(u'China')),
    ('CX', _(u'Christmas Island')),
    ('CC', _(u'Cocos (Keeling) Islands')),
    ('CO', _(u'Colombia')),
    ('KM', _(u'Comoros')),
    ('CG', _(u'Congo')),
    ('CD', _(u'Congo, the Democratic Republic of the')),
    ('CK', _(u'Cook Islands')),
    ('CR', _(u'Costa Rica')),
    ('CI', _(u'Côte d\'Ivoire')),
    ('HR', _(u'Croatia')),
    ('CU', _(u'Cuba')),
    ('CY', _(u'Cyprus')),
    ('CZ', _(u'Czech Republic')),
    ('DK', _(u'Denmark')),
    ('DJ', _(u'Djibouti')),
    ('DM', _(u'Dominica')),
    ('DO', _(u'Dominican Republic')),
    ('EC', _(u'Ecuador')),
    ('EG', _(u'Egypt')),
    ('SV', _(u'El Salvador')),
    ('GQ', _(u'Equatorial Guinea')),
    ('ER', _(u'Eritrea')),
    ('EE', _(u'Estonia')),
    ('ET', _(u'Ethiopia')),
    ('FK', _(u'Falkland Islands (Malvinas)')),
    ('FO', _(u'Faroe Islands')),
    ('FJ', _(u'Fiji')),
    ('FI', _(u'Finland')),
    ('FR', _(u'France')),
    ('GF', _(u'French Guiana')),
    ('PF', _(u'French Polynesia')),
    ('TF', _(u'French Southern Territories')),
    ('GA', _(u'Gabon')),
    ('GM', _(u'Gambia')),
    ('GE', _(u'Georgia')),
    ('DE', _(u'Germany')),
    ('GH', _(u'Ghana')),
    ('GI', _(u'Gibraltar')),
    ('GR', _(u'Greece')),
    ('GL', _(u'Greenland')),
    ('GD', _(u'Grenada')),
    ('GP', _(u'Guadeloupe')),
    ('GU', _(u'Guam')),
    ('GT', _(u'Guatemala')),
    ('GG', _(u'Guernsey')),
    ('GN', _(u'Guinea')),
    ('GW', _(u'Guinea-Bissau')),
    ('GY', _(u'Guyana')),
    ('HT', _(u'Haiti')),
    ('HM', _(u'Heard Island and McDonald Islands')),
    ('VA', _(u'Holy See (Vatican City State)')),
    ('HN', _(u'Honduras')),
    ('HK', _(u'Hong Kong')),
    ('HU', _(u'Hungary')),
    ('IS', _(u'Iceland')),
    ('IN', _(u'India')),
    ('ID', _(u'Indonesia')),
    ('IR', _(u'Iran, Islamic Republic of')),
    ('IQ', _(u'Iraq')),
    ('IE', _(u'Ireland')),
    ('IM', _(u'Isle of Man')),
    ('IL', _(u'Israel')),
    ('IT', _(u'Italy')),
    ('JM', _(u'Jamaica')),
    ('JP', _(u'Japan')),
    ('JE', _(u'Jersey')),
    ('JO', _(u'Jordan')),
    ('KZ', _(u'Kazakhstan')),
    ('KE', _(u'Kenya')),
    ('KI', _(u'Kiribati')),
    ('KP', _(u'Korea, Democratic People\'s Republic of')),
    ('KR', _(u'Korea, Republic of')),
    ('KW', _(u'Kuwait')),
    ('KG', _(u'Kyrgyzstan')),
    ('LA', _(u'Lao People\'s Democratic Republic')),
    ('LV', _(u'Latvia')),
    ('LB', _(u'Lebanon')),
    ('LS', _(u'Lesotho')),
    ('LR', _(u'Liberia')),
    ('LY', _(u'Libyan Arab Jamahiriya')),
    ('LI', _(u'Liechtenstein')),
    ('LT', _(u'Lithuania')),
    ('LU', _(u'Luxembourg')),
    ('MO', _(u'Macao')),
    ('MK', _(u'Macedonia, the former Yugoslav Republic of')),
    ('MG', _(u'Madagascar')),
    ('MW', _(u'Malawi')),
    ('MY', _(u'Malaysia')),
    ('MV', _(u'Maldives')),
    ('ML', _(u'Mali')),
    ('MT', _(u'Malta')),
    ('MH', _(u'Marshall Islands')),
    ('MQ', _(u'Martinique')),
    ('MR', _(u'Mauritania')),
    ('MU', _(u'Mauritius')),
    ('YT', _(u'Mayotte')),
    ('MX', _(u'Mexico')),
    ('FM', _(u'Micronesia, Federated States of')),
    ('MD', _(u'Moldova, Republic of')),
    ('MC', _(u'Monaco')),
    ('MN', _(u'Mongolia')),
    ('ME', _(u'Montenegro')),
    ('MS', _(u'Montserrat')),
    ('MA', _(u'Morocco')),
    ('MZ', _(u'Mozambique')),
    ('MM', _(u'Myanmar')),
    ('NA', _(u'Namibia')),
    ('NR', _(u'Nauru')),
    ('NP', _(u'Nepal')),
    ('NL', _(u'Netherlands')),
    ('AN', _(u'Netherlands Antilles')),
    ('NC', _(u'New Caledonia')),
    ('NZ', _(u'New Zealand')),
    ('NI', _(u'Nicaragua')),
    ('NE', _(u'Niger')),
    ('NG', _(u'Nigeria')),
    ('NU', _(u'Niue')),
    ('NF', _(u'Norfolk Island')),
    ('MP', _(u'Northern Mariana Islands')),
    ('NO', _(u'Norway')),
    ('OM', _(u'Oman')),
    ('PK', _(u'Pakistan')),
    ('PW', _(u'Palau')),
    ('PS', _(u'Palestinian Territory, Occupied')),
    ('PA', _(u'Panama')),
    ('PG', _(u'Papua New Guinea')),
    ('PY', _(u'Paraguay')),
    ('PE', _(u'Peru')),
    ('PH', _(u'Philippines')),
    ('PN', _(u'Pitcairn')),
    ('PL', _(u'Poland')),
    ('PT', _(u'Portugal')),
    ('PR', _(u'Puerto Rico')),
    ('QA', _(u'Qatar')),
    ('RE', _(u'Réunion')),
    ('RO', _(u'Romania')),
    ('RU', _(u'Russian Federation')),
    ('RW', _(u'Rwanda')),
    ('BL', _(u'Saint Barthélemy')),
    ('SH', _(u'Saint Helena')),
    ('KN', _(u'Saint Kitts and Nevis')),
    ('LC', _(u'Saint Lucia')),
    ('MF', _(u'Saint Martin (French part)')),
    ('PM', _(u'Saint Pierre and Miquelon')),
    ('VC', _(u'Saint Vincent and the Grenadines')),
    ('WS', _(u'Samoa')),
    ('SM', _(u'San Marino')),
    ('ST', _(u'Sao Tome and Principe')),
    ('SA', _(u'Saudi Arabia')),
    ('SN', _(u'Senegal')),
    ('RS', _(u'Serbia')),
    ('SC', _(u'Seychelles')),
    ('SL', _(u'Sierra Leone')),
    ('SG', _(u'Singapore')),
    ('SK', _(u'Slovakia')),
    ('SI', _(u'Slovenia')),
    ('SB', _(u'Solomon Islands')),
    ('SO', _(u'Somalia')),
    ('ZA', _(u'South Africa')),
    ('GS', _(u'South Georgia and the South Sandwich Islands')),
    ('ES', _(u'Spain')),
    ('LK', _(u'Sri Lanka')),
    ('SD', _(u'Sudan')),
    ('SR', _(u'Suriname')),
    ('SJ', _(u'Svalbard and Jan Mayen')),
    ('SZ', _(u'Swaziland')),
    ('SE', _(u'Sweden')),
    ('CH', _(u'Switzerland')),
    ('SY', _(u'Syrian Arab Republic')),
    ('TW', _(u'Taiwan, Province of China')),
    ('TJ', _(u'Tajikistan')),
    ('TZ', _(u'Tanzania, United Republic of')),
    ('TH', _(u'Thailand')),
    ('TL', _(u'Timor-Leste')),
    ('TG', _(u'Togo')),
    ('TK', _(u'Tokelau')),
    ('TO', _(u'Tonga')),
    ('TT', _(u'Trinidad and Tobago')),
    ('TN', _(u'Tunisia')),
    ('TR', _(u'Turkey')),
    ('TM', _(u'Turkmenistan')),
    ('TC', _(u'Turks and Caicos Islands')),
    ('TV', _(u'Tuvalu')),
    ('UG', _(u'Uganda')),
    ('UA', _(u'Ukraine')),
    ('AE', _(u'United Arab Emirates')),
    ('GB', _(u'United Kingdom')),
    ('US', _(u'United States')),
    ('UM', _(u'United States Minor Outlying Islands')),
    ('UY', _(u'Uruguay')),
    ('UZ', _(u'Uzbekistan')),
    ('VU', _(u'Vanuatu')),
    ('VE', _(u'Venezuela, Bolivarian Republic of')),
    ('VN', _(u'Viet Nam')),
    ('VG', _(u'Virgin Islands, British')),
    ('VI', _(u'Virgin Islands, U.S.')),
    ('WF', _(u'Wallis and Futuna')),
    ('EH', _(u'Western Sahara')),
    ('YE', _(u'Yemen')),
    ('ZM', _(u'Zambia')),
    ('ZW', _(u'Zimbabwe')),
)

class Event(models.Model):
    """ Event model. """
    user = models.ForeignKey(User, editable=False, related_name="owner",
            blank=True, null=True, verbose_name=_(u'User'))
    """The user who created the event or null if AnonymousUser"""
    creation_time = models.DateTimeField(_(u'Creation time'), editable=False,
            auto_now_add=True)
    """Time stamp for event creation"""
    modification_time = models.DateTimeField(_(u'Modification time'),
            editable=False, auto_now=True)
    """Time stamp for event modification"""
    acronym = models.CharField(_(u'Acronym'), max_length=20, blank=True,
            null=True, help_text=_(u'Example: 26C3'))
    title = models.CharField(_(u'Title'), max_length=200, blank=False,
            help_text=_(u'Example: Demostration in Munich against software \
                patents organised by the German association FFII e.V.'))
    start = models.DateField(_(u'Start'), blank=False, help_text=_("Examples \
            of valid dates: '2006-10-25' '10/25/2006' '10/25/06' 'Oct 25 \
            2006' 'Oct 25, 2006' '25 Oct 2006' '25 Oct, 2006' \
            'October 25 2006' 'October 25, 2006' '25 October 2006' '25 \
            October, 2006'"))
    end = models.DateField(_(u'End'), null=True, blank=True)
    tags = TagField(_(u'Tags'), blank=True, null=True, help_text=_(u"Tags are \
        case in-sensitive. Only letters (these can be international, like: \
        αöł), digits and hyphens (-) are allowed. Tags are separated with \
        spaces."))
    public = models.BooleanField(_(u'Public'), default=True, help_text=_("A \
        public event can be seen and edited by anyone, otherwise only by the \
        members of selected groups"))
    country = models.CharField(_(u'Country'), blank=True, null=True,
            max_length=2, choices=COUNTRIES)
    city = models.CharField(_(u'City'), blank=True, null=True, max_length=50)
    postcode = models.CharField(_(u'Postcode'), blank=True, null=True,
            max_length=16)
    address = models.CharField(_(u'Street address'), blank=True, null=True,
            max_length=100)
    latitude = models.FloatField(_(u'Latitude'), blank=True, null=True,
            help_text=_("In decimal degrees, not \
            degrees/minutes/seconds. Prefix with \"-\" for South, no sign for \
            North."))
    longitude = models.FloatField(_(u'Longitude'), blank=True, null=True,
            help_text=_("In decimal degrees, not \
                degrees/minutes/seconds. Prefix with \"-\" for West, no sign \
                for East."))
    timezone = models.SmallIntegerField(_(u'Timezone'), blank=True, null=True,
            help_text=_("Minutes relative to UTC (e.g. -60 means UTC-1"))
    description = models.TextField(_(u'Description'), blank=True, null=True)
    # the relation event-group is now handle in group
    # groups = models.ManyToManyField(Group, blank=True, null=True,
    # help_text=_("Groups to be notified and allowed to see it if not public"))

    class Meta:
        ordering = ['start']
        verbose_name = _(u'Event')
        verbose_name_plural = _(u'Events')

    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)

    def get_tags(self):
        return Tag.objects.get_for_object(self)

    def __unicode__(self):
        return self.start.isoformat() + " : " + self.title

    @models.permalink
    def get_absolute_url(self):
        #return '/e/show/' + str(self.id) + '/'
        #return (reverse('event_show', kwargs={'event_id': str(self.id)}))
        return ('event_show', (), { 'event_id': self.id })

    def save(self, *args, **kwargs):
        """ Call the real 'save' function after some assertions. """
        # It is not allowed to have a non-public event without owner:
        assert not ((self.public == False) and (self.user == None))
        # It is not allowed to modify the 'public' field:
        assert ((self.pk == None) # true when it is a new event
                or (self.public == Event.objects.get(pk=self.pk).public))
        super(Event, self).save(*args, **kwargs) # Call the "real" save() method.


    def as_text(self):
        """ Returns a multiline string representation of the event."""
        # TODO: add a test here to create an event as a text with the output of
        # this function
        to_return = ""
        # TODO: have a constant sort order
        for keyword in set(self.get_synonyms().values()):
            if keyword == 'title':
                to_return += keyword + ": " + unicode(self.title) + "\n"
            elif keyword == 'start':
                to_return += keyword + ": " + self.start.strftime("%Y-%m-%d") + "\n"
            elif keyword == 'end' and self.end:
                to_return += keyword + ": " + self.end.strftime("%Y-%m-%d") + "\n"
            elif keyword == 'country' and self.country:
                to_return += keyword + ": " + unicode(self.country) + "\n"
            elif keyword == 'timezone' and self.timezone:
                to_return += keyword + ": " + unicode(self.timezone) + "\n"
            elif keyword == 'latitude' and self.latitude:
                to_return += keyword + ": " + unicode(self.latitude) + "\n"
            elif keyword == 'longitude' and self.longitude:
                to_return += keyword + ": " + unicode(self.longitude) + "\n"
            elif keyword == 'acronym' and self.acronym:
                to_return += keyword + ": " + unicode(self.acronym) + "\n"
            elif keyword == 'tags' and self.tags:
                to_return += keyword + ": " + unicode(self.tags) + "\n"
            elif keyword == 'public' and self.public:
                to_return += keyword + ": " + unicode(self.public) + "\n"
            elif keyword == 'address' and self.address:
                to_return += keyword + ": " + unicode(self.address) + "\n"
            elif keyword == 'city' and self.city:
                to_return += keyword + ": " + unicode(self.city) + "\n"
            elif keyword == 'code' and self.code:
                to_return += keyword + ": " + unicode(self.code) + "\n"
            elif keyword == 'urls' and self.urls:
                urls = EventUrl.objects.filter(event=self.id)
                if len(urls) > 0:
                    to_return += "urls:\n"
                    for url in urls:
                        to_return += "    " + url.url_name + ': ' + url.url + "\n"
            elif keyword == 'deadlines' and self.deadlines:
                deadlines = EventDeadline.objects.filter(event=self.id)
                if len(deadlines) > 0:
                    to_return += "deadlines:\n"
                    for deadline in deadlines:
                        to_return += "".join([
                                "    ",
                                deadline.deadline_name,
                                ': ',
                                unicode(deadline.deadline),
                                "\n",
                                ])
            elif keyword == 'sessions' and self.sessions:
                time_sessions = EventSession.objects.filter(event=self.id)
                if len(time_sessions) > 0:
                    to_return += "sessions:"
                    for time_session in time_sessions:
                        if time_session.session_name == 'session':
                            to_return = "".join((to_return, " ",
                                time_session.session_date.strftime("%Y-%m-%d"), ": ",
                                time_session.session_starttime.strftime("%H:%M"), "-",
                                time_session.session_endtime.strftime("%H:%M")))
                    to_return += "\n"
                    for time_session in time_sessions:
                        if not time_session.session_name == 'session':
                            to_return = "".join((to_return, "    ",
                                time_session.session_name, ": ",
                                time_session.session_date.strftime("%Y-%m-%d"), ": ",
                                time_session.session_starttime.strftime("%H:%M"), "-",
                                time_session.session_endtime.strftime("%H:%M"), '\n'))
            elif keyword == 'groups' and self.event_in_groups:
                calendars = Calendar.objects.filter(event=self.id)
                if len(calendars) > 0:
                    to_return += keyword + ":"
                    for calendar in calendars:
                        to_return += ' "' + str(calendar.group.name) + '"'
                    to_return += '\n'
            elif keyword == 'description' and self.description:
                to_return += keyword + ": " + unicode(self.description) + "\n"
                # FIXME: support multiline descriptions
        return to_return

    @staticmethod
    def parse_text(input_text_in, event_id=None, user_id=None):
        """It parses a text and saves it as a single event in the data base.

        It raises a ValidationError if there is an error.

        A text to be parsed as an event is of the form:
            title: a title
            tags: tag1 tag2 tag3
            start: 2020-01-30
            ...

        There are synonyms for the names of the field like 't' for 'title'. See
        get_synonyms()

        The text for the field 'urls' is of the form:
            urls: web_url
                name1: name1_url
                name2: name2_url
                ...
        The idented lines are optional. If web_url is present, it will be saved
        with the url_name 'web'

        The text for the field 'deadlines' is of the form:
            deadlines: deadline_date
                deadline1_name: deadline1_date
                deadline2_name: deadline2_date
                ...
        The idented lines are optional. If deadline_date is present, it will be saved
        with the deadline_name 'deadline'

        The text for the field 'sessions' is of the form:
            sessions: session_date session_starttime session_endtime
                session1_name: session1_date: session1_starttime-session1_endtime
                session2_name: session2_date: session2_starttime-session2_endtime
                ...
        The idented lines are optional. If session_date is present, it will be saved
        with the session_name 'session'

        The text for the field 'groups' is of the form:
            groups: group1 group2 ...
        """
        # TODO: allow to put comments on events by email
        event_data = {}
        # separate events
        # get fields
        field_pattern = re.compile(
                r"^[^ \t:]+[ \t]*:.*(?:\n(?:[ \t])+.+)*", re.MULTILINE)
        parts_pattern = re.compile(
                r"^([^ \t:]+[ \t]*)[ \t]*:[ \t]*(.*)((?:\n(?:[ \t])+.+)*)", re.MULTILINE)
        # group 0 is the text before the colon
        # group 1 is the text after the colon
        # group 2 are all indented lines
        synonyms = Event.get_synonyms()

        # MacOS uses \r, and Windows uses \r\n - convert it all to Unix \n
        input_text = input_text_in.replace('\r\n', '\n').replace('\r', '\n')

        event_url_data_list = list()
        event_deadline_data_list = list()
        event_session_data_list = list()

        for field_text in field_pattern.findall(input_text):
            parts = parts_pattern.match(field_text).groups()
            try:
                field_name = synonyms[parts[0]]
            except KeyError: raise ValidationError(_(
                        "you used an invalid field name in '%s'" % field_text))

            if field_name == 'urls':
                event_url_index = 0
                if not parts[1] == '':
                    event_url_data = {}
                    event_url_data['url_name'] = u'web'
                    event_url_data['url'] = parts[1].strip()
                    event_url_data_list.append(event_url_data)
                    event_url_index += 1
                if not parts[2] == '':
                    for event_url_line in parts[2].splitlines():
                        if not event_url_line == '':
                            event_url_line_parts = event_url_line.split(":", 1)
                            event_url_data = {}
                            event_url_data['url_name'] = event_url_line_parts[0].strip()
                            event_url_data['url'] = event_url_line_parts[1].strip()
                            event_url_data_list.append(event_url_data)
                            event_url_index += 1

            elif field_name == 'deadlines':
                event_deadline_index = 0
                if not parts[1] == '':
                    event_deadline_data = {}
                    event_deadline_data['deadline_name'] = u'deadline'
                    event_deadline_data['deadline'] = parts[1].strip()
                    event_deadline_data_list.append(event_deadline_data)
                    event_deadline_index += 1
                if not parts[2] == '':
                    for event_deadline_line in parts[2].splitlines():
                        if not event_deadline_line == '':
                            event_deadline_data = {}
                            event_deadline_line_parts = event_deadline_line.split(":", 1)
                            event_deadline_data['deadline_name'] = event_deadline_line_parts[0].strip()
                            event_deadline_data['deadline'] = event_deadline_line_parts[1].strip()
                            event_deadline_data_list.append(event_deadline_data)
                            event_deadline_index += 1

            elif field_name == 'sessions':
                event_session_index = 0
                if not parts[1] == '':
                    event_session_data = {}
                    event_session_data['session_name'] = u'session'
                    event_session_str_parts = parts[1].split(":", 1)
                    event_session_data['session_date'] = event_session_str_parts[0].strip()
                    event_session_str_times_parts = event_session_str_parts[1].split("-", 1)
                    event_session_data['session_starttime'] = event_session_str_times_parts[0].strip()
                    event_session_data['session_endtime'] = event_session_str_times_parts[1].strip()
                    event_session_data_list.append(event_session_data)
                    event_session_index += 1
                if not parts[2] == '':
                    for event_session_line in parts[2].splitlines():
                        if not event_session_line == '':
                            event_session_data = {}
                            event_session_line_parts = event_session_line.split(":", 1)
                            event_session_data['session_name'] = event_session_line_parts[0].strip()
                            event_session_str_parts = event_session_line_parts[1].split(":", 1)
                            event_session_data['session_date'] = event_session_str_parts[0].strip()
                            event_session_str_times_parts = event_session_str_parts[1].split("-", 1)
                            event_session_data['session_starttime'] = event_session_str_times_parts[0].strip()
                            event_session_data['session_endtime'] = event_session_str_times_parts[1].strip()
                            event_session_data_list.append(event_session_data)
                            event_session_index += 1

            elif field_name == 'groups':
                event_groups_req_names_list = [p for p in re.split("( |\\\".*?\\\"|'.*?')", parts[1]) if p.strip()]

            else:
                if not parts[2] == '': raise ValidationError(_(
                        "field '%s' doesn't accept subparts" % parts[1]))
                if parts[0] == '': raise ValidationError(_(
                        "a left part of a colon is empty"))
                if not synonyms.has_key(parts[0]): raise ValidationError(_(
                        "keyword %s unknown" % parts[0]))
                event_data[synonyms[parts[0]]] = parts[1]

        event_groups_req_names_list = list() # list of group names
        if (event_id == None):
            pass
            # FIXME
        else:
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                raise ValidationError(_("event '%s' doesn't exist" % event_id))
            event_groups_cur_id_list = event.is_in_groups_id_list()
            event_groups_req_id_list = list()
            for group_name_quoted in event_groups_req_names_list:
                group_name = group_name_quoted.strip('"')
                g = Group.objects.get(name=group_name)
                event_groups_req_id_list.append(g.id)
                if g.id not in event_groups_cur_id_list:
                    if user_id is None or not g.is_user_in_group(user_id, g.id):
                        raise ValidationError(_(
                            "You are not a member of group: %s so you can not add any event to it." % g.name))
                    event.add_to_group(g.id)
            for group_id in event_groups_cur_id_list:
                if group_id not in event_groups_req_id_list:
                    if user_id is None or not g.is_user_in_group(user_id, group_id):
                        g = Group.objects.get(id=group_id)
                        raise ValidationError(_(
                            "You are not a member of group: %s so you can not remove an event from it." % g.name))
                    event.remove_from_group(group_id)

        # at this moment we have event_data, event_url_data_list, event_deadline_data_list and event_session_data_list

        from gridcalendar.events.forms import EventForm, EventUrlForm, EventDeadlineForm, EventSessionForm
        if (event_id == None):
            event_form = EventForm(event_data)
            event = event_form.save()
            final_event_id = event.id
        else:
            event_form = EventForm(event_data, instance=event)
            final_event_id = event_id

        if not event_form.is_valid():
            raise ValidationError(_("there is an error in the input data: %s" % event_form.errors))

        # now we will add the event ID's to the lists of dictionaries

        event_url_data_list2 = list()
        for event_url_data in event_url_data_list:
            event_url_data['event'] = final_event_id
            event_url_data_list2.append(event_url_data)

        event_deadline_data_list2 = list()
        for event_deadline_data in event_deadline_data_list:
            event_deadline_data['event'] = final_event_id
            event_deadline_data_list2.append(event_deadline_data)

        event_session_data_list2 = list()
        for event_session_data in event_session_data_list:
            event_session_data['event'] = final_event_id
            event_session_data_list2.append(event_session_data)

        # now we will create forms out of the lists of URLs, deadlines and sessions, and check if these forms are valid

        for event_url_data in event_url_data_list2:
            try:
                event_url = EventUrl.objects.get(Q(event=event_url_data['event']), Q(url_name__exact=event_url_data['url_name']))
                event_url_form = EventUrlForm(event_url_data, instance=event_url)
            except EventUrl.DoesNotExist:
                event_url_form = EventUrlForm(event_url_data)
            if not event_url_form.is_valid():
                if (event_id == None):
                    Event.objects.get(id=final_event_id).delete()
                raise ValidationError(_("There is an error in the input data in the URLs: %s" % event_url_form.errors))

        for event_deadline_data in event_deadline_data_list2:
            try:
                event_deadline = EventDeadline.objects.get(Q(event=event_deadline_data['event']), Q(deadline_name__exact=event_deadline_data['deadline_name']))
                event_deadline_form = EventDeadlineForm(event_deadline_data, instance=event_deadline)
            except EventDeadline.DoesNotExist:
                event_deadline_form = EventDeadlineForm(event_deadline_data)
            if not event_deadline_form.is_valid():
                if (event_id == None):
                    Event.objects.get(id=final_event_id).delete()
                raise ValidationError(_("There is an error in the input data in the deadlines: %s" % event_deadline_form.errors))

        for event_session_data in event_session_data_list2:
            try:
                event_session = EventSession.objects.get(Q(event=event_session_data['event']), Q(session_name__exact=event_session_data['session_name']))
                event_session_form = EventSessionForm(event_session_data, instance=event_session)
            except EventSession.DoesNotExist:
                event_session_form = EventSessionForm(event_session_data)
            if not event_session_form.is_valid():
                if (event_id == None):
                    Event.objects.get(id=final_event_id).delete()
                raise ValidationError(_("There is an error in the input data in the sessions: %s" % event_session_form.errors))

        if (event_id == None):
            pass
        else:
            EventUrl.objects.filter(event=event_id).delete()
            EventDeadline.objects.filter(event=event_id).delete()
            EventSession.objects.filter(event=event_id).delete()

        for event_url_data in event_url_data_list2:
            event_url_form = EventUrlForm(event_url_data)
            event_url_form.save()

        for event_deadline_data in event_deadline_data_list2:
            event_deadline_form = EventDeadlineForm(event_deadline_data)
            event_deadline_form.save()

        for event_session_data in event_session_data_list2:
            event_session_form = EventSessionForm(event_session_data)
            event_session_form.save()


    @staticmethod
    def get_synonyms():
        """Returns a dictionay with names (strings) and the fields (strings)
        they refer.

        All values of the returned dictionary (except groups, urls and
        sessions) must be names of fields of the Event class.

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
            def add(dictionary, key, value):
                assert( not dictionary.has_key(key))
                dictionary[key] = value
        else:
            def add(dictionary, key, value):
                dictionary[key] = value
        synonyms = {}
        add(synonyms, 'title', 'title')       # title
        add(synonyms, 't', 'title')
        add(synonyms, 'titl', 'title')
        add(synonyms, 'start', 'start')       # start
        add(synonyms, 'date', 'start')
        add(synonyms, 'd', 'start')
        add(synonyms, 'tags', 'tags')        # tags
        add(synonyms, 'subjects', 'tags')
        add(synonyms, 's', 'tags')
        add(synonyms, 'end', 'end')         # end
        add(synonyms, 'e', 'end')
        add(synonyms, 'endd', 'end')
        add(synonyms, 'acronym', 'acronym')     # acronym
        add(synonyms, 'acro', 'acronym')
        add(synonyms, 'public', 'public')      # public
        add(synonyms, 'p', 'public')
        add(synonyms, 'country', 'country')     # country
        add(synonyms, 'coun', 'country')
        add(synonyms, 'c', 'country')
        add(synonyms, 'city', 'city')        # city
        add(synonyms, 'cc', 'city')
        add(synonyms, 'postcode', 'postcode')    # postcode
        add(synonyms, 'pp', 'postcode')
        add(synonyms, 'zip', 'postcode')
        add(synonyms, 'code', 'postcode')
        add(synonyms, 'address', 'address')     # address
        add(synonyms, 'addr', 'address')
        add(synonyms, 'a', 'address')
        add(synonyms, 'latitude', 'latitude')    # latitude
        add(synonyms, 'lati', 'latitude')
        add(synonyms, 'longitude', 'longitude')   # longitude
        add(synonyms, 'long', 'longitude')
        add(synonyms, 'timezone', 'timezone')    # timezone
        add(synonyms, 'description', 'description') # description
        add(synonyms, 'desc', 'description')
        add(synonyms, 'des', 'description')
        add(synonyms, 'de', 'description')
        add(synonyms, 'groups', 'groups')      # groups (*)
        add(synonyms, 'group', 'groups')
        add(synonyms, 'g', 'groups')
        add(synonyms, 'urls', 'urls')        # urls (*)
        add(synonyms, 'u', 'urls')
        add(synonyms, 'web', 'urls')
        add(synonyms, 'deadlines', 'deadlines')  # deadlines (*)
        add(synonyms, 'deadline', 'deadlines')  # deadlines (*)
        add(synonyms, 'sessions', 'sessions')    # sessions (*)
        add(synonyms, 'times', 'sessions')
        add(synonyms, 'time', 'sessions')
        # (*) can have multi lines
        return synonyms

    @staticmethod
    def is_event_viewable_by_user(event_id, user_id):
        event = Event.objects.get(id=event_id)
        if event.public:
            return True
        elif event.user == None:
            return True
        elif event.user.id == user_id:
            return True
        else:
            # iterating over all groups that the event belongs to
            for g in Group.objects.filter(events__id__exact=event_id):
                if Group.is_user_in_group(user_id, g.id):
                    return True
            return False

    def is_in_groups_list(self):
        # TODO: rename this function and make it return a True or False value
        return Group.objects.filter(events=self)

    def is_in_groups_id_list(self):
        groups_id_list = list()
        for g in Group.objects.filter(events=self):
            groups_id_list.append(g.id)
        return groups_id_list

    def add_to_group(self, group_id):
        g = Group.objects.get(id=group_id)
        calentry = Calendar(event=self, group=g)
        calentry.save()

    def remove_from_group(self, group_id):
        g = Group.objects.get(id=group_id)
        calentry = Calendar.objects.get(event=self, group=g)
        calentry.delete()

class EventUrl(models.Model):
    event = models.ForeignKey(Event, related_name='urls')
    url_name = models.CharField(_(u'URL Name'), blank=False, null=False,
            max_length=80, help_text=_(
            "Example: information about accomodation"))
    url = models.URLField(_(u'URL'), blank=False, null=False)
    class Meta:
        ordering = ['event', 'url_name']
        unique_together = ("event", "url_name")
    def __unicode__(self):
        return self.url

class EventDeadline(models.Model):
    event = models.ForeignKey(Event, related_name='deadlines')
    deadline_name = models.CharField(_(u'Deadline name'), blank=False, null=False,
            max_length=80, help_text=_(
            "Example: call for papers deadline"))
    deadline = models.DateField(_(u'Deadline'), blank=False, null=False)
    class Meta:
        ordering = ['event', 'deadline', 'deadline_name']
        unique_together = ("event", "deadline_name")
    def __unicode__(self):
        return unicode(self.deadline) + u' - ' + self.deadline_name

class EventSession(models.Model):
    event = models.ForeignKey(Event, related_name='sessions')
    session_name = models.CharField(_(u'Session name'), blank=False, null=False,
            max_length=80, help_text=_(
            "Example: day 2 of the conference"))
    session_date = models.DateField(_(u'Session day'), blank=False,
            null=False)
    session_starttime = models.TimeField(_(u'Session start time'),
            blank=False, null=False)
    session_endtime = models.TimeField(_(u'Session end time'), blank=False, null=False)
    class Meta:
        ordering = ['event', 'session_date', 'session_starttime', 'session_endtime']
        unique_together = ("event", "session_name")
        verbose_name = _(u'Session')
        verbose_name_plural = _(u'Sessions')
    def __unicode__(self):
        return unicode(self.session_date) + u' - ' + unicode(self.session_starttime) + u' - ' + unicode(self.session_endtime) + u' - ' + self.session_name

class Filter(models.Model):
    user = models.ForeignKey(User, unique=False, verbose_name=_(u'User'))
    modification_time = models.DateTimeField(_(u'Modification time'),
            editable=False, auto_now=True)
    query = models.CharField(_(u'Query'), max_length=500, blank=False,
            null=False)
    name = models.CharField(_(u'Name'), max_length=40, blank=False, null=False)
    email = models.BooleanField(_(u'Email'), default=False, help_text=
            _(u'If set it sends an email to a user when a new event matches all fields set'))
    maxevents_email = models.SmallIntegerField(_(u'Number of events in e-mail'),
            blank=True, null=True, default=10, help_text=
            _("Maximum number of events to show in a notification e-mail"))
    class Meta:
        ordering = ['modification_time']
        unique_together = ("user", "name")
        verbose_name = _(u'Filter')
        verbose_name_plural = _(u'Filters')
    def __unicode__(self):
        return self.name
    @models.permalink
    def get_absolute_url(self):
        return ('filter_edit', (), { 'filter_id': self.id })

class Group(models.Model):
    # FIXME: groups only as lowerDeadlines case ascii (case insensitive). Validate everywhere including save method.
    name = models.CharField(_(u'Name'), max_length=80, unique=True)
    description = models.TextField(_(u'Description'))
    members = models.ManyToManyField(User, through='Membership',
            verbose_name=_(u'Members'))
    events = models.ManyToManyField(Event, through='Calendar',
            verbose_name=_(u'Events'))
    creation_time = models.DateTimeField(_(u'Creation time'), editable=False,
            auto_now_add=True)
    modification_time = models.DateTimeField(_(u'Modification time'),
            editable=False, auto_now=True)

    class Meta:
        ordering = ['creation_time']
        verbose_name = _(u'Group')
        verbose_name_plural = _(u'Groups')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('list_events_group', (), { 'group_id': self.id })

    @staticmethod
    def is_user_in_group(user_id, group_id):
        times_user_in_group = Membership.objects.filter(
                user__id__exact=user_id,
                group__id__exact=group_id)
        if times_user_in_group.count() > 0:
            assert(times_user_in_group == 1)
            return True
        else:
            return False

    def is_user_member_of(self, user):
        if Membership.objects.get(group=self, user=user):
            return True
        else:
            return False

    def is_event_in_calendar(self, event):
        return False

class Membership(models.Model):
    """Relation between users and groups."""
    user = models.ForeignKey(User, verbose_name=_(u'User'), related_name='user_in_groups')
    group = models.ForeignKey(Group, verbose_name=_(u'Group'), related_name='users_in_group')
    is_administrator = models.BooleanField(_(u'Is administrator'), default=True)
    """Not used at the moment. All members of a group are administrators."""
    new_event_email = models.BooleanField(_(u'New event email'), default=True)
    new_member_email = models.BooleanField(_(u'email_member_email'), default=True)
    date_joined = models.DateField(_(u'date_joined'), editable=False, auto_now_add=True)
    class Meta:
        unique_together = ("user", "group")
        verbose_name = _(u'Membership')
        verbose_name_plural = _(u'Memberships')

class Calendar(models.Model):
    """Relation between events and groups."""
    event = models.ForeignKey(Event, verbose_name=_(u'Event'), related_name='event_in_groups')
    group = models.ForeignKey(Group, verbose_name=_(u'Group'), related_name='calendar')
    date_added = models.DateField(_(u'Date added'), editable=False, auto_now_add=True)
    class Meta:
        unique_together = ("event", "group")
        verbose_name = _(u'Calendar')
        verbose_name_plural = _(u'Calendars')

# Next code is an adaptation of some code in python-django-registration
SHA1_RE = re.compile('^[a-f0-9]{40}$')
class GroupInvitationManager(models.Manager):
    """
    Custom manager for the ``GroupInvitation`` model.

    The methods defined here provide shortcuts for account creation
    and activation (including generation and emailing of activation
    keys), and for cleaning out expired Group Invitations.

    """
    def activate_invitation(self, activation_key):
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
        if SHA1_RE.search(activation_key):
            try:
                invitation = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not invitation.activation_key_expired():
                host = invitation.host
                guest = invitation.guest
                group = invitation.group
                as_administrator = invitation.as_administrator
                # check that the host is an administrator of the group
                h = Membership.objects.filter(user=host,group=group)
                if len(h) == 0:
                    return False
                if not h[0].is_administrator:
                    return False
                # check if the user is already in the group and give him administrator rights if he
                # hasn't it but it was set in the invitation
                member_list = Membership.objects.filter(user=guest, group=group)
                if not len(member_list) == 0:
                    assert len(member_list) == 1
                    if as_administrator and not member_list[0].is_administrator:
                        member_list[0].is_administrator = True
                        member_list[0].activation_key = self.model.ACTIVATED
                    return False
                else:
                    member = Membership(user=guest, group=group, is_administrator=as_administrator)
                    member.activation_key = self.model.ACTIVATED
                    member.save()
                    return True
        return False

    def create_invitation(self, host, guest, group, as_administrator):
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
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        activation_key = hashlib.sha1(salt+guest.username).hexdigest()
        self.create(host=host,guest=guest,group=group,as_administrator=as_administrator,
                           activation_key=activation_key)

        from django.core.mail import send_mail
        current_site = Site.objects.get_current()

        subject = render_to_string('groups/invitation_email_subject.txt',
                                   { 'site': current_site })
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        message = render_to_string('groups/invitation_email.txt',
                                   { 'activation_key': activation_key,
                                     'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                                     'site': current_site,
                                     'host': host.username,
                                     'group': group.name, })

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [guest.email])


    def delete_expired_invitations(self):
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

class GroupInvitation(models.Model):
    """
    A simple class which stores an activation key for use during
    user group invitations.

    Generally, you will not want to interact directly with instances
    of this model; the provided manager includes methods
    for creating and activating invitations, as well as for cleaning
    out group invitations which have never been activated.

    """
    ACTIVATED = u"ALREADY_ACTIVATED"

    host = models.ForeignKey(User, related_name="host", verbose_name=_(u'host'))
    guest = models.ForeignKey(User, related_name="guest", verbose_name=_(u'host'))
    group = models.ForeignKey(Group, verbose_name=_(u'group'))
    as_administrator = models.BooleanField(_(u'as administrator'), default=False)
    activation_key = models.CharField(_(u'activation key'), max_length=40)

    # see http://docs.djangoproject.com/en/1.0/topics/db/managers/
    objects = GroupInvitationManager()

    class Meta:
#        unique_together = ("host", "guest", "group")
        verbose_name = _(u'Group invitation')
        verbose_name_plural = _(u'Group invitations')

    def __unicode__(self):
        return u"group invitation information for group %s for user %s from user %s" % (self.group,
                self.guest, self.host)

    def activation_key_expired(self):
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
        expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or \
               (self.guest.date_joined + expiration_date <= datetime.datetime.now())
    # TODO: find out and explain here what this means:
    activation_key_expired.boolean = True


# TODO: add setting info to users. See the auth documentation because there is a method for adding
# fields to User. E.g.
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

