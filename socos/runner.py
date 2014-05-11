#!/usr/bin/env python
""" socos is a commandline tool for controlling Sonos speakers """

# when running from source, prefer source to installed version
import sys
import os.path
BASEDIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASEDIR, '..'))

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
