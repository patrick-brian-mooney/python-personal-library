#!/usr/bin/env python3
"""The postprocess-photos.py script performs the kind of postprocessing work that
needs to happen when I move photos to my hard drive. It processes an entire
directory at a time; just invoke it by typing

    postprocess-photos.py

in the directory that needs to be processed.

Currently, it performs the following tasks:
    1. Auto-rotates all photos in the current directory by calling exiftran.
    2. If any .SH files are found in the directory being processed, it assumes
       they are Bash scripts that call enfuse (and are the product of automatic
       exposure bracketing by Magic Lantern, which is the only way that .SH
       files ever wind up on my memory cards). It then re-writes them, makes
       them executable, and calls them to create those enfused pictures.
    3. Auto-renames all photos in the current directory.

That's it. That's all it does. Current limitations include:
    * It doesn't do anything with non-JPEG images. No PNG, TIFF, BMP, RAW, etc.
    * It only operates on the current working directory.
    * It doesn't process any Magic Lantern scripts other than the enfuse
      scripts.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk. It is
free software, and you are welcome to redistribute it under certain conditions,
according to the GNU general public license, either version 3 or (at your own
option) any later version. See the file LICENSE.md for details." 
"""

import sys
import subprocess
import os
import glob
import shutil

import exifread     # https://github.com/ianare/exif-py; sudo pip3 install exifread

def print_usage():
    print(__doc__)

if len(sys.argv) > 1:
    if sys.argv[1] == '--help' or sys.argv[1] == '-h':
        print_usage()
        sys.exit(0)
    else:               # There should be no command-line arguments other than --help or -h
        print_usage()
        sys.exit(1)

if input('Do you want to postprocess the directory %s?  ' % os.getcwd())[0].lower() != 'y':
    print('\n\nREMEMBER: this script only works on the current working directory.\n')
    sys.exit(1)

# OK, let's go
print("Keeping directory's .thumbnails subdirectory empty ... ", end='')
if os.path.exists('.thumbnails'):
    if os.path.isdir('.thumbnails'):
        shutil.rmtree('.thumbnails')
    else:
        os.unlink('.thumbnails')
# OK, now create the directory and make it writable for no one
os.mkdir('.thumbnails')
os.chmod('.thumbnails', 0o555)
print(' ... done.\n\n')

print('Auto-rotating images ...\n\n')
subprocess.call('exiftran -aigp *jpg *JPG', shell=True)

# Next, process any shell scripts created by MagicLantern

# Currently, we only process HDR_????.SH scripts, which call enfuse.
print('\nRewriting enfuse HDR scripts ... ', end='')
try:
    for which_script in glob.glob('HDR*SH'):
        old_perms = os.stat(which_script).st_mode
        with open(which_script, 'r') as the_script:
            script_lines = the_script.readlines()
            new_script = script_lines[:-1]                  # preserve the opening of the script as-is; we're only altering the last line.
            last_line = script_lines[-1]
            output_position = last_line.find('--output')    # find the location in the line of the --output parameter
            output_extension_position = last_line.find('.JPG', output_position)     # Find the first occurrence of '.JPG' after '--output'
            # Do we want to do any other processing here?
            new_script.append(last_line[:output_extension_position] + '.TIFF ' + last_line[output_extension_position + 4:])
        with open(which_script, 'w') as the_script:
            the_script.writelines(new_script)
        os.chmod(which_script, old_perms | 0o111)           # Make the script executable
except:
    print() # If an error occurs, end the line that's waiting to be ended before letting the error propagate.
    raise
print(' ... done.')

print("\nRunning the scripts we've written...\n\n")
for which_script in glob.glob('HDR*SH'):
    subprocess.call('./' + which_script) 
print("\n\n ... done.")

# Now, auto-rename files.
# First, read the date and time from each image. Keep a list: [dateTime, file_name].
file_list = [].copy()
for which_image in glob.glob('*jpg') + glob.glob('*JPG'):
    f = open(which_image, 'rb')
    tags = exifread.process_file(f, details=False)    # Don't parse thumbnails, etc.
    try:
        dt = tags['EXIF DateTimeOriginal'].values
    except KeyError:
        try:
            dt = tags['Image DateTime'].values
        except KeyError:            # Sigh. Not all of my image-generating devices generate EXIF info in all circumstances. Assume we can extract from filename.
            dt = which_image[1 + which_image.find('_'):]    # works for pix from my phone cam: just strip off leading "IMG_"
    datetime_string = '%s-%s-%s_%s_%s_%s.jpg' % (dt[0:4], dt[5:7], dt[8:10], dt[11:13], dt[14:16], dt[17:19])
    file_list.append([datetime_string, which_image])
    f.close()

# OK, now sort that list (twice). First, sort by original filename (glob does not preserve this). Then, sort again by datetime string.
# Since Python sorts are stable, the second sort will preserve the order of the first when the key for the second sort is identical.
file_list.sort(key=lambda item: item[1])
file_list.sort(key=lambda item: item[0])

# Finally, actually rename the files.
while len(file_list) > 0:
    which_file = file_list.pop(0)
    fname, f_ext = os.path.splitext(which_file[0])
    index = 0
    while which_file != []:
        if index > 0:
            the_name = '%s_%d%s' % (fname, index, f_ext)
        else:
            the_name = which_file[0]
        if os.path.exists(the_name):
            index += 1          # Bump the counter and try again
        else:
            os.rename(which_file[1], the_name)
            which_file = []     # Signal we're done with this item if successful

# We're done!
