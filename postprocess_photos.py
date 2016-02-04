#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

The postprocess-photos.py script performs the kind of postprocessing work that
needs to happen when I move photos to my hard drive. It processes an entire
directory at a time; just invoke it by typing

    postprocess-photos.py

in the directory that needs to be processed.

Currently, it performs the following tasks:
    1. Auto-renames all photos in the current directory, then writes a file,
       renamed.csv, indicating what the original name of each renamed file was.
    2. Auto-rotates all photos in the current directory by calling exiftran.
    3. If any .SH files are found in the directory being processed, it assumes
       they are Bash scripts that call enfuse, possibly preceded by a call to
       align_image_stack (and are the product of automatic exposure bracketing
       by Magic Lantern, which is the only way that .SH files ever wind up on
       my memory cards). It then re-writes them, makes them executable, and
       calls them to create those enfused pictures.

That's it. That's all it does. Current limitations include:
    * It doesn't do anything with non-JPEG images. No PNG, TIFF, BMP, RAW, etc.
    * It only operates on the current working directory.
    * It doesn't process any Magic Lantern scripts other than the enfuse
      scripts.

This program comes with ABSOLUTELY NO WARRANTY. Use at your own risk. It is
free software, and you are welcome to redistribute it under certain conditions,
according to the GNU general public license, either version 3 or (at your own
option) any later version. See the file LICENSE.md for details.
"""

import sys
import subprocess
import os
import glob
import shutil
import csv

import exifread     # https://github.com/ianare/exif-py; sudo pip3 install exifread

rewrite_scripts_for_TIFF_output = False     # I think I'll abandon this normally, but keep the logic in the script in case I change my mind.
file_name_mappings = {}.copy()              # Dictionary that maps original names to new names.

def print_usage():
    "Display a usage message."
    print(__doc__)

def empty_thumbnails():
    "Create an empty .thumbnails directory and make it writable for no one."
    print("Keeping directory's .thumbnails subdirectory empty ... ", end='')
    try:
        if os.path.exists('.thumbnails'):
            if os.path.isdir('.thumbnails'):
                shutil.rmtree('.thumbnails')
            else:
                os.unlink('.thumbnails')
        # OK, now create the directory and make it writable for no one
        os.mkdir('.thumbnails')
        os.chmod('.thumbnails', 0o555)
    except:
        print('\n') # If an error occurs, end the status line that's waiting to be ended before letting the error propagate.
        raise
    print(' ... done.\n\n')

def rename_photos():
    """First, auto-rename files.

    Start by reading the date and time from each image.
    
    Keeps a list as file_list: [dateTime, file_name], then converts it into another
    list, file_name_mappings: [originalName, newName]. 
    """
    print('Renaming photos (based on EXIF data, where possible) ... ', end='')
    try:
        file_list = [].copy()
        for which_image in glob.glob('*jpg') + glob.glob('*JPG'):
            f = open(which_image, 'rb')
            tags = exifread.process_file(f, details=False)    # details=False means don't parse thumbnails or other slow data we don't need.
            try:
                dt = tags['EXIF DateTimeOriginal'].values
            except KeyError:
                try:
                    dt = tags['Image DateTime'].values
                except KeyError:            # Sigh. Not all of my image-generating devices generate EXIF info in all circumstances. Base date on filename.
                    dt = which_image[1 + which_image.find('_'):]    # works for pix from my phone cam: just strip off leading "IMG_"
            datetime_string = '%s-%s-%s_%s_%s_%s.jpg' % (dt[0:4], dt[5:7], dt[8:10], dt[11:13], dt[14:16], dt[17:19])
            file_list.append([datetime_string, which_image])
            f.close()

        # OK, now sort that list (twice). First, sort by original filename (globbing filenames does not preserve this). Then, sort again by datetime string.
        # Since Python sorts are stable, the second sort will preserve the order of the first when values for the sort-by key for the second sort are identical.
        file_list.sort(key=lambda item: item[1])
        file_list.sort(key=lambda item: item[0])

        # Finally, actually rename the files, keeping a dictionary mapping the original to the new names.
        try:
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
                        file_name_mappings[which_file[1]] = the_name
                        which_file = []     # Signal we're done with this item if successful
        finally:
            # write the list to disk
            with open('file_names.csv', 'w') as file_names:
                file_names.write('original name, new name\n')
                file_names.writelines(['%s,%s\n' % (original_name, file_name_mappings[original_name]) for original_name in file_name_mappings])
    except:
        print('\n') # If an error occurs, end the status line that's waiting to be ended before letting the error propagate.
        raise
    print(' ... done.\n\n')

def read_filename_mappings():
    """Read file_names.csv back into memory. Do this before restoring original
    file names"""
    global file_name_mappings
    with open('file_names.csv') as infile:
        reader = csv.reader(infile)
        file_name_mappings = {rows[0]:rows[1] for rows in reader}

def restore_file_names():
    """Restore original file names, based on the file_names.csv file, which is
    assumed to be comprehensive and intact"""
    for original_name in file_name_mappings:
        if os.path.exists(file_name_mappings[original_name]):
            print('Renaming "%s" to "%s".' % (file_name_mappings[original_name], original_name))
            os.rename(file_name_mappings[original_name], original_name)

def rotate_photos():
    """Auto-rotate all photos using exiftran."""
    print('Auto-rotating images ...\n\n')
    subprocess.call('exiftran -aigp *jpg *JPG', shell=True)

def process_shell_scripts():
    """Next, process any shell scripts created by MagicLantern.

    Currently, we only process HDR_????.SH scripts, which call enfuse. They MAY 
    (well ... should) call align_image_stack first, but that depends on whether I
    remembered to choose 'align + enfuse" in Magic Lantern. Currently, up to two
    changes are made: old file names are replaced with their new file name
    equivalents, and (optionally) output is made TIFF instead of JPEG. This part of
    the script is currently heavily dependent on the structure of these Magic
    Lantern scripts (currently, they're produced by firmware version1.0.2-ml-v2.3).
    """

    print('\nRewriting enfuse HDR scripts ... ', end='')
    try:
        for which_script in glob.glob('HDR*SH'):
            old_perms = os.stat(which_script).st_mode
            with open(which_script, 'r') as the_script:
                script_lines = the_script.readlines()
                if script_lines[4].startswith('align_image_stack'):         # It's an align-first script, with 8 lines, 5 non-blank.
                    new_script = script_lines[0:4]                          # preserve the original opening
                    align_line_tokens = script_lines[4].split()
                    align_line = ' '.join(align_line_tokens[:4]) + ' '
                    align_line = align_line + ' '.join([file_name_mappings[which_file] if which_file in
                                                        file_name_mappings else which_file for which_file in
                                                        align_line_tokens[4:]]) + '\n'
                    new_script.append(align_line)
                    enfuse_line = script_lines[5]
                    output_position = enfuse_line.find('--output')          # find the location in the line of the --output parameter
                    output_extension_position = enfuse_line.find('.JPG', output_position)
                    enfuse_line = enfuse_line[:output_extension_position] + '.TIFF' + enfuse_line[output_extension_position + 4:] + '\n'
                    new_script.append(enfuse_line)
                    # OK, now convert the resulting TIFF to HQ JPEG and copy in EXIF metadata
                    HDR_filename = enfuse_line[output_position + len('--output='):][:8]
                    new_script.append('convert %s.TIFF -quality 95 %s.JPG\n' % (HDR_filename, HDR_filename))
                    new_script.append('rm %s.TIFF\n' % HDR_filename)
                    new_script.append('exiftool -tagsfromfile %s %s.JPG\n' % (file_name_mappings[align_line_tokens[4]], HDR_filename))
                    new_script.append('rm %s.JPG_original\n' % HDR_filename)
                    # write the end of the old script onto the end of the new one
                    for the_line in script_lines[6:]: new_script.append(the_line)
                else:                                                       # It's a just-call-enfuse script, with 6 lines, 3 non-blank.
                    new_script = script_lines[:-1]                          # preserve the opening of the script as-is; we're only altering the last line.
                    last_line_tokens = script_lines[-1].split()             # FIXME: incorporate logic from branch above here to produce better final output.
                    last_line = ' '.join(last_line_tokens[:3]) + ' '
                    last_line = last_line + ' '.join([file_name_mappings[which_file] for which_file in last_line_tokens[3:]]) + '\n'
                    if rewrite_scripts_for_TIFF_output:     # TODO: merge this logic with the new TIFF-to-JPEG-and-copy-EXIF logic above
                        output_position = last_line.find('--output')            # find the location in the line of the --output parameter
                        output_extension_position = last_line.find('.JPG', output_position)     # Find the first occurrence of '.JPG' after '--output'
                        last_line = last_line[:output_extension_position] + '.TIFF ' + last_line[output_extension_position + 4:]
                    new_script.append(last_line)
            # Here, write a line that copies EXIF info from the non-shifted image into the HDR, plus a line that removes the _original file.
            with open(which_script, 'w') as the_script:
                the_script.writelines(new_script)
            os.chmod(which_script, old_perms | 0o111)           # Make the script executable
    except:
        print() # If an error occurs, end the line that's waiting to be ended before letting the error propagate.
        raise
    print(' ... done.')

def run_shell_scripts():
    """Run the shell scripts."""
    print("\nRunning enfuse scripts ...\n\n")
    for which_script in glob.glob('HDR*SH'):
        print('\n\nRunning script: %s' % which_script)
        subprocess.call('./' + which_script)
    print("\n\n ... done.")

# OK, let's go
if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_usage()
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            sys.exit(0)
        else:               # There should be no command-line arguments other than --help or -h
            sys.exit(1)

    if input('Do you want to postprocess the directory %s?  ' % os.getcwd())[0].lower() != 'y':
        print('\n\nREMEMBER: this script only works on the current working directory.\n')
        sys.exit(1)

    empty_thumbnails()
    rename_photos()
    rotate_photos()
    process_shell_scripts()
    run_shell_scripts()

# We're done!
