import os, sys
sys.path.append('/usr/local/django-projects')
sys.path.append('/usr/local/django-projects/gridcalendar')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gridcalendar.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
