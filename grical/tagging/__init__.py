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
VERSION = (0, 3, 1, "final", 0)



def get_version():
    if VERSION[3] == "final":
        return "%s.%s.%s" % (VERSION[0], VERSION[1], VERSION[2])
    elif VERSION[3] == "dev":
        if VERSION[2] == 0:
            return "%s.%s.%s%s" % (VERSION[0], VERSION[1], VERSION[3], VERSION[4])
        return "%s.%s.%s.%s%s" % (VERSION[0], VERSION[1], VERSION[2], VERSION[3], VERSION[4])
    else:
        return "%s.%s.%s%s" % (VERSION[0], VERSION[1], VERSION[2], VERSION[3])


__version__ = get_version()


class AlreadyRegistered(Exception):
    """
    An attempt was made to register a model more than once.
    """
    pass


registry = []


def register(model, tag_descriptor_attr='tags',
             tagged_item_manager_attr='tagged'):
    """
    Sets the given model class up for working with tags.
    """

    from tagging.managers import ModelTaggedItemManager, TagDescriptor

    if model in registry:
        raise AlreadyRegistered("The model '%s' has already been "
            "registered." % model._meta.object_name)
    if hasattr(model, tag_descriptor_attr):
        raise AttributeError("'%s' already has an attribute '%s'. You must "
            "provide a custom tag_descriptor_attr to register." % (
                model._meta.object_name,
                tag_descriptor_attr,
            )
        )
    if hasattr(model, tagged_item_manager_attr):
        raise AttributeError("'%s' already has an attribute '%s'. You must "
            "provide a custom tagged_item_manager_attr to register." % (
                model._meta.object_name,
                tagged_item_manager_attr,
            )
        )

    # Add tag descriptor
    setattr(model, tag_descriptor_attr, TagDescriptor())

    # Add custom manager
    ModelTaggedItemManager().contribute_to_class(model, tagged_item_manager_attr)

    # Finally register in registry
    registry.append(model)
