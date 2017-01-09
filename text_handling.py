#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A collection of text-handling utilities."""


import sys, textwrap, shutil


def multi_replace(text, substitutions):
    """Modify TEXT and return the modified version by repeatedly replacing strings
    in SUBSTITUTIONS (a list of replacements, as specified below) until none of
    the replacements produce any further change in the text.
    
    SUBSTITUTIONS is a list of two-item lists. Each two-item list should be of the
    form [search_string, replace_string]. Here is a sample:
        subs = [['teh', 'the'],
                ['chir', 'chair'],
                ]
    """
    changed = True              # Be sure to run at least once.
    while changed:              # Repeatedly perform all substitutions until none of them change anything at all.
        orig_text = text[:]
        for which_replacement in substitutions:
            text = text.replace(which_replacement[0], which_replacement[1])
        changed = ( orig_text != text )
    return text


def begins_with_apostrophe(w):
    """Determines whether the word begins with an apostrophe.

    :param w: a word. (Or any string, really.)
    :return: True if the string W begins with an apostrophe, or False otherwise.
    """
    if len(w.strip()):
        return w.strip()[0] in ( "'", "’")
    return False    # If it's effectively zero-length, it doesn't begin with an apostrophe.


def strip_non_alphanumeric(w, also_allow_spacing=False):
    """Returns a string containing only the alphanumeric characters from string W and,
    if also_allow_spacing is True, whitespace characters.
    """
    if also_allow_spacing:
        return "".join(ch for ch in w if ch.isalpha() or ch.isnumeric() or ch.isspace())
    else:
        return "".join(ch for ch in w if ch.isalpha() or ch.isnumeric())


def _find_first_alphanumeric(w):
    """Returns the index of the first position in the string that is alphanumeric.
     If there are no alphanumeric characters in the string, returns -1
    """
    for i, c in enumerate(w):
        if c.isalpha() or c.isnumeric():
            return i
    return -1


def _find_last_alphanumeric(w):
    """Returns the index of the first position in the string that is alphanumeric.
     If there are no alphanumeric characters in the string, returns -1
    """
    for i, c in list(reversed(list(enumerate(w)))):
        if c.isalpha() or c.isnumeric():
            return i
    return -1


def strip_leading_and_trailing_punctuation(w):
    """Strips leading and trailing punctuation from the string W. Returns the
    filtered string.
    """
    return w[ _find_first_alphanumeric(w) : 1 + _find_last_alphanumeric(w) ]


def is_capitalized(w):
    """Returns True is the word W is capitalized, False if it is not. "Capitalized"
    in this context means that the string's first alphanumeric character
    satisfies str.isupper()'s criteria for being uppercase.

    Probably, this is somewhat better that just testing w[0].isupper(), because it
    ignores leading punctuation.
    """
    return w[_find_first_alphanumeric(w)].isupper()


def capitalize(w):
    """Capitalize the first letter of the string passed in as W. Leave the case of the
    rest of the string unchanged. Account for possible degenerate cases.

    #FIXME: Only works if the first character in the string is the one that should be
    capitalized.
    """
    if len(w) == 0:
        return w
    elif len(w) == 1:
        return w.upper()
    else:
        first = _find_first_alphanumeric(w)
        if first == -1:
            return w
        else:
            return w[:first] + w[first].upper() + w[1 + first:]

def terminal_width(default=80):
    """Do the best job possible of figuring out the width of the current terminal. Fall back on a default width if it
    absolutely cannot be determined.
    """
    width = shutil.get_terminal_size()[0]
    if width == -1: width = default
    return width

def _get_wrapped_lines(paragraph, indent_width=0, enclosing_width=-1):
    """Function that splits the paragraph into lines. Mostly just wraps textwrap.wrap().

    Note: Strips leading and trailing spaces.
    """
    if enclosing_width == -1: enclosing_width = terminal_width()
    ret= textwrap.wrap(paragraph, width=enclosing_width - 2*indent_width, replace_whitespace=False, expand_tabs=False, drop_whitespace=False)
    return [ l.lstrip() for l in ret ]

def print_indented(paragraph, each_side=4):
    """Print a paragraph with spacing on each side.
    """
    if '\n' in paragraph:                   # If there are newlines in PARAGRAPH ...
        for p in paragraph.split('\n'):     # ... recursively call print_indented() on each sub-paragraph
            print_indented(p, each_side=each_side)
        return
    lines = _get_wrapped_lines(paragraph, each_side)
    for l in lines:
        l = ' ' * each_side + l.strip()
        print(l)

def print_wrapped(paragraph):
    """Convenience function that wraps print_indented().
    """
    print_indented(paragraph, each_side=0)

def getkey():
    """Do the best job possible of waiting for and grabbing a single keystroke.
    Borrowed from Zombie Apocalypse. Keep any changes in sync. (Sigh.)
    """
    try:                            # Alas, the statistical likelihood is that this routine is being run under Windows, so try that first.
        import msvcrt
        return msvcrt.getch()       # This really needs to be actually tested under Windows.
    except ImportError:             # Under any non-Windows OS. (I hope.)
        try:
            import tty, termios
            stdin_fd = sys.stdin.fileno()
            old_status = termios.tcgetattr(stdin_fd)
            try:
                tty.setraw(stdin_fd)
                return sys.stdin.read(1)
            finally:
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_status)
        except:                     # If all else fails, fall back on this, though it may well return more than one keystroke's worth of data.
            return input('')

if __name__ == "__main__":
    print_wrapped("ERROR: text_handling.py is a collection of utilities for other programs to use. It's not itself a program you can run from the command line.")
    sys.exit(1)
