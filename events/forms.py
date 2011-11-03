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

""" Forms """

# imports {{{1
from calendar import HTMLCalendar # TODO use LocaleHTMLCalendar
from dateutil.parser import parse
import re
import datetime
import urllib2
import urlparse

from django.db import models
from django.contrib.gis.geos import Point
from django.core import validators
# import django.forms as forms
import floppyforms as forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from gridcalendar.settings_local import DEBUG
from gridcalendar.events.models import (Event, EventUrl, EventDate,
        EventSession, Filter, Group, Membership )
from gridcalendar.events.search import COORDINATES_REGEX
from gridcalendar.events.utils import ( validate_year, validate_event_exists,
        GermanParserInfo, SpanishParserInfo )

def _date(string): # {{{1
    """ parse a date in the format ``yyyy-mm-dd`` using
    ``gridcalendar.events.utils.validate_year """
    parsed_date = datetime.datetime.strptime(string.strip(), '%Y-%m-%d').date()
    validate_year( parsed_date )
    return parsed_date

def _time(string): # {{{1
    """ parse a time in the format: hh:mm """
    return datetime.datetime.strptime(string.strip(), '%H:%M').time()

class DatePicker(forms.DateInput):
    template_name = 'datepicker.html'
    # NOTE: the form in which this widget is used will add all media
    # definitions of all its widgets. Remember to add that media definition of
    # the form in the template with:
    # {% block extraheaders %}
    #     {{ form.media }}
    # {% endblock %}
    class Media:
        js = (
            'js/jquery.min.js',
            'js/jquery-ui.min.js',
        )
        css = {
            'all': (
                'css/jquery-ui.css',
            )
        }

class URLValidatorExtended( validators.URLValidator ): # {{{1
    """ Like ``URLValidation`` but adding support to HTTP Basic Auth.
    See https://code.djangoproject.com/ticket/9791 """
    def __call__( self, value ):
        try:
            return super( URLValidatorExtended, self ).__call__( value )
        except forms.ValidationError, err:
            # we check now http basic auth
            url = urlparse.urlsplit( value )
            if url.scheme.lower() != "http" and url.scheme.lower() != "https":
                raise forms.ValidationError(
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
                raise forms.ValidationError(
                        _( u"Couldn't get URL %(url)s: %(error)s" ) % 
                        { 'url': value, 'error': e} )
            except urllib2.URLError, e:
                raise forms.ValidationError(
                    "Couldn't connect to %s: %s" %
                        _( u"Couldn't connect to %(url)s: %(error)s" ) % 
                        { 'url': u[1], 'error':e.reason } )

class URLFieldExtended(forms.CharField): #{{{1
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

    def to_python(self, value):
        value = value.strip()
        return super( URLFieldExtended, self ).to_python( value )

class DatesTimesField(forms.Field): # {{{1
    """ processes one or two dates and optionally one or two times, returning a
    dictionary with possible keys: startdate, enddate, starttime, endtime

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

    - some other English formats recognized by dateutil.parser.parse
    - some other English formats recognized by dateutil.parser.parse with
      custom parserinfo (see utils.py)

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
        """ returns a dictionary with four values: startdate, enddate,
        starttime, endtime """
        if value:
            value = value.strip()
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
                return {'startdate': _date(matcher.group(1)),}
            matcher = re_d_d.match( value )
            if matcher:
                return {'startdate': _date(matcher.group(1)),
                        'enddate': _date(matcher.group(2))}
            matcher = re_d_t.match(value)
            if matcher:
                return {'startdate': _date(matcher.group(1)),
                        'starttime': _time(matcher.group(2))}
            matcher = re_d_t_d_t.match(value)
            if matcher:
                return {'startdate': _date(matcher.group(1)),
                        'starttime': _time(matcher.group(2)),
                        'enddate': _date(matcher.group(3)),
                        'endtime': _time(matcher.group(4))}
            matcher = re_d_t_t.match(value)
            if matcher:
                return {'startdate': _date(matcher.group(1)),
                        'starttime': _time(matcher.group(2)),
                        'endtime': _time(matcher.group(3))}
        except (TypeError, ValueError), e:
            pass
        except forms.ValidationError, e:
            # the validationError comes from utils.validate_year and the error
            # message is translated
            raise e
        # No matches, we try now dateutil.parser.parse without and with custom
        # parseinfos
        if value: # we need this here because parse('') returns today
            parseinfos = [ None, GermanParserInfo, SpanishParserInfo ]
            for parseinfo in parseinfos:
                try:
                    if not parseinfo:
                        dati = parse( value )
                    else:
                        dati = parse( value, parserinfo = parseinfo() )
                    if dati.hour==0 and dati.minute==0 and not " 00" in value:
                        # time was not specified
                        return { 'startdate': dati.date(), }
                    # time was specified
                    return  { 'startdate': dati.date(),
                              'starttime': dati.time(), }
                except ValueError:
                    pass
        # No matches. We try now DateField
        # TODO: try DateField with different language settings, and also
        # DateTimeField
        return { 'startdate':
                forms.DateField( required = self.required ).clean( value ) }

    def validate(self, value):
        """ checks that dates and times are in order, i.e. startdate before
        enddate """
        if value.has_key('enddate'):
            if value['startdate'] > value['enddate']:
                raise forms.ValidationError( _('end date is before start date') )
        if value.has_key('starttime') and value.has_key('endtime'):
            if value['starttime'] > value['endtime']:
                raise forms.ValidationError( _('end time is before start time') )

class DateExtendedField(DatesTimesField): # {{{1
    def __init__(self, *args, **kwargs):
        super( DateExtendedField, self ).__init__(
                *args, widget = DatePicker, **kwargs )
        #self.widget = DatePicker
    def to_python(self, value):
        datestimes = super( DateExtendedField, self ).to_python( value )
        return datestimes['startdate']
    def validate(self, value):
        return

class CoordinatesField( forms.CharField ): #{{{1
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
            raise forms.ValidationError(_(u'No two separate numbers with decimals'))
        return {
            'latitude':  float ( matcher.group(1) ),
            'longitude': float ( matcher.group(2) )}
    @staticmethod
    def validate_latitude( value ):
        if value['latitude'] < -90 or value['latitude'] > 90:
            raise forms.ValidationError( _( u'Latitude is not within (-90,90)' ) )
    @staticmethod
    def validate_longitude( value ):
        if value['longitude'] < -180 or value['longitude'] > 180:
            raise forms.ValidationError( _(u'Longitude is not within (-180,180)') )

class EventSessionForm( forms.ModelForm ):
    def __init__(self, *args, **kwargs):
        super(EventSessionForm, self).__init__(*args, **kwargs)
        self.fields['session_starttime'].widget.format = '%H:%M'
        self.fields['session_endtime'].widget.format = '%H:%M'
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = EventSession

class FilterForm(forms.ModelForm): # {{{1
    """ ModelForm using Filter excluding `user` """
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = Filter
        widgets = { 'user' : forms.HiddenInput(), }
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
    #        raise forms.ValidationError(
    #                 _(u"You already have a filter with the name " \
    #                 "'%(filter_name)s'. Choose another name") % \
    #                         {'filter_name': data.get('name')} )
    #    return data

class EventForm(forms.ModelForm): # {{{1
    """ ModelForm for all user editable fields of an Event, a custom coordinate
    field and fields for all days of two years from now """
    startdate = DateExtendedField( required = True )
    enddate = DateExtendedField( required = False )
    coordinates = CoordinatesField( max_length = 26, required = False )
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        # http://stackoverflow.com/questions/350799/how-does-django-know-the-order-to-render-form-fields
        self.fields.keyOrder = ['acronym', 'title', 'startdate', 'starttime',
            'enddate', 'endtime', 'timezone', 'tags', 'country', 'city',
            'postcode', 'address', 'coordinates', 'description']
        self.fields['startdate'].label = _(u'Start date')
        self.fields['enddate'].label = _(u'End date')
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
            # we also populate start and end dates:
            self.fields['startdate'].initial = instance.startdate
            self.fields['enddate'].initial = instance.enddate
        self.fields['starttime'].widget.format = '%H:%M'
        self.fields['endtime'].widget.format = '%H:%M'
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        exclude = ('coordinates',) # excludes the model field 'coordinates'
    def clean( self ):
        """ it adds the value of coordinates to the Event instance,
        checks that there is no other event with the same name and start
        date, checks that startdate if before enddate, checks that
        starttime is before endtime, and checks that if enddate != startdate it
        is not recurring """
        # see http://docs.djangoproject.com/en/1.3/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
        # coordinates
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
        # checks uniqueness of title and startdate
        title = self.cleaned_data.get("title", None)
        startdate = self.cleaned_data.get("startdate", None)
        if title and startdate:
            same_title_date = Event.objects.filter(
                    title = title,
                    dates__eventdate_name = 'start',
                    dates__eventdate_date = startdate )
            if hasattr(self, 'instance') and self.instance and \
                    hasattr(self.instance, 'id'):
                if same_title_date.exclude(id = self.instance.id).exists():
                    raise same_title_day_validation_error
            elif same_title_date.exists():
                raise same_title_day_validation_error
        # checks that startdate is before enddate if present
        enddate = self.cleaned_data.get("enddate", None)
        if startdate and enddate:
            if enddate < startdate:
                raise forms.ValidationError( _('enddate must be after startdate') )
            if enddate != startdate and self.instance.recurring:
                raise forms.ValidationError( _('recurring events cannot occur ' \
                        'more than one day') )
        # checks starttime and endtime constrains
        starttime = self.cleaned_data.get("starttime", None)
        endtime = self.cleaned_data.get("endtime", None)
        if endtime and not starttime:
            raise forms.ValidationError( 
                    _('endtime without starttime is not allowed') )
        if starttime and endtime and endtime < starttime:
            raise forms.ValidationError( _('endtime must be after starttime') )
        return self.cleaned_data

same_title_day_validation_error = forms.ValidationError(
        _('There is already an event with the same title and start date ' \
            '(for events taking place in different locations at the same ' \
            'day, create different events with a differentiated toponym in ' \
            ' the title).' ) )

def get_field_attr( field_name, field_attr ):
    """ returns the value of the attribute ``field_attr`` of the Event model
    field ``field_name`` """
    # from
    # http://stackoverflow.com/questions/2384436/how-to-introspect-django-model-fields
    field = models.get_model('events', 'Event')._meta.get_field_by_name(
            field_name )[0]
    return getattr( field, field_attr )

class SimplifiedEventForm( forms.ModelForm ): # {{{1
    """ ModelForm for Events with only the fields `title`, `start`, `tags`,
    """
    where = forms.CharField(
            max_length = get_field_attr( 'address', 'max_length'),
            required = False )
    when = DatesTimesField()
    web = URLFieldExtended(verify_exists=True)
    def __init__(self, *args, **kwargs):
        super(SimplifiedEventForm, self).__init__(*args, **kwargs)
        self.fields['title'].label = _(u'What')
        #self.fields['title'].widget = forms.Textarea()
        self.fields['where'].label = _(u'Where')
        self.fields['when'].label = _(u'When')
        self.fields['tags'].label = _(u'Tags or Topics')
        #self.fields['where'].help_text = \
        #        _(u'Example: Malmöer Str. 6, Berlin, DE')
        #self.fields['when'].help_text = \
        #        _(u"Examples: '25 Oct 2006', '2010-02-27', " \
        #        "'2010-02-27 11:00', '2010-02-27 11:00-13:00'")
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        fields = ('title', 'tags',)
    def clean( self ):
        """ checks that there is no other event with the same name and start
        date """
        # see http://docs.djangoproject.com/en/1.3/ref/forms/validation/#cleaning-and-validating-fields-that-depend-on-each-other
        self.cleaned_data = super(SimplifiedEventForm, self).clean()
        title = self.cleaned_data.get("title", None)# neccesary field, no checks
        when = self.cleaned_data.get("when", None)
        if title and when:
            startdate = when['startdate']   # neccesary field, no checks
            if Event.objects.filter(
                    title = title,
                    dates__eventdate_name = 'start',
                    dates__eventdate_date = startdate ).exists():
                raise same_title_day_validation_error
        return self.cleaned_data

class AlsoRecurrencesForm( forms.Form ):
    """ show options when editing an event which belongs to a recurrence """
    choices = forms.ChoiceField( label = _('Apply changes to'), choices = [
        ( 'this', _(u'only this event') ),
        ( 'past',   _(u'this and all past events') ),
        ( 'future', _(u'this and all future events') ),
        ( 'all', _(u'all events') ) ],
        widget = forms.RadioSelect )

class DeleteEventForm(forms.Form): # {{{1
    reason = forms.CharField( required = True, max_length = 100,
            label = _(u'Reason for the deletion'),
            help_text = _(u'please summarize the reason for the deletion' \
                    ' (maximum 100 characters).') )
    redirect = forms.IntegerField( required = False,
            label = _(u"Number of the event to redirect to" \
                    " (or blank for no redirection)"),
            help_text = _(u'If there is another event holding the ' \
                    'information of this one (e.g. if this one is a ' \
                    'duplicate), add here the number of that event.') )
    def __init__(self, *args, **kwargs):
        super(DeleteEventForm, self).__init__(*args, **kwargs)
        self.fields['redirect'].validators.append( validate_event_exists )

class NewGroupForm(forms.ModelForm): # {{{1
    """ ModelForm for Group with only the fields `name` and `description` """
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Group
        fields = ('name', 'description',)

class AddEventToGroupForm(forms.Form): # {{{1
    """ Form with a overriden constructor that takes an user and an event and
    rovides selectable group names in which the user is a member of and the
    event is not already in the group. """
    grouplist = forms.ModelMultipleChoiceField(
            queryset=Group.objects.none(), widget=forms.CheckboxSelectMultiple())
    def __init__(self, user, event, *args, **kwargs):
        super(AddEventToGroupForm, self).__init__(*args, **kwargs)
        self.fields["grouplist"].queryset = \
                Group.groups_for_add_event(user, event)
        self.fields['grouplist'].label = _(u'Groups:')

class InviteToGroupForm(forms.Form): # {{{1
    """ Form for a user name to invite to a group """
    group_id = forms.IntegerField(widget=forms.HiddenInput)
    # TODO: use the constrains of the model User
    username = forms.CharField(max_length=30)
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

class CalendarForm(HTMLCalendar): #TODO: use LocaleHTMLCalendar
    """ generates a HTML-calendar with a checkbox in each day
    """
    def __init__(self, *args, **kwargs):
        self.dates_iso = kwargs.pop( 'dates_iso', set() )
        self.not_editable_dates_iso = kwargs.pop(
                'not_editable_dates_iso', set() )
        super(CalendarForm, self).__init__(*args, **kwargs)
    def formatmonth(self, year, month, *args, **kwargs):
        # we save year and month for their use in formatday
        self.year, self.month = year, month
        return super(CalendarForm, self).formatmonth(
                year, month, *args, **kwargs )
    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>' # day outside month
        day_iso = datetime.date( self.year, self.month, day ).isoformat()
        if day_iso in self.not_editable_dates_iso:
            return '<td class="cal-form-day-not-editable">%d</td>' % day
        if day_iso in self.dates_iso:
            return \
                '<td class="cal-form-day-checked">' \
                '<input type="checkbox" ' \
                'name="recurrences" value="%s" checked="checked" /> ' \
                '%d</td>' % ( day_iso, day )
        else:
            return \
                '<td class="cal-form-day-unchecked">' \
                '<input type="checkbox" ' \
                'name="recurrences" value="%s" /> ' \
                '%d</td>' % ( day_iso, day )
