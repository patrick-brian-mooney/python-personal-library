#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_capitalization.py, by Patrick Mooney; 9 December 2016

This is a script to find capitalized words in the middle of sentences that
are not proper nouns (or approved other capitalized words). It also makes some
attempt to detect other capitalization problems. It goes through a text,
sentence by sentence, asking the user whether each sentence should be
capitalized. If not, it converts them to lowercase. When it has finished, it
writes the modified text back to the same file, i.e. it modifies the input file
in-place. It is primarily intended to check the output of my poetry_to_prose.py
script and was originally developed in order to facilitate the processing of a
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

  -h, --help
      Print this help message, then quit.

This script requires that NLTK be installed, because it relies on NLTK for a
lot of the work it does. See http://www.nltk.org/.

The most recent version of this script is available at:
https://github.com/patrick-brian-mooney/python-personal-library/blob/master/check_capitalization.py

This program is copyright 2016-21 by Patrick Mooney; it is licensed under the
GPL v3 or, at your option, any later version. See the file LICENSE.md for a
copy of this license.
"""


import getopt
import pprint
import os
import string
import sys
import typing

from collections import OrderedDict
from pathlib import Path

import nltk                                     # nltk.org

import file_utils                               # https://github.com/patrick-brian-mooney/python-personal-library/
import multi_choice_menu                        # Same source.
import text_handling as th                      # Same.


always_capitalize_sentence_beginnings = True    # Usually, it's helpful to set this to True if NLTK is doing a good job of finding the beginnings of sentences.


always_capitalize_list_filename = Path('/python-library/always_capitalize_list')    # Or leave empty not to use a global list.
apostrophe_words_filename = Path('/python-library/apostrophe_words')                # File listing words allowed to begin with an apostrophe
default_filename = None                                                             # Fill this in with a filename to validate that file


the_lines = [][:]
always_capitalize_list, original_always_capitalize_list = [][:], [][:]
apostrophe_words, original_apostrophe_words = [][:], [][:]


allowed_capitalized_words = ("i", "i'll",       # additional words that are allowed to be capitalized mid-sentence.
                             "i’ll", "i'd",     # these need to be represented in lowercase so the comparison works!
                             "i’d", "i'm", "i’m", "i've", "i’ve")
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
punc = ''.join(list(set(string.punctuation) - {"'"} | {'—‘“”'}))

text_source_file_changed = False                # Have we made any changes to the source file this run?


def puncstrip(w: str) -> str:
    """Return a version of W, a string, that has no punctuation at the beginning or
    end.
    """
    return w.rstrip("'").strip(punc)    # Only strip straight quotes off the end: at the beginning, they might be apostrophes.


def comparative_form(w: str) -> str:
    """A quick convenience function to just return a standardized form of a word for
    the purpose of comparing words for equality. It's lowercase, strips out (most)
    leading and trailing punctuation, and strips out some (but not necessarily all)
    whitespace.

    :param w: the word to take the comparative form of
    :return: the comparative form of the word
    """
    ret = puncstrip(puncstrip(w.strip()).strip()).casefold()
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
    # strip the same set of punctuation, then casefold the result. Additionally,
    # if the word begins with an apostrophe but doesn't appear in the global list
    # APOSTROPHE_WORDS, then strip the leading apostrophe.


def reassemble_sentence(sentence_list: typing.List[typing.Tuple[str, str]]) -> str:
    """Given a tagged sentence -- a list of tuples of the form
    [(word, POS), (word, POS) ... ] -- reassemble it into a string much like the
    original sentence (though possibly with spacing altered).
    """
    ret = ''        # FIXME: check if type annotation is correct
    for w, _ in sentence_list:
        ret = "%s%s" % (ret, w) if w in punc else "%s %s" % (ret, w)      # Add space, except before punctuation
    return ret


def check_word_capitalization(tagged_sentence: typing.List[typing.Tuple[str, str]],  # CHECK: is this correct?
                              word_number: int,
                              allow_always_correct: bool,
                              # The rest of these parameters are just in case we have to save while quitting in the
                              # middle of the run. They can be None; if either is, saving is not an option that's
                              # offered to the user.
                              the_lines: typing.Union[typing.List[str], None] = None,
                              working_filename: typing.Union[Path, None] = None,
                              ) -> bool:
    """Give the user a choice of whether to correct the capitalization of word number
    WORD_NUMBER in TAGGED_SENTENCE or not to correct the capitalization of that
    word. The "tagged" in TAGGED_SENTENCE means "POS-tagged by NLTK."

    If ALLOW_ALWAYS_CORRECT is True, the user is given the option to always
    capitalize this word; otherwise, the user is not given this option.
    """
    global text_source_file_changed
    global always_capitalize_list, apostrophe_words
    if working_filename:
        assert isinstance(working_filename, Path)

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
        if the_lines and working_filename:
            the_menu['Q'] = 'Quit, with option to save training data (but not modified text)'

        choice = comparative_form(multi_choice_menu.menu_choice(the_menu, "What would you like to do?"))
        if choice == 'a':
            always_capitalize_list += [comparative_form(the_word)]
            choice = "n" if th.is_capitalized(the_word) else "y"
        elif choice == 'q':                         # FIXME: we should really be able to save the modified source text.
            # The text file hasn't been fully reassembled yet, so we can't save it! Pass other parameters, though.
            # This branch only available if THE_LINES and WORKING_FILENAME were specified as parameters.
            save_files()
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


def correct_sentence_capitalization(s: str,
                                    working_filename: typing.Union[Path, None] = None,
                                    the_lines: typing.Union[typing.List[str], None] = None) -> str:
    """Return a corrected version of S, the sentence that was passed in.

    This is where the real work actually happens.
    """
    global text_source_file_changed

    count = 0
    tagged_sent = nltk.tag.pos_tag(s.split())   # This is now a list of tuples: [(word, POS), (word, POS) ...]
    for word, pos in tagged_sent:               # POS = "part of speech." Go through the list of tuples, word by word
        count += 1                              # In English language counting order, which word in the sentence is this?

        # OK, let's check for various capitalization problems.
        # First: check for problems that are independent of whether they occur in the first word of a sentence.
        if comparative_form(word) in always_capitalize_list and not th.is_capitalized(word):
            # Check: uncapitalized word we know should always be capitalized?
            tagged_sent[count-1] = (th.capitalize(tagged_sent[count-1][0]), pos)
            text_source_file_changed = True

        # Next, check for problems related to the first word of a sentence.
        if count == 1:                                  # Beginning of sentence has special handling.
            if not th.is_capitalized(word):                   # Check: should first word of sentence be capitalized?
                if always_capitalize_sentence_beginnings or check_word_capitalization(tagged_sent, count-1):
                    # If we capitalize it, set the indicated item in the list of tuples to a tuple that capitalizes the
                    # word in question and maintains the POS tagging for further checking. The rather ugly expression
                    # below is of course necessary because tuples are immutable.
                    tagged_sent[count-1] = (th.capitalize(tagged_sent[count-1][0]), pos)
                    text_source_file_changed = True

        # Now, check for problems that can happen only outside the first word of a sentence.
        else:                                           # Checks for words other than the first word of the sentence
            # First: is there an unexplained capitalized word beyond the first word of the sentence?
            # unused fragment, should it go back in?:  and (pos.upper() not in ['NNP'])
            # probably not: NLTK is detecting proper nouns in part based on capitalization.
            if th.is_capitalized(word) and (comparative_form(word) not in allowed_capitalized_words):
                # Capitalized, but not a proper noun?
                if check_word_capitalization(tagged_sentence=tagged_sent, word_number=count-1,
                                             allow_always_correct=True, the_lines=the_lines,
                                             working_filename=working_filename):
                    tagged_sent[count-1] = (tagged_sent[count-1][0].lower(), pos)
                    text_source_file_changed = True
            elif (not th.is_capitalized(word)) and (comparative_form(word) in always_capitalize_list):
                tagged_sent[count-1] = (th.capitalize(tagged_sent[count-1][0]), pos)
                text_source_file_changed = True

    return reassemble_sentence(tagged_sent).strip()


save_data_menu = OrderedDict([
    ('Y', "Overwrite the old data"),
    ('N', 'Cancel and lose the changes')
])


def save_files(the_lines: typing.Union[typing.List[str], None] = None,
               working_filename: typing.Union[Path, None] = None,
               suppress_kvetching: bool = False) -> None:
    """Give the user the option (possibly) to save the modified-in-place verified text (stored
    in global variable THE_LINES), plus, if modified, the list of words to always
    skip.

    If no changes were made, then the procedure well helpfully inform you of that,
    unless SUPPRESS_KVETCHING is True.
    """
    global apostrophe_words_filename, always_capitalize_list_filename       # semi-constant module configuration params
    global apostrophe_words, always_capitalize_list
    global original_always_capitalize_list
    global text_source_file_changed

    if working_filename:
        assert isinstance(working_filename, Path)
    if apostrophe_words_filename:
        assert isinstance(apostrophe_words_filename, Path)
    if always_capitalize_list_filename:
        assert isinstance(always_capitalize_list_filename, Path)

    if text_source_file_changed:
        if the_lines and working_filename:
            choice = comparative_form(multi_choice_menu.menu_choice(save_data_menu, 'Overwrite file "%s" with modified text?' % working_filename.name))
            if choice == 'y':
                with working_filename.open('w') as f:
                    f.writelines(the_lines)
    else:
        if not suppress_kvetching:
            print('No changes made in this file, moving on ...\n\n')
    always_capitalize_list.sort()           # FIXME! Is this happening when called from a module?
    if always_capitalize_list != original_always_capitalize_list:
        print('\n\n')
        choice = comparative_form(multi_choice_menu.menu_choice(save_data_menu, 'List of always-capitalize words "%s" modified. Save new list?' %
                                                                always_capitalize_list_filename.name))
        if choice == 'y':
            always_capitalize_list_filename = always_capitalize_list_filename or file_utils.do_open_dialog()
            with always_capitalize_list_filename.open('w') as f:
                f.writelines(sorted(list(set([comparative_form(line) + '\n' for line in always_capitalize_list]))))
                original_always_capitalize_list = always_capitalize_list

    apostrophe_words.sort()
    if apostrophe_words != original_apostrophe_words:
        print('\n\n')
        choice = comparative_form(multi_choice_menu.menu_choice(save_data_menu, 'List of begin-with-apostrophe words "%s" modified. Save new list?' %
                                                                apostrophe_words_filename.name))
        if choice == 'y':
            apostrophe_words_filename = apostrophe_words_filename or file_utils.do_open_dialog()
            with apostrophe_words_filename.open('w') as f:
                f.writelines(sorted(list(set(['’%s\n' % comparative_form(line).lstrip("’'") for line in apostrophe_words]))))


def print_usage(exit_code: int = 0) -> typing.NoReturn:
    """Print a usage message and exit. If a non-zero EXIT_CODE is specified, the OS
    will understand that there is an error condition.
    """
    print("\n\n" + __doc__)
    sys.exit(exit_code)


def process_command_line() -> typing.Tuple[typing.Union[Path, None], typing.Union[Path, None]]:
    """Read the command-line options. Set global variables appropriately.

    Returns a tuple: (path to opened file, path to always-capitalize list).
    Either or both may be None if the command line does not contain these options;
    defaults can be hardcoded above, beneath the docstring, but those constants are
    not read or otherwise dealt with by this function.
    """
    the_filename, the_always_capitalize_list_filename = None, None
    opts = tuple([])

    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'l:i:h', ['help', 'input='])
    except getopt.GetoptError:
        print_usage(2)
    for opt, param in opts:
        if opt in ('-h', '--help'):
            print_usage()
        elif opt in ('-i', '--input'):
            the_filename = Path(param)
        elif opt in ('-l', '--list'):
            print('Using always-capitalize file "%s"' % (param))
            the_always_capitalize_list_filename = Path(param)
        else:
            print('ERROR: unknown switch %s used. Exiting ...' % opt)
            sys.exit(3)
    return the_filename, the_always_capitalize_list_filename


def process_lines(lines: typing.List[str],
                  working_filename: Path) -> typing.List[str]:
    """Process LINES, a list of lines, correcting those that need correcting, and
     returning the list.
    """
    assert isinstance(working_filename, Path)
    ret = [][:]

    for which_line in [l.strip() for l in lines]:           # Go through the text, paragraph by paragraph.
        sentences = [][:]                                   # Build a list of corrected sentences to

        # re-assemble when done.
        for sentence in tokenizer.tokenize(which_line):     # Go through the paragraph, sentence by sentence.
            sentence = correct_sentence_capitalization(sentence, working_filename=working_filename)
            sentences.append(sentence)
        ret.append(' '.join(sentences) + '\n')

    return ret  # Check: is annotation for return type correct?


def process_file(the_filename: Path) -> typing.List[str]:
    """Loads the specified file and verifies it, producing a list of verified lines.
    It returns this list, which is a list of lines that SHOULD BE written back to
    disk.

    This routine DOES NOT SAVE the file back to disk; save_files() does that.
    """
    assert isinstance(the_filename, Path)
    print("Opening: %s ..." % the_filename.name, end=" ")

    with the_filename.open('r') as f:
        lines = f.readlines()

    print("successfully read %d lines. Processing...\n" % len(lines))

    ret = process_lines(lines, working_filename=the_filename)
    return ret                      # Check: is function return type annotation


force_debugging = False      # Do we want to force a controlled run instead of reading the command line?

if __name__ == "__main__":
    if force_debugging:
        opts = Path("""/home/patrick/Documents/programming/python_projects/LibidoMechanica/poetry_corpus/William Shakespeare: Sonnet 033"""), None
    else:
        opts = process_command_line()
    working_filename, always_capitalize_list_filename = default_filename or opts[0], always_capitalize_list_filename or opts[1]

    try:                                        # If an auto-capitalize list was specified, load it
        if always_capitalize_list_filename:
            with always_capitalize_list_filename.open('r') as skipfile:
                always_capitalize_list = sorted(list(set([comparative_form(line) for line in skipfile.readlines()])))
    except Exception as errrr:
        print("WARNING: unable to open always-capitalize file %s! The system said: %s" % (always_capitalize_list_filename, errrr))
        print("    ... proceeding with empty list")

    original_always_capitalize_list = always_capitalize_list.copy()     # Make a shallow copy of whatever we start with.

    try:                                        # If words-with-apostrophes file was specified, load it
        if apostrophe_words_filename:
            with apostrophe_words_filename.open('r') as skipfile:
                apostrophe_words = sorted(list(set([comparative_form(line).lstrip('’') for line in skipfile.readlines()])))
    except Exception as errrr:
        print("WARNING: unable to open apostrophe file %s! The system said: %s" % (apostrophe_words_filename, errrr))
        print("    ... proceeding with empty list")

    original_apostrophe_words = apostrophe_words.copy()

    working_filename = working_filename or file_utils.do_open_dialog()
    if not working_filename:
        print("No file to process!")
        sys.exit(0)

    the_lines = process_file(working_filename)

    print('\n\n\nEntire file processed.')

    save_files(the_lines=the_lines, working_filename=working_filename)        #FIXME: don't reference globals!

    print("All done!\n\n")
