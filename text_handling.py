#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A collection of text-handling utilities."""


import sys, textwrap, shutil



def terminal_width():
    terminal_width = shutil.get_terminal_size()[0]
    if terminal_width == -1: terminal_width = 80
    return terminal_width

def print_indented(paragraph, each_side=4):
    lines = textwrap.wrap(paragraph, width=terminal_width() - 2*each_side, replace_whitespace=False, expand_tabs=False, drop_whitespace=False)
    for l in lines:
        print(' ' * each_side + l)

if __name__ == "__main__":
    print("ERROR: text_handling.py is a collection of utilities for other programs to use. It's not itself a program you can run from the command line.") 
    sys.exit(1)
