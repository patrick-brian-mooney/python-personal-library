#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This quick hack makes bash script that uses the PTTools to stitch a panorama
from all photos in the current directory. Then it runs that script. It assumes
that all of the photos are JPGs in the current directory, that all of the JPGs
in the current directory are photos for the project, and that there are no
other .SH files in the current directory.

The output script written by this script makes a lot of assumptions; basically,
it automates my own most common panorama stitching process. It leaves behind a
.pto file that can be modified by hand, though.

A short (i.e., non-comprehensive) list of choices the output script makes for
you would involve:
    * using CPFind as the control point detector;
    * continuously overwriting the same project file instead of leaving
      multiple project files behind to allow for problem tracing;
    * the assumption that the input images are taken with a rectilinear lens;
    * runs Celeste;
    * runs CPFind's version of Celeste instead of Celeste standalone;
    * uses the --multirow match detection algorithm, which is generally good
      but not perfect for all possible scenarios;
    * runs CPClean with default parameters;
    * automatically optimizes control points, finds a suitable projection,
      and does photometric optimization;
    * automatically calculates ostensibly optimal canvas and crop sizes;
    
      
     

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk.

postprocess_photos.py is copyright 2015-16 by Patrick Mooney. It is free
software, and you are welcome to redistribute it under certain conditions,
according to the GNU general public license, either version 3 or (at your own
option) any later version. See the file LICENSE.md for details.
"""

import os, glob, subprocess

import postprocess_photos as pp # https://github.com/patrick-brian-mooney/personal-library/blob/master/postprocess_photos.py

the_files = sorted(glob.glob('*JPG') + glob.glob('*jpg'))
the_files_list = ' '.join(the_files)
project_file = the_files[0] + ".pto"
if the_files:
    the_script = """#!/usr/bin/env bash
# This script written by Patrick Mooney's create_HDR_script.py script, see
#     https://github.com/patrick-brian-mooney/personal-library/blob/master/create_panorama_script.py
pto_gen -o %s %s
""" % (project_file, the_files_list)
    
    the_script = the_script + """
cpfind --multirow --celeste -o %s %s
cpclean --output=%s %s
linefind -o %s %s
autooptimiser -a -l -s -m o %s %s
pano_modify --canvas=AUTO --crop=AUTO -o %s %s
PTBatcherGUI -b %s
""" % tuple([project_file] * 11)
    
    script_file_name = os.path.splitext(the_files[0])[0] + '.SH'
    with open(script_file_name, mode='w') as script_file:
        script_file.write(''.join(the_script))
    
    os.chmod(script_file_name, os.stat(script_file_name).st_mode | 0o111)    # or, in Bash, "chmod a+x SCRIPT_FILE_NAME"
    
    # pp.run_shell_scripts()
else:
    raise IndexError('You must call create_panorama_script.py in a folder with at least one .jpg or .JPG file;\n   current working directory is %s' % os.getcwd())