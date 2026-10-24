#!/usr/bin/env python3
"""Produces a declaration of the contents of my website, as described at
http://patrickbrianmooney.nfshost.com/~patrick/feeds/geographical-surveys/

This script is copyright 2017-20 by Patrick Mooney. It is licensed under the GNU
GPL, either version 3 or (at your option) any later version. See the file
LICENSE.md for details.
"""


import bz2
import collections
import datetime
import functools
import html
import json
import numbers
import random
import requests
import subprocess
import time
import tqdm
import typing
import uuid

from pathlib import Path


LOCAL_WEBSITE_ROOT = Path('/website-root')
SURVEY_DESCRIPTION_FILE = Path('/home/patrick/Documents/programming/python-library/site_survey_description.txt')
URL_ARCHIVE_DATES_CACHE = Path('/home/patrick/Documents/programming/python-library/url_archived_dates.cache')
SURVEY_DIRECTORY = Path('/~patrick/feeds/geographical-surveys/')

REMOTE_WEBSITE_ROOT = 'http://patrickbrianmooney.nfshost.com'
IA_SAVE_PREFIX = 'http://web.archive.org/save/'

skip_strings_list = ['.git', '.thumbnails']


def tz_offset():
    return abs(int(round((datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds())) / 3600)


def read_url_archived_dates_cache() -> typing.Dict[str, float]:
    """Read the file indicating when each URL was last cached and return the contents.
    If the file does not exist or otherwise cannot be read, return an empty
    dictionary. The dictionary maps URLs to the Unix time of when the URL was last
    cached on the Internet Archive by this script
    """
    try:
        with bz2.open(URL_ARCHIVE_DATES_CACHE, mode="rt", encoding='utf-8') as cache_file:
            return json.load(cache_file)
    except (json.JSONDecodeError, OSError, ValueError) as errrr:
        print(f"WARNING: unable to load URL cached-date data! The system said: {errrr}\n")
        print(" Using empty cache...")
        return dict()


def save_url_archived_dates_cache(cache: typing.Dict[str, float]) -> None:
    """Save the URL-cached dates to disk.
    """
    print("\n  Saving URL archived-date data ...")
    try:
        with bz2.open(URL_ARCHIVE_DATES_CACHE, mode='wt', encoding='utf-8') as cache_file:
            json.dump(cache, cache_file, sort_keys=True)
    except (OSError, ValueError) as errrr:
        print(f"  WARNING: unable to save URL cached-date data! The system said: {errrr}")


def archive_single_file(url: str,
                        verbose: bool = True) -> None:
    """Have the Internet Archive store a current copy of this particular file.
    Keep trying until we succeed or until we have no choice but to give up.
    """
    assert isinstance(url, str)

    success = False
    max_tries = 20

    errors = list()
    delay = 10              # delay between attempts, in seconds
    delay_change = 1.5      # factor by which to increase the delay amount after each failure

    if verbose:
        print(f'  INFO: archiving {url}')
        printed_this_url = True
    else:
        printed_this_url = False

    while not success:
        try:
            # Request a URL that causes the Internet Archive to archive the page in question
            urL_to_arch = IA_SAVE_PREFIX + url
            req = requests.get(urL_to_arch)

            # read the file to make the IArchive archive it.
            for _ in req.iter_content(chunk_size=100000):
                pass

            success = True

        except requests.RequestException as errrr:
            print(f"      unable to archive {'' if printed_this_url else 'URL ' + url}; the system said: {errrr}")
            printed_this_url = True
            print(f"      sleeping {delay} seconds and trying again")
            errors.append(errrr)

        except Exception as errrr:
            print(f"      unable to archive {'' if printed_this_url else 'URL ' + url} due to non-networking problem;"
                  f" the system said: {errrr}")
            printed_this_url = True
            print(f"      sleeping {delay} seconds and trying again")
            errors.append(errrr)

        if not success:
            if len(errors) > max_tries:     # Link each error to the next error as the explicit cause of that error
                for i in range(len(errors) - 1, 0, -1):
                    errors[i].__cause__ = errors[i - 1]
                raise RuntimeError(f"Too many consecutive failures to archive {url}!") from errors[-1]

            time.sleep(delay)
            delay *= delay_change

    if verbose or printed_this_url:
        print(f"    ... success!")


def archive_on_ia(files: typing.List[str],
                  max_acceptable_time_distance: typing.Type[numbers.Rational] = 86400,
                  verbose: bool = False):
    """Get the Internet Archive to save all the files in FILES_LIST.
    """
    assert isinstance(files, list)
    assert all([isinstance(f, str) for f in files])

    cache_times = read_url_archived_dates_cache()

    try:
        for count, page in enumerate(tqdm.tqdm(sorted(files))):
            if (time.time() - cache_times.get(page, 0)) <= max_acceptable_time_distance:
                if verbose:
                    print(f"{page} was recently cached! Skipping ...")

            else:
                archive_single_file(page, verbose=verbose)
                cache_times[page] = time.time()

                if (count > 1) and (count % 200 == 0):
                    save_url_archived_dates_cache(cache_times)

                t_sleep = max(random.gauss(3, 2), 1)
                print(f"          sleeping {t_sleep:.4f} seconds")
                time.sleep(t_sleep)

    finally:
        save_url_archived_dates_cache(cache_times)


def gpg_sign_file(which_file: Path):
    """Produce a detached GPG signature to assert that I certify this survey.
    """
    assert isinstance(which_file, Path)
    subprocess.run(['gpg', '--detach-sign', str(which_file)], check=True, capture_output=True)


def produce_feed(url_list: collections.abc.Iterable[str]):
    """Produce the actual Atom XML feed that constitutes the site survey's main data.
    """
    assert isinstance(url_list, collections.abc.Iterable)
    assert all([isinstance(u, str) for u in url_list])

    short_date = datetime.date.today().strftime('%d %B %Y')
    ISO8601_date = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S-0' + str(int(round(tz_offset()))) + ':00' )
    two_digit_year = datetime.datetime.now().strftime('%y')
    eight_digit_date = datetime.date.today().strftime('%Y%m%d')

    the_feed = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">

  <title>Geographical Site Survey, {short_date}: Patrick Brian Mooney's site</title>
  <link href="http://patrickbrianmooney.nfshost.com/~patrick/" />
  <updated>{ISO8601_date}</updated>

  <author>
    <name>Patrick Brian Mooney</name>
    <uri>http://patrickbrianmooney.nfshost.com/~patrick/</uri>
  </author>
  <link rel="self" href="http://patrickbrianmooney.nfshost.com/~patrick/feeds/geographical-surveys/{eight_digit_date}.xml.bz2" />
  <generator uri="https://github.com/patrick-brian-mooney/personal-library/blob/master/site_survey.py" version="0.1">Patrick's geographical site survey script</generator>
  <icon>http://patrickbrianmooney.nfshost.com/~patrick/icons/gear.png</icon>
  <rights>© 2015–{two_digit_year} Patrick Brian Mooney</rights>
  <id>urn:uuid:{uuid.uuid4()}</id>
  <subtitle>A listing of all files on Patrick Brian Mooney's personal web site as of {short_date}; also, a summary of site contents.</subtitle>

  <entry>
    <title>Site Survey</title>
    <id>urn:uuid:{short_date}</id>
    <updated>{ISO8601_date}</updated>
"""

    for the_file in url_list:
        the_feed += f'    <link rel="related self" href="{requests.utils.quote(the_file)}" />\n'

    the_feed += f"""    <content type="html">
{html.escape(open(SURVEY_DESCRIPTION_FILE).read())}
    </content>
  </entry>

</feed>\n"""

    bzipped_feed = bz2.compress(the_feed.encode(), compresslevel=9)
    feed_location = SURVEY_DIRECTORY / f'{eight_digit_date}.xml.bz2'
    with open(feed_location, 'wb') as the_atom_file:
        the_atom_file.write(bzipped_feed)
    gpg_sign_file(feed_location)


@functools.lru_cache(maxsize=None)
def comp_form(t: typing.Hashable) -> str:
    """Calculate and cache the comparison form for T."""
    return str(t).strip().casefold()


def yield_files_recursively(from_where: Path,
                            skip_strings: collections.abc.Iterable[str]) -> collections.abc.Iterator[Path]:
    """Yield all files, one at a time, under FROM_WHERE, including in that directory,
    excluding files that have any text contained in the SKIP_STRINGS collection.
    """
    assert isinstance(from_where, Path)
    assert from_where.is_dir()
    assert isinstance(skip_strings, collections.abc.Iterable)
    assert all([isinstance(f, str) for f in skip_strings])

    for f in from_where.glob('*'):
        if any([comp_form(s) in comp_form(f) for s in skip_strings]):
            print(f"  INFO: skipping {'directory' if f.is_dir() else 'file'} {f}; filtered out by existing skip rules")
        elif f.is_file():
            yield f
        elif f.is_dir():
            yield from yield_files_recursively(f, skip_strings)


if __name__ == "__main__":
    print(f"Beginning run!\n\nScanning files in {LOCAL_WEBSITE_ROOT} ...")
    local_files = sorted(str(f) for f in yield_files_recursively(LOCAL_WEBSITE_ROOT, skip_strings_list))

    print("\nTranslating local file paths to remote URLS ...")
    remote_files = [i.replace(str(LOCAL_WEBSITE_ROOT), REMOTE_WEBSITE_ROOT) for i in local_files]

    print("Done scanning and translating!\n\nProducing site survey ...")
    produce_feed(remote_files)

    print("\n\nSurvey produced! Archiving pages on the Internet Archive ...")
    archive_on_ia(remote_files)

    print("\n\n\nWE'RE DONE! Don't forget to update the site survey web page and survey list feed.")
