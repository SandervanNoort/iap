#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Read configuration files"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import logging

from .inibase import IniBase
from . import samples, tools

logger = logging.getLogger(__name__)


class Ini(IniBase):
    """Class to load the ini files"""
    # allow samples_period

    def update_intake(self):
        """Update intake based on other options, including samples"""
        IniBase.update_intake(self)
        for options in self.datasets.values():
            if options["samples_period"] != 0:
                min_date, max_date = samples.get_range(
                    options["country"], options["season"],
                    options["samples_period"], None, True)
                options["intake"] = tools.sql_and(
                    options["intake"],
                    "start_date<='{0}'".format(min_date),
                    "end_date>'{0}'".format(max_date))
