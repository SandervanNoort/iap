#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert various database formats to single one"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import glob
import re
import os
import sys  # pylint: disable=W0611
from six.moves import urllib  # pylint: disable=F0401
import collections
import paramiko
import subprocess
import logging
import six
import natsort
import mconvert

from .exceptions import IAPError
from . import utils, config, tools

EXTENSIONS = {"zip": "zip", "epi": "sql.gz", "sql": "sql.bz2",
              "dump": "dump"}
TMP_SQL = "/tmp/new.sql"
logger = logging.getLogger(__name__)


class Convert(object):
    """Import influenzanet data"""

    def __init__(self, period):
        self.period = period
        try:
            self.src = utils.period_to_src(self.period)
        except IAPError:
            self.src = None
            logger.error("No influenzanet period: {0}".format(self.period))
            return
        self.country, self.season = utils.period_to_country_season(period)

        self.dbini = utils.get_dbini(self.src)
        self.tables, self.dbvals = self._get_tables()

    def _get_tables(self):
        """All the interesting tables"""

        tables = {}
        dbvals = {}
        for table in ["intake", "survey"]:
            tables[(table, "new")] = utils.get_tbl(
                table, "new", self.period)

            tables[(table, "orig")] = utils.get_tbl(
                table, "orig",
                (self.dbini["{0}_orig".format(table)]
                 if "{0}_orig".format(table) in self.dbini else
                 self.src))

            tables[(table, "full")] = " ".join(
                [tables[(table, "orig")]] +
                ["left join {0} {1}".format(tbl, using)
                 for tbl, using in self._get_joins(table)])

            if table + "_src" in self.dbini:
                tables[(self.dbini[table + "_src"], "src")] = table

            dbvals[table] = self._get_dbvals(table)

            if table + "_src2" in self.dbini:
                tables[(self.dbini[table + "_src2"], "src")] = table + "2"
                tables[(table + "2", "orig")] = \
                    tables[(table, "orig")].replace(table, table + "2")
                tables[(table + "2", "new")] = tables[(table, "new")]
                tables[(table + "2", "full")] = \
                    tables[(table, "full")].replace(table, table + "2")
                dbvals[table + "2"] = self._get_dbvals(table + "2")

        return tables, dbvals

    def _get_dbvals(self, table):
        """Read the db/<period>.ini file to a dict"""

        dbvals_old = collections.OrderedDict()
        dbvals_new = collections.OrderedDict()
        for qa_new, qa_old in self.dbini[table].items():
            qnew, _split, anew = utils.split_qa(qa_new, config.SEP["qa"])
            qold, _split, aold = utils.split_qa(qa_old, config.SEP["qa"])

            if aold and not anew:
                anew = "1"

            if qold not in dbvals_old:
                dbvals_old[qold] = collections.defaultdict(list)
            dbvals_old[qold][aold].append((qnew, anew))

            if qnew not in dbvals_new:
                dbvals_new[qnew] = collections.defaultdict(list)
            dbvals_new[qnew][anew].append((qold, aold))

        return {"new": dbvals_new, "old": dbvals_old}

    def _add_orig_index(self):
        """Add indexes to orig tables if they have to be joined"""
        cache = tools.Cache()
        for table in ["intake", "survey"]:
            for join_table, join_string in self._get_joins(table):
                if cache(re.search(r"USING \((.*)\)", join_string)):
                    column = cache.output.group(1)
                    orig_table = self.tables[(table, "orig")]
                    utils.table_index(orig_table, column)
                    utils.table_index(join_table, column)

    def _get_joins(self, table):
        """Return the extra tables to be joined"""
        cache = tools.Cache()
        if "{0}_joins".format(table) in self.dbini:
            for left_join in self.dbini["{0}_joins".format(table)]:
                if cache(re.search(r"(.*)\[(.*)\]", left_join)):
                    yield cache.output.groups()

    def _update_gastro(self):
        """Determine which participants did participate in Gastronet"""

        if self.period != "pt08":
            return

        utils.connect()
        utils.query("""CREATE TEMPORARY TABLE tmp_uid
            SELECT
                DISTINCT {orig_survey}.uid
            FROM
                {orig_survey}
            LEFT JOIN
                {orig_gastro} USING (uid, date)
            WHERE
                {orig_gastro}.date IS NULL AND
                {orig_survey}.date <= "2009-5-1"
                """.format(orig_survey="orig_survey_{0}".format(self.period),
                           orig_gastro="orig_gastro_{0}".format(self.period)))

        utils.query("""ALTER TABLE tmp_uid ADD INDEX(uid)""")

        utils.add_columns(
            self.tables["intake", "new"],
            [("nogastro", "BOOL NOT NULL DEFAULT 0")])
        utils.query("""UPDATE {tbl_intake}
                SET
                    nogastro=1
                WHERE
                    uid IN (SELECT uid FROM tmp_uid)
                """.format(tbl_intake=self.tables["intake", "new"]))
        utils.drop_table("tmp_uid")

    def delete_orig(self, table):
        """Delete the orig table to save space"""
        if self.src is None:
            return
        utils.connect()
        utils.drop_table(self.tables[table, "orig"])

    def fill(self, table):
        """Fill the table intake / survey"""

        if self.src is None:
            return

        if not utils.table_exists(self.tables[table, "orig"]):
            logger.error("No downloaded {table} data for src: {src}".format(
                table=table, src=self.src))
            return

        logger.info("Fill table {0} for {1}".format(table, self.period))
        utils.connect()
        self._add_orig_index()

        self.create_new_table(table)
        limit = self.dbini["{0}_limit".format(table)] \
            if "{0}_limit".format(table) in self.dbini \
            else ""
        order = self.dbini["{0}_order".format(table)] \
            if "{0}_order".format(table) in self.dbini \
            else ""

        if self.dbini["rowtype"] == "python":
            self._fill_python(table, limit, order)
        elif self.dbini["rowtype"] == "sql":
            self._fill_sql(table, limit, order)
            if table + "2" in self.dbvals:
                self._fill_sql(table + "2", limit, order)
        else:
            raise IAPError(
                "Rowtype has to be 'python' or 'sql': {0}".format(
                    self.dbini["rowtype"]))

        if table == "survey":
            self._update_gastro()

        utils.query("OPTIMIZE TABLE {0}".format(self.tables[table, "new"]))

    def create_new_table(self, table):
        """Create a new table"""

        columns = collections.defaultdict(tools.SetList)

        for ext in ["", "2"]:
            if table + ext not in self.dbvals:
                continue
            for column in self.dbvals[table + ext]["new"].keys():
                question, _split, answer = utils.split_qa(column, "_")
                if answer is None:
                    columns[question] = None
                else:
                    columns[question].append(answer)

        sql_columns = []
        for column, values in config.TABLE[table].items():
            if ("type" not in values or
                    values["type"] == "options" or
                    "src" not in values and column not in columns):
                continue

            if (columns[column] is None and
                    values["type"] in ("checkbox", "radio")):
                raise IAPError(
                    ("Column {col} should be a column" +
                     " but is a value for {src}").format(
                         col=column, src=self.src))

            sqltype = "varchar({0:d})".format(4 * len(columns[column])) \
                if values["type"] in ("checkbox", "radio") \
                else values["type"]

            sql_columns.append("{0} {1}".format(column, sqltype))
            if values["type"] in ("checkbox", "radio"):
                for key in natsort.natsorted(columns[column]):
                    sql_columns.append("{0}_{1} {2}".format(
                        column, key, "BOOL NOT NULL DEFAULT 0"))

        if "mysql" in config.TABLE[table]:
            sql_columns.append(config.TABLE[table]["mysql"])

        utils.drop_table(self.tables[table, "new"])
        utils.query(
            "CREATE TABLE {tbl} ({columns})".format(
                tbl=self.tables[table, "new"],
                columns=",\n".join(sql_columns)))

    def _fill_sql(self, table, limit, order):
        """Fill tbl_new with values from tbl_orig, directly by sql"""

        dbvals = self.dbvals[table]["new"]
        cols_new = []
        cols_old = []
        for qnew, values in dbvals.items():
            sql = utils.get_default(re.sub(r"\d+", "", table), qnew)
            for anew, colvals in tools.sort_iter(values, natural=True):
                if len(colvals) != 1:
                    raise IAPError("Not implemented: {0} - {1}".format(
                        qnew, values))
                qold, aold = colvals[0]
                if aold is None and anew is None:
                    sql = qold
                elif anew.startswith("++"):
                    anew = anew[2:]
                    if not isinstance(sql, list):
                        sql = []
                    sql.append("""NULLIF(SUBSTR(REPEAT({val}, {count}),
                           1, {count} * LENGTH({val}) - 1
                           ), '')
                    """.format(
                        count="LEAST({max_val}, {qold})".format(
                            qold=qold,
                            max_val=config.CONFIG["settings"]["max_count"]),
                        val="CONCAT('{anew}', '{sep}')".format(
                            anew=anew,
                            sep=config.SEP["multi"])))
                elif aold is not None:
                    sql = "IF({qold}='{aold}', '{anew}', {sql})".format(
                        qold=qold, aold=aold, anew=anew, sql=sql)
                else:
                    raise IAPError(
                        ("aold is none but anew not ++:" +
                         " anew = {anew}").format(anew=anew))

            if isinstance(sql, list):
                sql = "CONCAT_WS(\"{sep}\", {sqlvals})".format(
                    sep=config.SEP["multi"],
                    sqlvals=",\n".join(sql))

            cols_new.append(qnew)
            cols_old.append(sql)

        country_check = ""
        if "country" in self.dbini and table == "intake":
            country_check = "WHERE {country_col} = '{country}'".format(
                country_col=self.dbini["country"],
                country=self.country)
        elif "orig_uid" in self.dbini and table == "survey":
            utils.query("""CREATE TEMPORARY TABLE tmp_uid
                    (SELECT uid from {tbl_intake})
            """.format(
                tbl_intake=self.tables["intake", "new"]))
            utils.query("ALTER TABLE tmp_uid ADD INDEX(uid)")

            utils.column_type(
                self.tables[table, "orig"],
                self.dbini["orig_uid"], "VARCHAR(40)")
            utils.table_index(
                self.tables[table, "orig"],
                self.dbini["orig_uid"])

            country_check = """LEFT JOIN tmp_uid
                ON {tbl_orig}.{orig_uid} = tmp_uid.uid
            WHERE
                tmp_uid.uid IS NOT NULL
            """.format(
                tbl_orig=self.tables[table, "full"],
                orig_uid=self.dbini["orig_uid"])

        utils.query("""INSERT INTO {tbl_new}
                ({keys})
            SELECT
                {values}
            FROM
                {tbl_orig}
            {country_check}
                {limit}
                {order}
            """.format(tbl_new=self.tables[table, "new"],
                       keys=",".join(cols_new),
                       values=",".join(cols_old),
                       tbl_orig=self.tables[table, "full"],
                       country_check=country_check,
                       order=order,
                       limit=limit))
        if "orig_uid" in self.dbini and table == "survey":
            utils.drop_table("tmp_uid")

    def _fill_python(self, table, limit, order, index=0):
        """Filling the columns for the new table, reading line by line"""

        cols_new = list(self.dbvals[table]["new"].keys())
        rows = []
        cursor = utils.query("""SELECT
                {columns_old}
            FROM
                {tbl}
            WHERE
                {country_col} = '{country}'
                {limit}
                {order}
            LIMIT
                {index}, {size}
        """.format(
            tbl=self.tables[table, "full"],
            columns_old=",".join(self.dbvals[table]["old"].keys()),
            country_col=(self.dbini["country"]
                         if "country" in self.dbini else
                         "'{0}'".format(self.country)),
            index=index,
            size=config.LOCAL["db"]["size"],
            country=self.country,
            limit=limit,
            order=order))
        # country in format() because str_to_date contains %-signs

        for row in cursor.fetchall():
            sql_dict = self._get_sql_dict(row, table)
            rows.append([sql_dict[key] if key in sql_dict else None
                         for key in cols_new])
        if len(rows) > 0:
            utils.query(
                """INSERT INTO {tbl_new}
                    ({columns}) VALUES ({values})
                """.format(tbl_new=self.tables[table, "new"],
                           columns=",".join(cols_new),
                           values=",".join(["%s"] * len(cols_new))),
                rows, many=True)
            self._fill_python(table, limit, order,
                              index + config.LOCAL["db"]["size"])

    def _value_to_list(self, value):
        """Split a mysql-value into a list"""

        if isinstance(value, list):
            return value
        elif (isinstance(value, six.string_types) and
              re.match("^c[0-9]+$", value)):
            return list(tools.flatten(
                [int(value[-pos]) * ["{0}".format(pos - 1)]
                 for pos in range(1, len(value))]))
        elif (isinstance(value, six.string_types) and
              self.dbini["multi_sep"] in value):
            return value.split(self.dbini["multi_sep"])
        elif isinstance(value, (six.integer_types, float)):
            return ["{0}".format(value)]
        else:
            return [value]

    def _get_sql_dict(self, row, table):
        """Return a sqldict of the row"""

        sql_dict = {}
        dbvals = self.dbvals[table]["old"]
        for column, value in row.items():
            column = self.get_column(column, dbvals.keys())
            if "python" in self.dbini and column in self.dbini["python"]:
                # the variable "value" is directly manipulated
                # (Use of exec) pylint: disable=W0122
                exec(self.dbini["python"][column].format(value))
                # (Use of exec) pylint: enable=W0122
            if value is None:
                continue

            values = self._value_to_list(value)
            for aold in values:
                if aold in dbvals[column]:
                    for qnew, anew in dbvals[column][aold]:
                        self.add_value(sql_dict, qnew, anew)
                if None in dbvals[column]:
                    for qnew, anew in dbvals[column][None]:
                        if anew is None:
                            sql_dict[qnew] = value
                        else:
                            try:
                                value = int(value)
                            except ValueError:
                                continue
                            for _counter in range(min(
                                    value,
                                    config.CONFIG["settings"]["max_count"])):
                                self.add_value(sql_dict, qnew, anew)
        return sql_dict

    @staticmethod
    def get_column(column, all_columns):
        """Return the column name"""
        # if multiple columns with the same name appear in multiple tables
        # the first column does not get the tablename
        if column in all_columns:
            return column

        for column2 in all_columns:
            if column2.endswith(column):
                return column2
        raise IAPError("Unknown column {0}".format(column))

    @staticmethod
    def add_value(mydict, qnew, value):
        """Update the sql_dict value, and append for ++value"""

        if isinstance(value, six.string_types) and value.startswith("++"):
            value = value[2:]
            if qnew in mydict:
                value = config.SEP["multi"].join(
                    natsort.natsorted(
                        mydict[qnew].split(config.SEP["multi"]) + [value]))
        mydict[qnew] = value

    def download(self):
        """Download the data from external server"""
        if self.src is None:
            return

        host = utils.get_value(
            config.CONFIG["country"][self.country], "host", self.season)
        if not host:
            logger.error("No download credentials for {0}".format(self.src))
            return

        ssh_params = config.LOCAL["host"][host]

        local_file = os.path.join(
            config.LOCAL["dir"]["download"],
            "inet",
            "{0}.{1}".format(self.src, EXTENSIONS[self.dbini["dbtype"]]))
        tools.create_dir(local_file)

        if "url" in ssh_params:
            logger.info("Download data for {0}".format(self.src))
            urllib.request.urlretrieve(ssh_params["url"], local_file)
            return
        elif "username" not in ssh_params or "hostname" not in ssh_params:
            logger.error("No user/host or url for src {0}".format(self.src))
            return

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if "password" in ssh_params:
            ssh.connect(ssh_params["hostname"],
                        username=ssh_params["username"],
                        password=ssh_params["password"])
        else:
            keyfile = ssh_params["keyfile"] if "keyfile" in ssh_params \
                else os.path.join(os.path.expanduser("~"), ".ssh", "id_dsa")
            ssh.connect(ssh_params["hostname"],
                        username=ssh_params["username"],
                        key_filename=keyfile)

        def ssh_exec(cmd):
            """Execute an ssh command and return output"""
            stdin, _stdout, _stderr = ssh.exec_command(cmd)
            return stdin.channel.recv_exit_status()

        if "fname" in ssh_params:
            server_file = ssh_params["fname"]
        else:
            cmd = "rm -Rf {0} && mkdir {0}".format(
                config.CONFIG["settings"]["server_tmp"])
            ssh_exec(cmd)

            server_file = self.download_zip(ssh_exec, ssh_params) \
                if self.dbini["dbtype"] == "zip" \
                else self.download_epi(ssh_exec) \
                if self.dbini["dbtype"] == "epi" \
                else self.download_sql(ssh_exec, ssh_params) \
                if self.dbini["dbtype"] == "sql" \
                else None

        logger.info("Download data for {0}".format(self.src))
        sftp = ssh.open_sftp()
        try:
            sftp.get(server_file, local_file)
        except IOError:
            logger.error("Cannot download {server} to {local}".format(
                server=server_file, local=local_file))
            return
        ssh_exec("rm -Rf {0}".format(config.CONFIG["settings"]["server_tmp"]))

    def download_epi(self, ssh_exec):
        """Download inet data from toast server"""
        logger.info("Generate remote zip for {0}".format(self.src))
        server_file = "{0}/{1}.sql.gz".format(
            config.CONFIG["settings"]["server_tmp"], self.src)

        cmd = ("cp /home/{epi}/epidb_results.sql {tmp}/{src}.sql" +
               " && gzip {tmp}/{src}.sql").format(
                   tmp=config.CONFIG["settings"]["server_tmp"],
                   src=self.src, epi=config.CONFIG["epi"][self.src])
        ssh_exec(cmd)
        return server_file

    def download_zip(self, ssh_exec, ssh_params):
        """Download inet data from toast server"""

        logger.info("Generate remote zip for {0}".format(self.src))
        server_file = "{0}/{1}.zip".format(
            config.CONFIG["settings"]["server_tmp"], self.src)
        for table in ["survey", "intake"]:
            cmd = ("psql -c \"copy (SELECT * FROM {table}) TO STDOUT" +
                   " WITH CSV HEADER;\" > {tmp}/{csv}").format(
                       table=ssh_params[table],
                       tmp=ssh_params["csv"],
                       csv="{0}_{1}.csv".format(self.src, table))
            ssh_exec(cmd)

        cmd = ("zip --junk-paths -r {tmp}/{src}.zip {tmp}/*csv").format(
            tmp=config.CONFIG["settings"]["server_tmp"], src=self.src)
        ssh_exec(cmd)
        return server_file

    def download_sql(self, ssh_exec, ssh_params):
        """Download data from mysql server"""

        logger.info("Generate sql for {0}".format(self.src))
        server_sqlfile = "{0}/{1}.sql".format(
            config.CONFIG["settings"]["server_tmp"], self.src)
        server_file = "{0}/{1}.sql.bz2".format(
            config.CONFIG["settings"]["server_tmp"], self.src)

        cmd = ("{mysqldump} --quote-names --opt {db} {intake}" +
               " {survey} {tables} > {server_sqlfile}").format(
                   mysqldump=ssh_params["mysqldump"],
                   db=ssh_params["db"],
                   intake=ssh_params["intake"],
                   survey=ssh_params["survey"],
                   tables=" ".join(ssh_params["tables"]),
                   server_sqlfile=server_sqlfile)
        ssh_exec(cmd)

        replace = " ".join(
            ["-e s/\\`{}\\`/\\`{}\\`/g".format(orig, new)
             for orig, new in zip(
                 list(ssh_params["tables"]) +
                 [ssh_params["intake"]] +
                 [ssh_params["survey"]],
                 list(ssh_params["tables_translate"]) +
                 [self.tables["intake", "orig"]] +
                 [self.tables["survey", "orig"]])])
        ssh_exec(("sed {replace} {server_sqlfile}" +
                  " > {server_sqlfile}.tmp").format(
                      replace=replace,
                      server_sqlfile=server_sqlfile))
        ssh_exec("mv {0}.tmp {0}".format(server_sqlfile))

        ssh_exec("bzip2 -f {0}".format(server_sqlfile))
        return server_file

    def sqlimport(self):
        """Fill orig tables from the download inet data"""

        if not self.src:
            return False

        logger.info("Import sql for {0}".format(self.src))
        imported = False

        def rename_tbl(orig):
            """Rename table to orig_{period}"""
            orig = tools.to_unicode(orig)
            if orig in [
                    "orig_intake_{0}".format(self.src),
                    "orig_survey_{0}".format(self.src)]:
                dest = orig
            elif orig == self.dbini.get("survey_src"):
                dest = "orig_survey_{0}".format(self.src)
            elif orig == self.dbini.get("intake_src"):
                dest = "orig_intake_{0}".format(self.src)
            else:
                logger.error("Unknown sql table: {0}".format(orig))
                dest = orig

            return dest.encode("utf8")

        for basename in [self.src] + self.dbini["extra_import"]:
            for fname in glob.glob(
                    os.path.join(
                        config.LOCAL["dir"]["download"], "inet", basename) +
                    ".*"):
                imported = True
                tools.remove_file(TMP_SQL)
                converted, _not_converted = mconvert.convert_fname(
                    fname, TMP_SQL,
                    ftypes=["application/sql-mysql",
                            "application/sql-mysql_application/sql-mysql"],
                    options=[("rename_tbl", rename_tbl)],
                    unpack=True)
                if TMP_SQL not in converted:
                    logger.error("Not converted: {0}".format(fname))
                    return False
                cmd = (
                    "mysql -u {mysql_user}" +
                    " -p{mysql_pass} {mysql_db} < {tmp_sql}").format(
                        mysql_user=config.LOCAL["db"]["user"],
                        mysql_pass=config.LOCAL["db"]["pass"],
                        mysql_db=config.LOCAL["db"]["db"],
                        tmp_sql=TMP_SQL)
                try:
                    subprocess.check_call(cmd, shell=True)
                except subprocess.CalledProcessError:
                    logger.error("Failed import sql for {0}".format(self.src))
                    return False
        return imported
