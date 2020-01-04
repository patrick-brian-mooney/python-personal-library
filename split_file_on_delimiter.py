#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""split_file_on_delimiter.py: split a file into multiple files, based on the
specified delimiter.

Usage:

        ./split_file_on_delimiter.py FILENAME DELIMITER

splits the file FILENAME into FILENAME-0001, FILENAME-0002, etc. on the
specified delimiter, producing them in the same directory as FILENAME. FILENAME
still exists after this script runs.

Copyright © 2016 by Patrick Mooney.

This script is licensed under the GNU GPL, either v3 or, at your option, any
later version. See the file LICENSE.md for a copy of this license. You are
welcome to use this program, but it is presented WITHOUT ANY WARRANTY or other
guarantee: without even tghe guarantee of MERCHANTABILITY of FITNESS FOR ANY
PARTICULAR PURPOSE. Use of this script is at your own risk.
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

    oldpath = os.getcwd()
    newpath, filename = os.path.split(sys.argv[1])
    if newpath: os.chdir(newpath)

    with open(filename) as the_file:
        file_contents = the_file.read()
        new_files = file_contents.split(sys.argv[2])
        for which_file in range(len(new_files)):
            with open('%s-%04d' % (filename, which_file + 1), 'w') as this_file:
                this_file.write(new_files[which_file])

    os.chdir(oldpath)
