#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A quick script to be run by a cron job; it periodically commits changes to
various git repositories. This is useful for me on certain projects: some of my
autotext projects keep archives of the generated texts, and those archives are
often also stored in the project's GitHub repo, so this script, if run
periodically, is intended to keep those projects' data synced to GitHub in a
timely fashion.

Short version: task_list is a dictionary with directory pathnames as keys and
a list of commands as the value of each each. For each key, the script changes
the current working directory to the value of the key, then executes each
command in the list of commands, trapping errors. It substitutes the current
date for the string @DATE@ in each case.

This script is licensed under the GNU GPL, either v3 or, at your option, any
later version. See the file LICENSE.md for a copy of this license. You are
welcome to use this program, but it is presented WITHOUT ANY WARRANTY or other
guarantee: without even the guarantee of MERCHANTABILITY of FITNESS FOR ANY
PARTICULAR PURPOSE. Use of this script is at your own risk. By using this
program, you agree that in no circumstance will the author of the script be
liable for any damage it causes.
"""


import datetime, os, subprocess

import text_handling as th      # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py

import patrick_logger           # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/patrick_logger.py
from patrick_logger import log_it

patrick_logger.verbosity_level = 3


task_list = {'/lovecraft': ['git add titles.txt archives/',
                            'git commit -m "@DATE@: archiving new stories"',
                            'git push'],
             '/archive-junta': ['git add data/',
                                'git add logs/',
								'git add unhandled_data/',
								'git add unhandled_data/unrecorded_deletions/', 
                                'git commit -m "@DATE@: archiving new tweets and logs"',
                                'git push'],
             '/LibidoMechanica': ['git add archives/',
                                  'git add similarity_cache*',
                                  'git commit -m "@DATE@: archiving new poems"',
                                  'git push'],
             '/TrumpTweets': ['git add data/',
                              'git commit -m "@DATE@: archiving new data"',
                              'git push'],
             '/home/patrick/Documents/programming/python_projects/STFUDonnyBot': ['git add archives',
                                                                                  'git commit -m "@DATE@: archiving new data"',
                                                                                  'git push'],
             '/home/patrick/Documents/programming/python_projects/network-reporter': ['git add data/',
                                                                                      'git add reports/',
                                                                                      'git commit -m "@DATE@: archiving new data"',
                                                                                      'git push'],
            }

if __name__ == "__main__":
    log_it("INFO: We're starting a run of git_committer.py\n\n", 1)
    olddir = os.getcwd()
    try:
        for dir, acts in task_list.items():
            log_it("INFO: changing directory to '%s'" % dir, 2)
            os.chdir(dir)
            log_it('\n> cd %s' % dir, 0)
            for act in acts:
                try:
                    act = act.replace('@DATE@',  datetime.datetime.now().strftime('%d %b %Y'))
                    log_it('\n> %s\n\n' % act, 0)
                    subprocess.call(act, shell=True)
                except BaseException as e:
                    log_it('ERROR: unable to run command "%s" because %s' % (act, e), 2)
    finally:
        os.chdir(olddir)
