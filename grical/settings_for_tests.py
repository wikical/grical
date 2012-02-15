#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" configuration file for local installations of the source tree """
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79

from settings_base import *

SECRET_KEY = '(a#%@bhr23!af9875tybca(_a.13524fgav@#$a1ybkdzlfrq$'

DATABASES = {  
    'default': {  
         'ENGINE': 'django.contrib.gis.db.backends.postgis',
         'NAME': 'dev',
         'USER': 'development',           
         'PASSWORD': 'testingthings',
     }
}

# Receive messages from emails
IMAP_SERVER = 'localhost'
IMAP_LOGIN = 'eventdev'
IMAP_PASSWD = 'edee218#E'
IMAP_SSL = False

GEONAMES_USERNAME = 'ogai'
GEONAMES_URL = 'https://secure.geonames.net/'

ADMINS = (
    ('Ivan Villanueva', 'ivan@gridmind.org'),
)

MANAGERS = ADMINS

# Emails
REPLY_TO = 'office@grical.org'
DEFAULT_FROM_EMAIL = 'noreply@grical.org'
SERVER_EMAIL = 'noreply@grical.org'
EMAIL_SUBJECT_PREFIX = '[dev.grical.org]'
EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'event'
EMAIL_HOST_PASSWORD = 'cloca88'
EMAIL_USE_TLS = True
SEND_BROKEN_LINK_EMAILS = True

# IRC
LOG_PIPE = False
LOG_PIPE_GID = 33
IRC_NETWORK = 'irc.freenode.net'
IRC_PORT = 6667
IRC_CHANNEL = '#gridcalendar-dev'
IRC_NICK = 'gricalrobot-dev'
IRC_NAME = 'dev.grical.org log robot'
