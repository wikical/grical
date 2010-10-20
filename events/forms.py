#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
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

import re

from django.forms import (CharField, IntegerField, HiddenInput,
        ModelMultipleChoiceField, URLField, ModelForm, ValidationError,
        TextInput, CheckboxSelectMultiple, Form)
from django.contrib.auth.models import User

from gridcalendar.settings_local import DEBUG
from gridcalendar.events.models import (Event, EventUrl, EventDeadline,
        EventSession, Filter, Group, Membership)

def get_event_form(user):
    """returns a simplied event form with or without the public field"""
    if user.is_authenticated():
        return SimplifiedEventForm()
    return SimplifiedEventFormAnonymous()

class FilterForm(ModelForm):
    """ ModelForm using Filter excluding `user` """
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = Filter
        exclude = ('user',)

class EventForm(ModelForm):
    """ ModelForm for all editable fields of Event except `public` """
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs["size"] = 60
        self.fields['tags'].widget.attrs["size"] = 60
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        exclude = ('public',) # public field cannot be edited after creation
    def clean_tags(self): # pylint: disable-msg=C0111
        data = self.cleaned_data['tags']
        if re.search("[^ \-\w]", data, re.UNICODE):
            raise ValidationError("Punctuation marks are not allowed!")
        # Always return the cleaned data, whether you have changed it or not.
        return data

class EventUrlForm(ModelForm):
    """ ModelForm for EventUrl """
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
        self.fields['session_starttime'].widget = TextInput(attrs = {'size':5})
        assert(self.fields.has_key('session_endtime'))
        self.fields['session_endtime'].widget = TextInput(attrs = {'size':5})
    class Meta: # pylint: disable-msg=C0111,W0232,R0903
        model = EventSession

class SimplifiedEventForm(EventForm):
    """ ModelForm for Events with only the fields `title`, `start`, `tags`,
    `public` """
    if DEBUG:
        web = URLField(verify_exists=False)
    else:
        web = URLField(verify_exists=True)
    # Use CSS instead of this kind of code:
    #def __init__(self, *args, **kwargs):
    #    super(EventForm, self).__init__(*args, **kwargs)
    #    self.fields['web'].widget.attrs["size"] = 60
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        fields = ('title', 'start', 'tags', 'public')

class SimplifiedEventFormAnonymous(EventForm):
    """ ModelForm for Events with only the fields `title`, `start`, `tags`
    """
    if DEBUG:
        web = URLField(verify_exists=False)
    else:
        web = URLField(verify_exists=True)
    # TODO: try to subclass from SimplifiedEventForm to avoid repeating the
    # code above
    class Meta:  # pylint: disable-msg=C0111,W0232,R0903
        model = Event
        fields = ('title', 'start', 'tags')

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

class InviteToGroupForm(Form):
    """ Form for a user name to invite to a group """
    group_id = IntegerField(widget=HiddenInput)
    username = CharField(max_length=30) # TODO: use the CharField of the User
                                        # Model if possible
    def clean(self):
        """ Raises a `ValidationError` if the user is already in the group """
        cleaned_data = self.cleaned_data
        group_id = cleaned_data.get("group_id")
        username = cleaned_data.get("username")
        group = Group.objects.get(id=group_id)
        user = User.objects.filter(username=username)
        user_in_group = Membership.objects.filter(user=user, group=group)
        if len(user_in_group) > 0:
            raise ValidationError("This user is already in this group.")
        return cleaned_data
