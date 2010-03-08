# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

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
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

from tagging.models import Tag
from tagging.fields import TagField
from tagging import register

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
        return '/e/show/' + str(self.id) + '/'
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


SHA1_RE = re.compile('^[a-f0-9]{40}$')

class Group(models.Model):
    name = models.CharField(_('Name'), max_length=80, unique=True)
    description = models.TextField(_('Description'))
    members = models.ManyToManyField(User, through='Membership', verbose_name=_('Members'))
    events = models.ManyToManyField(Event, through='Calendar', verbose_name=_('Events'))
    creation_time = models.DateTimeField(_('Creation time'), editable=False, auto_now_add=True)
    modification_time = models.DateTimeField(_('Modification time'), editable=False, auto_now=True)
    class Meta:
        ordering = ['creation_time']
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')
    def __unicode__(self):
        return self.name
    def get_absolute_url(self):
        return '/group/' + str(self.id) + '/'

class Membership(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    group = models.ForeignKey(Group, verbose_name=_('Group'))
    is_administrator = models.BooleanField(_('Is administrator'), default=True) # TODO: default true, not used for the moment
    new_event_email = models.BooleanField(_('New event email'), default=True)
    new_member_email = models.BooleanField(_('email_member_email'), default=True)
    date_joined = models.DateField(_('date_joined'), editable=False, auto_now_add=True)
    class Meta:
        unique_together = ("user", "group")
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')

# model "Calendar" is about which events are interesting for which group
class Calendar(models.Model):
    event = models.ForeignKey(Event, verbose_name=_('Event'))
    group = models.ForeignKey(Group, verbose_name=_('Group'))
    date_added = models.DateField(_('Date added'), editable=False, auto_now_add=True)
    class Meta:
        unique_together = ("event", "group")
        verbose_name = _('Calendar')
        verbose_name_plural = _('Calendars')

# explained at
# http://docs.djangoproject.com/en/dev/ref/contrib/admin/#working-with-many-to-many-intermediary-models
class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1
class CalendarInline(admin.TabularInline):
    model = Calendar
    extra = 1
class GroupAdmin(admin.ModelAdmin):
    inlines = (MembershipInline, CalendarInline,)


# They are already registered somehow
# admin.site.register(Group, GroupAdmin)
# register(Event)

# Next code is an adaptation of some code in python-django-registration

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

        To prevent membership of a user who has been
        removed by a group administrator after his activation, the activation key is reset to the
        string ``ALREADY_ACTIVATED`` after successful activation.

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
