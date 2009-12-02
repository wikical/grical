import re
from django.forms import CharField, IntegerField, HiddenInput, Form, ModelForm, ValidationError
from django.contrib.auth.models import User
from gridcalendar.groups.models import Group, Membership, Calendar

class NewGroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'description',)

class AddEventToGroupForm(ModelForm):
    class Meta:
        model = Calendar
        fields = ('group',)

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

