#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Get influenzanet data from the database"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import datetime
import logging

from .exceptions import IAPError
from . import utils, split, config, tools

logger = logging.getLogger(__name__)


class Series(object):
    """Create influenzanet timeseries"""

    def __init__(self, options, category):
        self.options = options.copy()
        self.options["category"] = category

        self.columns = utils.get_columns("datasets")
        self.columns.remove("updated")
        self.columns.remove("dataset")

        self.set_dataset()
        if "country" not in options:
            self.set_options()

        self.options["period"] = utils.country_season_to_period(
            self.options["country"], self.options["season"])

        self.options["tbl_intake"] = utils.get_tbl(
            "intake", "new", self.options["period"])
        self.options["tbl_survey"] = utils.get_tbl(
            "survey", "new", self.options["period"])

        self.options["onset_column"] = (
            "IF(s210>0, s210, IF(s110>0, s110, sdate))"
            if self.options["onset"] == "fever"
            else "IF(s110>0, s110, sdate)"
            if self.options["onset"] == "symptoms"
            else "sdate")

        labels = split.get_labels(
            self.options["full_cutter"], self.options["full_answer"],
            self.options["period"])
        self.options["where_label"] = (
            "1=0" if len(labels) == 0 else
            "label=\"{0}\"".format(labels[0]) if len(labels) == 1 else
            "label IN ({0})".format(",".join(["'{0}'".format(label)
                                              for label in labels])))

    def set_dataset(self):
        """set options["dataset"]"""

        if self.options["category"] != "control":
            self.options["control"] = ""
            self.options["control_days"] = 0
        if self.options["category"] in ("joins", "leaves"):
            # They don't have influence, to keep the database clean
            self.options["casedef"] = ""
            self.options["onset"] = ""
            self.options["ignore_double"] = False
            self.options["ignore_multiple"] = False

        cursor = utils.query(
            """SELECT
                dataset, updated
            FROM
                datasets
            WHERE
                {columns}
            """.format(columns=" AND\n   ".join(
                ["{0}=%({0})s".format(column)
                 for column in self.columns if column != "snapshot"] +
                ["snapshot IS NULL" if self.options["snapshot"] is None else
                 "snapshot=%(snapshot)s"])),
            self.options)
        if cursor.rowcount >= 1:
            row = cursor.fetchone()
            self.options["dataset"] = row["dataset"]
            self.options["updated"] = row["updated"]
            logger.info(tools.Format(
                "Load dataset {dataset} ({updated})").format(
                    extra=self.options))
        else:
            cursor = utils.query(
                """INSERT INTO datasets
                    ({columns})
                VALUES
                    ({values})
                """.format(columns=", ".join(self.columns),
                           values=", ".join(["%({0})s".format(column)
                                             for column in self.columns])),
                self.options)
            self.options["dataset"] = cursor.lastrowid
            self.options["updated"] = None
            logger.info(tools.Format("Create dataset {dataset}").format(
                extra=self.options))

    def set_options(self):
        """set options based on options["dataset"]"""

        cursor = utils.query(
            """SELECT
                {columns}
            FROM
                datasets
            WHERE
                dataset=%(dataset)s
            """.format(columns=",".join(self.columns)),
            self.options)
        if cursor.rowcount != 1:
            raise IAPError("Dataset {0} does not exist".format(
                self.options["dataset"]))
        row = cursor.fetchone()

        for column in self.columns:
            self.options[column] = row[column]

    def get_labels(self):
        """Return all the available labels"""

        self.fill()
        cursor = utils.query(
            tools.Format("""SELECT
                distinct label
            FROM
                series
            WHERE
                dataset=%(dataset)s AND
                ({where_label})
            """).format(extra=self.options),
            {"dataset": self.options["dataset"]})
        for row in cursor.fetchall():
            yield row["label"]

    def get_series(self):
        """Get the series by date"""

        self.fill()
        cursor = utils.query(
            tools.Format("""SELECT
                label, date, sum(value) AS val
            FROM
                series
            WHERE
                dataset=%(dataset)s AND
                ({where_label})
            GROUP BY
                date, label
            ORDER BY
                date, label
            """).format(extra=self.options),
            self.options)
        for row in cursor.fetchall():
            if row["date"]:
                yield row["label"], row["date"], int(row["val"])

    def get_total(self, min_date, max_date):
        """Get the total number of entries"""

        self.fill()
        self.options["date_sql"] = ""
        if min_date is not None:
            self.options["date_sql"] += " AND date>=%(min_date)s"
        if max_date is not None:
            self.options["date_sql"] += " AND date<=%(max_date)s"

        cursor = utils.query(
            tools.Format("""SELECT
                COALESCE(SUM(value), 0) AS total
            FROM
                series
            WHERE
                dataset=%(dataset)s AND
                {where_label}
                {date_sql}
            """).format(extra=self.options),
            {"dataset": self.options["dataset"],
             "min_date": min_date,
             "max_date": max_date})

        row = cursor.fetchone()
        return int(row["total"])

    def get_total_survey_cutter(self, min_date=None, max_date=None):
        """Get the total number of entries"""

        self.fill()
        self.options["date_sql"] = ""
        if min_date is not None:
            self.options["date_sql"] += " AND date>=%(min_date)s"
        if max_date is not None:
            self.options["date_sql"] += " AND date<=%(max_date)s"

        cursor = utils.query(
            tools.Format("""SELECT
                label, COALESCE(SUM(value), 0) AS total
            FROM
                series
            WHERE
                dataset=%(dataset)s
                {date_sql}
            GROUP BY
                label
            """).format(extra=self.options),
            {"dataset": self.options["dataset"],
             "min_date": min_date,
             "max_date": max_date})

        return {row["label"]: int(row["total"])
                for row in cursor.fetchall()}

    def fill(self):
        """Fill the series tables"""

        if self.options["updated"] is None:
            logger.info(tools.Format("Filling empty dataset {dataset}").format(
                extra=self.options))
        elif self.options["reload"] and config.NOW > self.options["updated"]:
            logger.info(tools.Format("Refilling dataset {dataset}").format(
                extra=self.options))
        else:
            # all other datasets are already filled
            return

        if self.options["category"] in ("cases", "control"):
            self.fill_intake()
            self.fill_survey()
            self.fill_series("cases")
            utils.drop_table("tmp_intake")
            utils.drop_table("tmp_survey")
        elif self.options["category"] in ("joins",):
            self.fill_intake()
            self.fill_series("joins")
            utils.drop_table("tmp_intake")
        elif self.options["category"] in ("leaves",):
            self.fill_intake()
            self.fill_series("leaves")
            utils.drop_table("tmp_intake")
        else:
            raise IAPError("Unknown category: {0}".format(
                self.options["category"]))

        utils.query("LOCK TABLE series WRITE, datasets WRITE")

        utils.query(
            "DELETE FROM series WHERE dataset=%(dataset)s", self.options)
        utils.query("""INSERT INTO series
            SELECT
                dataset, label, date, value
            FROM
                tmp_series
            """)

        utils.query("""UPDATE datasets
            SET
                updated=NOW()
            WHERE
                dataset=%(dataset)s
            """, self.options)
        utils.query("UNLOCK TABLES")

        self.options["updated"] = datetime.datetime.now()
        utils.drop_table("tmp_series")

    def fill_intake(self):
        """Fill the table intake"""

        if self.options["intake"]:
            self.options["where_intake"] = utils.check_db(
                tools.Format("WHERE {intake}").format(extra=self.options),
                self.options["period"])
        else:
            self.options["where_intake"] = ""

        utils.drop_table("tmp_intake")
        utils.query(tools.Format("""
            CREATE
                TEMPORARY TABLE tmp_intake
            SELECT
                *
            FROM
                {tbl_intake} AS tbl_intake
            {where_intake}
            """).format(extra=self.options))
        utils.query("ALTER TABLE tmp_intake ADD INDEX(uid)")

        if self.options["snapshot"] is not None:
            utils.query(tools.Format("""
                CREATE
                    TEMPORARY TABLE tmp_end_date
                SELECT
                    uid, max(sdate) as sdate
                FROM
                   {tbl_survey} AS tbl_survey
                WHERE
                   tbl_survey.sdate<%(snapshot)s
                GROUP BY
                   uid
                """).format(extra=self.options), self.options)
            utils.query("""ALTER TABLE tmp_end_date ADD INDEX(uid)""")
            utils.query("""
                UPDATE
                    tmp_intake
                LEFT JOIN
                    tmp_end_date
                USING
                    (uid)
                SET
                    end_date = sdate
                """)
            utils.drop_table("tmp_end_date")

        elif self.options["last_survey"] != 0:
            utils.query(tools.Format("""
                UPDATE
                    tmp_intake
                LEFT JOIN
                    {tbl_survey} AS tbl_survey
                    ON tmp_intake.uid=tbl_survey.uid AND
                       tbl_survey.sid_uid=%(last_survey)s
                SET
                    end_date = sdate
                WHERE
                    sdate IS NOT NULL
                """).format(extra=self.options), self.options)

        if self.options["first_survey"] != 2:
            utils.query(
                tools.Format("""UPDATE
                    tmp_intake
                LEFT JOIN
                    {tbl_survey} AS tbl_survey
                    ON tmp_intake.uid=tbl_survey.uid AND
                       tbl_survey.sid_uid=%(sid_uid)s
                SET
                    start_date = DATE_ADD(sdate, INTERVAL %(interval)s DAY)
                """).format(extra=self.options),
                dict(self.options,
                     sid_uid=max(self.options["first_survey"] - 1, 1),
                     interval=1 if self.options["first_survey"] > 1 else -6))

        if self.options["snapshot"] is not None:
            utils.query("""
                DELETE FROM
                    tmp_intake
                WHERE
                    start_date>=%(snapshot)s
                """, self.options)

        utils.query("""DELETE
            FROM
                tmp_intake
            WHERE
                start_date IS NULL OR
                end_date IS NULL OR
                start_date>end_date
            """)

    def fill_survey(self):
        """Fill the table survey"""

        self.options["where_casedef"] = (
            utils.check_db(
                tools.Format("WHERE {casedef}").format(extra=self.options),
                self.options["period"])
            if self.options["casedef"] else
            "")

        if self.options["snapshot"] is not None:
            extra = tools.Format(
                "sdate < '{snapshot}'").format(extra=self.options)
            if self.options["where_casedef"] == "":
                self.options["where_casedef"] = "WHERE {0}".format(extra)
            else:
                self.options["where_casedef"] += " AND {0}".format(extra)

        utils.drop_table("tmp_survey")
        utils.query(tools.Format("""
            CREATE
                TEMPORARY TABLE tmp_survey
            SELECT
                *
            FROM
                {tbl_survey} AS tbl_survey
            {where_casedef}
            """).format(extra=self.options))

        utils.query("""ALTER TABLE tmp_survey
                ADD INDEX(uid),
                ADD INDEX(sid)""")

        if self.options["ignore_double"] or self.options["ignore_multiple"]:
            utils.query("""CREATE TEMPORARY TABLE tmp_survey2
                SELECT
                    sid, uid, sid_uid
                FROM
                    tmp_survey""")
            utils.query("""ALTER TABLE tmp_survey2 ADD INDEX(uid),
                    ADD INDEX(sid_uid)""")

            utils.query(
                """CREATE TEMPORARY TABLE tmp_sid
                SELECT tmp_survey.sid
                    FROM
                        tmp_survey
                    LEFT JOIN
                        tmp_survey2
                        ON {check} AND
                           tmp_survey.uid = tmp_survey2.uid
                    WHERE
                        tmp_survey2.sid IS NOT NULL
                """.format(check=(
                    "tmp_survey.sid_uid > tmp_survey2.sid_uid"
                    if self.options["ignore_multiple"] else
                    "tmp_survey.sid_uid - 1 = tmp_survey2.sid_uid")))

            utils.query("ALTER TABLE tmp_sid ADD INDEX(sid)")

            utils.query("""DELETE FROM tmp_survey
                WHERE
                    sid IN (SELECT sid FROM tmp_sid)
                """)
            utils.drop_table("tmp_sid")
            utils.drop_table("tmp_survey2")

        # delete survey data outside active period of participant
        # delete survey data from excluded participants
        utils.query(tools.Format("""
            DELETE
                tmp_survey
            FROM
                tmp_survey
            LEFT JOIN tmp_intake
                USING (uid)
            WHERE
                tmp_intake.uid IS NULL OR
                {onset_column} < start_date OR
                {onset_column} > end_date
            """).format(extra=self.options))

        if self.options["control"] != "":
            for control in self.options["control"].split(" AND "):
                if self.options["snapshot"] is not None:
                    sys.exit("todo: control and snapshot")
                self.options["where_control"] = utils.check_db(
                    "WHERE NOT ({0})".format(control),
                    self.options["period"])

                utils.query(tools.Format("""
                    CREATE
                        TEMPORARY TABLE tmp_survey2
                    SELECT
                        tbl_survey.*
                    FROM
                        tmp_survey
                    LEFT JOIN
                        {tbl_survey} AS tbl_survey
                        ON tbl_survey.sid_uid - 1 = tmp_survey.sid_uid AND
                           tbl_survey.uid = tmp_survey.uid
                    WHERE
                        tbl_survey.sid IS NOT NULL AND
                        DATEDIFF(tbl_survey.sdate, tmp_survey.sdate) <
                        {control_days}
                    """).format(extra=self.options))

                # do seperate to not have ambigious columns in
                # tmp_survey and tmp_survey2
                utils.query(tools.Format("""
                    DELETE
                        tmp_survey2
                    FROM
                        tmp_survey2
                    {where_control}
                    """).format(extra=self.options))

                utils.query("""
                    CREATE
                        TEMPORARY TABLE tmp_survey3
                    SELECT
                        sid_uid, uid
                    FROM
                        tmp_survey2""")

                utils.query(tools.Format("""
                    DELETE
                        tmp_survey
                    FROM
                        tmp_survey
                    LEFT JOIN
                        tmp_survey3
                        ON tmp_survey3.sid_uid - 1 = tmp_survey.sid_uid AND
                           tmp_survey3.uid = tmp_survey.uid
                    {where_control} AND
                    tmp_survey3.sid_uid IS NULL
                    """).format(extra=self.options))
                utils.drop_table("tmp_survey3")

                if self.options["survey_cutter"] != "":
                    if self.options["survey_cutter"].startswith("s3"):
                        # GP visit, take the original
                        self.options["new_cutter"] = tools.Format("""
                            IF(tmp_survey.{survey_cutter} IS NOT NULL AND
                               tmp_survey.{survey_cutter} NOT IN ("e", "d"),
                               tmp_survey.{survey_cutter},
                               tmp_survey2.{survey_cutter})
                            """).format(extra=self.options)
                    elif self.options["survey_cutter"].startswith("s4"):
                        # Stay home, take the last
                        self.options["new_cutter"] = tools.Format("""
                            IF(tmp_survey2.{survey_cutter} IS NOT NULL AND
                               tmp_survey2.{survey_cutter} NOT IN ("e", "d"),
                               tmp_survey2.{survey_cutter},
                               tmp_survey.{survey_cutter})
                            """).format(extra=self.options)
                    else:
                        raise IAPError(
                            ("survey_cutter {0} has to be defined" +
                             " for the max").format(
                                 self.options["survey_cutter"]))

                    utils.query(tools.Format("""
                        UPDATE
                            tmp_survey
                        LEFT JOIN
                            tmp_survey2
                            ON tmp_survey.sid_uid = tmp_survey2.sid_uid - 1 AND
                               tmp_survey.uid = tmp_survey2.uid
                        SET
                            tmp_survey.{survey_cutter} = {new_cutter}
                        WHERE
                            tmp_survey2.sid_uid IS NOT NULL
                        """).format(extra=self.options))

                utils.drop_table("tmp_survey3")
                utils.drop_table("tmp_survey2")

    def fill_series(self, category):
        """Fill the series table for joins or leaves"""

        sql = split.get_sql(
            self.options["full_cutter"], self.options["period"])
        if category == "cases" and self.options["survey_cutter"] != "":
            utils.query(tools.Format("""
                CREATE
                    TEMPORARY TABLE tmp_series
                SELECT
                    %(dataset)s AS dataset,
                    {onset_column} AS date,
                    IFNULL({survey_cutter}, '') AS label,
                    COUNT(*) AS value
                FROM
                    tmp_survey
                LEFT JOIN
                    tmp_intake USING (uid)
                GROUP BY
                    date, label
                """).format(extra=self.options), self.options)
        elif category == "cases":
            utils.query(tools.Format("""
                CREATE
                    TEMPORARY TABLE tmp_series
                SELECT
                    %(dataset)s AS dataset,
                    {onset_column} AS date,
                    {sql} AS label,
                    COUNT(*) AS value
                FROM
                    tmp_survey
                LEFT JOIN
                    tmp_intake USING (uid)
                GROUP BY
                    date, label
                """).format(sql=sql, extra=self.options), self.options)
        elif category in ("joins", "leaves"):
            utils.query(
                tools.Format("""CREATE
                    TEMPORARY TABLE tmp_series
                SELECT
                    %(dataset)s AS dataset,
                    IFNULL({date}, "0000-00-00") AS date,
                    {sql} AS label,
                    count(*) AS value
                FROM
                    tmp_intake
                GROUP BY
                    date, label
                """).format(
                    date=("start_date" if category == "joins" else
                          "DATE_ADD(end_date, INTERVAL '1' DAY)"),
                    sql=sql,
                    extra=self.options),
                self.options)
        else:
            raise IAPError("Unknown category {0}".format(category))
