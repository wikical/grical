from django.contrib.syndication.views import feed
from gridcalendar.feeds import FeedAllComingEvents, FeedGroupEvents, FeedSearchEvents

class RssForSearchAuth():

    def __call__(self, request, query):
        f = feed(request='', url='/s/1/', feed_dict= { u's': FeedSearchEvents })
        return f
#        assert False






def rss_for_search(request, query):
        f = feed(request = request, url = 's/debian', feed_dict = {
            u's': FeedSearchEvents,
            u'test': FeedAllComingEvents,
        })
        return f
