#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Usage:
    
    ./create_HDR_script FIRST-FILENAME

This script takes one argument, the name of the first file to be used in an HDR
enfuse script. The bash scripts produced by this script are similar to the
re-written Magic Lantern scripts produced by my postprocess-photos.py script.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk.

create_HDR_script.py is copyright 2015-16 by Patrick Mooney. It is free
software, and you are welcome to redistribute it under certain conditions,
according to the GNU general public license, either version 3 or (at your own
option) any later version. See the file LICENSE.md for details.
"""

import sys
import glob
import os

total_number_of_files = 5   # Total number of input files that are referenced by default in the auto-generated enfuse script

def print_usage(exit_value=0):
    """Print a usage message."""
    print(__doc__)
    sys.exit(exit_value)

def create_script_from_file_list(HDR_input_files, file_to_move=None, file_to_delete=None):
    """This procedure creates an enfuse HDR script from a list of files that compose it."""
    output_file = os.path.splitext(HDR_input_files[0])[0].strip() + "_HDR.TIFF"
    output_TIFF_base = os.path.splitext(output_file)[0].strip().replace('-','').replace('_','')
    
    the_script = """#!/usr/bin/env bash

# %s from %s ... %s with aligning first
# This script written by Patrick Mooney's create_HDR_script.py script, see
#     https://github.com/patrick-brian-mooney/personal-library/blob/master/create_HDR_script.py
""" % (output_file, HDR_input_files[0], HDR_input_files[-1])
    
    the_script = the_script + """
align_image_stack -mv -a HDR_AIS_%s %s
enfuse "$@"  --output=%s HDR_AIS_%s*
rm HDR_AIS_%s*
""" % (output_TIFF_base, ' '.join(HDR_input_files), output_file, output_TIFF_base, output_TIFF_base)
    
    the_script = the_script + """
convert %s -quality 95 %s.JPG
rm %s
exiftool -tagsfromfile %s %s.JPG
""" % (output_file, os.path.splitext(output_file)[0], output_file, HDR_input_files[0], os.path.splitext(output_file)[0])
    
    the_script = the_script + """
rm %s.JPG_original
mv %s HDR_components/
""" % (os.path.splitext(output_file)[0], ' '.join(HDR_input_files))
    
    script_file_name = os.path.splitext(output_file)[0] + '.SH'
    with open(script_file_name, mode='w') as script_file:
        script_file.write(''.join(the_script))
    
    os.chmod(script_file_name, os.stat(script_file_name).st_mode | 0o111)    # or, in Bash, "chmod a+x SCRIPT_FILE_NAME"
    
    if file_to_move:
        try:
            if not os.path.exists('old_scripts/'):
                os.mkdir('old_scripts')
            shutil.move(file_to_move, os.path.join(os.getcwd(), 'old_scripts/'))
        except Exception as e:
            print('ERROR: unable to move the old script %s' % file_to_move)
            print('    The system said "%s".' % str(e))
    if file_to_delete:
        try:
            os.remove(file_to_delete)
        except:
            print('ERROR: unable to delete the old script %s' % file_to_delete)


def create_script_from_first_file(first_file, num_files=total_number_of_files, file_to_delete=None):
    """This script creates an enfuse HDR script from the first file on the list and,
    optionally, the number of files that sequentially follow the first file that
    should be input files for the enfuse operation.
    
    To adjust the default number of files to use as inputs to the enfuse operation,
    change the value of the total_number_of_files constant, above.
    
    FILE_TO_DELETE specifies the name of a file (e.g., an old script, for instance)
    to delete if the creation of the new script is successful.
    """
    oldpath = os.getcwd()
    newdir, first_file = os.path.split(first_file)
    if newdir: 
        os.chdir(newdir)
    
    files_in_directory = sorted(glob.glob('*jpg') + glob.glob('*JPG'))
    selected_file_position = files_in_directory.index(first_file)
    HDR_input_files = files_in_directory[selected_file_position : selected_file_position + num_files]
    
    create_script_from_file_list(HDR_input_files, file_to_delete=file_to_delete)
            
    os.chdir(oldpath)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print_usage()
    else:
        print("ERROR: You must specify the first file in the sequence.\n")
        print_usage(exit_value=1)
    
    create_script_from_first_file(sys.argv[1])

