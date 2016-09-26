#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2016 Stefanos Kozanis <stefanos ät wikical.com>
#
# This file is part of GriCal.
#
# GriCal is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# GriCal is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GriCal. If not, see <http://www.gnu.org/licenses/>.
#############################################################################
import datetime
from time import time
import vobject

from django.contrib.auth.models import User
from django.contrib.gis.db.models import Count
from django.test import TestCase
from django.utils.encoding import smart_str

from ..models import (Calendar, Event, EventDate, EXAMPLE, ExtendedUser,
        Filter, Group, Membership)

class ModelsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user( username='test_user',
                email='test_user@example.com', password='p')

    def test_icalendar(self):
        event,l = Event.parse_text(EXAMPLE)
        ical = event.icalendar()
        ical = vobject.readOne(ical.serialize())
        self.assertEqual(ical.vevent.categories.serialize(),
                u'CATEGORIES:calendar,software,open-source,'
                'gridmind,gridcalendar\r\n')

    def test_clone(self):
        today = datetime.date.today()
        today_t = today.isoformat()
        events = Event.objects.filter( title='GridCalendar presentation' )
        if events: events.delete()
        event,l = Event.parse_text(EXAMPLE)
        event.enddate = None
        clone = event.clone( self.user, startdate = today )
        clone_text = clone.as_text()
        clone_text = clone_text.replace(
            today_t, event.startdate.isoformat(), 1)
        self.assertEqual(event.as_text(), clone_text)

    def test_example(self):
        example = Event.example()
        event,l = Event.parse_text(example)
        self.assertEqual(smart_str(example), event.as_text())

    def test_recurrence_model(self):
        today = datetime.date.today()
        tomorrow = datetime.timedelta(days=1) + today
        after_tomorrow = datetime.timedelta(days=2) + today
        e1 = Event.objects.create(title="Re1" )
        e1.startdate = today
        e2 = Event.objects.create(title="Re2" )
        e2.startdate = tomorrow
        e3 = Event.objects.create(title="Re3" )
        e3.startdate = after_tomorrow
        self.assertIsNone(e1.recurring)
        self.assertIsNone(e2.recurring)
        self.assertIsNone(e3.recurring)
        r = e1.recurrences.create(event = e2)
        r = e1.recurrences.create(event = e3)
        self.assertIsNotNone(e1.recurring)
        self.assertIsNotNone(e2.recurring)
        self.assertIsNotNone(e3.recurring)
        self.assertEqual(e1.recurring.master, e1)
        self.assertEqual(e2.recurring.master, e1)
        self.assertEqual(e3.recurring.master, e1)
        event_list = [r.event for r in e1.recurrences.all()]
        self.assertIn(e1, event_list)
        self.assertIn(e2, event_list)
        self.assertIn(e3, event_list)
        self.assertEqual(e1.recurrences.count(), 3)
        # we now put e2 start in the past and check that master is updated
        e2.startdate = datetime.timedelta(days=-1)+today
        e2.save()
        e1 = Event.objects.get( title="Re1" )
        e2 = Event.objects.get( title="Re2" )
        e3 = Event.objects.get( title="Re3" )
        self.assertEqual(e1.recurring.master, e2)
        self.assertEqual(e2.recurring.master, e2)
        self.assertEqual(e3.recurring.master, e2)
        event_list = [r.event for r in e2.recurrences.all()]
        self.assertIn(e1, event_list)
        self.assertIn(e2, event_list)
        self.assertIn(e3, event_list)
        self.assertEqual(e2.recurrences.count(), 3)
        # we now check that master is updated when master is deleted
        e2.delete()
        e1 = Event.objects.get( title="Re1" )
        e3 = Event.objects.get( title="Re3" )
        self.assertEqual(e1.recurring.master, e1)
        self.assertEqual(e3.recurring.master, e1)

    def test_extended_user_model(self):
        now = datetime.datetime.now().isoformat()
        user = self.user
        group1 = Group.objects.create(name="group1 " + now)
        Membership.objects.create(user=user, group=group1)
        group2 = Group.objects.create(name="group2 " + now)
        Membership.objects.create(user=user, group=group2)
        euser = ExtendedUser.objects.get(id = user.id)
        self.assertEqual(len( euser.get_groups() ), 2)
        self.assertTrue(euser.has_groups())
        Filter.objects.create(user = user, name = "f1", query = "query")
        Filter.objects.create(user = user, name = "f2", query = "query")
        self.assertEqual(len( euser.get_filters() ), 2)
        self.assertTrue(euser.has_filters())
        event = Event(title="test for ExtendedUser " + now, tags = "test")
        event.save()
        event.startdate = datetime.date.today()
        Calendar.objects.create(event = event, group = group2)
        self.assertTrue(euser.has_groups_with_coming_events())

    def test_event_url_model(self):
        # Migrated from doctest, does not seem to check something specific, it
        # looks more like a code example
        urls_numbers = Event.objects.annotate(urls_nr=Count('urls'))
        events_with_more_than_1_url = urls_numbers.filter(urls_nr__gte=2)
        self.assertFalse(events_with_more_than_1_url)

    def test_filter_model_query_matches_event(self):
        t = str(time()).replace('.','')
        now = datetime.datetime.now().isoformat()
        today = datetime.date.today()
        group = Group.objects.create(name="matchesevent" + t)
        event = Event.objects.create(title="test for events " + now,
            tags = "test" )
        event.startdate = datetime.timedelta(days=-1)+today
        eventdate = EventDate(
                event = event, eventdate_name = "test",
                eventdate_date = today)
        eventdate.save()
        calendar = Calendar.objects.create( group = group,
            event = event )
        calendar.save()
        user = User.objects.create(username = now)
        fil = Filter.objects.create(user=user, name=now, query='test')
        self.assertTrue(fil.matches_event(event))
        fil.query = today.isoformat()
        self.assertTrue(fil.matches_event(event))
        fil.query = (datetime.timedelta(days=-1) + today ).isoformat()
        self.assertTrue(fil.matches_event(event))
        fil.query = '!' + group.name
        self.assertTrue(fil.matches_event(event))
        fil.query = '#test'
        self.assertTrue(fil.matches_event(event))
        fil.query = 'abcdef'
        self.assertFalse(fil.matches_event(event))


class GroupTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user( username='test_user',
                email='test_user@example.com', password='p')

    def test_group(self):
        now = datetime.datetime.now().isoformat()
        today = datetime.date.today()
        group = Group.objects.create(name="group " + now)
        event = Event(title="test for events " + now,
            tags = "test" )
        event.save()
        event.startdate = datetime.timedelta(days=-1)+today
        eventdate = EventDate(
                event = event, eventdate_name = "test",
                eventdate_date = today)
        eventdate.save()
        Calendar.objects.create(group = group, event = event)
        self.assertEqual(len(group.get_coming_events()), 1)
        self.assertTrue(group.has_coming_events())
        self.assertEqual(len(group.get_users()), 0)
        Membership.objects.create(group = group, user = self.user)
        self.assertEqual(len(group.get_users()), 1)

    def test_is_user_in_group(self):
        now = datetime.datetime.now().isoformat()
        user2 = User.objects.create(username = "u2" + now)
        group1 = Group.objects.create(name="group1 " + now)
        Membership.objects.create(user=self.user, group=group1)
        self.assertTrue(Group.is_user_in_group(self.user, group1))
        self.assertFalse(Group.is_user_in_group(user2, group1))
        self.assertTrue(Group.is_user_in_group(self.user.id, group1.id))
        self.assertFalse(Group.is_user_in_group(user2.id, group1.id))

    def test_groups_of_user(self):
        now = datetime.datetime.now().isoformat()
        user2 = User.objects.create(username = "u2" + now)
        group12 = Group.objects.create(name="group12 " + now)
        group2 = Group.objects.create(name="group2 " + now)
        Membership.objects.create(user=self.user, group=group12)
        Membership.objects.create(user=user2, group=group12)
        Membership.objects.create(user=user2, group=group2)
        groups_of_user_2 = Group.groups_of_user(user2)
        self.assertEqual(len(groups_of_user_2), 2)
        self.assertIsInstance(groups_of_user_2, list)
        self.assertIsInstance(groups_of_user_2[0], Group)
        self.assertIsInstance(groups_of_user_2[1], Group)
        groups_of_user_1 = Group.groups_of_user(self.user)
        self.assertEqual(len(groups_of_user_1), 1)
