#!/usr/bin/env python3
"""Removes line endings from lines that don't end with sentence-terminating
punctuation. Additionally, it removes leading and trailing spaces from each
line.

Usage:
    
    ./poetry_to_prose.py FILENAME

This script is copyright 2016 by Patrick Mooney. It is licensed under the GPL,
either version 3 or (at your option) any later version. See the file LICENSE.md
for a copy of this license.


"""


debugging = True

import sys, os
import nltk                    # See http://www.nltk.org/install.html

def quick_tokenize(what):
    """Produce an NLTK-tokenized list of tuples: (word, part of speech)."""
    return nltk.pos_tag(nltk.word_tokenize(what))

def starts_proper(what):
    """Return TRUE if NLTK thinks the first word in WHAT is a proper noun."""
    return (quick_tokenize(what)[0][1] == "NNP")

def lower_first(what):
    """Return the string WHAT, as passed in, except that the first character is
    forced to be lowercase.
    """
    if len(what) == 0: return ""
    elif len(what) == 1: return what.lower()
    else: return what[0].lower() + what[1:]

def main(the_filename):

    if debugging: print('\n\nProcessing %s ...' % the_filename)

    with open(the_filename) as the_file:
        the_text = the_file.readlines()
    
    output_file = [][:]
    for which_line in the_text:
        which_line = which_line.strip()
        if len(output_file) == 0:
            output_file.append(which_line + '\n')
        else:
            if len(which_line) == 0:
                output_file.append('\n')
            elif len(output_file[-1].strip()) > 0 and output_file[-1].strip()[-1] in '.!?':
                output_file.append(which_line + ' \n')
            else:
                if not which_line[0].isupper():        # If the line starts with a lowercase letter, just copy it onto the end of prev. line.
                    output_file[-1] = output_file[-1].strip() + ' ' + which_line + '\n'
                elif starts_proper(which_line):        # Ditto for lines that start with proper nouns
                    output_file[-1] = output_file[-1].strip() + ' ' + which_line + '\n'
                else:                                  # Otherwise, lowercase the first letter of the sentence before adding it.
                    output_file[-1] = output_file[-1].strip() + ' ' + lower_first(which_line)

    with open(the_filename, 'w') as the_file:
        the_file.writelines(output_file)

if __name__ == "__main__":
    main(sys.argv[1])
