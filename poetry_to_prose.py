#!/usr/bin/env python3
"""Removes line endings from lines that don't end with sentence-terminating punctuation."""


debugging = True

import sys, os

def main(the_filename):

    if debugging: print('\n\nProcessing %s ...' % the_filename)

    with open(the_filename) as the_file:
        the_text = the_file.readlines()
    
    output_file = [][:]
    for which_line in the_text:
        if len(output_file) == 0:
            output_file.append(which_line.strip() + '\n')
        else:
            if len(which_line.strip()) == 0:
                output_file.append('\n')
            elif len(output_file[-1].strip()) > 0 and output_file[-1].strip()[-1] in '.!?':
                output_file.append(which_line.strip() + '\n')
            else:
                output_file[-1] = output_file[-1].strip() + ' ' + which_line.strip() + '\n'

    with open(the_filename, 'w') as the_file:
        the_file.writelines(output_file)

if __name__ == "__main__":
    main(sys.argv[1])
