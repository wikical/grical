# -*- coding: utf-8 -*-
# This is needed for example for:
# return render_to_response( ... , context_instance=RequestContext(request))

# TODO: think of (also) using TEMPLATE_CONTEXT_PROCESSORS =
# ('django.core.context_processors.request',)

def global_template_vars(request):
    from django.contrib.sites.models import Site
    from django.conf import settings
    current_site = Site.objects.get_current()
    if request.is_secure(): protocol = "https"
    else: protocol = "http"
    return {
            'PROTOCOL': protocol,
            'DOMAIN': current_site.domain,
            'media_url': settings.MEDIA_URL,
            'user': request.user,
            'VERSION': settings.VERSION,
            }
