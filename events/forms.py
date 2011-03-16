#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
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

""" Forms """

# imports {{{1
import re
import datetime
import urlparse

from django.core import validators
from django.forms import ( CharField, IntegerField, HiddenInput,
        ModelMultipleChoiceField, ModelForm, ValidationError,
        TextInput, CheckboxSelectMultiple, Form, Field, DateField )
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from gridcalendar.settings_local import DEBUG
from gridcalendar.events.models import (Event, EventUrl, EventDeadline,
        EventSession, Filter, Group, Membership)
from gridcalendar.events.utils import validate_year

def _date(string): # {{{1
    """ parse a date in the format ``yyyy-mm-dd`` using
    ``gridcalendar.events.utils.validate_year """
    parsed_date = datetime.datetime.strptime(string, '%Y-%m-%d').date()
    validate_year( parsed_date )
    return parsed_date

def _time(string): # {{{1
    """ parse a time in the format: hh:mm """
    return datetime.datetime.strptime(string, '%H:%M').time()

# Tue Mar  8 10:08:46 CET 2011:
# From Django repository in order to append 'http' when missing.
# Additionally, added support for in-URL basic AUTH ( code found at
# http://code.djangoproject.com/ticket/9791 )
class URLFieldExtended(CharField):
    default_error_messages = {
        'invalid': _(u'Enter a valid URL.'),
        'invalid_link': _(u'This URL appears to be a broken link.'),
    }

    def __init__(self, max_length=None, min_length=None, verify_exists=False,
            validator_user_agent=validators.URL_VALIDATOR_USER_AGENT,
            *args, **kwargs):
        super(URLFieldExtended, self).__init__(
                max_length, min_length, *args, **kwargs )
        self.validators.append( validators.URLValidator(
            verify_exists=verify_exists,
            validator_user_agent=validator_user_agent ) )

    def to_python(self, value):
        if value:
            split_result = urlparse.urlsplit(value) # returns a SplitResult
            url_fields = list( split_result )
            if not url_fields[0]:
                # If no URL scheme given, assume http://
                url_fields[0] = 'http'
            if not url_fields[1]:
                # Assume that if no domain is provided, that the path segment
                # contains the domain.
                url_fields[1] = url_fields[2]
                url_fields[2] = ''
                # Rebuild the url_fields list, since the domain segment may now
                # contain the path too.
                value = urlparse.urlunsplit(url_fields)
                url_fields = list(urlparse.urlsplit(value))
            if not url_fields[2]:
                # the path portion may need to be added before query params
                url_fields[2] = '/'
            value = urlparse.urlunsplit( url_fields )
        return super( URLFieldExtended, self ).to_python( value )

class DatesTimesField(Field): # {{{1
    """ processes one or two dates and optionally one or two times, returning a
    dictionary with possible keys: start_date, end_date, start_time, end_time

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
    >>> d = dt.to_python('2010-01-25 2010-01-26')
    >>> d = dt.to_python('2010-01-25 10:00')
    >>> d = dt.to_python('2010-01-25 10:00 2010-01-26 18:00')
    >>> d = dt.to_python('2010-01-25 10:00 11:00')
    >>> d = dt.to_python('2010-01-25 10:00-11:00')
    >>> d = dt.to_python('25 October, 2006')
    """
    def to_python(self, value):
        """ returns a dictionary with four values: start_date, end_date,
        start_time, end_time """
        re_d = \
            re.compile( r'^\s*(\d\d\d\d-\d\d-\d\d)\s*$', re.UNICODE )
        re_d_d = \
            re.compile(r'^\s*(\d\d\d\d-\d\d-\d\d)\s+(\d\d\d\d-\d\d-\d\d)\s*$',
                    re.UNICODE)
        re_d_t = \
            re.compile(r'^\s*(\d\d\d\d-\d\d-\d\d)\s+(\d\d:\d\d)\s*$',
                    re.UNICODE)
        re_d_t_d_t = \
            re.compile(r"""
                ^\s*(\d\d\d\d-\d\d-\d\d)
                \s+(\d\d:\d\d)
                \s+(\d\d\d\d-\d\d-\d\d)
                \s+(\d\d:\d\d)\s*$""", re.UNICODE | re.X )
        re_d_t_t = \
            re.compile(r"""
                ^\s*(\d\d\d\d-\d\d-\d\d)
                \s+(\d\d:\d\d)
                \s+(\d\d:\d\d)\s*$""", re.UNICODE | re.X )
        re_d_t_t =   re.compile( r"""
            ^\s*(\d\d\d\d-\d\d-\d\d) # beginning, optional spaces, start date
             \s+(\d\d:\d\d)          # start time after one ore more spaces
             (?:(?:\s+)|(?:\s*-\s*)) # one or more spaces, alternatively -
             (\d\d:\d\d)\s*$         # end time before optional spaces""",
            re.UNICODE | re.X )
        try:
            matcher = re_d.match( value )
            if matcher:
                return {'start_date': _date(matcher.group(1)),}
            matcher = re_d_d.match( value )
            if matcher:
                return {'start_date': _date(matcher.group(1)),
                        'end_date': _date(matcher.group(2))}
            matcher = re_d_t.match(value)
            if matcher:
                return {'start_date': _date(matcher.group(1)),
                        'start_time': _time(matcher.group(2))}
            matcher = re_d_t_d_t.match(value)
            if matcher:
                return {'start_date': _date(matcher.group(1)),
                        'start_time': _time(matcher.group(2)),
                        'end_date': _date(matcher.group(3)),
                        'end_time': _time(matcher.group(4))}
            matcher = re_d_t_t.match(value)
            if matcher:
                return {'start_date': _date(matcher.group(1)),
                        'start_time': _time(matcher.group(2)),
                        'end_time': _time(matcher.group(3))}
        except (TypeError, ValueError), e:
            pass
        except ValidationError, e:
            # the validationError comes from utils.validate_year and the error
            # message is translated
            raise e
        # No matches. We try now DateField
        return { 'start_date': DateField().clean( value ) }

    def validate(self, value):
        """ checks that dates and times are in order, i.e. start before end """
        if value.has_key('end_date'):
            if value['start_date'] > value['end_date']:
                raise ValidationError( _('end date is before start date') )
        if value.has_key('end_time'):
            if value['start_time'] > value['end_time']:
                raise ValidationError( _('end time is before start time') )

def get_event_form(user): # {{{1
    """returns a simplied event form with or without the public field"""
    """ returns a dictionary with four values: start_date, end_date,
    start_time, end_time """

    if user.is_authenticated():
        return SimplifiedEventForm()
    return SimplifiedEventFormAnonymous()

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


class CoordinatesField( CharField ):
    default_error_messages = {
            'invalid': _(u'Enter a valid pair of coordinates'),
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
        regex = re.compile(r'(-?\s*\d+\.\d+)\s*[,;:+| ]\s*(-?\s*\d+\.\d+)')
        matcher = regex.match( value )
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


class EventForm(ModelForm): # {{{1
    """ ModelForm for all editable fields of Event except `public` """
    coordinates = CoordinatesField( max_length = 26, required = False )
    # TODO: put this in the right position within the form, see
    # http://stackoverflow.com/questions/350799/how-does-django-know-the-order-to-render-form-fields
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        if kwargs.has_key('instance'):
            # not a new event and ``public`` cannot be changed after creation
            self.fields['public'].widget = HiddenInput()
            self.fields['latitude'].widget = HiddenInput()
            self.fields['longitude'].widget = HiddenInput()
            # We use a single field called 'coordinates' for
            # showing/editing/entering latitude and longitude, we populate now
            # 'coordinates' with the values of event.latitude and
            # event.longitude
            instance = kwargs['instance']
            coordinates_value = u''
            if instance.latitude:
                coordinates_value += str( instance.latitude )
            if instance.longitude:
                coordinates_value += ", " + str( instance.longitude )
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
    def clean_tags(self): # pylint: disable-msg=C0111
        data = self.cleaned_data['tags']
        if re.search("[^ \-\w]", data, re.UNICODE):
            raise ValidationError(_(u"Punctuation marks are not allowed"))
        # Always return the cleaned data, whether you have changed it or not.
        return data
    def clean_coordinates( self ):
        coordinates = self.cleaned_data['coordinates']
        if coordinates:
            self.cleaned_data['latitude'] = coordinates['latitude']
            self.cleaned_data['longitude'] = coordinates['longitude']

class SimplifiedEventForm(EventForm): # {{{1
    """ ModelForm for Events with only the fields `title`, `start`, `tags`,
    `public` """
    where = CharField( max_length = 100, required = False )
    when = DatesTimesField()
    web = URLFieldExtended(verify_exists=True)
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        del self.fields['coordinates']
        self.fields['title'].label = _(u'What')
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
        fields = ('title', 'tags', 'public')

class SimplifiedEventFormAnonymous(SimplifiedEventForm): # {{{1
    """ ModelForm for Events with only the fields `title`, `start`, `tags`
    """
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        fields = ('title', 'tags')

class EventUrlForm(ModelForm): # {{{1
    """ ModelForm for EventUrl """
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = EventUrl

class EventDeadlineForm(ModelForm):
    """ ModelForm for EventDeadline """
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = EventDeadline

class EventSessionForm(ModelForm):
    """ A ModelForm for an EventSession with small sizes for the widget of some
        fields. """
    # TODO: better use CSS: modify the widget to add a html css class name.
    def __init__(self, *args, **kwargs):
        super(EventSessionForm, self).__init__(*args, **kwargs)
        assert(self.fields.has_key('session_date'))
        self.fields['session_date'].widget = TextInput(attrs = {'size':10})
        assert(self.fields.has_key('session_starttime'))
        self.fields['session_starttime'].widget = TextInput(
                attrs = { 'size': 5, 'format': '%H:%M' } )
        assert(self.fields.has_key('session_endtime'))
        self.fields['session_endtime'].widget = TextInput(
                attrs = { 'size': 5, 'format': '%H:%M' } )
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = EventSession

class NewGroupForm(ModelForm):
    """ ModelForm for Group with only the fields `name` and `description` """
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Group
        fields = ('name', 'description',)

class AddEventToGroupForm(Form):
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

class InviteToGroupForm(Form):
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
