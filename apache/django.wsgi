from os.path import dirname, realpath
from os import environ
from sys import path

path.append(dirname(realpath(dirname(__file__))))

environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
