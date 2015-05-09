#!/usr/bin/env python
""" socos is a commandline tool for controlling Sonos speakers """

# when running from source, prefer source to installed version
import sys
import os.path
BASEDIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(BASEDIR, '..'))

from socos import SoCos


def main():
    """ main switches between (non-)interactive mode """
    socos = SoCos()
    args = sys.argv[1:]

    if args:
        # process command and exit
        socos.process_cmd(args)
    else:
        # start interactive shell
        socos.shell()


if __name__ == '__main__':
    main()
