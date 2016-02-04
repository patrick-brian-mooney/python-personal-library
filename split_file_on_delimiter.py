#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""split_file_on_delimiter.py: split a file into multiple files, based on the
specified delimiter.

Usage:

        ./split_file_on_delimiter.py FILENAME DELIMITER

splits the file FILENAME into FILENAME-001, FILENAME-002, etc. on the specified
delimiter.

Copyright © 2016–present by Patrick Mooney. 

This script is licensed under the GNU GPL, either v3 or, at your option, any
later version. See the file LICENSE.md for a copy of this license. You are
welcome to use this program, but it is presented WITHOUT ANY WARRANTY or other
guarantee: without even tghe guarantee of MERCHANTABILITY of FITNESS FOR ANY
PARTICULAR PURPOSE. use of this script is at your own risk. By using this
program, you agree that in no circumstance
will the a 
"""

import sys, os

if __name__ == "__main__":
    if sys.argv[1] in ['-h', '--help']:
        print('\n')
        print(__doc__)
        sys.exit(0)
    elif len(sys.argv) != 3:
        print('\nERROR: Wrong number of command-line parameters.\n')
        print(__doc__)
        sys.exit(1)
