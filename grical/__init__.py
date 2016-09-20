# See: http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
# DO NOT* remove this, it is used to load celery application.
from .celery import app as celery_app

VERSION = (1,0)
