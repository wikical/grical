# -*- coding: utf-8 -*-
#############################################################################
# Copyright  2010 Adam Beret Manczuk <beret@hipisi.org.pl>
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

import datetime
from django.contrib.auth.models import User
from events.models import Event, Group, Membership, Calendar, Filter
from django.test import TestCase

NUMBER_OF_EVENTS = 3


class EventTestCase(TestCase):
    "testing case for event application"
    def setUp(self):
        """models value initiation"""
        def createEvent(user=False):
            "create event for user"
            for event_c in range(NUMBER_OF_EVENTS):
                for when, start_delta, end_delta in (('past', -36, -33),
                                                     ('future', 33, 36)):
                    start_str = str(datetime.date.today() + datetime.timedelta(start_delta))
                    end_str = str(datetime.date.today() + datetime.timedelta(end_delta))
                    if user:
                        pv_list = [(True, 'PUBLIC'),
                                   (False, 'NON-PUBLIC')]
                        user_str = "USER %s" % str(user.id)
                    else:
                        pv_list = [(True, 'PUBLIC'), ]
                        user_str = "USERLESS"
                    for pv, pv_str in pv_list:
                        data_str = {'event': str(event_c),
                                    'when':when,
                                    'user':  user_str,
                                    'pv': pv_str}
                        event = Event(
                                acronym='ACRO',
                                title="EVENT %(event)s %(when)s %(user)s %(pv)s" % data_str,
                                start=start_str,
                                end=end_str,
                                public=pv,
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
                        try:
                            event.save()
                            print "OK    SAVING EVENT: %(event)s %(when)s %(user)s %(pv)s" % data_str
                        except Exception, error:
                            data_str['error'] = str(error)
                            print "ERROR %(error)s WHEN SAVING EVENT: %(event)s %(when)s %(user)s %(pv)s" % data_str

#-------------------- create some userless events ----------------
        
        createEvent()
        
        #----------------- create some users and let them create some events ----------------
        
        for user_id in range(1, 5):
            user = User.objects.create_user(
                username='u' + str(user_id),
                email='test' + str(user_id) + '@gridcalendar.org',
                password='p',
                )
            user.is_staff = True
            user.is_superuser = True
            try:
                user.save()
                print "OK    SAVING USER: %s" % str(user_id)
            except Exception, error:
                print "ERROR %s WHEN SAVING USER: %s" % (str(error), str(user_id))
        
            filter = Filter(user=user,
                query='berlin',
                name=user.username + "'s filter: berlin"
                )
            filter.save()
        
        createEvent(user)
        
        #------ create some groups ---------------------------------------
        
        group_data = [
            [1, 2],
            [1, 3]
        ]
        
        
        for group_id in range(1, 3):
            group = Group(
                name='g' + str(group_id),
                description='test description' + str(group_id),
                )
            try:
                group.save()
                print "OK    SAVING GROUP: " + str(group_id)
            except:
                print "ERROR SAVING GROUP: " + str(group_id)
        
            for user_id in group_data[group_id - 1]:
                user = User.objects.get(id=user_id)
                member1 = Membership(
                    group=group,
                    user=user,
                    new_member_email='test@example.org',
                )
                member1.save()
        
        #------ add some events to groups ------------------------
        
        for event_id in range(1, Event.objects.count(), 3):
                event = Event.objects.get(id=event_id)
                group_id = 1
                group = Group.objects.get(id=group_id)
                cal1 = Calendar(
                    event=event,
                    group=group,
                )
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
        "testing sites for event"
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
        for filter in Filter.objects.all():
            response = self.client.get("/f/%d/ical/" % filter.id)
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

