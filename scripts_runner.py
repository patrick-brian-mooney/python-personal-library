#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contains routines to interact with the file system. Currently, it contains the
following routines:

 * find_and_execute_scripts(): given a directory, executes all executable
   shell scripts (files with names ending in SH) in that directory and its
   subdirectories, then runs them.

When run from the command line, the script runs find_and_execute_scripts() in
the current directory.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk.

scripts_runner.py is copyright 2015-16 by Patrick Mooney. It is free software,
and you are welcome to redistribute it under certain conditions, according to
the GNU general public license, either version 3 or (at your own option) any
later version. See the file LICENSE.md for details.
"""


import os, sys, subprocess


debugging = True


def find_and_execute_scripts(path='.'):
    """Find executable *SH files in the current directory and its subdirectories,
    then execute them. Specify the path to walk as PATH; it defaults to the
    current directory.
    """
    for (dirname, subsheres, fileshere) in os.walk(path):
        print('Looking for scripts in %s' % dirname)
        file_list = sorted([ which_script for which_script in fileshere if which_script.endswith('SH') ])
        # file_list = [ which_script for which_script in file_list if os.access(which_script, os.X_OK) ]
        for which_script in file_list:
            try:
                olddir = os.getcwd()
                os.chdir(dirname)
                print('\n\n    Running script: %s' % which_script)
                subprocess.call('./' + which_script)
                os.system('chmod a-x -R %s' % which_script)
            finally:
                os.chdir(olddir)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            for whichdir in sys.argv[1:]:
                find_and_execute_scripts(path=whichdir)
    else:
        if debugging: os.chdir('/home/patrick/NeedProcessing/Pictures/PanoramaGroups')
        find_and_execute_scripts()
