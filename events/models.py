# -*- coding: utf-8 -*-

import datetime
import random
import re
import sha

from django.db import models
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

#from gridcalendar.events.forms import EventForm

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

class Event(models.Model):
    """ Event model. """
    user = models.ForeignKey(User, editable=False, related_name="owner",
            blank=True, null=True, verbose_name=_('User'))
    """The user who created the event or null if AnonymousUser"""
    creation_time = models.DateTimeField(_('Creation time'), editable=False,
            auto_now_add=True)
    """Time stamp for event creation"""
    modification_time = models.DateTimeField(_('Modification time'),
            editable=False, auto_now=True)
    """Time stamp for event modification"""
    acronym = models.CharField(_('Acronym'), max_length=20, blank=True,
            null=True, help_text=_('Example: 26C3'))
    title = models.CharField(_('Title'), max_length=200, blank=False,
            help_text=_('Example: Demostration in Munich against software \
                patents organised by the German association FFII e.V.'))
    start = models.DateField(_('Start'), blank=False, help_text=_("Examples \
            of valid dates: '2006-10-25' '10/25/2006' '10/25/06' 'Oct 25 \
            2006' 'Oct 25, 2006' '25 Oct 2006' '25 Oct, 2006' \
            'October 25 2006' 'October 25, 2006' '25 October 2006' '25 \
            October, 2006'"))
    end = models.DateField(_('End'), null=True, blank=True)
    tags = TagField(_('Tags'), blank=True, null=True, help_text=_(u"Tags are \
        case in-sensitive. Only letters (these can be international, like: \
        αöł), digits and hyphens (-) are allowed. Tags are separated with \
        spaces."))
    public = models.BooleanField(_('Public'), default=True, help_text=_("A \
        public event can be seen and edited by anyone, otherwise only by the \
        members of selected groups"))
    country = models.CharField(_('Country'), blank=True, null=True,
            max_length=2, choices=COUNTRIES)
    city = models.CharField(_('City'), blank=True, null=True, max_length=50)
    postcode = models.CharField(_('Postcode'), blank=True, null=True,
            max_length=16)
    address = models.CharField(_('Street address'), blank=True, null=True,
            max_length=100)
    latitude = models.FloatField(_('Latitude'), blank=True, null=True,
            help_text=_("In decimal degrees, not \
            degrees/minutes/seconds. Prefix with \"-\" for South, no sign for \
            North."))
    longitude = models.FloatField(_('Longitude'), blank=True, null=True,
            help_text=_("In decimal degrees, not \
                degrees/minutes/seconds. Prefix with \"-\" for West, no sign \
                for East."))
    timezone = models.SmallIntegerField(_('Timezone'), blank=True, null=True,
            help_text=_("Minutes relative to UTC (e.g. -60 means UTC-1"))
    description = models.TextField(_('Description'), blank=True, null=True)
    # the relation event-group is now handle in group
    # groups = models.ManyToManyField(Group, blank=True, null=True,
    # help_text=_("Groups to be notified and allowed to see it if not public"))

    class Meta:
        ordering = ['start']
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

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
                    to_return += "urls:"
                    for url in urls:
                        if url.url_name == 'web':
                            to_return += " " + unicode(url.url)
                    to_return += "\n"
                    for url in urls:
                        if not url.url_name == 'web':
                            to_return += "    " + url.url_name + ': ' + url.url + "\n"
            elif keyword == 'deadlines' and self.deadlines:
                deadlines = EventDeadline.objects.filter(event=self.id)
                if len(deadlines) > 0:
                    to_return += "deadlines:"
                    for deadline in deadlines:
                        if deadline.deadline_name == 'deadline':
                            to_return += " " + unicode(deadline.deadline)
                    to_return += "\n"
                    for deadline in deadlines:
                        if not deadline.deadline_name == 'deadline':
                            to_return += "    " + deadline.deadline_name + ': ' + deadline.deadline + "\n"
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
                # TODO: support multiline descriptions
        return to_return

    @staticmethod
    def parse_text(input_text_in, event_id=None, user_id=None):
        """It parses a text and saves it as a single event in the data base.

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
                session1_name: session1_date session1_starttime session1_endtime
                session2_name: session2_date session2_starttime session2_endtime
                ...
        The idented lines are optional. If session_date is present, it will be saved
        with the session_name 'session'

        The text for the field 'groups' is of the form:
            groups: group1 group2 ...
        """
        # TODO: allow to put comments on events by email
        data = {}
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

        url_data = {}
        deadline_data = {}
        session_data = {}
        group_data = {}
        for field_text in field_pattern.findall(input_text):
            parts = parts_pattern.match(field_text).groups()
            try:
                field_name = synonyms[parts[0]]
            except KeyError: raise ValidationError(_(
                        "you used an invalid field name in '%s'" % field_text))
            if field_name == 'urls':
                url_index = 0
                url_data['urls-INITIAL_FORMS'] = u'0'
                if not parts[1] == '':
                    url_data['urls-' + str(url_index) + '-url_name'] = u'web'
                    url_data['urls-' + str(url_index) + '-url'] = parts[1].strip()
                    url_index += 1
                if not parts[2] == '':
                    for url_line in parts[2].splitlines():
                        if not url_line == '':
                            url_line_parts = url_line.split(":", 1)
                            url_data['urls-' + str(url_index) + '-url_name'] = url_line_parts[0].strip()
                            url_data['urls-' + str(url_index) + '-url'] = url_line_parts[1].strip()
                            url_index += 1
                url_data['urls-TOTAL_FORMS'] = str(url_index)
            elif field_name == 'deadlines':
                deadline_index = 0
                deadline_data['deadlines-INITIAL_FORMS'] = u'0'
                if not parts[1] == '':
                    deadline_data['deadlines-' + str(deadline_index) + '-deadline_name'] = u'deadline'
                    deadline_data['deadlines-' + str(deadline_index) + '-deadline'] = parts[1].strip()
                    deadline_index += 1
                if not parts[2] == '':
                    for deadline_line in parts[2].splitlines():
                        if not deadline_line == '':
                            deadline_line_parts = deadline_line.split(":", 1)
                            deadline_data['deadlines-' + str(deadline_index) + '-deadline_name'] = deadline_line_parts[0].strip()
                            deadline_data['deadlines-' + str(deadline_index) + '-deadline'] = deadline_line_parts[1].strip()
                            deadline_index += 1
                deadline_data['deadlines-TOTAL_FORMS'] = str(deadline_index)
            elif field_name == 'sessions':
                session_index = 0
                session_data['sessions-INITIAL_FORMS'] = u'0'
                if not parts[1] == '':
                    session_data['sessions-' + str(session_index) + '-session_name'] = u'session'
                    session_str_parts = parts[1].split(":", 1)
                    session_data['sessions-' + str(session_index) + '-session_date'] = session_str_parts[0].strip()
                    session_str_times_parts = session_str_parts[1].split("-", 1)
                    session_data['sessions-' + str(session_index) + '-session_starttime'] = session_str_times_parts[0].strip()
                    session_data['sessions-' + str(session_index) + '-session_endtime'] = session_str_times_parts[1].strip()
                    session_index += 1
                if not parts[2] == '':
                    for session_line in parts[2].splitlines():
                        if not session_line == '':
                            session_line_parts = session_line.split(":", 1)
                            session_data['sessions-' + str(session_index) + '-session_name'] = session_line_parts[0].strip()
                            session_str_parts = session_line_parts[1].split(":", 1)
                            session_data['sessions-' + str(session_index) + '-session_date'] = session_str_parts[0].strip()
                            session_str_times_parts = session_str_parts[1].split("-", 1)
                            session_data['sessions-' + str(session_index) + '-session_starttime'] = session_str_times_parts[0].strip()
                            session_data['sessions-' + str(session_index) + '-session_endtime'] = session_str_times_parts[1].strip()
                            session_index += 1
                session_data['sessions-TOTAL_FORMS'] = str(session_index)
            elif field_name == 'groups':
                event_groups_req_names_list = [p for p in re.split("( |\\\".*?\\\"|'.*?')", parts[1]) if p.strip()]
            else:
                if not parts[2] == '': raise ValidationError(_(
                        "field '%s' doesn't accept subparts" % parts[1]))
                if parts[0] == '': raise ValidationError(_(
                        "a left part of a colon is empty"))
                if not synonyms.has_key(parts[0]): raise ValidationError(_(
                        "keyword %s unknown" % parts[0]))
                data[synonyms[parts[0]]] = parts[1]

        if (event_id == None):
            pass
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


        from gridcalendar.events.forms import EventForm
        if (event_id == None):
            event_form = EventForm(data)
        else:
            event_form = EventForm(data, instance=event)
        if event_form.is_valid():
            # TODO: would be nice if instead of deleting all URLs each time, it would update
            EventUrl.objects.filter(event=event_id).delete()
            EventDeadline.objects.filter(event=event_id).delete()
            EventSession.objects.filter(event=event_id).delete()
            if len(url_data) > 0:
                EventUrlInlineFormSet = inlineformset_factory(Event, EventUrl, extra=0)
                ef_url = EventUrlInlineFormSet(url_data, instance=event)
                if ef_url.is_valid():
                    ef_url.save()
                else:
                    raise ValidationError(_(
                        "There is an error in the input data in the URLs: %s" % ef_url.errors))
            if len(deadline_data) > 0:
                EventDeadlineInlineFormSet = inlineformset_factory(Event, EventDeadline, extra=0)
                ef_deadline = EventDeadlineInlineFormSet(deadline_data, instance=event)
                if ef_deadline.is_valid():
                    ef_deadline.save()
                else:
                    raise ValidationError(_(
                        "There is an error in the input data in the deadlines: %s" % ef_deadline.errors))
            if len(session_data) > 0:
                EventSessionInlineFormSet = inlineformset_factory(Event, EventSession, extra=0)
                ef_session = EventSessionInlineFormSet(session_data, instance=event)
                if ef_session.is_valid():
                    ef_session.save()
                else:
                    raise ValidationError(_(
                        "There is an error in the input data in the sessions: %s" % ef_session.errors))
            event_form.save()
        else:
            raise ValidationError(_(
                "there is an error in the input data: %s" % event_form.errors))

    @staticmethod
    def get_synonyms():
        """Returns a dictionay with names (strings) and the fields (strings)
        they refer.

        All values of the returned dictionary (except groups, urls and
        sessions) must be names of fields of the Event class.

        >>> synomyns_values_set = set(Event.get_synonyms().values())
        >>> assert ('groups' in synomyns_values_set)
        >>> synomyns_values_set.remove('groups')
        >>> assert ('urls' in synomyns_values_set)
        >>> synomyns_values_set.remove('urls')
        >>> assert ('deadlines' in synomyns_values_set)
        >>> synomyns_values_set.remove('deadlines')
        >>> assert ('sessions' in synomyns_values_set)
        >>> synomyns_values_set.remove('sessions')
        >>> assert (set(dir(Event)) >= synomyns_values_set)
        """
        # TODO: subclass dictionary to ensure you don't override a key
        synonyms = {}
        synonyms['title']       = 'title'       # title
        synonyms['t']           = 'title'
        synonyms['titl']        = 'title'
        synonyms['start']       = 'start'       # start
        synonyms['date']        = 'start'
        synonyms['d']           = 'start'
        synonyms['tags']        = 'tags'        # tags
        synonyms['subjects']    = 'tags'
        synonyms['s']           = 'tags'
        synonyms['end']         = 'end'         # end
        synonyms['e']           = 'end'
        synonyms['endd']        = 'end'
        synonyms['acronym']     = 'acronym'     # acronym
        synonyms['acro']        = 'acronym'
        synonyms['public']      = 'public'      # public
        synonyms['p']           = 'public'
        synonyms['country']     = 'country'     # country
        synonyms['coun']        = 'country'
        synonyms['c']           = 'country'
        synonyms['city']        = 'city'        # city
        synonyms['cc']          = 'city'
        synonyms['postcode']    = 'postcode'    # postcode
        synonyms['pp']          = 'postcode'
        synonyms['zip']         = 'postcode'
        synonyms['code']        = 'postcode'
        synonyms['address']     = 'address'     # address
        synonyms['addr']        = 'address'
        synonyms['a']           = 'address'
        synonyms['latitude']    = 'latitude'    # latitude
        synonyms['lati']        = 'latitude'
        synonyms['longitude']   = 'longitude'   # longitude
        synonyms['long']        = 'longitude'
        synonyms['timezone']    = 'timezone'    # timezone
        synonyms['description'] = 'description' # description
        synonyms['desc']        = 'description'
        synonyms['des']         = 'description'
        synonyms['de']          = 'description'
        synonyms['groups']      = 'groups'      # groups (*)
        synonyms['group']       = 'groups'
        synonyms['g']           = 'groups'
        synonyms['urls']        = 'urls'        # urls (*)
        synonyms['u']           = 'urls'
        synonyms['web']         = 'urls'
        synonyms['sessions']    = 'sessions'    # sessions (*)
        synonyms['time']        = 'sessions'
        synonyms['t']           = 'sessions'
        synonyms['deadlines']   = 'deadlines'   # deadlines (*)
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
    url_name = models.CharField(_('URL Name'), blank=False, null=False,
            max_length=80, help_text=_(
            "Example: information about accomodation"))
    url = models.URLField(_('URL'), blank=False, null=False)
    class Meta:
        ordering = ['event', 'url_name']
        unique_together = ("event", "url_name")
    def __unicode__(self):
        return self.url

class EventDeadline(models.Model):
    event = models.ForeignKey(Event, related_name='deadlines')
    deadline_name = models.CharField(_('Deadline name'), blank=False, null=False,
            max_length=80, help_text=_(
            "Example: call for papers deadline"))
    deadline = models.DateField(_('Deadline'), blank=False, null=False)
    class Meta:
        ordering = ['event', 'deadline', 'deadline_name']
        unique_together = ("event", "deadline_name")
    def __unicode__(self):
        return unicode(self.deadline) + u' - ' + self.deadline_name

class EventSession(models.Model):
    event = models.ForeignKey(Event, related_name='sessions')
    session_name = models.CharField(_('Session name'), blank=False, null=False,
            max_length=80, help_text=_(
            "Example: day 2 of the conference"))
    session_date = models.DateField(_('Session day'), blank=False,
            null=False)
    session_starttime = models.TimeField(_('Session start time'),
            blank=False, null=False)
    session_endtime = models.TimeField(_('Session end time'), blank=False, null=False)
    class Meta:
        ordering = ['event', 'session_date', 'session_starttime', 'session_endtime']
        unique_together = ("event", "session_name")
    def __unicode__(self):
        return unicode(self.session_date) + u' - ' + unicode(self.session_starttime) + u' - ' + unicode(self.session_endtime) + u' - ' + self.session_name

class Filter(models.Model):
    user = models.ForeignKey(User, unique=False, verbose_name=_('User'))
    modification_time = models.DateTimeField(_('Modification time'),
            editable=False, auto_now=True)
    query = models.CharField(_('Query'), max_length=500, blank=False,
            null=False)
    name = models.CharField(_('Name'), max_length=40, blank=False, null=False)
    email = models.BooleanField(_('Email'), default=False, help_text=
            _('If set it sends an email to a user when a new event matches all fields set'))
    maxevents_email = models.SmallIntegerField(_('Number of events in e-mail'),
            blank=True, null=True, default=10, help_text=
            _("Maximum number of events to show in a notification e-mail"))
    class Meta:
        ordering = ['modification_time']
        unique_together = ("user", "name")
        verbose_name = _('Filter')
        verbose_name_plural = _('Filters')
    def __unicode__(self):
        return self.name
    @models.permalink
    def get_absolute_url(self):
        return ('filter_edit', (), { 'filter_id': self.id })

class Group(models.Model):
    name = models.CharField(_('Name'), max_length=80, unique=True)
    description = models.TextField(_('Description'))
    members = models.ManyToManyField(User, through='Membership',
            verbose_name=_('Members'))
    events = models.ManyToManyField(Event, through='Calendar',
            verbose_name=_('Events'))
    creation_time = models.DateTimeField(_('Creation time'), editable=False,
            auto_now_add=True)
    modification_time = models.DateTimeField(_('Modification time'),
            editable=False, auto_now=True)

    class Meta:
        ordering = ['creation_time']
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('list_events_group', (), { 'group_id': self.id })

    @staticmethod
    def is_user_in_group(user_id, group_id):
        if Membership.objects.filter(user__id__exact=user_id,
                group__id__exact=group_id).count() > 0:
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
    user = models.ForeignKey(User, verbose_name=_('User'), related_name='user_in_groups')
    group = models.ForeignKey(Group, verbose_name=_('Group'), related_name='users_in_group')
    is_administrator = models.BooleanField(_('Is administrator'), default=True)
    """Not used at the moment. All members of a group are administrators."""
    new_event_email = models.BooleanField(_('New event email'), default=True)
    new_member_email = models.BooleanField(_('email_member_email'), default=True)
    date_joined = models.DateField(_('date_joined'), editable=False, auto_now_add=True)
    class Meta:
        unique_together = ("user", "group")
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')

class Calendar(models.Model):
    """Relation between events and groups."""
    event = models.ForeignKey(Event, verbose_name=_('Event'), related_name='event_in_groups')
    group = models.ForeignKey(Group, verbose_name=_('Group'), related_name='calendar')
    date_added = models.DateField(_('Date added'), editable=False, auto_now_add=True)
    class Meta:
        unique_together = ("event", "group")
        verbose_name = _('Calendar')
        verbose_name_plural = _('Calendars')

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
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+guest.username).hexdigest()
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

    host = models.ForeignKey(User, related_name="host", verbose_name=_('host'))
    guest = models.ForeignKey(User, related_name="guest", verbose_name=_('host'))
    group = models.ForeignKey(Group, verbose_name=_('group'))
    as_administrator = models.BooleanField(_('as administrator'), default=False)
    activation_key = models.CharField(_('activation key'), max_length=40)

    # see http://docs.djangoproject.com/en/1.0/topics/db/managers/
    objects = GroupInvitationManager()

    class Meta:
#        unique_together = ("host", "guest", "group")
        verbose_name = _('Group invitation')
        verbose_name_plural = _('Group invitations')

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

