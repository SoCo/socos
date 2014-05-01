#!/usr/bin/env python
""" socos is a commandline tool for controlling Sonos speakers """


# Will be parsed by setup.py to determine package metadata
__author__ = 'SoCo team <python-soco @googlegroups.com>'
__version__ = '0.1'
__website__ = 'https://github.com/SoCo/socos'
__license__ = 'MIT License'
import sys
from socos import process_cmd, shell


def main():
    """ main switches between (non-)interactive mode """
    args = sys.argv[1:]

    if args:
        # process command and exit
        process_cmd(args)
    else:
        # start interactive shell
        shell()

if __name__ == '__main__':
    main()
