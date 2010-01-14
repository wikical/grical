from django.contrib.syndication.views import feed
from gridcalendar.feeds import FeedAllComingEvents, FeedGroupEvents, FeedSearchEvents, FeedFilterEvents

def rss_for_search(request, query):
        f = feed(request = request, url = 's/' + query, feed_dict = {
            u's': FeedSearchEvents,
        })
        return f

#---------------------------

def rss_for_filter(request, filter_id):
        f = feed(request = request, url = 'f/' + filter_id, feed_dict = {
            u'f': FeedFilterEvents,
        })
        return f

def rss_for_filter_auth(request, filter_id):
        return rss_for_filter(request, filter_id)

def rss_for_filter_hash(request, filter_id, user_id, hash):
        return rss_for_filter(request, filter_id)

#---------------------------

def rss_for_group(request, group_id):
        f = feed(request = request, url = 'g/' + group_id, feed_dict = {
            u'g': FeedGroupEvents,
        })
        return f

def rss_for_group_auth(request, group_id):
        return rss_for_group(request, group_id)

def rss_for_group_hash(request, group_id, user_id, hash):
        return rss_for_group(request, group_id)

#---------------------------

