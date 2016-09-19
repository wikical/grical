#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# gpl {{{1
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker

import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from ..models import Calendar, Event, Filter, Group, Membership

class EventViewsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user( username='test_user',
                email='test_user@example.com', password='p')

    def test_help_page(self):
        response = self.client.get(reverse('help'))
        self.assertEqual(response.status_code, 200)

    def test_legal_notice(self):
        response = self.client.get(reverse('legal_notice'))
        self.assertEqual(response.status_code, 200)

    def test_event_edit(self):
    # TODO: create more tests above for e.g. trying to save a new event
    # without a URL; and deleting some urls, deadlines and sessions
        e = Event.objects.create( title = 'ee_test', tags = 'berlin' )
        e.startdate = datetime.date.today()
        response = self.client.get(reverse('event_edit',
                kwargs={'event_id': e.id,}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('event_new'))
        self.assertEqual(response.status_code, 200)

    def test_event_new_raw(self):
        response = self.client.get(reverse('event_new_raw'))
        self.assertEqual(response.status_code, 200)

    def test_event_edit_raw(self):
        e = Event.objects.create(title = 'eer_test', tags = 'berlin')
        e.startdate = datetime.date.today()
        response = self.client.get(reverse('event_edit_raw',
                kwargs={'event_id': e.id,}))
        self.assertEqual(response.status_code, 200)

    def test_event_show_all(self):
        e = Event.objects.create( title = 'es_test', tags = 'berlin' )
        e.startdate = datetime.date.today()
        response = self.client.get(reverse('event_show_all',
                kwargs={'event_id': e.id,}))
        self.assertEqual(response.status_code, 200)

    def test_event_show_raw(self):
        e = Event.objects.create( title = 'esr_test', tags = 'berlin' )
        e.startdate = datetime.date.today()
        response = self.client.get(reverse('event_show_raw',
                kwargs={'event_id': e.id,}))
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        e1 = Event.objects.create(
                title = 's1_test', tags = 'berlin', city = 'prag' )
        e1.startdate = datetime.date.today()
        e2 = Event.objects.create(
                title = 's2_test', tags = 'berlin', city = 'madrid' )
        e2.startdate = datetime.date.today()
        response = self.client.get(reverse('search_query',
                kwargs={'query': 'test',}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('search_query_view',
                kwargs={'query': 'test', 'view': 'table'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('search_query_view',
                kwargs={'query': 'test', 'view': 'map'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('search_query_view',
                kwargs={'query': 'test', 'view': 'calendars'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('search'), {'query': '#berlin',})
        self.assertEqual(response.status_code, 200)
        response = response = self.client.get(reverse('search'), {'query': '#berlinn',})
        self.assertContains(response,
                'There are no events for this search currently')
        response = self.client.get(reverse('search'), {'query': '@madrid',})
        self.assertEqual(response.status_code, 200)
        response = response = self.client.get(reverse('search'), {'query': '@madridd',})
        self.assertContains(response,
            'There are no events for this search currently')

    def test_filter_save(self):
        self.client.login(username = self.user.username, password = 'p')
        response = self.client.get(reverse('filter_save'),
                kwargs={'q': 'abcdef',})
        self.assertEqual(response.status_code, 200)

    def test_filter_edit(self):
        self.client.login(username = self.user.username, password = 'p')
        f, c = Filter.objects.get_or_create(name="test", user = self.user,
                query="abcdef" )
        response = self.client.get(reverse('filter_edit',
                kwargs={'filter_id': f.id,}))
        self.assertEqual(response.status_code, 200)

    def test_filter_drop(self):
        self.client.login(username = self.user.username, password = 'p')
        f, c = Filter.objects.get_or_create( name="test", user = self.user,
                query="abcdef" )
        response = self.client.get( reverse ( 'filter_drop',
                kwargs={'filter_id': f.id,} ) )
        self.assertEqual(response.status_code, 302)

    def test_list_filters_my(self):
        self.client.login(username = self.user.username, password = 'p')
        f, c = Filter.objects.get_or_create( name="test", user = self.user,
                query="abcdef" )
        response = self.client.get(reverse('list_filters_my'))
        self.assertEqual(response.status_code, 200)

    def test_list_events_my(self):
        e = Event.objects.create( title='lem_test', tags='berlin',
                user=self.user)
        e.startdate = datetime.date.today()
        self.client.login(username = self.user.username, password = 'p')
        response = self.client.get(reverse('list_events_my'))
        self.assertEqual(response.status_code, 200)

    def test_main(self):
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)

    def test_group_new(self):
        self.client.login(username = self.user.username, password = 'p')
        response = self.client.get(reverse('group_new'))
        self.assertEqual(response.status_code, 200)

    def test_list_groups_my(self):
        self.client.login(username = self.user.username, password = 'p')
        response = self.client.get(reverse('list_groups_my'))
        self.assertEqual(response.status_code, 302)

    def test_group_quit(self):
        u2 = User.objects.create_user('group_quit_2', '0@example.com', 'p')
        g = Group.objects.create(name = 'group_quit')
        Membership.objects.create(user = self.user, group = g)
        Membership.objects.create(user = u2, group = g)
        self.assertEqual(Membership.objects.filter(group = g).count(), 2)
        self.client.login(username = self.user.username, password = 'p')
        response = self.client.get(reverse('group_quit',
                kwargs={'group_id': g.id,}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Membership.objects.filter(group = g).count(), 1)

    def test_group_add_event(self):
        self.client.login(username = self.user.username, password = 'p')
        g, c = Group.objects.get_or_create(name = 'test')
        m, c = Membership.objects.get_or_create(user = self.user, group = g)
        e = Event.objects.create( title='gae_test', tags='berlin',
                user=self.user)
        e.startdate = datetime.date.today()
        response = self.client.get(reverse('group_add_event',
                kwargs={'event_id': e.id,}))
        self.assertEqual(response.status_code, 200)
        m, c = Calendar.objects.get_or_create(group = g, event = e)
        response = self.client.get(reverse('group_add_event',
                kwargs={'event_id': e.id,}))
        self.assertEqual(response.status_code, 302)

    def test_group_view(self):
        g, c = Group.objects.get_or_create(name = 'test')
        m, c = Membership.objects.get_or_create(user = self.user, group = g)
        e = Event.objects.create(
                title = 'event in group', tags = 'group-view', user=self.user)
        e.startdate = datetime.date.today()
        m, c = Calendar.objects.get_or_create(group = g, event = e)
        response = self.client.get(reverse('group_view',
                kwargs={'group_id': g.id,}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'event in group')

    def test_group_invite(self):
        self.client.login(username = self.user.username, password = 'p')
        g, c = Group.objects.get_or_create(name = 'test')
        m, c = Membership.objects.get_or_create(user = self.user, group = g)
        response = self.client.get(reverse('group_invite',
                kwargs={'group_id': g.id,}))
        self.assertEqual(response.status_code, 200)

    def test_ical_for_search(self):
        e = Event.objects.create( title = 'icfs_test', tags = 'berlin' )
        e.startdate = datetime.date.today()
        response = self.client.get(reverse('search_ical',
                kwargs={'query': 'berlin',}))
        self.assertEqual(response.status_code, 200)

    def test_ical_for_event(self):
        e = Event( title = 'icfe_test', tags = 'berlin')
        e.save()
        e.startdate = datetime.date.today()
        response = self.client.get( reverse( 'event_show_ical',
                kwargs={'event_id': e.id,}))
        self.assertEqual(response.status_code, 200)

    def test_ical_for_group(self):
        e = Event.objects.create( title = 'icfg_test', tags = 'berlin' )
        e.startdate = datetime.date.today()
        g, c = Group.objects.get_or_create(name = 'test')
        m, c = Membership.objects.get_or_create(user = self.user, group = g)
        ca, c = Calendar.objects.get_or_create(group = g, event = e)
        self.client.login(username = self.user.username, password = 'p')
        response = self.client.get(reverse('list_events_group_ical',
                kwargs={'group_id': g.id,}))
        self.assertEqual(response.status_code, 200)
