#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_capitalization.py, by Patrick Mooney

This is a script to find capitalized words in the middle of sentences that
are not proper nouns (or approved other capitalized words). It also makes some
attempt to detect other capitalization problems. It goes through a text,
sentence by sentence, asking the user whether they should be capitalized. If
not, it converts them to lowercase. When it has finished, it writes the
modified text back to the same file, i.e. it modifies the input file in-place.
It is primarily intended to check the output of my poetry_to_prose.py script
and was originally developed in order to facilitate the processing of a
complete edition of Shakespeare for my automated text blog Ulysses Redux.

Usage:

    check_capitalization.py [options] -i FILE

Options:

  -l WORDLIST, --list WORDLIST
      Specify an additional list of words that are allowed to be capitalized
      without asking. If changes are made, check_capitalization.py will offer
      to overwrite the original file. Don't edit this file during a run of the
      program; if you do, your changes will be overwritten.

  -i FILE, --input FILE
      Specify the file to check. You may only process one file at a time with
      this script. If you do not specify a file, the script will ask you which
      file you want it to process.

  -h, --help
      Print this help message, then quit.

  -v, --verbose
      Increase the verbosity of the script, i.e. get more output. Can be
      specified multiple times to make the script more and more verbose.

  -q, --quiet
      Decrease the verbosity of the script. You can mix -v and -q, bumping the
      verbosity level up and down as the command line is processed, but really,
      what are you doing with your life?

This script requires that NLTK be installed, because it relies on NLTK for a
lot of the work it does. See http://www.nltk.org/.

The most recent version of this script is available at:


This program is licensed under the GPL v3 or, at your option, any later
version. See the file LICENSE.md for a copy of this licence.
"""


import sys, os, string, getopt, pprint
from collections import OrderedDict

import nltk

import text_handling, patrick_logger, multi_choice_menu, simple_standard_file   # https://github.com/patrick-brian-mooney/python-personal-library/


always_capitalize_sentence_beginnings = True    # Usually, it's helpful to set this to True if NLTK is doing a good job of finding the beginnings of sentences.
patrick_logger.verbosity_level = 1
always_capitalize_list_filename = '/python-library/always_capitalize_list'  # Or leave empty not to use a global list.
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')


filename = ''                                                   # Fill this in with a filename to validate that file
always_capitalize_list, original_always_capitalize_list = [][:], [][:]
the_lines = [][:]


allowed_capitalized_words = ( "i", "i'll",      # these need to be represented in lowercase so the comparison works!
                              "i’ll", "i'd", "i’d", "i'm", "i’m", "i've", "i’ve" )
punc = ''.join(list(set(string.punctuation) - set(["'"]) | set(['—'])))



def puncstrip(w):
    return w.strip(punc)


def comparative_form(w):
    """A quick convenience function to just return a standardized form of a word for
    the purpose of comparing words for equality. It's lowercase, strips out leading
    and trailing punctuation, and strips out some (but not necessarily all)
    whitespace.
    """
    return puncstrip(puncstrip(w.strip()).strip()).lower()
    # That is to say: strip whitespace from both ends, then strip leading and
    # trailing elements of string.punctuation except for the apostrophe, plus
    # additional other stuff, then strip whitespace from both ends again, then
    # strip the same set of punctuation, then lowercase the result.


def reassemble_sentence(sentence_list):
    """Given a tagged sentence -- a list of tuples of the form
    [(word, POS), (word, POS) ... ] -- reassemble it into a string much like the
    original sentence (though possibly with spacing altered).
    """
    ret = ''
    for w, _ in sentence_list:
        ret = "%s%s" % (ret, w) if w in punc else "%s %s" % (ret, w)      # Add space, except before punctuation
    return ret


def save_files(the_lines, the_filename, the_always_capitalize_list, the_always_capitalize_list_filename):
    """Give the user the option to save the modified-in-place verified text (stored
    in global variable THE_LINES), plus, if modified, the list of words to always
    skip.

    Parameters:
          the_lines                             List of lines to be written back to the original file.
          the_filename                          Path/name of the original file to be overwritten.
          the_always_capitalize_list            List of words always to capitalize.
          the_always_capitalize_list_filename   Location of always-capitalize list.


    Returns a tuple:
        ( the [possibly modified] THE_ALWAYS_CAPITALIZE_LIST,
          the [possibly modified] THE_ALWAYS_CAPITALIZE_LIST_FILENAME,
        )
    """
    global original_always_capitalize_list

    the_menu = OrderedDict([                                    # Use this same menu for both questions
                            ('Y', "Overwrite the old data"),
                            ('N', 'Cancel and lose the changes')
                            ])
    choice = comparative_form(multi_choice_menu.menu_choice(the_menu, 'Overwrite file "%s" with modified text?' % os.path.split(filename)[1]))
    if choice == 'y':
        with open(the_filename, 'w') as f:
            f.writelines(the_lines)

    the_always_capitalize_list.sort()
    if the_always_capitalize_list != original_always_capitalize_list:
        print('\n\n')
        choice = comparative_form(multi_choice_menu.menu_choice(the_menu, 'List of always-capitalize words "%s" modified. Save new list?' %
                                                                os.path.split(the_always_capitalize_list_filename)[1]))
        if choice == 'y':
            the_always_capitalize_list_filename = the_always_capitalize_list_filename or sfp.do_open_dialog()
            with open(the_always_capitalize_list_filename, 'w') as f:
                f.writelines(sorted(list(set([ comparative_form(line) + '\n' for line in the_always_capitalize_list ]))))

    return the_always_capitalize_list, the_always_capitalize_list_filename


def check_word_capitalization(tagged_sentence, word_number, allow_always_correct=False):
    """Give the user a choice of whether to correct the capitalization of the
    word or not to correct the capitalization of the word.

    Returns True if the capitalization NEEDS TO BE ALTERED; False if capitalization IS ALREADY CORRECT.
    This routine modifies the global list always_capitalize_list.
    """
    global the_lines, filename, always_capitalize_list, always_capitalize_list_filename     # In case we abort and save.

    the_word = tagged_sentence[word_number][0]
    if comparative_form(the_word) in always_capitalize_list:
        return True
    else:
        # First, reassemble the sentence, except capitalize the entire word whose capitalization is in question
        context_sentence = ''
        count = 0
        for w, _ in tagged_sentence:
            if count == word_number:
                w = w.upper()
            count += 1
            context_sentence = "%s%s" % (context_sentence, w) if w in punc else "%s %s" % (context_sentence, w)

        print()
        verb = "is" if the_word[0].isupper() else "is not"
        question = 'POSSIBLE ERROR DETECTED: the word "%s" %s capitalized. Is this wrong?' % (puncstrip(the_word), verb)
        text_handling.print_indented(question, 2)
        print()
        text_handling.print_indented('CONTEXT: %s\n' % context_sentence, 2)

        the_menu = OrderedDict([])
        the_menu['Y'] = ("Decapitalize" if the_word[0].isupper() else "Capitalize") + " this word"
        the_menu['N'] = 'Leave this word as-is'
        if allow_always_correct:
            the_menu['A'] = "Always capitalize this word"
        the_menu['Q'] = 'Quit, with option to save changes'

        choice = comparative_form(multi_choice_menu.menu_choice(the_menu, "What would you like to do?"))
        if choice == 'a':
            always_capitalize_list += [ comparative_form(the_word) ]
            choice = "n" if the_word[0].isupper() else "y"
        elif choice == 'q':
            save_files(the_lines, filename, always_capitalize_list, always_capitalize_list_filename)
            print('\nQuitting ...')
            sys.exit(0)

        ret = choice.lower() == 'y'
        return ret


def correct_sentence_capitalization(s):
    """Return a corrected version of the sentence that was passed in.
    This is where the real work actually happens.
    """
    count = 0
    tagged_sent = nltk.tag.pos_tag(s.split())   # This is now a list of tuples: [(word, POS), (word, POS) ...]
    for word, pos in tagged_sent:               # POS = "part of speech." Go through the list of tuples, word by word
        count += 1                              # In English language counting order, which word in the sentence is this?

        # OK, let's check for various capitalization problems.
        # First: check for problems that are independent of whether they occur in the first word of a sentence.
        if comparative_form(word) in always_capitalize_list and not word[0].isupper():
            # Check: uncapitalized word we know should always be capitalized?
            patrick_logger.log_it('DEBUGGING: found non-capitalized word "%s" on the always-capitalize list' % comparative_form(word), 2)
            tagged_sent[count-1] = (text_handling.capitalize(tagged_sent[count-1][0]), pos)

        # Next, check for problems related to the first word of a sentence.
        if count == 1:                                  # Beginning of sentence has special handling.
            if not word[0].isupper():                   # Check: should first word of sentence be capitalized?
                patrick_logger.log_it('DEBUGGING: found non-capitalized word "%s" at the beginning of a sentence' % comparative_form(word), 2)
                if always_capitalize_sentence_beginnings or check_word_capitalization(tagged_sent, count-1):
                    # If we capitalize it, set the indicated item in the list of tuples to a tuple that capitalizes the word
                    # in question and maintains the POS tagging for further checking. The rather ugly expression below is of
                    # course necessary because tuples are immutable.
                    tagged_sent[count-1] = (text_handling.capitalize(tagged_sent[count-1][0]), pos)

        # Now, check for problems that can happen only outside the first word of a sentence.
        else:                                           # Checks for words other than the first word of the sentence
            # First: is there an unexplained capitalized word beyond the first word of the sentence?
            if word[0].isupper() and (pos.upper() not in [ 'NNP' ]) and (comparative_form(word) not in allowed_capitalized_words):
                patrick_logger.log_it('DEBUGGING: the word "%s" may be inappropriately capitalized' % comparative_form(word), 2)
                # Capitalized, but not a proper noun?
                if check_word_capitalization(tagged_sent, count-1, allow_always_correct=True):
                    tagged_sent[count-1] = (tagged_sent[count-1][0].lower(), pos)

    return reassemble_sentence(tagged_sent).strip()


def print_usage(exit_code=0):
    print("\n\n" + __doc__)
    sys.exit(exit_code)


def process_command_line():
    """Read the command-line options. Set global variables appropriately.

    Returns a tuple: (filename of opened file, filename of always-capitalize list).
    Either or both may be None if the command line does not contain these options;
    they can be hardcoded above, below the docstring.
    """
    the_filename, the_always_capitalize_list_filename = None, None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'l:i:h', ['help', 'input='])
        patrick_logger.log_it('INFO: options returned from getopt.getopt() are: %s' % pprint.pformat(opts), 2)
    except getopt.GetoptError:
        patrick_logger.log_it('ERROR: Bad command-line arguments; exiting to shell', 0)
        print_usage(2)
    patrick_logger.log_it('INFO: detected number of command-line arguments is %d' % len(sys.argv), 2)
    for opt, args in opts:
        patrick_logger.log_it('Processing option %s' % opt, 2)
        if opt in ('-h', '--help'):
            patrick_logger.log_it('INFO: %s invoked, printing usage message' % opt)
            print_usage()
        elif opt in ('-i', '--input'):
            patrick_logger.log_it('INFO: %s invoked; file "%s" will be processed' % (opt, args))
            the_filename = args
        elif opt in ('-v', '--verbose'):
            patrick_logger.verbosity_level += 1
            patrick_logger.log_it('INFO: %s invoked. Raising verbosity level to %d.' % (opt, patrick_logger.verbosity_level))
        elif opt in ('-q', '--quiet'):
            patrick_logger.log_it('INFO: %s invoked. Decreasing verbosity level to %d' % (opt, patrick_logger.verbosity_level-1))
            patrick_logger.verbosity_level -= 1
        elif opt in ('-l', '--list'):
            patrick_logger.log_it('INFO: %s invoked; always-capitalize file "%s" will be used' % (opt, args))
            the_always_capitalize_list_filename = args
        else:
            patrick_logger.log_it('ERROR: unimplemented switch %s used. Exiting ...' % opt, -1)
            sys.exit(3)

    patrick_logger.log_it('INFO: Done parsing command line. patrick_logger.verbosity_level after parsing command line is  %d.' % patrick_logger.verbosity_level, 1)
    return the_filename, the_always_capitalize_list_filename


def process_file(filename):
    """Loads the specified file and verifies it, producing a list of verified lines.
    It returns this list, which is a list of lines that SHOULD BE written back to
    disk.

    This routine DOES NOT SAVE the file back to disk; save_files() does that.
    """
    print("Opening: %s ..." % os.path.split(filename)[1], end=" ")

    with open(filename, 'r') as f:
        the_lines = f.readlines()

    print("successfully read %d lines. Processing..." % len(the_lines))

    for (count, which_line) in zip(range(len(the_lines)), the_lines):   # Go through the text, paragraph by paragraph.
        if patrick_logger.verbosity_level > 0:
            patrick_logger.log_it("\nProcessing line %d" % (count + 1), 1)
            patrick_logger.log_it('THE ORIGINAL LINE IS:\t%s' % which_line, 1)
            patrick_logger.log_it('', 1)

        which_line = which_line.strip()                                 # Note that this is one source of changes of some lines from one valid form to another
        sentences = [].copy()                                           # Build a list of corrected sentences to re-assemble when done.
        for sentence in tokenizer.tokenize(which_line):                 # Go through the paragraph, sentence by sentence.
            sentence = correct_sentence_capitalization(sentence)
            sentences += [ sentence ]                                   # Add corrected sentence to the list of sentences in this paragraph
        corrected_line = ' '.join(sentences) + '\n'                     # Note that we're not (necessarily) preserving original spacing here.

        patrick_logger.log_it('\nTHE CORRECTED LINE IS:\t%s' % corrected_line)

        the_lines[count] = corrected_line

    return the_lines



if __name__ == "__main__":
    opts = process_command_line()
    filename, always_capitalize_list_filename = filename or opts[0], always_capitalize_list_filename or opts[1]

    try:
        if always_capitalize_list_filename:     # If an auto-capitalize list was specified, load it
            with open(always_capitalize_list_filename, 'r') as skipfile:
                always_capitalize_list = sorted(list(set([ comparative_form(line) for line in skipfile.readlines() ])))
    except:
        patrick_logger.log_it("WARNING: unable to open always-capitalize file %s" % always_capitalize_list_filename, 0)
        patrick_logger.log_it("    ... proceeding with empty list", 0)

    original_always_capitalize_list = always_capitalize_list.copy()     # Make a shallow copy of whatever we start with.

    filename = filename or simple_standard_file.do_open_dialog()

    the_lines = process_file(filename)

    print('\n\n\nEntire file processed.')

    always_capitalize_list, always_capitalize_list_filename = save_files(the_lines,filename, always_capitalize_list, always_capitalize_list_filename)

    print("All done!\n\n")
