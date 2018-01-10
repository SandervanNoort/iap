#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Update the intake/survey tables"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import collections
import re
import logging

from .exceptions import IAPError
from . import utils, config, tools

logger = logging.getLogger(__name__)


class Update(object):
    """Update the intake/survey tables"""

    def __init__(self, period):
        self.period = period
        try:
            self.src = utils.period_to_src(self.period)
        except IAPError:
            self.src = None
            logger.error("No influenzanet period: {0}".format(self.period))
            return

        self.country, self.season = utils.period_to_country_season(period)
        self.tables = {
            (table, "new"): utils.get_tbl(
                table, "new", self.period)
            for table in ["intake", "survey"]}
        self.dbini = utils.get_dbini(self.src)

    def survey_update(self):
        """Update the table survey"""
        if self.src is None:
            return

        if not utils.table_exists(self.tables["survey", "new"]):
            return
        logger.info("Update survey table for {0}".format(self.period))
        utils.connect()

        # Only keep the latest entry for each user and date
        utils.query("""CREATE TEMPORARY TABLE tmp_id_uid
            (SELECT
                MAX(sid) as max, uid, sdate
            FROM
                {tbl_survey}
            GROUP BY
                uid, sdate
            HAVING
                COUNT(sid) > 1
            )""".format(tbl_survey=self.tables["survey", "new"]))
        utils.query("""DELETE {tbl_survey}
            FROM
                {tbl_survey}
            LEFT JOIN
                tmp_id_uid USING (uid, sdate)
            WHERE
                sid != max
            """.format(tbl_survey=self.tables["survey", "new"]))
        utils.drop_table("tmp_id_uid")

        # Set survey date (if empty) from onset date of symptoms or fever
        utils.query("""UPDATE {tbl_survey}
            SET
                sdate = IF(s110<s210, s110, s210)
            WHERE
                sdate IS NULL AND
                (s110 IS NOT NULL OR s210 IS NOT NULL)
            """.format(tbl_survey=self.tables["survey", "new"]))

        # Set symptoms date to null, if no symptoms
        columns = utils.get_columns(self.tables["survey", "new"])
        symptom_columns = [
            column for column in columns
            if column.startswith("s100_")]
        if len(symptom_columns) > 0:
            where_symptoms = " OR ".join([
                "{0}=1".format(col)
                for col in symptom_columns])
            cursor = utils.query("""UPDATE {tbl_survey}
                SET
                    s110 = NULL
                WHERE
                    s110 IS NOT NULL AND
                    NOT({where_symptoms})
                """.format(tbl_survey=self.tables["survey", "new"],
                           where_symptoms=where_symptoms))
            logger.info("{tot} symptoms dates in {period} set to null".format(
                tot=cursor.rowcount, period=self.period))
        else:
            logger.info("No symptom columns for {period}".format(
                period=self.period))

        # Fill the column sid_uid
        sid_uid = 1
        updated = True
        while updated:
            cursor = utils.query("""UPDATE {tbl_survey}
                INNER JOIN
                (SELECT
                    uid, MIN(sid) as sid
                FROM
                    {tbl_survey}
                WHERE
                    sid_uid IS NULL
                GROUP BY
                    uid) AS min_uid
                USING (uid, sid)
                SET
                    {tbl_survey}.sid_uid = {sid_uid}
                """.format(tbl_survey=self.tables["survey", "new"],
                           sid_uid=sid_uid))
            sid_uid += 1
            updated = cursor.rowcount > 0

        # Set fever date to null, if no fever
        where_fever = utils.check_db("s200>='370' OR s100_18", self.period)
        cursor = utils.query("""UPDATE {tbl_survey}
            SET
                s210 = NULL
            WHERE
                s210 IS NOT NULL AND
                NOT({where_fever})
            """.format(tbl_survey=self.tables["survey", "new"],
                       where_fever=where_fever))
        logger.info("{tot} fever dates in {period} set to null".format(
            tot=cursor.rowcount, period=self.period))

        # Delete survey which have no date at all
        utils.query("""DELETE FROM {tbl_survey}
            WHERE
                sdate IS NULL
            """.format(tbl_survey=self.tables["survey", "new"]))

        # Delete symptoms date if after survey date
        utils.query("""UPDATE {tbl_survey}
            SET
                s110 = NULL
            WHERE
                s110 > sdate
            """.format(tbl_survey=self.tables["survey", "new"]))

        # Delete fever date if after survey date
        utils.query("""UPDATE {tbl_survey}
            SET
                s210 = NULL
            WHERE
                s210 > sdate
            """.format(tbl_survey=self.tables["survey", "new"]))

    def intake_update(self):
        """Update the table intake without need for survey table"""

        if self.src is None:
            return

        tbl_intake = self.tables["intake", "new"]
        if not utils.table_exists(tbl_intake):
            return

        logger.info("Update table {0}".format(tbl_intake))
        utils.connect()

        utils.query("""CREATE TEMPORARY TABLE tmp_qid_uid
            (SELECT
                MAX(qid) AS max, uid
            FROM
                {tbl_intake}
            GROUP BY
                uid
            HAVING
                COUNT(qid) > 1
            )""".format(tbl_intake=tbl_intake))
        utils.query("ALTER TABLE tmp_qid_uid ADD INDEX(uid)")

        utils.query("""DELETE {tbl_intake}
            FROM
                {tbl_intake}
            LEFT JOIN
                tmp_qid_uid USING (uid)
            WHERE
                qid != max
            """.format(tbl_intake=tbl_intake))
        utils.drop_table("tmp_qid_uid")

    def both_update(self):
        """Update the table intake without need for survey table"""

        if self.src is None:
            return

        if (not utils.table_exists(self.tables["intake", "new"]) or
                not utils.table_exists(self.tables["survey", "new"])):
            return
        logger.info("Update table {0} and {1}".format(
            self.tables["intake", "new"],
            self.tables["survey", "new"]))
        utils.connect()

        # Fill the vaccin column if later vaccinated
        for survey_col, intake_col in [
                ("s600_1", "q700_3"),
                ("s610_1", "q730_3")]:
            if survey_col in utils.get_columns(
                    self.tables["survey", "new"]):
                utils.add_columns(
                    self.tables["intake", "new"],
                    [(intake_col, "BOOL NOT NULL DEFAULT 0")])
                utils.query("""CREATE TEMPORARY TABLE tmp_uid
                    SELECT
                        DISTINCT uid
                    FROM
                        {tbl_survey} AS tbl_survey
                    WHERE
                        {survey_col} = '1'
                    """.format(survey_col=survey_col,
                               tbl_survey=self.tables["survey", "new"]))
                utils.query("ALTER TABLE tmp_uid ADD INDEX(uid)")
                utils.query("""UPDATE {tbl_intake} AS tbl_intake
                    SET
                        {intake_col} = '1'
                    WHERE
                        uid IN (SELECT uid FROM tmp_uid)
                    """.format(intake_col=intake_col,
                               tbl_intake=self.tables["intake", "new"]))
                utils.drop_table("tmp_uid")

        # surveys     = Number of completed surveys
        # days        = Number of active days
        # freq        = Average time between surveys
        utils.query("""
            UPDATE
                {tbl_intake} AS tbl_intake,
                (SELECT
                    uid,
                    COUNT(sid) AS surveys,
                    DATEDIFF(MAX(sdate), MIN(sdate)) AS days,
                    ROUND(DATEDIFF(MAX(sdate), MIN(sdate))
                            / (COUNT(sid) - 1)) AS freq
                FROM
                    {tbl_survey} AS tbl_survey
                GROUP BY
                    uid) AS temp
            SET
                tbl_intake.surveys = temp.surveys,
                tbl_intake.days = temp.days,
                tbl_intake.freq = temp.freq
            WHERE
                tbl_intake.uid = temp.uid
            """.format(tbl_intake=self.tables["intake", "new"],
                       tbl_survey=self.tables["survey", "new"]))

        # set the default start_date (first_survey=2)
        utils.query("""
            UPDATE {tbl_intake} AS tbl_intake
            LEFT JOIN
                {tbl_survey} AS tbl_survey
                ON tbl_intake.uid = tbl_survey.uid AND
                   tbl_survey.sid_uid = '1'
            SET
                start_date = DATE_ADD(sdate, INTERVAL 1 DAY)
            """.format(tbl_intake=self.tables["intake", "new"],
                       tbl_survey=self.tables["survey", "new"]))

        # set the default end_date (last_survey=0)
        utils.query("""
            UPDATE {tbl_intake} AS tbl_intake
            LEFT JOIN
                {tbl_survey} AS tbl_survey
                ON tbl_intake.uid = tbl_survey.uid AND
                   tbl_survey.sid_uid = tbl_intake.surveys
            SET
                end_date = sdate
            """.format(tbl_intake=self.tables["intake", "new"],
                       tbl_survey=self.tables["survey", "new"]))

        if "q300" in utils.get_columns(self.tables["intake", "new"]):
            column = (
                "qdate" if "qdate" in utils.get_columns(
                    self.tables["intake", "new"]) else
                "start_date")
            utils.query("""
                UPDATE
                    {tbl_intake}
                SET age = IF(
                    DATE_ADD({column}, INTERVAL 1 - DAY({column}) DAY)<q300,
                    -1,
                    IF(
                        YEAR({column})=YEAR(q300),
                        -1,
                        (YEAR({column}) - YEAR(q300)) +
                        IF(
                            (MONTH({column}) - MONTH(q300))>=6,
                            1,
                            IF(
                                (MONTH(q300) - MONTH({column}))>=6,
                                -1,
                                0
                            )
                        )
                    )
                )""".format(tbl_intake=self.tables["intake", "new"],
                            column=column))

        # after the age
        self.add_children()

    def add_children(self, refill=False):
        """Add children to sql_dict"""

        if not utils.table_exists(self.tables["intake", "new"]):
            return

        columns = utils.get_columns(self.tables["intake", "new"])
        if "q1250" not in columns:
            return

        overlap = set(["q1200", "q1200_1", "q1200_2", "q1200_3",
                       "q1200_d"]).intersection(columns)
        if len(overlap) > 0 and not refill:
            return
        utils.drop_columns(self.tables["intake", "new"], overlap)
        utils.add_columns(
            self.tables["intake", "new"],
            [("q1200", "VARCHAR(10)"),
             ("q1200_d", "BOOL NOT NULL DEFAULT 0"),
             ("q1200_1", "BOOL NOT NULL DEFAULT 0"),
             ("q1200_2", "BOOL NOT NULL DEFAULT 0"),
             ("q1200_3", "BOOL NOT NULL DEFAULT 0")])

        q1200 = self.get_q1200()
        for answer, qids in q1200.items():
            utils.query(
                """UPDATE {tbl}
                   SET
                       q1200_{answer} = 1
                    WHERE
                        qid in ({qids})
                """.format(tbl=self.tables["intake", "new"],
                           answer=answer,
                           qids=",".join(["{0}".format(qid)
                                          for qid in qids])))

    def get_q1200(self):
        """Get a dictionary of the qids for the q1200 column"""

        q1200 = collections.defaultdict(list)
        cursor = utils.query("""SELECT
                qid, age, q1250
             FROM
                {tbl}
            """.format(tbl=self.tables["intake", "new"]))

        excluded = ["pt10", "pt11", "pt12", "uk10", "it10"]
        for row in cursor.fetchall():
            if row["q1250"] is None:
                q1200["d"].append(row["qid"])
                continue

            if row["q1250"] in ("", None):
                if self.period in excluded:
                    q1200["1"].append(row["qid"])
                else:
                    q1200["d"].append(row["qid"])
                continue

            kids, adults = 0, 0
            age = row["age"] if self.period not in excluded else None
            for age_range in row["q1250"].split(config.SEP["multi"]):
                min_age, max_age = (
                    (int(item) for item in age_range.split(
                        config.SEP["range"]))
                    if config.SEP["range"] in age_range else
                    (int(age_range) - 1, int(age_range) + 1)
                    if age_range.isdigit() else
                    (None, None))
                # todo: doesn't do anythin?
                # if min_age is None:
                #     pass
                if age is not None and age >= min_age and age <= max_age:
                    age = None
                    continue

                kid_threshold = 19 if self.period in ("uk10", "it10") else 18
                if max_age <= kid_threshold:
                    kids += 1
                elif min_age >= kid_threshold:
                    adults += 1

            if kids > 0:
                q1200[3].append(row["qid"])
            elif adults > 0:
                q1200[2].append(row["qid"])
            else:
                q1200[1].append(row["qid"])
        return q1200

    def datasets_delete(self):
        """Delete all datasets and series for this period"""

        if self.src is None:
            return

        logger.info("Delete datasets for period {0}".format(self.period))
        utils.query("""DELETE series
                FROM series, datasets
            WHERE
                series.dataset=datasets.dataset AND
                season=%(season)s AND
                country=%(country)s
            """, {"season": self.season, "country": self.country})

        utils.query("""UPDATE datasets
            SET
                updated = NULL
            WHERE
                season = %(season)s AND
                country = %(country)s
            """, {"season": self.season, "country": self.country})

        utils.query(
            """DELETE FROM linreg
            WHERE
                country = %(country)s AND
                seasons LIKE "%%{season}%%"
            """.format(season=self.season),
            {"country": self.country})

        utils.query("""DELETE FROM samples
            WHERE
                country = %(country)s AND
                season = "%(season)s"
            """, {"country": self.country, "season": self.season})

        utils.query(
            """DELETE baseline
                FROM baseline
            WHERE
                country = %(country)s AND
                seasons LIKE "%%{season}%%"
            """.format(season=self.season),
            {"country": self.country})

    def implode_columns(self, table):
        """Implode multiple columns col_1, col_3 => to col=1,3"""

        if (self.src is None or
                not utils.table_exists(self.tables[table, "new"])):
            return
        cache = tools.Cache()

        logger.info("Implode columns for {0}".format(
            self.tables[table, "new"]))

        utils.connect()

        implodes = collections.defaultdict(list)

        for column in utils.get_columns(self.tables[table, "new"]):
            if cache(re.search(r"([qs]\d+)_(.+)", column)):
                question, answer = cache.output.groups()
                implodes[question].append(
                    "IF({0}=1, '{1}', NULL)".format(column, answer))

        implodes2 = [
            "{question} = CONCAT_WS('{glue}',{answers})".format(
                question=question,
                answers=",".join(answers),
                glue=config.SEP["multi"])
            for question, answers in implodes.items()]

        if len(implodes2) > 0:
            utils.query("""UPDATE {tbl}
                SET
                    {implodes}
                """.format(tbl=self.tables[table, "new"],
                           implodes=",".join(implodes2)))
