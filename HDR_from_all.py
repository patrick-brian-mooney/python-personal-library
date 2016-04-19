#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This quick hack makes an HDR script from all JPG photos in the current 
directory. Then it runs it. It assumes that all of the photos are JPGs in the
current directory, that all of the JPGs in the current directory are photos for
the project, and that there are no other .SH files in the current directory.
"""

import os, glob, subprocess

import postprocess_photos as pp
import create_HDR_script as cHs

cHs.create_script_from_file_list(glob.glob('*JPG') + glob.glob('*jpg'))
pp.run_shell_scripts()