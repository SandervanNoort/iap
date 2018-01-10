#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""The base IAP class (Influenzanet Analysis Program)"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import sys
import datetime
import configobj
# import matplotlib.figure # load matplotlib first to prevent mysql warnings
import logging

from . import tools
from .exceptions import IAPError

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(ROOT, "config")

# if reloading, only load since now
NOW = datetime.datetime.now()

# database connection
CURSOR = None

# cache
PERIODS = {}
LIMITS = {}
COLUMNS = {}

logger = logging.getLogger(__name__)
# logger.addHandler(logging.NullHandler())

LOCAL = None
TRANSLATE = None
CONFIG = None
TABLES = None
TABLE = None
SEP = None


def init(mod):
    """Initialize"""
    try:
        mod.LOCAL = configobj.ConfigObj(
            os.path.join(CONFIG_DIR, "local.ini"),
            configspec=os.path.join(CONFIG_DIR, "local.spec"))
        tools.cobj_check(mod.LOCAL, exception=IAPError)
        for key, folder in mod.LOCAL["dir"].items():
            if not folder.startswith("/"):
                mod.LOCAL["dir"][key] = os.path.join(ROOT, folder)

        mod.CONFIG = configobj.ConfigObj(
            os.path.join(CONFIG_DIR, "config.ini"),
            configspec=os.path.join(CONFIG_DIR, "config.spec"))
        tools.cobj_check(mod.CONFIG, exception=IAPError)
        mod.SEP = mod.CONFIG["seperators"]

        mod.TRANSLATE = {}
        for lang in os.listdir(os.path.join(CONFIG_DIR, "lang")):
            if not os.path.isdir(os.path.join(CONFIG_DIR, "lang", lang)):
                continue
            mod.TRANSLATE[lang] = {}
            for fname in os.listdir(os.path.join(CONFIG_DIR, "lang", lang)):
                base, ext = os.path.splitext(fname)
                if ext != ".ini":
                    continue
                try:
                    mod.TRANSLATE[lang][base] = configobj.ConfigObj(
                        os.path.join(CONFIG_DIR, "lang", lang, fname))
                except configobj.ConfigObjError as error:
                    raise IAPError(
                        "Parsing error in {error}: {lang}{fname}".format(
                            error=error, fname=fname, lang=lang))

        mod.TABLES = configobj.ConfigObj(
            os.path.join(CONFIG_DIR, "tables.ini"))

        mod.TABLE = {
            "intake": configobj.ConfigObj(
                os.path.join(CONFIG_DIR, "intake.ini")),
            "survey": configobj.ConfigObj(
                os.path.join(CONFIG_DIR, "survey.ini")),
            "cutter": configobj.ConfigObj(
                os.path.join(CONFIG_DIR, "cutter.ini"))}

    except IAPError as error:
        logger.critical(error)
        # utils.close()
        sys.exit()
    except:
        # utils.close()
        raise

tools.Delayed(__name__, init)
