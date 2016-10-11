#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backs up system config. A quick hack for my own use. Useful before 
(re)installing a Linux distro.
"""

import subprocess

working_location = '/home/patrick/.system-config-backup'

backup_file_list = [    '/etc/anacrontab',
                        '/etc/fstab',
                        '/etc/hosts',
                        '/etc/hosts.allow',
                        '/etc/exports',
                        '/etc/apt/sources.list*',
                        '/etc/postfix/*',
                        '~/.ssh/',
                        '/root/.ssh/',
                        working_location
                    ]

commands_list = [   'crontab -l > %s/patrick.cronbak' % working_location,               # export user crontab
                    'sudo crontab -l > %s/patrick.cronbak' % working_location,          # export root crontab
                    'ls -la / | grep -- "->" > $s/root-symlinks' % working_location,    # export list of symlinks at root of drive
                    'sudo dpkg --get-selections > %s/installed-software.tsv' % working_location,    # export list of installed (Debian) pkgs.
                 ]

if __name__ == "__main__":
    for which_command in commands_list:
        subprocess.call(which_command, shell=True)

    # OK, create the archive
    subprocess.call('tar -cvf %s/sys-backup.tar %s' % (working_location, ' '.join(backup_file_list)), shell=True)
