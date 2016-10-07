#!/usr/bin/env python3
"""Runs a specified program, with any specified command-line arguments, in a
terminal, using nohup and redirecting stdout and stderr to /dev/null. That is,
it starts a program in a terminal, silencing its output and keeping it running
even if the terminal quits.

Usage:

    %s [command line you want to run]
"""

import subprocess, sys

if len(sys.argv) <= 1:
    print('\n\n' + __doc__ % sys.argv[0])
    sys.exit(2)

if sys.argv[1] in ['-h', '--help']:
    print('\n\n' + __doc__ % sys.argv[0])
    sys.exit(0)

subprocess.call('nohup %s &> /dev/null &' % ' '.join(sys.argv[1:]), shell=True)



