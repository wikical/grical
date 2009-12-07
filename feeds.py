from django.contrib.syndication.feeds import Feed
from gridcalendar.events.models import Event
from gridcalendar.groups.models import Group
from gridcalendar import settings

class FeedLatestEntries(Feed):
    title = "gridcalendar news"
    link = "/groups/"
    description = "Updates on changes ."

    def items(self):
        return Event.objects.order_by('-start')[:settings.FEED_SIZE]

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
        return "/"

    def description(self, obj):
        return "events in group %s" % obj.name

    def items(self, group_id):
#        group = Group.objects.filter(id=group_id)
        return Event.objects.filter(group=group_id).order_by('-start')[:settings.FEED_SIZE]
