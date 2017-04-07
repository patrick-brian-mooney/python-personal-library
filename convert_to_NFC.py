#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick hack to convert a given string to Unicode Text Normalization Form C, which
is the W3C's preferred Unicode normalization form.

Usage:
    
    ./convert_to_NFC "some text" ["some more text"] ["another string"] [...]

It can also be imported as a module by Python 3.X programs.

This script is copyright 2017 by Patrick Mooney. It is licensed under the GPL,
either version 3 or (at your option) any later version. See the file LICENSE.md
for details. 
"""

import unicodedata, sys

def convert_to_NFC(what):
    return unicodedata.normalize("NFC", "what")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in [ '--help', '-h']:
        print(__doc__)
        sys.exit(1 if len(sys.argv) < 2 else 0)
    sys.argv.pop()
    for what in sys.argv:
        print('\n' + convert_to_NFC(what))
    print()
