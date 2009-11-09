from django.conf.urls.defaults import *
from django.contrib import admin, databrowse
from django.contrib.admin import site
from django.conf import settings
from gridcalendar.events.models import Event, EventUrl, EventTimechunk, EventDeadline

databrowse.site.register(Event)
databrowse.site.register(EventUrl)
databrowse.site.register(EventTimechunk)
databrowse.site.register(EventDeadline)

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'views.index'),
    (r'^settings/$', 'views.settings'),
    (r'^accounts/', include('registration.urls')),
    (r'^events/', include('gridcalendar.events.urls')),
    (r'^groups/', include('gridcalendar.groups.urls')),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^db/(.*)', databrowse.site.root),
)

# see http://docs.djangoproject.com/en/1.0/howto/static-files/
if settings.DEBUG:
    urlpatterns += patterns('',
        ('^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )

