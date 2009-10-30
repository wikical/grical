from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.admin import site
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'views.index'),
    (r'^settings/$', 'views.settings'),
    (r'^accounts/', include('registration.urls')),
    (r'^events/', include('cloudcalendar.events.urls')),
    (r'^groups/', include('cloudcalendar.groups.urls')),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    (r'^comments/', include('django.contrib.comments.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
)

# see http://docs.djangoproject.com/en/1.0/howto/static-files/
if settings.DEBUG:
    urlpatterns += patterns('',
        ('^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )

