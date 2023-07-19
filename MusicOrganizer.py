#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A script to assist in organizing a directory of unprocessed music files: it
works toward validating basic assumptions about metadata tagging, and organizes
files into a regular directory structure. This is not a particularly
configurable tool in general, though some attention has been paid to basic
configurability.

Basic tasks performed as it traverses the specified directory:

* Pre-scans to find directories with music files.
* Traverses that list of directories, validating that music files found are
  not tagged in inappropriate ways. (Removes a lot of crufty metadata. Asks
  when it doesn't know what to do about a tag type.)
* Moves files into a new, regularized directory structure.

Does not yet, but will:

* convert files to an appropriate format. (Currently skips non-approved media
  file formats).

Currently, most usefully run from within an IDE with appropriate breakpoints so
its behavior can be observed.

This script takes a first pass at the needed work in order to eliminate
drudgery, but is not intended to be a substitute for human oversight in
caring for a file's metadata.

This project and all associated code is copyright 2023 by Patrick Mooney. Code
in this project is licensed under the GPL, either version 3 or (at your option)
any other version. See the file LICENSE.md for details.
"""


import collections
import json
import os

from pathlib import Path

import pprint
import shutil
import typing

import mutagen                      # https://mutagen.readthedocs.io/
from mutagen.id3 import ID3
from mutagen.easyid3 import EasyID3

import tqdm                         # https://tqdm.github.io/

import flex_config as fc            # https://github.com/patrick-brian-mooney/python-personal-library
import file_utils as fu             # same
import multi_choice_menu as mcm     # same
import text_handling as th          # same


# Global variables
default_config = {
    'folder to organize':"/home/patrick/Music/Receiving Bay",
    'folders to skip': ["""/home/patrick/Music/Receiving Bay/00-Incomplete collections""",
                        """/home/patrick/Music/Receiving Bay/00-To Transcode""",],
    'destination': '/home/patrick/Music/Receiving Bay/0xFF - organized',
    'allowed music extensions': ['.mp3',],
    "music extensions to convert": [".flac", ".wma", ".wav", ".ape", ".m4p", ".aa", ".m4a", ".m4b", ".part",],
    "extensions to ignore": [".htm", ".html", ".txt", ".jpg", ".jpeg", ".pdf", ".cue", ".gif", ".png", ".css",
                             ".m3u", ".nfo", ".doc", "", ".js", ".aspx", ".m4v", ".pls", ".vob", ".bmp",
                             ".rtf", ".avi", ".bz2",],
    "extensions to delete": [ ".log", ".log", ".ini", ".sfv", ".accurip", ".ffp", ".md5", ".url"],
    "allowed frames": ["APIC", "SYLT", "TALB", "TCOM", "TCON", "TDOR", "TDRC", "TDRL", "TFLT", "TIPL", "TIT1",
                       "TIT2", "TIT3", "TKEY", "TLAN", "TLEN", "TMCL", "TOAL", "TOLY", "TOPE", "TPE1", "TPE2",
                       "TPE3", "TPE4", "TPOS", "TPUB", "TRCK", "TSOA", "TSOP", "TSOTTSST", "USLT", "WOAF",
                       "WOAR", "WOAS", "WPUB", "TMED", "WXXX", "TBPM", "MCDI", "©DAY", "TEXT",],
    "frames to delete": ["TDTG", "TENC", "TMOO", "TOWN", "TPRO", "TRSN", "TRSO", "TSRC", "TSSE", "UFID",
                         "USER", "WCOM", "WCOP", "WORS", "WPAY", "TSO2", "TXXX", "COMM", "TCOP", "PRIV",
                         "TCMP", "PCNT", "RVA2", "TDEN", "TSST", "POPM",],
}


config = None           # But will be re-assigned soon, below

# Global variables tracking the state of the music-processing operation.
dirs_with_music = set()
unprocessed_dirs = set()


# Some very general utility code.
def _flatten_list(l: typing.Iterable[typing.Any]) -> typing.Generator[typing.Any, None, None]:
    """Emit the non-list (and non-list-like) atoms composing the list L. If L contains
    any lists (or list-like iterables), only the ELEMENTS of those sublists are ever
    emitted, rather than the sublists themselves. No matter how deeply nested L is,
    the yielded atoms will never be lists, but only the atoms of those lists.

    Note that strings (and bytestrings) are explicitly not considered to be "list-
    like iterables," but rather atoms, even though Python treats strings just like
    any other iterable.

    Note that this actually returns a generator expression, not a list, and so
    wrapping it in a list() constructor may be wise in some circumstances.
    """
    for elem in l:
        if isinstance(elem, collections.Iterable) and not isinstance(elem, (str, bytes)):
            for sub in _flatten_list(elem):
                yield sub
        else:
            yield elem


def flatten_list(l: typing.Iterable[typing.Any]) -> typing.List[typing.Any]:
    """Purely a convenience fucntion that wraps _flatten_list in a list() call so that
    it returns a whole list rather than yielding one element at a time.
    """
    return list(_flatten_list(l))


def _files_in_folders_recursively(p: Path) -> typing.Generator[Path, None, None]:
    """A generator that emits each file that is in any subdirectory of P, a Path
    representing a directory. If an all-at-once list of every file under this folder
    is needed, use the no-underscore convenience function with a similar name,
    below.
    """
    assert isinstance(p, Path)
    assert p.is_dir()

    for item in p.glob("*"):
        if item.is_dir():
            yield from _files_in_folders_recursively(item)
        elif item.is_file():
            yield item


def files_in_folders_recursively(p: Path) -> typing.List[Path]:
    """Just a convenience function that produces a list, all at once, from the
    similarly named generator function.
    """
    return list(_files_in_folders_recursively(p))


def rmdir_if_effectively_empty(dir: Path) -> bool:
    """A directory is "effectively empty" if it ...
        * contains no files; and either
        * contains no subdirectories, or
        * contains only subdirectories that are themselves effectively empty.

    This function recursively traverses DIR, a directory, deleting leaf actually
    empty directories under DIR, then crawling back up and deleting directories that
    have been made empty by having their subdirectories deleted. If the function is
    able to empty everything beneath DIR, it removes the now-empty DIR itself and
    returns True. If, at any point, it encounters a file, it stops processing
    immediately and returns False.
    """
    assert isinstance(dir, Path)
    assert dir.is_dir()

    for i in dir.glob('*'):
        if i.is_file():
            return False
        elif i.is_dir():
            if not rmdir_if_effectively_empty(i):
                return False

    if len(list(dir.glob('*'))) == 0:
        dir.rmdir()
        return True


def sanitize_text(text: str) -> str:
    """Takes TEXT, a string and makes it safe to use as a pathname. This means that it
    strips leading/trailing whitespace and removes characters that are not safe to
    use in filenames.
    """
    return th.multi_replace(text.strip(), [['/', '_'], [r"\\", '_']])


def sanitize_path(suggested_name: Path) -> Path:
    """Removes invalid characters from a filename and strips leading/trailing spaces.
    Does not attempt to make a name unique -- use clean_name() for that, which calls
    sanitize_*() as part of its processing.
    """
    return suggested_name.with_name(sanitize_text(suggested_name.name)).with_suffix(suggested_name.suffix)


def clean_name(suggested_name: Path,
               other_dirs_unique: typing.Iterable[Path] = ()) -> Path:
    """Given SUGGESTED NAME, returns a unique Path to a file in the same directory
    specified, but that does not exist and whose name is based on SUGGESTED_NAME.
    If SUGGESTED_NAME does not exist, appends (1), (2), (3) ... to SUGGESTED NAME
    until it finds a unique name. Keeps the same prefix as SUGGESTED_NAME.

    SUGGESTED_NAME should be a complete Path specification, either relative to the
    current working directory, or else a fully resolve absolute Path.

    OTHER_DIRS_UNIQUE, if specified, is an iterable of Paths representing
    directories. The generated clean name will also be unique relative to these
    other directories as well as relative to the directory represented in the
    SUGGESTED_NAME Path.
    """
    assert isinstance(suggested_name, Path)
    assert all([isinstance(d, Path) for d in other_dirs_unique])
    assert all([d.is_dir() for d in other_dirs_unique])

    new_name, suffix = sanitize_text(suggested_name.stem), suggested_name.suffix
    count = 0
    dirs_to_check = list(other_dirs_unique) + [suggested_name.parent]

    # Vulnerable to race conditions, but what else can we do?
    while True:
        if count:
            new_name = f"{suggested_name.stem} ({count})"
        else:
            new_name = suggested_name.stem

        count += 1
        if not any ([(d / new_name).with_suffix(suffix).exists() for d in dirs_to_check]):
            break

    return suggested_name.with_name(new_name).with_suffix(suffix)


class PathAsStrJSONEncoder(json.JSONEncoder):
    """Store paths as plain strings. They'll be re-interpreted as paths on load.
    """
    def default(self, obj):
        if issubclass(type(obj), Path):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def do_convert_audio(which_files: typing.Iterable[Path]) -> None:
    """Convert WHICH_FILES to the default target audio format.
    """
    print(f"Not converting files {which_files} -- functionality not yet implemented!")          # FIXME


# Set-up and pre-scanning routines.
def set_up() -> None:
    """Do what setup is necessary. This largely involves making sure that prefs keys
    that are supposed to be in non-JSON-serializable formats are in fact in the
    correct formats, and also some sanity checking on the prefs.
    """
    global config

    config = fc.PrefsTracker(appname="MusicOrganizer", defaults=default_config, json_encoder=PathAsStrJSONEncoder)
    config.save_preferences()               # Warn early if we can't write prefs back to disk.

    for key in ('folder to organize', 'folders to skip', 'destination'):
        if isinstance(config[key], typing.Iterable) and not isinstance(config[key], str):
            if any([not issubclass(type(item), Path) for item in config[key]]):
                config[key] = [Path(i).resolve() for i in config[key]]
        elif not issubclass(type(config[key]), Path):
            config[key] = Path(config[key]).resolve()

    # Make absolutely sure we don't accidentally scan the destination folder.
    if config['destination'] not in config['folders to skip']:
        config['folders to skip'].append(config['destination'])

    # Check to make sure the destination folder exists and looks like an actual folder.
    if not config['destination'].exists():
        config['destination'].mkdir(parents=True)
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

        # Found something that can be read with Mutagen.
        # Add this dir to the list of dirs with music, then stop scanning files in this dir.
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
            pprint.pprint(data.getall(key))
        else:
            raise RuntimeError(f"Somehow got an invalid response ({answer}) from menu_choice()!!")
        print('\n\n')


# These next few routines do the actual work of cleaning files, renaming them, and moving them around.
def do_clean_tags(which_file: Path,
                  title: typing.Optional[str] = None,
                  artist: typing.Optional[str] = None,
                  album: typing.Optional[str] = None,
                  albumartist: typing.Optional[str] = None,
                  composer: typing.Optional[str] = None,
                  conductor: typing.Optional[str] = None,
                  author: typing.Optional[str] = None,
                  version: typing.Optional[str] = None,
                  discnumber: typing.Optional[str] = None,
                  tracknumber: typing.Optional[str] = None,
                  language: typing.Optional[str] = None,
                  genre: typing.Optional[str] = None,
                  date: typing.Optional[str] = None,
                  originaldate: typing.Optional[str] = None,
                  performer: typing.Optional[str] = None,
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
        for key in {k[:4].strip().upper() for k in data.tags.keys()}:
            if key in config['frames to delete']:
                data.tags.delall(key)
            elif key not in config['allowed frames']:
                if not ask_about_key(key, which_file, data.tags):        # If key goes onto the 'delete' list ...
                    data.tags.delall(key)

        data.save()

        if any([title, artist, album, albumartist, composer, conductor, author, version, discnumber,
                tracknumber, language, genre, date, originaldate, performer]):
            data = EasyID3(which_file)

            if title: data['title'] = title
            if artist: data['artist'] = artist
            if album: data['album'] = album
            if albumartist: data['albumartist'] = albumartist
            if composer: data['composer'] = composer
            if conductor: data['conductor'] = conductor
            if author: data['author'] = author
            if version: data['version'] = version
            if discnumber: data['discnumber'] = discnumber
            if tracknumber: data['tracknumber'] = tracknumber
            if language: data['language'] = language
            if genre: data['genre'] = genre
            if date: data['date'] = date
            if originaldate: data['originaldate'] = originaldate
            if performer: data['performer'] = performer

            data.save()

    except (IOError, mutagen.MutagenError) as errrr:
        print(f"Could not update {which_file}! The system said: {errrr}")
    except (Exception,) as errrr:
        print(f"Could not update {which_file}! The system said: {errrr}")


def _data_from_easy(data: EasyID3,
                    key: str) -> typing.Union[str, None]:
    """Parses DATA, an EasyID3 tag, to extract KEY, if possible; if it's possible,
    returns the relevant data; otherwise, returns None.
    """
    try:
        ret = data[key]
        if isinstance(ret, str):
            return ret
        elif isinstance(ret, typing.Iterable):
            return ret[0]
    except (KeyError,):
        return None


def title_from_easy(data: EasyID3,
                    f: Path) -> typing.Union[str, None]:
    """Parses DATA, an EasyID3 tag, to try to extract the song title from that data.
    Tries to deal sensibly with problems. Returns None if it absolutely cannot
    figure that out.
    """
    return _data_from_easy(data, 'title')


def artist_from_easy(data: EasyID3,
                     f: Path) -> typing.Union[str, None]:
    """Try to get the artist name for the song represented by DATA. Return that name
    as a string, or else None, if we can't figure it out.
    """
    return _data_from_easy(data, 'artist')


def album_from_easy(data: EasyID3,
                    f: Path) -> typing.Union[str, None]:
    """Try to get the album name for the song represented by DATA. Return that name
    as a string, or else None, if we can't figure it out.
    """
    return _data_from_easy(data, 'album')


def albumartist_from_easy(data: EasyID3,
                          f: Path) -> typing.Union[str, None]:
    """Try to get the album artist name for the song represented by DATA. Return that
    name as a string, or else None, if we can't figure it out.
    """
    return _data_from_easy(data, 'albumartist')


def artist_or_albumartist_from_easy(data:EasyID3,
                                    f: Path) -> typing.Union[str, None]:
    """Try to get the artist name for the song represented by DATA. If that's not
    possible, try getting the album artist instead. If neither is possible, return
    None instead.
    """
    return artist_from_easy(data, f) or albumartist_from_easy(data, f) or None


def trackno_from_easy(data: EasyID3,
                      f: Path) -> typing.Union[str, None]:
    """Try to extract the track number from DATA, an EasyID3 object describing metadata
    for a file; try to deal with the formats it may come in, primarily the
    track-number-slash-total-number-of-tracks common format. If the determination
    cannot be made, return None.
    """
    ret = _data_from_easy(data, 'tracknumber')
    if (not ret) or (not isinstance(ret, (str, int))):
        return None

    if '/' in ret:
        ret = ret[:ret.index('/')]

    try:
        ret = int(ret)
    except (ValueError, TypeError):
        pass

    return f"{ret:02d}"


def year_from_easydata(data: EasyID3,
                       f: Path) -> typing.Union[str, None]:
    """Try to extract the (release, presumably) year from EasyID3 metadata. Tries to
    deal with predictable problems that may occur. Returns a string if it can
    determine the year, or None if that cannot be determined.
    """
    try:
        date = _data_from_easy(data, 'date').strip()
    except (AttributeError,):
        return None             # the None singleton, of course, doesn't have a .strip attribute.

    if len(date) == 4:
        return date
    elif len(date) < 4:
        print(f"Cannot determine date for {trackno_from_easy(data, f)} - {artist_from_easy(data, f)} - "
                      f"{title_from_easy(data, f)}! Malformed data: {data, f}")
        return None

    for sep in ('-', '/'):
        if sep in date:
            components = date.split(sep)
            right_length = [i for i in components if len(i) == 4]
            if right_length:
                return right_length[0]      # pick the first of the right length; best guess.

    return None


def check_if_write_to_tag(frames_to_check: typing.Union[str, typing.Iterable[str]],
                          value: str,
                          which_file: Path) -> bool:
    """A utility function called when the user has manually specified the value for a
    tag; it asks whether the user wants to write the value to the relevant frame in
    the file, and if so, does so. THe user also has the option of also writing the
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

    assert isinstance(frames_to_check, typing.Iterable)
    assert all([isinstance(i, str) for i in frames_to_check])
    assert isinstance(value, str)
    assert isinstance(which_file, Path)
    assert which_file.is_file()

    ret = mcm.menu_choice({'Y': f"Write the metadata to {which_file.name}'s tag",
                           'N': f"Do not write the metadata to {which_file.name}'s tag",
                           '--': '--',
                           'A': f"Write the metadata to {which_file.name}'s tag, and also do the tags of all other"
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


def artist_or_albumartist(data: EasyID3,
                          f: Path) -> typing.Union[str, None]:
    """Gets an artist, or album artist, preferentially from ID3 data, but trying
    several other things if that's not available. Only returns None if everything,
    including asking the user, fails to turn up useful information.
    """
    ret = artist_or_albumartist_from_easy(data, f)
    if ret:
        return ret

    rel_path = fu.relative_to(config['folder to organize'], f)
    parts = {i for i in rel_path.parts if i}
    known_artists = {i.name.strip().casefold() for i in config['folder to organize'].glob('*') if i.is_dir()}
    known_artists |= {i.name.strip().casefold() for i in config['destination'].glob('*') if i.is_dir()}
    opts = {i.strip().casefold() for i in parts}.intersection(known_artists)
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
                              components: typing.Iterable[typing.Union[typing.Callable[[EasyID3,], typing.Union[str, None]],
                                                                       typing.Iterable[typing.Callable[[EasyID3,], typing.Union[str, None]]]]],
                              ) -> typing.Union[Path, None]:
    """Given F, a path to a music file, try to suggest a new name for that file based on
    the file's metadata, keeping the location within the filesystem and the existing
    suffix. That suggested filename is built from COMPONENTS, an iterable of
    functions that extract a string from EasyID3 metadata. Returns the new Path if
    it's able to construct one, or else None if this turns out to be completely
    impossible.

    The elements of the COMPONENTS iterable can be not only single callables, but
    iterables of callables. In this case, each callable in that second-level
    iterable is called sequentially for the given data until one of them returns a
    non-Falsey result, which is the result of the whole iterable of callables. Once
    a non-Falsey result is returned, no more callables in that sub-iterable will be
    invoked.

    For instance, if the COMPONENTS iterable consists of
        (trackno_from_easy, (artist_from_easy, albumartists_from_easy),
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
        data = EasyID3(f)
    except (Exception, ) as errrr:
        print(f"Cannot read metadata for file {f.name}! The system said: {errrr}.")
        return

    for item in components:
        if not isinstance(item, typing.Iterable):
            item = [item]
        for func in item:
            try:
                new = sanitize_text(func(data, f))
                if not new:
                    continue

                if ret:
                    ret += " - "
                ret += new
                break
            except (Exception, ) as errrr:
                pass

    return sanitize_path(f.with_name(ret.strip()).with_suffix(f.suffix))


def most_common_answer(music_files: typing.Iterable[Path],
                       data_getter: typing.Callable[[EasyID3], typing.Union[str, None]],
                       exclude_falsey: bool = True) -> typing.Union[str, None]:
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
    assert isinstance(music_files, typing.Iterable)
    assert all([isinstance(i, Path) for i in music_files])
    assert isinstance(data_getter, typing.Callable)

    data = list()
    for f in music_files:
        try:
            data.append(data_getter(EasyID3(f), f))
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


def album_by_artist_filename(f: Path) -> typing.Union[Path, None]:
    """Given F, a Path to a music file, tries to scan the file's metadata and generate
    a new name for the file of the form [track #] - [Artist] - [Song title].suffix.
    """
    return _filename_from_components(f, (trackno_from_easy, artist_from_easy, title_from_easy))


def album_by_artist_folder_structure(year: typing.Optional[str] = None,
                                     artist: typing.Optional[str] = None,
                                     album: typing.Optional[str] = None) -> typing.Union[Path, None]:
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


def process_collection(music_files: typing.Set[Path],
                       non_music_files: typing.Set[Path],
                       parent_dir: Path,
                       filename_generator: typing.Callable[[Path,], typing.Union[Path, None]],
                       dirname_generator: typing.Callable[[typing.Iterable[Path],], typing.Union[Path, None]],
                       ) -> bool:
    """A folder-processing routine that takes the relevant file lists and processes
    the files, ultimately moving cleaned music files and (untouched) all other files
    into the relevant new directory.
    """
    assert isinstance(parent_dir, Path)
    assert isinstance(music_files, set)
    assert isinstance(non_music_files, set)
    assert all([isinstance(i, Path) for i in music_files])
    assert all([isinstance(i, Path) for i in non_music_files])

    music_files = {f: f.stat() for f in music_files}    # stash os.stat() info that will be needed later, before making changes

    dir = dirname_generator(music_files)

    target_dir = config['destination'] / dir
    if target_dir.exists() and target_dir.is_dir() and not target_dir.parent.samefile(config['destination']):
        # Let dirs that are subdirectories at the top level beneath the destination accumulate multiple albums.
        target_dir = clean_name(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    for f in sorted(music_files):
        do_clean_tags(f)
        new_name = sanitize_path(filename_generator(f))

        while (target_dir / new_name.name).exists():
            new_name = clean_name(new_name, [target_dir])

        if new_name.exists() and new_name.samefile(f):  # Did we just re-generate the same name? Nothing to do, then.
            continue

        f.rename(new_name)
        music_files[new_name] = music_files[f]  # OK to modify music_files, we're iterating over a derivative iterable
        del music_files[f]                      # ditto

    # OK. We've got a destination directory, and files ready to move into it. Let's do this.
    for f, st_info in music_files.items():
        if f.is_file():                             # move all files, music or otherwise
            dest = shutil.move(str(f), str(target_dir))         # shutil.move chokes on Paths for Pythons < 3.9.
            os.utime(dest, (st_info.st_atime, st_info.st_mtime))       # maintain access/modified times after moving
        elif f.is_dir():                                            # move only non-empty directories
            if files_in_folders_recursively(f):                 # ignore empty folders
                shutil.move(str(f), str(target_dir))                # shutil.move() chokes on Paths for Pythons < 3.9.


def process_as_album_by_artist(music_files: typing.Iterable[Path],
                               non_music_files: typing.Iterable[Path],
                               parent_dir: Path) -> bool:
    """Convenience wrapper for process_collection, filling in some parameters.
    """
    def dirname_generator(files: typing.Iterable[Path]) -> typing.Union[Path, None]:
        """Convenience wrapper to avoid one hell of a lambda.
        """
        return album_by_artist_folder_structure(year=most_common_answer(files, year_from_easydata),
                                                artist=most_common_answer(files, artist_from_easy),
                                                album=most_common_answer(files, album_from_easy))
    return process_collection(music_files=music_files, non_music_files=non_music_files, parent_dir=parent_dir,
                              filename_generator=album_by_artist_filename,
                              dirname_generator=dirname_generator)


def grab_bag_filename(f: Path) -> typing.Union[Path, None]:
    """Given F, a Path to a music file, tries to scan the file's metadata and generate
    a new name for the file of the form [track #] - [Artist] - [Song title].suffix.
    """
    return _filename_from_components(f, (artist_or_albumartist_from_easy, album_from_easy,
                                         trackno_from_easy, title_from_easy))


def grab_bag_dirname(files: typing.Iterable[Path]) -> typing.Union[Path, None]:
    """Get the directory in which FILES should be dumped after cleaning.
    """
    try:
        return Path(most_common_answer(files, artist_or_albumartist))
    except (TypeError,) as errrr:
        return None


def process_as_grab_bag(music_files: typing.Iterable[Path],
                        non_music_files: typing.Iterable[Path],
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

    if rmdir_if_effectively_empty(p):
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
        do_convert_audio([f for f in p.glob('*') if f.suffix in all_exts_in_dir.intersection(set(config['music extensions to convert']))])
        print(f"The following files need to be converted: {set(f.name for f in p.glob('*') if f.suffix in all_exts_in_dir.intersection(set(config['music extensions to convert'])))}")
        return      # For now, we just don't process directories containing unendorsed audio types.         #FIXME

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

    artists = set(flatten_list([data['artist'] for data in music_files.values() if ('artist' in data)]))
    album_artists = set(flatten_list([data['albumartist'] for data in music_files.values() if ('albumartist' in data)]))
    albums = set(flatten_list([data['album'] for data in music_files.values() if ('album' in data)]))

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
        print(f"Folder {p} is unprocessed: no strategy for dealing with this collection!")

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
    set_up()
    print(f"\n\nBeginning run; pre-scanning {config['folder to organize']} ...", end="")
    prescan_dir(config['folder to organize'])
    print(" ... finished.")
    process_library()
