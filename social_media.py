#!/usr/bin/env python3
"""Unit providing simple interfaces for social media accounts I use.

Imports another unit, social_media_auth.py, that contains the necessary
authentication constants. social_media_auth.py is not, of course, contained
in the GitHub repo that contains this unit, because, well, those are my private
authentication constants."""

from tumblpy import Tumblpy

def tumblr_text_post(the_client, the_tags, the_title, the_content):
    tumblog_url = the_client.post('user/info')
    tumblog_url = tumblog_url['user']['blogs'][0]['url']
    the_status = the_client.post('post', blog_url=tumblog_url, params={'type': 'text', 'tags': the_tags, 'title': the_title, 'body': the_content})
    return the_status