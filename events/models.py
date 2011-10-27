#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# GPL {{{1
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

""" Models """

# imports {{{1
import datetime
import hashlib
from itertools import chain
import pytz
import random
import re
from re import UNICODE
from smtplib import SMTPConnectError

import vobject

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.comments import Comment
from django.contrib.comments.signals import comment_was_posted
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.gis.db.models import Q
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D # ``D`` is a shortcut for ``Distance``
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator
from django.db.models import Min
from django.db.models.signals import \
        pre_save, post_save, pre_delete, post_delete
from django.forms import DateField
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import smart_str, smart_unicode
from django.utils.translation import ugettext_lazy as _
# FIXME from gridcalendar.events.decorators import autoconnect

from tagging.fields import TagField
from tagging.models import Tag, TaggedItem
import reversion
from reversion import revision
from reversion.models import Version, Revision, VERSION_ADD, VERSION_DELETE

from gridcalendar.events.utils import ( validate_year, search_name,
        search_address, search_timezone, text_diff, validate_tags_chars )
from gridcalendar.events.tasks import (
        log_using_celery, notify_users_when_wanted )

# COUNTRIES {{{1
# TODO: use instead a client library from http://www.geonames.org/ accepting
# names (in different languages) and codes like e.g. ES, es,  ESP, eSp, 724,
# España, etc. Name colisions in different languages needs to be checked.
# OR use python.django.countries
# TODO: use the language selected by the user in all APIs
# TODO: use a package with the names which is updated automatically, think
# what would happen if a name is longer than the len of the field in the DB
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

# TIMEZONES {{{1
# data from: ``from pytz import common_timezones`` at Wed Oct 12 2011
# TODO: use a package with the names which is updated automatically, think
# what would happen if a name is longer than the len of the field in the DB
TIMEZONES = (
    ( _( 'Africa' ), ( # {{{2
        ( 'Africa/Abidjan', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Abidjan' )) ),
        ( 'Africa/Accra', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Accra' )) ),
        ( 'Africa/Addis Ababa', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Addis Ababa' )) ),
        ( 'Africa/Algiers', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Algiers' )) ),
        ( 'Africa/Asmara', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Asmara' )) ),
        ( 'Africa/Bamako', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Bamako' )) ),
        ( 'Africa/Bangui', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Bangui' )) ),
        ( 'Africa/Banjul', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Banjul' )) ),
        ( 'Africa/Bissau', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Bissau' )) ),
        ( 'Africa/Blantyre', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Blantyre' )) ),
        ( 'Africa/Brazzaville', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Brazzaville' )) ),
        ( 'Africa/Bujumbura', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Bujumbura' )) ),
        ( 'Africa/Cairo', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Cairo' )) ),
        ( 'Africa/Casablanca', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Casablanca' )) ),
        ( 'Africa/Ceuta', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Ceuta' )) ),
        ( 'Africa/Conakry', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Conakry' )) ),
        ( 'Africa/Dakar', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Dakar' )) ),
        ( 'Africa/Dar es Salaam', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Dar es Salaam' )) ),
        ( 'Africa/Djibouti', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Djibouti' )) ),
        ( 'Africa/Douala', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Douala' )) ),
        ( 'Africa/El Aaiun', unicode(_( 'Africa' )) + u'/' + unicode(_( 'El Aaiun' )) ),
        ( 'Africa/Freetown', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Freetown' )) ),
        ( 'Africa/Gaborone', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Gaborone' )) ),
        ( 'Africa/Harare', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Harare' )) ),
        ( 'Africa/Johannesburg', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Johannesburg' )) ),
        ( 'Africa/Kampala', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Kampala' )) ),
        ( 'Africa/Khartoum', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Khartoum' )) ),
        ( 'Africa/Kigali', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Kigali' )) ),
        ( 'Africa/Kinshasa', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Kinshasa' )) ),
        ( 'Africa/Lagos', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Lagos' )) ),
        ( 'Africa/Libreville', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Libreville' )) ),
        ( 'Africa/Lome', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Lome' )) ),
        ( 'Africa/Luanda', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Luanda' )) ),
        ( 'Africa/Lubumbashi', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Lubumbashi' )) ),
        ( 'Africa/Lusaka', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Lusaka' )) ),
        ( 'Africa/Malabo', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Malabo' )) ),
        ( 'Africa/Maputo', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Maputo' )) ),
        ( 'Africa/Maseru', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Maseru' )) ),
        ( 'Africa/Mbabane', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Mbabane' )) ),
        ( 'Africa/Mogadishu', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Mogadishu' )) ),
        ( 'Africa/Monrovia', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Monrovia' )) ),
        ( 'Africa/Nairobi', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Nairobi' )) ),
        ( 'Africa/Ndjamena', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Ndjamena' )) ),
        ( 'Africa/Niamey', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Niamey' )) ),
        ( 'Africa/Nouakchott', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Nouakchott' )) ),
        ( 'Africa/Ouagadougou', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Ouagadougou' )) ),
        ( 'Africa/Porto-Novo', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Porto-Novo' )) ),
        ( 'Africa/Sao Tome', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Sao Tome' )) ),
        ( 'Africa/Tripoli', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Tripoli' )) ),
        ( 'Africa/Tunis', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Tunis' )) ),
        ( 'Africa/Windhoek', unicode(_( 'Africa' )) + u'/' + unicode(_( 'Windhoek' )) ), )
    ),
    ( _( 'America' ), ( # {{{2
        ( 'America/Adak', unicode(_( 'America' )) + u'/' + unicode(_( 'Adak' )) ),
        ( 'America/Anchorage', unicode(_( 'America' )) + u'/' + unicode(_( 'Anchorage' )) ),
        ( 'America/Anguilla', unicode(_( 'America' )) + u'/' + unicode(_( 'Anguilla' )) ),
        ( 'America/Antigua', unicode(_( 'America' )) + u'/' + unicode(_( 'Antigua' )) ),
        ( 'America/Araguaina', unicode(_( 'America' )) + u'/' + unicode(_( 'Araguaina' )) ),
        ( 'America/Argentina/Buenos Aires', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina' )) + u'/' + unicode(_( 'Buenos Aires' )) ),
        ( 'America/Argentina/Catamarca', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Catamarca' )) ),
        ( 'America/Argentina/Cordoba', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Cordoba' )) ),
        ( 'America/Argentina/Jujuy', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Jujuy' )) ),
        ( 'America/Argentina/La Rioja', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'La Rioja' )) ),
        ( 'America/Argentina/Mendoza', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Mendoza' )) ),
        ( 'America/Argentina/Rio Gallegos', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Rio Gallegos' )) ),
        ( 'America/Argentina/Salta', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Salta' )) ),
        ( 'America/Argentina/San Juan', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'San Juan' )) ),
        ( 'America/Argentina/San Luis', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'San Luis' )) ),
        ( 'America/Argentina/Tucuman', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Tucuman' )) ),
        ( 'America/Argentina/Ushuaia', unicode(_( 'America' )) + u'/' + unicode(_( 'Argentina')) + u'/' + unicode(_( 'Ushuaia' )) ),
        ( 'America/Aruba', unicode(_( 'America' )) + u'/' + unicode(_( 'Aruba' )) ),
        ( 'America/Asuncion', unicode(_( 'America' )) + u'/' + unicode(_( 'Asuncion' )) ),
        ( 'America/Atikokan', unicode(_( 'America' )) + u'/' + unicode(_( 'Atikokan' )) ),
        ( 'America/Bahia', unicode(_( 'America' )) + u'/' + unicode(_( 'Bahia' )) ),
        ( 'America/Barbados', unicode(_( 'America' )) + u'/' + unicode(_( 'Barbados' )) ),
        ( 'America/Belem', unicode(_( 'America' )) + u'/' + unicode(_( 'Belem' )) ),
        ( 'America/Belize', unicode(_( 'America' )) + u'/' + unicode(_( 'Belize' )) ),
        ( 'America/Blanc-Sablon', unicode(_( 'America' )) + u'/' + unicode(_( 'Blanc-Sablon' )) ),
        ( 'America/Boa Vista', unicode(_( 'America' )) + u'/' + unicode(_( 'Boa Vista' )) ),
        ( 'America/Bogota', unicode(_( 'America' )) + u'/' + unicode(_( 'Bogota' )) ),
        ( 'America/Boise', unicode(_( 'America' )) + u'/' + unicode(_( 'Boise' )) ),
        ( 'America/Cambridge Bay', unicode(_( 'America' )) + u'/' + unicode(_( 'Cambridge Bay' )) ),
        ( 'America/Campo Grande', unicode(_( 'America' )) + u'/' + unicode(_( 'Campo Grande' )) ),
        ( 'America/Cancun', unicode(_( 'America' )) + u'/' + unicode(_( 'Cancun' )) ),
        ( 'America/Caracas', unicode(_( 'America' )) + u'/' + unicode(_( 'Caracas' )) ),
        ( 'America/Cayenne', unicode(_( 'America' )) + u'/' + unicode(_( 'Cayenne' )) ),
        ( 'America/Cayman', unicode(_( 'America' )) + u'/' + unicode(_( 'Cayman' )) ),
        ( 'America/Chicago', unicode(_( 'America' )) + u'/' + unicode(_( 'Chicago' )) ),
        ( 'America/Chihuahua', unicode(_( 'America' )) + u'/' + unicode(_( 'Chihuahua' )) ),
        ( 'America/Costa Rica', unicode(_( 'America' )) + u'/' + unicode(_( 'Costa Rica' )) ),
        ( 'America/Cuiaba', unicode(_( 'America' )) + u'/' + unicode(_( 'Cuiaba' )) ),
        ( 'America/Curacao', unicode(_( 'America' )) + u'/' + unicode(_( 'Curacao' )) ),
        ( 'America/Danmarkshavn', unicode(_( 'America' )) + u'/' + unicode(_( 'Danmarkshavn' )) ),
        ( 'America/Dawson', unicode(_( 'America' )) + u'/' + unicode(_( 'Dawson' )) ),
        ( 'America/Dawson Creek', unicode(_( 'America' )) + u'/' + unicode(_( 'Dawson Creek' )) ),
        ( 'America/Denver', unicode(_( 'America' )) + u'/' + unicode(_( 'Denver' )) ),
        ( 'America/Detroit', unicode(_( 'America' )) + u'/' + unicode(_( 'Detroit' )) ),
        ( 'America/Dominica', unicode(_( 'America' )) + u'/' + unicode(_( 'Dominica' )) ),
        ( 'America/Edmonton', unicode(_( 'America' )) + u'/' + unicode(_( 'Edmonton' )) ),
        ( 'America/Eirunepe', unicode(_( 'America' )) + u'/' + unicode(_( 'Eirunepe' )) ),
        ( 'America/El Salvador', unicode(_( 'America' )) + u'/' + unicode(_( 'El Salvador' )) ),
        ( 'America/Fortaleza', unicode(_( 'America' )) + u'/' + unicode(_( 'Fortaleza' )) ),
        ( 'America/Glace Bay', unicode(_( 'America' )) + u'/' + unicode(_( 'Glace Bay' )) ),
        ( 'America/Godthab', unicode(_( 'America' )) + u'/' + unicode(_( 'Godthab' )) ),
        ( 'America/Goose Bay', unicode(_( 'America' )) + u'/' + unicode(_( 'Goose Bay' )) ),
        ( 'America/Grand Turk', unicode(_( 'America' )) + u'/' + unicode(_( 'Grand Turk' )) ),
        ( 'America/Grenada', unicode(_( 'America' )) + u'/' + unicode(_( 'Grenada' )) ),
        ( 'America/Guadeloupe', unicode(_( 'America' )) + u'/' + unicode(_( 'Guadeloupe' )) ),
        ( 'America/Guatemala', unicode(_( 'America' )) + u'/' + unicode(_( 'Guatemala' )) ),
        ( 'America/Guayaquil', unicode(_( 'America' )) + u'/' + unicode(_( 'Guayaquil' )) ),
        ( 'America/Guyana', unicode(_( 'America' )) + u'/' + unicode(_( 'Guyana' )) ),
        ( 'America/Halifax', unicode(_( 'America' )) + u'/' + unicode(_( 'Halifax' )) ),
        ( 'America/Havana', unicode(_( 'America' )) + u'/' + unicode(_( 'Havana' )) ),
        ( 'America/Hermosillo', unicode(_( 'America' )) + u'/' + unicode(_( 'Hermosillo' )) ),
        ( 'America/Indiana/Indianapolis', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Indianapolis' )) ),
        ( 'America/Indiana/Knox', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Knox' )) ),
        ( 'America/Indiana/Marengo', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Marengo' )) ),
        ( 'America/Indiana/Petersburg', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Petersburg' )) ),
        ( 'America/Indiana/Tell City', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Tell City' )) ),
        ( 'America/Indiana/Vevay', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Vevay' )) ),
        ( 'America/Indiana/Vincennes', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Vincennes' )) ),
        ( 'America/Indiana/Winamac', unicode(_( 'America')) + u'/' + unicode(_( 'Indiana' )) + u'/' + unicode(_( 'Winamac' )) ),
        ( 'America/Inuvik', unicode(_( 'America' )) + u'/' + unicode(_( 'Inuvik' )) ),
        ( 'America/Iqaluit', unicode(_( 'America' )) + u'/' + unicode(_( 'Iqaluit' )) ),
        ( 'America/Jamaica', unicode(_( 'America' )) + u'/' + unicode(_( 'Jamaica' )) ),
        ( 'America/Juneau', unicode(_( 'America' )) + u'/' + unicode(_( 'Juneau' )) ),
        ( 'America/Kentucky/Louisville', unicode(_( 'America')) + u'/' + unicode(_( 'Kentucky' )) + u'/' + unicode(_( 'Louisville' )) ),
        ( 'America/Kentucky/Monticello', unicode(_( 'America')) + u'/' + unicode(_( 'Kentucky' )) + u'/' + unicode(_( 'Monticello' )) ),
        ( 'America/La Paz', unicode(_( 'America' )) + u'/' + unicode(_( 'La Paz' )) ),
        ( 'America/Lima', unicode(_( 'America' )) + u'/' + unicode(_( 'Lima' )) ),
        ( 'America/Los Angeles', unicode(_( 'America' )) + u'/' + unicode(_( 'Los Angeles' )) ),
        ( 'America/Maceio', unicode(_( 'America' )) + u'/' + unicode(_( 'Maceio' )) ),
        ( 'America/Managua', unicode(_( 'America' )) + u'/' + unicode(_( 'Managua' )) ),
        ( 'America/Manaus', unicode(_( 'America' )) + u'/' + unicode(_( 'Manaus' )) ),
        ( 'America/Martinique', unicode(_( 'America' )) + u'/' + unicode(_( 'Martinique' )) ),
        ( 'America/Matamoros', unicode(_( 'America' )) + u'/' + unicode(_( 'Matamoros' )) ),
        ( 'America/Mazatlan', unicode(_( 'America' )) + u'/' + unicode(_( 'Mazatlan' )) ),
        ( 'America/Menominee', unicode(_( 'America' )) + u'/' + unicode(_( 'Menominee' )) ),
        ( 'America/Merida', unicode(_( 'America' )) + u'/' + unicode(_( 'Merida' )) ),
        ( 'America/Mexico City', unicode(_( 'America' )) + u'/' + unicode(_( 'Mexico City' )) ),
        ( 'America/Miquelon', unicode(_( 'America' )) + u'/' + unicode(_( 'Miquelon' )) ),
        ( 'America/Moncton', unicode(_( 'America' )) + u'/' + unicode(_( 'Moncton' )) ),
        ( 'America/Monterrey', unicode(_( 'America' )) + u'/' + unicode(_( 'Monterrey' )) ),
        ( 'America/Montevideo', unicode(_( 'America' )) + u'/' + unicode(_( 'Montevideo' )) ),
        ( 'America/Montreal', unicode(_( 'America' )) + u'/' + unicode(_( 'Montreal' )) ),
        ( 'America/Montserrat', unicode(_( 'America' )) + u'/' + unicode(_( 'Montserrat' )) ),
        ( 'America/Nassau', unicode(_( 'America' )) + u'/' + unicode(_( 'Nassau' )) ),
        ( 'America/New York', unicode(_( 'America' )) + u'/' + unicode(_( 'New York' )) ),
        ( 'America/Nipigon', unicode(_( 'America' )) + u'/' + unicode(_( 'Nipigon' )) ),
        ( 'America/Nome', unicode(_( 'America' )) + u'/' + unicode(_( 'Nome' )) ),
        ( 'America/Noronha', unicode(_( 'America' )) + u'/' + unicode(_( 'Noronha' )) ),
        ( 'America/North Dakota/Center', unicode(_( 'America' )) + u'/' + unicode(_( 'North Dakota' )) + u'/' + unicode(_( 'Center' )) ),
        ( 'America/North Dakota/New Salem', unicode(_( 'America' )) + u'/' + unicode(_( 'North Dakota' )) + u'/' + unicode(_( 'New Salem' )) ),
        ( 'America/Ojinaga', unicode(_( 'America' )) + u'/' + unicode(_( 'Ojinaga' )) ),
        ( 'America/Panama', unicode(_( 'America' )) + u'/' + unicode(_( 'Panama' )) ),
        ( 'America/Pangnirtung', unicode(_( 'America' )) + u'/' + unicode(_( 'Pangnirtung' )) ),
        ( 'America/Paramaribo', unicode(_( 'America' )) + u'/' + unicode(_( 'Paramaribo' )) ),
        ( 'America/Phoenix', unicode(_( 'America' )) + u'/' + unicode(_( 'Phoenix' )) ),
        ( 'America/Port-au-Prince', unicode(_( 'America' )) + u'/' + unicode(_( 'Port-au-Prince' )) ),
        ( 'America/Port of Spain', unicode(_( 'America' )) + u'/' + unicode(_( 'Port of Spain' )) ),
        ( 'America/Porto Velho', unicode(_( 'America' )) + u'/' + unicode(_( 'Porto Velho' )) ),
        ( 'America/Puerto Rico', unicode(_( 'America' )) + u'/' + unicode(_( 'Puerto Rico' )) ),
        ( 'America/Rainy River', unicode(_( 'America' )) + u'/' + unicode(_( 'Rainy River' )) ),
        ( 'America/Rankin Inlet', unicode(_( 'America' )) + u'/' + unicode(_( 'Rankin Inlet' )) ),
        ( 'America/Recife', unicode(_( 'America' )) + u'/' + unicode(_( 'Recife' )) ),
        ( 'America/Regina', unicode(_( 'America' )) + u'/' + unicode(_( 'Regina' )) ),
        ( 'America/Resolute', unicode(_( 'America' )) + u'/' + unicode(_( 'Resolute' )) ),
        ( 'America/Rio Branco', unicode(_( 'America' )) + u'/' + unicode(_( 'Rio Branco' )) ),
        ( 'America/Santa Isabel', unicode(_( 'America' )) + u'/' + unicode(_( 'Santa Isabel' )) ),
        ( 'America/Santarem', unicode(_( 'America' )) + u'/' + unicode(_( 'Santarem' )) ),
        ( 'America/Santiago', unicode(_( 'America' )) + u'/' + unicode(_( 'Santiago' )) ),
        ( 'America/Santo Domingo', unicode(_( 'America' )) + u'/' + unicode(_( 'Santo Domingo' )) ),
        ( 'America/Sao Paulo', unicode(_( 'America' )) + u'/' + unicode(_( 'Sao Paulo' )) ),
        ( 'America/Scoresbysund', unicode(_( 'America' )) + u'/' + unicode(_( 'Scoresbysund' )) ),
        ( 'America/St Johns', unicode(_( 'America' )) + u'/' + unicode(_( 'St Johns' )) ),
        ( 'America/St Kitts', unicode(_( 'America' )) + u'/' + unicode(_( 'St Kitts' )) ),
        ( 'America/St Lucia', unicode(_( 'America' )) + u'/' + unicode(_( 'St Lucia' )) ),
        ( 'America/St Thomas', unicode(_( 'America' )) + u'/' + unicode(_( 'St Thomas' )) ),
        ( 'America/St Vincent', unicode(_( 'America' )) + u'/' + unicode(_( 'St Vincent' )) ),
        ( 'America/Swift Current', unicode(_( 'America' )) + u'/' + unicode(_( 'Swift Current' )) ),
        ( 'America/Tegucigalpa', unicode(_( 'America' )) + u'/' + unicode(_( 'Tegucigalpa' )) ),
        ( 'America/Thule', unicode(_( 'America' )) + u'/' + unicode(_( 'Thule' )) ),
        ( 'America/Thunder Bay', unicode(_( 'America' )) + u'/' + unicode(_( 'Thunder Bay' )) ),
        ( 'America/Tijuana', unicode(_( 'America' )) + u'/' + unicode(_( 'Tijuana' )) ),
        ( 'America/Toronto', unicode(_( 'America' )) + u'/' + unicode(_( 'Toronto' )) ),
        ( 'America/Tortola', unicode(_( 'America' )) + u'/' + unicode(_( 'Tortola' )) ),
        ( 'America/Vancouver', unicode(_( 'America' )) + u'/' + unicode(_( 'Vancouver' )) ),
        ( 'America/Whitehorse', unicode(_( 'America' )) + u'/' + unicode(_( 'Whitehorse' )) ),
        ( 'America/Winnipeg', unicode(_( 'America' )) + u'/' + unicode(_( 'Winnipeg' )) ),
        ( 'America/Yakutat', unicode(_( 'America' )) + u'/' + unicode(_( 'Yakutat' )) ),
        ( 'America/Yellowknife', unicode(_( 'America' )) + u'/' + unicode(_( 'Yellowknife' ))), )
    ),
    ( _( 'Antarctica' ), ( # {{{2
        ( 'Antarctica/Casey', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'Casey' )) ),
        ( 'Antarctica/Davis', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'Davis' )) ),
        ( 'Antarctica/DumontDUrville', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'DumontDUrville' )) ),
        ( 'Antarctica/Mawson', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'Mawson' )) ),
        ( 'Antarctica/McMurdo', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'McMurdo' )) ),
        ( 'Antarctica/Palmer', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'Palmer' )) ),
        ( 'Antarctica/Rothera', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'Rothera' )) ),
        ( 'Antarctica/Syowa', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'Syowa' )) ),
        ( 'Antarctica/Vostok', unicode(_( 'Antarctica' )) + u'/' + unicode(_( 'Vostok' )) ), )
    ),
    ( _( 'Asia' ), ( # {{{2
        ( 'Asia/Aden', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Aden' )) ),
        ( 'Asia/Almaty', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Almaty' )) ),
        ( 'Asia/Amman', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Amman' )) ),
        ( 'Asia/Anadyr', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Anadyr' )) ),
        ( 'Asia/Aqtau', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Aqtau' )) ),
        ( 'Asia/Aqtobe', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Aqtobe' )) ),
        ( 'Asia/Ashgabat', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Ashgabat' )) ),
        ( 'Asia/Baghdad', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Baghdad' )) ),
        ( 'Asia/Bahrain', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Bahrain' )) ),
        ( 'Asia/Baku', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Baku' )) ),
        ( 'Asia/Bangkok', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Bangkok' )) ),
        ( 'Asia/Beirut', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Beirut' )) ),
        ( 'Asia/Bishkek', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Bishkek' )) ),
        ( 'Asia/Brunei', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Brunei' )) ),
        ( 'Asia/Choibalsan', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Choibalsan' )) ),
        ( 'Asia/Chongqing', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Chongqing' )) ),
        ( 'Asia/Colombo', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Colombo' )) ),
        ( 'Asia/Damascus', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Damascus' )) ),
        ( 'Asia/Dhaka', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Dhaka' )) ),
        ( 'Asia/Dili', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Dili' )) ),
        ( 'Asia/Dubai', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Dubai' )) ),
        ( 'Asia/Dushanbe', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Dushanbe' )) ),
        ( 'Asia/Gaza', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Gaza' )) ),
        ( 'Asia/Harbin', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Harbin' )) ),
        ( 'Asia/Ho Chi Minh', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Ho Chi Minh' )) ),
        ( 'Asia/Hong Kong', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Hong Kong' )) ),
        ( 'Asia/Hovd', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Hovd' )) ),
        ( 'Asia/Irkutsk', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Irkutsk' )) ),
        ( 'Asia/Jakarta', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Jakarta' )) ),
        ( 'Asia/Jayapura', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Jayapura' )) ),
        ( 'Asia/Jerusalem', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Jerusalem' )) ),
        ( 'Asia/Kabul', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kabul' )) ),
        ( 'Asia/Kamchatka', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kamchatka' )) ),
        ( 'Asia/Karachi', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Karachi' )) ),
        ( 'Asia/Kashgar', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kashgar' )) ),
        ( 'Asia/Kathmandu', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kathmandu' )) ),
        ( 'Asia/Kolkata', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kolkata' )) ),
        ( 'Asia/Krasnoyarsk', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Krasnoyarsk' )) ),
        ( 'Asia/Kuala Lumpur', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kuala Lumpur' )) ),
        ( 'Asia/Kuching', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kuching' )) ),
        ( 'Asia/Kuwait', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Kuwait' )) ),
        ( 'Asia/Macau', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Macau' )) ),
        ( 'Asia/Magadan', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Magadan' )) ),
        ( 'Asia/Makassar', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Makassar' )) ),
        ( 'Asia/Manila', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Manila' )) ),
        ( 'Asia/Muscat', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Muscat' )) ),
        ( 'Asia/Nicosia', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Nicosia' )) ),
        ( 'Asia/Novokuznetsk', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Novokuznetsk' )) ),
        ( 'Asia/Novosibirsk', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Novosibirsk' )) ),
        ( 'Asia/Omsk', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Omsk' )) ),
        ( 'Asia/Oral', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Oral' )) ),
        ( 'Asia/Phnom Penh', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Phnom Penh' )) ),
        ( 'Asia/Pontianak', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Pontianak' )) ),
        ( 'Asia/Pyongyang', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Pyongyang' )) ),
        ( 'Asia/Qatar', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Qatar' )) ),
        ( 'Asia/Qyzylorda', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Qyzylorda' )) ),
        ( 'Asia/Rangoon', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Rangoon' )) ),
        ( 'Asia/Riyadh', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Riyadh' )) ),
        ( 'Asia/Sakhalin', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Sakhalin' )) ),
        ( 'Asia/Samarkand', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Samarkand' )) ),
        ( 'Asia/Seoul', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Seoul' )) ),
        ( 'Asia/Shanghai', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Shanghai' )) ),
        ( 'Asia/Singapore', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Singapore' )) ),
        ( 'Asia/Taipei', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Taipei' )) ),
        ( 'Asia/Tashkent', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Tashkent' )) ),
        ( 'Asia/Tbilisi', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Tbilisi' )) ),
        ( 'Asia/Tehran', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Tehran' )) ),
        ( 'Asia/Thimphu', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Thimphu' )) ),
        ( 'Asia/Tokyo', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Tokyo' )) ),
        ( 'Asia/Ulaanbaatar', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Ulaanbaatar' )) ),
        ( 'Asia/Urumqi', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Urumqi' )) ),
        ( 'Asia/Vientiane', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Vientiane' )) ),
        ( 'Asia/Vladivostok', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Vladivostok' )) ),
        ( 'Asia/Yakutsk', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Yakutsk' )) ),
        ( 'Asia/Yekaterinburg', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Yekaterinburg' )) ),
        ( 'Asia/Yerevan', unicode(_( 'Asia' )) + u'/' + unicode(_( 'Yerevan' )) ), )
    ),
    ( _( 'Atlantic' ), ( # {{{2
        ( 'Atlantic/Azores', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Azores' )) ),
        ( 'Atlantic/Bermuda', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Bermuda' )) ),
        ( 'Atlantic/Canary', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Canary' )) ),
        ( 'Atlantic/Cape Verde', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Cape Verde' )) ),
        ( 'Atlantic/Faroe', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Faroe' )) ),
        ( 'Atlantic/Madeira', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Madeira' )) ),
        ( 'Atlantic/Reykjavik', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Reykjavik' )) ),
        ( 'Atlantic/South Georgia', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'South Georgia' )) ),
        ( 'Atlantic/St Helena', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'St Helena' )) ),
        ( 'Atlantic/Stanley', unicode(_( 'Atlantic' )) + u'/' + unicode(_( 'Stanley' )) ), )
    ),
    ( _( 'Australia' ), ( # {{{2
        ( 'Australia/Adelaide', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Adelaide' )) ),
        ( 'Australia/Brisbane', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Brisbane' )) ),
        ( 'Australia/Broken Hill', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Broken Hill' )) ),
        ( 'Australia/Currie', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Currie' )) ),
        ( 'Australia/Darwin', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Darwin' )) ),
        ( 'Australia/Eucla', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Eucla' )) ),
        ( 'Australia/Hobart', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Hobart' )) ),
        ( 'Australia/Lindeman', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Lindeman' )) ),
        ( 'Australia/Lord Howe', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Lord Howe' )) ),
        ( 'Australia/Melbourne', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Melbourne' )) ),
        ( 'Australia/Perth', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Perth' )) ),
        ( 'Australia/Sydney', unicode(_( 'Australia' )) + u'/' + unicode(_( 'Sydney' )) ), )
    ),
    ( _( 'Canada' ), ( # {{{2
        ( 'Canada/Atlantic', unicode(_( 'Canada' )) + u'/' + unicode(_( 'Atlantic' )) ),
        ( 'Canada/Central', unicode(_( 'Canada' )) + u'/' + unicode(_( 'Central' )) ),
        ( 'Canada/Eastern', unicode(_( 'Canada' )) + u'/' + unicode(_( 'Eastern' )) ),
        ( 'Canada/Mountain', unicode(_( 'Canada' )) + u'/' + unicode(_( 'Mountain' )) ),
        ( 'Canada/Newfoundland', unicode(_( 'Canada' )) + u'/' + unicode(_( 'Newfoundland' )) ),
        ( 'Canada/Pacific', unicode(_( 'Canada' )) + u'/' + unicode(_( 'Pacific' )) ), )
    ),
    ( _( 'Europe' ), ( # {{{2
        ( 'Europe/Amsterdam', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Amsterdam' )) ),
        ( 'Europe/Andorra', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Andorra' )) ),
        ( 'Europe/Athens', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Athens' )) ),
        ( 'Europe/Belgrade', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Belgrade' )) ),
        ( 'Europe/Berlin', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Berlin' )) ),
        ( 'Europe/Brussels', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Brussels' )) ),
        ( 'Europe/Bucharest', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Bucharest' )) ),
        ( 'Europe/Budapest', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Budapest' )) ),
        ( 'Europe/Chisinau', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Chisinau' )) ),
        ( 'Europe/Copenhagen', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Copenhagen' )) ),
        ( 'Europe/Dublin', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Dublin' )) ),
        ( 'Europe/Gibraltar', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Gibraltar' )) ),
        ( 'Europe/Helsinki', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Helsinki' )) ),
        ( 'Europe/Istanbul', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Istanbul' )) ),
        ( 'Europe/Kaliningrad', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Kaliningrad' )) ),
        ( 'Europe/Kiev', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Kiev' )) ),
        ( 'Europe/Lisbon', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Lisbon' )) ),
        ( 'Europe/London', unicode(_( 'Europe' )) + u'/' + unicode(_( 'London' )) ),
        ( 'Europe/Luxembourg', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Luxembourg' )) ),
        ( 'Europe/Madrid', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Madrid' )) ),
        ( 'Europe/Malta', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Malta' )) ),
        ( 'Europe/Minsk', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Minsk' )) ),
        ( 'Europe/Monaco', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Monaco' )) ),
        ( 'Europe/Moscow', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Moscow' )) ),
        ( 'Europe/Oslo', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Oslo' )) ),
        ( 'Europe/Paris', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Paris' )) ),
        ( 'Europe/Prague', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Prague' )) ),
        ( 'Europe/Riga', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Riga' )) ),
        ( 'Europe/Rome', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Rome' )) ),
        ( 'Europe/Samara', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Samara' )) ),
        ( 'Europe/Simferopol', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Simferopol' )) ),
        ( 'Europe/Sofia', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Sofia' )) ),
        ( 'Europe/Stockholm', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Stockholm' )) ),
        ( 'Europe/Tallinn', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Tallinn' )) ),
        ( 'Europe/Tirane', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Tirane' )) ),
        ( 'Europe/Uzhgorod', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Uzhgorod' )) ),
        ( 'Europe/Vaduz', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Vaduz' )) ),
        ( 'Europe/Vienna', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Vienna' )) ),
        ( 'Europe/Vilnius', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Vilnius' )) ),
        ( 'Europe/Volgograd', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Volgograd' )) ),
        ( 'Europe/Warsaw', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Warsaw' )) ),
        ( 'Europe/Zaporozhye', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Zaporozhye' )) ),
        ( 'Europe/Zurich', unicode(_( 'Europe' )) + u'/' + unicode(_( 'Zurich' )) ), )
    ),
    ( _( 'GMT' ), ( # {{{2
        ( 'GMT', _( 'GMT' ) ), )
    ),
    ( _( 'Indian' ), ( # {{{2
        ( 'Indian/Antananarivo', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Antananarivo' )) ),
        ( 'Indian/Chagos', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Chagos' )) ),
        ( 'Indian/Christmas', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Christmas' )) ),
        ( 'Indian/Cocos', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Cocos' )) ),
        ( 'Indian/Comoro', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Comoro' )) ),
        ( 'Indian/Kerguelen', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Kerguelen' )) ),
        ( 'Indian/Mahe', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Mahe' )) ),
        ( 'Indian/Maldives', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Maldives' )) ),
        ( 'Indian/Mauritius', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Mauritius' )) ),
        ( 'Indian/Mayotte', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Mayotte' )) ),
        ( 'Indian/Reunion', unicode(_( 'Indian' )) + u'/' + unicode(_( 'Reunion' )) ), )
    ),
    ( _( 'Pacific' ), ( # {{{2
        ( 'Pacific/Apia', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Apia' )) ),
        ( 'Pacific/Auckland', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Auckland' )) ),
        ( 'Pacific/Chatham', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Chatham' )) ),
        ( 'Pacific/Easter', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Easter' )) ),
        ( 'Pacific/Efate', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Efate' )) ),
        ( 'Pacific/Enderbury', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Enderbury' )) ),
        ( 'Pacific/Fakaofo', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Fakaofo' )) ),
        ( 'Pacific/Fiji', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Fiji' )) ),
        ( 'Pacific/Funafuti', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Funafuti' )) ),
        ( 'Pacific/Galapagos', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Galapagos' )) ),
        ( 'Pacific/Gambier', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Gambier' )) ),
        ( 'Pacific/Guadalcanal', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Guadalcanal' )) ),
        ( 'Pacific/Guam', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Guam' )) ),
        ( 'Pacific/Honolulu', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Honolulu' )) ),
        ( 'Pacific/Johnston', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Johnston' )) ),
        ( 'Pacific/Kiritimati', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Kiritimati' )) ),
        ( 'Pacific/Kosrae', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Kosrae' )) ),
        ( 'Pacific/Kwajalein', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Kwajalein' )) ),
        ( 'Pacific/Majuro', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Majuro' )) ),
        ( 'Pacific/Marquesas', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Marquesas' )) ),
        ( 'Pacific/Midway', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Midway' )) ),
        ( 'Pacific/Nauru', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Nauru' )) ),
        ( 'Pacific/Niue', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Niue' )) ),
        ( 'Pacific/Norfolk', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Norfolk' )) ),
        ( 'Pacific/Noumea', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Noumea' )) ),
        ( 'Pacific/Pago Pago', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Pago Pago' )) ),
        ( 'Pacific/Palau', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Palau' )) ),
        ( 'Pacific/Pitcairn', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Pitcairn' )) ),
        ( 'Pacific/Ponape', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Ponape' )) ),
        ( 'Pacific/Port Moresby', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Port Moresby' )) ),
        ( 'Pacific/Rarotonga', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Rarotonga' )) ),
        ( 'Pacific/Saipan', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Saipan' )) ),
        ( 'Pacific/Tahiti', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Tahiti' )) ),
        ( 'Pacific/Tarawa', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Tarawa' )) ),
        ( 'Pacific/Tongatapu', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Tongatapu' )) ),
        ( 'Pacific/Truk', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Truk' )) ),
        ( 'Pacific/Wake', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Wake' )) ),
        ( 'Pacific/Wallis', unicode(_( 'Pacific' )) + u'/' + unicode(_( 'Wallis' )) ), )
    ),
    ( _( 'US' ), ( # {{{2
        ( 'US/Alaska', unicode(_( 'US' )) + u'/' + unicode(_( 'Alaska' )) ),
        ( 'US/Arizona', unicode(_( 'US' )) + u'/' + unicode(_( 'Arizona' )) ),
        ( 'US/Central', unicode(_( 'US' )) + u'/' + unicode(_( 'Central' )) ),
        ( 'US/Eastern', unicode(_( 'US' )) + u'/' + unicode(_( 'Eastern' )) ),
        ( 'US/Hawaii', unicode(_( 'US' )) + u'/' + unicode(_( 'Hawaii' )) ),
        ( 'US/Mountain', unicode(_( 'US' )) + u'/' + unicode(_( 'Mountain' )) ),
        ( 'US/Pacific', unicode(_( 'US' )) + u'/' + unicode(_( 'Pacific' )) ), )
    ),
    ( _( 'UTC' ), ( # {{{2
        ( 'UTC', _( 'UTC' ) ), )
    )
)

# EXAMPLE {{{1
EXAMPLE = u"""acronym: GriCal
title: GridCalendar presentation
startdate: 2010-12-29
starttime: 10:00
enddate: 2010-12-30
endtime: 18:00
timezone: Europe/Berlin
tags: calendar software open-source gridmind gridcalendar
urls:
    code    http://example.com
    web    http://example.org
address: Gleimstr. 6
postcode: 10439
city: Berlin
country: DE
coordinates: 52.55247, 13.40364
dates:
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

class Event( models.Model ): # {{{1 pylint: disable-msg=R0904
    """ Event model """ # doc {{{2
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
    version = models.PositiveSmallIntegerField(
            _('version'), editable = False, default = 1 )
    acronym = models.CharField( _( u'Acronym' ), max_length = 20, blank = True,
            null = True, help_text = _( u'Example: 26C3' ) )
    title = models.CharField( _( u'Title' ), max_length = 200, blank = False )
    starttime = models.TimeField( 
            _( u'Start time' ), blank = True, null = True,
            help_text = _(u'Example: 18:00') )
    endtime = models.TimeField( 
            _( u'End time' ), blank = True, null = True,
            help_text = _(u'Example: 18:00') )
    # max_length in the line below was calculated with:
    # max( [len(x) for x in common_timezones] )
    timezone = models.CharField( _( u'Timezone' ), blank = True, null = True,
            max_length = 30, choices = TIMEZONES )
    tags = TagField( _( u'Tags' ), blank = True, null = True,
            validators = [validate_tags_chars] )
    country = models.CharField( _( u'Country' ), blank = True, null = True,
            max_length = 2, choices = COUNTRIES )
    city = models.CharField( 
            _( u'City' ), blank = True, null = True, max_length = 50 )
    postcode = models.CharField( _( u'Postcode' ), blank = True, null = True,
            max_length = 16 )
    address = models.CharField( _( u'Address' ), blank = True,
            null = True, max_length = 200,
            help_text = _( u'Complete address including city and country. ' \
                u'Example: Malmöer Str. 6, Berlin, DE' ) )
    coordinates = models.PointField( _('Coordinates'),
            editable = False, blank=True, null=True )
    """ used for calculating events within a distance to a point """
    description = models.TextField(
            _( u'Description' ), blank = True, null = True,
            help_text = _( u'For formating use <a href="http://docutils.' \
                'sourceforge.net/docs/user/rst/quickref.html">' \
                'ReStructuredText</a> syntax. Events can be referenced with' \
                ' for instance :e:`123`' ) )

    objects = models.GeoManager() # {{{2

    # convenient properties {{{2

    # latitude, longitude {{{3
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
    longitude = property(_get_longitude, _set_longitude)

    # startdate, enddate {{{3
    # NOTE: we use (and create if needed) instance properties as a kind of
    # cache, otherwise e.g. sorting a list of events by startdate or enddate
    # would be very expensive
    def _get_startdate(self):
        if hasattr(self, 'startdate_cache') and self.startdate_cache:
            return self.startdate_cache
        try:
            eventdate = self.dates.get(eventdate_name='start')
        except EventDate.DoesNotExist:
            return None
        self.startdate_cache = eventdate.eventdate_date
        return self.startdate_cache
    def _set_startdate(self, value):
        try:
            eventdate = self.dates.get(eventdate_name='start')
        except EventDate.DoesNotExist:
            if value:
                self.dates.create(
                        eventdate_name='start', 
                        eventdate_date=value )
        else:
            if value:
                eventdate.eventdate_date = value
                eventdate.save()
            else:
                eventdate.delete()
        self.startdate_cache = value
    startdate = property(_get_startdate, _set_startdate)
    def _get_enddate(self):
        if hasattr(self, 'enddate_cache') and self.enddate_cache:
            return self.enddate_cache
        try:
            eventdate = self.dates.get(eventdate_name='end')
        except EventDate.DoesNotExist:
            return None
        self.enddate_cache = eventdate.eventdate_date
        return eventdate.eventdate_date
    def _set_enddate(self, value):
        try:
            eventdate = self.dates.get(eventdate_name='end')
        except EventDate.DoesNotExist:
            if value:
                self.dates.create(
                        eventdate_name='end', 
                        eventdate_date=value )
        else:
            if value:
                eventdate.eventdate_date = value
                eventdate.save()
            else:
                eventdate.delete()
        self.enddate_cache = value
    enddate = property(_get_enddate, _set_enddate)

    # read only upcomingdate property {{{3
    @property
    def upcomingdate(self):
        """ get the next upcoming date, or start if all are in the past. """
        if hasattr( self, 'upcomingdate_cache' ) and self.upcomingdate_cache:
            return self.upcomingdate_cache
        today = datetime.date.today()
        future_dates = EventDate.objects.filter(
                event = self, eventdate_date__gte = today )
        if future_dates:
            # not necessary because EventDate has a default ordering:
            # future_dates = future_dates.order_by('dates__eventdate_date')
            self.upcomingdate_cache = future_dates[0].eventdate_date
            return self.upcomingdate_cache
        self.upcomingdate_cache = self.startdate
        return self.startdate

    # Meta {{{2
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        verbose_name = _( u'Event' )
        verbose_name_plural = _( u'Events' )
        # needed for proper order of e.g. master_event.instances:
        # ordering = ['upcoming'] # TODO: see sql queries because this may make
                                # everything too slow

    # methods {{{2
    def custom_dates(self):
        """ returns a queryset with custom EventDates (not reserved, see
        :meth:`EventDate.reserved_names` ) """
        return EventDate.objects.filter( event = self ).exclude(
                eventdate_name__in = EventDate.reserved_names() )

    def tags_separated_by_comma(self): #{{{3
        """ returns the list of tags separated by commas as unicode string """
        return self.tags.replace(' ',',')
    
    def contains( self, date ):
        """ returns True if the event happens in ``date`` or ``date`` is an
        event date. """
        return self.dates.filter(eventdate_date = date).exists()

    def fg_color(self):
        from gridcalendar.events.views import bg_color, fg_color
        return "rgb(%d, %d, %d)" % fg_color( bg_color( self.title ) )
    
    def bg_color(self):
        from gridcalendar.events.views import bg_color, fg_color
        return "rgb(%d, %d, %d)" % bg_color( self.title )
    

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
        upcoming = self.upcomingdate
        keys = days_colors.keys()
        keys.sort()
        keys.reverse()
        for days in keys:
            days_from_today = (upcoming - today).days
            if days_from_today >= days:
                return days_colors[days]
        # FIXME: include a different color-palette for past events:
        return 0

    def update_timezone( self ):
        """ recalculate and save self.timezone according to self.coordinates,
            or self.address, or self.city and self.country

        >>> event = Event.parse_text(EXAMPLE)
        >>> timezone = event.timezone
        >>> latitude = event.latitude
        >>> longitude = event.longitude
        >>> event.coordinates = None
        >>> event.timezone = None
        >>> event.save()
        >>> event.update_timezone()
        >>> assert event.timezone == timezone
        >>> event.timezone = None
        >>> event.city = None
        >>> event.country = None
        >>> event.address = None
        >>> event.coordinates = Point( longitude, latitude )
        >>> event.save()
        >>> event.update_timezone()
        >>> assert event.timezone == timezone
        >>> event.delete()
        """
        if self.coordinates:
            timezone = search_timezone( self.latitude, self.longitude )
            if timezone:
                self.timezone = timezone
                self.save()
                return
        # either no coordinates or they didn't help. We try with the address
        if self.address:
            locations = search_address( self.address )
            if locations and len( locations ) == 1:
                location = locations.items()[0][1]
                timezone = search_timezone(
                        location['latitude'], location['longitude'] )
                if timezone:
                    self.timezone = timezone
                    self.save()
                    return
        if self.country:
            if self.city:
                locations = search_address( self.country + ', ' + self.city )
                if locations and len( locations ) == 1:
                    location = locations.items()[0][1]
                    timezone = search_timezone(
                        location['latitude'], location['longitude'] )
                    if timezone:
                        self.timezone = timezone
                        self.save()
        
    def icalendar( self, ical = None ): #{{{3
        """ returns an iCalendar object of the event entry or add it to 'ical'

        >>> events = Event.objects.filter( title='GridCalendar presentation',
        ...     dates__eventdate_name = 'start',
        ...     dates__eventdate_date = '2010-12-29' )
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
            ical.add('CALSCALE').value = 'GREGORIAN'
        vevent = ical.add('vevent')
        vevent.add('SUMMARY').value = self.title
        vevent.add('URL').value = 'http://' + \
            Site.objects.get_current().domain + self.get_absolute_url()
        if self.starttime:
            date_time = datetime.datetime.combine(
                    self.startdate, self.starttime )
            if not self.timezone:
                self.update_timezone()
            if self.timezone:
                timezone = pytz.timezone( self.timezone )
                loc_dt = timezone.localize( date_time )
                date_time = loc_dt.astimezone( pytz.utc )
            vevent.add('DTSTART').value = date_time
        else:
            vevent.add('DTSTART').value = self.startdate
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
        # calculate DTEND
        if self.enddate:
            enddate = self.enddate
        else:
            enddate = self.startdate
        if self.endtime:
            date_time = datetime.datetime.combine(
                    enddate, self.endtime )
            if self.timezone:
                timezone = pytz.timezone( self.timezone )
                loc_dt = timezone.localize( date_time )
                date_time = loc_dt.astimezone( pytz.utc )
            vevent.add('DTEND').value = date_time
        else:
            vevent.add('DTEND').value = enddate
        # calculate DESCRIPTION
        if self.description: vevent.add('DESCRIPTION').value = self.description
        # see rfc5545 3.8.7.2. Date-Time Stamp
        vevent.add('DTSTAMP').value = self.modification_time
        vevent.add('CLASS').value = 'PUBLIC'
        if self.coordinates:
            vevent.add('GEO').value = \
                unicode(self.coordinates.y) +u";"+ unicode(self.coordinates.x)
        # TODO: add eventdates. As VALARMs or there is something better in
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
        startdate, either 'title' or 'startdate' must be used in **kwargs.

        If ``self`` has a master in :class:`Recurrence`, the master
        of the returned clone in :class:`Recurrence` will be set to the same
        master.
        
        This method makes a clone of all related objects, and relates them to
        the new created clone, except for the models in ``except_models``,
        which are ignored.

        ``kwargs`` can contain field names and values to replace in the clone
        the original of ``self``, e.g. ``{"startdate": a_date}``

        >>> from events.models import Event
        >>> from django.utils.encoding import smart_str
        >>> import datetime
        >>> now_t = datetime.datetime.now().isoformat()
        >>> today = datetime.date.today()
        >>> today_t = today.isoformat()
        >>> user, c = User.objects.get_or_create( username = unicode(now_t) )
        >>> events = Event.objects.filter( title='GridCalendar presentation' )
        >>> if events: events.delete()
        >>> event = Event.parse_text(EXAMPLE)
        >>> event.enddate = None
        >>> clone = event.clone( user, startdate = today )
        >>> clone_text = clone.as_text()
        >>> clone_text = clone_text.replace(
        ...     today_t, event.startdate.isoformat(), 1 )
        >>> assert ( event.as_text() == clone_text )
        >>> event.delete()
        >>> clone.delete()
        """
        clone = Event()
        assert 'startdate' in self.get_simple_fields()
        assert 'enddate' in self.get_simple_fields()
        simple_fields_in_Event = [ f for f in self.get_simple_fields() if \
                f not in ('startdate', 'enddate') ]
        for field in simple_fields_in_Event:
            if kwargs.has_key( field ):
                setattr( clone, field, kwargs[field] )
            else: 
                setattr( clone, field, getattr(self, field) )
        # Dealing now with :attr:`Event.description` which is not returned by
        # :meth:`Event.get_simple_fields`
        assert u'description' in [unicode(f.name) for f in Event._meta.fields]
        if kwargs.has_key( 'description' ):
            clone.description = kwargs['description']
        else:
            clone.description = self.description
        clone.user = user
        clone.save() # we need the id to be able to save related objects
        # we deal now with startdate and enddate
        for field in ('startdate', 'enddate'):
            if kwargs.has_key( field ):
                setattr( clone, field, kwargs[field] )
            else: 
                setattr( clone, field, getattr(self, field) )
        # dealing with recurrence
        if recurrence:
            if self.recurring:
                # self is a recurrence of a serie
                if self.recurring.master == self:
                    # self is the master of the recurrence: we make clone a new
                    # recurrence of the serie
                    self.recurrences.create( event = clone )
                else: # self is a recurrence of another master
                    self.recurring.master.recurrences.create( event = clone )
            else:
                self.recurrences.create( event = clone )
        related_models = [EventDate, EventSession, EventUrl] # TODO: get the list automatically
        new_objs = [] # list of new related objects
        # we now traverse all related models and its objects
        for model in ( related_models ):
            if model == Event or model in except_models:
                continue
            # next line is not the proper thing to do hier because for
            # instance urls from clones of clone are also returned
            # for pk, obj in collected_objs[ model ].sub_objs.iteritems():
            assert hasattr( model, 'event' )
            for obj in model.objects.filter( event = self ):
                # for recurrences, we don't clone startdate, enddate and
                # ongoing in EventDate
                if recurrence and model == EventDate and \
                        obj.eventdate_name in ('start', 'end', 'ongoing'):
                    continue
                # Notice that in order for the next line to work, we expect
                # all models with a reference to Event to have a method called
                # ``clone`` with two parameters: an event (to reference to) and
                # a user
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
        return clone

    def set_tags( self, tags ): #{{{3
        "set tags"
        Tag.objects.update_tags( self, tags )

    def get_tags( self ): #{{{3
        "get tags"
        return Tag.objects.get_for_object( self )

    def __unicode__( self ): #{{{3
        return unicode(self.pk) + " " + self.title

    @models.permalink
    def get_absolute_url( self ): #{{{3
        "get URL of an event"
        return ( 'event_show_all', (), {'event_id': self.id,} )

    def delete( self, *args, **kwargs ): #{{{3
        """ it tests that ``self`` is not the master of a recurrence fixing it
        if it is. """
        if self.recurring and self == self.recurring.master:
            events = Event.objects.filter( _recurring__master = self)
            try:
                first = add_start(events.exclude( pk = self.pk )).order_by(
                        'start' )[0]
                recurrences = Recurrence.objects.filter( master = self )
                recurrences.update( master = first )
            except IndexError:
                pass
        # Call the "real" delete() method:
        super( Event, self ).delete( *args, **kwargs )

    def save( self, *args, **kwargs ): #{{{3
        """ Marks an event as new or not (for :meth:`Event.post_save`),
        and update the master of a recurrence if appropiate."""
        # FIXME: increase version field of all events in the recurring serie
        try:
            Event.objects.get( id = self.id )
            self.not_new = True # Event.post_save uses this
        except Event.DoesNotExist:
            pass
        if self.recurring:
            master = self.recurring.master
            if self.startdate < master.startdate:
                # self is going to be the new master of the serie. The master
                # is by convention the first event of a serie.
                master.recurrences.all().update( master = self )
        self.version = self.version + 1
        # Call the "real" save() method:
        super( Event, self ).save( *args, **kwargs )
        # deletes caches
        if hasattr( self, 'startdate_cache'):
            delattr( self, 'startdate_cache')
        if hasattr( self, 'enddate_cache'):
            delattr( self, 'enddate_cache')
        if hasattr( self, 'upcomingdate_cache'):
            delattr( self, 'upcomingdate_cache')

    @staticmethod # def post_save( sender, **kwargs ): {{{3
    def post_save( sender, **kwargs ):
        """ notify users if a filter of a user matches an event but only for
        new events.
        """
        event = kwargs['instance']
        if event.recurring:
            # this event is an instance of a serie of recurring events
            return
        if hasattr(event, "not_new") and event.not_new:
            return
        notify_users_when_wanted.delay( event = event )

    @staticmethod # def example(): {{{3
    def example():
        """ returns an example of an event as unicode
        
        >>> from django.utils.encoding import smart_str
        >>> example = Event.example()
        >>> event = Event.parse_text(example)
        >>> assert smart_str(example) == event.as_text()
        >>> event.delete()
        >>> text = example.replace(u'DE', u'Germany')
        >>> event = Event.parse_text(text)
        >>> assert (smart_str(example) == event.as_text())
        >>> event.delete()
        >>> text = text.replace(u'Germany', u'de')
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
                to_return += keyword + ": " + self.title + "\n"
            elif keyword == u'startdate':
                to_return += keyword + ": " + \
                    unicode(self.startdate.strftime( "%Y-%m-%d" )) + "\n"
            elif keyword == u'starttime':
                if self.starttime:
                    to_return += keyword + ": " + \
                        unicode(self.starttime.strftime( "%H:%M" )) + "\n"
            elif keyword == u'enddate':
                if self.enddate:
                    to_return += keyword + ": " + \
                        unicode(self.enddate.strftime( "%Y-%m-%d")) + "\n"
            elif keyword == u'endtime':
                if self.endtime:
                    to_return += keyword + ": " + \
                        unicode(self.endtime.strftime( "%H:%M" )) + "\n"
            elif keyword == u'timezone':
                if self.timezone:
                    to_return += keyword + ": " + self.timezone + "\n"
            elif keyword == u'country':
                if self.country:
                    to_return += keyword + ": " + self.country + "\n"
            elif keyword == u'coordinates':
                if self.coordinates:
                    to_return += u"coordinates: %s, %s\n" % (
                            unicode( self.coordinates.y ),
                            unicode( self.coordinates.x ) )
            elif keyword == u'acronym':
                if self.acronym:
                    to_return += keyword + u": " + self.acronym + "\n"
            elif keyword == u'tags':
                if self.tags:
                    to_return += keyword + u": " + self.tags + "\n"
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
            elif keyword == u'dates':
                eventdates = EventDate.objects.filter(
                        Q( event = self.id ) &
                        ~Q( eventdate_name__in = EventDate.reserved_names() ) )
                if eventdates and len( eventdates ) > 0:
                    to_return += u"dates:\n"
                    for eventdate in eventdates:
                        to_return += u"    " + \
                            eventdate.eventdate_date.strftime("%Y-%m-%d") + \
                            '    ' + eventdate.eventdate_name + "\n"
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
        >>> s[u'enddate']
        u'2010-12-30'
        >>> s[u'endtime']
        u'18:00'
        >>> s[u'coordinates']
        u'52.55247, 13.40364'
        >>> s[u'postcode']
        u'10439'
        >>> s[u'startdate']
        u'2010-12-29'
        >>> s[u'starttime']
        u'10:00'
        >>> s[u'tags']
        u'calendar software open-source gridmind gridcalendar'
        >>> s[u'title']
        u'GridCalendar presentation'
        >>> c[u'description'][1]
        u'GridCalendar will be presented'
        >>> c[u'dates'][1].replace(' ','')
        u'2009-11-01visitortickets'
        >>> c[u'dates'][2].replace(' ','')
        u'2010-10-01callforpapers'
        >>> c['dates'][3]
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
        # used to know if a key appears more than one:
        field_names = set( simple_list + complex_list )
        assert len( field_names ) == len( simple_list ) + len( complex_list )
        # field names and synonyms as keys, field names as values:
        syns = Event.get_synonyms()
        current = None # current field being parsed
        lines = list() # lines belonging to current field
        field_p = re.compile(r"(^[^\s:]+)\s*:\s*(.*?)\s*$")
        # group 1 is the name of the field, group 2 is the value
        empty_line_p = re.compile(r"^\s*$")
        line_counter = 0
        # we test that there is a field called 'description' because we are
        # going to use it, i.e. it is hardcoded in the code below:
        assert filter( lambda x: x == 'description', complex_list)
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
                            u"extra lines for %(field_name)s must start with " \
                            u"identation") % {'field_name': current,})
                    lines.append(line)
                    continue
            if (not current) and not field_m:
                raise ValidationError(_(
                        "line number %(number)d is wrong: %(line)s") % \
                                {'number': line_counter, 'line': line})
            if not syns.has_key(field_m.group(1).lower()):
                raise ValidationError(_(u"wrong field name: ") + field_m.group(1))
            # checks no duplicity
            if not current:
                if not syns[field_m.group(1).lower()] in field_names:
                    raise ValidationError(
                        _(u"field '%(field_name)s' is defined more than one") %
                        {'field_name': syns[field_m.group(1).lower()],} ) #
                        # TODO: show line number and line in errors
                else:
                    field_names.discard( syns[field_m.group(1).lower()] )
            # checks simple field
            if syns[field_m.group(1).lower()] in simple_list:
                simple_dic[ syns[field_m.group(1).lower()] ] = field_m.group(2)
                continue
            # checks complex field
            if not syns[field_m.group(1).lower()] in complex_list:
                raise RuntimeError("field %s was not in 'complex_list'" %
                        field_m.group(1))
            current = syns[field_m.group(1).lower()]
            lines.append( line[ len(field_m.group(1))+1 : ].lstrip() )
        if current:
            complex_dic[current] = lines
        return simple_dic, complex_dic

    # parse_text {{{3
    @staticmethod
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

        The text for the field 'dates' is of the form::

            dates: deadline_date
                date_1 name_1
                date_2 name_2
                ...

        The idented lines are optional when deadline_date is present, which
        will be saved with the eventdate_name 'deadline'

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
            # NOTE: the following line can raise a User.DoesNotExist
            user = User.objects.get(id = user_id)
        else:
            user = None
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
            lines_d = complex_fields[u'description']
            if len( lines_d ) > 0:
                if lines_d[0].strip():
                    event_form.data['description'] = u"\n".join( lines_d )
                elif len( lines_d ) > 1:
                    event_form.data['description'] = u"\n".join( lines_d[1:] )
            del complex_fields[u'description']
        # testing data
        if not event_form.is_valid():
            raise ValidationError(event_form.errors.as_text())
        # create a preliminary event from the form
        event = event_form.save(commit = False)
        if user and not event_id:
            # event.user is the user who created the event, we add her/him if
            # the user is present and the event is new (event_id = None)
            event.user = user
        event.save()
        # save startdate (and enddate if present and != startdate)
        startdate = event_form.cleaned_data.get('startdate', None)
        if startdate:
            try: 
                eventdate = EventDate.objects.get( event = event,
                        eventdate_name = 'start' )
                if eventdate.eventdate_date != startdate:
                    eventdate.eventdate_date = startdate
                    eventdate.save()
            except EventDate.DoesNotExist:
                EventDate.objects.create( event = event,
                        eventdate_name = 'start', eventdate_date = startdate )
        enddate = event_form.cleaned_data.get('enddate', None)
        if enddate:
            if enddate != startdate:
                try: 
                    eventdate = EventDate.objects.get( event = event,
                            eventdate_name = 'end' )
                    if eventdate.eventdate_date != enddate:
                        eventdate.eventdate_date = enddate
                        eventdate.save()
                except EventDate.DoesNotExist:
                    EventDate.objects.create( event = event,
                            eventdate_name = 'end', eventdate_date = enddate )
            else:
                try: 
                     eventdate = EventDate.objects.get( event = event,
                            eventdate_name = 'end' )
                     eventdate.delete()
                except EventDate.DoesNotExist:
                    pass
        else:
            # we delete the enddate if there was one
            try:
                enddate = EventDate.objects.get(
                        event = event, eventdate_name = 'end' )
                enddate.delete()
            except EventDate.DoesNotExist:
                pass
        # urls {{{5
        if complex_fields.has_key(u'urls'):
            urls = EventUrl.get_urls( complex_fields[u'urls'] )
            event_urls_final = list() # stores EventURLs to be saved at the end
            for url_name, url in urls.items():
                try:
                    previous_event_url = EventUrl.objects.get(
                            event=event, url_name=url_name)
                except EventUrl.DoesNotExist:
                    event_url = EventUrl(event=event, url_name=url_name, url=url)
                    # see
                    # http://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects
                    event_url.full_clean()
                    event_urls_final.append(event_url)
                else:
                    previous_event_url.url = url
                    assert(previous_event_url.url_name == url_name)
                    assert(previous_event_url.event == event)
                    previous_event_url.full_clean()
                    event_urls_final.append(previous_event_url)
            assert(len(event_urls_final) == len(urls))
            # save all
            for event_url in event_urls_final:
                event_url.save()
            # delete old urls of the event which are not in ``text`` parameter
            EventUrl.objects.filter(event=event).exclude(
                    pk__in = [ eu.pk for eu in event_urls_final ] ).delete()
            del complex_fields[u'urls']
        # dates {{{5
        if complex_fields.has_key(u'dates'):
            eventdates = EventDate.get_eventdates( complex_fields[u'dates'] )
            eventdates_final = list() # stores EventDate instances to be saved
            reserved_names = EventDate.reserved_names()
            for name, date in eventdates.items():
                if name in reserved_names:
                    raise ValidationError(
                        _(u"the name '%(name)s' for a date is not allowed") %
                            {'name': name,} )
                try:
                    previous_eventdate = EventDate.objects.get(
                            event=event, eventdate_name=name)
                    if previous_eventdate.eventdate_date != date:
                        previous_eventdate.eventdate_date = date
                        previous_eventdate.full_clean()
                        eventdates_final.append( previous_eventdate )
                except EventDate.DoesNotExist:
                    eventdate = EventDate(event=event, eventdate_name=name,
                            eventdate_date=date)
                    # see
                    # http://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects
                    eventdate.full_clean()
                    eventdates_final.append(eventdate)
            # save all
            for eventdate in eventdates_final:
                eventdate.save()
            # delete old eventdates of the event which are not in ``text`` parameter
            all_eventdates = EventDate.objects.filter(event=event)
            for eventdate in all_eventdates:
                name = eventdate.eventdate_name
                if ( name not in reserved_names ) and \
                        not eventdates.has_key(name):
                    eventdate.delete()
            del complex_fields[u'dates']
        # sessions {{{5
        if complex_fields.has_key(u'sessions'):
            sessions_in_text = \
                    EventSession.get_sessions( complex_fields[u'sessions'] )
            # stores EventSessions to be saved at the end
            event_sessions_to_save = list()
            for session in sessions_in_text:
                if session.date < event.startdate:
                    raise ValidationError( _("the following session's " \
                        "date is before the start date of the event, " \
                        "which is not allowed: %s") % session.name )
                try:
                    # check if there is an EventSession with the same name
                    previous_event_session = EventSession.objects.get(
                            event = event, session_name = session.name)
                    # check that the session date is not before the startdate
                    previous_event_session.session_date = session.date
                    previous_event_session.session_starttime = session.start
                    previous_event_session.session_endtime = session.end
                    # http://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects
                    previous_event_session.full_clean()
                    event_sessions_to_save.append( previous_event_session )
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
                    event_sessions_to_save.append(event_session)
            # save all
            for event_session in event_sessions_to_save:
                event_session.save()
            # delete old sessions of the event which are not in ``text`` parameter
            EventSession.objects.filter( event = event ).exclude(
                pk__in = [ es.pk for es in event_sessions_to_save ] ).delete()
            del complex_fields[u'sessions']
        # recurrences {{{5
        from forms import DatesTimesField
        if complex_fields.has_key(u'recurrences'):
            dates = list()
            for text_date in complex_fields[u'recurrences'][1:]:
                dates_times_field = DatesTimesField()
                try:
                    dates_times = dates_times_field.clean( text_date )
                except ValidationError:
                    raise ValidationError( _(
                        u'date not in iso format (yyyy-mm-dd): %(date)s') % \
                                {'date': text_date} )
                if dates_times.has_key('enddate'):
                    raise ValidationError( _(
                        u'a repeating date cannot have an end date: (date)s') % \
                                {'date': text_date} )
                # we do not clone dates nor sessions, as they 
                # refer to the main event and not to the recurring events.
                # TODO: inform the user
                event.clone( user = user,
                        except_models = [EventDate, EventSession],
                        **dates_times )
            del complex_fields[u'recurrences']
        # test and return event {{{5
        assert(len(complex_fields) == 0)
        # startdate_cache avoids to query the DB, see
        # :meth:`Event._get_startdate`
        event.startdate_cache = startdate
        # enddate_cache avoids to query the DB, see
        # :meth:`Event._get_enddate`
        event.enddate_cache = enddate
        return event

    @staticmethod # def get_complex_fields(): {{{3
    def get_complex_fields():
        """ returns a tuple of names of user-editable fields (of events) which
        can contain many lines in the input text representation of an Event.
        """
        return ("urls", "dates", "sessions", "recurrences", "description",)

    @staticmethod # def get_simple_fields(): {{{3
    def get_simple_fields():
        """ returns a tuple of names of user-editable fields (of events) which
        have only one line in the input text representation of an Event.
        """ 
        field_names = [unicode(f.name) for f in Event._meta.fields]
        field_names.append(u'startdate')
        field_names.append(u'enddate')
        field_names.remove(u"id")
        field_names.remove(u"user")
        field_names.remove(u"creation_time")
        field_names.remove(u"modification_time")
        field_names.remove(u"description")
        field_names.remove(u"version")
        return tuple(field_names)
 
    @staticmethod # def get_necessary_fields(): {{{3
    def get_necessary_fields():
        """ returns a tuple of names of the necessary filed fields of an event.
        """
        return (u"title", u"startdate", u"tags", u"urls")

    @staticmethod # def get_priority_list(): #{{{3
    def get_priority_list():
        """ returns a tuple of names of fields in the order they
        should appear when showing an event as a text, i.e. in the output text
        representation of an Event.
        
        Notice that 'recurrences' can be present in the input text
        representation, but it is not present in the output text
        representation.
 
        >>> gpl_len = len(Event.get_priority_list())  # 17
        >>> gsf_len = len(Event.get_simple_fields())  # 13
        >>> gcf_len = len(Event.get_complex_fields()) #  5 recurring not in gpl
        >>> assert(gpl_len + 1 == gsf_len + gcf_len)
        >>> synonyms_values_set = set(Event.get_synonyms().values())
        >>> assert(gpl_len + 1  == len(synonyms_values_set))
        """
        return ( u"acronym", u"title", u"startdate", u"starttime", u"enddate",
                u"endtime", u"timezone", u"tags", u"urls", u"address",
                u"postcode", u"city", u"country", u"coordinates", u"dates",
                u"sessions", u"description" )
 
    @staticmethod # def get_synonyms(): {{{3
    def get_synonyms():
        """Returns a dictionay with names (strings) and the fields (strings)
        they refer.

        All values of the returned dictionary (except recurrences, urls,
        sessions, dates, start and end) are names of fields of the Event class.

        >>> synonyms_values_set = set(Event.get_synonyms().values())
        >>> assert ('urls' in synonyms_values_set)
        >>> synonyms_values_set.remove('urls')
        >>> assert ('dates' in synonyms_values_set)
        >>> synonyms_values_set.remove('dates')
        >>> assert ('sessions' in synonyms_values_set)
        >>> synonyms_values_set.remove('sessions')
        >>> assert ('recurrences' in synonyms_values_set)
        >>> synonyms_values_set.remove('recurrences')
        >>> field_names = [f.name for f in Event._meta.fields]
        >>> field_names_set = set(field_names)
        >>> field_names_set.remove('id')
        >>> field_names_set.remove('user')
        >>> field_names_set.remove('creation_time')
        >>> field_names_set.remove('modification_time')
        >>> field_names_set.remove('version')
        >>> field_names_set.add('startdate')
        >>> field_names_set.add('enddate')
        >>> assert field_names_set == synonyms_values_set
        """
        if settings.DEBUG:
            # ensure you don't override a key
            def add( dictionary, key, value ):
                """ assert that the key is not already there """
                assert not dictionary.has_key( key ), key
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
            follow=[ "urls_set", "sessions_set", "dates_set" ] )

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

#class RecurrenceManager( models.Manager ): #{{{1
#    def get_by_natural_key(self, event):
#        return self.get( event = Event.get_by_natural_key( *event ) )

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

    If we have an event ``e`` with a master ``m`` (``e`` is a recurrence of a
    serie with ``m`` as master), we can get its master with::

        e.recurring.master

    For a master of a serie::

        e.recurring.master == e

    To get all events of a serie with ``m`` as master::

        Event.objects.filter( _recurring__master = m )

    To get all recurrences of an event (``m``) which is a master::

        m.recurrences.all()

    The above code returns an empty list if there is no event with ``m`` as
    master.

    To count the number of recurrences (more efficient than retrieving them)::

        m.recurrences.count()

    If we have an event ``m``, we attach an instance (``e``) to a serie
    having ``m`` as master with::

        m.recurrences.create(event = e)

    To change a master::

        event.recurring.master = new_master
        event.recurring.save()

    >>> import datetime
    >>> from datetime import timedelta
    >>> today = datetime.date.today()
    >>> tomorrow = timedelta(days=1) + today
    >>> after_tomorrow = timedelta(days=2) + today
    >>> e1 = Event.objects.create(title="Re1" )
    >>> e1.startdate = today
    >>> e2 = Event.objects.create(title="Re2" )
    >>> e2.startdate = tomorrow
    >>> e3 = Event.objects.create(title="Re3" )
    >>> e3.startdate = after_tomorrow
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
    >>> # we now put e2 start in the past and check that master is updated
    >>> e2.startdate = timedelta(days=-1)+today
    >>> e2.save()
    >>> e1 = Event.objects.get( title="Re1" )
    >>> e2 = Event.objects.get( title="Re2" )
    >>> e3 = Event.objects.get( title="Re3" )
    >>> assert e1.recurring.master == e2
    >>> assert e2.recurring.master == e2
    >>> assert e3.recurring.master == e2
    >>> event_list = [r.event for r in e2.recurrences.all()]
    >>> assert e1 in event_list
    >>> assert e2 in event_list
    >>> assert e3 in event_list
    >>> e2.recurrences.count()
    3
    >>> # we now check that master is updated when master is deleted
    >>> e2.delete()
    >>> e1 = Event.objects.get( title="Re1" )
    >>> e3 = Event.objects.get( title="Re3" )
    >>> assert e1.recurring.master == e1
    >>> assert e3.recurring.master == e1
    >>> e3.delete()
    >>> e1.delete()
    """
    # NOTE that it would be possible to just have an attribute ``master`` in
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

    #objects = RecurrenceManager()

    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        verbose_name = _( u'Recurrence' )
        verbose_name_plural = _( u'Recurrences' )
        # see http://docs.djangoproject.com/en/1.3/ref/models/options/#order-with-respect-to
        # order_with_respect_to = 'master'

    #def natural_key( self ):
    #    return self.event.natural_key()
    #natural_key.dependencies = ['events.event']

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
        # we call Event.save to update Event.version and to update masters if
        # necessary
        self.event.save()

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
    >>> event = Event(title="test for ExtendedUser " + now, tags = "test" )
    >>> event.save()
    >>> event.startdate = datetime.date.today()
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
        (start, end or a date in the future)
        """
        for group in self.get_groups():
            if group.has_coming_events():
                return True
        return False

#class EventUrlManager( models.Manager ): # {{{1
#    def get_by_natural_key(self, url_name, event):
#        return self.get(
#                url_name = url_name,
#                event = Event.objects.get_by_natural_key( *event ) )

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

    #objects = EventUrlManager()

    class Meta: # pylint: disable-msg=C0111
        ordering = ['url_name']
        unique_together = ( "event", "url_name" )

    #def natural_key( self ):
    #    return ( self.url_name, self.event.natural_key() )
    #natural_key.dependencies = ['events.event']

    def save( self, *args, **kwargs ):
        super( EventUrl, self ).save( *args, **kwargs )
        # we update Event.version
        event_queryset = Event.objects.filter( pk = self.event.pk )
        event_queryset.update( version = self.event.version + 1 )

    def __unicode__( self ): # {{{2
        return self.url

    def clone( self, event, user ): # {{{2
        """ creates a copy of itself related to ``event`` """
        new = EventUrl( event = event, url_name = self.url_name, url = self.url )
        new.save()
        return new

    @staticmethod # def get_urls( text ): {{{2
    def get_urls( lines ):
        """ validates text lines containing EventUrl entries, raising
        ValidationErrors if there are errors, otherwise it returns a dictionary
        with names and urls (both unicode objects).

        If ``line[0]`` is not empty it is the default url.
        """
        urls = {} # keys are url-names, values are urls
        if lines[0].strip():
            urls['url'] = lines[0].strip() # default url
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
                                    u'%(name)s') % {'name': name} )
                urls[name] = field_m.group(2)
        # we now check each url using the validators of this class and
        # events.forms.URLValidatorExtended
        errors = []
        url_validators = EventUrl._meta.get_field_by_name('url')[0].validators
        from gridcalendar.events.forms import URLValidatorExtended
        url_validators.append( URLValidatorExtended() )
        url_name_validators = \
                EventUrl._meta.get_field_by_name('url_name')[0].validators
        for url_name, url in urls.items():
            for val in url_name_validators:
                try:
                    val( url_name )
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

#class EventDateManager( models.Manager ): # {{{1
#    def get_by_natural_key(self, eventdate_name, event):
#        return self.get(
#                eventdate_name = eventdate_name,
#                event = Event.objects.get_by_natural_key( *event ) )

class EventDate( models.Model ): # {{{1
    """ stores dates for events """
    eventdate_date = models.DateField( _( u'Date' ), blank = False,
            null = False, db_index = True, validators = [validate_year] )
    eventdate_name = models.CharField( 
            _( u'Name' ), blank = False, null = False,
            max_length = 80, help_text = _( 
            "Example: call for papers" ) )
    event = models.ForeignKey( Event, related_name = 'dates' )

    objects = models.GeoManager()
#    objects = EventDateManager()

    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        ordering = ['eventdate_date']
        unique_together = ( "event", "eventdate_name", "eventdate_date" )

    def save( self, *args, **kwargs ): #{{{3
        assert 'start' in self.reserved_names()
        assert 'end' in self.reserved_names()
        assert 'ongoing' in self.reserved_names()
        # checkings {{{4
        if self.eventdate_name == 'start':
            # we check that, if there is an end, it is after the start
            try:
                end = EventDate.objects.get(
                        event = self.event,
                        eventdate_name = 'end' )
                if end.eventdate_date <= self.eventdate_date:
                    raise RuntimeError( unicode(self.event) +
                            " was going to have an end not after start" )
            except EventDate.DoesNotExist:
                pass
        elif self.eventdate_name == 'end':
            # we check that, if there is a start, it is before the end
            try:
                start = EventDate.objects.get(
                        event = self.event,
                        eventdate_name = 'start' )
                if start.eventdate_date >= self.eventdate_date:
                    raise RuntimeError( unicode(self.event) +
                            " was going to have a start not before end" )
            except EventDate.DoesNotExist:
                pass
        elif self.eventdate_name == 'ongoing':
            # we check that 'ongoing' is after start
            start = self.event.startdate
            if not start:
                raise RuntimeError( unicode(self.event) +
                        " was going to have an ongoing without a start" )
            if start >= self.eventdate_date:
                raise RuntimeError( unicode(self.event) +
                        " was going to have an ongoing before start" )
            # we check that 'ongoing' is before end
            end = self.event.enddate
            if not end:
                raise RuntimeError( unicode(self.event) +
                        " was going to have an ongoing without an end" )
            if end <= self.eventdate_date:
                raise RuntimeError( unicode(self.event) +
                        " was going to have an ongoing after end" )
        super( EventDate, self ).save( *args, **kwargs ) # {{{4
        # adding missing ongoing dates {{{4
        # if it is and end-date, we add missing ongoing-dates:
        if self.eventdate_name == 'end':
            end = self.eventdate_date
            start = self.event.startdate
            ongoings = EventDate.objects.filter(
                    event = self.event, eventdate_name = 'ongoing' )
            dates = [ start + datetime.timedelta(days=x) for x in
                    range( 1, (end - start).days) ]
            for date in dates:
                EventDate.objects.get_or_create(
                        event = self.event,
                        eventdate_name = 'ongoing',
                        eventdate_date = date )
                # TODO: the above can be done more efficiently, see
                # http://stackoverflow.com/questions/2252530/efficent-way-to-bulk-insert-with-get-or-create-in-django-sql-python-django
        # we call Event.save to update Event.version {{{4
        # we update Event.version
        event_queryset = Event.objects.filter( pk = self.event.pk )
        event_queryset.update( version = self.event.version + 1 )

    #def natural_key( self ):
    #    return ( self.eventdate_name, self.event.natural_key() )
    #natural_key.dependencies = ['events.event']
    
    def __unicode__( self ): # {{{2
        return unicode( self.eventdate_date ) + u'    ' + self.eventdate_name

    def clone( self, event, user ): # {{{2
        """ creates a copy of itself related to ``event`` """
        new = EventDate( event = event, eventdate_name = self.eventdate_name,
                eventdate_date = self.eventdate_date )
        new.save()
        return new

    @staticmethod # def reserved_names: {{{2
    def reserved_names():
        """ tuple with the names of reserved eventdate_names (start,
        end, ongoing) """
        return ('start', 'end', 'ongoing')

    @staticmethod # def get_eventdates( text ): {{{2
    def get_eventdates( lines ):
        """ validates text lines containing EventDate entries,
        raising ValidationErrors if there are errors, otherwise it returns a
        dictionary with names and dates. """
        # TODO: this code can be simplified using only the django validators
        names_dates = {} # keys are names, values are dates
        errors = [] # we store here errors
        date_field = DateField()
        # default date (deadline):
        if lines[0].strip():
            try:
                date = date_field.clean( lines[0].strip() )
            except:
                raise ValidationError(
                        _(u"default date (deadline) is not a valid date: %s") %
                        lines[0].strip() )
            names_dates['deadline'] = date
        field_p = re.compile(r"^\s+(\d\d\d\d)-(\d?\d)-(\d?\d)\s+(.*?)\s*$")
        if len(lines) > 1:
            for line in lines[1:]:
                field_m = field_p.match(line)
                if not field_m:
                    raise ValidationError(
                        _(u"the following line for a date is malformed: ")
                        + line)
                name = field_m.group(4)
                if names_dates.has_key( name ):
                    errors.append( _(u'the following date name appers ' \
                            u'more than one: %(name)s') % {'name': name} )
                elif name.lower() in EventDate.reserved_names():
                    errors.append( _(u"the name '%(name)s' is not allowed") %
                            {'name': name,} )
                else:
                    try:
                        names_dates[ field_m.group(4) ] = datetime.date(
                                int(field_m.group(1)), int(field_m.group(2)),
                                int(field_m.group(3)))
                    except (TypeError, ValueError), e:
                        errors.append(
                            _(u"The date '%(eventdate_name)s' is not " \
                                    u"correct") % {'eventdate_name':
                                        field_m.group(4),} )
        if errors:
            raise ValidationError( errors )
        # we now check each date using django.core.validators for the
        # fields of this class
        eventdate_date_validators = EventDate._meta.get_field_by_name(
                'eventdate_date')[0].validators
        eventdate_name_validators = EventDate._meta.get_field_by_name(
                'eventdate_name')[0].validators
        for eventdate_name, eventdate_date in names_dates.items():
            for val in eventdate_name_validators:
                try:
                    val(eventdate_name)
                except ValidationError, e:
                    errors.append(
                            _('Error in date name %(eventdate_name)s') %
                            {'eventdate_name': eventdate_name,} )
                    errors.extend( e.messages )
            for val in eventdate_date_validators:
                try:
                    val(eventdate_date)
                except ValidationError, e:
                    errors.append( _('Error in date %(date)s') %
                            {'date': eventdate_date,} )
                    errors.extend( e.messages )
        if errors:
            raise ValidationError( errors )
        return names_dates

if not reversion.is_registered( EventDate ): # {{{1
    reversion.register( EventDate, format = 'yaml' )
    # see https://github.com/etianen/django-reversion/wiki/Low-Level-API

#class EventSessionManager( models.Manager ): # {{{1
#    def get_by_natural_key(self, session_name, event):
#        return self.get(
#                session_name = session_name,
#                event = Event.objects.get_by_natural_key( *event ) )

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

    #objects = EventSessionManager()

    #def natural_key( self ):
    #    return ( self.session_name, self.event.natural_key() )
    #natural_key.dependencies = ['events.event']

    class Meta: # {{{2 pylint: disable-msg=C0111,W0232,R0903
        ordering = ['session_date', 'session_starttime']
        unique_together = ( "event", "session_name" )
        verbose_name = _( u'Session' )
        verbose_name_plural = _( u'Sessions' )

    def save( self, *args, **kwargs ): #{{{3
        super( EventSession, self ).save( *args, **kwargs )
        # we update Event.version
        event_queryset = Event.objects.filter( pk = self.event.pk )
        event_queryset.update( version = self.event.version + 1 )

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
    def get_sessions( lines ):
        """ validates text lines containing EventSession entries,
        raising ValidationErrors if there are errors, otherwise it returns a
        dictionary with session names as keys and Session instances as values.
        """
        # TODO: simplify this code using the sessions form to validate data.
        # The form  should include validation code that check for instance that
        # the start time is before the end time, etc. See
        # http://docs.djangoproject.com/en/1.2/ref/forms/api/#using-forms-to-validate-data
        if lines[0].strip():
            raise ValidationError(_(u"first line for sessions was not empty"))
        if len ( lines ) < 2:
            raise ValidationError(
                    _(u"there is no sessions data") )
        syns = Event.get_synonyms()
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
                        u' %(name)s') % {'name': name} )
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
        from gridcalendar.events.search import search_events
        return search_events( self.query, related = False )

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
        ...     tags = "test" )
        >>> event.startdate = timedelta(days=-1)+today
        >>> eventdate = EventDate(
        ...         event = event, eventdate_name = "test",
        ...         eventdate_date = today)
        >>> eventdate.save()
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
        >>> event.delete()
        >>> group.delete()
        """
        # body {{{3
        from gridcalendar.events.search import search_events
        qset = search_events( query, related = False ).filter(pk = event.id)
        if qset.exists():
            return True
        return False
        # EFFICIENCY: a much more efficient way would be to check manually
        # everything here, but then every change in
        # :meth:`search.search` would cause changes here and
        # comparing and adapting both methods would be very time consuming and
        # error-pround. We had a long code here until charset 336:e725aaa6a108


    def matches_count( self ): # {{{2
        """ returns the number of events which would be returned without
        *count* by :meth:`search.search` """
        from gridcalendar.events.search import search_events
        return search_events( self.query ).count()

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
    ...     tags = "test" )
    >>> event.save()
    >>> event.startdate = timedelta(days=-1)+today
    >>> eventdate = EventDate(
    ...         event = event, eventdate_name = "test",
    ...         eventdate_date = today)
    >>> eventdate.save()
    >>> calendar = Calendar.objects.create( group = group,
    ...     event = event )
    >>> assert ( len(group.get_coming_events()) == 1 )
    >>> assert ( group.has_coming_events() )
    >>> assert ( len(group.get_users()) == 0 )
    >>> user = User.objects.create(username = now)
    >>> membership = Membership.objects.create(group = group, user = user)
    >>> assert ( len(group.get_users()) == 1 )
    >>> event.delete()
    """
    # TODO test names with special characters including urls like grical.org/group_name
    name = models.CharField( _( u'Name' ), max_length = 80, unique = True,
            validators = [ RegexValidator(
                re.compile(r'.*[^0-9].*'),
                message = _(u'a group name must contain at least one ' \
                        u'character which is not a number') ) ] )
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
        """ Returns a list of maximal ``limit`` events with at least one date
        in the future. If ``limit`` is -1 it returns all.

        """
        today = datetime.date.today()
        events = Event.objects.filter( Q(calendar__group = self) & (
                    Q(dates__eventdate_date__gte = today) )).distinct()
        events = add_upcoming( events ).order_by('upcoming')
        if limit == -1:
            return events
        else:
            return events[0:limit]

    def has_coming_events(self): # {{{2
        """ returns True if the group has coming events (with a date
        of an event of the group in the future)
        """
        today = datetime.date.today()
        return Event.objects.filter(
                Q( calendar__group = self ) &
                Q( dates__eventdate_date__gte = today) ).exists()

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

def add_start( queryset ): #{{{1
    """ returns a new queryset adding a join query to ``queryset``
    (Event or EventDate as model) which include the ``start`` date
    of each event """
    if queryset.model == EventDate:
        return queryset.extra(select={'start':
            "SELECT T2.eventdate_date FROM events_eventdate T2 WHERE " \
            "T2.event_id = events_eventdate.event_id and " \
            "T2.eventdate_name = 'start'"})
    elif queryset.model == Event:
        return queryset.extra(select={'start':
            "SELECT eventdate_date FROM events_eventdate WHERE " \
            "events_event.id = events_eventdate.event_id and " \
            "eventdate_name = 'start'"})
    else:
        raise RuntimeError('queryset.model was either EventDate nor Event')

def add_end( queryset ): #{{{1
    """ returns a new queryset adding a join query to ``queryset``
    (Event or EventDate as model) which include the ``end`` date
    of each event """
    if queryset.model == EventDate:
        return queryset.extra(select={'end':
            "SELECT T2.eventdate_date FROM events_eventdate T2 WHERE " \
            "T2.event_id = events_eventdate.event_id and " \
            "T2.eventdate_name = 'end'"})
    elif queryset.model == Event:
        return queryset.extra(select={'end':
            "SELECT eventdate_date FROM events_eventdate WHERE " \
            "events_event.id = events_eventdate.event_id and " \
            "eventdate_name = 'end'"})
    else:
        raise RuntimeError('queryset.model was either EventDate nor Event')

def add_upcoming( queryset ): #{{{1
    if queryset.model == Event:
        return queryset.annotate( upcoming = Min('dates__eventdate_date') )
    else:
        raise RuntimeError('queryset.model was not Event')

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
if settings.LOG_PIPE and not settings.DEBUG:
    def write_to_pipe( **kwargs ): # {{{2
        from gridcalendar.events.models import Event, RevisionInfo
        site = Site.objects.get_current().domain
        # comment {{{3
        if kwargs['sender'] == Comment:
            comment = kwargs['comment']
            log_using_celery.delay( u'http://%(site)s%(comment_url)s\n' \
                '*** %(comment)s ***\n' % {
                    'site': site,
                    'comment_url': comment.get_absolute_url(),
                    'comment': comment.comment, } )
        # event created/updated {{{3
        elif kwargs['sender'] == RevisionInfo:
            revision_info = kwargs['instance']
            revision = revision_info.revision
            event_content_type = ContentType.objects.get_for_model( Event )
            text = u''
            # in a revision there can be more than one event, e.g. when
            # recurring events are introduced with a text form.
            for event_version in revision.version_set.filter(
                    content_type = event_content_type ):
                try:
                    event = Event.objects.get( pk = event_version.object_id )
                except Event.DoesNotExist:
                    # this happens when an event has been deleted
                    return
                event_url = event.get_absolute_url()
                # TODO: optimize the next code to hit the db less
                text += u'http://%(site)s%(event_url)s\n' % {
                        'site': site, 'event_url': event_url }
                revisions = [ version.revision for version in
                    Version.objects.get_for_object( event ) ]
                if len( revisions ) > 1:
                    rev_info_old = revisions[-2].revisioninfo_set.all()
                    rev_info_new = revisions[-1].revisioninfo_set.all()
                    diff = text_diff(
                            rev_info_old[0].as_text,
                            rev_info_new[0].as_text )
                    text += diff
                else:
                    text += smart_unicode( event.as_text() )
            log_using_celery.delay( text )
        # event deleted {{{3
        elif kwargs['sender'] == Event:
            event = kwargs['instance']
            deleted_url = reverse( 'event_deleted',
                    kwargs={'event_id': event.id,} )
            log_using_celery.delay( u'http://%(site)s%(deleted_url)s\n' % {
                'site': unicode( site ), 'deleted_url': deleted_url, } )
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
                        log_using_celery.delay(
                            u'http://%(site)s%(history_url)s\n' % {
                            'site': site, 'history_url': history_url, } )
                    return
                previous = revision
    # connecting to signals {{{2
    post_save.connect( write_to_pipe,
            sender = RevisionInfo,
            #weak = False,
            dispatch_uid = 'pipe_logger_revisioninfo' )
    comment_was_posted.connect( write_to_pipe,
            sender = Comment,
            #weak = False,
            dispatch_uid = 'pipe_logger_comment' )
    post_delete.connect( write_to_pipe,
            sender = Event,
            #weak = False,
            dispatch_uid = 'pipe_logger_event_deleted' )
    post_save.connect( write_to_pipe,
            sender = Version,
            #weak = False,
            dispatch_uid = 'pipe_logger_undeleted' )
