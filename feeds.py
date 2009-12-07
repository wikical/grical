import hashlib
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from gridcalendar.events.models import Event
from gridcalendar.groups.models import Group, Membership
from gridcalendar import settings
from django.contrib.auth.models import User

class FeedAllComingEvents(Feed):
    title = "All coming events"
    link = "/"
    description = "All upcoming events."

    def items(self):
        return Event.objects.order_by('start')[:settings.FEED_SIZE]

class FeedGroupEvents(Feed):
    title_template = 'feeds/groupevents_title.html'
    description_template = 'feeds/groupevents_description.html'

    def get_object(self, bits):
        if len(bits) != 3:
            raise ObjectDoesNotExist
        group_id = bits[0]
        user_id = bits[1]
        token = bits[2]
        g = Group.objects.filter(id=group_id)
        u = User.objects.filter(id=user_id)
        if (token == hashlib.sha512("%s!%s!%s" % (settings.SECRET_KEY, group_id, user_id)).hexdigest()) and (len(Membership.objects.filter(group=g).filter(user=u)) == 1):
            return Group.objects.get(id=group_id)
        else:
            return None

    def title(self, obj):
        if obj is None:
            return "You are not allowed to view this feed."
        else:
            return "events in group '%s'" % obj.name

    def link(self, obj):
        if obj is None:
            return '/'
        elif not obj:
            raise FeedDoesNotExist
        else:
            return obj.get_absolute_url()

    def description(self, obj):
        if obj is None:
            return "You are not allowed to view this feed."
        else:
            return "events in group %s" % obj.name

    def items(self, obj):
        if obj is None:
            return Event.objects.none()
        else:
            return Event.objects.filter(group=obj).order_by('start')[:settings.FEED_SIZE]

# does not work, because 'datetime.date' object has no attribute 'tzinfo'
#    def item_pubdate(self, item):
#        return item.start

