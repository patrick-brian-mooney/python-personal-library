#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A short Python script that leverages existing code to transcode any
understood audio files to .mp3 or .m4a. Other destination formats are not
currently supported.

This project and all associated code is copyright 2023 by Patrick Mooney. Code
in this project is licensed under the GPL, either version 3 or (at your option)
any other version. See the file LICENSE.md for details.
"""

import argparse
import sys

from pathlib import Path
from typing import List, Type

import music_file_handling as mfh


def convert_files(filename: List[Type[Path]],
                  delete: bool,
                  mp4: bool,
                  no_vbrfix: bool) -> None:
    for f in filename:
        assert isinstance(f, Path)
        assert f.is_file()

        if (ext := f.suffix.strip().casefold()) == '.flac':
            dec_args = mfh.executable_locations['flac'] + mfh.config['flac options'] + [str(f.resolve())]
        elif ext in ['.wav', '.wave']:
            dec_args = [mfh.executable_locations['cat'], str(mfh.which_file.resolve())]
        else:
            dec_args = mfh.construct_ffmpeg_cmdline(f)

        if mp4:
            enc_args = [mfh.executable_locations['ffmpeg']] + mfh.config['m4a options']
        else:
            enc_args = [mfh.executable_locations['lame']] + mfh.config['LAME options']

        # FIXME! mp4 -> mp3 tag conversion gives the literal Python string representation of 1-item lists of strings!
        new_f = mfh.run_conversion(f, dec_args=dec_args, enc_args=enc_args, new_suffix=('.m4a' if mp4 else '.mp3'),
                                   quiet=False, vbrfix=(not no_vbrfix))

        if new_f.exists() and delete:
            f.unlink()


def process_command_line(args: List[str]) -> None:
    parser = argparse.ArgumentParser(prog='transcode_audio', description=__doc__.strip().split('\n')[0],
                                     epilog=__doc__.strip().split('\n')[-1])

    parser.add_argument('filename', type=Path, nargs='+')       # positional argument
    parser.add_argument('-4', '--mp4', '--m4a', '--to-mp4', '--to-m4a', action='store_true',
                        help='Transcode to .m4a instead of to .mp3.')
    parser.add_argument('-d', '--delete', '--del', '--delete-originals', '--delete-files',
                        action='store_true', help="Delete originals after conversion.")
    parser.add_argument('-n', '--no-vbrfix', action='store_true',
                        help="Don't run VBRfix after conversion, even on .mp3 files.")

    convert_files(**vars(parser.parse_args(args)))

    for f in (Path('.').glob("vbrfix.*")):
        if f.is_file():
            f.unlink()


if __name__ == "__main__":
    force_debugging = True
    if force_debugging:
        process_command_line(['/home/patrick/Music/by Artist/Frank Zappa/[1998] Cheap Thrills/The Torture Never Stops.m4a'])
        sys.exit()

    process_command_line(sys.argv[1:])
