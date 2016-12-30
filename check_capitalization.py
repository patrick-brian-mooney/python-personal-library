#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_capitalization.py, by Patrick Mooney; 9 December 2016

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

    ./check_capitalization.py [options] -i FILE

Options:

  -i FILE, --input FILE
      Specify the file to check. You may only process one file at a time with
      this script. If you do not specify a file, the script will ask you which
      file you want it to process.

  -l WORDLIST, --list WORDLIST
      Specify an additional list of words that are allowed to be capitalized
      without asking. If you add words to the list during a run of
      check_capitalization.py, the program will offer to overwrite the original
      file. This file is a simple text file containing one lowercase word per
      line. Don't edit this file during a run of the program; if you do, your
      changes will be overwritten when check_capitalization.py ends.

  -v, --verbose
      Increase the verbosity of the script, i.e. get more output. Can be
      specified multiple times to make the script more and more verbose.

  -q, --quiet
      Decrease the verbosity of the script. You can mix -v and -q, bumping the
      verbosity level up and down as the command line is processed, but really,
      what are you doing with your life?

  -h, --help
      Print this help message, then quit.

This script requires that NLTK be installed, because it relies on NLTK for a
lot of the work it does. See http://www.nltk.org/.

The most recent version of this script is available at:
https://github.com/patrick-brian-mooney/python-personal-library/blob/master/check_capitalization.py

This program is copyright 2016 by Patrick Mooney; it is licensed under the
GPL v3 or, at your option, any later version. See the file LICENSE.md for a
copy of this licence.
"""


import sys, os, string, getopt, pprint
from collections import OrderedDict

import nltk

import patrick_logger, multi_choice_menu                        # https://github.com/patrick-brian-mooney/python-personal-library/
import text_handling as th                                      # Same source.
import simple_standard_file as sfp                              # Once again: same source.


always_capitalize_sentence_beginnings = True    # Usually, it's helpful to set this to True if NLTK is doing a good job of finding the beginnings of sentences.
patrick_logger.verbosity_level = 1


always_capitalize_list_filename = '/python-library/always_capitalize_list'  # Or leave empty not to use a global list.
apostrophe_words_filename = '/python-library/apostrophe_words'              # File listing words allowed to begin with an apostrophe
filename = ''       # Fill this in with a filename to validate that file


the_lines = [][:]
always_capitalize_list, original_always_capitalize_list = [][:], [][:]
apostrophe_words, original_apostrophe_words = [][:], [][:]


allowed_capitalized_words = ("i", "i'll",       # additional words that are allowed to be capitalized mid-sentence.
                             "i’ll", "i'd",     # these need to be represented in lowercase so the comparison works!
                             "i’d", "i'm", "i’m", "i've", "i’ve")
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
punc = ''.join(list(set(string.punctuation) - {"'"} | {'—‘“”'}))


def puncstrip(w):
    return w.rstrip("'").strip(punc)    # Only strip straight quotes off the end: at the beginning, they might be apostrophes.


def comparative_form(w):
    """A quick convenience function to just return a standardized form of a word for
    the purpose of comparing words for equality. It's lowercase, strips out (most)
    leading and trailing punctuation, and strips out some (but not necessarily all)
    whitespace.

    :param w: the word to take the comparative form of
    :return: the comparative form of the word
    """
    ret = puncstrip(puncstrip(w.strip()).strip()).lower()
    if th.begins_with_apostrophe(ret):      # Next, normalize the apostrophe form.
        if ret not in apostrophe_words:     # If it's not allowed to begin with an apostrophe, return it without the apostrophe, on the assumption that that apostrophe is really an opening quote mark.
            if len(ret) > 1:                # Avoid degenerate cases, e.g. where W *is* an apostrophe
                ret = ret[1:]
            else:
                ret = "’"
        else:
            ret = "’" + ret[1:]             # Correct the apostrophe to an unambiguous form.
    return ret
    # That is to say: strip whitespace from both ends, then strip leading and
    # trailing elements of string.punctuation except for the apostrophe, plus
    # additional other stuff, then strip whitespace from both ends again, then
    # strip the same set of punctuation, then lowercase the result. Additionally,
    # if the word begins with an apostrophe but doesn't appear in the global list
    # APOSTROPHE_WORDS, then strip the leading apostrophe.


def reassemble_sentence(sentence_list):
    """Given a tagged sentence -- a list of tuples of the form
    [(word, POS), (word, POS) ... ] -- reassemble it into a string much like the
    original sentence (though possibly with spacing altered).

    :param sentence_list: the list of tuples to be reassembled.
    """
    ret = ''
    for w, _ in sentence_list:
        ret = "%s%s" % (ret, w) if w in punc else "%s %s" % (ret, w)      # Add space, except before punctuation
    return ret


def check_word_capitalization(tagged_sentence, word_number, allow_always_correct=False):
    """Give the user a choice of whether to correct the capitalization of the
    word or not to correct the capitalization of the word.

    Returns True if the capitalization NEEDS TO BE ALTERED; False if capitalization IS ALREADY CORRECT.
    This routine modifies the global list always_capitalize_list.
    :param tagged_sentence: the NLTK-tagged-with-POS sentence to be reassembled, a list of tuples.
    :param word_number: which word in the sentence is to have its capitalization checked.
    :param allow_always_correct: True if the user is to be given the option to always capitalize this word.
    """
    global the_lines, filename, always_capitalize_list, always_capitalize_list_filename     # In case we abort and save.
    global apostrophe_words, apostrophe_words_filename                                      # Same reason.

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
        verb = "is" if th.is_capitalized(the_word) else "is not"
        question = 'POSSIBLE ERROR DETECTED: the word "%s" %s capitalized. Is this wrong?' % (comparative_form(the_word), verb)
        th.print_indented(question, 2)
        print()
        th.print_indented('CONTEXT: %s\n' % context_sentence, 2)

        the_menu = OrderedDict([])
        the_menu['Y'] = ("Decapitalize" if th.is_capitalized(the_word) else "Capitalize") + " this word"
        the_menu['N'] = 'Leave this word as-is'
        if allow_always_correct:
            the_menu['A'] = "Always capitalize this word"
        if th.begins_with_apostrophe(the_word) and comparative_form(the_word).strip("’'") not in apostrophe_words:
            the_menu['D'] = "Allow this word to begin with an apostrophe"
        if the_word.strip().startswith("'") and comparative_form(the_word).strip("’'") not in apostrophe_words:
            the_menu['C'] = "Correct initial apostrophe ( ' ) to opening quote ( ‘ )"
        the_menu['Q'] = 'Quit, with option to save training data (but not modified text)'

        choice = comparative_form(multi_choice_menu.menu_choice(the_menu, "What would you like to do?"))
        if choice == 'a':
            always_capitalize_list += [comparative_form(the_word)]
            choice = "n" if th.is_capitalized(the_word) else "y"
        elif choice == 'q':                         # FIXME: we should really be able to save the modified source text.
            save_files(allow_saving_text=False)     # The text file hasn't been fully reassembled yes, so we can't save it!
            print('\nQuitting ...')
            sys.exit(0)
        elif choice == "d":
            apostrophe_words += [the_word[0] + comparative_form(the_word).strip("’'") ]             # Add the word to the list ...
            return check_word_capitalization(tagged_sentence, word_number, allow_always_correct)    # And check again.
        elif choice == "c":
            tagged_sentence[word_number] = ("‘" + the_word.strip().lstrip("'"), tagged_sentence[word_number][1])
            return check_word_capitalization(tagged_sentence, word_number, allow_always_correct)    # And check again.
        ret = choice.lower() == 'y'
        return ret


def correct_sentence_capitalization(s):
    """Return a corrected version of the sentence that was passed in.
    This is where the real work actually happens.

    :param s: a string: the sentence to be examined.
    """
    count = 0
    tagged_sent = nltk.tag.pos_tag(s.split())   # This is now a list of tuples: [(word, POS), (word, POS) ...]
    for word, pos in tagged_sent:               # POS = "part of speech." Go through the list of tuples, word by word
        count += 1                              # In English language counting order, which word in the sentence is this?

        # OK, let's check for various capitalization problems.
        # First: check for problems that are independent of whether they occur in the first word of a sentence.
        if comparative_form(word) in always_capitalize_list and not th.is_capitalized(word):
            # Check: uncapitalized word we know should always be capitalized?
            patrick_logger.log_it('DEBUGGING: found non-capitalized word "%s" on the always-capitalize list' % comparative_form(word), 2)
            tagged_sent[count-1] = (th.capitalize(tagged_sent[count-1][0]), pos)

        # Next, check for problems related to the first word of a sentence.
        if count == 1:                                  # Beginning of sentence has special handling.
            if not th.is_capitalized(word):                   # Check: should first word of sentence be capitalized?
                patrick_logger.log_it('DEBUGGING: found non-capitalized word "%s" at the beginning of a sentence' % comparative_form(word), 2)
                if always_capitalize_sentence_beginnings or check_word_capitalization(tagged_sent, count-1):
                    # If we capitalize it, set the indicated item in the list of tuples to a tuple that capitalizes the word
                    # in question and maintains the POS tagging for further checking. The rather ugly expression below is of
                    # course necessary because tuples are immutable.
                    tagged_sent[count-1] = (th.capitalize(tagged_sent[count-1][0]), pos)

        # Now, check for problems that can happen only outside the first word of a sentence.
        else:                                           # Checks for words other than the first word of the sentence
            # First: is there an unexplained capitalized word beyond the first word of the sentence?
            if th.is_capitalized(word) and (pos.upper() not in ['NNP']) and (comparative_form(word) not in allowed_capitalized_words):
                patrick_logger.log_it('DEBUGGING: the word "%s" may be inappropriately capitalized' %
                                       comparative_form(word), 2)
                # Capitalized, but not a proper noun?
                if check_word_capitalization(tagged_sent, count-1, allow_always_correct=True):
                    tagged_sent[count-1] = (tagged_sent[count-1][0].lower(), pos)

    return reassemble_sentence(tagged_sent).strip()


def save_files(allow_saving_text=True):
    """Give the user the option (possibly) to save the modified-in-place verified text (stored
    in global variable THE_LINES), plus, if modified, the list of words to always
    skip.

    :param allow_saving_text:


    Deals with these global variables:
        the_lines                             List of lines to be written back to the original file.
        filename                              Path/name of the original file to be overwritten.
        always_capitalize_list                List of words always to capitalize.
        always_capitalize_list_filename       Location of always-capitalize list.
        apostrophe_words                      List of words allowed to begin with an apostrophe
        apostrophe_words_filename             Location of file listing words allowed to begin with an apostrophe

    """
    global always_capitalize_list, always_capitalize_list_filename, apostrophe_words_filename

    the_menu = OrderedDict([                                    # Use this same menu for both questions
                            ('Y', "Overwrite the old data"),
                            ('N', 'Cancel and lose the changes')
                            ])

    if allow_saving_text:
        choice = comparative_form(multi_choice_menu.menu_choice(the_menu, 'Overwrite file "%s" with modified text?' % os.path.split(filename)[1]))
        if choice == 'y':
            with open(filename, 'w') as f:
                f.writelines(the_lines)

    always_capitalize_list.sort()
    if always_capitalize_list != original_always_capitalize_list:
        print('\n\n')
        choice = comparative_form(multi_choice_menu.menu_choice(the_menu, 'List of always-capitalize words "%s" modified. Save new list?' %
                                                                os.path.split(always_capitalize_list_filename)[1]))
        if choice == 'y':
            always_capitalize_list_filename = always_capitalize_list_filename or sfp.do_open_dialog()
            with open(always_capitalize_list_filename, 'w') as f:
                f.writelines(sorted(list(set([comparative_form(line) + '\n' for line in always_capitalize_list]))))

    apostrophe_words.sort()
    if apostrophe_words != original_apostrophe_words:
        print('\n\n')
        choice = comparative_form(multi_choice_menu.menu_choice(the_menu, 'List of begin-with-apostrophe words "%s" modified. Save new list?' %
                                                                os.path.split(apostrophe_words_filename)[1]))
        if choice == 'y':
            apostrophe_words_filename = apostrophe_words_filename or sfp.do_open_dialog()
            with open(apostrophe_words_filename, 'w') as f:
                f.writelines(sorted(list(set(['’%s\n' % comparative_form(line).lstrip("’'") for line in apostrophe_words]))))


def print_usage(exit_code=0):
    print("\n\n" + __doc__)
    sys.exit(exit_code)


def process_command_line():
    """Read the command-line options. Set global variables appropriately.

    Returns a tuple: (filename of opened file, filename of always-capitalize list).
    Either or both may be None if the command line does not contain these options;
    they can be hardcoded above, beneath the docstring.
    """
    the_filename, the_always_capitalize_list_filename = None, None
    opts = tuple([])

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


def process_file(the_filename):
    """Loads the specified file and verifies it, producing a list of verified lines.
    It returns this list, which is a list of lines that SHOULD BE written back to
    disk.

    This routine DOES NOT SAVE the file back to disk; save_files() does that.

    :param the_filename: the name of the file to be processed.
    """

    print("Opening: %s ..." % os.path.split(the_filename)[1], end=" ")

    with open(the_filename, 'r') as f:
        lines = f.readlines()

    print("successfully read %d lines. Processing..." % len(lines))

    for (count, which_line) in zip(range(len(lines)), lines):   # Go through the text, paragraph by paragraph.
        if patrick_logger.verbosity_level > 0:
            patrick_logger.log_it("\nProcessing line %d" % (count + 1), 1)
            patrick_logger.log_it('THE ORIGINAL LINE IS:\t%s' % which_line, 1)
            patrick_logger.log_it('', 1)

        which_line = which_line.strip()                                 # Note that this is one source of changes of some lines from one valid form to another
        sentences = [][:]                                               # Build a list of corrected sentences to
        # re-assemble when done.
        for sentence in tokenizer.tokenize(which_line):                 # Go through the paragraph, sentence by sentence.
            sentence = correct_sentence_capitalization(sentence)
            sentences += [sentence]                                    # Add corrected sentence to the list of sentences in this paragraph
        corrected_line = ' '.join(sentences) + '\n'                     # Note that we're not (necessarily) preserving original spacing here.

        patrick_logger.log_it('\nTHE CORRECTED LINE IS:\t%s' % corrected_line)

        lines[count] = corrected_line

    return lines


if __name__ == "__main__":
    opts = process_command_line()
    filename, always_capitalize_list_filename = filename or opts[0], always_capitalize_list_filename or opts[1]

    try:                                        # If an auto-capitalize list was specified, load it
        if always_capitalize_list_filename:
            with open(always_capitalize_list_filename, 'r') as skipfile:
                always_capitalize_list = sorted(list(set([comparative_form(line) for line in skipfile.readlines()])))
    except:
        patrick_logger.log_it("WARNING: unable to open always-capitalize file %s" % always_capitalize_list_filename, 0)
        patrick_logger.log_it("    ... proceeding with empty list", 0)

    original_always_capitalize_list = always_capitalize_list.copy()     # Make a shallow copy of whatever we start with.

    try:                                        # If words-with-apostrophes file was specified, load it
        if apostrophe_words_filename:
            with open(apostrophe_words_filename, 'r') as skipfile:
                apostrophe_words = sorted(list(set([comparative_form(line).lstrip('’') for line in skipfile.readlines()])))
    except:
        patrick_logger.log_it("WARNING: unable to open apostrophe file %s" % apostrophe_words_filename, 0)
        patrick_logger.log_it("    ... proceeding with empty list", 0)

    original_apostrophe_words = apostrophe_words.copy()

    filename = filename or sfp.do_open_dialog()
    patrick_logger.log_it('File chosen is "%s"' % filename, 2)
    if not filename:
        print("No file to process!")
        sys.exit(0)

    the_lines = process_file(filename)

    print('\n\n\nEntire file processed.')

    save_files()

    print("All done!\n\n")
