import os, sys
sys.path.append('/home/hg')
sys.path.append('/home/hg/cloca')
os.environ['DJANGO_SETTINGS_MODULE'] = 'cloca.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
