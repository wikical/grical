def global_template_vars(request):
    from django.conf import settings
    return {'media_url': settings.MEDIA_URL, 'server_name': request.get_host(), 'user': request.user,}
