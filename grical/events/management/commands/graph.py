#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set expandtab tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker:
# gpl {{{1
#############################################################################
# Copyright 2009-2011 Ivan F. Villanueva B. <ivan ät wikical.com>
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
# Set PYTHONPATH and DJANGO_SETTINGS_MODULE for your django app
# Example:
# export PYTHONPATH="/home/hg/gridcalendar:/home/hg/" ; export DJANGO_SETTINGS_MODULE="gridcalendar.settings"
# ./graph.py <django_app_name> | dot -Tpng -o graph.png

import sys
from django.contrib.gis.db.models import get_app, get_models
from django.core.management.base import BaseCommand, CommandError

class Command( BaseCommand ): # {{{1
    """ management command that writes to stdout a
    `DOT<http://en.wikipedia.org/wiki/DOT_language>`_ text describing the
    structure of the database.

    Usage example as management command::

            ./manage.py graph | dot -Tpng -o graph.png

    Usage example as management command for one application (``events`` as
    example)::

            ./manage.py graph events | dot -Tpng -o graph.png

    Usage example as script::

        export PYTHONPATH="/home/hg/gridcalendar:/home/hg/"
        export DJANGO_SETTINGS_MODULE="gridcalendar.settings"
        ./graph.py <django_app_name> | dot -Tpng -o graph.png

    """

    args = '<application_name>'
    help = "Write to stdout a DOT of the database. Usage example: " \
            "./manage graph | dot -Tpng -o graph.png"

    def handle( self, *args, **options ): # {{{2
        if len( args ) == 0:
            raise CommandError(
                    'this command needs one or more application names as ' \
                    'parameters' )
        graph( args, Command.stdout )

def graph(apps, outfile):
    models = []
    for app in apps:
        models += get_models(get_app(app))

    outfile.write("digraph G {\n")

    for model in models:

        # Format the shape
        name = model._meta.object_name
        label = "%s\\n" % name + "\\n".join([field.name for field in model._meta._fields()])
        outfile.write("%s [shape=box,label=\"%s\"];" % (name, label))

        # Draw the relations
        for related in model._meta.get_all_related_objects():
            outfile.write("\t%s -> %s;\n" % (name, related.model._meta.object_name))

        for related in model._meta.get_all_related_many_to_many_objects():
            outfile.write("\t%s -> %s [dir=both];\n" % (name, related.model._meta.object_name))

    outfile.write("}\n")

if __name__=="__main__":

    if len(sys.argv) != 2:
        print "graph.py <appname>"
        print "\tWrites a graph of your models suitable for processing with graphviz"
        sys.exit(1)

    graph(sys.argv[1], sys.stdout)

# setting stdout and stderr for Command {{{1
try:
    getattr( Command, 'stdout' )
except AttributeError:
    Command.stdout = sys.stdout
try:
    getattr( Command, 'stderr' )
except AttributeError:
    Command.stderr = sys.stderr
