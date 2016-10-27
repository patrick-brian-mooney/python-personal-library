#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command-line interface to function post_tweet() in social_media.py. That is,
this program tweets for me from the command line.

Usage:
    %s "the tweet"

It requires that the appropriate authentication constants are already set up
in social_media_auth.py.
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
    if len(the_tweet) > 140:
        print("ERROR: Your tweet is %d characters long, which is more than 140." % len(the_tweet))
        sys.exit(1)
    social_media.post_tweet(social_media_auth.personalTwitter_client, the_tweet)