# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

import datetime
import random
import re
import sha

from gridcalendar.tagging import register
from gridcalendar.events.models import Event

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.models import Site


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
admin.site.register(Group, GroupAdmin)
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
