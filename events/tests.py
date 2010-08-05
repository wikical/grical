#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2010 Adam Beret Manczuk <beret@hipisi.org.pl>,
# Ivan Villanueva <iv@gridmind.org>
#
# This file is part of GridCalendar.
# 
# GridCalendar is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# GridCalendar is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the Affero GNU Generevent.idal Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

""" testing events application """
import datetime
from django.contrib.auth.models import User
from events.models import Event, Group, Filter, EventUrl
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
import re
import httplib, urllib
import hashlib
import settings
#import time
#import threading
#import random

USERS_COUNT = 10

class EventTestCase(TestCase):              #pylint: disable-msg=R0904
    """testing case for event application"""

    @staticmethod
    def user_name(user_nr):
        "cereate user name for nr"
        return "u_%02d_test" % user_nr

    @staticmethod
    def user_email(user_nr):
        "cereate user email for nr"
        return "u_%02d_test@gridcalendar.net" % user_nr

    def validate_ical(self, url):
        "validate iCalendar url"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        params = urllib.urlencode({'snip':content})
        conn = httplib.HTTPConnection("severinghaus.org")
        conn.request("POST", "/projects/icv/", params, headers)
        response = conn.getresponse()
        result = response.read()
        self.assertTrue('Congratulations' in result, content)

    def validate_rss(self, url):
        "validate rss feed data"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content
        params = urllib.urlencode({'fragment':content})
        conn = httplib.HTTPConnection("validator.w3.org")
        conn.request("POST", "/check", params)
        response = conn.getresponse()
        result = response.read()
        self.assertTrue('Congratulations' in result, content)


    @classmethod
    def get_user(cls, user_nr):
        "get user instance for nr"
        return User.objects.get(username=cls.user_name(user_nr))

    @classmethod
    def get_event(cls, user, public, future, contest=False):
        "find and return event for params"
        if contest:
            Event.objects.set_user(contest)
        else:
            Event.objects.set_user(user)
        event = Event.objects.get(title = cls.event_title(user, public, future))
        return event

    @classmethod
    def event_title(cls, user, public, future):
        "create title for event"
        user_str = user and user.username or 'USERLESS'
        when = future and 'future' or 'past'
        public_value_str = public and 'public' or 'private'
        title = "EVENT %(when)s %(user)s %(pv)s" % {
                    'when':     when,
                    'user':     user_str,
                    'pv':       public_value_str,
                    }
        return title

    @classmethod
    def create_event(cls, user=False):
        """helper function to create events for user"""
        for future, start_delta, end_delta in ((False, -36, -33),
                                             (True, 33, 36)):
            start_str = str(datetime.date.today() +
                    datetime.timedelta(start_delta))
            end_str = str(datetime.date.today() +
                    datetime.timedelta(end_delta))
            if user:
                public_value_list = [True, False]
            else:
                public_value_list = [True,]
                user = False
            for public_value in public_value_list:
                
                event = Event(
                        acronym='ACRO',
                        title=cls.event_title(user, public_value, future),
                        start=start_str,
                        end=end_str,
                        public=public_value,
                        tags='tag',
                        country='DE',
                        city='Berlin',
                        postcode='10439',
                        address='Random Street 3',
                        latitude=50.32323,
                        longitude=13.83245,
                        timezone=60,
                        description='Event description.'
                        )
                if user:
                    event.user = user
                event.save()
    
    def login_user(self, user_nr):
        "login user for id"
        login = self.client.login(username=self.user_name(user_nr), \
                                  password='p')
        return login

    def setUp(self):                            # pylint: disable-msg=C0103
        """models value initiation"""

        # create some userless events
        EventTestCase.create_event(False)
        
        # create some users and let them create some filters and events
        for user_nr in range(USERS_COUNT):
            user = User.objects.create_user(
                    username=self.user_name(user_nr),
                    email=self.user_email(user_nr),
                    password='p',
                    )
            user.save()
            event_filter = Filter(user=user,
                query='berlin',
                name=user.username + "'s filter: berlin"
                )
            event_filter.save()
            EventTestCase.create_event(user)
    
    def test_login(self):
        "testing for login"
        for user_id in range(1, 5):
            login = self.login_user(user_id)
            self.failUnless(login, 'Could not log in')
            response = self.client.get(reverse('group_new'))
            self.failUnlessEqual(response.status_code, 200)

    def user_test_visibility(self, user_nr):
        "tests visibility private and public events for user"
        login = self.login_user(user_nr)
        self.assertTrue(login)
        user = self.get_user(user_nr)
        public_event = self.get_event(user, True, True)
        private_event = self.get_event(user, False, True)
        response = self.client.get(reverse('list_events_tag', \
                                         kwargs = {'tag':'tag'}))
        txt = response.content
        self.assertTrue(public_event.title in txt)
        self.assertTrue(private_event.title in txt)
        for nr in range(USERS_COUNT):# pylint: disable-msg=C0103
            if nr != user_nr:
                public_title = self.event_title(self.get_user(nr), True, True)
                private_title = self.event_title(self.get_user(nr), False, True)
                self.assertTrue(public_title in txt, \
                                "not visible public event: %s" % public_title)
                self.assertFalse(private_title in txt, \
                                 "visible private event: %s" % private_title)
        self.client.logout()

    def user_group_edit(self, user_nr):
        "tests edit private and public events for user \
        after add this to group"
        user = self.get_user(user_nr)
        for nr in range(USERS_COUNT):# pylint: disable-msg=C0103
            if nr != user_nr:
                public_event = self.get_event(user, True, True, 
                                              self.get_user(nr))
                private_event = self.get_event(user, False, True, 
                                               self.get_user(nr))
                login = self.login_user(nr)
                self.assertTrue(login)
                response = self.client.get(reverse('event_edit', \
                                                 kwargs = {'event_id':
                                                           public_event.id}))
                txt = response.content
                self.assertTrue(public_event.title in txt, \
                                "can't edit public event: %s\n %s" % 
                                (public_event.title, txt))
                response = self.client.get(reverse('event_edit', \
                                                 kwargs = {'event_id':
                                                           private_event.id}))
                txt = response.content
                self.assertTrue(private_event.title in txt, \
                                "can't edit private event: %s\n %s" % 
                                (private_event.title, txt))
                self.client.logout()

    def user_group_visibility(self, user_nr):
        "tests visibility private and public events for user \
        after add this to group"
        login = self.login_user(user_nr)
        self.assertTrue(login)
        response = self.client.get(reverse('list_events_tag', \
                                         kwargs = {'tag':'tag'}))
        txt = response.content
        for nr in range(USERS_COUNT):# pylint: disable-msg=C0103
            if nr != user_nr:
                public_title = self.event_title(self.get_user(nr), True, True)
                private_title = self.event_title(self.get_user(nr), False, True)
                self.assertTrue(public_title in txt, \
                                "not visible public event: %s" % public_title)
                self.assertTrue(private_title in txt, \
                                 "not visible private event from group: %s" \
                                 % private_title)
        self.client.logout()

    def user_create_groups(self, user_nr):
        "create groups and send invitive to all users"
        login = self.login_user(user_nr)
        self.assertTrue(login)
        user = self.get_user(user_nr)
        self.client.post(reverse('group_new'), \
                                    {'name':user.username, 
                                     'description':user.username})
        group = Group.objects.get(users_in_group=user)
        self.assertEqual(group, Group.objects.get(name=user.username))
        for nr in range(USERS_COUNT):# pylint: disable-msg=C0103
            self.client.post(reverse('group_invite', \
                                            kwargs={'group_id': group.id}), \
                        {'username': self.user_name(nr),
                        'group_id': group.id})

    def user_add_event(self, user_nr):
        "add event to user's group"
        mail.outbox = []
        login = self.login_user(user_nr)
        self.assertTrue(login)
        user = self.get_user(user_nr)
        public_event = self.get_event(user, True, True)
        private_event = self.get_event(user, False, True)
        group = Group.objects.get(name=user.username)
        for event in (public_event, private_event):
            self.client.post(reverse('group_add_event', \
                                            kwargs = {'event_id':event.id}), \
                                    {'grouplist': group.id})
#        is no message after add new event to group
#        print map(lambda x: (x.to[0],x.body), mail.outbox)

    def test_event_url(self):
        "test editing adding and deleting event's url"
        for user_nr in range(USERS_COUNT):
            self.assertTrue(self.login_user(user_nr))
            user = self.get_user(user_nr)
            for public in (True, False):
                event = self.get_event(user, public, True)
                self.client.post(reverse('event_edit',
                                         kwargs = {'event_id':event.id})
                ,{'urls-3-url_name':    '',
                'urls-2-url':    '',
                'sessions-1-id':    '',
                'postcode':    '',
                'title':    'test',
                'deadlines-3-deadline_name':    '',
                'sessions-0-id':    '',
                'urls-3-event':    event.id,
                'sessions-3-id':    '',
                'latitude':    '',
                'sessions-0-session_starttime':    '',
                'urls-TOTAL_FORMS':    '4',
                'sessions-2-session_name':    '',
                'deadlines-1-event':    event.id,
                'deadlines-2-id':    '',
                'deadlines-3-deadline':    '',
                'deadlines-0-event':    event.id,
                'sessions-3-session_name':    '',
                'sessions-2-session_endtime':    '',
                'urls-0-event':    event.id,
                'urls-3-id':    '',
                'urls-3-url':    '',
                'deadlines-MAX_NUM_FORMS':    '',
                'sessions-3-session_endtime':    '',
                'tags':    'tag',
                'acronym':    'LALA',
                'address':    '',
                'deadlines-0-id':    '',
                'sessions-0-session_date':    '',
                'deadlines-INITIAL_FORMS':    '0',
                'country':    '',
                'urls-INITIAL_FORMS':    '0',
                'deadlines-3-event':    event.id,
                'sessions-0-session_endtime':    '',
                'deadlines-2-deadline_name':    '',
                'sessions-1-session_starttime':    '',
                'deadlines-0-deadline':    '',
                'urls-0-url':    'http://onet.pl',
                'deadlines-1-deadline_name':    '',
                'sessions-3-session_starttime':    '',
                'sessions-2-session_starttime':    '',
                'sessions-INITIAL_FORMS':    '0',
                'urls-2-event':    event.id,
                'city':    '',
                'urls-1-url_name':    'wp',
                'urls-0-url_name':    'onet',
                'start':    '2010-10-10',
                'sessions-TOTAL_FORMS':    '4',
                'sessions-3-session_date':    '',
                'deadlines-2-deadline':    '',
                'urls-1-event':    event.id,
                'deadlines-1-id':    '',
                'sessions-0-event':    event.id,
                'deadlines-0-deadline_name':    '',
                'longitude':    '',
                'sessions-0-session_name':    '',
                'deadlines-2-event':    event.id,
                'deadlines-TOTAL_FORMS':    '4',
                'timezone':    '',
                'sessions-MAX_NUM_FORMS':    '',
                'sessions-1-session_date':    '',
                'deadlines-3-id':    '',
                'sessions-2-id':    '',
                'sessions-1-event':    event.id,
                'end':    '',
                'deadlines-1-deadline':    '',
                'sessions-2-session_date':    '',
                'sessions-1-session_name':    '',
                'urls-0-id':    '',
                'description':    '',
                'urls-1-url':    'http://wp.pl',
                'sessions-3-event':    event.id,
                'urls-2-url_name':    '',
#                'urls-0-DELETE':    'on',
                'urls-2-id':    '',
                'urls-1-id':    '',
                'sessions-1-session_endtime':    '',
                'urls-MAX_NUM_FORMS':    '4',
                'sessions-2-event':    event.id
                })
                response = self.client.get(reverse('event_edit_raw', 
                                         kwargs = {'event_id':event.id}))
                self.assertTrue('http://onet.pl' in response.content)
                self.assertTrue('http://wp.pl' in response.content)
                url0 = EventUrl.objects.get(event=event, url_name='onet')
                url1 = EventUrl.objects.get(event=event, url_name='wp')
                
                self.client.post(reverse('event_edit',
                                         kwargs = {'event_id':event.id})
                ,{'urls-3-url_name':    '',
                'urls-2-url':    '',
                'sessions-1-id':    '',
                'postcode':    '',
                'title':    'test',
                'deadlines-3-deadline_name':    '',
                'sessions-0-id':    '',
                'urls-3-event':    event.id,
                'sessions-3-id':    '',
                'latitude':    '',
                'sessions-0-session_starttime':    '',
                'urls-TOTAL_FORMS':    '4',
                'sessions-2-session_name':    '',
                'deadlines-1-event':    event.id,
                'deadlines-2-id':    '',
                'deadlines-3-deadline':    '',
                'deadlines-0-event':    event.id,
                'sessions-3-session_name':    '',
                'sessions-2-session_endtime':    '',
                'urls-0-event':    event.id,
                'urls-3-id':    '',
                'urls-3-url':    '',
                'deadlines-MAX_NUM_FORMS':    '',
                'sessions-3-session_endtime':    '',
                'tags':    'tag',
                'acronym':    'LALA',
                'address':    '',
                'deadlines-0-id':    '',
                'sessions-0-session_date':    '',
                'deadlines-INITIAL_FORMS':    '0',
                'country':    '',
                'urls-INITIAL_FORMS':    '2',
                'deadlines-3-event':    event.id,
                'sessions-0-session_endtime':    '',
                'deadlines-2-deadline_name':    '',
                'sessions-1-session_starttime':    '',
                'deadlines-0-deadline':    '',
                'urls-0-url':    'http://onet.pl',
                'deadlines-1-deadline_name':    '',
                'sessions-3-session_starttime':    '',
                'sessions-2-session_starttime':    '',
                'sessions-INITIAL_FORMS':    '0',
                'urls-2-event':    event.id,
                'city':    '',
                'urls-1-url_name':    'wp',
                'urls-0-url_name':    'onet',
                'start':    '2010-10-10',
                'sessions-TOTAL_FORMS':    '4',
                'sessions-3-session_date':    '',
                'deadlines-2-deadline':    '',
                'urls-1-event':    event.id,
                'deadlines-1-id':    '',
                'sessions-0-event':    event.id,
                'deadlines-0-deadline_name':    '',
                'longitude':    '',
                'sessions-0-session_name':    '',
                'deadlines-2-event':    event.id,
                'deadlines-TOTAL_FORMS':    '4',
                'timezone':    '',
                'sessions-MAX_NUM_FORMS':    '',
                'sessions-1-session_date':    '',
                'deadlines-3-id':    '',
                'sessions-2-id':    '',
                'sessions-1-event':    event.id,
                'end':    '',
                'deadlines-1-deadline':    '',
                'sessions-2-session_date':    '',
                'sessions-1-session_name':    '',
                'urls-0-id':    url0.id,
                'description':    '',
                'urls-1-url':    'http://wp.pl',
                'sessions-3-event':    event.id,
                'urls-2-url_name':    '',
                'urls-0-DELETE':    'on',
                'urls-2-id':    '',
                'urls-1-id':    url1.id,
                'sessions-1-session_endtime':    '',
                'urls-MAX_NUM_FORMS':    '4',
                'sessions-2-event':    event.id
                })
                response = self.client.get(reverse('event_edit_raw', 
                                         kwargs = {'event_id':event.id}))
                self.assertFalse('http://onet.pl' in response.content)
                self.assertTrue('http://wp.pl' in response.content)

    def test_visibility(self):
        "testing visibility public and private events"
        for user_nr in range(USERS_COUNT):
            self.user_test_visibility(user_nr)

    def test_groups(self):
        "test groups behavior"
        mail.outbox = []
        re_inv_code = re.compile(r'g\/invite\/confirm\/([0-9a-f]+)\/')
        for user_nr in range(USERS_COUNT):
            self.user_create_groups(user_nr)
        for code, email in \
        map(lambda x: (re_inv_code.findall(x.body)[0], x.to[0]), mail.outbox):# pylint: disable-msg=W0141,C0301
            user = User.objects.get(email=email)
            self.client.login(username=user.username, password='p')
            self.client.get(reverse('group_invite_activate', \
                                    kwargs={'activation_key':code}))
            self.client.logout()
        mail.outbox = []
        for user_nr in range(USERS_COUNT):
            self.user_add_event(user_nr)
        for user_nr in range(USERS_COUNT):
            self.user_group_visibility(user_nr)
            self.user_group_edit(user_nr)

    def test_group_rss(self):
        "test for one rss.xml icon for each group"
        groups = Group.objects.all()
        for group in groups:
            self.validate_rss(reverse('list_events_group_rss',
                                      kwargs = {'group_id':group.id}))

    def test_group_ical(self):
        "test for one ical file for each group"
        for user_nr in range(USERS_COUNT):
            self.user_create_groups(user_nr)
        for user_nr in range(USERS_COUNT):
            self.user_add_event(user_nr)
        groups = Group.objects.all()
        for group in groups:
            self.validate_ical(reverse('list_events_group_ical',
                                      kwargs = {'group_id':group.id}))

    def test_event_ical(self):
        "test for one ical file for each event"
        events = Event.objects.all()
        for event in events:
            self.validate_ical(reverse('event_show_ical',
                                      kwargs = {'event_id':event.id}))

    def test_search_ical(self):
        "test for ical search"
        self.validate_ical(reverse('list_events_search_ical',
                                      kwargs = {'query':'belin'}))

    def test_filter_rss(self):
        "test for one rss.xml icon for each filter"
        for user_nr in range(USERS_COUNT):
            self.login_user(user_nr)
            user = self.get_user(user_nr)
            filters = Filter.objects.filter(user=user)
            for filer in filters:
                self.validate_rss(reverse('list_events_filter_rss',
                                      kwargs = {'filter_id':filer.id}))

    def test_filter_ical(self):
        "test for one iCalendar file for each filter"
        for user_nr in range(USERS_COUNT):
            self.login_user(user_nr)
            user = self.get_user(user_nr)
            filters = Filter.objects.filter(user=user)
            for filer in filters:
                self.validate_ical(reverse('list_events_filter_ical',
                                      kwargs = {'filter_id':filer.id}))

    @staticmethod
    def user_hash(user_id):
        "return correct hash for user_id"
        return hashlib.sha256("%s!%s" % 
                              (settings.SECRET_KEY, user_id)).hexdigest()

    def test_hash_filter_rss(self):
        "test for one rss.xml icon for each filter"
        for user_nr in range(USERS_COUNT):
            user = self.get_user(user_nr)
            filters = Filter.objects.filter(user=user)
            user_hash = self.user_hash(user.id)
            for filer in filters:
                self.validate_rss(reverse('list_events_filter_rss_hashed',
                                      kwargs = {'filter_id':filer.id,
                                                'user_id':user.id,
                                                'hash':user_hash}))

    def test_hash_filter_ical(self):
        "test for one iCalendar file for each filter"
        for user_nr in range(USERS_COUNT):
            user = self.get_user(user_nr)
            filters = Filter.objects.filter(user=user)
            user_hash = self.user_hash(user.id)
            for filer in filters:
                self.validate_ical(reverse('list_events_filter_ical_hashed',
                                      kwargs = {'filter_id':filer.id,
                                                'user_id':user.id,
                                                'hash':user_hash}))

    def test_private_to_public(self):
        "A private event cannot be made public"
        for user_nr in range(USERS_COUNT):
            self.login_user(user_nr)
            user = self.get_user(user_nr)
            private_event = self.get_event(user, False, True)
            private_event.public = True
            self.assertRaises(AssertionError, private_event.save)

    def test_public_to_private(self):
        "A public event cannot be made private"
        for user_nr in range(USERS_COUNT):
            self.login_user(user_nr)
            user = self.get_user(user_nr)
            public_event = self.get_event(user, True, True)
            public_event.public = False
            self.assertRaises(AssertionError, public_event.save)



#This test can't work with sqlite, because sqlite not support multiusers, 
#is recomendet to use this in future
#    def test_visibility_in_thread(self):
#        "testing visibility public and private events in thread"
#        class TestThread(threading.Thread):
#            "thread with random delay"
#            def __init__(self, test, user_nr):
#                self.user_nr = user_nr
#                self.test = test
#                threading.Thread.__init__(self)
#            def run(self):
#                time.sleep(random.randint(0, 100)/100.0)
#                self.test.user_test_visibility(self.user_nr)
#        for user_nr in range(USERS_COUNT):
#            thread = TestThread(self, user_nr)
#            thread.start()
#        for second in range(20, 0, -1):
#            print "wait %d seconds     \r" % second,
#            time.sleep(1)


    # TODO: test that a notification email is sent to all members of a group
    # when a new event is added to the group. See class Membership in
    # events/models.py

