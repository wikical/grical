import os, sys
sys.path.append('/home/hg')
sys.path.append('/home/hg/gridcalendar')
os.environ['DJANGO_SETTINGS_MODULE'] = 'gridcalendar.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
