#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Just an irregularly-changing script used to call something else to be debugged
in an IDE.

Copyright 2017 by Patrick Mooney. Licensed under the GPL v3+, version to be
chosen by you. See LICENSE.md for details.
"""


import patrick_logger       # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py
import text_handling as th  # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py


if __name__ == "__main__":
    if True:
        import social_media as sm
        import social_media_auth as sma



    if False:
        import sentence_generator as sg
        text = sg.process_acronyms("For the U.S.A. The U.S. In the P.M. When it's not the p.m. During the A.M. It is 12 a.m. Who is the V.P.? Mr. Smith is. Dr. Jones wants to be married to Mrs. Guadalupe Gonzales. Ms. Rev. Carazsco lusts after the Hon. J.P. Holding. A fantastic day in D.C. Met with President Obama for first time. Really good meeting, great chemistry. Melania liked Mrs․ O a lot! This is the U.S.A., birthplace of RADAR. Mr. Smith went to Washington. #MAGA It can happen in the a.m. or the p.m. Who is the V.P.?")

    if False:
        import sentence_generator as sg
        starts, the_mapping = sg.buildMapping(sg.word_list('/TrumpTweets/test.txt'), markov_length=2)
        th.print_wrapped(sg.gen_text(the_mapping, starts, markov_length=2, sentences_desired=7, paragraph_break_probability=0.3))

    if True: pass
