#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A stub to provide a command-line interface to the find_and_execute_scripts() in
file_utils.py.

scripts_runner.py is copyright 2015-20 by Patrick Mooney. It is free software,
and you are welcome to redistribute it under certain conditions, according to
the GNU general public license, either version 3 or (at your own option) any
later version. See the file LICENSE.md for details.
"""


import os
import sys


import file_utils as fu


debugging = False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            for whichdir in sys.argv[1:]:
                fu.find_and_execute_scripts(path=whichdir)
    else:
        if debugging: os.chdir('/home/patrick/NeedProcessing/Pictures/PanoramaGroups')
        fu.find_and_execute_scripts()
