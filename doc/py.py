#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2012-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Run a python command with the right paths set"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import subprocess
import os
import sys
import importlib
import logging

MODULES = ["iap", "pyfig"]
EXTRA = ["thesis", "tools", "convert"]
FALLBACK = [os.path.join(os.environ["HOME"], ".python")]


def is_iapdir(dirname):
    """The dirname contains the iap dir"""
    return set(MODULES).issubset(os.listdir(dirname))


def get_devdir():
    """Return the dir which contains dev_names"""

    # first, check the current localpath
    devdir = os.path.abspath(os.curdir)
    if is_iapdir(devdir):
        return devdir
    new_devdir = os.path.dirname(devdir)
    while new_devdir != devdir:
        devdir = new_devdir
        if is_iapdir(devdir):
            return devdir
        new_devdir = os.path.dirname(devdir)

    # check the fallback
    for devdir in FALLBACK:
        if is_iapdir(devdir):
            return devdir

    sys.exit("No iap dir found")


def set_python():
    """Set the pythonpath variable"""
    # devdir = get_devdir()
    python_dirs = (os.environ["PYTHONPATH"].split(":")
                   if "PYTHONPATH" in os.environ else
                   [])

    # for dirname in MODULES + EXTRA:
    #     fullname = os.path.join(devdir, dirname)
    for fullname in [os.path.join(os.environ["HOME"], ".python")]:
        if os.path.exists(fullname):
            if fullname not in python_dirs:
                python_dirs.append(fullname)
            if fullname not in sys.path:
                sys.path.append(fullname)
    os.environ["PYTHONPATH"] = ":".join(python_dirs)

if __name__ == "__main__":
    version3 = "3" if "3" in sys.argv[0] else ""
    set_python()
    try:
        while "-d" in sys.argv:
            import iap
            sys.argv.remove("-d")
            logging.basicConfig(level=logging.DEBUG)

        if len(sys.argv) == 1:
            subprocess.call("ipython" + version3)
        elif sys.argv[1] == "sql":
            import iap
            cmd = "mysql -u {user} -p{pass} {db}".format(**iap.LOCAL["db"])
            subprocess.call(cmd, shell=True)
        elif "pall" in sys.argv:
            index = sys.argv.index("pall")
            for fname in sys.argv[index + 1:]:
                if not fname.endswith(".py"):
                    continue
                print("Running {fname} {args}...".format(
                    fname=fname,
                    args=" ".join(sys.argv[1:index])))
                if "" not in sys.path:
                    sys.path.insert(0, "")
                module = os.path.splitext(fname)[0]
                try:
                    local = importlib.import_module(module)
                    local.main()
                finally:
                    if os.path.exists(module + ".pyc"):
                        os.remove(module + ".pyc")
#                 subprocess.call(["python" + version3, fname] +
#                                 sys.argv[1:index])
        else:
            subprocess.call(["python" + version3] + sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit("exit by keyboard ctrl-c")
