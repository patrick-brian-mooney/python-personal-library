#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A quick script that takes a group of photos from Google checkout and uploads
those photos to Flickr. Works as of early March 2017, though it may or may not
have been kept up since then. Though there are plenty of things I don't like
about Google's photo-hosting and the way that its capabilities have shifted
since I started using it around 2008, Google deserves a lot of praise for
making it possible to easily download a user's own data in open formats. This
script is intended to ease the transition to another provider (currently
Flickr, about which I also have reservations, though I currently prefer them to
Google, largely because their photo servers seem to behave better and to take
less extreme measures to prevent users from doing what they want with their
photos other than downloading them).

This script assumes that the Google Takeout archive (or at least the subfolder
of the archive that contains the photos) has been expanded into a folder that
contains a series of subfolders, each of which represents what was an album on
Google Photos. It then tries to process each of these subfolders, uploading the
photos that it contains to Flickr. Since (in my experience) Google Takeout
archives don't have a particularly regular structure, it tries to deal with
this irregular data in at least a semi-robust way.

The Flickr API doesn't expose enough of Flickr's functionality in a documented
way to allow for the script to do all of its work automatically; in particular,
the Flickr API doesn't document a way to create new albums, despite the fact
that they promised to do so "soon" in a forum posting over nine years ago.
Because of this, some supervised work needs to be done: namely, the creation
and arrangement of albums. I deal with this by making sure the script turns the
old album name into a tag, then putting a breakpoint at the end of the album-
uploading procedure. When the script stops running, I go to Flickr, find the
new photos that have the tag in question, and organize them into an album by
hand. It's not perfect, but it seems to be the best I can do for now.

Google is a trademark of Google. Flickr is a trademark of Yahoo!. This script
is copyright 2017 by Patrick Mooney; it is licensed under the GNU GPL version
3 or (at your option) any later version. See the file LICENSE.md for details.
"""


import json, os, glob, urllib.request, shutil

import flickrapi            # [sudo] pip3 install flickrapi or see https://stuvel.eu/flickrapi

import patrick_logger       # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py
from social_media_auth import flickr_api_key as f_a_k   # unshared file where I keep my social media authentication constants


# Set up the Flickr API object. Thanks, Sybren A. Stüvel!
flickr = flickrapi.FlickrAPI(f_a_k['key'], f_a_k['secret'])
if not flickr.token_valid(perms='write'):
    flickr.get_access_token(f_a_k['verifier'])

patrick_logger.verbosity_level = 4


def preprocess_dir(pathname):
    """Goes through the dir PATHNAME, which should be a directory that contains an
    album of Google photos, making sure that the directory is ready to have its
    contents uploaded. Google Photos directories, as of the time of this writing,
    seem to contain the following files:
        * `metadata.json`, which contains metadata about the album itself
        * individual photos, which are:
          1. the actual graphic or movie file (.png, .jpg, .mov, .mp4, .gif, others?)
          2. a .json file giving the graphic/movie file's metadata.

    Currently, "getting a dir ready for upload" means:
        1. Renames "degenerate" to "proper" extensions, e.g. a.jso -> a.json
        2. making sure that every individual-photo-metadata .json file has a
           corresponding image; if not, it attempts to download it.
        3. that's it. Nothing else.
    """
    patrick_logger.log_it('INFO: preprocessing directory: %s' % pathname)
    degenerate_extensions = {'json': ['js', 'jso'],
                             'jpg': ['j', 'jpg_', 'JPG'],
                             }
    olddir = os.getcwd()
    os.chdir(pathname)
    try:
        # first, fix "degenerate" extensions
        for ext in degenerate_extensions:
            for degen in degenerate_extensions[ext]:
                for f in glob.glob('*' + degen):
                    patrick_logger.log_it("INFO: renaming degenerate-extension file %s" % f, 2)
                    os.rename(f, os.path.splitext(f)[0] + '.%s' % ext)
                    try:                    # Also try to rename any metadata for the photo
                        os.rename(f + ".json", os.path.splitext(f)[0] + '.%s.json' % ext)
                    except Exception: pass  # Oh well.

        # now, try to make sure there's an actual graphic file for each metadata file.
        for f in [f for f in glob.glob('*json') if f.strip() != 'metadata.json']:
                image_f = os.path.splitext(f)[0]    # Dropping the .json still leaves us with something ending in .jpg, etc.)
                if not os.path.isfile(image_f):
                    patrick_logger.log_it('INFO: image file %s is missing; downloading ...' % image_f)
                    with open(f) as data_file:
                        data = json.load(data_file)
                    try:
                        with urllib.request.urlopen(data['url']) as response, open(image_f, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)
                    except Exception as e:
                        patrick_logger.log_it('WARNING: cannot download image for metadata file %s; the system said: \n%s' % (f, e), 1)
    except Exception as e:
        patrick_logger.log_it("ERROR: %s" % e, 0)
    finally:
        os.chdir(olddir)
    patrick_logger.log_it('    INFO: done preprocessing directory: %s' % pathname, 2)

def upload_photos(dir):
    """Upload all of the photos in the current directory. If a .json metadata file
    is available, (appropriate) data from it is passed to Flickr.
    """
    olddir = os.getcwd()
    try:
        os.chdir(dir)
        patrick_logger.log_it('INFO: about to upload photos in directory: %s' % dir)
        default_folder_metadata = {'title': os.path.basename(dir)}
        folder_metadata = default_folder_metadata.copy()
        try:    # First, try to rename the folder to the album name
            with open(os.path.join(dir, 'metadata.json')) as json_file:
                data = json.load(json_file)
            folder_metadata.update(data)
            patrick_logger.log_it('    INFO: successfully read album metadata', 3)
            if os.path.basename(dir).strip() != folder_metadata['title'].strip():
                os.rename(dir, os.path.join(os.path.dirname(dir), folder_metadata['title'].strip()))
        except Exception:   # Oh well.
            patrick_logger.log_it('    INFO: cannot read album metadata; using defaults', 2)

        default_data_fields = {'description': '', 'tags': [], 'title': '' }     # Fields that must appear in image file metadata
        image_file_extensions = ['*jpg', '*png', '*gif', '*avi', "*m4v", '*MOV']
        images = [][:]
        for ext in image_file_extensions:
            images.extend(glob.glob(ext))
        for image in sorted(list(set(images))):
            patrick_logger.log_it("    INFO: about to upload image %s" % image)
            try:                                                    # First, get any available metadata
                with open(image + '.json') as json_file:
                    file_data = json.load(json_file)
                json_data = default_data_fields.copy()
                json_data.update(file_data)
                if image.strip() != json_data['title'].strip():     # If the filename doesn't match what the metadata says it should be ...
                    os.rename(image, json_data['title'].strip())    # Rename the file
                    os.rename(image + '.json', json_data['title'].strip() + '.json')    # And its metadata file
                    image = json_data['title'].strip()              # And track the new name instead of the old one
                patrick_logger.log_it('    INFO: successfully read photo metadata', 3)
            except Exception:
                json_data = default_data_fields.copy()
                json_data.update({'title': image})
                patrick_logger.log_it('    INFO: failed to read photo metadata; using defaults', 2)
            try:
                json_data['tags'] = '"%s"' % folder_metadata['title']       # Yes, just the single quoted string. Dump any other tags.
                flickr.upload(filename=image, title=json_data['title'], description=json_data['description'], tags=json_data['tags'])
                patrick_logger.log_it("    INFO: successfully uploaded file", 4)
                os.remove(image)
                try:
                    os.remove(image + '.json')
                except NameError: pass          # If the metadata file doesn't exist, oh well.
            except Exception as e:
                patrick_logger.log_it("    INFO: unable to upload or delete file %s; the system said %s" % (image, e))
    except Exception as e:
        patrick_logger.log_it('ERROR: system said %s' % e)
    finally:
        os.chdir(olddir)


if __name__ == "__main__":
    # Get a (non-recursive) list of all subdirectories of the current directory. Ignore any non-directory files in the current directory.
    for dir in sorted([ d for d in glob.glob('/home/patrick/Desktop/working/to post (Flickr)/Google Albums/*') if os.path.isdir(d) ]):
        preprocess_dir(dir)
        upload_photos(dir)
