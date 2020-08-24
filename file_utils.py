#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Some file-handling utilities.

This script is copyright 2017-20 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""

import os
from pathlib import Path

import patrick_logger


def empty_and_delete_dir(which_dir):
    """Empties out a directory if at all possible. Dangerous! Potentially
    deletes lots of data! Does not ask for confirmation before deleting lots of
    data!
    """
    try:
        assert isinstance(which_dir, Path)
    except AssertionError:
        which_dir = Path(which_dir)

    try:                                # Account for the degenerate case: what if it's not a directory?
        assert which_dir.is_dir()
    except AssertionError:
        which_dir.unlink()
        return

    for f in which_dir.glob('*'):
        if f.is_dir():
            empty_and_delete_dir(f)
        else:
            f.unlink()

    os.rmdir(which_dir)


def find_and_execute_scripts(path='.'):
    """Find executable *SH files in the current directory and its subdirectories,
    then execute them. Specify the path to walk as PATH; it defaults to the
    current directory.
    """
    for (dirname, subshere, fileshere) in os.walk(path, topdown=True):
        subshere.sort()
        print('Looking for scripts in %s' % dirname)
        file_list = sorted([ which_script for which_script in fileshere if which_script.endswith('SH') ])
        # file_list = [ which_script for which_script in file_list if os.access(which_script, os.X_OK) ]
        for which_script in file_list:
            try:
                olddir = os.getcwd()
                os.chdir(dirname)
                print('\n\n    Running script: %s' % os.path.abspath(which_script))
                try:
                    subprocess.call('nice -n 10 ./' + which_script, shell=True)
                    os.system('chmod a-x -R %s' % which_script)
                except BaseException as e:
                    print('Unable to execute script: the system said: ' + str(e))
            finally:
                os.chdir(olddir)


def get_files_list(which_dir, skips=None):
    """Get a complete list of all files and folders under WHICH_DIR, except those matching SKIPS.
    Calls itself recursively, so it's a bad idea if the directory is (literally)
    very profound.
    """
    if skips == None:
        skips = [][:]
    ret = [][:]
    for (thisdir, dirshere, fileshere) in os.walk(which_dir):
        ret.append(os.path.join(thisdir))
        if dirshere:
            for dname in dirshere:
                ret += get_files_list(os.path.join(thisdir, dname), skips)
        if fileshere:
            for fname in fileshere:
                ret.append(os.path.join(thisdir, fname))
        if skips:
            for the_skip in skips:
                ret = [the_item for the_item in ret if the_skip not in the_item]
        ret.sort()
        return ret


def do_save_dialog(**kwargs):
    """Shows a dialog asking the user where to save a file, or comes as close as
    possible to doing so. Any keyword arguments passed in are piped to the
    underlying function tkinter.filedialog.asksaveasfilename

    Returns a path to the file that the user wants to create.

    Adapted from more complex code in Zombie Apocalypse.
    """
    import tkinter.filedialog       # Don't want to make tkinter a dependency for every project that uses this module
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
    import \
        tkinter.filedialog  # Don't want to make tkinter a dependency for every project that uses this module
    patrick_logger.log_it("DEBUGGING: simple_standard_file.do_open_dialog() called", 2)
    try:            # Use TKinter if possible
        import tkinter
        import tkinter.filedialog
        tkinter.Tk().withdraw()     # No root window
        filename = tkinter.filedialog.askopenfilename(**kwargs)
    except:         # If all else fails, ask the user to type it.
        filename = input('What file would you like to open? ')
    if filename == tuple([]):
        patrick_logger.log_it('    INFO: simple_standard_file: do_open_dialog() cancelled', 2)
        filename = None
    else:
        patrick_logger.log_it('    INFO: simple_standard_file: Selected file is "%s"' % filename, 2)
    return filename


if __name__ == "__main__":
    pass
