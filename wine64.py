#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility to launch 64-bit Windows applications in 64-bit Wine on my system
so that I don't have to remember the details of the invocation.

Usage:
    wine64.py EXECTUABLE_NAME [options for Windows program]

This script is copyright 2023 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


from pathlib import Path
import sys
import subprocess

WINEPREFIX = Path("~/.wine64/").expanduser().resolve()
WINEARCH = "win64"
WINEEXECPATH = Path("/usr/lib/wine/wine64").resolve()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1].strip().casefold() in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    subprocess.run(([str(WINEPREFIX), WINEARCH, str(WINEEXECPATH)] + sys.argv[1:]))

