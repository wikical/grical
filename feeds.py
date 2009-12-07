from django.contrib.syndication.feeds import Feed
from gridcalendar.events.models import Event
from gridcalendar.groups.models import Group
from gridcalendar import settings

class FeedAllComingEvents(Feed):
    title = "All coming events"
    link = "/"
    description = "All upcoming events."

    def items(self):
        return Event.objects.order_by('start')[:settings.FEED_SIZE]

class FeedGroupEvents(Feed):
    title_template = 'feeds/groupevents_title.html'
    description_template = 'feeds/groupevents_description.html'

    def get_object(self, group_id):
        if len(group_id) < 1:
            raise ObjectDoesNotExist
        return Group.objects.get(id=group_id[0])

    def title(self, obj):
        return "events in group '%s'" % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return "events in group %s" % obj.name

    def items(self, group_id):
        if 1 == 0:
            return Event.objects.filter(group=group_id).order_by('start')[:settings.FEED_SIZE]
        else:
            return None

# does not work, because 'datetime.date' object has no attribute 'tzinfo'
#    def item_pubdate(self, item):
#        return item.start

