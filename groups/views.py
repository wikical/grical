import datetime
from django.http import HttpResponse
from tagging.models import TaggedItem
from tagging.models import Tag
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from tagging.models import TaggedItem
from tagging.models import Tag
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect

from gridcalendar.events.views import Event
from gridcalendar.groups.models import Group, Membership, Calendar
from gridcalendar.groups.forms import NewGroupForm, AddEventToGroupForm

def edit(request, event_id):
    pass
#    try:
#        event = Event.objects.get(id=event_id)
#    except Event.DoesNotExist:
#        return render_to_response('index.html',
#                    {'form': getEventForm(request.user),
#                    'message_col1': _("The event with the following number doesn't exist") + ": " + str(event_id)},
#                    context_instance=RequestContext(request))
#    # events submitted by anonymous users can be edited by anyone, otherwise only by the submitter
#    if (event.user is not None) and ((not request.user.is_authenticated()) or (event.user.id != request.user.id)):
#        return render_to_response('index.html',
#                {'form': getEventForm(request.user),
#                'message_col1': _('You are not allowed to edit the event with the following number') +
#                ": " + str(event_id) + ". " +
#                _("Maybe it is because you are not logged in with the right account") + "."},
#                context_instance=RequestContext(request))
#    else:
#        if request.method == 'POST':
#            if request.user.is_authenticated():
#                ef = EventForm(request.POST, instance=event)
#            else:
#                ef = EventFormAnonymous(request.POST, instance=event)
#            if ef.is_valid():
#                ef.save()
#                # TODO: look in a thread for all users who wants to receive an email notification and send it
#                return HttpResponseRedirect('/')
#            else:
#                return render_to_response('events/edit.html', {'form': ef}, context_instance=RequestContext(request))
#        else:
#            if request.user.is_authenticated():
#                form = EventForm(instance=event)
#            else:
#                form = EventFormAnonymous(instance=event)
#            return render_to_response('events/edit.html', {'form': form}, context_instance=RequestContext(request))

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
                {'title': 'error', 'message_col1': _("You are not a member of any groups yet") + "."},
                context_instance=RequestContext(request))
        else:
            return render_to_response('groups/list_my.html',
                {'title': 'list my groups', 'groups': groups},
                context_instance=RequestContext(request))

def quit_group(request, group_id):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to quit your groups") + "."},
                context_instance=RequestContext(request))
    else:
        u = User(request.user)
        try:
            g = Group.objects.get(id=group_id, membership__user=u)
            m = Membership.objects.get(user=request.user, group=g)
            m.delete()
            return HttpResponseRedirect('/groups/list/')
        except:
            return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("There is no such group or you are not a member of that group") + "."},
                context_instance=RequestContext(request))

def add_event(request, event_id):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to add an event to a group") + "."},
                context_instance=RequestContext(request))
    e = Event.objects.get(id=event_id)
    calentry = Calendar(event=e)
    if request.POST:
        form = AddEventToGroupForm(data=request.POST, instance=calentry)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/groups/list/')
        else:
            request.user.message_set.create(message='Please check your data.')
    else:
        form = AddEventToGroupForm(instance=calentry)
    context = dict()
    context['form'] = form
    return render_to_response('groups/add_event_to_group.html', context_instance=RequestContext(request, context))

#        u = User(request.user)
#        data = {'user_id': u,}
#        form = AddEventToGroupForm(data)
#        return render_to_response('groups/add_event_to_group.html', {'form': form}, context_instance=RequestContext(request))

def group(request, group_id):
    if ((not request.user.is_authenticated()) or (request.user.id is None)):
        return render_to_response('error.html',
                {'title': 'error', 'message_col1': _("You must be logged in to view events in a group") + "."},
                context_instance=RequestContext(request))
    else:
        group = Group.objects.filter(id=group_id)
        events = Event.objects.filter(group=group)
        return render_to_response('groups/group.html',
                {'title': 'group page', 'group_id': group_id, 'events': events},
                context_instance=RequestContext(request))

def answer_invitation(request, group_id):
    """A user can accept or deny the invitation"""
    pass
