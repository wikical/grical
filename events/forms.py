import re
from django.forms import ModelForm, ValidationError
from gridcalendar.events.models import Event

class EventForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs["size"] = 60
        self.fields['tags'].widget.attrs["size"] = 60
    class Meta:
        model = Event
    def clean_tags(self):
        data = self.cleaned_data['tags']
        if re.search("[^ \-\w]", data, re.UNICODE):
            raise ValidationError("Punctuation marks are not allowed!")
        # Always return the cleaned data, whether you have changed it or not.
        return data

class EventFormAnonymous(EventForm):
    class Meta:
        model = Event
        exclude = ('public',)

class SimplifiedEventForm(EventForm):
    class Meta:
        model = Event
        fields = ('title', 'start', 'tags', 'public')

class SimplifiedEventFormAnonymous(EventForm):
    class Meta:
        model = Event
        fields = ('title', 'start', 'tags')

