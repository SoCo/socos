""" socos is a commandline tool for controlling Sonos speakers """

# Will be parsed by setup.py to determine package metadata
__author__ = 'SoCo team <python-soco@googlegroups.com>'
__version__ = '0.1'
__website__ = 'https://github.com/SoCo/socos'
__license__ = 'MIT License'

from .core import process_cmd, shell

__all__ = ['process_cmd', 'shell']
