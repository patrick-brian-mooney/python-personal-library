#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick hack to XML-encode a string passed in via the terminal

Usage:

    ./HTML_escape "some text" ["some more text"] ["another string"] [...]

It can also be imported as a module by Python 3.X programs, though why you
would want to go to the trouble of doing so is beyond me.

This script is copyright 2017 by Patrick Mooney. It is licensed under the GPL,
either version 3 or (at your option) any later version. See the file LICENSE.md
for details.
"""


import html
import sys


def do_escape(what):
    return html.escape(what)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in [ '--help', '-h']:
        print(__doc__)
        sys.exit(1 if len(sys.argv) < 2 else 0)
    sys.argv.pop(0)
    for what in sys.argv:
        print('\n' + do_escape(what))
    print()
