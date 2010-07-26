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
# FITNESS FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################

""" testing events application """

import datetime
from django.contrib.auth.models import User
from events.models import Event, Group, Membership, Calendar, Filter
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
import time
import threading
import random

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

    @classmethod
    def get_user(cls, user_nr):
        "get user instance for nr"
        return User.objects.get(username=cls.user_name(user_nr))

    @classmethod
    def get_event(cls, user, public, future):
        "find and return event for params"
        if user:
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
        for user_nr in range(100):
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
        for nr in range(100):
            if nr != user_nr:
                public_title = self.event_title(self.get_user(nr), True, True)
                private_title = self.event_title(self.get_user(nr), False, True)
                self.assertTrue(public_title in txt, \
                                "not visible public event: %s" % private_title)
                self.assertFalse(private_title in txt, \
                                 "visible private event: %s" % private_title)

    def test_visibility(self):
        "testing visibility public and private events"
        mail.outbox = []
        for user_nr in range(100):
            self.user_test_visibility(user_nr)

#This test can't work with sqlite, because sqlite not support multiusers, is recomendet to use this with postgresql
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
#        for user_nr in range(2):
#            thread = TestThread(self, user_nr)
#            thread.start()
#        for second in range(20, 0, -1):
#            print "wait %d seconds     \r" % second,
#            time.sleep(1)



    # TODO: test that a notification email is sent to all members of a group
    # when a new event is added to the group. See class Membership in
    # events/models.py

