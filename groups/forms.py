import re
from django.forms import CharField, Form, ModelForm, ValidationError
from gridcalendar.groups.models import Group, Calendar

class NewGroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'description',)

class AddEventToGroupForm(ModelForm):
    class Meta:
        model = Calendar
        fields = ('group',)

class InviteToGroupForm(Form):
    username = CharField(max_length=30)

