#!/usr/bin/env python3
"""Produces a declaration of the contents of my website, as described at
http://patrickbrianmooney.nfshost.com/~patrick/feeds/geographical-surveys/"""

import requests, time, datetime, uuid, html, bz2, subprocess

import searcher         # https://github.com/patrick-brian-mooney/personal-library/blob/master/searcher.py

local_website_root = '/website-root'
description_file = 'site_survey_description.txt'
survey_directory = '/~patrick/feeds/geographical-surveys/'

remote_website_root = 'http://patrickbrianmooney.nfshost.com'
IA_save_prefix = 'http://web.archive.org/save/'

skip_strings_list = ['.git', '.thumbnails']

def tz_offset():
    return abs(int(round((datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds())) / 3600)

def IA_archive(files_list):
    """Get the Internet Archive to save all of the files in FILES_LIST."""
    for which_page in files_list:                                   # Request a URL that causes the Internet Archive to archive the page in question
        req = requests.get(IA_save_prefix + which_page)
        for the_item in req.iter_content(chunk_size=100000): pass   # read the file to make the IArchive archive it.
        time.sleep(3)

def GPG_sign_file(which_file):
    subprocess.check_output(['gpg --detach-sign %s' % which_file ], shell=True)

def produce_feed(files_list):
    """Produce the Atom XML feed."""
    short_date = datetime.date.today().strftime('%d %B %Y')
    ISO8601_date = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S-0' + str(int(round(tz_offset()))) + ':00' )
    two_digit_year = datetime.datetime.now().strftime('%y')
    eight_digit_date = datetime.date.today().strftime('%Y%m%d')

    the_feed = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">

  <title>Geographical Site Survey, %s: Patrick Brian Mooney's site</title>
  <link href="http://patrickbrianmooney.nfshost.com/~patrick/" />
  <updated>%s</updated>

  <author>
    <name>Patrick Brian Mooney</name>
    <uri>http://patrickbrianmooney.nfshost.com/~patrick/</uri>
  </author>
  <link rel="self" href="http://patrickbrianmooney.nfshost.com/~patrick/feeds/geographical-surveys/%s.xml.bz2" />
  <generator uri="https://github.com/patrick-brian-mooney/personal-library/blob/master/site_survey.py" version="0.1">Patrick's geographical site survey script</generator>
  <icon>http://patrickbrianmooney.nfshost.com/~patrick/icons/gear.png</icon>
  <rights>© 2015–%s Patrick Brian Mooney</rights>
  <id>urn:uuid:%s</id>
  <subtitle>A listing of all files on Patrick Brian Mooney's personal web site as of %s; also, a summary of site contents.</subtitle>

  <entry>
    <title>Site Survey</title>
    <id>urn:uuid:%s</id>
    <updated>%s</updated>
""" % (short_date, ISO8601_date, eight_digit_date, two_digit_year, uuid.uuid4(), short_date, uuid.uuid4(), ISO8601_date)
    
    for the_file in files_list:
        the_feed = the_feed + '    <link rel="related self" href="%s" />\n' % requests.utils.quote(the_file)
    
    the_feed = the_feed + """    <content type="html">
""" + html.escape(open(description_file).read())
    
    the_feed = the_feed + """
    </content>
  </entry>

</feed>
"""
    bzipped_feed = bz2.compress(the_feed.encode(), compresslevel=9)
    feed_location = '%s/%s.xml.bz2' % (survey_directory, eight_digit_date)
    with open(feed_location, 'wb') as the_atom_file:
        the_atom_file.write(bzipped_feed)
    GPG_sign_file(feed_location)

if __name__ == "__main__":
    local_files = searcher.get_files_list(local_website_root, skip_strings_list)
    remote_files = [ the_item.replace(local_website_root, remote_website_root) for the_item in local_files ]
    
    produce_feed(remote_files)
    IA_archive(remote_files)
    
    print("\n\n\nWE'RE DONE! Don't forget to update the site survey web page and survey list feed.")
