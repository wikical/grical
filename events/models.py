# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from gridcalendar.tagging.models import Tag
from gridcalendar.tagging.fields import TagField
from gridcalendar.tagging import register
from django.utils.translation import ugettext_lazy as _


COUNTRIES = (
    ('AF', _('Afghanistan')),
    ('AX', _(u'Åland Islands')),
    ('AL', _('Albania')),
    ('DZ', _('Algeria')),
    ('AS', _('American Samoa')),
    ('AD', _('Andorra')),
    ('AO', _('Angola')),
    ('AI', _('Anguilla')),
    ('AQ', _('Antarctica')),
    ('AG', _('Antigua and Barbuda')),
    ('AR', _('Argentina')),
    ('AM', _('Armenia')),
    ('AW', _('Aruba')),
    ('AU', _('Australia')),
    ('AT', _('Austria')),
    ('AZ', _('Azerbaijan')),
    ('BS', _('Bahamas')),
    ('BH', _('Bahrain')),
    ('BD', _('Bangladesh')),
    ('BB', _('Barbados')),
    ('BY', _('Belarus')),
    ('BE', _('Belgium')),
    ('BZ', _('Belize')),
    ('BJ', _('Benin')),
    ('BM', _('Bermuda')),
    ('BT', _('Bhutan')),
    ('BO', _('Bolivia, Plurinational State of')),
    ('BA', _('Bosnia and Herzegovina')),
    ('BW', _('Botswana')),
    ('BV', _('Bouvet Island')),
    ('BR', _('Brazil')),
    ('IO', _('British Indian Ocean Territory')),
    ('BN', _('Brunei Darussalam')),
    ('BG', _('Bulgaria')),
    ('BF', _('Burkina Faso')),
    ('BI', _('Burundi')),
    ('KH', _('Cambodia')),
    ('CM', _('Cameroon')),
    ('CA', _('Canada')),
    ('CV', _('Cape Verde')),
    ('KY', _('Cayman Islands')),
    ('CF', _('Central African Republic')),
    ('TD', _('Chad')),
    ('CL', _('Chile')),
    ('CN', _('China')),
    ('CX', _('Christmas Island')),
    ('CC', _('Cocos (Keeling) Islands')),
    ('CO', _('Colombia')),
    ('KM', _('Comoros')),
    ('CG', _('Congo')),
    ('CD', _('Congo, the Democratic Republic of the')),
    ('CK', _('Cook Islands')),
    ('CR', _('Costa Rica')),
    ('CI', _(u'Côte d\'Ivoire')),
    ('HR', _('Croatia')),
    ('CU', _('Cuba')),
    ('CY', _('Cyprus')),
    ('CZ', _('Czech Republic')),
    ('DK', _('Denmark')),
    ('DJ', _('Djibouti')),
    ('DM', _('Dominica')),
    ('DO', _('Dominican Republic')),
    ('EC', _('Ecuador')),
    ('EG', _('Egypt')),
    ('SV', _('El Salvador')),
    ('GQ', _('Equatorial Guinea')),
    ('ER', _('Eritrea')),
    ('EE', _('Estonia')),
    ('ET', _('Ethiopia')),
    ('FK', _('Falkland Islands (Malvinas)')),
    ('FO', _('Faroe Islands')),
    ('FJ', _('Fiji')),
    ('FI', _('Finland')),
    ('FR', _('France')),
    ('GF', _('French Guiana')),
    ('PF', _('French Polynesia')),
    ('TF', _('French Southern Territories')),
    ('GA', _('Gabon')),
    ('GM', _('Gambia')),
    ('GE', _('Georgia')),
    ('DE', _(u'Germany')),
    ('GH', _('Ghana')),
    ('GI', _('Gibraltar')),
    ('GR', _('Greece')),
    ('GL', _('Greenland')),
    ('GD', _('Grenada')),
    ('GP', _('Guadeloupe')),
    ('GU', _('Guam')),
    ('GT', _('Guatemala')),
    ('GG', _('Guernsey')),
    ('GN', _('Guinea')),
    ('GW', _('Guinea-Bissau')),
    ('GY', _('Guyana')),
    ('HT', _('Haiti')),
    ('HM', _('Heard Island and McDonald Islands')),
    ('VA', _('Holy See (Vatican City State)')),
    ('HN', _('Honduras')),
    ('HK', _('Hong Kong')),
    ('HU', _('Hungary')),
    ('IS', _('Iceland')),
    ('IN', _('India')),
    ('ID', _('Indonesia')),
    ('IR', _('Iran, Islamic Republic of')),
    ('IQ', _('Iraq')),
    ('IE', _('Ireland')),
    ('IM', _('Isle of Man')),
    ('IL', _('Israel')),
    ('IT', _('Italy')),
    ('JM', _('Jamaica')),
    ('JP', _('Japan')),
    ('JE', _('Jersey')),
    ('JO', _('Jordan')),
    ('KZ', _('Kazakhstan')),
    ('KE', _('Kenya')),
    ('KI', _('Kiribati')),
    ('KP', _('Korea, Democratic People\'s Republic of')),
    ('KR', _('Korea, Republic of')),
    ('KW', _('Kuwait')),
    ('KG', _('Kyrgyzstan')),
    ('LA', _('Lao People\'s Democratic Republic')),
    ('LV', _('Latvia')),
    ('LB', _('Lebanon')),
    ('LS', _('Lesotho')),
    ('LR', _('Liberia')),
    ('LY', _('Libyan Arab Jamahiriya')),
    ('LI', _('Liechtenstein')),
    ('LT', _('Lithuania')),
    ('LU', _('Luxembourg')),
    ('MO', _('Macao')),
    ('MK', _('Macedonia, the former Yugoslav Republic of')),
    ('MG', _('Madagascar')),
    ('MW', _('Malawi')),
    ('MY', _('Malaysia')),
    ('MV', _('Maldives')),
    ('ML', _('Mali')),
    ('MT', _('Malta')),
    ('MH', _('Marshall Islands')),
    ('MQ', _('Martinique')),
    ('MR', _('Mauritania')),
    ('MU', _('Mauritius')),
    ('YT', _('Mayotte')),
    ('MX', _('Mexico')),
    ('FM', _('Micronesia, Federated States of')),
    ('MD', _('Moldova, Republic of')),
    ('MC', _('Monaco')),
    ('MN', _('Mongolia')),
    ('ME', _('Montenegro')),
    ('MS', _('Montserrat')),
    ('MA', _('Morocco')),
    ('MZ', _('Mozambique')),
    ('MM', _('Myanmar')),
    ('NA', _('Namibia')),
    ('NR', _('Nauru')),
    ('NP', _('Nepal')),
    ('NL', _('Netherlands')),
    ('AN', _('Netherlands Antilles')),
    ('NC', _('New Caledonia')),
    ('NZ', _('New Zealand')),
    ('NI', _('Nicaragua')),
    ('NE', _('Niger')),
    ('NG', _('Nigeria')),
    ('NU', _('Niue')),
    ('NF', _('Norfolk Island')),
    ('MP', _('Northern Mariana Islands')),
    ('NO', _('Norway')),
    ('OM', _('Oman')),
    ('PK', _('Pakistan')),
    ('PW', _('Palau')),
    ('PS', _('Palestinian Territory, Occupied')),
    ('PA', _('Panama')),
    ('PG', _('Papua New Guinea')),
    ('PY', _('Paraguay')),
    ('PE', _('Peru')),
    ('PH', _('Philippines')),
    ('PN', _('Pitcairn')),
    ('PL', _('Poland')),
    ('PT', _('Portugal')),
    ('PR', _('Puerto Rico')),
    ('QA', _('Qatar')),
    ('RE', _(u'Réunion')),
    ('RO', _('Romania')),
    ('RU', _('Russian Federation')),
    ('RW', _('Rwanda')),
    ('BL', _(u'Saint Barthélemy')),
    ('SH', _('Saint Helena')),
    ('KN', _('Saint Kitts and Nevis')),
    ('LC', _('Saint Lucia')),
    ('MF', _('Saint Martin (French part)')),
    ('PM', _('Saint Pierre and Miquelon')),
    ('VC', _('Saint Vincent and the Grenadines')),
    ('WS', _('Samoa')),
    ('SM', _('San Marino')),
    ('ST', _('Sao Tome and Principe')),
    ('SA', _('Saudi Arabia')),
    ('SN', _('Senegal')),
    ('RS', _('Serbia')),
    ('SC', _('Seychelles')),
    ('SL', _('Sierra Leone')),
    ('SG', _('Singapore')),
    ('SK', _('Slovakia')),
    ('SI', _('Slovenia')),
    ('SB', _('Solomon Islands')),
    ('SO', _('Somalia')),
    ('ZA', _('South Africa')),
    ('GS', _('South Georgia and the South Sandwich Islands')),
    ('ES', _('Spain')),
    ('LK', _('Sri Lanka')),
    ('SD', _('Sudan')),
    ('SR', _('Suriname')),
    ('SJ', _('Svalbard and Jan Mayen')),
    ('SZ', _('Swaziland')),
    ('SE', _('Sweden')),
    ('CH', _('Switzerland')),
    ('SY', _('Syrian Arab Republic')),
    ('TW', _('Taiwan, Province of China')),
    ('TJ', _('Tajikistan')),
    ('TZ', _('Tanzania, United Republic of')),
    ('TH', _('Thailand')),
    ('TL', _('Timor-Leste')),
    ('TG', _('Togo')),
    ('TK', _('Tokelau')),
    ('TO', _('Tonga')),
    ('TT', _('Trinidad and Tobago')),
    ('TN', _('Tunisia')),
    ('TR', _('Turkey')),
    ('TM', _('Turkmenistan')),
    ('TC', _('Turks and Caicos Islands')),
    ('TV', _('Tuvalu')),
    ('UG', _('Uganda')),
    ('UA', _('Ukraine')),
    ('AE', _('United Arab Emirates')),
    ('GB', _('United Kingdom')),
    ('US', _('United States')),
    ('UM', _('United States Minor Outlying Islands')),
    ('UY', _('Uruguay')),
    ('UZ', _('Uzbekistan')),
    ('VU', _('Vanuatu')),
    ('VE', _('Venezuela, Bolivarian Republic of')),
    ('VN', _('Viet Nam')),
    ('VG', _('Virgin Islands, British')),
    ('VI', _('Virgin Islands, U.S.')),
    ('WF', _('Wallis and Futuna')),
    ('EH', _('Western Sahara')),
    ('YE', _('Yemen')),
    ('ZM', _('Zambia')),
    ('ZW', _('Zimbabwe')),
)

class CountryField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 2)
        kwargs.setdefault('choices', COUNTRIES)

        super(CountryField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"


class Event(models.Model):
	# related_name avoids the errors:
	# events.event: Accessor for field 'user' clashes with related m2m field 'User.event_set'. Add a related_name argument to the definition for 'user'.
	# events.event: Accessor for m2m field 'users' clashes with related field 'User.event_set'. Add a related_name argument to the definition for 'users'.
    #
    # AnonymousUser is not a user in the table User. For events posted by non-logged-in-users, this field will be null
    user = models.ForeignKey(User, editable=False, related_name="owner", blank=True, null=True, verbose_name=_('User'))
    # time stamp for event creation
    creation_time = models.DateTimeField(_('Creation time'), editable=False, auto_now_add=True)
    modification_time = models.DateTimeField(_('Modification time'), editable=False, auto_now=True)
    ##############################################################
    acro = models.CharField(_('Acronym'), max_length=20, blank=True, null=True, help_text=_('Example: 26C3'))
    #
    title = models.CharField(_('Title'), max_length=200, blank=False, help_text=_('Example: Demostration in Munich against software patents organised by the German association FFII e.V.'))
    #
    start = models.DateField(_('Start'), blank=False, help_text=_("Examples of valid dates: '2006-10-25' '10/25/2006' '10/25/06' 'Oct 25 2006' 'Oct 25, 2006' '25 Oct 2006' '25 Oct, 2006' 'October 25 2006' 'October 25, 2006' '25 October 2006' '25 October, 2006'"))
    end = models.DateField(_('End'), null=True, blank=True)
    #
    tags = TagField(_('Tags'), blank=True, null=True, help_text=_(u"Tags are case in-sensitive. Only letters (these can be international, like: αöł), digits and hyphens are allowed. Tags are separated with spaces."))
    #
    public_view = models.BooleanField(_('Publicly viewable'), default=True, help_text=_("A publicly viewable entry can be seen by anyone, otherwise only by the selected persons and groups"))
    public_edit = models.BooleanField(_('Publicly editable'), default=False, help_text=_("A publicly editable entry can be edited by anyone, otherwise only by the selected persons and groups"))
    #
    country = models.CharField(_('Country'), blank=True, null=True, max_length=2, choices=COUNTRIES)
    city = models.CharField(_('City'), blank=True, null=True, max_length=50)
    postcode = models.CharField(_('Postcode'), blank=True, null=True, max_length=16)
    address = models.CharField(_('Street address'), blank=True, null=True, max_length=100)
    latitude = models.FloatField(_('Latitude'), blank=True, null=True, help_text=_("Please type decimal degrees, not degrees/minutes/seconds. Prefix with \"-\" for South, no sign for North."))
    longitude = models.FloatField(_('Longitude'), blank=True, null=True, help_text=_("Please type decimal degrees, not degrees/minutes/seconds. Prefix with \"-\" for West, no sign for East."))
    timezone = models.SmallIntegerField(_('Timezone'), blank=True, null=True, help_text=_("Minutes relative to UTC. Examples: UTC+1 = 60, UTC-3 = -180"))
    #
    description = models.TextField(_('Description'), blank=True, null=True)
    ##############################################################
    # groups = models.ManyToManyField(Group, blank=True, null=True, help_text=_("Groups to be notified and allowed to see it if not public"))
    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)
    def get_tags(self):
        return Tag.objects.get_for_object(self)
    def __unicode__(self):
		return self.start.isoformat() + " : " + self.title
    def get_absolute_url(self):
        return 'http://dev.cloca.net/events/view_astext/' + str(self.id) + '/'
    class Meta:
        ordering = ['start']
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

class EventUrl(models.Model):
    event = models.ForeignKey(Event, related_name='event_of_url')
    url_name = models.CharField(_('URL Name'), blank=True, null=True, max_length=80, help_text=_("Example: information about accomodation"))
    url = models.URLField(_('URL'), blank=False, null=False)
    def __unicode__(self):
        return self.url

class EventTimechunk(models.Model):
    event = models.ForeignKey(Event, related_name='event_of_timechunk')
    timechunk_name = models.CharField(_('Timechunk name'), blank=True, null=True, max_length=80, help_text=_("Example: day 2 of the conference"))
    timechunk_date = models.DateField(_('Timechunk day'), blank=False, null=False)
    timechunk_starttime = models.TimeField(_('Timechunk start time'), blank=False, null=False)
    timechunk_endtime = models.TimeField(_('Timechunk end time'), blank=False, null=False)
    def __unicode__(self):
        return self.timechunk_name

class EventDeadline(models.Model):
    event = models.ForeignKey(Event, related_name='event_of_deadline')
    deadline_name = models.CharField(_('Deadline name'), blank=True, null=True, max_length=80, help_text=_("Example: call for papers deadline"))
    deadline = models.DateField(_('Deadline'), blank=False, null=False)
    def __unicode__(self):
        return self.deadline_name

# TODO: add setting info to users. See the auth documentation because there is a method for adding
# fields to User. E.g.
#   - interesting locations
#   - interesting tags
#   - hidden: location and tags clicked before

#TODO: events comment model. Check for already available django comment module

class Filter(models.Model):
    user = models.ForeignKey(User, unique=False, verbose_name=_('User'))
    modification_time = models.DateTimeField(_('Modification time'), editable=False, auto_now=True)
    query = models.CharField(_('Query'), max_length=500, blank=False, null=False)
    name = models.CharField(_('Name'), max_length=40, blank=False, null=False)
    email = models.BooleanField(_('Email'), default=False, help_text=_('If set it sends an email to a user when a new event matches all fields set'))
    maxevents_email = models.SmallIntegerField(_('Max events in e-mail'), blank=True, null=True, default=10, help_text=_("Maximum number of events you to show in a notification e-mail"))
    class Meta:
        ordering = ['modification_time']
        unique_together = ("user", "name")
        verbose_name = _('Filter')
        verbose_name_plural = _('Filters')

