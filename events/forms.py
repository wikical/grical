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


import re

from django.forms import CharField, IntegerField, HiddenInput, ModelMultipleChoiceField, URLField
from django.forms import Form, ModelForm, ValidationError, TextInput
from django.forms import CheckboxSelectMultiple, SelectMultiple

from django.contrib.auth.models import User

from gridcalendar.events.models import Event, EventUrl, EventDeadline, EventSession
from gridcalendar.events.models import Filter, Group, Membership, Calendar
from gridcalendar.settings_local import DEBUG


def getEventForm(user):
    """returns a simplied event form with or without the public field"""
    if user.is_authenticated():
        return SimplifiedEventForm()
    return SimplifiedEventFormAnonymous()


class FilterForm(ModelForm):
    class Meta:
        model = Filter
        exclude = ('user',)

class EventForm(ModelForm):
    """Form to edit all fields except 'public'"""
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs["size"] = 60
        self.fields['tags'].widget.attrs["size"] = 60
    class Meta:
        model = Event
        exclude = ('public',) # public field cannot be edited after creation
    def clean_tags(self):
        data = self.cleaned_data['tags']
        if re.search("[^ \-\w]", data, re.UNICODE):
            raise ValidationError("Punctuation marks are not allowed!")
        # Always return the cleaned data, whether you have changed it or not.
        return data

class EventUrlForm(ModelForm):
    class Meta:
        model = EventUrl

class EventDeadlineForm(ModelForm):
    class Meta:
        model = EventDeadline

class EventSessionForm(ModelForm):
    """ A ModelForm for an EventSession with small sizes for the widget of some
        fields. """
    # TODO: better use CSS: modify the widget to add a html css class name.
    def __init__(self, *args, **kwargs):
        super(EventSessionForm, self).__init__(*args, **kwargs)
        assert(self.fields.has_key('session_date'))
        self.fields['session_date'].widget=TextInput(attrs={'size':10})
        assert(self.fields.has_key('session_starttime'))
        self.fields['session_starttime'].widget=TextInput(attrs={'size':5})
        assert(self.fields.has_key('session_endtime'))
        self.fields['session_endtime'].widget=TextInput(attrs={'size':5})
    class Meta:
        model = EventSession

class SimplifiedEventForm(EventForm):
    if DEBUG:
        web = URLField(verify_exists=False)
    else:
        web = URLField(verify_exists=True)
    # Use CSS instead of this kind of code:
    #def __init__(self, *args, **kwargs):
    #    super(EventForm, self).__init__(*args, **kwargs)
    #    self.fields['web'].widget.attrs["size"] = 60
    class Meta:
        model = Event
        fields = ('title', 'start', 'tags', 'public')

class SimplifiedEventFormAnonymous(EventForm):
    if DEBUG:
        web = URLField(verify_exists=False)
    else:
        web = URLField(verify_exists=True)
    # TODO: try to subclass from SimplifiedEventForm to avoid repeating the
    # code above
    class Meta:
        model = Event
        fields = ('title', 'start', 'tags')

class NewGroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'description',)

class AddEventToGroupForm(Form):
    grouplist = ModelMultipleChoiceField(queryset=Group.objects.none(), widget=CheckboxSelectMultiple())
    def __init__(self, u, e, *args, **kwargs):
        super(AddEventToGroupForm, self).__init__(*args, **kwargs)
        self.fields["grouplist"].queryset = Group.objects.filter(members=u).exclude(events=e)

class InviteToGroupForm(Form):
    group_id = IntegerField(widget=HiddenInput)
    username = CharField(max_length=30)
    def clean(self):
        cleaned_data = self.cleaned_data
        group_id = cleaned_data.get("group_id")
        username = cleaned_data.get("username")
        g = Group.objects.get(id=group_id)
        u = User.objects.filter(username=username)
        user_in_group = Membership.objects.filter(user=u, group=g)
        if len(user_in_group) > 0:
                raise ValidationError("This user is already in this group.")
        return cleaned_data
