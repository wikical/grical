# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin, databrowse

from events.models import Event, Group, EventUrl, EventSession, EventDeadline

# databrowse.site.register(Event)
# databrowse.site.register(Group)
# databrowse.site.register(EventUrl)
# databrowse.site.register(EventSession)
# databrowse.site.register(EventDeadline)

admin.autodiscover()

urlpatterns = patterns('',
    (r'^a/admin/doc/', include('django.contrib.admindocs.urls')),
    #(r'^a/admin/(.*)', admin.site.root),
    (r'^a/admin/', admin.site.urls),
    (r'^a/db/(.*)', databrowse.site.root),
    (r'^a/accounts/', include('registration.urls')),
    (r'^a/accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
)

urlpatterns += patterns('',
    #(r'^comments/', include('django.contrib.comments.urls')),
)

urlpatterns += patterns('',
    (r'', include('events.urls')),
)

# see http://docs.djangoproject.com/en/1.0/howto/static-files/
if settings.DEBUG:
    urlpatterns += patterns('',
        ('^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
