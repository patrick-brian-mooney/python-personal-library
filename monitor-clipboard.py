#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitor the X clipboard. When it changes, spit out whatever the new contents of
the clipboard are to stdout, from which it can, if necessary, be redirected.

This script relies on the external program XCLIP (try sudo apt-get install xclip
from within Ubuntu or other Debian-based distributions). It is really just a
quick hack, but if you want to, you can use it; it's licensed under the GNU GPL
(either version 3 or, at your option, any later version); see the file
LICENSE.md for details.

This script is copyright 2017-20 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


import time, subprocess, sys

if __name__ == "__main__":
    print("\n\nMonitoring clipboard, press Ctrl-C to quit ...", file=sys.stderr)

    try:
        last_clipboard = ''
        while True:
            try:
                the_contents = subprocess.run('xclip -sel clip -o', shell=True, capture_output=True).stdout.decode()
                if the_contents != last_clipboard:
                    last_clipboard = the_contents
                    print(the_contents)
                    time.sleep(0.2)
            except (subprocess.CalledProcessError, UnicodeDecodeError):
                if last_clipboard:
                    print("WARNING! Unable to read and covert clipboard")
                    last_clipboard = None
    except KeyboardInterrupt:
        print("\nCaught Ctrl-C, quitting ...\n", file=sys.stderr)
