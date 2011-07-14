#!/usr/bin/env python
# -*- coding: utf-8 -*-
# gpl {{{1
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
#############################################################################
# Copyright 2010,2011 Adam Beret Manczuk <beret@hipisi.org.pl>,
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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU Generevent.idal Public License
# for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with GridCalendar. If not, see <http://www.gnu.org/licenses/>.
#############################################################################
# doc {{{1
""" tests for events application.

Some used ideas are from http://toastdriven.com/fresh/django-doctest-tips/ and 
http://stackoverflow.com/questions/1615406/configure-django-to-find-all-doctests-in-all-modules
"""

# imports {{{1
import unittest
import doctest
import datetime
from datetime import timedelta
import re
import httplib
import urllib
import string
from random import choice
import vobject
from time import time

from django.contrib.auth.models import User
from django.db import transaction, connection
from django.test import TestCase # WebTest is a subclass of TestCase
from django.core.urlresolvers import reverse
from django.core import mail
from registration.models import RegistrationProfile

# the reason for this package is well explained at
# http://stackoverflow.com/questions/2257958/django-unit-testing-for-form-edit
# source: http://bitbucket.org/kmike/django-webtest/src
from django_webtest import WebTest
from MultipartPostHandler import MultipartPostHandler
import urllib2

from gridcalendar.events import models, views, forms, utils, recurring
from gridcalendar.events.models import ( Event, Group, Filter, Membership,
        Calendar, GroupInvitation, ExtendedUser, EventDeadline )
from gridcalendar.events.management.commands.updateupcoming import Command

def suite(): #{{{1
    """ returns a TestSuite naming the tests explicitly 
    
    This allows to include e.g. the doctests of views.py which are not included
    by default.
    """
    tests = unittest.TestSuite()
    tests.addTest(doctest.DocTestSuite( models ))
    tests.addTest(doctest.DocTestSuite( views ))
    tests.addTest(doctest.DocTestSuite( forms ))
    tests.addTest(doctest.DocTestSuite( utils ))
    tests.addTest(doctest.DocTestSuite( recurring ))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(
        EventsTestCase ))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(
        EventsWebTestCase ))
    return tests

# there is a bug in WebTest which have been solved by TestCase but not for
# WebTest, see
# http://groups.google.com/group/django-users/browse_thread/thread/617457f5d62366ae/e5d1436ac93aeb61?pli=1

class EventsWebTestCase( WebTest ):           # {{{1 pylint: disable-msg=R0904
    """ WebTest for the 'events' application """

    csrf_checks = False
    """ see http://pypi.python.org/pypi/django-webtest """

    def test_anon_event_submission( self ): # {{{2
        """ test adding and editing and event anonymously. """
        self.client.logout()
        event_form = self.app.get( reverse('main') ).forms[1]
        title = 'event submission ' + str( datetime.datetime.now() )
        event_form['title'] = title
        event_form['when'] = datetime.date.today().isoformat()
        event_form['tags'] = 'submission test'
        event_form['web'] = 'http://example.com'
        # submitt and get extended form
        response = event_form.submit().follow()
        self.assertEqual(
                Event.objects.filter(title = title).count(),
                1 )
        event_form = response.forms[1]
        # TODO add one url
        # TODO delete one url


class EventsTestCase( TestCase ):           # {{{1 pylint: disable-msg=R0904
    """TestCase for the 'events' application"""

    def setUp( self ): # {{{2 pylint: disable-msg=C0103
        pass

    def _create_user(self, name = None, throw_web = False): # {{{2
        """ create a user either on the API or using the web and email """
        if name is None:
            chars = string.letters # you can append: + string.digits
            name = ''.join( [ choice(chars) for i in xrange(8) ] )
        if not throw_web:
            user = User.objects.create_user(username = name,
                    email = name + '@example.com', password = 'p')
            user.save()
        else:
            response = self.client.post(
                    reverse( 'registration_register' ),#'/a/accounts/register/',
                    {
                        'username': name,
                        'email': name + '@example.com',
                        'password1': 'p',
                        'password2': 'p',
                    } )
            self.assertRedirects( response,
                    'http://testserver%s' % reverse( 'registration_complete' ) )
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject,
                    u'[example.com] Account activation email')
            body = mail.outbox[0].body
            profile = RegistrationProfile.objects.get(
                    user__username=name)
            key = profile.activation_key
            regex = re.compile('^.*/a/accounts/activate/(.*)/$')
            for line in body.splitlines():
                matcher = regex.match(line)
                if matcher:
                    self.assertEqual(key, matcher.group(1))
                    response = self.client.get( reverse('registration_activate',
                            kwargs={'activation_key': key,} ) )
                    self.assertEqual( response.status_code, 200 )
                    break
            mail.outbox = []
        user = User.objects.get(username=name)
        self.failUnless( user.is_active )
        login = self.client.login( username = user.username, password = 'p' )
        self.assertTrue( login )
        self.assertEqual(user.email, name + '@example.com')
        return user

    def _create_group(self, user, name = None, throw_web = False): # {{{2
        """ create a user either on the API or using the web and email """
        self.assertTrue( isinstance( user, User ) )
        if name is None:
            chars = string.letters # you can append: + string.digits
            name = ''.join( [ choice(chars) for i in xrange(8) ] )
        if not throw_web:
            group = Group.objects.create(name = name)
            Membership.objects.create(user = user, group = group)
            return group
        else:
            self.assertTrue( user.is_active )
            login = self.client.login(
                    username = user.username, password = 'p' )
            self.assertTrue( login )
            response = self.client.post ( reverse('group_new'),
                    {'name': name, 'description': u'create_group'} )
            self.assertEqual( response.status_code, 302 )
            return Group.objects.get(name = name)

    def _login(self, user, throw_web = False): # {{{2
        """ logs in `user` """
        if not throw_web:
            login = self.client.login(
                    username = user.username, password = 'p' )
            self.failUnless(login, 'Could not log in')
            response = self.client.get(reverse('group_new'))
            self.failUnlessEqual(response.status_code, 200)
        else:
            response = self.Client.post('/a/accounts/login/',
                    {'username':user.username, 'password':'p'})
            self.assertEqual(response.status_code, 200)

    def _validate_ical( self, url ): # {{{2
        """ validate an ical file (the output of `url`) with an external online
        validator """
        response = self.client.get( url )
        self.assertEqual( response.status_code, 200 )
        content = response.content
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        params = urllib.urlencode( {'snip':content} )
        conn = httplib.HTTPConnection( "severinghaus.org", timeout = 20 )
        conn.request( "POST", "/projects/icv/", params, headers )
        response = conn.getresponse()
        result = response.read()
        #self.assertTrue( 'Congratulations' in result, content )
        self.assertTrue( 'Congratulations' in result )

    def _validate_rss( self, url ): # {{{2
        "validate rss feed data"
        response = self.client.get( url )
        self.assertEqual( response.status_code, 200 )
        content = response.content
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        params = urllib.urlencode( {'rawdata':content} )
        conn = httplib.HTTPConnection("validator.w3.org", timeout = 60)
        conn.request( "POST", "/feed/check.cgi", params, headers )
        response = conn.getresponse()
        result = response.read()
        self.assertTrue( 'Congratulations!' in result, result )

    def test_valid_user_activation(self): # {{{2
        """ tests account creation throw web """
        user = self._create_user( throw_web = True)
        user = self._create_user( throw_web = False)

    def test_event_visibility_in_search(self): # {{{2
        """ visibility of events """
        user = self._create_user('tpev1')
        event = Event.objects.create(
                user = user, title = "1234",
                tags = "test", start=datetime.date.today() )
        self._login ( user )
        response = self.client.get( reverse( 
                'search_query',
                kwargs = {'query': '1234',} ) )
        self.assertTrue( event.title in [
            e.title for e in response.context['events'].object_list ] )
        event.delete()

    def test_group_invitation(self): # {{{2
        """ test group invitation """
        user1 = self._create_user( throw_web = True)

        login = self.client.login(
                    username = user1.username, password = 'p' )
        self.assertTrue( login )

        self.assertTrue( isinstance( user1, User ) )
        user2 = self._create_user( throw_web = True)
        self.assertTrue( isinstance( user2, User ) )
        group = self._create_group( user = user1, throw_web = True )
        users = User.objects.filter( membership__user = user1 )
        self.assertEqual( len(users), 1 )
        self.assertEqual(users[0], user1)
        self._login( user1 )
        response = self.client.post(
                reverse( 'group_invite', kwargs = {
                    'group_id': group.id,} ),
                {'username': user2.username,} )
        self.assertTrue(response.status_code, 200)
        invitation = GroupInvitation.objects.get( host = user1, guest = user2,
                group = group )
        self.assertFalse( invitation.activation_key_expired() )
        self.client.logout()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], user2.email)
        body = mail.outbox[0].body
        regex = re.compile('^.*g/invite/confirm/(.*)/.*$')
        matched = False
        for line in body.splitlines():
            matcher = regex.match(line)
            if matcher:
                self.assertEqual(matcher.group(1), invitation.activation_key)
                invitation = GroupInvitation.objects.get( activation_key =
                        matcher.group(1) )
                self.assertFalse( invitation.activation_key_expired() )
                url = reverse(
                        'group_invite_activate',
                        kwargs = {'activation_key': matcher.group(1),} )
                response = self.client.get( url )
                self.assertEqual(response.status_code, 200)
                matched = True
                break
        assert (matched)
        users = User.objects.filter( membership__group = group )
        self.assertEqual( len(users), 2 )
        self.assertTrue(user1 in users)
        self.assertTrue(user2 in users)
        mail.outbox = []

    def test_group_ical( self ): # {{{2
        """ tests for icals of groups """
        user = self._create_user()
        event1 = Event.objects.create( title = 'title1',
                tags = 'test', start = datetime.date.today(), user = user )
        event2 = Event.objects.create( title = 'title2',
                tags = 'test', start = datetime.date.today(), user = user )
        # self.client.login( username = user1.username, password = 'p' )
        group = self._create_group( user )
        Calendar.objects.create( group = group, event = event1 )
        Calendar.objects.create( group = group, event = event2 )
        url = reverse( 'list_events_group_ical',
            kwargs = {'group_id': group.id,} )
        self._validate_ical( url )
        content = self.client.get( url ).content
        vevents = vobject.readComponents(
                content, validate = True ).next().vevent_list
        self.assertEqual( len(vevents), 2 )
        self.assertEqual( vevents[0].summary.value, "title1" )
        self.assertEqual( vevents[1].summary.value, "title2" )
        event1.delete()
        event2.delete()

    def test_group_rss( self ): # {{{2
        """ tests for rss feeds of groups """
        user = self._create_user()
        event1 = Event.objects.create( title = 'title1',
                tags = 'test', start = datetime.date.today(), user = user )
        event2 = Event.objects.create( title = 'title2',
                tags = 'test', start = datetime.date.today(), user = user )
        # self.client.login( username = user1.username, password = 'p' )
        group = self._create_group( user )
        Calendar.objects.create( group = group, event = event1 )
        Calendar.objects.create( group = group, event = event2 )
        url = reverse( 'list_events_group_rss',
            kwargs = {'group_id': group.id,} )
        self._validate_rss( url )
        content = self.client.get( url ).content
        self.assertTrue( 'title1' in content )
        self.assertTrue( 'title2' in content )
        event1.delete()
        event2.delete()

    def test_lastadded_rss( self ): # {{{2
        user = self._create_user()
        event1 = Event.objects.create( title = 'title1',
                tags = 'test', start = datetime.date.today(), user = user )
        event2 = Event.objects.create( title = 'title2',
                tags = 'test', start = datetime.date.today(), user = user )
        url = reverse( 'lastadded_events_rss' )
        self._validate_rss( url )
        content = self.client.get( url ).content
        self.assertTrue( 'title1' in content )
        self.assertTrue( 'title2' in content )
        event1.delete()
        event2.delete()
        user.delete()

    def test_upcoming_rss( self ): # {{{2
        user = self._create_user()
        event1 = Event.objects.create( title = 'title1',
                tags = 'test', start = datetime.date.today(), user = user )
        event2 = Event.objects.create( title = 'title2',
                tags = 'test', start = datetime.date.today(), user = user )
        url = reverse( 'upcoming_events_rss' )
        self._validate_rss( url )
        content = self.client.get( url ).content
        self.assertTrue( 'title1' in content )
        self.assertTrue( 'title2' in content )
        event1.delete()
        event2.delete()
        user.delete()

    def test_filter_notification( self ): # {{{2
        """ test filter notification """
        user1 = self._create_user()
        user2 = self._create_user()
        Filter.objects.create(
                user = user2, query = '#filter', name = "test", email = True )
        self.assertEqual(len(mail.outbox), 0)
        eve = Event.objects.create( title = 'test filter notification',
                tags = 'filter', start = datetime.date.today(), user = user1 )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], user2.email)
        mail.outbox = []
        # no notification if event changes
        self.assertEqual(len(mail.outbox), 0)
        eve.title = 'title changes'
        eve.save()
        self.assertEqual(len(mail.outbox), 0)
        # TODO: makes this work even if emails are sent in a different thread
        eve.delete()

    def test_updateupcoming( self ):
        now = datetime.datetime.now().isoformat()
        today = datetime.date.today()
        yesterday = timedelta( days = -1 ) + today
        tomorrow = timedelta( days = +1 ) + today
        days2 = timedelta( days = +2 ) + today
        days3 = timedelta( days = +3 ) + today
        dayspast2 = timedelta( days = -2 ) + today
        dayspast3 = timedelta( days = -3 ) + today
        event = Event(title="test updateupcoming " + now,
            start = days2, tags="test")
        event.save()
        # start = days2
        assert( event.upcoming == event.start )
        event_deadline = EventDeadline(
            event = event, deadline_name = "test",
            deadline = tomorrow )
        event_deadline.save()
        event = Event.objects.get( pk = event.pk )
        # deadline = tomorrow
        assert( event.upcoming == tomorrow )
        # save methods work for Event and EventDeadline
        # Now we try the command updateupcoming. To avoid to call the save
        # methods, we write directly to the database.
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE events_eventdeadline SET deadline = %s WHERE id = %s",
            [yesterday.isoformat(), event_deadline.id] )
        transaction.commit_unless_managed()
        event_deadline = EventDeadline.objects.get( pk = event_deadline.id )
        assert( event_deadline.deadline == yesterday )
        cursor.execute(
            "UPDATE events_event SET upcoming = %s WHERE id = %s",
            [yesterday.isoformat(), event.id] )
        transaction.commit_unless_managed()
        event = Event.objects.get( pk = event.pk )
        assert( event.upcoming == yesterday )
        # start = days2 , upcoming = yesterday , deadline = yesterday
        updateupcoming = Command()
        updateupcoming.handle_noargs()
        event = Event.objects.get( pk = event.pk )
        assert( event.upcoming == event.start )
        # we now put everything in the past but upcoming is not start
        cursor.execute(
            "UPDATE events_eventdeadline SET deadline = %s WHERE id = %s",
            [dayspast3.isoformat(), event_deadline.id] )
        transaction.commit_unless_managed()
        cursor.execute(
            "UPDATE events_event SET upcoming = %s WHERE id = %s",
            [dayspast3.isoformat(), event.id] )
        transaction.commit_unless_managed()
        cursor.execute(
            "UPDATE events_event SET start = %s WHERE id = %s",
            [dayspast2.isoformat(), event.id] )
        transaction.commit_unless_managed()
        # start = dayspast2 , upcoming = dayspast3 , deadline = dayspast3
        event = Event.objects.get( pk = event.id )
        event_deadline = EventDeadline.objects.get( pk = event_deadline.id )
        assert( event.start == dayspast2 )
        assert( event.upcoming == dayspast3 )
        assert( event_deadline.deadline == dayspast3 )
        assert( event.upcoming != event.start )
        assert( event.next_coming_date_or_start() == event.start )
        updateupcoming.handle_noargs()
        event = Event.objects.get( pk = event.id )
        assert( event.upcoming == event.start )
        # now we test with an event without deadlines
        event_deadline.delete()
        cursor.execute(
            "UPDATE events_event SET upcoming = %s WHERE id = %s",
            [dayspast3.isoformat(), event.id] )
        transaction.commit_unless_managed()
        event = Event.objects.get( pk = event.id )
        assert( event.upcoming == dayspast3 )
        assert( event.start == dayspast2 )
        updateupcoming.handle_noargs()
        event = Event.objects.get( pk = event.id )
        assert( event.start == event.upcoming )
        event.delete()

    def test_event_ical( self ): # {{{2
        "test for one ical file for each event"
        user = self._create_user()
        event1 = Event.objects.create( title = 'title1',
                tags = 'test', start = datetime.date.today(), user = user )
        event2 = Event.objects.create( title = 'title2',
                tags = 'test', start = datetime.date.today(), user = user )
        events = Event.objects.all()
        for event in events:
            self._validate_ical( reverse( 'event_show_ical',
                                      kwargs = {'event_id':event.id} ) )
        event1.delete()
        event2.delete()

    def test_search_ical( self ): # {{{2
        "test for ical search"
        event = Event.objects.create( title = 'berlin'+str(time()),
                tags = 'berlin', start = datetime.date.today() )
        self._validate_ical( reverse( 'search_ical',
                                      kwargs = {'query':'berlin'} ) )
        # TODO: text for a no match also
        event.delete()

    def test_search_rss( self ): # {{{2
        "test for rss search"
        event = Event.objects.create( title = 'berlin',
                tags = 'berlin', start = datetime.date.today() )
        self._validate_rss( reverse( 'search_rss',
                                      kwargs = {'query':'berlin',} ) )
        # TODO: text for a no match also
        event.delete()

    def test_valid_html( self ): # {{{2
        """ validates html with validator.w3.org """
        # test main page
        validatorURL = "http://validator.w3.org/check"
        opener = urllib2.build_opener(MultipartPostHandler)
        params = { 'fragment': self.client.get("/").content, }
        result = opener.open(validatorURL, params).read()
        self.assertTrue( 'Congratulations' in result )
        # TODO: test event edit
        # TODO create an event with everthing and validate the full event output
        # TODO create a group with some events and validate the output

    def test_clone_of_event( self ):
        """ checks that all classes with references to Event implement a clone
        method with ``self`` and ``event`` as only parameters.
        """
        pass # FIXME
        # TODO check also a clone of another clone

    # TODO {{{2
    #This test can't work with sqlite, because sqlite not support multiusers. 
    #It is recomended to use this in future
    # def test_visibility_in_thread(self):
    #     "testing visibility public and private events in thread"
    #     class TestThread(threading.Thread):
    #         "thread with random delay"
    #         def __init__(self, test, user_nr):
    #             self.user_nr = user_nr
    #             self.test = test
    #             threading.Thread.__init__(self)
    #         def run(self):
    #             time.sleep(random.randint(0, 100)/100.0)
    #             self.test.user_test_visibility(self.user_nr)
    #     for user_nr in range(USERS_COUNT):
    #         thread = TestThread(self, user_nr)
    #         thread.start()
    #     for second in range(20, 0, -1):
    #         print "wait %d seconds     \r" % second,
    #         time.sleep(1)

    # TODO: test that a notification email is sent to all members of a group
    # when a new event is added to the group. See class Membership in
    # events/models.py
