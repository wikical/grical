from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.management.base import NoArgsCommand

from gridcal.models import Filter, GroupInvitation
from gridcal.views import list_search_get

def mail_notif():
    site = Site.objects.get(pk=1)


    # TODO: in production version uncomment the .all() and remove the "miernik"!
    # users = User.objects.all()
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
               try:
                    send_mail(subject, message, from_email, [to_email])
               except BadHeaderError:
                   assert False


"""
A management command which deletes expired group invitations from the database.

Calls ``GroupInvitation.objects.delete_expired_invitations()``, which
contains the actual logic for determining which invitations are deleted.

"""

class Command(NoArgsCommand):
    help = "Delete expired group invitations from the database"

    def handle_noargs(self, **options):
        GroupInvitation.objects.delete_expired_invitations()

