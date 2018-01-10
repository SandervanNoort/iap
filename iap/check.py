#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Check if all columns are converted"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import re
import logging

import natsort

from .convert import Convert
from . import config, utils, tools

NULL_VALUES = [None, "", "\\N", "NULL", "f", "-1"]
logger = logging.getLogger(__name__)


class Check(Convert):
    """Import influenzanet data"""

    def __init__(self, period):
        Convert.__init__(self, period)
        self.tbl_columns = self._get_tbl_columns()

    def missing(self):
        """Show columns/values not configured"""

        if not self.src:
            return

        missing_cols = {}
        for table in ["intake", "survey"]:
            self._missing_table(table)

            dbvals = self.dbvals[table]["old"]
            for tbl, columns in self.tbl_columns[table].items():
                if tbl not in missing_cols:
                    missing_cols[tbl] = tools.SetList(columns)
                missing_cols[tbl] -= dbvals.keys()

        for tbl, columns in missing_cols.items():
            for column in columns:
                logger.warning("Column {column} in {tbl} is not" +
                               " configured".format(column=column, tbl=tbl))

    def add_extra_vals(self, dbvals, table):
        """Add the extra/removed/empty dbvals"""

        cache = tools.Cache()

        for key in ("remove", "empty", "unknown", "ignore"):
            for tbl in [table] + [tbl for tbl, _ in self._get_joins(table)]:
                if key in self.dbini and tbl in self.dbini[key]:
                    for qold in self.dbini[key][tbl].keys():
                        if cache(re.search("(.+){0}(.+)".format(
                                config.SEP["qa"]), qold)):
                            question, answer = cache.output.groups()
                            if question not in dbvals:
                                dbvals[question] = {}
                            dbvals[question][answer] = key
                        else:
                            dbvals[qold] = key

        for qold in list(dbvals.keys()):
            if cache(re.match(r"^IF\(([^ ]*) ", qold)):
                dbvals[cache.output.group(1)] = dbvals[qold]
                del dbvals[qold]

    def _get_tbl_columns(self):
        """Return all the tables and columns associated with table"""

        cache = tools.Cache()
        tbl_columns = {}
        for table in ["intake", "survey"]:
            tbl_columns[table] = {
                self.tables[table, "orig"]:
                utils.get_columns(self.tables[table, "orig"])}

            if "{0}_joins".format(table) in self.dbini:
                for left_join in self.dbini["{0}_joins".format(table)]:
                    if cache(re.search(r"(.*)\[.*\]", left_join)):
                        tbl_columns[table][cache.output.group(1)] \
                            = utils.get_columns(cache.output.group(1))
        return tbl_columns

    def _get_orig_tbl(self, qold, values, table):
        """Return the orig_table which should be checked for sql_vals"""

        orig_tbl = None
        for tbl, columns in self.tbl_columns[table].items():
            if qold in columns:
                orig_tbl = tbl

        if values == "remove":
            return None

        if orig_tbl is None:
            logger.warning(
                ("Column {qold} defined in config, but not" +
                 " available in {tbl} (+joins)").format(
                     qold=qold,
                     tbl=self.tables[table, "orig"],
                     src=self.src))
            return None

        if values == "unknown":
            return None

        if values == "ignore":
            return None

        return orig_tbl

    def _missing_table(self, table):
        """Show columns/values not configured for table"""

        dbvals = self.dbvals[table]["old"]
        self.add_extra_vals(dbvals, table)

        for qold, values in dbvals.items():
            orig_tbl = self._get_orig_tbl(qold, values, table)
            if orig_tbl is None:
                continue

            cursor = utils.query("""SELECT
                    DISTINCT {qold} AS qold
                FROM
                    {tbl}
                LIMIT
                    10000
                """.format(tbl=orig_tbl, qold=qold))
            values_distinct = [row["qold"] for row in cursor.fetchall()]

            values_distinct = tools.SetList(
                [None if val in config.CONFIG["settings"]["null_values"] else
                 val
                 for val in values_distinct])

            if values == "empty":
                if len(values_distinct) == 1:
                    # columns which are empty
                    continue

                cursor = utils.query("""SELECT
                        {qold} AS qold, count(*) AS tot
                    FROM
                        {tbl}
                    GROUP BY
                        qold
                    """.format(tbl=orig_tbl, qold=qold))
                values_tot = dict([(row["qold"], row["tot"])
                                   for row in cursor.fetchmany(10)])
                values_tot = {key: val
                              for key, val in values_tot.items()
                              if val > 5}

                if len(values_tot) > 1:
                    logger.warning(
                        ("Column {qold} configured as empty in" +
                         " {tbl}, but continues values: {tots}?").format(
                             qold=qold,
                             tbl=orig_tbl,
                             tots=values_tot))
                continue

            if None in values:
                if len(values_distinct) == 1:
                    logger.warning(
                        ("Column {qold} in {tbl} configured but" +
                         " it seems empty: {distinct}").format(
                             qold=qold,
                             tbl=orig_tbl,
                             distinct=values_distinct))
                continue

            sql_vals = tools.SetList(tools.flatten(
                [self._value_to_list(val)
                 for val in values_distinct]))
            sql_vals = natsort.natsorted(sql_vals)

            for sql_val in sql_vals:
                if (sql_val not in dbvals[qold] and
                        sql_val is not None and
                        (sql_val != "0" or len(dbvals[qold]) != 1)):
                    logger.warning(
                        ("Column {qold} in {tbl} contains value" +
                         " {sql_val} but is not configured").format(
                             qold=qold, sql_val=sql_val, tbl=orig_tbl))
            for db_val in dbvals[qold].keys():
                if db_val not in sql_vals:
                    logger.warning(
                        ("Column {qold} in {tbl} configured" +
                         " value {db_val}, but not in the db").format(
                             qold=qold,
                             db_val=db_val,
                             tbl=orig_tbl))
