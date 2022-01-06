#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Take one or more pickle-encoded files and attempt to produce JSON equivalents of
their contents. ("Pickle" is a Python-specific data storage format.)

Not all pickle-encoded files can be expressed as JSON files because pickling is
a more flexible serialization strategy than conversion to JSON. Files that
cannot be converted will be skipped, and a warning message will be printed
before processing continues.

Usage:
    pickle_to_json.py FILENAME [FILENAME2] [FILENAME3] [...]

If the script complains that the version of the pickle files you are trying to
read is too high, try running the script with a more recent version of Python.

This script is copyright 2022 by Patrick Mooney. It is licensed under the GNU
GPL, either v3 or, at your option, any later version. See the file LICENSE.md
for a copy of this license.
"""


import json

from pathlib import Path

import pickle
import sys


def print_usage(exit_code: int = 0) -> None:
    """Print a usage message and quit, passing EXIT_CODE to the system shell.
    """
    print(__doc__)
    sys.exit(exit_code)


def pickle_to_json(which_file: Path) -> None:
    """Attempt to decode WHICH_FILE, which must be a pickled data structure, to a
    corresponding JSON file in the same directory. Try to issue an informative error
    message if decoding or encoding fails.
    """
    assert isinstance(which_file, Path)
    print(f'\nUnpickling and converting {which_file.name} ...')

    try:
        with open(which_file, 'rb') as pickle_file:
            # Read the first pickled object from the file
            data = pickle.load(pickle_file)
            if not data:
                raise RuntimeWarning(f"No pickled data found in {which_file.name}!")
            else:
                json_file = which_file.with_suffix('.json')
                if json_file.exists():
                    raise RuntimeWarning(f"Skipping instead of overwriting existing file {json_file.name}!")
                json_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

                # Now try to read more data from the pickled file; issue a warning if any more data can be read
                try:
                    _ = pickle.load(pickle_file)
                    raise RuntimeWarning(f"File contains more than one pickled object! Skipping data after first object in file.")
                except EOFError:
                    print('    ... done!')
                    return              # No more data? We're done.

    except (pickle.UnpicklingError,) as err:
        print(f"    Unable to decode pickled data in {which_file}! Source data may be empty or corrupted. The system said: {err}.")
    except (RuntimeWarning,) as err:
        print(f"    {err}")
    except (Exception,) as err:
        print(f"    Unable to complete conversion! The system said: {err}.")


if __name__ == "__main__":
    force_test = True
    if force_test:
        pickle_to_json(Path('/home/patrick/Documents/programming/python_projects/VideoDataStore/samples/.metadata.pkl'))
        sys.exit(0)

    if len(sys.argv) == 1:
        print_usage(1)
    elif len(sys.argv) == 2 and (sys.argv[1].lower().strip() in ["--help", "-h"]):
        print_usage(0)
    elif len(sys.argv) >=2:
        for which_file in sys.argv[1:]:
            pickle_to_json(Path(which_file))
