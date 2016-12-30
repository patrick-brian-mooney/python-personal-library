#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick hack to move all the files in subfolders of the current folder into
the current directory and rename them in the order that a lexicographic search
encounters them. Not anywhere near general purpose, and is POSIX-dependent.

Really, I'm just putting this here so I don't have to rewrite it from scratch
some other time.

This program is licensed under the GPL v3 or, at your option, any later
version. See the file LICENSE.md for a copy of this license.
"""

import os, sys, glob, pprint, subprocess

import text_handling as th      # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py

debugging = True

current_dir = os.getcwd()
dirs_list = sorted([ d for d in glob.glob('*') if os.path.isdir(d) ])

file_count = 1

if debugging:
    th.print_wrapped("DEBUGGING: directories list is %s" % dirs_list)
    _ = input("Hit ENTER to continue")
    print()

for d in dirs_list:
    try:
        if debugging:
            th.print_wrapped('DEBUGGING: entering directory "%s".' % d)
            _ = input("Hit ENTER to continue")
            print()
        
        os.chdir(d)   
        files = sorted(glob.glob('*'))
        if debugging:
            th.print_wrapped('DEBUGGING: files in that directory are %s.' % files)
            _ = input("Hit ENTER to continue")
        
        for f in files:
            if debugging: th.print_wrapped("  ...processing %s" % f)
            new_name = "%05d%s" % (file_count, os.path.splitext(f)[1])
            os.rename(f, new_name)
            file_count += 1
            subprocess.call('mv "%s" ../' % new_name, shell=True)
    finally:
        os.chdir(current_dir)