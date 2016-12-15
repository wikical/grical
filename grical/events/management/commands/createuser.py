#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker
# Copyright 2014 Stefanos Kozanis <stefanos@gridmind.org>
# Copyright 2014 Ivan Villanueava <ivan@gridmind.org>

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = 'Creates a user'

    def add_arguments(self, parser):
        # https://docs.python.org/2.7/library/argparse.html#module-argparse
        parser.add_argument('username', type=str, nargs=1)
        parser.add_argument('password', type=str, nargs=1)
        parser.add_argument('email', type=str, nargs=1)
        parser.add_argument('--superuser', action = 'store_true',
            default = False,
            help = 'If set, it creates a superuser'
        )

    def handle(self, *args, **options):
        username = options['username'][0]
        password = options['password'][0]
        email = options['email'][0]
        User = get_user_model()

        def create_user():
            if User.objects.filter(username__iexact=username).exists():
                raise RuntimeError('A similar user already exists whose name '
                    'collisions on a case insensitive comparison with '
                    '"{}"'.format(username))
            credentials = \
                {'username': username, 'password': password,
                        'email': email,}
            if options.get('superuser'):
                user = User.objects.create_superuser(**credentials)
            else:
                user = User.objects.create_user(**credentials)
            user.save()

        try:
            User.objects.get(username=username)
            self.stdout.write('User with this username already exists\n')
        except User.DoesNotExist:
            create_user()
