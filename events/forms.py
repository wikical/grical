# -*- coding: utf-8 -*-

import re

from django.forms import CharField, IntegerField, HiddenInput, ModelMultipleChoiceField
from django.forms import Form, ModelForm, ValidationError
from django.forms import CheckboxSelectMultiple, SelectMultiple

from django.contrib.auth.models import User

from gridcalendar.events.models import Event
from gridcalendar.events.models import Filter, Group, Membership, Calendar


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

class SimplifiedEventForm(EventForm):
    class Meta:
        model = Event
        fields = ('title', 'start', 'tags', 'public')

class SimplifiedEventFormAnonymous(EventForm):
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

