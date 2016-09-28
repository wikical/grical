#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2012 Ivan F. Villanueva B. <ivan ät wikical.com>
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
from django.db import models

from grical.tagging.fields import TagField

class Perch(models.Model):
    size = models.IntegerField()
    smelly = models.BooleanField(default=True)

class Parrot(models.Model):
    state = models.CharField(max_length=50)
    perch = models.ForeignKey(Perch, null=True)

    def __unicode__(self):
        return self.state

    class Meta:
        ordering = ['state']

class Link(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Article(models.Model):
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']

class FormTest(models.Model):
    tags = TagField('Test', help_text='Test')
