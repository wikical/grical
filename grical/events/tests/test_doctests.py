# -*- coding: utf-8 -*-
# vi:expandtab:tabstop=4 shiftwidth=4 textwidth=79 foldmethod=marker

"""
Loading of ``wikical.core`` doctests
"""

from doctest import DocTestSuite

from .. import utils

def load_tests(loader, tests, ignore): #{{{1
    """ Load doctests from modules containing such tests.  """
    tests.addTest(DocTestSuite(utils))
    return tests
