#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Some file-handling utilities.

This script is copyright 2017-20 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""
import json
import os
import subprocess
import typing

from pathlib import Path
from typing import Generator, List

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


def get_files_list(which_dir: typing.Union[Path, str],
                   skips: typing.Optional[typing.Iterable[typing.Union[str, Path]]] = None
                   ) -> typing.Iterable[typing.Union[str, Path]]:
    """Get a complete list of all files and folders under WHICH_DIR, except those matching SKIPS.
    Calls itself recursively, so it's a bad idea if the directory is (literally)
    very profound.
    """
    if skips is None:
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
    import tkinter.filedialog  # Don't want to make tkinter a dependency for every project that uses this module
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


def relative_to(from_where: Path,
                to_where: Path) -> Path:
    """Describe the path leading from the file or directory FROM_WHERE to the file or
    directory TO_WHERE, even if FROM_WHERE is not an ancestor of TO_WHERE.

    Relies largely on os.path.relpath(), but that's not *quite* always what we want;
    if FROM_WHERE is a file, we don't want the initial '../' that means "move up
    from that file to its parent directory"; users expect '../' to mean "move up
    from one directory to another," not "take the parent directory of this file,"
    which is a rather pedantic interpretation from a UI perspective even if it's
    perfectly correct from a path-operation perspective.

    In fact, os.path.relpath() assumes both components are directories, which is
    kind of weird, so we test and correct both FROM_WHERE and TO_WHERE.
    """
    assert isinstance(from_where, Path)
    assert isinstance(to_where, Path)

    if from_where.is_file():
        from_where = from_where.parent
    if to_where.is_file():
        to_where = to_where.parent

    return Path(os.path.relpath(to_where, from_where))


def relative_to_with_name(from_where: Path,
                          to_where: Path) -> Path:
    """Same as relative_to() above, but returns a Path with a terminal filename, not
    just the relative directory structure.
    """
    assert isinstance(from_where, Path)
    assert isinstance(to_where, Path)

    ret = Path(relative_to(from_where, to_where))
    if ret.name != to_where.name:
        ret = ret / to_where.name
    return ret


class PathAsStrJSONEncoder(json.JSONEncoder):
    """Store paths as plain strings. They'll be re-interpreted as paths on load.
    """
    def default(self, obj):
        if issubclass(type(obj), Path) or isinstance(obj, Path):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def _files_in_folders_recursively(p: Path) -> Generator[Path, None, None]:
    """A generator that emits each file that is in any subdirectory of P, a Path
    representing a directory. If an all-at-once list of every file under this folder
    is needed, use the no-underscore convenience function with a similar name,
    below.
    """
    assert isinstance(p, Path)
    assert p.is_dir()

    for item in p.glob("*"):
        if item.is_dir():
            yield from _files_in_folders_recursively(item)
        elif item.is_file():
            yield item


def files_in_folders_recursively(p: Path) -> List[Path]:
    """Just a convenience function that produces a list, all at once, from the
    similarly named generator function.
    """
    return list(_files_in_folders_recursively(p))


def rmdir_if_effectively_empty(dir: Path) -> bool:
    """A directory is "effectively empty" if it ...
        * contains no files; and either
        * contains no subdirectories, or
        * contains only subdirectories that are themselves effectively empty.

    This function recursively traverses DIR, a directory, deleting leaf actually
    empty directories under DIR, then crawling back up and deleting directories that
    have been made empty by having their subdirectories deleted. If the function is
    able to empty everything beneath DIR, it removes the now-empty DIR itself and
    returns True. If, at any point, it encounters a file, it stops processing
    immediately and returns False.
    """
    assert isinstance(dir, Path)
    assert dir.is_dir()

    for i in dir.glob('*'):
        if i.is_file():
            return False
        elif i.is_dir():
            if not rmdir_if_effectively_empty(i):
                return False

    if len(list(dir.glob('*'))) == 0:
        dir.rmdir()
        return True


if __name__ == "__main__":
    pass
