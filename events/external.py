#import datetime
#from time import strftime
#import re

#from django import forms
#from django.db.models import Q
#from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
#from django.template import RequestContext
from django.utils.translation import ugettext as _
#from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail, BadHeaderError

from gridcalendar.events.views import list_search_get
from gridcalendar.events.models import Filter

#from gridcalendar.events.forms import SimplifiedEventForm, SimplifiedEventFormAnonymous, EventForm, EventFormAnonymous, FilterForm


def mail_notif():

    site = Site.objects.get(pk=1)

#    users = User.objects.all()
    users = User.objects.filter(username='miernik')

    for u in users:
        to_email = u.email
        user_filters = Filter.objects.filter(user=u).filter(email=True)

# user_events will be a list of dictionaries containing event data
        user_events = list()

        for fff in user_filters:
            search_results = list_search_get(fff.query)['list_of_events']
            search_error = list_search_get(fff.query)['errormessage']
            if search_error == '':
                fff_len = len(search_results)
                if fff_len <= 10:
                    show = fff_len
                else:
                    show = 10
                for event in search_results[0:show]:
                    user_events.append(event)
            else:
                assert False

            del fff_len
            del search_error

        context = {
            'user_events': user_events,
            'site': site,
        }

        print user_events

        subject = 'notification about new events on ' + site.domain
#       subject = render_to_string('events/notif_email_subject.txt', context)
        message = render_to_string('events/notif_email.txt', context)
        from_email = 'noreply@' + site.domain
        if subject and message and from_email:
#            print subject
#            print message
#            print from_email
#            print to_email
#            try:
                send_mail(subject, message, from_email, [to_email])
#            except BadHeaderError:
#                assert False


