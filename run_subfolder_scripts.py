#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search through the subfolders of the current folder. For each subfolder found,
chdir() to it, then run all executable scripts ending in .SH in that folder.
Does not exhaustively search for subfolders of subfolders, or subfolders of
subfolders of subfolders, etc.; it only does exactly what was described in that
first sentence, without recursion.

Note that this calls scripts in an insecure way:

    subprocess.call(script_name, shell=True)

so it should only be called on scripts that are trusted completely.

This script is copyright 2017-20 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


import glob
import os

from pprint import pprint

import subprocess


the_dirs = [ d for d in glob.glob("*") if os.path.isdir(d) ]
for which_dir in the_dirs:
    olddir = os.getcwd()
    try:
        os.chdir(which_dir)
        print("changed directory to %s" % os.getcwd())
        exec_scripts = [ which_script for which_script in list(set(glob.glob('*SH') + glob.glob('*sh'))) if os.access(which_script, os.X_OK) ]
        pprint("exec_scripts are: %s" % exec_scripts)
        for which_script in exec_scripts:
            print("About to call script: %s" % which_script)
            subprocess.call('./' + which_script, shell=True)
            subprocess.call('chmod a-x %s' % which_script)
    except BaseException as e:
        print('Something went wrong; the system said %s' % e)
    finally:
        os.chdir(olddir)
