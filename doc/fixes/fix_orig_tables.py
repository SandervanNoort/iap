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
        if period == "pt09":
            iap.utils.query("drop table if exists tmp_pt09")
            iap.utils.query("""
                create table tmp_pt09
                select
                    max(sid) as sid
                    ,uid
                    ,date
                    ,max(q3000) as q3000
                    ,max(q3001) as q3001
                    ,max(q3002) as q3002
                    ,max(q3003) as q3003
                    ,max(q3004) as q3004
                    ,max(q3005) as q3005
                    ,max(q3006) as q3006
                    ,max(q3007) as q3007
                    ,max(q3008) as q3008
                    ,max(sync) as sync
                    ,max(date_tmp) as date_tmp
                    ,max(date_epiwork) as date_epiwork
                from
                    orig_survey_pt09
                where
                    date >= 20091117
                group by
                    uid
                    ,date(date)
                """)
            iap.utils.query("""delete from orig_survey_pt09
                     where date >= 20091117""")
            iap.utils.query("""insert into orig_survey_pt09
                    select * from tmp_pt09""")
            iap.utils.query("drop table if exists tmp_pt09")

        if period == "pt10":
            cursor = iap.utils.query("""show fields
                    from orig_survey_pt10""")
            fields = cursor.fetchall()
            for column in  [field["Field"] for field in fields]:
                if column.startswith("qs_"):
                    iap.utils.query("""alter table orig_survey_pt10
                            change %(orig)s %(new)s varchar(60)"""
                            % {"orig": column, "new": column.replace("_", "")})
