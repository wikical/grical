from django.forms import ModelForm
from cloudcalendar.events.models import Event

class EventForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs["size"] = 60
        self.fields['tags'].widget.attrs["size"] = 60

    class Meta:
        model = Event

class SimplifiedEventForm(EventForm):
    class Meta:
        model = Event
        fields = ('title', 'start', 'tags', 'public')

class SimplifiedEventFormAnonymous(EventForm):
    class Meta:
        model = Event
        fields = ('title', 'start', 'tags')

class EventFormAnonymous(EventForm):
    class Meta:
        model = Event
        exclude = ('public',)
