#!/usr/bin/env python3
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Command line iap"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import subprocess
import sys

import iap


if __name__ == "__main__":
    cmd = "mysql -u {user} -p{pass} {db}".format(**iap.config.LOCAL["db"])
    try:
        subprocess.call(cmd, shell=True)
    except subprocess.CalledProcessError as error:
        print(error)
        print(error.output)
        sys.exit()
