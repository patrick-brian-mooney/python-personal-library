#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patrick_logger.py is a simple multi-verbosity-level logger for when the
standard library module is way more than needed. Several of my scripts
depend on this module.

GPL v3+ at your option. No guarantees or representations of fitness or
warranties apply. This is free software; you're getting more than you paid
for. More info in the file LICENSE.md.

Nevertheless, I'd love to hear suggestions or feedback if anything occurs to
you.

http://patrickbrianmooney.nfshost.com/~patrick/
"""


import sys

import text_handling        # https://github.com/patrick-brian-mooney/python-personal-library/


# Can set the starting level above zero explicitly when debugging.
verbosity_level = 0


class Logger(object):
    "An abstract logger class that encapsulates settings and behavior."
    def __init__(self, name="default logger"):
        """Set up the logger object. Any of these can be changed at any time, if desired."""
        self.output_destination = sys.stdout
        self.width = text_handling.terminal_width()
        self.name = name
    
    def __del__(self):
        """Clean up. More specifically: close any open files that aren't standard
        streams.
        """
        if self.output_destination not in [sys.stdout, sys.stderr, sys.stdin]:
            self.output_destination.close()

    def log_it(self, message, minimum_level=1):
        """Add a message to the log if the current verbosity_level is at least the minimum_level of the message.
        """
        if verbosity_level >= 6: # set verbosity to at least 6 to get this message output in the debug log
            print("\nDEBUGGING: function log_it() called", file=self.output_destination)
        if verbosity_level >= minimum_level:
            print('\n'.join(text_handling._get_wrapped_lines(message)), file=self.output_destination)

the_logger = Logger()


def log_it(message, minimum_level=1):
    """Convenience function to wrap the automatically created default Logger object."""
    the_logger.log_it(message, minimum_level)
