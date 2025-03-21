#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A script to assist in organizing a directory of unprocessed music files: it
works toward validating basic assumptions about metadata tagging, and organizes
files into a regular directory structure. This is not a particularly
configurable tool in general, though some attention has been paid to basic
configurability.

Basic tasks performed as it traverses the specified directory:

* Pre-scans to find directories with music files.

* Converts certain audio files to an approved format.
  * Currently, these formats are:
        .flac, .wma, .wav, .ape, .m4p, .aa,  .m4b, .part

* Traverses that list of directories, validating that music files found are
  not tagged in inappropriate ways. (Removes a lot of crufty metadata. Asks
  when it doesn't know what to do about a tag type.)

* Moves files into a new, regularized directory structure.

Does not yet, but will:

* convert other audio files to an appropriate format. (Currently skips
  directories with non-approved media file formats).

Currently, most usefully run from within an IDE with appropriate breakpoints so
its behavior can be observed.

This script takes a first pass at the needed work in order to eliminate
drudgery, but is not intended to be a substitute for human oversight in
caring for a file's metadata. There are plenty of good reasons to run it in
a debugger, setting breakpoints to watch what it's doing as it goes about its
business.

This project and all associated code is copyright 2023 by Patrick Mooney. Code
in this project is licensed under the GPL, either version 3 or (at your option)
any other version. See the file LICENSE.md for details.
"""


import collections
import os

from pathlib import Path

import shutil

from typing import Callable, Iterable, Optional, Set, Union

import mutagen                      # https://mutagen.readthedocs.io/
from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4Tags

import tqdm                         # https://tqdm.github.io/

import flex_config as fc            # https://github.com/patrick-brian-mooney/python-personal-library
import file_utils as fu             # same
import multi_choice_menu as mcm     # same
import music_file_handling as mfh   # same


# Global variables
default_config = collections.ChainMap({
    'folder to organize':"/home/patrick/Music/Receiving Bay",
    'folders to skip': ["""/home/patrick/Music/Receiving Bay/00-unidentified""",],
    'destination': '/home/patrick/Music/Receiving Bay/0xFF - organized',
    'allowed music extensions': ['.mp3', ".m4a",],
    "music extensions to convert": [".flac", ".wma", ".wav", ".ape", ".m4p", ".aa",  ".m4b", ".part",],
    "extensions to ignore": [".htm", ".html", ".txt", ".jpg", ".jpeg", ".pdf", ".cue", ".gif", ".png", ".css",
                             ".m3u", ".nfo", ".doc", "", ".js", ".aspx", ".m4v", ".pls", ".vob", ".bmp",
                             ".rtf", ".avi", ".bz2",],
    "extensions to delete": [ ".log", ".log", ".ini", ".sfv", ".accurip", ".ffp", ".md5", ".url"],
    "allowed frames": ["APIC", "SYLT", "TALB", "TCOM", "TCON", "TDOR", "TDRC", "TDRL", "TFLT", "TIPL", "TIT1",
                       "TIT2", "TIT3", "TKEY", "TLAN", "TLEN", "TMCL", "TOAL", "TOLY", "TOPE", "TPE1", "TPE2",
                       "TPE3", "TPE4", "TPOS", "TPUB", "TRCK", "TSOA", "TSOP", "TSST", "USLT", "WOAF",
                       "WOAR", "WOAS", "WPUB", "TMED", "WXXX", "TBPM", "MCDI", "©DAY", "TEXT", 'covr', '©wrt', 'TMPO',
                       '©alb', 'tmpo', 'cprt', '©WRT', 'trkn', '©gen', '©day', 'TSOT', '©GEN', 'CPIL', '©ART', 'pgap',
                       'TSST', 'PGAP', 'disk', 'geID', 'stik', '©nam', 'aART', '©lyr', 'cpil', ],
    "frames to delete": ["TDTG", "TENC", "TMOO", "TOWN", "TPRO", "TRSN", "TRSO", "TSRC", "TSSE", "UFID",
                         "USER", "WCOM", "WCOP", "WORS", "WPAY", "TSO2", "TXXX", "COMM", "TCOP", "PRIV",
                         "TCMP", "PCNT", "RVA2", "TDEN", "TSST", "POPM", 'purd', 'akID', 'SOAA', 'apID', 'sfID',
                         '----', '©too', 'cnID', 'plID', 'atID', 'flvr', 'cmID', 'soaa', 'rtng', 'soar',],
}, mfh.default_config)


config = None           # But will be re-assigned soon, below

# Global variables tracking the state of the music-processing operation.
dirs_with_music = set()
unprocessed_dirs = set()


# Set-up and pre-scanning routines.
def set_up() -> None:
    """Do what setup is necessary. This largely involves making sure that prefs keys
    that are supposed to be in non-JSON-serializable formats are in fact in the
    correct formats, and also some sanity checking on the prefs.
    """
    global config

    config = fc.PrefsTracker(appname="MusicOrganizer", defaults=default_config, json_encoder=fu.PathAsStrJSONEncoder)
    config.save_preferences()               # Warn early if we can't write prefs back to disk.

    for key in ('folder to organize', 'folders to skip', 'destination'):
        if isinstance(config[key], Iterable) and not isinstance(config[key], str):
            if any([not issubclass(type(item), Path) for item in config[key]]):
                config[key] = [Path(i).resolve() for i in config[key]]
        elif not issubclass(type(config[key]), Path):
            config[key] = Path(config[key]).resolve()

    # Make absolutely sure we don't accidentally scan the destination folder.
    if config['destination'] not in config['folders to skip']:
        config['folders to skip'].append(config['destination'])

    # Check to make sure the destination folder exists and looks like an actual folder.
    config['destination'].mkdir(parents=True, exist_ok=True)
    assert config['destination'].exists(), f"Could not create {config['destination']} !!!"
    assert config['destination'].is_dir(), f"{config['destination']} seems to exist, but is not a folder!"

    config.save_preferences()


def prescan_dir(which_dir: Path) -> None:
    """Iterate over the objects in WHICH_DIR, handling them appropriately. What
    it means to "handle appropriately" differs depends on the objects encountered:
    files get examined, other directories get recursively scanned.
    """
    assert isinstance(which_dir, Path)
    assert which_dir.is_dir()
    global dirs_with_music

    which = which_dir.resolve()

    if which in config['folders to skip']:
        return

    for i in (f for f in which.glob('*') if f.is_file()):
        try:
            f = mutagen.File(i)
        except Exception as errrr:
            continue

        # If we didn't get back something Falsey, we found something that can be read with Mutagen.
        # Add this dir to the list of dirs with music, then stop scanning files in this dir.
        if f:
            dirs_with_music.add(which)
            break

    for i in (f for f in which.glob("*") if f.is_dir()):
        if i.is_dir():
            prescan_dir(i)


# Now some utilities to deal with interacting with the user.
def ask_about_extension(ext: str) -> None:
    """Ask the user how to handle file extension EXT. Remember the answer.
    """
    print(f"\nExtension {ext} is unknown!\n")
    ext = ext.strip().casefold()

    answer = mcm.menu_choice(choice_menu={
        'A': 'music file in an allowed format',
        'C': 'music file in a format that must be converted',
        'N': 'non-music file',
        'D': 'file type to always delete when encountered',
        '--': '--',
        'I': 'ignore the fact that this extension exists and ask again next time',
    }, prompt=f"How to treat unknown file extension '{ext}'?").strip().casefold()

    if answer == "a":
        config['allowed music extensions'].append(ext)
    elif answer == "c":
        config['music extensions to convert'].append(ext)
    elif answer == 'n':
        config['extensions to ignore'].append(ext)
    elif answer == "d":
        config['extensions to delete'].append(ext)

    config.save_preferences()


def ask_about_key(key: str,
                  which_file: Path,
                  data:ID3) -> bool:
    """Ask the user whether ID3 tags of type KEY should be allowed in music files.
    If the user says "yes," remember this response, and return True. If the user
    says "no," remember this response, and return False. Also allow the user to
    say "skip this decision for now," and returns True (i.e., allows the tag to
    remain in the file, but doesn't record a "yes" preference).

    Returns True if the key is allowed to remain in the file for now, or False if
    the key needs to be deleted.
    """
    while True:
        answer = mcm.menu_choice(choice_menu={
            'Y': f'allow tag frames of type {key.strip().upper()}',
            'N': f'always remove tag frames of type {key.strip().upper()}',
            'I': f'allow the {key.strip().upper()} data to remain in {which_file.name}, and ask again next time we encounter this tag',
            'R': f'remove the {key.strip().upper()} data from {which_file.name}, and ask again next time we encounter this tag',
            '--': '--',
            'S': f'Show the data associated with tag {key.upper().strip()} in {which_file.name}',
            }, prompt=f"How to treat data frame of type {key.strip().upper()} in file {which_file.name}?").strip().casefold()

        if answer == "y":
            config['allowed frames'].append(key)
            config.save_preferences()
            return True
        elif answer == "n":
            config['frames to delete'].append(key)
            config.save_preferences()
            return False
        elif answer == "i":
            return True
        elif answer == 'r':
            return False
        elif answer == "s":
            mfh.print_tags(data, key)
        else:
            raise RuntimeError(f"Somehow got an invalid response ({answer}) from menu_choice()!!")
        print('\n\n')


def check_if_write_to_tag(frames_to_check: Union[str, Iterable[str]],
                          value: str,
                          which_file: Path) -> bool:
    """A utility function called when the user has manually specified the value for a
    tag; it asks whether the user wants to write the value to the relevant frame in
    the file, and if so, does so. The user also has the option of also writing the
    value to the relevant frame of every music file in an allowable format in the
    same directory, non-recursively.

    FRAMES_TO_CHECK is an iterable of which frames the user might want to write this
    info to; if it contains multiple options, the user will be asked to choose one.
    (If it contains just one item, the choice is made automatically.) VALUE is the
    value to write to teh relevant frame(s). WHICH_FILE is the file to write the
    data to.

    Returns True if at least one frame was written to at least one file, or False
    otherwise.
    """
    if isinstance(frames_to_check, str):
        frames_to_check = [frames_to_check]

    assert isinstance(frames_to_check, Iterable)
    assert frames_to_check      # e.g., not an empty iterable.
    assert all([isinstance(i, str) for i in frames_to_check])
    assert isinstance(value, str)
    assert isinstance(which_file, Path)
    assert which_file.is_file()

    ret = mcm.menu_choice({'Y': f"Write the metadata to {which_file.name}'s tag",
                           'N': f"Do not write the metadata to {which_file.name}'s tag",
                           '--': '--',
                           'A': f"Write the metadata to {which_file.name}'s tag, and also to the tags of all other "
                                f"audio files in allowable formats in the same directory"},
                          prompt=f"Write the updated metadata to the {' or '.join([i.upper() for i in frames_to_check])} frame for {which_file.name}?").casefold().lower()

    if ret == "n":
        return False

    if ret == "a":
        files = [i for i in which_file.parent.glob('*') if i.suffix in config['allowed music extensions']]
    else:
        files = [which_file]

    if len(frames_to_check) > 1:
        frame = mcm.easy_menu_choice(frames_to_check, f"Which frame do you want to write the data {value.upper()} to?")
    else:
        frame = frames_to_check[0]

    for f in files:
        do_clean_tags(f, **{frame: value})

    return True


# These next few routines do the actual work of cleaning files, renaming them, and moving them around.
def do_clean_tags(which_file: Path,
                  title: Optional[str] = None,
                  artist: Optional[str] = None,
                  album: Optional[str] = None,
                  albumartist: Optional[str] = None,
                  composer: Optional[str] = None,
                  conductor: Optional[str] = None,
                  author: Optional[str] = None,
                  version: Optional[str] = None,
                  discnumber: Optional[str] = None,
                  tracknumber: Optional[str] = None,
                  language: Optional[str] = None,
                  genre: Optional[str] = None,
                  date: Optional[str] = None,
                  originaldate: Optional[str] = None,
                  performer: Optional[str] = None,
                  ) -> None:
    """Clean tags from the .mp3 or other authorized files. Keeps and updates a list of
    allowed and disallowed tags. Removes disallowed tags. Queries the user about
    new tags it encounters.

    If ARTIST, ALBUM, TITLE, and/or ALBUM_ARTIST are specified, they are set; if
    they are None, this function leaves them alone. Same is true for the other
    (selected) EasyID3 tags in the function header.

    Saves the updated file to disk after making any modifications.
    """
    assert isinstance(which_file, Path)

    try:
        data = mutagen.File(which_file)
        for key in {k[:4].strip() for k in data.tags.keys()}:
            if key in config['frames to delete']:
                mfh.del_tags(data.tags, key)
            elif key not in config['allowed frames']:
                if not ask_about_key(key, which_file, data.tags):        # If key goes onto the 'delete' list ...
                    mfh.del_tags(data.tags, key)

        data.save()

        if any([title, artist, album, albumartist, composer, conductor, author, version, discnumber,
                tracknumber, language, genre, date, originaldate, performer]):
            data = mfh.easy_from(which_file)

            if title: data.tags['title'] = title
            if artist: data.tags['artist'] = artist
            if album: data.tags['album'] = album
            if albumartist: data.tags['albumartist'] = albumartist
            if composer: data.tags['composer'] = composer
            if conductor: data.tags['conductor'] = conductor
            if author: data.tags['author'] = author
            if version: data.tags['version'] = version
            if discnumber: data.tags['discnumber'] = discnumber
            if tracknumber: data.tags['tracknumber'] = tracknumber
            if language: data.tags['language'] = language
            if genre: data.tags['genre'] = genre
            if date: data.tags['date'] = date
            if originaldate: data.tags['originaldate'] = originaldate
            if performer: data.tags['performer'] = performer

            data.save()

    except (IOError, mutagen.MutagenError) as errrr:
        print(f"Could not update {which_file}! The system said: {errrr}")
    except (Exception,) as errrr:
        print(f"Could not update {which_file}! The system said: {errrr}")


def most_common_answer(music_files: Iterable[Path],
                       data_getter: Callable[[Path], Union[str, None]],
                       exclude_falsey: bool = True,
                       ) -> Union[str, None]:
    """Apply the DATA_GETTER function to the EasyID3 data from each file in
    MUSIC_FILES, then return the answer most frequently provided by the function.
    In the case of ties, it just picks one. If EXCLUDE_FALSEY is True (the default),
    then frequencies for Falsey answers are discounted in determining the "winner."

    Returns None if none of MUSIC_FILES provides an answer to the question
    DATA_GETTER encodes, or if the answer cannot be determined for any other reason.

    This function is useful to, for instance, determine which album a group of files
    in a folder was ripped from: most_common_answer(files, album_from_easy) will
    find the album that the largest number of files in a folder think they belong to.
    """
    assert isinstance(music_files, Iterable)
    assert all([isinstance(i, Path) for i in music_files])
    assert isinstance(data_getter, Callable)

    data = list()
    for f in music_files:
        try:
            data.append(data_getter(mfh.easy_metadata_from(f), f))
        except (Exception,) as errrr:
            pass

    counts = collections.Counter([d for d in data if d])

    ret = counts.most_common(1)
    if (len(ret) < 1) or (len(ret[0]) < 1):
        return None

    ret = ret[0][0]
    while exclude_falsey and counts and not ret:
        del counts[ret]
        ret = counts.most_common(1)[0][0]

    return ret


# More high-level data-getting operations.
def artist_or_albumartist(data: Union[EasyID3, EasyMP4Tags],
                          f: Path) -> Union[str, None]:
    """Gets an artist, or album artist, preferentially from ID3 data, but trying
    several other things if that's not available. Only returns None if everything,
    including asking the user, fails to turn up useful information.
    """
    ret = mfh.artist_or_albumartist_from_easy(data, f)
    if ret:
        return ret

    rel_path = fu.relative_to(config['folder to organize'], f)
    parts = {i for i in rel_path.parts if i}
    known_artists = {i.name.strip() for i in config['folder to organize'].glob('*') if i.is_dir() and i.name.strip()}
    known_artists |= {i.name.strip() for i in config['destination'].glob('*') if i.is_dir() and i.name.strip()}
    opts = {i.strip() for i in parts}.intersection(known_artists)
    if opts:
        if len(opts) == 1:
            ret = list(opts)[0]
            return [i.strip() for i in parts if (i.strip().casefold() == ret.strip().casefold())][0]
        else:
            opts = sorted(opts)
            opts.extend(['--', 'None of these options'])
            ans = mcm.easy_menu_choice(opts, 'Use a containing folder name for the [album] artist? ')
            if ans.strip().casefold() != 'none of these options':
                check_if_write_to_tag(('artist', 'albumartist'), ans, f)
                return ans

    return None


def _filename_from_components(f: Path,
                              components: Iterable[Union[Callable[[Union[EasyID3, EasyMP4Tags],],
                                                                  Union[str, None]],
                                                         Iterable[Callable[[Union[EasyID3, EasyMP4Tags],],
                                                                           Union[str, None]]]]],
                              ) -> Union[Path, None]:
    """Given F, a path to a music file, try to suggest a new name for that file based on
    the file's metadata, keeping the location within the filesystem and the existing
    suffix. That suggested filename is built from COMPONENTS, an iterable of
    functions that extract a string from EasyID3 (or similar) metadata. Returns the
    new Path if it's able to construct one, or else None if this turns out to be
    completely impossible.

    The elements of the COMPONENTS iterable can be not only single callables, but
    iterables of callables. In this case, each callable in that second-level
    iterable is called sequentially for the given data until one of them returns a
    non-Falsey result, which is the result of the whole iterable of callables. Once
    a non-Falsey result is returned, no more callables in that sub-iterable will be
    invoked.

    For instance, if the COMPONENTS iterable consists of
        (trackno_from_easy, (mfh.artist_from_easy, albumartists_from_easy),
         title_from_easy)

    ...then the generated filename would start with the track, if one can be
    determined; followed by the artist, if that can be determined, or else the
    album artist, if that can be determined; followed by the track name, if that can
    be determined.

    Tries to deal gracefully with missing metadata and to avoid clobbering other
    files in the directory.
    """
    assert isinstance(f, Path)
    ret = ''

    try:
        data = mfh.easy_metadata_from(f)
    except (Exception, ) as errrr:
        print(f"Cannot read metadata for file {f.name}! The system said: {errrr}.")
        return

    for item in components:
        if not isinstance(item, Iterable):
            item = [item]
        for func in item:
            try:
                new = mfh.sanitize_text(func(data, f))
                if not new:
                    continue

                if ret:
                    ret += " - "
                ret += new
                break
            except (Exception, ) as errrr:
                pass

    return mfh.sanitize_path(f.with_name(ret.strip()).with_suffix(f.suffix))


def album_by_artist_filename(f: Path) -> Union[Path, None]:
    """Given F, a Path to a music file, tries to scan the file's metadata and generate
    a new name for the file of the form [track #] - [Artist] - [Song title].suffix.
    """
    return _filename_from_components(f, (mfh.trackno_from_easy, mfh.artist_from_easy, mfh.title_from_easy))


def album_by_artist_folder_structure(year: Optional[str] = None,
                                     artist: Optional[str] = None,
                                     album: Optional[str] = None) -> Union[Path, None]:
    """Generates a relative Path, meant to be created underneath the destination
    directory, not necessarily unique, not necessarily already existing or not.
    Returns a Path if it can be constructed, or None if that is impossible.
    """
    ret = ""
    if year:
        ret += f"[{year}]"
    if album:
        ret += f" {album}"

    if artist:
        if ret:
            return Path(artist) / ret
        else:
            return None
    else:
        return Path(ret) if ret else None


# Now, the very high-level functions that compose the basic units of the task as a whole.
def process_collection(music_files: Set[Path],
                       non_music_files: Set[Path],
                       parent_dir: Path,
                       filename_generator: Callable[[Path,], Union[Path, None]],
                       dirname_generator: Callable[[Iterable[Path],], Union[Path, None]],
                       ) -> None:
    """A folder-processing routine that takes the relevant file lists and processes
    the files, ultimately moving cleaned music files and (untouched) all other files
    into the relevant new directory.
    """
    assert isinstance(parent_dir, Path)
    assert isinstance(music_files, set)
    assert isinstance(non_music_files, set)
    assert all([isinstance(i, Path) for i in music_files])
    assert all([isinstance(i, Path) for i in non_music_files])

    music_files = {f: f.stat() for f in music_files}            # stash os.stat() info that will be needed later,
    non_music_files = {f: f.stat() for f in non_music_files}    # before making changes

    dir = dirname_generator(music_files)

    target_dir = config['destination'] / dir
    if target_dir.exists() and target_dir.is_dir() and not target_dir.parent.samefile(config['destination']):
        # Let dirs that are subdirectories at the top level beneath the destination accumulate multiple albums.
        target_dir = mfh.clean_name(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    for f in sorted(music_files):
        do_clean_tags(f)
        new_name = mfh.sanitize_path(filename_generator(f))

        while (target_dir / new_name.name).exists():
            new_name = mfh.clean_name(new_name, [target_dir])

        if new_name.exists() and new_name.samefile(f):  # Did we just re-generate the same name? Nothing to do, then.
            continue

        f.rename(new_name)
        music_files[new_name] = music_files[f]  # OK to modify music_files, we're iterating over a derivative iterable
        del music_files[f]                      # ditto

    for i in sorted(non_music_files):
        new_name = mfh.clean_name(i, [target_dir])
        if (new_name.exists()) and new_name.samefile(i):
            continue

        i.rename(new_name)
        non_music_files[new_name] = non_music_files[i]
        del non_music_files[i]

    # OK. We've got a destination directory, and files ready to move into it. Let's do this.
    for f, st_info in (sorted(music_files.items()) + sorted(non_music_files.items())):
        if f.is_file():                             # move all files, music or otherwise
            dest = shutil.move(str(f), str(target_dir))         # shutil.move chokes on Paths for Pythons < 3.9.
            os.utime(dest, (st_info.st_atime, st_info.st_mtime))       # maintain access/modified times after moving
        elif f.is_dir():                                            # move only non-empty directories
            if fu.files_in_folders_recursively(f):                 # ignore empty folders
                shutil.move(str(f), str(target_dir))                # shutil.move() chokes on Paths for Pythons < 3.9.


def process_as_album_by_artist(music_files: Iterable[Path],
                               non_music_files: Iterable[Path],
                               parent_dir: Path) -> bool:
    """Convenience wrapper for process_collection, filling in some parameters.
    """
    def dirname_generator(files: Iterable[Path]) -> Union[Path, None]:
        """Convenience wrapper to avoid one hell of a lambda.
        """
        return album_by_artist_folder_structure(year=most_common_answer(files, mfh.year_from_easydata),
                                                artist=most_common_answer(files, mfh.artist_from_easy),
                                                album=most_common_answer(files, mfh.album_from_easy))
    return process_collection(music_files=music_files, non_music_files=non_music_files, parent_dir=parent_dir,
                              filename_generator=album_by_artist_filename,
                              dirname_generator=dirname_generator)


def grab_bag_filename(f: Path) -> Union[Path, None]:
    """Given F, a Path to a music file, tries to scan the file's metadata and generate
    a new name for the file of the form [track #] - [Artist] - [Song title].suffix.
    """
    return _filename_from_components(f, (mfh.artist_or_albumartist_from_easy, mfh.album_from_easy,
                                         mfh.trackno_from_easy, mfh.title_from_easy))


def grab_bag_dirname(files: Iterable[Path]) -> Union[Path, None]:
    """Get the directory in which FILES should be dumped after cleaning.
    """
    try:
        return Path(most_common_answer(files, artist_or_albumartist))
    except (TypeError,) as errrr:
        return None


def process_as_grab_bag(music_files: Iterable[Path],
                        non_music_files: Iterable[Path],
                        parent_dir: Path) -> bool:
    """Process as a "grab bag" collection, i.e. one where files share artist or album
    artist, but are not from the same album.
    """
    return process_collection(music_files=music_files, non_music_files=non_music_files, parent_dir=parent_dir,
                              filename_generator=grab_bag_filename,
                              dirname_generator=grab_bag_dirname)


# Now comes the core functionality
def do_clean_dir(p: Path) -> None:
    """Do clean-up work on P, a directory. Currently, this means ...

        * removing any empty directories that are subdirectories of P; then
        * removing P, if it is empty; then
        * going up the filesystem towards the path root, removing each empty parent
          directory until it finds one that is not empty.
    """
    assert isinstance(p, Path)
    assert p.is_dir()

    if fu.rmdir_if_effectively_empty(p):
        if not (p.exists() and p.samefile(config['folder to organize'])):   # stop if we reach back up to the start dir.
            if not (p.exists() and p.samefile(p.parent)):                   # also stop at top of file hierarchy.
                do_clean_dir(p.parent)


def process_dir(p: Path) -> None:
    """Process P, an individual directory, in the manner described under
    process_library(), below.
    """
    assert isinstance(p, Path)
    assert p.is_dir()
    global dirs_with_music, unprocessed_dirs

    music_files = dict()        # Filename -> mutagen.FileType
    non_music_files = set()

    # Now, check to see if we need to preprocess any music files.
    # All files are sorted into 1 of 3 categories: allowed music formats, disallowed music formats, and other files.
    # Allowed music formats are passed through to the next stage of the process. Disallowed music formats are
    # converted to .mp3. Non-music files are left alone. File type is determined solely by extension.

    all_known_exts = set(config['allowed music extensions'] + config['music extensions to convert'])
    all_known_exts |= set(config['extensions to ignore'] + config['extensions to delete'])

    all_exts_in_dir = {f.suffix.lower().strip() for f in p.glob('*') if f.is_file()}

    # If we don't yet know what category an extension should be treated as, ask the user.
    for ext in (all_exts_in_dir - all_known_exts):
        ask_about_extension(ext)
        all_known_exts = (set(config['allowed music extensions']) | set(config['music extensions to convert']) | \
                          set(config['extensions to ignore']) | set(config['extensions to delete']))

    if all_exts_in_dir.intersection(set(config['music extensions to convert'])):
        mfh.do_convert_audio([f for f in p.glob('*') if f.suffix in all_exts_in_dir.intersection(set(config['music extensions to convert']))])

    for i in p.glob('*'):
        try:
            if i.is_dir():      # any subdirs we might be interested in are already in are already in dirs_with_music
                continue
            if i.suffix.strip().casefold() in config['extensions to delete']:
                i.unlink()
                continue
            data = mutagen.File(i, easy=True)
            if data:
                music_files[i] = data
            else:
                non_music_files.add(i)
        except Exception as errrr:
            print(f"Cannot process {i}! The system said: {errrr}")
            non_music_files.add(i)

    if not music_files:     # Empty dict shouldn't happen, because we should have already detected problems leading to
        print(f"{p} does not contain any processable music files! Skipping ...")    # it. Check once more
        return              # to be absolutely sure.

    # OK, we have a list of (supported) music files, and list of all other files. Check to see what type
    # of organization we should be imposing on each folder. In order to make that determination, we need to
    # scan some already-existing metadata on the files.

    artists = set(mfh.flatten_list([data['artist'] for data in music_files.values() if ('artist' in data)]))
    album_artists = set(mfh.flatten_list([data['albumartist'] for data in music_files.values() if ('albumartist' in data)]))
    albums = set(mfh.flatten_list([data['album'] for data in music_files.values() if ('album' in data)]))

    cmp_artists = {a.strip().casefold() for a in artists}
    cmp_album_artists = {a.strip().casefold() for a in album_artists}
    cmp_albums = {a.strip().casefold() for a in albums}

    music_files = set(music_files.keys())           # We've used all the data we need from the dict's values.

    # Now, actually process the relevant files
    if (len(cmp_artists) == 1) and ((len(cmp_album_artists) == 0) or (list(cmp_artists)[0] in cmp_album_artists)) and (len(cmp_albums) == 1):
        if len(music_files) < 4:
            process_as_grab_bag(music_files, non_music_files, p)
        else:
            process_as_album_by_artist(music_files, non_music_files, p)
    else:
        print(f"Giving up on figuring out how to process {p}! Treating collection as grab bag.")
        process_as_grab_bag(music_files, non_music_files, p)

    do_clean_dir(p)


def process_library() -> None:
    """Go through the library, processing each folder.

    "To process a folder" means to examine the files in the folder, determining which
    are music files that Mutagen can read, and then to organize the files in that
    directory, cleaning their tags, regularizing their names, and performing any
    other processing that is necessary; and then to move the files in that folder,
    as a group, to a new folder, in the configured output directory.

    Non-media files in the directory are moved to the new directory, too, without
    renaming them or making any attempt to process their contents. The intent is
    that all files in the source folder are moved to the destination folder, with
    the audio files renamed consistently after their metadata is cleaned, and with
    cover images, liner notes, booklet scans, data tracks, and other related files
    simply moved with the albums whose music files they accompany.

    We proceed from longer paths (judged by number of path components, not by string
    length) to shorter paths, because this facilitates the cleaning process we
    perform while going along.
    """
    for p in tqdm.tqdm(sorted(sorted(dirs_with_music), key=lambda i: str(i).count(os.path.sep), reverse=True)):
        process_dir(p)


if __name__ == "__main__":
    print("Setting up for run ...")
    set_up()    # FIXME! Code has been refactored. Should work, but step through a few times on next run.
    print(f"\n\nBeginning run; pre-scanning {config['folder to organize']} ...", end="")
    prescan_dir(config['folder to organize'])
    print(f" ... finished. Identified {len(dirs_with_music)} folders with music")
    process_library()
