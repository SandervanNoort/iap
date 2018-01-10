#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Install script"""

import os
import re

from distutils.core import setup
import distutils.command.build_py
import distutils.command.install_data  # pylint: disable=W0404


def data_include(install_root, local_root, exclude=None):
    """Include all files from a subdirectory"""
    if not exclude:
        exclude = []
    data_files = []
    for dirpath, _dirnames, fnames in os.walk(local_root):
        install_dir = os.path.normpath(
            os.path.join(install_root, os.path.relpath(dirpath, local_root)))
        files = [os.path.join(dirpath, fname)
                 for fname in fnames
                 if fname not in exclude]
        data_files.append((install_dir, files))
    return data_files


def substitute(fname, values):
    """Substitute the variable declarations"""

    with open(os.path.join(fname), "r") as fobj:
        contents = fobj.read()
        for key, value in values.items():
            contents = re.sub(
                "{0} *=.*".format(key),
                "{0} = \"{1}\"".format(key, value),
                contents)
    with open(os.path.join(fname), "w") as fobj:
        fobj.write(contents)


class build_py(distutils.command.build_py.build_py):
    """Build python modules"""
    # pylint: disable=R0904,C0103

    def run(self):
        distutils.command.build_py.build_py.run(self)
        substitute(
            os.path.join(self.build_lib, "iap/__init__.py"),
            {"CONFIG_DIR": "/etc/iap"})


class install_data(distutils.command.install_data.install_data):
    """Install data files"""
    # pylint: disable=R0904,C0103

    def run(self):
        distutils.command.install_data.install_data.run(self)
        substitute(
            os.path.join(self.root, "etc", "iap", "local.ini"),
            {"download": "/var/lib/iap/download",
             "data":  "/var/lib/iap/data",
             "export": "/var/lib/iap/export"})


setup(
    name="iap",
    cmdclass={"build_py": build_py, "install_data": install_data},
    version="20120226",
    description="Influenzanet Analyses Program",
    author="Sander van Noort",
    author_email="Sander.van.Noort@gmail.com",
    url="http://www.influenzanet.info/",
    packages=["iap", "iap/extra"],
    scripts=["bin/iap_cmd.py"],
    license="GPL v3",
    data_files=(
        [("/var/lib/iap/download", ["download/README"]),
         ("/var/lib/iap/export", ["export/README"]),
         ("share/doc/iap", ["LICENSE.txt"]),
         ("/etc/iap", ["doc/local.ini"])] +
        data_include("/etc/iap", "config", exclude=["local.ini"]) +
        data_include("/var/lib/iap/data", "data") +
        data_include("/etc/iap/db", "config/db") +
        data_include("share/doc/iap", "doc")))
