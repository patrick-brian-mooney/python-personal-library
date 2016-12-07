#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A collection of text-handling utilities."""


import sys, textwrap, shutil


def strip_non_alphanumeric(w, also_allow_spacing=False):
    """Returns a string containing only the alphanumeric characters from string W. """
    if also_allow_spacing:
        return "".join(ch for ch in w if ch.isalpha() or ch.isnumeric() or ch.isspace())
    else:
        return "".join(ch for ch in w if ch.isalpha() or ch.isnumeric())

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
        return w[0].upper() + w[1:]

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
    print_indented("ERROR: text_handling.py is a collection of utilities for other programs to use. It's not itself a program you can run from the command line.")
    sys.exit(1)
