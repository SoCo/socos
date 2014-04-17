#!/usr/bin/env python

try:
    from setuptools import setup
    has_setuptools = True
except ImportError:
    from distutils.core import setup
    has_setuptools = False

import re
import os.path

dirname = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(dirname, 'socos.py')
src = open(filename).read()
metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", src))
docstrings = re.findall('"""(.*)"""', src)

PACKAGE = 'socos'

MODULES = (
    'socos',
)

AUTHOR_EMAIL = metadata['author']
VERSION = metadata['version']
WEBSITE = metadata['website']
LICENSE = metadata['license']
DESCRIPTION = docstrings[0]

REQUIREMENTS = list(open('requirements.txt'))

OPTIONS = {}

if has_setuptools:
    OPTIONS = {
        'install_requires': REQUIREMENTS,
    }

# Extract name and e-mail ("Firstname Lastname <mail@example.org>")
AUTHOR, EMAIL = re.match(r'(.*) <(.*)>', AUTHOR_EMAIL).groups()

setup(name=PACKAGE,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      author_email=EMAIL,
      license=LICENSE,
      url=WEBSITE,
      py_modules=MODULES,
      scripts=['bin/socos'],
      entry_points={
          'console_scripts': [
              'socos = socos:main',
          ]
      },
      **OPTIONS)
