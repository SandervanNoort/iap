#!/usr/bin/python
# -*-coding: utf-8-*-

"""Import data from the other countries"""

from __future__ import with_statement

import sys
import os

if os.path.exists(".pythonpath"):
    with open(".pythonpath", "r") as pyobj:
        for pyline in pyobj.readlines():
            sys.path.append(pyline.strip())

import iap

if len(sys.argv) < 2:
    sys.exit("Usage: import.py <period>")
else:
    periods = sys.argv[1:]

try:
    iap.init()
    iap.cfg.debug_value = iap.cfg.DEBUG
    for period in periods:
        cursor = iap.utils.query("""
            update
                survey_%(period)s
            set
                s210 = NULL
            where
                s210 > date and date > 0
            """ % {"period": period})

        cursor = iap.utils.query("""
            update
                survey_%(period)s
            set
                s110 = NULL
            where
                s110 > date and date > 0
            """ % {"period": period})

except iap.MyError, inst:
    print "Caught error:", inst
except:
    iap.close()
    raise
iap.close()
