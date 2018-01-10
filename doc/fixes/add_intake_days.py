#!/usr/bin/python
# -*-coding: utf-8-*-

"""Import data from the other countries"""

import sys
import os

import iap

if len(sys.argv) < 2:
    sys.exit("Usage: import.py <period>")
else:
    if sys.argv[1] == "ALL":
        periods = iap.PERIODS_VALID
    else:
        periods = sys.argv[1:]

try:
    iap.utils.create_table("my_intake")
    for period in periods:
        cursor = iap.utils.query("""
            show
                fields
            from
                intake_%(period)s
            """ % {"period": period})
        old_fields = [row["Field"] for row in cursor.fetchall()]

        cursor = iap.utils.query("""
            show
                fields
            from
                my_intake
            """)
        new_fields = [row["Field"] for row in cursor.fetchall()]

        if old_fields == new_fields:
            print "Fields equal for", period
        if "days" in set(new_fields) - set(old_fields):
            print "adding days to %s" % period
            iap.utils.drop_table("new_%s" % period)
            iap.utils.query("""
                create
                    table new_%(period)s
                like
                    my_intake
                """ % {"period": period})
            iap.utils.query("""
                insert
                    into new_%(period)s
                (%(fields)s)
                    select
                        %(fields)s
                    from
                        intake_%(period)s
                """ % {"period": period,
                        "fields": ",".join(old_fields)})
            iap.utils.drop_table("intake_%s" % period)
            iap.utils.query("""
                alter table
                    new_%(period)s
                rename
                    intake_%(period)s
                """ % {"period": period})
            iap.utils.query("""
                update intake_%(period)s
                set
                    days = datediff(survey_last, survey_1)
                """ % {"period": period})
        if "freq" in set(new_fields) - set(old_fields):
            print "adding freq to %s" % period
            iap.utils.drop_table("new_%s" % period)
            iap.utils.query("""
                create
                    table new_%(period)s
                like
                    my_intake
                """ % {"period": period})
            iap.utils.query("""
                insert
                    into new_%(period)s
                (%(fields)s)
                    select
                        %(fields)s
                    from
                        intake_%(period)s
                """ % {"period": period,
                        "fields": ",".join(old_fields)})
            iap.utils.drop_table("intake_%s" % period)
            iap.utils.query("""
                alter table
                    new_%(period)s
                rename
                    intake_%(period)s
                """ % {"period": period})
            iap.utils.query("""
                update intake_%(period)s
                set
                    freq = round(days / (surveys - 1))
                """ % {"period": period})
except iap.IAPError, inst:
    print "Caught error:", inst
except:
    iap.utils.close()
    raise
iap.utils.close()
