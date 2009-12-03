# This is needed for example for: return render_to_response( ... , context_instance=RequestContext(request))

def global_template_vars(request):
    from django.contrib.sites.models import Site
    from django.conf import settings
    from gridcalendar.groups.views import all_events_in_user_groups
    current_site = Site.objects.get_current()
#    return {'DOMAIN': current_site.domain, 'media_url': settings.MEDIA_URL, 'server_name': request.get_host(), 'user': request.user,}
    return {'DOMAIN': current_site.domain, 'media_url': settings.MEDIA_URL, 'user': request.user,}
#    return {'DOMAIN': current_site.domain, 'media_url': settings.MEDIA_URL, 'user': request.user, 'all_events_in_user_groups': all_events_in_user_groups(request.user.id)}
