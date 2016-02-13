#!/usr/bin/env python3
"""Produces a declaration of the contents of my website, as described at
http://patrickbrianmooney.nfshost.com/~patrick/feeds/geographical-surveys/"""

import requests, time, datetime

import searcher

local_website_root = '/website-root'
remote_website_root = 'http://patrickbrianmooney.nfshost.com'

skip_strings_list = ['.git', '.thumbnails']

def IA_archive(files_list):
    """Get the Internet Archive to save all of the files in FILES_LIST."""
    for which_page in files_list:                                   # Request a URL that causes the Internet Archive to archive the page in question
        req = requests.get('http://web.archive.org/save/' + which_page)
        for the_item in req.iter_content(chunk_size=100000): pass   # read the file to make the IArchive archive it.
        time.sleep(3)

def tz_offset():
    return abs(int(round((datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds())) / 3600)

def produce_feed(files_list):
    the_feed = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">

  <title>Geographical Site Survey, %s: Patrick Brian Mooney's site</title>
  <link href="http://patrickbrianmooney.nfshost.com/~patrick/" />
  <updated>%s</updated>"""
  the_feed += """
  <author>
    <name>Patrick Brian Mooney</name>
    <uri>http://patrickbrianmooney.nfshost.com/~patrick/</uri>
  </author>
  <link rel="self" href="http://patrickbrianmooney.nfshost.com/~patrick/feeds/geographical-surveys/20151006.xml.bz2" />
  <generator uri="http://bluefish.openoffice.nl/download.html" version="2.2.3">Bluefish</generator>
  <icon>http://patrickbrianmooney.nfshost.com/~patrick/icons/gear.png</icon>
  <rights>© 2015&ndash;%s Patrick Brian Mooney</rights>
  <id>urn:uuid:1179447b-b2b8-43e2-9131-0b0f9469156f</id>
  <subtitle>A listing of all files on Patrick Brian Mooney's personal web site as of 6 October 2015; also, a summary of site contents.</subtitle>

  <entry>
    <title>Site Survey</title>
    <id>urn:uuid:3ffecebe-4ece-48ca-8cf2-40512bdd7e4f</id>
    <updated>2015-10-06T19:10:00-08:00</updated>
    """
    
    the_entry = """<link rel="related self" href="http://patrickbrianmooney.nfshost.com/" />
""" % (datetime.date.today().strftime('%d %B %Y'), datetime.date.now().strftime('%d-%m-%YT%H:%M:%S-0') + tz_offset() + ':00', datetime.date.now().strftime('%y'))

if __name__ == "__main__":
    local_files = searcher.get_files_list(local_website_root, skip_strings_list)
    remote_files = [ the_item.replace(local_website_root, remote_website_root) for the_item in local_files ]
    
    IA_archive(remote_files)
