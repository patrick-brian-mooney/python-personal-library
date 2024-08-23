#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to scan thorugh my music collection and attempt to downsample music
encoded with a high bitrate.

This project and all associated code is copyright 2024 by Patrick Mooney. Code
in this project is licensed under the GPL, either version 3 or (at your option)
any other version. See the file LICENSE.md for details.
"""

import collections
import os
import sys

from pathlib import Path
from typing import Iterable, Optional, TextIO

import music_file_handling as mfh
import flex_config as fc                        # https://github.com/patrick-brian-mooney/python-personal-library


default_config = dict(collections.ChainMap(mfh.default_config, {
    'music_root': Path("/home/patrick/Music"),          # Where to start searching.
    'extensions_to_scan': {'.mp3', '.m4a', },           # Extensions for music files.
    'uncompressible': dict(),                           # Files we have already tried without success to compress.
    'max_bitrate': 224,                                 # Past this point, we start trying to downsample.
    'minimum_savings': 0.05,                            # What fraction of file size must be reduced to keep the
                                                        # resampled file in place of the old one. e.g., 0.05 = 5%
    'files_shrunk': 0,                                  # number of files whose size we have reduced
    'bytes_saved': 0,                                   # total bytes saved.
}))


mfh.config = fc.PrefsTracker(appname="Python MusicDownsampler", defaults=default_config)


def try_reduce_bitrate(which_file: Path,
                       depth: int,
                       old_bitrate: float,
                       run_quiet: bool = True) -> None:
    """Re-encode WHICH_FILE, an existing music file, as VBR, in the standard VBR
    manner, in an attempt to reduce its file size. If, after re-encoding, the new
    file is not smaller than the original, the original is kept.

    DEPTH is how deep in the file-search recursion we are, which affects how we
    print status messages. OLD_BITRATE is the bitrate of the existing file, which we
    have already calculated by the time we get here and need not assess again.

    If RUN_QUIET is True (the default), the output from the conversion subprocesses
    will be suppressed instead of shown.
    """

    # first: check if we've unsuccessfully tried, on a previous run, to recompress this file
    old_size = os.path.getsize(which_file)
    if str(which_file.resolve()) in  mfh.config['uncompressible']:  # if file is tracked as previously tried ...
        if mfh.config['uncompressible'][str(which_file.resolve())] == old_size: # and its file size hasn't changed ...
            return                                                  # don't try again

    new_file: Optional[Path] = None

    try:
        print(f"{' ' * (depth + 2)}trying to downsample {which_file.name}, which has bitrate {old_bitrate} ...")
        old_suffix = which_file.suffix.strip().casefold()

        dec_args = mfh.construct_ffmpeg_cmdline(which_file)

        if old_suffix == '.m4a':
            vbrfix, new_suffix = False, '.new.m4a'
            enc_args = [mfh.executable_locations['ffmpeg']] + mfh.config['m4a options']
        elif old_suffix == '.mp3':
            vbrfix, new_suffix = True, '.new.mp3'
            enc_args = [mfh.executable_locations['lame']] + mfh.config['LAME options']
        else:
            raise RuntimeError(f"Extension for {which_file.name} is {old_suffix}, not .mp3 or .m4a!")

        try:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            if run_quiet:
                sys.stdout, sys.stderr = TextIO(), TextIO()         # create dummy streams
            new_file = mfh.run_conversion(which_file, dec_args=dec_args, enc_args=enc_args, new_suffix=new_suffix,
                                          quiet=run_quiet, vbrfix=vbrfix)
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

        new_size = os.path.getsize(new_file)
        if new_size > (old_size * (1 - mfh.config['minimum_savings'])):     # If the new file is not small enough ...
            if new_size > old_size:                                             # assemble some explanatory text; and
                desc = f"is {100 * ((new_size-old_size)/old_size):.2f}% larger"
            elif new_size == old_size:
                desc = "is the the same size"
            else:
                desc = f"only reduces file size by {((old_size-new_size)/old_size) * 100:.2f}%"
            print(f"{' ' * (depth + 4)}... new size is {new_size}, which {desc}! Keeping original.")
            new_file.unlink()                                                   # delete the old; and
            mfh.config['uncompressible'][str(which_file.resolve())] = old_size  # mark it not worth trying again.
            mfh.config.save_preferences()
        else:                                                               # otherwise ...
            print(f"{' ' * (depth + 4)} ... re-encoded with new bitrate {mfh.bitrate_from(new_file)}, saving "
                  f"{(old_size - new_size)} bytes, or {100 * ((old_size-new_size)/old_size):2f}%!")
            which_file.unlink()                                                 # replace the old file with the new.
            new_file.rename(which_file)

            mfh.config['files_shrunk'] += 1
            mfh.config['bytes_saved'] += (old_size - new_size)
            mfh.config.save_preferences()

    except Exception as errrr:
        print(f"{' ' * (depth + 4)}Unable to process file {which_file}! The system said: {errrr}.")
        if new_file:
            print(f"{' ' * (depth + 5)}... deleting partially created file {new_file}.")
            new_file.unlink()


def scan_dir(which_dir: Path,
             already_scanned: Iterable[Path] = (),
             depth: int = 0) -> None:
    """Scans through WHICH_DIR, checking to see whether the bitrate of any discovered
    music files is too high. Downsamples any high-bitrate files found, and
    recursively scans through any more directories found. Tracks files that do are
    not reduced in size by reprocessing so that we don't try again on subsecquent
    runs.
    """
    assert isinstance(which_dir, Path)
    assert which_dir.is_dir()
    already_scanned = already_scanned or set()

    which_dir = which_dir.resolve()
    if which_dir in already_scanned:
        return

    print(f"{' ' * depth} ... scanning {which_dir}")

    for f in sorted([fil for fil in which_dir.glob('*') if fil.suffix.lower() in mfh.config['extensions_to_scan']]):
        rate = mfh.bitrate_from(f)
        if rate and (rate > mfh.config['max_bitrate']):
            try_reduce_bitrate(f, depth, rate)

    already_scanned.add(which_dir)

    for d in sorted([fil.resolve() for fil in which_dir.glob('*') if fil.is_dir()]):
        scan_dir(d, already_scanned, 1+depth)
        already_scanned.add(d)


if __name__ == "__main__":
    scan_dir(mfh.config['music_root'])
    print(f"\n\n\nShrunk {mfh.config['files_shrunk']} files, saving {mfh.config['bytes_saved']} total bytes!")
