REVISION HISTORY
================

Current version is v1.2, 29 September 2015


v1: 7 October 2015
------------------
Only contains the file "patrick_logger.py", a simple logging module.

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
  * writes a `.csv` file for this mapping.
  * rewrites the `enfuse` bash scripts to use the new names.
* Also, minor changes to `genClassCalendar.py`; this corrects problems with date formatting for hEvent 1.0 microformat.

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

12 February 2016
----------------
* Added `searcher.py`, which has (currently) one list-the-files-in-the-directory function.
* Added `site_survey.py`, which I am currently writing; it produces "[geographical surveys](http://patrickbrianmooney.nfshost.com/~patrick/feeds/geographical-surveys/index.html)" of my site.

13 February 2016
----------------
`site_survey.py` is robust enough that it produced a survey.

20 February 2016
----------------
`poetry_to_prose.py` is more robust: it no longer modifies the list of lines in place, but produces another list as it works.

27 March 2016
-------------
Logic updated in `postprocess_photos` to create an `HDR_components` subdirectory, then have the scripts that are rewritten move ... well, the HDR components ... to that subdirectory. The script is now more self-documenting, too. And there are `spring_forward()` and `fall_back()` routines that are never run when the script itself is run from the shell; I bet you can guess why I've needed these recently. There is also now a `--pythonhelp` command-line option recognized that spits out a bit of info about using the script as a Python 3 module.

29 March 2016
-------------
Added `create_HDR_scripts.py` to the library, because a series of stupid mistakes cause me to accidentally erase all of the HDR scripts, and their backups, for the first folder (`/home/patrick/Photos/2016-03-15/`) of photos from my recent vacation, as I edited and tested a new version of the `postprocess_photos.py` script. `postprocess_photos.py` now imports this script as a module and uses it to create the HDR scripts from basic info in either the enfuse or align+enfuse scripts. `postprocess_photos.py` now also offers to hang around at the end of its run, running any executable scripts it finds. I find this helpful in the case of the recent script deletions to have it do so, then set `create_HDR_scripts.py` as an action in GQView, and using it to create scripts that will automatically by run by the watchful process.

`create_HDR_scripts.py` can be imported as a Python module, which exposes some additional functionality.


17 April 2016
-------------
Updating with minor changes to `create_HDR_script.py` and `postprocess_photos.py`, both of which now support new script `HDR_from_all.py`, a quick hack that just creates an enfuse script for all photos in the current directory, then runs it. `genClassCalendar.py` was updated for spring quarter, and `poetry_to_prose.py` now avoids crashes that used to happen occasionally based on miscounting.

Also, there's now a `create_panorama_script.py` script, which does just what you'd think. It still needs a lot of testing before I'll be happy about it, but it's a step toward automating this rather time-consuming task.

30 April 2016
-------------
`create_panorama_script.py` now creates scripts that end in `-pano.SH`, which should help to prevent them from overwriting existing HDR scripts.

6 May 2016
----------
Rewrote some of the logic in `postprocess_photos.py`: now the "do you want me to hang around?" prompt is part of the main loop, rather than the procedure hang_around(). Also, run_shell_scripts() no longer prints that it's running enfuse scripts; instead, it prints that it's running scripts in a particular directory.

7 May 2016
----------
There's a generic module now, `scripts_runner.py`, containing procedures that search for scripts. Currently, it has one procedure that walks through a specified directory, running an executable *SH files it finds.

8 May 2016
----------
* `postprocess_photos.py` now indicates that it's renaming even before the renaming operation is complete.
* `postprocess_photos.py` now takes a more broadly applicable guess at a time-based filename for photos without any EXIF info.

8 July 2016
-----------
Added `defuseBOM.py`, which removes the BOM from UTF-8 files if it exists (and seems to tolerate BOMless UTF-8, too).

21 July 2016
------------
Expanded `introspection.py` so that it now has a routine `class_methods_in_module`, which is handy for Zombie Apocalypse.


30 August 2016
--------------
* added `run_subfolder_scripts.py`, a quick hack that looks through subfolders of the current folder
  * though not the subfolders of subfolders, etc.
  * it then runs all executable scripts found in those subfolders, then makes them non-executable.

28 September 2016
------------------
* `create_panorama_script.py` now calls `hugin_executor` instead of `PTBatcherGUI`, to save memory.
  * and it comments out the line that calls hugin_executor, because I'm currently generating a lot of new scripts.
* finally adding and committing `run_subfolder_scripts.py`, which I'd previously forgotten to do.

30 September 2016
-----------------
Added `justrunit.py`, a quick silence-output-and-`nohup` wrapper.


6 October 2016
--------------
* Added `tweet.py`, a quick wrapper for other functions to tweet from the command line.
* Fixed a typo in `justrunit.py`.

11 October 2016
---------------
* Added `system-backup.py`, a quick sketch of what I'm doing as I prepare to reinstall a Linux distro.
    * Needs actual testing; I've never run it yet.
    * Need a command-line option to treat something other than the current root as the root so it can be run on a distro not currently running.

14 October 2016
---------------
* Changed `justrunit.py` so it no longer uses `&>` for redirection, which is a `bash`-only convenience synonym.

20 October 2016
---------------
* Fixed (hopefully) a longstanding, low-priority bug in `postprocess_photos.py`.
  * It emerged with photos with no EXIF info, and resulted in gibberishy names.
  * Photos with no EXIF info and whose filenames are also not datetime stamps still have gibberishy-looking names.
    * Really, though, what can you do? If the metadata doesn't exist anywhere, it can't be used, can it?

25 October 2016
---------------
* Fixed a new problem introduced in `postprocess_photos.py` by the 20 Oct fix.
* `tweet.py` now checks, itself, whether tweets are more than 140 characters before trying to post them.
  * It does not take URL shortening, however into account.

23 November 2016
----------------
* A new module, `text_handling.py`, has been created. It's intended to collect some text-handling utilities.
  * Currently, it just has a `print_indented()` function, which breaks lines and keeps padding at the beginning and end of each line.

24 November 2016
----------------
* `text_handling.py` now has some new routines:
  * `terminal_width()`
  * `print_wrapped()`
  * `get_key()`

5 December 2016
---------------
* `text_handling.py` has now abstracted the "split text into separate wrapped lines" routine off.
  * It's now in `_get_indented_lines()`, which just wraps `textwrap.wrap()` with preferred prefs.
  * Other changes in `text_handling.py`:
    * `strip_non_alphanumeric()` does what it sounds like it should. It's a quick convenience filter.
* Rewrote `patrick_logger.py` so that it instantiates a (newly written) `Logger` object.
  * The original interface (the function `log_it()` and the variable `verbosity_level`) is still there.
  * The `Logger` is now wrapping lines (by default, to the width of the process's terminal).
    * This also applies to the default interface.
* There is now a `simple_standard_file.py` that provides quick Open and Save location prompting.
  * Could be handled a little more elegantly, I guess, but it's something.

6 December 2016
---------------
* New file `check_capitalization.py` is now moderately successful and has been added to repo.
  * Plenty of tweaks still needed. It's still pretty basic.
  * It's primarily intended to help preprocess input texts for Ulysses Redux.

7 December 2016
---------------
* Added `multi_choice_menu.py`, a module with a function that prints a menu asking the user to make a choice.
  * It's being worked into `check_capitalization.py`, but that's not yet done. (at 14:36)
  * OK, it seems to be done. (15:23)
  * Additional tweaks.
* Very small changes to small bits of logic in `postprocess_photos.py`.

8 December 2016
---------------
* `check_capitalization.py` has hit a stability point, where it approximately performs predictably.
  * There's still plenty of false negatives, though.
    * Still, it's currently verified all 38 Shakespeare plays that are currently being used by *Ulysses Redux*.
  * Next improvement: work on less clumsy *capitalization* and *capitalization detection* algorithms.
  * Next under-the-hood, substantial improvement: compare capitalization of sentence with capitalization of a truecased version.

9 December 2016
---------------
* `text_handling.py` how has two private functions, `_find_first_alphanumeric()` and `_find_last_alphanumeric()`.
  * Both are intended to help with capitalization functions, which I'll talk about in the next bullet point.
* `text_handling.py` now has two new public functions, `capitalize()` and `is_capitalized()`.
  * `check_capitalization.py` now relies on these functions.

29 December 2016
----------------
* `text_handling.py` now has a new function, `strip_leading_and_trailing_punctuation()`. It does just what it sounds like it does.

1 January 2017
--------------
* added `unpickle_and_dump()` to `introspection.py`.

2 January 2017
--------------
* `print_indented()` and `print_wrapped()` in `text_handling.py` now deal appropriately with embedded newlines.

9 January 2017
--------------
* `text_handling.py` now has a new routine, `multi_replace()`, which continuously makes replacements until the text doesn't change any more.
  * It's imported from [the TrumpTweets project](https://twitter.com/false_trump), which should go live soon.

10 January 2017
---------------
* Added `scripts_caller.py`, a stub to aid in debugging.

9 March 2017
------------
* Added `merge_json.py`, a utility to merge multiple JSON files.

10 March 2017
-------------
* Added `google_photos_to_flickr.py`, a script that will hopefully ease moving my Google photos to Flickr.

7 April 2017
------------
* Added `convert_to_NFC.py`, a script to convert text to Unicode Text Normalization Form C.
  * Which is the w3c's perferred text normalization form for HTML5.

13 April 2017
-------------
* Added `HTML_escape.py`, a quick hack to get HTML-escaped text with entities.

15 April 2017
-------------
* Updated `postprocess_photos.py` so that it correctly writes `file_names.csv` even if the original photo names contain a comma ... which is a problem now that I have an iPhone.
  * Hooray for the Python's `csv` module, which I should have been using consistently already.

18 April 2017
-------------
* Minor tweaks in `text_handling.py`, mostly punctuation.
* Created a `dump_str()` method in `introspection.py` to return the string printed by `dump()` instead of just printing it.
  * Of course, `dump()` is now just a convenience wrapper for `dump_str()`
  
20 April 2017
-------------
* Altering the scripts produced by `create_HDR_script.py`.
  * The scripts created now use `-xyzdivvv` as the arguments to `align_image_stack`.
  * `-m` seems to cause more trouble than it fixes, and I wind up using `-xyzdiv` much of the time anyway when re-running.
  * We'll see how this works.
  
2 May 2017
----------
* Adding another parameter, `delete_originals` (default False), to `create_script_from_file_list()` in `create_HDR_script.py`.
  * This affects the script created. Normally, the original files are moved into the subfolder `HDR_components` after the created script runs.
  * If this parameter is True, the script instead deletes these files after a successful run.
  * All of this is intended to support ...
* Created a new script, `HDR_from_raw`, intended to create an automated HDR tonemapping from a single raw image. It's still pretty rough and not yet done. 

11 May 2017
-----------
* Added `remove_prefix()` to `text_handling.py` to do what I keep wanting `lstrip()` to actually do.
  * That is, it removes a specific string from the beginning of another string, if that other string begins with that specific string.
* `tumblr_text_post()` in `social_media.py` now returns more information. Multiple scripts depending on it have been updated.

16 May 2017
-----------
* Added `monitor-clipboard.py`, a quick hack to collect things that wind up in the X clipboard.

19 May 2017
-----------
* Made some modifications to `patrick_logger.py` and `text_handling.py` to help support using them from Python 2.X.
  * My utility [https://github.com/patrick-brian-mooney/beerxml-to-hrecipe](`BeerXML-to-hRecipe`) currently uses Python 2.X.
    * one of the `pip`-installable modules it requires only runs on the 2.X python line.

5 June 2017
-----------
Splitting off several files into a new project, `photo-processing`:
  * `create_HDR_script.py`
  * `create_panorama_script.py`
  * `HDR_from_all.py`
  * `HDR_from_raw.py`
  * `postprocess_photos.py`

28 June 2017
------------
Added `git_committer.py`, a quick hack that periodically commits archived data to multiple GitHub projects.

10 July 2017
------------
`git_committer.py` modified slightly
  * the `git commit` commands no longer use the `-a` switch
    * ... so known, existing files (e.g., code) are not automatically committed
    * this is intended to prevent in-progress code changes from being committed before they're ready.
  * other minor cosmetic changes   

11 Sept 2017
------------
* `patrick_logger.py` now supports passing in a filename to open a log file at that point.
* It now also supports multiple output streams (files, stdout, stderr) for a single logger object.
* Made output of `git_committer.py` a bit more legible. It now also archives the logs of the `archive_junta` project.

15 Oct 2017
-----------
Updated `check_capitalization.py` to avoid asking if we want to save when no changes have been made.

16 Oct 2017
-----------
Fixed a problem in `text_handling.py`'s `print_indented()` that sometimes caused a line to be printed twice. (Dumb error. Sigh.)

FUTURE PLANS
============
* Continue seeing what I need to do and writing code to do it.

KNOWN BUGS
==========
* No known bugs listed at the moment. However, check individual module files to be sure that I haven't just forgotten to list something here.
