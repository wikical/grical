import os, sys
#sys.path.append('/home/hg/gridcalendar')
sys.path.append(dirname(os.path.realpath(os.path.dirname(__file__))))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
