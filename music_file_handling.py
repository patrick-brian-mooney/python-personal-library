#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A Python library providing utility functions for dealing with audio files.
The kernel of this librarywas originally written to support MusicOrganizer;
functions have been gathered here instead to make them more generally useful.

This project and all associated code is copyright 2023 by Patrick Mooney. Code
in this project is licensed under the GPL, either version 3 or (at your option)
any other version. See the file LICENSE.md for details.
"""


import collections
import pprint
import shutil
import subprocess

from pathlib import Path
from typing import Any, Generator, Iterable, List, Union


import mutagen                                  # https://mutagen.readthedocs.io/
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4Tags
from mutagen.id3 import ID3
from mutagen.mp4 import MP4Tags


import flex_config as fc                        # https://github.com/patrick-brian-mooney/python-personal-library
import text_handling as th                      # same


default_config = {
    # de-/encoding options.
    'LAME options': ['--replaygain-accurate', '-t', '--id3v2-only', '-V', '2', '-h', '-', ],  # ENcoding opt for .mp3
    'm4a options': ["-i", "pipe:", "-c:a", "aac", "-q:a", "2", ],  # ENcoding for .m4a

    'flac options': ['-cd', ],  # DEcoding opts

    "ffmpeg pre-input options": ['-i', ],  # ffmpeg can often be used as a general decoder
    "ffmpeg post-input options": ['-f', 'wav', '-c:a', 'pcm_s16le', '-ar', '44100', 'pipe:1'],
}


config = fc.PrefsTracker(appname="Python MFHlib music-handling", defaults=default_config)


# General utilities
def _flatten_list(l: Iterable[Any]) -> Generator[Any, None, None]:
    """Emit the non-list (and non-list-like) atoms composing the list L. If L contains
    any lists (or list-like iterables), only the ELEMENTS of those sublists are ever
    emitted, rather than the sublists themselves. No matter how deeply nested L is,
    the yielded atoms will never be lists, but only the atoms of those lists.

    Note that strings (and bytestrings) are explicitly not considered to be "list-
    like iterables," but rather atoms, even though Python treats strings just like
    any other iterable.

    Note that this actually yields items one by one, rather than returning a list,
    and so wrapping it in a list() constructor (or using the convenience function
    no-underscore flatten_list(), below) may be wise in some circumstances.
    """
    for elem in l:
        if isinstance(elem, collections.Iterable) and not isinstance(elem, (str, bytes)):
            for sub in _flatten_list(elem):
                yield sub
        else:
            yield elem


def flatten_list(l: Iterable[Any]) -> List[Any]:
    """Purely a convenience function that wraps _flatten_list in a list() call so that
    it returns a whole list rather than yielding one element at a time.
    """
    return list(_flatten_list(l))


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
               other_dirs_unique: Iterable[Path] = ()) -> Path:
    """Given SUGGESTED NAME, returns a unique Path to a file in the same directory
    specified, but that does not exist and whose name is based on SUGGESTED_NAME.
    If SUGGESTED_NAME does not exist, appends (1), (2), (3) ... to SUGGESTED NAME
    until it finds a unique name. Keeps the same prefix as SUGGESTED_NAME.

    SUGGESTED_NAME should be a complete Path specification, either relative to the
    current working directory, or else a fully resolved absolute Path.

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

    # Vulnerable to race conditions, but what else can we do?
    unique = False
    while not unique:
        if count:
            new_name = suggested_name.stem + " (" + str(count) + ")"
        else:
            new_name = suggested_name.stem

        count += 1

        # First: if new full name we generated exists, it's a conflict if it's not the same file as the suggested name.
        new_full = suggested_name.parent / (new_name + suffix)
        if suggested_name.exists() and new_full.exists():
            if not suggested_name.samefile(new_full):
                continue            # generated name is not unique. Try again by starting from the top of the main loop

        # next, check to see if it's unique relative to the other_dirs_unique directories.
        unique = True
        for f in other_dirs_unique:
            if (f / (new_name + suffix)).exists():
                unique = False
                break

    return new_full


# High-level utilities for handling tags in a format-agnostic way.
def del_tags(data: Union[ID3, MP4Tags],
             key: str) -> None:
    """A function that provides an abstract interface to functionality that deletes
    data of a certain type from a tags structure. Annoyingly, this functionality is
    named different for different types of audio files, so this convenience function
    provides a uniform interface regardless of underlying file type. If the tag
    structure supports multiple tags of the same type, all tags of that type are
    removed.

    DATA is the tag data to operate on. KEY is the key whose information should be
    deleted.
    """
    try:
        assert isinstance(data, ID3)
        data.delall(key)                   # FIXME! Can we just use del data[key], as with MP4?
    except (AssertionError, AttributeError,):
        assert isinstance(data, MP4Tags)
        for which_key in sorted(i for i in data.keys() if i.strip().casefold().startswith(key.strip().casefold())):
            del data[which_key]


def get_tags(data: Union[ID3, MP4Tags],
             key: str) -> List[str]:
    """Returns a list of all tags in DATA matching KEY. If no tags in DATA mach KEY,
    returns an empty list.
    """
    try:
        assert isinstance(data, ID3)
        return [str(i) for i in data.getall(key)]
    except AssertionError:
        assert isinstance(data, MP4Tags)
        return [f"{i}:\n{str(data[i])}" for i in data.keys() if i.startswith(key)]


def print_tags(data: Union[ID3, MP4Tags],
               key: str) -> None:
    """Pretty-print the information matching KEY in DATA.
    """
    pprint.pprint(get_tags(data, key))


def do_copy_tags(from_f: Path,
                 to_f: Path,
                 quiet: bool = False) -> None:
    """Copy tags from FROM_F, a music file, to TO_F, another music file, as well as
    possible. Makes no attempt to avoid copying tags from "prohibited" frame types.

    "As well as possible" means "doing whatever can easily be done with easy=True
    while using Mutagen to open files." There is also some mapping from one system
    of key naming to another so that metadata from, e.g., .wma files, which has a
    different nomenclatural system for what each bit of metadata is called.
    """
    def value_of(what: Any) -> str:
        """Returns a string extracted from WHAT, a data value being copied by key from
        another type of data stream. These may just functionally be strings, or they
        may be attribute lists. In any case, tries hard to get the "real value" of the
        data.
        """
        if isinstance(what, str):
            return what
        elif isinstance(what, bytes):
            return th.unicode_of(what)
        elif isinstance(what, Iterable) and (len(what) > 0):
            atom = what[0]
            try:
                return atom.value
            except (AttributeError,):
                if isinstance(atom, Iterable) and not isinstance(atom, (str, bytes)):
                    return str(atom[0])
            except Exception as errrr:
                pass

        # if all else fails ...
        return str(what)

    assert isinstance(from_f, Path)
    assert isinstance(to_f, Path)
    assert from_f.exists()
    assert to_f.exists()

    from_data, to_data = mutagen.File(from_f, easy=True), mutagen.File(to_f, easy=True)

    for data, which_f in ((from_data, from_f), (to_data, to_f)):
        if not data:
            if not quiet:
                print(f"Unable to handle metadata on {which_f.name}! Not copying metadata ...")
            return

    for k, v in from_data.items():
        try:
            to_data[data_key_trans.get(k, k)] = value_of(v)
        except Exception as errr:
            if not quiet:
                if k not in config['foreign ignore frames']:
                    print(f"        ... unable to add value {v} for key {k} in {to_f.name}")
                    if k != data_key_trans.get(k, k):
                        print(f"          ... this key was translated as {data_key_trans.get(k, k)}")

    to_data.save()


def do_vbrfix(which_file: Path,
              quiet: bool = False) -> None:
    """Fixes the VBR header in WHICH_FILE, an .mp3 file, by using the vbrfix utility.

    Creates a temporary file, then overwrites the original file if successful.
    """
    tmp = sanitize_path(Path(which_file.name + '-temp' + which_file.suffix))
    out = subprocess.run([executable_locations['vbrfix'], str(which_file.resolve()), str(tmp.resolve())],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if out.returncode == 0:
        tmp.replace(which_file)
    else:
        if not quiet:
            print(f"Unable to fix VBR bitrate information for {which_file.name}! The system said: {out.stdout}")


# This next dictionary is lists translations from "foreign" (.e.g, .wma) metadata keys to those understood by
# Mutagen's Easy interface.
data_key_trans = {
    # .wma-related fields
    'Author': 'artist',

    'ID3/TMED': 'media',

    'WM/AlbumArtist': 'albumartist',
    'WM/AlbumTitle': 'album',
    'WM/AudioFileURL': 'website',
    'WM/AudioSourceURL': 'website',
    'WM/AuthorURL': 'website',
    'WM/Composer': 'composer',
    'WM/Genre': 'genre',
    'WM/Track': 'tracknumber',
    'WM/TrackNumber': 'tracknumber',
    'WM/UserWebURL': 'website',
    'WM/Year': 'date',

    # other formats?
}


# Utilities for handling file-format conversion.
executables_required = ('lame', 'flac', 'vbrfix', 'ffmpeg', 'cat', 'mp3splt')
executable_locations = {n: shutil.which(n) for n in executables_required}


# A list of converter functions used by convert_file(), below, mapping extensions to functions that handle
# that extension. Each function must have the same call signature as convert_file and also return a new Path.
# Use convert_flac(), above, as a model for new extensions.
def convert_audible_audiobook(which_file: Path,
                              quiet: bool = True) -> Path:
    """Converts WHICH_FILE, which must be a valid .aa file, to .m4a.
    """
    dec_args = construct_ffmpeg_cmdline(which_file)
    enc_args = [executable_locations['ffmpeg']] + config['m4a options']

    return run_conversion(which_file, dec_args=dec_args, enc_args=enc_args, new_suffix='.m4a',
                          quiet=quiet, vbrfix=False)


def convert_flac(which_file: Path,
                 quiet: bool = True) -> Path:
    """Converts WHICH_FILE, which must be a valid .flac file, to .mp3.
    """
    dec_args = [executable_locations['flac']] + config['flac options'] + [str(which_file.resolve())]
    enc_args = [executable_locations['lame']] + config['LAME options']

    return run_conversion(which_file, dec_args=dec_args, enc_args=enc_args, new_suffix='.mp3',
                          quiet=quiet, vbrfix=True)


def convert_ipod_audiobook(which_file: Path,
                           quiet: bool = True) -> Path:
    """Converts an iPod audiobook (an .m4b file) to an .m4a file. Since an .m4b file is
    always just an .m4a file with an .m4b extension, all we have to do is to change
    the extension of the file. We generate a new clean name to make absolutely sure
    (well, as sure as we can be, barring race conditions) we're nto overwriting an
    existing file.
    """
    assert isinstance(which_file, Path)
    assert which_file.suffix
    assert which_file.suffix.strip().casefold() == '.m4b'

    new_name = clean_name(suggested_name=which_file.with_suffix('.m4a'))
    which_file.rename(new_name)
    assert new_name.exists()
    return new_name


def convert_monkey(which_file: Path,
                   quiet: bool = True) -> Path:
    """Converts WHICH_FILE, which must be a valid Monkey's Audio (ugh) file, to .mp3.

    If the directory containing WHICH_FILE also includes EXACTLY ONE .cue file, then
    an attempt is made to split the resulting .mp3 into a series of .mp3s using that
    .cue file. If this succeeds, the intermediate (long, full-album) .mp3 file is
    discarded, and the return value for the function becomes only the first filename
    generated (lexicographically) in the split.

    Note that the exact command sent to ffmpeg is not currently user-configurable
    via the preferences mechanism.

    Note that there is plenty of information that copy_tags does not copy from .wma
    files to .mp3. Manual intervention in the process is helpful here.
    """
    dec_args = construct_ffmpeg_cmdline(which_file)
    enc_args = [executable_locations['lame']] + config['LAME options']

    ret = run_conversion(which_file, dec_args=dec_args, enc_args=enc_args, new_suffix='.mp3',
                         quiet=quiet, vbrfix=True)

    # Now, check to see if we've inherited a .cue file.
    cue_files = [i for i in which_file.parent.glob("*") if i.suffix.strip().casefold() == ".cue"]
    if len(cue_files) == 1:
        if not quiet:
            print(f"    ... found single .cue file, {cue_files[0].name}. Attempting to split .mp3 ...")
        out = subprocess.run([executable_locations['mp3splt'], '-a', '-c',
                              str(cue_files[0].resolve()), str(ret.resolve())],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if out.returncode == 0:
            if not quiet:
                print("    ... success!")
            old_ret, ret = ret, [i for i in ret.parent.glob("*") if i.suffix in ('.mp3', '.MP3')][0]
            old_ret.unlink()
        else:
            if not quiet:
                print(f"Unable to split .mp3 (result code {out.returncode})! The system said: {out.stdout}")

    return ret


def convert_wav(which_file: Path,
                quiet: bool = True) -> Path:
    """Converts WHICH_FILE, which must be a valid IBM/Microsoft .wav file with standard
    header, to .mp3.

    Note that not much metadata is copied from the .wav to the .mp3; it seems like
    mutagen's support for accessing .wav files through the Easy interface is limited?
    """
    dec_args = [executable_locations['cat'], str(which_file.resolve())]
    enc_args = [executable_locations['lame']] + config['LAME options']

    return run_conversion(which_file, dec_args=dec_args, enc_args=enc_args, new_suffix='.mp3',
                          quiet=quiet, vbrfix=True)


def convert_wma(which_file: Path,
                quiet: bool = True) -> Path:
    """Converts WHICH_FILE, which must be a valid .flac file, to .mp3.

    Note that the exact command sent to ffmpeg is not currently user-configurable
    via the preferences mechanism.

    Note that there is plenty of information that copy_tags does not copy from .wma
    files to .mp3. Manual intervention in the process is helpful here.
    """
    dec_args = [executable_locations['ffmpeg']] + ['-i', str(which_file.resolve()), '-f', 'wav',
                                                   '-c:a', 'pcm_s16le', '-ar', '44100', 'pipe:1']
    enc_args = [executable_locations['lame']] + config['LAME options']

    return run_conversion(which_file, dec_args=dec_args, enc_args=enc_args, new_suffix='.mp3',
                          quiet=quiet, vbrfix=True)


converters = {
    '.aa': convert_audible_audiobook,
    '.ape': convert_monkey,
    '.flac': convert_flac,
    '.m4b': convert_ipod_audiobook,
    '.wav': convert_wav,
    '.wma': convert_wma,
}


def run_conversion(infile: Path,
                   dec_args: List[str],
                   enc_args: List[str],
                   new_suffix: str = '.mp3',
                   quiet: bool = False,
                   vbrfix: bool = None,
                   ) -> Path:
    """Takes INFILE, a file to be processed, and processes it by starting two processes
    modeled by two Popen instances. THe first is started using DEC_ARGS as the
    command-line argument; the second is started using ENC_ARGS as the argument
    list. The stdout output from the decoder (first, started from DEC_ARGS) is fed
    into the stdin input for the encoder (second, started from ENC_ARGS).

    The new filename generated will be unique within its own directory and have the
    file extension specified by NEW_SUFFIX. Assuming the conversion succeeds and
    produces the expected file, tags are copied from the old to the new file, and,
    if VBRFIX is True, a pass through the vbrfix program will be made at the end of
    processing. (This last is useful because LAME does not automatically put this
    information at the beginning of the file when taking input through a pipe,
    because it does not have the necessary information at the beginning of the
    single pass it makes.) If VBRFIX is None (the default), this VBR-fixing pass is
    performed iff the extension of the new file is (case-insensitive) ".mp3".

    ENC_ARGS is modified before the process is started by appending the name of the
    desired output file after that output filename has been generated. This requires
    that the command be constructed in such a way that it ends with the output
    filename. Specifying command-line options in the prefs files is pretty hacky in
    general and it's easy for end-users to break by editing thoughtlessly.

    ENC_ARGS and DEC_ARGS are passed directly to the underlying OS and therefore
    must begin with the name of a command.
    """
    assert isinstance(infile, Path)
    assert isinstance(dec_args, Iterable)
    assert all([isinstance(o, str) for o in dec_args])
    assert isinstance(enc_args, Iterable)
    assert all([isinstance(o, str) for o in enc_args])

    if vbrfix is None:
        vbrfix = (new_suffix.casefold().strip() == '.mp3')

    outfile = clean_name(infile.with_suffix(new_suffix))
    enc_args.append(outfile)

    p1 = subprocess.Popen(dec_args, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(enc_args, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    p1.stdout.close()       # Allow p1 to receive a SIGPIPE if p2 exits.)
    out = p2.communicate()
    assert outfile.exists()

    if vbrfix:
        do_vbrfix(outfile, quiet)
    do_copy_tags(infile, outfile, quiet)
    if not quiet:
        print('\n\n'.join([th.unicode_of(i) for i in out if i]).strip(), end="\n\n")

    return outfile


def construct_ffmpeg_cmdline(which_file: Path) -> List[str]:
    """Convenience function to construct a parameter list calling ffmpeg to do the
    work of converting to .wav and outputting to stdout to be piped into a
    compressor.
    """
    ret = [executable_locations['ffmpeg']] + config["ffmpeg pre-input options"] + [str(which_file.resolve())]
    ret += config["ffmpeg post-input options"]
    return ret


def convert_file(which_file: Path,
                 delete_original: bool = False,
                 quiet: bool = False) -> Path:
    """Convert a single file, WHICH_FILE, to an acceptable format. Also copies any
    available tag information from the original file to the converted file. Returns
    the Path to the new file. If DELETE_ORIGINAL is True (default False), also
    delete the original file after conversion and tag copying.

    The format of WHICH_FILE is determined purely by file extension.

    The returned name should generally be the same as WHICH_NAME, except with a new
    suffix, but may be renamed due to conflicts with existing files in the
    directory.
    """
    assert isinstance(which_file, Path)
    assert which_file.exists()

    if not quiet:
        print(f"\nConverting {which_file.name} ...")

    try:
        ret = converters[which_file.suffix.strip().casefold()](which_file, quiet)
    except (KeyError,) as errr:
        raise RuntimeError(f"Cannot determine what to do with file {which_file}: unrecognized extension!") from errr
    except Exception as errr:
        print(f"Cannot process file {which_file.name}! The system said: {errr}")
        raise errr

    assert ret.suffix.strip().casefold() in config['allowed music extensions']
    if not quiet:
        print(f"    ... conversion of {which_file.name} resulted in {ret.name}")

    if delete_original and which_file.exists(): # File might have been removed or renamed as a side-effect
        which_file.unlink()                         # of various processing along the way. Gone already? Oh well.
        if not quiet:
            print(f"        ... deleted original file: {which_file.name}")
    return ret


def do_convert_audio(which_files: Iterable[Path]) -> None:
    """Convert WHICH_FILES to the default target audio format.
    """
    print(f"\nConverting {len(which_files)} files ...")
    for f in sorted(which_files):
        convert_file(f, delete_original=True)


# Lower-level functions handling getting info out of metadata for files.


def easy_from(which_file: Path):  # FIXME: annotate returns types!
    """Returns the Easy-style mutagen.File object, after validating that it has
    appropriate tags.

    Note that if all you want is read-only metadata, use the convenience function
    easy_metadata_from(), below.
    """
    ret = None

    try:
        ret = mutagen.File(which_file, easy=True)
        assert isinstance(ret.tags, (EasyMP4Tags, EasyID3))

    except (IOError, AttributeError, AssertionError, ) as errrr:
        print(f"Unable to read metadata from {which_file.name}! the system said: {errrr}.")
    except Exception as errrr:
        print(f"Unanticipated error occurred! Could not load metadata for file {which_file.name}.THe system said: {errrr}")

    return ret


def easy_metadata_from(which_file: Path) -> Union[EasyID3, EasyMP4Tags, None]:
    """Returns the Easy-style metadata object for WHICH_FILE's tags. Returns None if
    metadata cannot be found.
    """
    return easy_from(which_file).tags


def _data_from_easy(data: Union[EasyID3, EasyMP4Tags],
                    key: str) -> Union[str, None]:
    """Parses DATA, an EasyID3 tag, to extract KEY, if possible; if it's possible,
    returns the relevant data; otherwise, returns None.
    """
    try:
        ret = data[key]
        if isinstance(ret, str):
            return ret
        elif isinstance(ret, Iterable):
            return ret[0]
    except (KeyError,):
        return None


def title_from_easy(data: Union[EasyID3, EasyMP4Tags],
                    f: Path) -> Union[str, None]:
    """Parses DATA, an EasyID3 tag, to try to extract the song title from that data.
    Tries to deal sensibly with problems. Returns None if it absolutely cannot
    figure that out.
    """
    return _data_from_easy(data, 'title')


def artist_from_easy(data: Union[EasyID3, EasyMP4Tags],
                     f: Path) -> Union[str, None]:
    """Try to get the artist name for the song represented by DATA. Return that name
    as a string, or else None, if we can't figure it out.
    """
    return _data_from_easy(data, 'artist')


def album_from_easy(data: Union[EasyID3, EasyMP4Tags],
                    f: Path) -> Union[str, None]:
    """Try to get the album name for the song represented by DATA. Return that name
    as a string, or else None, if we can't figure it out.
    """
    return _data_from_easy(data, 'album')


def albumartist_from_easy(data: Union[EasyID3, EasyMP4Tags],
                          f: Path) -> Union[str, None]:
    """Try to get the album artist name for the song represented by DATA. Return that
    name as a string, or else None, if we can't figure it out.
    """
    return _data_from_easy(data, 'albumartist')


def artist_or_albumartist_from_easy(data: Union[EasyID3, EasyMP4Tags],
                                    f: Path) -> Union[str, None]:
    """Try to get the artist name for the song represented by DATA. If that's not
    possible, try getting the album artist instead. If neither is possible, return
    None instead.
    """
    return artist_from_easy(data, f) or albumartist_from_easy(data, f) or None


def trackno_from_easy(data: Union[EasyID3, EasyMP4Tags],
                      f: Path) -> Union[str, None]:
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


def year_from_easydata(data: Union[EasyID3, EasyMP4Tags],
                       f: Path) -> Union[str, None]:
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
