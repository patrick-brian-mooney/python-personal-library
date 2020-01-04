#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

__doc__ = """%s: Remove the BOM from BOM-containing UTF-8 text files. These are, almost
without exception, produced by Microsoft products, especially under Windows. 

Hey Microsoft: fuck you for deciding to produce noncompliant files instead of 
adequately tracking metadata. Stop shitting all over people's data to mark
your turf and/or cover your mistakes. It's bad information citizenship.

Usage:
    
    %s --help
        Show this help message

    %s FILE [FILE2, FILE3, ...]
        Rewrite the specified UTF-8 files in place, removing any leading BOM.

This program will not work if the input file is encoded with any encoding other
than UTF-8. (It WILL work, i.e. do nothing, if the input file is UTF-8 with no
BOM.) It will not produce output files in any format other than BOMless UTF-8.
Use a program like iconv for more general conversions.

%s is copyright © 2016-17 by Patrick Mooney. 

This script is licensed under the GNU GPL, either v3 or, at your option, any
later version. See the file LICENSE.md for a copy of this license. You are
welcome to use this program, but it is presented WITHOUT ANY WARRANTY or other
guarantee: without even the guarantee of MERCHANTABILITY of FITNESS FOR ANY
PARTICULAR PURPOSE. Use of this script is at your own risk. By using this
program, you agree that in no circumstance will the author of the script be
liable for any damage it causes. 
""" % (tuple([sys.argv[0]]) * 4)


def print_usage(exit_code=0):
    print(__doc__)
    sys.exit(exit_code)


def produce_BOMless(f):
    with open(f, encoding="utf-8-sig") as fh:
        content = fh.read()
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(content)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_usage(1)
    elif len(sys.argv) == 2 and (sys.argv[1].lower() == "--help" or sys.argv[1].lower() == "-h"):
        print_usage(0)
    elif len(sys.argv) >=2:
        for which_file in sys.argv[1:]:
            produce_BOMless(which_file)
