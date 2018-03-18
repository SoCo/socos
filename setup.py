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
filename = os.path.join(dirname, 'socos/__init__.py')
src = open(filename).read()
metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", src))
docstrings = re.findall('"""(.*)"""', src)

PACKAGE = 'socos'
PACKAGES = [ PACKAGE ]

AUTHOR_EMAIL = metadata['author']
VERSION = metadata['version']
WEBSITE = metadata['website']
LICENSE = metadata['license']
DESCRIPTION = docstrings[0]

CLASSIFIERS = [
	'Development Status :: 4 - Beta',
	'Environment :: Console',
	'Intended Audience :: End Users/Desktop',
	'License :: OSI Approved :: MIT License',
	'Natural Language :: English',
	'Operating System :: OS Independent',
	'Programming Language :: Python',
	'Programming Language :: Python :: 2',
	'Programming Language :: Python :: 2.7',
	'Programming Language :: Python :: 3',
	'Programming Language :: Python :: 3.2',
	'Programming Language :: Python :: 3.3',
	'Programming Language :: Python :: 3.4',
	'Programming Language :: Python :: 3.5',
	'Programming Language :: Python :: 3.6',
	'Programming Language :: Python :: 3.7',
	'Topic :: Home Automation',
	'Topic :: Multimedia :: Sound/Audio',
	'Topic :: Multimedia :: Sound/Audio :: Players',
]

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
      packages=PACKAGES,
      entry_points={
          'console_scripts': [
              'socos = socos.runner:main',
          ]
      },
	  classifiers=CLASSIFIERS,
      **OPTIONS)
