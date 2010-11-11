#!/usr/bin/env python
# -*- coding: utf-8 -*-
# gpl {{{1
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
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
import hashlib
import string
from random import choice
import vobject
from time import time

from django.contrib.auth.models import User
from django.db import transaction
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core import mail
from registration.models import RegistrationProfile

import settings
from gridcalendar.events import models,views
from events.models import ( Event, Group, Filter, EventUrl, Membership,
        Calendar, GroupInvitation, ExtendedUser )


def suite(): #{{{1
    """ returns a TestSuite naming the tests explicitly 
    
    This allows to include e.g. the doctests of views.py which are not included
    by default.
    """
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(models))
    suite.addTest(doctest.DocTestSuite(views))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(EventsTestCase))
    return suite

class EventsTestCase( TestCase ):           # {{{1 pylint: disable-msg=R0904
    """TestCase for the 'events' application"""

    def setUp( self ): # {{{2 pylint: disable-msg=C0103
        pass

    def _create_user(self, name = None, throw_web = False): # {{{2
        """ create a user either on the API or using the web and email """
        if name is None:
            name = datetime.datetime.now().isoformat()
        if not throw_web:
            user = User.objects.create_user(username = name,
                    email = name + '@example.com', password = 'p')
            user.save()
            return user
        else:
            response = self.client.post('/a/accounts/register/', {
                'username': name,
                'email': name + '@example.com',
                'password1': 'p',
                'password2': 'p',})
            self.assertRedirects(response, '/a/accounts/register/complete/')
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject,
                    u'[example.com] Activation email')
            body = mail.outbox[0].body
            profile = RegistrationProfile.objects.get(
                    user__username=name)
            key = profile.activation_key
            regex = re.compile('^.*/a/accounts/activate/(.*)/$')
            for line in body.split('\n'):
                matcher = regex.match(line)
                if matcher:
                    self.assertEqual(key, matcher.group(1))
                    response = self.client.get('/a/accounts/activate/' + key)
                    # the above line returns a HttpResponsePermanentRedirect (I,
                    # ivan, don't know why). items()[1][1] is where it redirects
                    # to.
                    response = self.client.get(response.items()[1][1])
                    # TODO: test the page
                    self.failUnless(User.objects.get(username=name).is_active)
                    break
            user = User.objects.get(username=name)
            self.assertEqual(user.email, name + '@example.com')
            mail.outbox = []
            return user

    def _create_group(self, user, name = None, throw_web = False): # {{{2
        """ create a user either on the API or using the web and email """
        if name is None:
            chars = string.letters # you can append: + string.digits
            name = ''.join( [ choice(chars) for i in xrange(8) ] )
        if not throw_web:
            group = Group.objects.create(name = name)
            m = Membership.objects.create(user = user, group = group)
            return group
        else:
            self.client.login(
                    username = user.username, password = 'p' )
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
        conn = httplib.HTTPConnection( "severinghaus.org" )
        conn.request( "POST", "/projects/icv/", params, headers )
        response = conn.getresponse()
        result = response.read()
        #self.assertTrue( 'Congratulations' in result, content )
        self.assertTrue( 'Congratulations' in result )

    def _validate_rss( self, url ): # {{{2
        "validate rss feed data"
        response = self.client.get( url )
        self.assertEqual( response.status_code, 200 )
        conn = httplib.HTTPConnection(
                "http://feedvalidator.org/check.cgi?url=" + url )
        conn.request()
        response = conn.getresponse()
        result = response.read()
        self.assertTrue( 'Congratulations!' in result, url )
    def test_anonymous_private_error(self): # {{{2
        """ tests that an Event of the anonymous user cannot be private """
        e = Event(user=None, public=False, title="test",
                start=datetime.date.today(), tags="test test1 test2")
        self.assertRaises(AssertionError, e.save)

    def test_valid_activation(self): # {{{2
        """ tests account creation throw web """
        self._create_user('test_activation_web', True)

    def test_public_private_event_visibility(self): # {{{2
        """ public/private visibility of events """
        user1 = self._create_user('tpev1')
        user2 = self._create_user('tpev2')
        event_public = Event.objects.create(
                user = user1, title = "public 1234",
                tags = "test", start=datetime.date.today() )
        event_private = Event.objects.create(
                user = user1, title = "private 1234",
                public = False,
                tags = "test", start=datetime.date.today() )
        self._login ( user2 )
        response = self.client.get( reverse( 
                'list_events_search',
                kwargs = {'query': '1234',} ) )
        self.assertTrue(event_public in response.context['events'])
        self.assertFalse(event_private in response.context['events'])

    def test_public_private_change_error(self): # {{{2
        """ tests that an event cannot be changed from private to public """
        user = self._create_user('tppce', False)
        event = Event(user = user, public = True, title="test",
                start=datetime.date.today(), tags="test")
        event.save()
        event.public = False
        self.assertRaises(AssertionError, event.save)

    def test_none_user_private_event_error( self ):
        """ tests that an event cannot be created without an owner and being
        private """
        event = Event(user = None, public = False, title="test",
                start=datetime.date.today(), tags="test")
        self.assertRaises(AssertionError, event.save)

    def test_private_public_change_error(self): # {{{2
        """ tests that an event cannot be changed from public to private """
        user = self._create_user('tppce', False)
        event = Event(user = user, public = False, title="test",
                start=datetime.date.today(), tags="test")
        event.save()
        assert (event.public == False)
        transaction.commit()
        assert ( Event.objects.get( id = event.id ) )
        event.public = True
        self.assertRaises(AssertionError, event.save)

    def test_group_invitation(self): # {{{2
        """ test group invitation """
        user1 = self._create_user('tgi1', True)
        user2 = self._create_user('tgi2', True)
        group = self._create_group( user = user1, name = "group", throw_web = True )
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
        for line in body.split('\n'):
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
        """ tests for public and private icals of groups """
        user1 = self._create_user()
        event1 = Event.objects.create( title = 'public',
                tags = 'test', start = datetime.date.today(), user = user1 )
        event2 = Event.objects.create( title = 'private',
                tags = 'test', start = datetime.date.today(), user = user1,
                public = False )
        # self.client.login( username = user1.username, password = 'p' )
        group = self._create_group( user1 )
        Calendar.objects.create( group = group, event = event1 )
        Calendar.objects.create( group = group, event = event2 )
        # user1
        url_user1_hashed = reverse( 'list_events_group_ical_hashed',
            kwargs = {'group_id': group.id, 'user_id': user1.id,
                'hash': ExtendedUser.calculate_hash( user1.id )} )
        self._validate_ical( url_user1_hashed )
        content = self.client.get( url_user1_hashed ).content
        vevents = vobject.readComponents(
                content, validate = True ).next().vevent_list
        self.assertEqual( len(vevents), 2 )
        self.assertEqual( vevents[0].summary.value, "public" )
        self.assertEqual( vevents[1].summary.value, "private" )
        # user2
        user2 = self._create_user()
        url_user2_hashed = reverse( 'list_events_group_ical_hashed',
            kwargs = {'group_id': group.id, 'user_id': user2.id,
                'hash': ExtendedUser.calculate_hash( user2.id )} )
        content = self.client.get( url_user2_hashed ).content
        self.assertTrue( 'not a member' in content )
        # anonymous
        url_non_hashed = reverse( 'list_events_group_ical',
                kwargs = {'group_id': group.id,} )
        self._validate_ical( url_non_hashed )
        content = self.client.get( url_non_hashed ).content
        vevents = vobject.readComponents(
                content, validate = True ).next().vevent_list
        self.assertEqual( len(vevents), 1 )
        self.assertEqual( vevents[0].summary.value, "public" )

    def test_group_rss( self ): # {{{2
        """ tests for public and private rss feeds of groups """
        user1 = self._create_user()
        event1 = Event.objects.create( title = 'public',
                tags = 'test', start = datetime.date.today(), user = user1 )
        event2 = Event.objects.create( title = 'private',
                tags = 'test', start = datetime.date.today(), user = user1,
                public = False )
        # self.client.login( username = user1.username, password = 'p' )
        group = self._create_group( user1 )
        Calendar.objects.create( group = group, event = event1 )
        Calendar.objects.create( group = group, event = event2 )
        # user1
        url_user1_hashed = reverse( 'list_events_group_rss_hashed',
            kwargs = {'group_id': group.id, 'user_id': user1.id,
                'hash': ExtendedUser.calculate_hash( user1.id )} )
        self._validate_ical( url_user1_hashed )
        content = self.client.get( url_user1_hashed ).content
        self._validate_rss( content )
        self.assertTrue( 'public' in content )
        self.assertTrue( 'private' in content )
        # user2
        user2 = self._create_user()
        url_user2_hashed = reverse( 'list_events_group_rss_hashed',
            kwargs = {'group_id': group.id, 'user_id': user2.id,
                'hash': ExtendedUser.calculate_hash( user2.id )} )
        self._validate_ical( url_user2_hashed )
        content = self.client.get( url_user2_hashed ).content
        self.assertTrue( 'not a member' in content )
        # anonymous
        url_non_hashed = reverse( 'list_events_group_rss',
                kwargs = {'group_id': group.id,} )
        self._validate_ical( url_non_hashed )
        content = self.client.get( url_non_hashed ).content
        self._validate_rss( content )
        self.assertTrue( 'public' in content )
        self.assertFalse( 'private' in content )

    def user_group_edit( self, user_nr ): # {{{2
        "tests edit private and public events for user \
        after add this to group"
        user = self.get_user( user_nr )
        for nr in range( USERS_COUNT ):# pylint: disable-msg=C0103
            if nr != user_nr:
                public_event = self.get_event( user, True, True,
                                              self.get_user( nr ) )
                private_event = self.get_event( user, False, True,
                                               self.get_user( nr ) )
                login = self.login_user( nr )
                self.assertTrue( login )
                response = self.client.get( reverse(
                    'event_edit', kwargs = {'event_id': public_event.id} ) )
                txt = response.content
                self.assertTrue(
                        public_event.title.decode('utf-8') in txt.decode('utf-8'),
                        u"can't edit public event: %s\n %s" %
                            ( public_event.title.decode('utf-8'),
                                txt.decode('utf-8') ) )
                response = self.client.get( reverse( 
                    'event_edit', kwargs = {'event_id': private_event.id} ) )
                txt = response.content
                self.assertTrue(
                        private_event.title.decode('utf-8') in txt.decode('utf-8'),
                        "can't edit private event: %s\n %s" %
                            ( private_event.title.decode('utf-8'),
                                txt.decode('utf-8') ) )
                self.client.logout()

    def user_group_visibility( self, user_nr ): # {{{2
        "tests visibility private and public events for user \
        after add this to group"
        login = self.login_user( user_nr )
        self.assertTrue( login )
        response = self.client.get( reverse( 'list_events_tag', \
                                         kwargs = {'tag':'tag'} ) )
        txt = response.content
        for nr in range( USERS_COUNT ):# pylint: disable-msg=C0103
            if nr != user_nr:
                public_title = self.event_title( self.get_user( nr ), \
                                                 True, True )
                private_title = self.event_title( self.get_user( nr ), \
                                                  False, True )
                self.assertTrue(
                        public_title.decode('utf-8') in txt.decode('utf-8'),
                        u"not visible public event: %s" % \
                        public_title.decode('utf-8') )
                self.assertTrue(
                        private_title.decode('utf-8') in txt.decode('utf-8'), \
                        u"not visible private event from group: %s" \
                        % private_title.decode('utf-8') )
        self.client.logout()

    #FIXME: create a user with a filter, introduce an event anonymously
    # matching the filter, check that an email has been sent

    # FIXME: test is not working
    #def test_event_url( self ):
    #    "test editing adding and deleting event's url"
    #    for user_nr in range( USERS_COUNT ):
    #        self.assertTrue( self.login_user( user_nr ) )
    #        user = self.get_user( user_nr )
    #        for public in ( True, False ):
    #            event = self.get_event( user, public, True )
    #            # print map( lambda x: x.pk, Event.objects.all() ), event.pk
    #            history = EventHistory.objects.filter( event = event )
    #            self.client.post( reverse( 'event_edit',
    #                                     kwargs = {'event_id':event.id} )
    #            , {'urls-3-url_name':    '',
    #            'urls-2-url':    '',
    #            'sessions-1-id':    '',
    #            'postcode':    '',
    #            'title':    'test',
    #            'deadlines-3-deadline_name':    '',
    #            'sessions-0-id':    '',
    #            'urls-3-event':    event.id,
    #            'sessions-3-id':    '',
    #            'latitude':    '',
    #            'sessions-0-session_starttime':    '',
    #            'urls-TOTAL_FORMS':    '4',
    #            'sessions-2-session_name':    '',
    #            'deadlines-1-event':    event.id,
    #            'deadlines-2-id':    '',
    #            'deadlines-3-deadline':    '',
    #            'deadlines-0-event':    event.id,
    #            'sessions-3-session_name':    '',
    #            'sessions-2-session_endtime':    '',
    #            'urls-0-event':    event.id,
    #            'urls-3-id':    '',
    #            'urls-3-url':    '',
    #            'deadlines-MAX_NUM_FORMS':    '',
    #            'sessions-3-session_endtime':    '',
    #            'tags':    'tag',
    #            'acronym':    'LALA',
    #            'address':    '',
    #            'deadlines-0-id':    '',
    #            'sessions-0-session_date':    '',
    #            'deadlines-INITIAL_FORMS':    '0',
    #            'country':    '',
    #            'urls-INITIAL_FORMS':    '0',
    #            'deadlines-3-event':    event.id,
    #            'sessions-0-session_endtime':    '',
    #            'deadlines-2-deadline_name':    '',
    #            'sessions-1-session_starttime':    '',
    #            'deadlines-0-deadline':    '',
    #            'urls-0-url':    'http://onet.pl',
    #            'deadlines-1-deadline_name':    '',
    #            'sessions-3-session_starttime':    '',
    #            'sessions-2-session_starttime':    '',
    #            'sessions-INITIAL_FORMS':    '0',
    #            'urls-2-event':    event.id,
    #            'city':    '',
    #            'urls-1-url_name':    'wp',
    #            'urls-0-url_name':    'onet',
    #            'start':    '2010-10-10',
    #            'sessions-TOTAL_FORMS':    '4',
    #            'sessions-3-session_date':    '',
    #            'deadlines-2-deadline':    '',
    #            'urls-1-event':    event.id,
    #            'deadlines-1-id':    '',
    #            'sessions-0-event':    event.id,
    #            'deadlines-0-deadline_name':    '',
    #            'longitude':    '',
    #            'sessions-0-session_name':    '',
    #            'deadlines-2-event':    event.id,
    #            'deadlines-TOTAL_FORMS':    '4',
    #            'timezone':    '',
    #            'sessions-MAX_NUM_FORMS':    '',
    #            'sessions-1-session_date':    '',
    #            'deadlines-3-id':    '',
    #            'sessions-2-id':    '',
    #            'sessions-1-event':    event.id,
    #            'end':    '',
    #            'deadlines-1-deadline':    '',
    #            'sessions-2-session_date':    '',
    #            'sessions-1-session_name':    '',
    #            'urls-0-id':    '',
    #            'description':    '',
    #            'urls-1-url':    'http://wp.pl',
    #            'sessions-3-event':    event.id,
    #            'urls-2-url_name':    '',
    #            # 'urls-0-DELETE':    'on',
    #            'urls-2-id':    '',
    #            'urls-1-id':    '',
    #            'sessions-1-session_endtime':    '',
    #            'urls-MAX_NUM_FORMS':    '4',
    #            'sessions-2-event':    event.id
    #            } )
    #            response = self.client.get( reverse( 'event_edit_raw',
    #                                     kwargs = {'event_id':event.id} ) )
    #            self.assertTrue( 'http://onet.pl' in response.content )
    #            self.assertTrue( 'http://wp.pl' in response.content )
    #            history = EventHistory.objects.filter( event = event )
    #            # print 2, map( lambda x: ( x.new, x.user ), history ), len( history )
    #            url0 = EventUrl.objects.get( event = event, url_name = 'onet' )
    #            url1 = EventUrl.objects.get( event = event, url_name = 'wp' )
    #            self.client.post( reverse( 'event_edit',
    #                                     kwargs = {'event_id':event.id} )
    #            , {'urls-3-url_name':    '',
    #            'urls-2-url':    '',
    #            'sessions-1-id':    '',
    #            'postcode':    '',
    #            'title':    'test',
    #            'deadlines-3-deadline_name':    '',
    #            'sessions-0-id':    '',
    #            'urls-3-event':    event.id,
    #            'sessions-3-id':    '',
    #            'latitude':    '',
    #            'sessions-0-session_starttime':    '',
    #            'urls-TOTAL_FORMS':    '4',
    #            'sessions-2-session_name':    '',
    #            'deadlines-1-event':    event.id,
    #            'deadlines-2-id':    '',
    #            'deadlines-3-deadline':    '',
    #            'deadlines-0-event':    event.id,
    #            'sessions-3-session_name':    '',
    #            'sessions-2-session_endtime':    '',
    #            'urls-0-event':    event.id,
    #            'urls-3-id':    '',
    #            'urls-3-url':    '',
    #            'deadlines-MAX_NUM_FORMS':    '',
    #            'sessions-3-session_endtime':    '',
    #            'tags':    'tag',
    #            'acronym':    'LALA',
    #            'address':    '',
    #            'deadlines-0-id':    '',
    #            'sessions-0-session_date':    '',
    #            'deadlines-INITIAL_FORMS':    '0',
    #            'country':    '',
    #            'urls-INITIAL_FORMS':    '2',
    #            'deadlines-3-event':    event.id,
    #            'sessions-0-session_endtime':    '',
    #            'deadlines-2-deadline_name':    '',
    #            'sessions-1-session_starttime':    '',
    #            'deadlines-0-deadline':    '',
    #            'urls-0-url':    'http://onet.pl',
    #            'deadlines-1-deadline_name':    '',
    #            'sessions-3-session_starttime':    '',
    #            'sessions-2-session_starttime':    '',
    #            'sessions-INITIAL_FORMS':    '0',
    #            'urls-2-event':    event.id,
    #            'city':    '',
    #            'urls-1-url_name':    'wp',
    #            'urls-0-url_name':    'onet',
    #            'start':    '2010-10-10',
    #            'sessions-TOTAL_FORMS':    '4',
    #            'sessions-3-session_date':    '',
    #            'deadlines-2-deadline':    '',
    #            'urls-1-event':    event.id,
    #            'deadlines-1-id':    '',
    #            'sessions-0-event':    event.id,
    #            'deadlines-0-deadline_name':    '',
    #            'longitude':    '',
    #            'sessions-0-session_name':    '',
    #            'deadlines-2-event':    event.id,
    #            'deadlines-TOTAL_FORMS':    '4',
    #            'timezone':    '',
    #            'sessions-MAX_NUM_FORMS':    '',
    #            'sessions-1-session_date':    '',
    #            'deadlines-3-id':    '',
    #            'sessions-2-id':    '',
    #            'sessions-1-event':    event.id,
    #            'end':    '',
    #            'deadlines-1-deadline':    '',
    #            'sessions-2-session_date':    '',
    #            'sessions-1-session_name':    '',
    #            'urls-0-id':    url0.id,
    #            'description':    '',
    #            'urls-1-url':    'http://wp.pl',
    #            'sessions-3-event':    event.id,
    #            'urls-2-url_name':    '',
    #            'urls-0-DELETE':    'on',
    #            'urls-2-id':    '',
    #            'urls-1-id':    url1.id,
    #            'sessions-1-session_endtime':    '',
    #            'urls-MAX_NUM_FORMS':    '4',
    #            'sessions-2-event':    event.id
    #            } )
    #            response = self.client.get( reverse( 'event_edit_raw',
    #                                     kwargs = {'event_id':event.id} ) )
    #            self.assertFalse( 'http://onet.pl' in response.content )
    #            self.assertTrue( 'http://wp.pl' in response.content )
    #            history = EventHistory.objects.filter( event = event )
    #            # print 3, map( lambda x: ( x.new, x.user ), history ), len( history )


    # FIXME: test is not working
    #def test_groups( self ):
    #    "test groups behavior"
    #    mail.outbox = []
    #    re_inv_code = re.compile( r'g\/invite\/confirm\/([0-9a-f]+)\/' )
    #    for user_nr in range( USERS_COUNT ):
    #        self.user_create_groups( user_nr )
    #    for code, email in \
    #    map( lambda x: ( re_inv_code.findall( x.body )[0], x.to[0] ), mail.outbox ):# pylint: disable-msg=W0141,C0301
    #        user = User.objects.get( email = email )
    #        self.client.login( username = user.username, password = 'p' )
    #        self.client.get( reverse( 'group_invite_activate', \
    #                                kwargs = {'activation_key':code} ) )
    #        self.client.logout()
    #    mail.outbox = []
    #    for user_nr in range( USERS_COUNT ):
    #        self.user_add_event( user_nr )
    #    for user_nr in range( USERS_COUNT ):
    #        self.user_group_visibility( user_nr )
    #        self.user_group_edit( user_nr )

    def test_group_rss( self ): # {{{2
        "test for one rss.xml icon for each group"
        groups = Group.objects.all()
        for group in groups:
            self.validate_rss( reverse( 'list_events_group_rss',
                                      kwargs = {'group_id':group.id} ) )


    def test_visibility_private_event_in_group_when_searching( self ): # {{{2
        """ test that a private event added to a group is visible in the result
        of a search for a member of the group """
        user1 = self._create_user()
        user2 = self._create_user()
        group = self._create_group(user1)
        membership = Membership.objects.create(user=user2, group=group)
        membership.save()
        event = Event(user = user1, public = False, title="private",
                    start=datetime.date.today() + timedelta(days=10),
                    tags="test")
        event.save()
        cal = Calendar.objects.create(event = event, group = group)
        cal.save()
        self._login( user2 )
        content = self.client.get( reverse( 
                'list_events_search',
                kwargs = {'query': 'test',} ) )
        self.assertTrue( event in content.context['events'] )

    def test_event_ical( self ): # {{{2
        "test for one ical file for each event"
        events = Event.objects.all()
        for event in events:
            self._validate_ical( reverse( 'event_show_ical',
                                      kwargs = {'event_id':event.id} ) )

    def test_search_ical( self ): # {{{2
        "test for ical search"
        Event.objects.create( title = 'berlin'+str(time()), tags = 'berlin',
                start = datetime.date.today() )
        self._validate_ical( reverse( 'list_events_search_ical',
                                      kwargs = {'query':'berlin'} ) )
        # FIXME: text for a no match also

#    def test_filter_rss( self ): # {{{2
#        "test for the rss file of a filter"
#        user_tfi = self._create_user()
#        # creates 10 events anonymously and 10 belonging to user_tfi
#        chars = string.letters # you can append: + string.digits
#        tag = ''.join( [ choice(chars) for i in xrange(10) ] )
#        for i in range(20):
#            if i % 2: user = user_tfi
#            else: user = None
#            event = Event(user = user, public = True, title="test" + str(i),
#                    start=datetime.date.today() + timedelta(days=i-10),
#                    tags=tag)
#        # creates a filter
#        fil = Filter.objects.create(
#                user = user_tfi, query = tag, name = "test")
#        # checks the ical of the filter
#        user = self._login( user_tfi )
#        self._validate_ical( reverse( 'list_events_filter_ical',
#                                      kwargs = {'filter_id':fil.id} ) )
#        # FIXME: check that all the events are correct

#    def test_filter_ical( self ): # {{{2
#        "test for the iCalendar file of a filter"
#        user_tfi = self._create_user()
#        # creates 10 events anonymously and 10 belonging to user_tfi
#        chars = string.letters # you can append: + string.digits
#        tag = ''.join( [ choice(chars) for i in xrange(10) ] )
#        for i in range(20):
#            if i % 2: user = user_tfi
#            else: user = None
#            event = Event(user = user, public = True, title="test" + str(i),
#                    start=datetime.date.today() + timedelta(days=i-10),
#                    tags = tag )
#        # creates a filter
#        fil = Filter.objects.create(
#                user = user_tfi, query = tag, name = "test")
#        # checks the ical of the filter
#        user = self._login( user_tfi )
#        self._validate_ical( reverse( 'list_events_filter_ical',
#                                      kwargs = {'filter_id':fil.id} ) )
#        # FIXME: check that all the events are correct

#    def test_hash_filter_rss( self ): # {{{2
#        "test for one rss.xml icon for each filter"
#        for user_nr in range( USERS_COUNT ):
#            user = self.get_user( user_nr )
#            filters = Filter.objects.filter( user = user )
#            user_hash = self.user_hash( user.id )
#            for filer in filters:
#                self.validate_rss( reverse( 'list_events_filter_rss_hashed',
#                                      kwargs = {'filter_id':filer.id,
#                                                'user_id':user.id,
#                                                'hash':user_hash} ) )

#    def test_hash_filter_ical( self ): # {{{2
#        "test for one iCalendar file for each filter"
#        for user_nr in range( USERS_COUNT ):
#            user = self.get_user( user_nr )
#            filters = Filter.objects.filter( user = user )
#            user_hash = self.user_hash( user.id )
#            for filer in filters:
#                self._validate_ical( reverse( 'list_events_filter_ical_hashed',
#                                      kwargs = {'filter_id':filer.id,
#                                                'user_id':user.id,
#                                                'hash':user_hash} ) )

    # def test_history( self ): # {{{2
    #     "testing event's parser"
    #     for user_nr in range( USERS_COUNT ):
    #         user = self.get_user( user_nr )
    #         self.login_user( user_nr )
    #         for public in ( True, False ):
    #             event = self.get_event( user, public, True )
    #             self.client.post( reverse( 'event_edit',
    #                                      kwargs = {'event_id':event.id} )
    #             , {'urls-3-url_name':    '',
    #             'urls-2-url':    '',
    #             'sessions-1-id':    '',
    #             'postcode':    '',
    #             'title':    'test',
    #             'deadlines-3-deadline_name':    '',
    #             'sessions-0-id':    '',
    #             'urls-3-event':    event.id,
    #             'sessions-3-id':    '',
    #             'latitude':    '',
    #             'sessions-0-session_starttime':    '',
    #             'urls-TOTAL_FORMS':    '4',
    #             'sessions-2-session_name':    '',
    #             'deadlines-1-event':    event.id,
    #             'deadlines-2-id':    '',
    #             'deadlines-3-deadline':    '',
    #             'deadlines-0-event':    event.id,
    #             'sessions-3-session_name':    '',
    #             'sessions-2-session_endtime':    '',
    #             'urls-0-event':    event.id,
    #             'urls-3-id':    '',
    #             'urls-3-url':    '',
    #             'deadlines-MAX_NUM_FORMS':    '',
    #             'sessions-3-session_endtime':    '',
    #             'tags':    'tag',
    #             'acronym':    'LALA',
    #             'address':    '',
    #             'deadlines-0-id':    '',
    #             'sessions-0-session_date':    '',
    #             'deadlines-INITIAL_FORMS':    '0',
    #             'country':    '',
    #             'urls-INITIAL_FORMS':    '0',
    #             'deadlines-3-event':    event.id,
    #             'sessions-0-session_endtime':    '',
    #             'deadlines-2-deadline_name':    '',
    #             'sessions-1-session_starttime':    '',
    #             'deadlines-0-deadline':    '',
    #             'urls-0-url':    'http://onet.pl',
    #             'deadlines-1-deadline_name':    '',
    #             'sessions-3-session_starttime':    '',
    #             'sessions-2-session_starttime':    '',
    #             'sessions-INITIAL_FORMS':    '0',
    #             'urls-2-event':    event.id,
    #             'city':    '',
    #             'urls-1-url_name':    'wp',
    #             'urls-0-url_name':    'onet',
    #             'start':    '2010-10-10',
    #             'sessions-TOTAL_FORMS':    '4',
    #             'sessions-3-session_date':    '',
    #             'deadlines-2-deadline':    '',
    #             'urls-1-event':    event.id,
    #             'deadlines-1-id':    '',
    #             'sessions-0-event':    event.id,
    #             'deadlines-0-deadline_name':    '',
    #             'longitude':    '',
    #             'sessions-0-session_name':    '',
    #             'deadlines-2-event':    event.id,
    #             'deadlines-TOTAL_FORMS':    '4',
    #             'timezone':    '',
    #             'sessions-MAX_NUM_FORMS':    '',
    #             'sessions-1-session_date':    '',
    #             'deadlines-3-id':    '',
    #             'sessions-2-id':    '',
    #             'sessions-1-event':    event.id,
    #             'end':    '',
    #             'deadlines-1-deadline':    '',
    #             'sessions-2-session_date':    '',
    #             'sessions-1-session_name':    '',
    #             'urls-0-id':    '',
    #             'description':    '',
    #             'urls-1-url':    'http://wp.pl',
    #             'sessions-3-event':    event.id,
    #             'urls-2-url_name':    '',
    # #                'urls-0-DELETE':    'on',
    #             'urls-2-id':    '',
    #             'urls-1-id':    '',
    #             'sessions-1-session_endtime':    '',
    #             'urls-MAX_NUM_FORMS':    '4',
    #             'sessions-2-event':    event.id
    #             } )
    #             history = EventHistory.objects.filter( event = event )
    #             print map( lambda x: ( x.date, x.user ), history ), len( history )
    #             url0 = EventUrl.objects.get( event = event, url_name = 'onet' )
    #             url1 = EventUrl.objects.get( event = event, url_name = 'wp' )
    #             self.client.post( reverse( 'event_edit',
    #                                      kwargs = {'event_id':event.id} )
    #             , {'urls-3-url_name':    '',
    #             'urls-2-url':    '',
    #             'sessions-1-id':    '',
    #             'postcode':    '',
    #             'title':    'test',
    #             'deadlines-3-deadline_name':    '',
    #             'sessions-0-id':    '',
    #             'urls-3-event':    event.id,
    #             'sessions-3-id':    '',
    #             'latitude':    '',
    #             'sessions-0-session_starttime':    '',
    #             'urls-TOTAL_FORMS':    '4',
    #             'sessions-2-session_name':    '',
    #             'deadlines-1-event':    event.id,
    #             'deadlines-2-id':    '',
    #             'deadlines-3-deadline':    '',
    #             'deadlines-0-event':    event.id,
    #             'sessions-3-session_name':    '',
    #             'sessions-2-session_endtime':    '',
    #             'urls-0-event':    event.id,
    #             'urls-3-id':    '',
    #             'urls-3-url':    '',
    #             'deadlines-MAX_NUM_FORMS':    '',
    #             'sessions-3-session_endtime':    '',
    #             'tags':    'tag',
    #             'acronym':    'LALA',
    #             'address':    '',
    #             'deadlines-0-id':    '',
    #             'sessions-0-session_date':    '',
    #             'deadlines-INITIAL_FORMS':    '0',
    #             'country':    '',
    #             'urls-INITIAL_FORMS':    '2',
    #             'deadlines-3-event':    event.id,
    #             'sessions-0-session_endtime':    '',
    #             'deadlines-2-deadline_name':    '',
    #             'sessions-1-session_starttime':    '',
    #             'deadlines-0-deadline':    '',
    #             'urls-0-url':    'http://onet.pl',
    #             'deadlines-1-deadline_name':    '',
    #             'sessions-3-session_starttime':    '',
    #             'sessions-2-session_starttime':    '',
    #             'sessions-INITIAL_FORMS':    '0',
    #             'urls-2-event':    event.id,
    #             'city':    '',
    #             'urls-1-url_name':    'wp',
    #             'urls-0-url_name':    'onet',
    #             'start':    '2010-10-10',
    #             'sessions-TOTAL_FORMS':    '4',
    #             'sessions-3-session_date':    '',
    #             'deadlines-2-deadline':    '',
    #             'urls-1-event':    event.id,
    #             'deadlines-1-id':    '',
    #             'sessions-0-event':    event.id,
    #             'deadlines-0-deadline_name':    '',
    #             'longitude':    '',
    #             'sessions-0-session_name':    '',
    #             'deadlines-2-event':    event.id,
    #             'deadlines-TOTAL_FORMS':    '4',
    #             'timezone':    '',
    #             'sessions-MAX_NUM_FORMS':    '',
    #             'sessions-1-session_date':    '',
    #             'deadlines-3-id':    '',
    #             'sessions-2-id':    '',
    #             'sessions-1-event':    event.id,
    #             'end':    '',
    #             'deadlines-1-deadline':    '',
    #             'sessions-2-session_date':    '',
    #             'sessions-1-session_name':    '',
    #             'urls-0-id':    url0.id,
    #             'description':    '',
    #             'urls-1-url':    'http://wp.pl',
    #             'sessions-3-event':    event.id,
    #             'urls-2-url_name':    '',
    #             'urls-0-DELETE':    'on',
    #             'urls-2-id':    '',
    #             'urls-1-id':    url1.id,
    #             'sessions-1-session_endtime':    '',
    #             'urls-MAX_NUM_FORMS':    '4',
    #             'sessions-2-event':    event.id
    #             } )
    #             history = EventHistory.objects.filter( event = event )
    #             print map( lambda x: ( x.date, x.user ), history ), len( history )

    #This test can't work with sqlite, because sqlite not support multiusers, 
    #is recomendet to use this in future
    # def test_visibility_in_thread(self): # {{{2
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
