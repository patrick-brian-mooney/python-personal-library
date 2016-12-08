#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""simple_standard_file.py is a set of quick "just somehow ask the user where to
save/open a file" routines. Each does its best to ask the user a specific
question in the best way available and to degrade gracefully if the services
it's trying to use prove not to be available.


This program is licensed under the GPL v3 or, at your option, any later
version. See the file LICENSE.md for a copy of this licence.
"""

import sys

import patrick_logger       # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py

def do_save_dialog(**kwargs):
    """Shows a dialog asking the user where to save a file, or comes as close as
    possible to doing so. Any keyword arguments passed in are piped to the
    underlying function tkinter.filedialog.asksaveasfilename

    Returns a path to the file that the user wants to create.

    Adapted from more complex code in Zombie Apocalypse.
    """
    patrick_logger.log_it("DEBUGGING: simple_standard_file.do_save_dialog() called", 2)
    try:            # Use TKinter if possible
        import tkinter
        import tkinter.filedialog
        tkinter.Tk().withdraw()     # No root window
        filename = tkinter.filedialog.asksaveasfilename()
    except:         # If all else fails, ask the user to type a filename.
        filename = input('Under what name would you like to save the file? ')
    patrick_logger.log_it('    Selected file is %s' % filename, 2)
    return filename

def do_open_dialog(**kwargs):
    """Shows a dialog asking the user which file to open, or comes as close as
    possible to doing so. Any keyword arguments passed in are piped to the
    underlying function tkinter.filedialog.askopenfilename

    Returns a path to the file that the user wants to open.

    Adapted from more complex code in Zombie Apocalypse.
    """
    patrick_logger.log_it("DEBUGGING: simple_standard_file.do_open_dialog() called", 2)
    try:            # Otherwise, use TKinter if possible
        import tkinter
        import tkinter.filedialog
        tkinter.Tk().withdraw()     # No root window
        filename = tkinter.filedialog.askopenfilename(**kwargs)
    except:         # If all else fails, ask the user to type it.
        filename = input('What file would you like to open? ')
    patrick_logger.log_it('    Selected file is %s' % filename, 2)
    return filename

if __name__ == "__main__":
    patrick_logger.log_it("ERROR: %s is not a program you can run. It is a collection of software to be used by other software." % sys.argv[0])
