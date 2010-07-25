#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#############################################################################
# Copyright 2009, 2010 Iván F. Villanueva B. <ivan ät gridmind.org>
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

""" Groups related views """

import hashlib

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from gridcalendar.events.decorators import login_required

from gridcalendar.settings import SECRET_KEY

from gridcalendar.events.models import (
        Event, Group, Membership, Calendar, GroupInvitation, )
from gridcalendar.events.forms import (
        NewGroupForm, AddEventToGroupForm, InviteToGroupForm )

@login_required
def group_new(request):
    """ View to create a new group """
    if not request.user.is_authenticated():
        return render_to_response('groups/no_authenticated.html',
                {}, context_instance=RequestContext(request))
    if request.method == 'POST':
        form = NewGroupForm(request.POST)
        if form.is_valid():
            form.save()
            group_name = request.POST.get('name', '')
            new_group = Group.objects.get(name=group_name)
            new_membership = Membership(user=request.user, group=new_group)
            new_membership.save()
            # TODO: notify all invited members of the group
            return HttpResponseRedirect(reverse('list_groups_my'))
        else:
            return render_to_response('groups/create.html',
                    {'form': form}, context_instance=RequestContext(request))
    else:
        form = NewGroupForm()
        return render_to_response('groups/create.html',
                {'form': form}, context_instance=RequestContext(request))

@login_required
def list_groups_my(request):
    """ view that lists all groups of the logged-in user """
    # Theoretically not needed because of the decorator:
    #if ((not request.user.is_authenticated()) or (request.user.id is None)):
    #    return render_to_response('error.html',
    #            {
    #                'title': 'error',
    #                'message_col1': _("You must be logged in to list your \
    #                    groups")
    #            },
    #            context_instance=RequestContext(request))
    #else:
    user = User(request.user)
    groups = Group.objects.filter(users_in_group__user=user)
    if len(groups) == 0:
        return render_to_response('error.html',
            {
                'title': 'error',
                'message_col1': _("You are not a member of any group"),
            },
            context_instance=RequestContext(request))
    else:
        return render_to_response('groups/list_my.html',
            {'title': 'list my groups', 'groups': groups},
            context_instance=RequestContext(request))

@login_required
def group_quit(request, group_id, sure):
    """ remove the logged-in user from a group asking for confirmation if the
    user is the last member of the group """
    user = User(request.user)
    try:
        group = Group.objects.get(id=group_id, users_in_group__user=user)
    except Group.DoesNotExist:
        return render_to_response('error.html',
                {
                    'title': 'error',
                    'message_col1': _("There is no such group, or you \
                        are not a member of that group")
                },
                context_instance=RequestContext(request))
    testsize = len(
            Membership.objects.filter(group=group).exclude(user=user))
    if (testsize > 0):
        membership = Membership.objects.get(user=request.user, group=group)
        membership.delete()
        return HttpResponseRedirect(reverse('list_groups_my'))
    elif (sure):
        membership = Membership.objects.get(user=request.user, group=group)
        membership.delete()
        group.delete()
        return HttpResponseRedirect(reverse('list_groups_my'))
    else:
        return render_to_response('groups/quit_group_confirm.html',
                # TODO: show the user a list of all private events which will
                # be lost for everyone
                {
                    'group_id': group_id,
                    'group_name': group.name
                },
                context_instance=RequestContext(request))
#        except:
#            return render_to_response('error.html', {'title': 'error',
#            'message_col1': _("Quitting group failed") + "."},
#            context_instance=RequestContext(request))

@login_required
def group_quit_ask(request, group_id):
    """ view to confirm of quiting a group """
    return group_quit(request, group_id, False)

@login_required
def group_quit_sure(request, group_id):
    """ view to confirm of quiting a group being sure"""
    return group_quit(request, group_id, True)

@login_required
def group_add_event(request, event_id):
    """ view to add an event to a group """
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {
                    'title': 'GridCalendar.net - error',
                    'message_col1': _("You must be logged in to add an event \
                            to a group")
                },
                context_instance=RequestContext(request))
    event = Event.objects.get(id=event_id)
    user = User(request.user)
    if len(Group.objects.filter(members=user).exclude(events=event)) > 0:
        if request.POST:
            form = AddEventToGroupForm(
                    data=request.POST, user=user, event=event)
            if form.is_valid():
                if not event.public:
                    event = event.get_clone()
                for group in form.cleaned_data['grouplist']:
                    calentry = Calendar(event=event, group=group)
                    calentry.save()
                return HttpResponseRedirect(reverse('list_groups_my'))
            else:
                request.user.message_set.create(
                        message='Please check your data.')
        else:
            form = AddEventToGroupForm(user=user, event=event)
        context = dict()
        context['form'] = form
        return render_to_response('groups/add_event_to_group.html',
                context_instance=RequestContext(request, context))
    else:
        return render_to_response('error.html',
                    {
                        'title': 'error',
                        'message_col1': _("This event is already in all \
                                groups that you are in, so you can't add it \
                                to any more groups.")
                    },
                    context_instance=RequestContext(request))

@login_required
def list_events_group(request, group_id):
    """ view that lists the events of group """
    group = Group.objects.filter(id=group_id)
    events = Event.objects.filter(group=group)
    hashvalue = hashlib.sha256(
            "%s!%s" % (SECRET_KEY, request.user.id)).hexdigest()
    return render_to_response('groups/group.html',
            {
                'title': 'group page',
                'group_id': group_id,
                'user_id': request.user.id,
                'hash': hashvalue,
                'events': events
            },
            context_instance=RequestContext(request))

@login_required
def group_invite(request, group_id):
    """ view to invite a user to a group """
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {
                    'title': 'error',
                    'message_col1': _("You must be logged in to invite \
                            someone to a group")
                },
                context_instance=RequestContext(request))
    else:
        group = Group.objects.get(id=group_id)
        if request.POST:
            username_dirty = request.POST['username']
            formdata = {'username': username_dirty,
                        'group_id': group_id}
            form = InviteToGroupForm(data=formdata)
            if form.is_valid():
                username = form.cleaned_data['username']
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return render_to_response('error.html',
                        {
                            'title': 'error',
                            'message_col1': _("There is no user with the \
                                username: ") + username
                        },
                        context_instance=RequestContext(request))
                GroupInvitation.objects.create_invitation(host=request.user,
                        guest=user, group=group , as_administrator=True)
                return HttpResponseRedirect(reverse('list_groups_my'))
            else:
                request.user.message_set.create(
                        message='Please check your data.')
        else:
#            form = InviteToGroupForm(instance=invitation)
#            formdata = {
#                        'username': None,
#                        'group_id': group_id}
#            form = InviteToGroupForm(data=formdata)
            form = InviteToGroupForm()
        return render_to_response('groups/invite.html',
                {
                    'title': 'invite to group',
                    'group_id': group_id,
                    'form': form
                },
                context_instance=RequestContext(request))

@login_required
def group_invite_activate(request, activation_key):
    """ A user clicks on activation link """
    invitation = GroupInvitation.objects.get(activation_key=activation_key)
    group_id = invitation.id
    activation = GroupInvitation.objects.activate_invitation(activation_key)
    if activation:
        return render_to_response('groups/invitation_activate.html',
                {'title': 'activate invitation', 'group_id': group_id},
                context_instance=RequestContext(request))
    else:
        return render_to_response('groups/invitation_activate_failed.html',
                {'title': 'activate invitation failed', 'group_id': group_id},
                context_instance=RequestContext(request))

