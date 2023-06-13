#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A flexible system for managing an application's config files in a filesystem.
This module allows for multiple config files to be read, with user-level files
overriding system-specific files, so that system administrators can set up
default options for all users, and individual users can override those options.
These "config files" are JSON-serialized Python dictionaries in which a string-
indexed dictionaries access whatever (JSON-serializable) data the application
needs to store.

flex_config reads all config files in locations where config files are expected
to be stored in Linux, macOS, and Windows, and presents them as if they were a
Python dictionary. This hashmap-style object can also have its settings
changed, and those settings can be written back to disk; the settings are
written as a single JSON file that contains *changed* (not *all*) data, in the
first location it can find when traversing backward through the list of
locations where config files may be stored. That is, it will store updated
prefs in user-level locations first, and only in system-level locations if it
cannot find a usable user-level location. Of course it skips locations where
the user running the program does not have the ability to write.

This script is copyright 2022-23 by Patrick Mooney. It is licensed under the
GNU GPL, either v3 or, at your option, any later version. See the file
LICENSE.md for a copy of this license.
"""


import collections
import json
import os

from pathlib import Path

import shutil
import typing
import warnings


def path_of(what: str) -> typing.Union[str, None]:
    """Given WHAT, the name of an executable, try to find that executable and return the
    filesystem path to it as a string. If we cannot determine the filesystem path,
    return WHAT unmodified, in the hope that it represents an executable in the
    system $PATH.
    """
    try:
        return shutil.which(what)
    except Exception as err:
        return None


def jsonify(what: typing.Any, **kwargs) -> str:
    """Takes WHAT and serializes it as a JSON string. WHAT must obey the general rules
    for JSON serializability.

    This is just a utility function that wraps json.dumps so that other code doesn't
    have to specify the same parameters over and over. Additional parameters not
    specified here can be passed in as **kwargs.
    """
    return json.dumps(what, indent=2, ensure_ascii=False, sort_keys=True, **kwargs)


class PrefsTracker(collections.abc.MutableMapping):
    """A set of routines to manage a global preferences store, bound up with data
    about that store's state.

    Code which may update the preferences is responsible for manually writing changes
    (by calling save_preferences()) when it's done making them. This object assumes
    that changes have already been written by the time it is destroyed.
    """
    def __init__(self, appname: str,
                 defaults: typing.Optional[typing.Dict[str, typing.Any]] = None,
                 *args, **kwargs):
        """Go through the list of possible locations for preferences files, reading
        any that are found and assembling them into a ChainMap. Start the ChainMap with
        the embedded defaults so we have the hard-coded fallback if there are no prefs
        files anywhere along the search path.

        APPNAME is the name of the application; it is needed to name preferences files
        correctly as "[APPNAME] preferences".

        DEFAULTS is a dictionary of application-supplied default settings; supplying
        this means that the default settings are the last-checked (i.e., lowest-
        priority) dictionary when looking up preferences
        """
        assert appname, "The APPNAME supplied at a PrefsTracker initialization cannot be blank!"
        assert appname.strip(), "The APPNAME supplied at a PrefsTracker initialization cannot be only whitespace!"
        if not defaults:
            defaults = dict()

        self.prefs_file_name = f"{appname} preferences"
        self.config_dirs = [  # directories in which we search for configuration files.
            Path('/etc') / appname,                                 # Unix
            Path('/Library/Preferences') / appname,                 # macOS
            Path(__file__).resolve().parent.parent,                 # application installation directory
            Path(os.path.expanduser('~')),                          # any
            Path(os.path.expanduser('~')) / 'Library/Preferences' / appname,  # macOS
            Path(os.path.expanduser('~')) / ('.' + appname),        # Unix
            Path(os.path.expanduser('~')) / '.config' / appname,    # Unix
            Path(os.environ['XDG_CONFIG_HOME']) / appname if os.environ.get('XDG_CONFIG_HOME') else None,  # Unix
            Path(os.environ['LOCALAPPDATA']) / appname if os.environ.get('LOCALAPPDATA') else None,  # Windoze
        ]

        self.data = collections.ChainMap(defaults)  # The furthest-back map is the hardcoded application defaults.
        for p in [loc for loc in self.config_dirs if loc]:  # Filter out any Nones from the list
            this_config = p / self.prefs_file_name
            if this_config.exists():
                try:
                    self.data = self.data.new_child(json.loads(this_config.read_text(encoding='utf-8')))
                except (OSError, json.JSONDecodeError) as errrr:
                    warnings.warn(f"Unable to open prefs file {this_config}. The system said: {errrr}")

        # The frontmost map in the ChainMap is a new empty dict, which will catch all assignments to the preferences
        # structure. This means that we can track just what's changed and write just the changes to an on-disk
        # preferences file that integrates into our preferences file hierarchy.
        self.changed_data = dict()                  # This is the frontmost map
        self.data = self.data.new_child(self.changed_data)

        # Now copy references to mutable objects to the frontmost map to make sure that, when they are modified,
        # the modifications are saved. (__getitem__() lookups will find items deeper in the ChainMap than the frontmost
        # map; altering those items won't result in changes to the frontmost map and therefore won't be saved. We
        # avoid this by copying all mutable data to the frontmost map every single time we load the preferences from
        # on-disk files.)

        for key, value in self.data.items():
            if isinstance (value, (dict, list)):
                self.changed_data[key] = value

        self.writeable_prefs_dir = None             # Or a Path, once we discover one.

        # Next, write some summary data to the backmost map in the chain, so it's not written out in a prefs file
        # (and therefore -- intentionally -- has to be recalculated on every run).
        all_known_types = self['known_video_types'] + self['known_audio_types']
        all_processable_types = [i for i in all_known_types if not i in self['never_process_types']]
        self.data.maps[-1].update({'all_processable_types': all_processable_types})

        # Finally, if we're passed any dict-type constructor arguments, update us.
        self.update(dict(*args, **kwargs))
        self.validate_settings()

    def __getitem__(self, key: typing.Hashable) -> typing.Any:
        """Makes the object indexable by key so we don't have to keep referring to
        [object].data['something']
        """
        return self.data[key]

    def __setitem__(self, key: typing.Hashable,
                    value: typing.Any) -> None:
        self.data[key] = value

    def __delitem__(self, key: typing.Hashable) -> None:
        del self.data[key]

    def __iter__(self) -> typing.Iterator:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def save_preferences(self) -> None:
        """Goes backwards through the list of CONFIG_DIRECTORIES, trying to create a
        preferences file in any existing directory that it finds. When it finds a
        location to which it can write a preferences file, it writes the first map from
        the PREFERENCES ChainMap -- those key-value pairs that have been assigned or
        changed just during this run -- to the location it found.

        If there is already a preferences file in that location, the preferences file
        that overwrites it incorporates any data in the prefs file being overwritten,
        except (of course) for those things that have changed during this run.
        """
        if not self.changed_data:           # No changes made? No work needs be done.
            return

        saved = False
        dirs_to_check = self.config_directories[::-1]
        if self.writeable_prefs_dir:
            dirs_to_check = [self.writeable_prefs_dir] + dirs_to_check

        while not saved and dirs_to_check:
            dir = dirs_to_check.pop(0)
            if not dir:
                continue  # Skip everything else if dir is None, i.e. doesn't exist on this machine.
            if not dir.exists():                    # If the directory doesn't exist on this system, try to create it.
                try:
                    dir.mkdir(parents=True)
                except (OSError,):                  # Trap errors, including the frequent PermissionError.
                    continue                            # If we can't create the containing directory, move on.
            if not dir.exists():                    # If we didn't manage to create it, move along.
                continue
            p = dir / self.prefs_file_name
            old_data = dict()
            if p.exists():
                try:
                    old_data = json.loads(p.read_text(encoding='utf-8'))
                except (IOError, json.JSONDecodeError):
                    pass
            try:
                data_to_write = dict(collections.ChainMap(self.changed_data, old_data))
                p.write_text(jsonify(data_to_write, default=repr), encoding='utf-8')
                saved = True
                self.writeable_prefs_dir = dir      # Keep track of where we last saved prefs.

            except (IOError,):
                pass

        if not saved:
            warnings.warn('Unable to save preferences anywhere!')

