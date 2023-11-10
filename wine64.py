#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility to launch 64-bit Windows applications in 64-bit Wine on my system
so that I don't have to remember the details of the invocation.

Usage:
    wine64.py EXECTUABLE_NAME [options for Windows program]

Uses unsafe behavior to be lazy about how programs are launched, and is
therefore not a good option to allow untrusted users to use.

This script is copyright 2023 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


import collections
import os

from pathlib import Path

import sys
import subprocess

from typing import List


import text_handling as th


WINEPREFIX = Path("~/.wine64/").expanduser().resolve()
WINEARCH = "win64"
WINEEXECPATH = Path("/usr/lib/wine/wine64").resolve()


def main(args: List[str]) -> None:
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    if args[1].strip().casefold() in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    cmdline = [f"{WINEEXECPATH}",] + args[1:]
    env = collections.ChainMap({'WINEPREFIX': str(WINEPREFIX),
                                'WINEARCH': WINEARCH},
                               os.environ)

    print(f"Running under {sys.version}")
    print(f"Executing: {cmdline}")

    proc = subprocess.run(cmdline, capture_output=True, env=env)
    if proc.returncode:
        from pprint import pprint
        th.print_wrapped(th.unicode_of(f"Called process exit status {proc.returncode}"))
        th.print_wrapped(th.unicode_of(f"Standard output:\n{proc.stdout}"))
        th.print_wrapped(th.unicode_of(f"\nStandard error:\n{proc.stderr}\n\n"))


if __name__ == "__main__":
    if False:
        main(['', """/home/patrick/games/IF/competitions/[2023] IFComp 29/Games/Have Orb Will Travel/update of 25 Oct 2023/Have Orb, Will Travel.exe"""])
        sys.exit(0)
    main(sys.argv)

