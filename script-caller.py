#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Just an irregularly-changing script used to call something else to be debugged
in an IDE.

Copyright 2017 by Patrick Mooney. Licensed under the GPL v3+, version to be
chosen by you. See LICENSE.md for details.
"""


import sys, subprocess

import patrick_logger   # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py

if __name__ == "__main__":
    import sentence_generator as sg
    sg.buildMapping(sg.word_list('/TrumpTweets/test.txt'), markov_length=2)
