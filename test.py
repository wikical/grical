#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79

# read http://docs.djangoproject.com/en/dev/topics/testing/
# specially the section about using login

for x in range(0, 200):
    m = my_model(title=random_title(), field2=random_string(), ...)
    m.save()

