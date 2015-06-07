#!/usr/bin/env python

"""Run socos tests"""

from __future__ import print_function

import sys
import importlib
import pkgutil
import doctest

# prefer modules in current working directory
sys.path.insert(0, '.')

# package to test
PACKAGE = 'socos'


def doctest_package(package):
    """run doctests for the given package"""
    failed = 0

    # pylint: disable=unused-variable
    for _importer, modname, _ispkg in pkgutil.iter_modules([package]):
        # import all module from the package
        pkg = importlib.import_module(PACKAGE + '.' + modname)

        # run doctests
        res = doctest.testmod(pkg)
        print('{}: {!r}'.format(pkg.__name__, res))

        # accumulate failed tests
        failed += res.failed

    return failed

# return number of failed tests, ie error if at least one test failed
sys.exit(doctest_package(PACKAGE))
