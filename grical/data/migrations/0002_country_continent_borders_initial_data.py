#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2016 Stefanos Kozanis <stefanos ät wikical.com>
#
# This file is part of GriCal.
#
# GriCal is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# GriCal is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the Affero GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with GriCal. If not, see <http://www.gnu.org/licenses/>.
#############################################################################
from __future__ import unicode_literals

import os.path

from django.core import serializers
from django.db import migrations

fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
        '../fixtures'))
fixture_filename = 'borders.json'

def load_fixture(apps, schema_editor):
    from django.conf import settings
    if settings.TESTS_RUNNING:
        # Currently we don't have any test relying to borders, we skip
        # to accelerate tests
        return

    fixture_file = os.path.join(fixture_dir, fixture_filename)

    with open(fixture_file) as fixture:
        objects = serializers.deserialize('json', fixture, ignorenonexistent=True)
        for obj in objects:
            obj.save()

# Most probably we won't add some revertion code to go to 0001, so this code
# won't execute ever and I take it out for coverage. At some point we may
# delete. Stefanos 2015-10-12 16:46:00+03:00
def unload_fixture(apps, schema_editor): # pragma: no cover
    "Brutally deleting all entries for this model..."

    CountryBorder = apps.get_model("data", "CountryBorder")
    CountryBorder.objects.all().delete()
    ContinentBorder = apps.get_model("data", "ContinentBorder")
    ContinentBorder.objects.all().delete()

class Migration(migrations.Migration):

    """
    Loads country borders
    See:
    http://stackoverflow.com/questions/25960850/loading-initial-data-with-django-1-7-and-data-migrations
    """

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_fixture, reverse_code=unload_fixture),
    ]
