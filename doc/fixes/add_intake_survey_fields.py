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
    iap.DEBUG_VALUE = iap.FULL
    for period in periods:
        for table in ["intake", "survey"]:
            cursor = iap.utils.query("""
                show
                    fields
                from
                    %(table)s_%(period)s
                """ % {"table": table, "period": period})
            old_fields = [row["Field"] for row in cursor.fetchall()]

            cursor = iap.utils.query("""
                show
                    fields
                from
                    my_%(table)s
                """ % {"table": table})
            new_fields = [row["Field"] for row in cursor.fetchall()]

            if old_fields == new_fields:
                print "Fields equal for", table, period
            else:
                print "Adding fields to", table, period, "..."
                iap.utils.drop_table("new_%s" % period)
                iap.utils.query("""
                    create
                        table new_%(period)s
                    like
                        my_%(table)s
                    """ % {"table": table, "period": period})
                iap.utils.query("""
                    insert
                        into new_%(period)s
                    (%(fields)s)
                        select
                            %(fields)s
                        from
                            %(table)s_%(period)s
                    """ % {"table": table,
                            "period": period,
                            "fields": ",".join(old_fields)})
                iap.utils.drop_table("survey_%s" % period)
                iap.utils.query("""
                    alter table
                        new_%(period)s
                    rename
                        %(table)s_%(period)s
                    """ % {"table": table, "period": period})
except iap.IAPError, inst:
    print "Caught error:", inst
except:
    iap.utils.close()
    raise
iap.utils.close()
