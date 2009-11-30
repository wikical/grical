import re
from django.forms import ModelForm, ValidationError
from gridcalendar.groups.models import Group, Calendar

class NewGroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ('name', 'description',)

class AddEventToGroupForm(ModelForm):
    class Meta:
        model = Calendar
        fields = ('group',)
#    def __init__(self, *args, **kwargs):
#        super(AddEventToGroupForm, self).__init__(*args, **kwargs)
#        if self.instance:
#            self.fields['group'].queryset = Group.objects.filter(membership__user=self.data['user_id'])


