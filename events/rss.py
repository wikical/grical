# -*- coding: utf-8 -*-

import hashlib

from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.shortcuts import render_to_response

from django.contrib.syndication.views import feed
from django.contrib.auth.models import User

import settings

from gridcalendar.events.feeds import FeedAllComingEvents, FeedGroupEvents, FeedSearchEvents, FeedFilterEvents
from gridcalendar.events.forms import getEventForm
from gridcalendar.events.models import Group, Membership

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
    g = Group.objects.filter(id=group_id)
    u = User.objects.filter(id=user_id)
    if (hash == hashlib.sha256("%s!%s" % (settings.SECRET_KEY, user_id)).hexdigest()) and (len(Membership.objects.filter(group=g).filter(user=u)) == 1):
        return rss_for_group(request, group_id)
    else:
        return render_to_response('error.html',
                {'title': 'error', 'form': getEventForm(request.user),
                'message_col1': _("You are not allowed to see this RSS feed") + "."},
                context_instance=RequestContext(request))


#---------------------------

