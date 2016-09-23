#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79

# Source:
# http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html

from __future__ import absolute_import

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grical.settings.settings')

from django.conf import settings

# http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
app = Celery('grical')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
