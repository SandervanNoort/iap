#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""The base IAP class (Influenzanet Analysis Program)"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import time
import re
import sys
import subprocess
import datetime
import configobj
# import matplotlib.figure # load matplotlib first to prevent mysql warnings
import MySQLdb
import logging

from .ini import Ini
from .series import Series
from .data import Data
from .bardata import BarData, Venn
from .convert import Convert
from .update import Update
from .check import Check
from .export import Export
from .exceptions import IAPError

from . import download, linreg, samples, baseline, config, split, utils, tools

# Analyses is heavy due to scipy
# from .analyses import Analyses

# All figure should be imported via .fig
# Fig, dia, Plot, Barplot

# risk with rpy2 is slow to import
# from .risk import Risk
