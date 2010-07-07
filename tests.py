# -*- coding: utf-8 -*-
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

class EventTestCase(TestCase):
    """testing case for event application"""

    @staticmethod
    def create_event(user=None, number_of_events=3):
        """helper function to create events for user"""
        for event_c in range(number_of_events):
            for when, start_delta, end_delta in (('past', -36, -33),
                                                 ('future', 33, 36)):
                start_str = str(datetime.date.today() +
                        datetime.timedelta(start_delta))
                end_str = str(datetime.date.today() +
                        datetime.timedelta(end_delta))
                if user is not None:
                    public_value_list = [(True, 'PUBLIC'),
                               (False, 'NON-PUBLIC')]
                    user_str = "USER %s" % str(user.id)
                else:
                    public_value_list = [(True, 'PUBLIC'), ]
                    user_str = "USERLESS"
                for public_value, public_value_str in public_value_list:
                    title = "EVENT %(event)s %(when)s %(user)s %(pv)s" % {
                        'event':    str(event_c),
                        'when':     when,
                        'user':     user_str,
                        'pv':       public_value_str,
                        }
                    event = Event(
                            acronym='ACRO',
                            title=title,
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

    def setUp(self):                            # pylint: disable-msg=C0103
        """models value initiation"""

        # create some userless events
        EventTestCase.create_event()
        
        # create some users and let them create some filters and events
        for user_id in range(1, 5):
            user = User.objects.create_user(
                    username='u' + str(user_id),
                    email='test' + str(user_id) + '@gridcalendar.net',
                    password='p',
                    )
            user.save()
            event_filter = Filter(user=user,
                query='berlin',
                name=user.username + "'s filter: berlin"
                )
            event_filter.save()
            EventTestCase.create_event(user)
        
        # create some groups
        group_data = [
            [1, 2],
            [1, 3]
        ]
        for group_id in range(1, 3):
            group = Group(
                name='g' + str(group_id),
                description='test description' + str(group_id),
                )
            group.save()
            for user_id in group_data[group_id - 1]:
                user = User.objects.get(id=user_id)
                member1 = Membership(
                    group=group,
                    user=user,
                )
                member1.save()
        
        # add some events to groups
        for event_id in range(1, Event.objects.count(), 3):
            event = Event.objects.get(id=event_id)
            group_id = 1
            group = Group.objects.get(id=group_id)
            cal1 = Calendar(event=event, group=group,)
            cal1.save()
        for event_id in range(2, Event.objects.count(), 3):
            event = Event.objects.get(id=event_id)
            group_id = 2
            group = Group.objects.get(id=group_id)
            cal1 = Calendar(
                event=event,
                group=group,
            )
            cal1.save()

    def test_event(self):
        """testing sites for event"""
        response = self.client.get('/e/new/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/e/new/raw/')
        self.failUnlessEqual(response.status_code, 200)
        for event in Event.objects.all():
            response = self.client.get("/e/edit/%d/" % event.id)
            self.failUnlessEqual(response.status_code, 200)
            response = self.client.get("/e/edit/%d/raw/" % event.id)
            self.failUnlessEqual(response.status_code, 200)
            response = self.client.get("/e/show/%d/" % event.id)
            self.failUnlessEqual(response.status_code, 200)
            response = self.client.get("/e/show/%d/raw/" % event.id)
            self.failUnlessEqual(response.status_code, 200)
            response = self.client.get("/e/show/%d/ical/" % event.id)
            self.failUnlessEqual(response.status_code, 200)

    def test_filter(self):
        "testing sites for filter"
        for event_filter in Filter.objects.all():
            response = self.client.get("/f/%d/ical/" % event_filter.id)
            self.failUnlessEqual(response.status_code, 200)

    def test_queries(self):
        "testing sites for queries"
        response = self.client.get('/q/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/s/berlin/ical/')
        self.failUnlessEqual(response.status_code, 200)
        response = self.client.get('/s/berlin/')
        self.failUnlessEqual(response.status_code, 200)

    def test_login(self):
        "testing for login"
        for user_id in range(1, 5):
            login = self.client.login(username='u' + str(user_id), password='p')
            self.failUnless(login, 'Could not log in')

    # TODO: test that a notification email is sent to all members of a group
    # when a new event is added to the group. See class Membership in
    # events/models.py

    # TODO: test that a notification email is sent to all members of a group
    # when a new member is added to the group. See class Membership in
    # events/models.py

