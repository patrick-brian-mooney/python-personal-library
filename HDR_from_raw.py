#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Takes a raw image file and creates a tonemapped HDR from it. Requires dcraw
and the panotools suite.

Usage:

    ./HDR_from_raw FILE [FILE2] [FILE3] [...]

It can also be imported as a module by Python 3.X programs.

This script is copyright 2017 by Patrick Mooney. It is licensed under the GPL,
either version 3 or (at your option) any later version. See the file LICENSE.md
for details.
"""


import os, subprocess, sys

import create_HDR_script as chs     # from  https://github.com/patrick-brian-mooney/python-personal-library


force_debug = False


def create_HDR_script(rawfile):
    """Create a series of EV-shifted versions of the raw file, then produce a script
    that will tonemap them. Return the filename of the script.
    """
    files_to_merge = [][:]
    shifts = range(-4, 5)
    for shift_factor in shifts:                 # Create ISO-shifted files
        outfile = os.path.splitext(rawfile)[0] + ("+" if shift_factor >= 0 else "") + str(shift_factor) + ".jpg"
        command = 'dcraw  -c -v -w -W -b %s %s | cjpeg -quality 100 -dct float > %s' % (2 ** shift_factor, rawfile, outfile)
        subprocess.call(command, shell=True)
        files_to_merge += [outfile]
    chs.create_script_from_file_list(files_to_merge, delete_originals=True)
    return os.path.splitext(files_to_merge[0])[0] + '_HDR.SH'

if __name__ == "__main__":
    if force_debug:
        sys.argv += ['/home/patrick/Desktop/working/temp/IMG_7642.CR2']
    if len(sys.argv) == 1 or sys.argv[1] in ['--help', '-h']:
        print(__doc__)
        sys.exit(0)
    for whichfile in sys.argv[1:] :
        the_script = create_HDR_script(whichfile)
        subprocess.call(os.path.abspath(the_script), shell=True)
