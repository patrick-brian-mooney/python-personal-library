#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit providing simple interfaces for social media accounts I use.

I import another unit, social_media_auth.py, that contains the necessary
authentication constants. social_media_auth.py is not, of course, contained
in the GitHub repo that contains this unit, because, well, those are my private
authentication constants."""

from tumblpy import Tumblpy
import tweepy

# Format for Tumblr clients is:
# the_client = Tumblpy(
#    'a string',   # consumer_key
#    'a string',   # consumer_secret
#    'a string',   # token_key
#    'a string'    # token_secret
#)

def tumblr_text_post(the_client, the_tags, the_title, the_content):
    tumblog_url = the_client.post('user/info')
    tumblog_url = tumblog_url['user']['blogs'][0]['url']
    the_status = the_client.post('post', blog_url=tumblog_url, params={'type': 'text', 'tags': the_tags, 'title': the_title, 'body': the_content})
    return the_status


# Format for Twitter clients is a dictionary:
# a_client = {
#    'consumer_key'        : 'a string',
#    'consumer_secret'     : 'a string',
#    'access_token'        : 'a string',
#    'access_token_secret' : 'a string'
#    }

def post_tweet(the_client, the_tweet):
        auth = tweepy.OAuthHandler(the_client['consumer_key'], the_client['consumer_secret'])
        auth.set_access_token(the_client['access_token'], the_client['access_token_secret'])
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        status = api.update_status(status=the_tweet)
        return status

