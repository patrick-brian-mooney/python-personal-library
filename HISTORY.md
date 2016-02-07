REVISION HISTORY
================

Current version is v1.2, 29 September 2015


v1: 7 October 2015
------------------
Only contains the file "patrick_logger.py", a simple logging application.

v1.1: 28 December 2015
----------------------
* Small updates to `patrick_logger.py` to make it compatible with Python 3.
* Added files `README.md` and `LICENSE.md`. It's totally, like, a real Git thing now!
* Added `genClassCalendar.py`, a small script to generate vEvent markup for my syllabus every quarter.
* Added `postprocess-photos.py`, a script to automate processing for photos after I offload them from my camera.

9 January 2016
--------------
Primarily, changes to postprocess-photos.py:
      * first, renames photos in EXIF date order, keeping track of old and new names.
      * writes a .csv file for this mapping.
      * rewrites the enfuse bash scripts to use the new names.
* Also, minor changes to genClassCalendar.py; this corrects problems with date formatting for hEvent 1.0 microformat.

21 January 2016
---------------
Reworking existing projects to abstract out some social media-handling code to a new unit in the library, social_media.py.
  * The necessary authentication constants will be kept in yet another unit, which is of course ignored by the GitHub repo for security reasons.
  * Currently, this handles Tumblr text posts, though it will be expanded eventually.
  * As of this date, this affects the following projects: AutoLovecraft; UlyssesRedux; Irish Lit Discourses (but not Irish Lit Tweets: no Twitter yet).

24 January 2016
---------------
Reworked `postprocess_photos.py` to make it a series of functions rather than one long script; this makes life easier for me to pick back up if the script runs partially but fails for some reason (it is, after all, still being developed). Some utility routines have been added to support undoing the renaming of the photos.

31 January 2016
---------------
`postprocess_photos.py` now rewrites ML's enfuse scripts so as to work through an intermedia TIFF instead of producing a JPEG directly; this means that the quality of the resulting JPEG can be controled. It now also copies EXIF info from the first photo in the sequence, which should be the unshifted one.

3 February 2016
---------------
* Add encoding declarations to all files.
* Add `split_file_on_delimiter.py` to the repo.

4 Feburary 2016
---------------
* Added `poetry_to_prose.py` to the repo.
  * it just removes line breaks that don't occur with sentence-ending punctuation, overwriting the old file in the process.

6 February 2016
---------------
Added `introspection.py`, which will eventually contain routines to support that.

FUTURE PLANS
============
* Abstractify the logger interface in `patrick_logger.py`.
* Do pure Python EXIF-based image roatation in `postprocess-photos.py`.

KNOWN BUGS
==========
* No bugs known at the moment.