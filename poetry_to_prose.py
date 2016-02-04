#!/usr/bin/env python3
"""A quick hack: it takes the file and removes line breaks that don't match up with
sentence-ending punctuation. Usage:

    ./poetry_to_prose.py FILENAME
"""

debugging = False

import sys, os

if __name__ == "__main__":
    the_filename = sys.argv[1]
    with open(the_filename) as the_file:
        the_text = the_file.readlines()
    
    which_line = 0
    while which_line < len(the_text):
        if debugging: print("DEBUG: We're on line number %d; total length of text is now %d" % (which_line, len(the_text)))
        if the_text[which_line].strip() != '':
            while the_text[which_line].strip()[-1] not in '.!?':
                next_line = the_text.pop(which_line + 1)
                try:
                    the_text[which_line] = "%s %s" % (the_text[which_line].strip(), next_line)
                except IndexError:
                    pass    # If we've reached this point and there is no next line, we have a badly formed line ending by conventional standards, but oh well. 
        which_line += 1

    with open(the_filename, 'w') as the_file:
        the_file.writelines(the_text)
