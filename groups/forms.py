import re
from django.forms import ModelForm, ValidationError
from gridcalendar.groups.models import Group

class NewGroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'description')


