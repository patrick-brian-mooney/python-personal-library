#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Folds the contents of multiple JSON files into one JSON file. Intended as a 
convenience for importing Google Photos albums to Flickr, because Google Photos
albums seem to occasionally be split into two folders, each with JSON metadata
that may or may not be the same.

This script is copyright 2017 by Patrick Mooney. It is licensed under the GPL,
either version 3 or (at your option) any later version. See the file LICENSE.md
for details.
"""

import argparse, json


parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], epilog=__doc__.split('\n\n')[1])
parser.add_argument('file', type=str, nargs='+', help='Files to be merged with this program. Values in files specified later on the command line override values in files specified earlier if there are conflicts in key names within the JSON files.')
parser.add_argument('-o', '--output', dest='output', action='store', required=True, help='specify the name of the output file')

args = parser.parse_args()

output_data = {}.copy()

for which_file in args.file:
    with open(which_file) as json_file:
        data = json.load(json_file)
        output_data.update(data)

with open(args.output, 'w') as output_file:
    json.dump(output_data, output_file)

