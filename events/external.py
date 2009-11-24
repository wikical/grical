from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from gridcalendar.events.models import Filter
from gridcalendar.events.views import list_search_get

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
                if fff_len <= fff.maxevents_email:
                    show = fff_len
                else:
                    show = maxevents_email
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

        if len(user_events) > 0:

            subject = 'notification about new events on ' + site.domain
            message = render_to_string('events/notif_email.txt', context)
            from_email = 'noreply@' + site.domain
            if subject and message and from_email:
#               try:
                    send_mail(subject, message, from_email, [to_email])
#               except BadHeaderError:
#                   assert False

