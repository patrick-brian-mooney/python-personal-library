#!/usr/bin/env python3
"""Routines for searching files and folders"""

import os

def get_files_list(which_dir, skips=None):
    """Get a complete list of all files and folders under WHICH_DIR, except those matching SKIPS.
    Calls itself recursively, so it's a bad idea if the directory is (literally) profound.
    """
    if skips == None: 
        skips = [][:]
    ret = [][:]
    for (thisdir, dirshere, fileshere) in os.walk(which_dir):
        ret.append(os.path.join(thisdir))
        if dirshere:
            for dname in dirshere:
                ret += get_files_list(os.path.join(thisdir, dname), skips)
        if fileshere:
            for fname in fileshere:
                ret.append(os.path.join(thisdir, fname))
        if skips:
            for the_skip in skips:
                ret = [the_item for the_item in ret if the_skip not in the_item]
        ret.sort()
        return ret

if __name__ == "__main__":
    from pprint import pprint
    pprint(get_files_list('.', None))
