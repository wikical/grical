from os.path import dirname, realpath
from os import environ
from sys import path

path.append(dirname(realpath(dirname(__file__))))

path.append(dirname(dirname(realpath(dirname(__file__)))))

environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

import settings
# see http://blog.dscpl.com.au/2008/12/using-modwsgi-when-developing-django.html
import gridcalendar.monitor
if settings.DEBUG:
    gridcalendar.monitor.start(interval=1.0)
