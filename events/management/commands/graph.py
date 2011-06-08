#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79
#!/usr/bin/env python

# Found at http://djangosnippets.org/snippets/1168/

# Copyright (C) 2008 Adam Lofts
#               2011 Ivan Villanueva <iv ät gridmind.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# This program generates a graphviz file to plot a graph of your database
# layout.
# 
# Usage:
#
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
    
    Usage example::

            ./manage graph | dot -Tpng -o graph.png

    """

    args = '<application_name>'
    help = "Write to stdout a DOT of the database. Usage example: " \
            "./manage graph | dot -Tpng -o graph.png"

    def handle( self, *args, **options ): # {{{2
        if len( args ) > 1:
            raise CommandError(
                    'this command accept 0 or 1 argument but not more' )
        if len( args ) == 1:
            application_name = args[0]
        else:
            application_name = 'events'
        graph( application_name, Command.stdout )

def graph(app, outfile):

    models = get_models(get_app(app))

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
