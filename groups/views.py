import datetime, hashlib

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from tagging.models import TaggedItem, Tag

from gridcalendar.events.views import Event
from gridcalendar.groups.models import Group, Membership, Calendar, GroupInvitation, GroupInvitationManager
from gridcalendar.groups.forms import NewGroupForm, AddEventToGroupForm, InviteToGroupForm
from gridcalendar.groups.functions import all_events_in_user_groups

from gridcalendar.settings import SECRET_KEY

def create(request):
    if not request.user.is_authenticated():
        return render_to_response('groups/no_authenticated.html', {}, context_instance=RequestContext(request))
    if request.method == 'POST':
        form = NewGroupForm(request.POST)
        if form.is_valid():
            form.save()
            group_name = request.POST.get('name', '')
            new_group = Group.objects.get(name=group_name)
            new_membership = Membership(user=request.user, group=new_group)
            new_membership.save()
            # TODO: notify all invited members of the group
            return HttpResponseRedirect('/groups/list/')
        else:
            return render_to_response('groups/create.html', {'form': form}, context_instance=RequestContext(request))
    else:
        form = NewGroupForm()
        return render_to_response('groups/create.html', {'form': form}, context_instance=RequestContext(request))

def list_my_groups(request):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to list your groups") + "."},
                context_instance=RequestContext(request))
    else:
        u = User(request.user)
        groups = Group.objects.filter(membership__user=u)
        if len(groups) == 0:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You are not a member of any group") + "."},
                context_instance=RequestContext(request))
        else:
            return render_to_response('groups/list_my.html',
                {'title': 'list my groups', 'groups': groups},
                context_instance=RequestContext(request))

def quit_group(request, group_id, sure):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to quit your groups") + "."},
                context_instance=RequestContext(request))
    else:
        u = User(request.user)
        s = int(sure)
        try:
            try:
                g = Group.objects.get(id=group_id, membership__user=u)
            except Group.DoesNotExist:
#               if (len(Membership.objects.filter(group=g).filter(user=u)) == 0):
                return render_to_response('error.html', {'title': 'error', 'message_col1': _("There is no such group, or you are not a member of that group") + "."}, context_instance=RequestContext(request))
            else:
                testsize = len(Membership.objects.filter(group=g).exclude(user=u))
                if (testsize > 0):
                    m = Membership.objects.get(user=request.user, group=g)
                    m.delete()
                    return HttpResponseRedirect('/groups/list/')
                elif (s == 1):
                    m = Membership.objects.get(user=request.user, group=g)
                    m.delete()
                    g.delete()
                    return HttpResponseRedirect('/groups/list/')
                else:
                    return render_to_response('groups/quit_group_confirm.html', {'group_id': group_id, 'group_name': g.name}, context_instance=RequestContext(request))
        except:
            return render_to_response('error.html', {'title': 'error', 'message_col1': _("Quitting group failed") + "."}, context_instance=RequestContext(request))

def add_event(request, event_id):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to add an event to a group") + "."},
                context_instance=RequestContext(request))
    e = Event.objects.get(id=event_id)
    u = User(request.user)
    if len(Group.objects.filter(members=u).exclude(events=e)) > 0:
        if request.POST:
            f = AddEventToGroupForm(data=request.POST, u=u, e=e)
            if f.is_valid():
                for g in f.cleaned_data['grouplist']:
                    calentry = Calendar(event=e, group=g)
                    calentry.save()
                return HttpResponseRedirect('/groups/list/')
            else:
                request.user.message_set.create(message='Please check your data.')
        else:
            f = AddEventToGroupForm(u=u, e=e)
        context = dict()
        context['form'] = f
        return render_to_response('groups/add_event_to_group.html', context_instance=RequestContext(request, context))
    else:
        return render_to_response('error.html',
                    {'title': 'error',
                    'message_col1': _("This event is already in all groups that you are in, so you can't add it to any more groups.") },
                    context_instance=RequestContext(request))

def group(request, group_id):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to view events in a group") + "."},
                context_instance=RequestContext(request))
    else:
        group = Group.objects.filter(id=group_id)
        events = Event.objects.filter(group=group)
        token = hashlib.sha512("%s!%s!%s" % (SECRET_KEY, group_id, request.user.id)).hexdigest()
#        token = md5("%s!%s!%s" % (SECRET_KEY, group_id, request.user.id)).hexdigest()
        return render_to_response('groups/group.html',
                {'title': 'group page', 'group_id': group_id, 'user_id': request.user.id, 'token': token, 'events': events},
                context_instance=RequestContext(request))

def invite(request, group_id):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to invite someone to a group") + "."},
                context_instance=RequestContext(request))
    else:
        g = Group.objects.get(id=group_id)
        if request.POST:
            username_dirty=request.POST['username']
            formdata = {'username': username_dirty,
                        'group_id': group_id}
            form = InviteToGroupForm(data=formdata)
            if form.is_valid():
                username = form.cleaned_data['username']
                u = User.objects.get(username=username)
                GroupInvitation.objects.create_invitation(host=request.user, guest=u, group=g , as_administrator=True)
                return HttpResponseRedirect('/groups/list/')
            else:
                request.user.message_set.create(message='Please check your data.')
        else:
#            form = InviteToGroupForm(instance=invitation)
#            formdata = {
#                        'username': None,
#                        'group_id': group_id}
#            form = InviteToGroupForm(data=formdata)
            form = InviteToGroupForm()
        return render_to_response('groups/invite.html',
                {'title': 'invite to group', 'group_id': group_id, 'form': form},
                context_instance=RequestContext(request))

def activate(request, activation_key):
    """A user clicks on activation link"""
    i = GroupInvitation.objects.get(activation_key=activation_key)
    group_id = i.id
    a = GroupInvitation.objects.activate_invitation(activation_key)
    if a:
        return render_to_response('groups/invitation_activate.html',
                {'title': 'activate invitation', 'group_id': group_id},
                context_instance=RequestContext(request))
    else:
        return render_to_response('groups/invitation_activate_failed.html',
                {'title': 'activate invitation failed', 'group_id': group_id},
                context_instance=RequestContext(request))

