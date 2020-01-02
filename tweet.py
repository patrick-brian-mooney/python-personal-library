#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line interface to function post_tweet() in social_media.py. That is,
this program tweets for me from the command line.

Usage:
    %s "the tweet"

It requires that the appropriate authentication constants are already set up
in social_media_auth.py.

This script is copyright 2017-20 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


import sys

import social_media, social_media_auth  # https://github.com/patrick-brian-mooney/personal-library


if len(sys.argv) <= 1:
    print('\n\n' + __doc__ % sys.argv[0])
    sys.exit(2)

if sys.argv[1] in ['-h', '--help']:
    print('\n\n' + __doc__ % sys.argv[0])
    sys.exit(0)

if __name__ == "__main__":
    the_tweet = ' '.join(sys.argv[1:])
    if len(the_tweet) > 280:
        print("ERROR: Your tweet is %d characters long, which is more than 280." % len(the_tweet))
        sys.exit(1)
    social_media.post_tweet(the_tweet, client_credentials=social_media_auth.personalTwitter_client)
