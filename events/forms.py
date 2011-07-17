#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4:shiftwidth=4:textwidth=79:fdm=marker
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

""" Forms """

# imports {{{1
import re
import datetime
import urllib2
import urlparse

from django.contrib.gis.geos import Point
from django.core import validators
from django.forms import ( CharField, IntegerField, HiddenInput,
        ModelMultipleChoiceField, ModelForm, ValidationError,
        TextInput, CheckboxSelectMultiple, Form, Field, DateField, TimeField )
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from gridcalendar.settings_local import DEBUG
from gridcalendar.events.models import (Event, EventUrl, EventDeadline,
        EventSession, Filter, Group, Membership )
from gridcalendar.events.search import COORDINATES_REGEX
from gridcalendar.events.utils import validate_year, validate_event_exists

def _date(string): # {{{1
    """ parse a date in the format ``yyyy-mm-dd`` using
    ``gridcalendar.events.utils.validate_year """
    parsed_date = datetime.datetime.strptime(string, '%Y-%m-%d').date()
    validate_year( parsed_date )
    return parsed_date

def _time(string): # {{{1
    """ parse a time in the format: hh:mm """
    return datetime.datetime.strptime(string, '%H:%M').time()

class URLValidatorExtended( validators.URLValidator ):
    """ Like ``URLValidation`` but adding support to HTTP Basic Auth.
    See https://code.djangoproject.com/ticket/9791 """
    def __call__( self, value ):
        try:
            return super( URLValidatorExtended, self ).__call__( value )
        except ValidationError, err:
            # we check now http basic auth
            url = urlparse.urlsplit( value )
            if url.scheme.lower() != "http" and url.scheme.lower() != "https":
                raise ValidationError(
                    _( u"Only http and https are supported" ) )
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            if url.netloc.find('@') >= 0:
                user = url.username
                passwd = url.password
                url = list(url)
                url[1] = url[1].split('@')[1]
                urlf = urlparse.urlunsplit(url)
                passman.add_password( None, urlf.split("//")[1], user, passwd )
            else:
                raise err
            authhandler = urllib2.HTTPBasicAuthHandler(passman)
            opener = urllib2.build_opener(authhandler)
            urllib2.install_opener(opener)
            headers = {
                "Accept": "text/xml,application/xml,application/xhtml+xml," \
                        "text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
                "Accept-Language": "en-us,en;q=0.5",
                "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                "Connection": "close",
                "User-Agent": self.user_agent,
            }
            # TODO: try first a HEAD request, see Django code of URLValidator
            try:
                req = urllib2.Request( urlf, headers = headers )
                f = urllib2.urlopen( req, timeout = 10 )
            except urllib2.HTTPError, e:
                raise ValidationError(
                        _( u"Couldn't get URL %(url)s: %(error)s" ) % 
                        { 'url': value, 'error': e} )
            except urllib2.URLError, e:
                raise ValidationError(
                    "Couldn't connect to %s: %s" %
                        _( u"Couldn't connect to %(url)s: %(error)s" ) % 
                        { 'url': u[1], 'error':e.reason } )

class URLFieldExtended(CharField): #{{{1
    """ like URLFiled but adding support for in-URL basic AUTH, see
        http://code.djangoproject.com/ticket/9791 """
    default_error_messages = {
        'invalid': _(u'Enter a valid URL.'),
        'invalid_link': _(u'This URL appears to be a broken link.'),
    }
    def __init__(self, max_length=None, min_length=None, verify_exists=False,
            validator_user_agent=validators.URL_VALIDATOR_USER_AGENT,
            *args, **kwargs):
        super(URLFieldExtended, self).__init__(
                max_length, min_length, *args, **kwargs )
        self.validators.append( URLValidatorExtended(
            verify_exists=verify_exists,
            validator_user_agent=validator_user_agent ) )

class DatesTimesField(Field): # {{{1
    """ processes one or two dates and optionally one or two times, returning a
    dictionary with possible keys: start, end, starttime, endtime

    Valid formats:

    - 2010-01-25
    - 2010-01-25 2010-01-26
    - 2010-01-25 10:00
    - 2010-01-25 10:00 2010-01-26 18:00
    - 2010-01-25 10:00 11:00
    - 2010-01-25 10:00-11:00
    - Django DateField formats taking into account L10N. For English:

        - 2006-10-25
        - 10/25/2006
        - 10/25/06
        - Oct 25 2006
        - Oct 25, 2006
        - 25 Oct 2006
        - 25 Oct, 2006
        - October 25 2006
        - October 25, 2006
        - 25 October 2006
        - 25 October, 2006

    >>> dt = DatesTimesField()
    >>> d = dt.to_python('2010-01-25')
    >>> d = dt.to_python('2010-1-25')
    >>> d = dt.to_python('2010-01-25 2010-01-26')
    >>> d = dt.to_python('2010-1-25 2010-1-26')
    >>> d = dt.to_python('2010-01-25 10:00')
    >>> d = dt.to_python('2010-1-25 1:00')
    >>> d = dt.to_python('2010-01-25 10:00 2010-01-26 18:00')
    >>> d = dt.to_python('2010-1-25 1:00 2010-1-26 2:00')
    >>> d = dt.to_python('2010-01-25 10:00 11:00')
    >>> d = dt.to_python('2010-1-25 8:00 9:00')
    >>> d = dt.to_python('2010-01-25 10:00-11:00')
    >>> d = dt.to_python('2010-1-25 8:00-9:00')
    >>> d = dt.to_python('25 October, 2006')
    """
    def to_python(self, value):
        """ returns a dictionary with four values: start, end,
        starttime, endtime """
        re_d = \
            re.compile( r'^\s*(\d\d\d\d-\d?\d-\d?\d)\s*$', re.UNICODE )
        re_d_d = \
            re.compile(
                r'^\s*(\d\d\d\d-\d?\d-\d?\d)\s+(\d\d\d\d-\d?\d-\d?\d)\s*$',
                    re.UNICODE)
        re_d_t = \
            re.compile(r'^\s*(\d\d\d\d-\d?\d-\d?\d)\s+(\d?\d:\d\d)\s*$',
                    re.UNICODE)
        re_d_t_d_t = \
            re.compile(r"""
                ^\s*(\d\d\d\d-\d?\d-\d?\d)
                \s+(\d?\d:\d\d)
                \s+(\d\d\d\d-\d?\d-\d?\d)
                \s+(\d?\d:\d\d)\s*$""", re.UNICODE | re.X )
        re_d_t_t = \
            re.compile(r"""
                ^\s*(\d\d\d\d-\d?\d-\d?\d)
                \s+(\d?\d:\d\d)
                \s+(\d?\d:\d\d)\s*$""", re.UNICODE | re.X )
        re_d_t_t =   re.compile( r"""
            ^\s*(\d\d\d\d-\d?\d-\d?\d) # beginning, optional spaces, start date
             \s+(\d?\d:\d\d)          # start time after one ore more spaces
             (?:(?:\s+)|(?:\s*-\s*)) # one or more spaces, alternatively -
             (\d?\d:\d\d)\s*$         # end time before optional spaces""",
            re.UNICODE | re.X )
        try:
            matcher = re_d.match( value )
            if matcher:
                return {'start': _date(matcher.group(1)),}
            matcher = re_d_d.match( value )
            if matcher:
                return {'start': _date(matcher.group(1)),
                        'end': _date(matcher.group(2))}
            matcher = re_d_t.match(value)
            if matcher:
                return {'start': _date(matcher.group(1)),
                        'starttime': _time(matcher.group(2))}
            matcher = re_d_t_d_t.match(value)
            if matcher:
                return {'start': _date(matcher.group(1)),
                        'starttime': _time(matcher.group(2)),
                        'end': _date(matcher.group(3)),
                        'endtime': _time(matcher.group(4))}
            matcher = re_d_t_t.match(value)
            if matcher:
                return {'start': _date(matcher.group(1)),
                        'starttime': _time(matcher.group(2)),
                        'endtime': _time(matcher.group(3))}
        except (TypeError, ValueError), e:
            pass
        except ValidationError, e:
            # the validationError comes from utils.validate_year and the error
            # message is translated
            raise e
        # No matches. We try now DateField
        return { 'start': DateField().clean( value ) }

    def validate(self, value):
        """ checks that dates and times are in order, i.e. start before end """
        if value.has_key('end'):
            if value['start'] > value['end']:
                raise ValidationError( _('end date is before start date') )
        if value.has_key('endtime'):
            if value['starttime'] > value['endtime']:
                raise ValidationError( _('end time is before start time') )

class CoordinatesField( CharField ): #{{{1
    default_error_messages = {
            'invalid': _(
                u'Enter a valid pair of coordinates (latitude,longitude)'),
        }
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super( CoordinatesField, self).__init__(
                max_length, min_length, *args, **kwargs )
        self.validators.append( CoordinatesField.validate_latitude )
        self.validators.append( CoordinatesField.validate_longitude )
    def to_python( self, value ):
        """Normalize coordinates to a dictionary with two keys: latitude and
        longitude. """
        if not value:
            return {}
        value = value.strip()
        matcher = COORDINATES_REGEX.match( value )
        if not matcher:
            raise ValidationError(_(u'No two separate numbers with decimals'))
        return {
            'latitude':  float ( matcher.group(1) ),
            'longitude': float ( matcher.group(2) )}
    @staticmethod
    def validate_latitude( value ):
        if value['latitude'] < -90 or value['latitude'] > 90:
            raise ValidationError( _( u'Latitude is not within (-90,90)' ) )
    @staticmethod
    def validate_longitude( value ):
        if value['longitude'] < -180 or value['longitude'] > 180:
            raise ValidationError( _(u'Longitude is not within (-180,180)') )

class FilterForm(ModelForm): # {{{1
    """ ModelForm using Filter excluding `user` """
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = Filter
        widgets = { 'user' : HiddenInput(), }
    # TODO: change the error displayed when the name already exists:
    # "Filter with this User and Name already exists."
    # It should be: you already has a filter with this name
    # One option:
    #def clean_name( self ):
    #    """ checks that the user doesn't have a filter with the same name """
    #    data = self.cleaned_data
    #    if self.instance and self.instance.user:
    #        # we ignore user_id from the form if an instance is there with a
    #        # user (not the case for new filters but for old ones)
    #        user_id = self.instance.user.id
    #    else:
    #        user_id = data.get('user_id')
    #    if Filter.objects.filter(
    #            user = user_id, name = data.get('name') ).exists():
    #        raise ValidationError(
    #                 _(u"You already have a filter with the name " \
    #                 "'%(filter_name)s'. Choose another name") % \
    #                         {'filter_name': data.get('name')} )
    #    return data

class EventForm(ModelForm): # {{{1
    """ ModelForm for all editable fields of Event """
    coordinates = CoordinatesField( max_length = 26, required = False )
    # TODO: put this in the right position within the form, see
    # http://stackoverflow.com/questions/350799/how-does-django-know-the-order-to-render-form-fields
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        if kwargs.has_key('instance'):
            # not a new event
            # We use a custom field called 'coordinates' for
            # showing/editing/entering latitude and longitude stored in
            # Event.coordinates (which is a Point). We populate now
            # 'coordinates' with the values of event.coordinates
            instance = kwargs['instance']
            coordinates_value = u''
            if instance.coordinates:
                coordinates_value += str( instance.coordinates.y ) + ', ' + \
                        str( instance.coordinates.x )
            if coordinates_value:
                self.fields['coordinates'].initial = coordinates_value
        #TODO: use css instead
        self.fields['title'].widget.attrs["size"] = 70
        self.fields['start'].widget.attrs["size"] = 10
        self.fields['end'].widget.attrs["size"] = 10
        self.fields['starttime'].widget.attrs["size"] = 5
        self.fields['starttime'].widget.format = '%H:%M'
        self.fields['endtime'].widget.attrs["size"] = 5
        self.fields['endtime'].widget.format = '%H:%M'
        self.fields['tags'].widget.attrs["size"] = 70
        self.fields['address'].widget.attrs["size"] = 70
        self.fields['description'].widget.attrs["rows"] = 20
        self.fields['description'].widget.attrs["cols"] = 70
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        exclude = ('coordinates',) # excludes the model field 'coordinates'
    def clean( self ):
        """ it adds the value of coordinates to the Event instance """
        self.cleaned_data = super(EventForm, self).clean()
        if self.cleaned_data.has_key('coordinates'):
            coordinates = self.cleaned_data['coordinates']
            if coordinates:
                self.instance.coordinates = Point(
                        float(coordinates['longitude']),
                        float(coordinates['latitude']) )
            else:
                self.instance.coordinates = None
        else:
            self.instance.coordinates = None
        return self.cleaned_data

class SimplifiedEventForm( ModelForm ): # {{{1
    """ ModelForm for Events with only the fields `title`, `start`, `tags`,
    """
    where = CharField( max_length = 100, required = False )
    when = DatesTimesField()
    web = URLFieldExtended(verify_exists=True)
    def __init__(self, *args, **kwargs):
        super(SimplifiedEventForm, self).__init__(*args, **kwargs)
        self.fields['title'].label = _(u'What')
        self.fields['title'].widget.attrs["size"] = 70
        self.fields['tags'].widget.attrs["size"] = 70
        self.fields['where'].label = _(u'Where')
        self.fields['where'].help_text = \
                _(u'Example: Malmöer Str. 6, Berlin, DE')
        self.fields['when'].label = _(u'When')
        self.fields['when'].help_text = \
                _(u"Examples: '25 Oct 2006', '2010-02-27', " \
                "'2010-02-27 11:00', '2010-02-27 11:00-13:00'")
        #self.fields['title'].widget.attrs["size"] = 42
        #self.fields['tags'].widget.attrs["size"] = 42
        #self.fields['web'].widget.attrs["size"] = 42
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        fields = ('title', 'tags',)
    def clean( self ):
        """ checks that there is no other event with the same name and start
        date """
        # see # http://docs.djangoproject.com/en/1.3/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
        self.cleaned_data = super(SimplifiedEventForm, self).clean()
        title = self.cleaned_data.get("title", None)# neccesary field, no checks
        when = self.cleaned_data.get("when", None)
        if title and when:
            start = when['start']   # neccesary field, no checks
            if Event.objects.filter( title = title, start = start ).exists():
                raise ValidationError( _('There is already an event with the ' \
                        'same title and start date ' \
                        '(for events taking place in different locations ' \
                        'at the same day, create different events with ' \
                        'a differentiated toponym in the title).' ) )
        return self.cleaned_data

class DeleteEventForm(Form): # {{{1
    reason = CharField( required = True, max_length = 100,
            label = _(u'Reason for the deletion'),
            help_text = _(u'please summarize the reason for the deletion' \
                    ' (maximum 100 characters).') )
    redirect = IntegerField( required = False,
            label = _(u"Number of the event to redirect to" \
                    " (or blank for no redirection)"),
            help_text = _(u'If there is another event holding the ' \
                    'information of this one (e.g. if this one is a ' \
                    'duplicate), add here the number of that event.') )
    def __init__(self, *args, **kwargs):
        super(DeleteEventForm, self).__init__(*args, **kwargs)
        self.fields['redirect'].validators.append( validate_event_exists )
        self.fields['reason'].widget.attrs["size"] = 50
        self.fields['redirect'].widget.attrs["size"] = 5

class NewGroupForm(ModelForm): # {{{1
    """ ModelForm for Group with only the fields `name` and `description` """
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Group
        fields = ('name', 'description',)

class AddEventToGroupForm(Form): # {{{1
    """ Form with a overriden constructor that takes an user and an event and
    provides selectable group names in which the user is a member of and the
    event is not already in the group. """
    grouplist = ModelMultipleChoiceField(
            queryset=Group.objects.none(), widget=CheckboxSelectMultiple())
    def __init__(self, user, event, *args, **kwargs):
        super(AddEventToGroupForm, self).__init__(*args, **kwargs)
        self.fields["grouplist"].queryset = \
                Group.groups_for_add_event(user, event)
        self.fields['grouplist'].label = _(u'Groups:')

class InviteToGroupForm(Form): # {{{1
    """ Form for a user name to invite to a group """
    group_id = IntegerField(widget=HiddenInput)
    # TODO: use the constrains of the model User
    username = CharField(max_length=30)
    def __init__(self, *args, **kwargs):
        super(InviteToGroupForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = _(u'Username')
    def clean(self):
        """ Checks that the user and group exist and the user is not in the
        group already """
        # see http://docs.djangoproject.com/en/1.2/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
        cleaned_data = self.cleaned_data
        group_id = cleaned_data.get("group_id")
        username = cleaned_data.get("username")
        if group_id and username:
            # no errors found so far
            try:
                group = Group.objects.get( id = group_id )
                user = User.objects.get( username = username )
                if Membership.objects.filter(
                        user = user, group = group).exists():
                    msg = _( u"This user is already in the group" )
                    self._errors['username'] = self.error_class([msg])
                    del cleaned_data['username']
            except Group.DoesNotExist:
                msg = _( u"The group doesn't exist" )
                self._errors['group_id'] = self.error_class([msg])
                del cleaned_data['group_id']
            except User.DoesNotExist:
                msg = _( u"The user doesn't exist" )
                self._errors['username'] = self.error_class([msg])
                del cleaned_data['username']
        return cleaned_data
    # TODO: accept also an email and create an account with the username as
    # email and a random generated password sent by email to the user
    # (encrypted if possible)
