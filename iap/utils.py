#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Various utils"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import re
import datetime
import MySQLdb
import MySQLdb.converters
import warnings
import os
import collections
import logging
import configobj
import sys  # pylint: disable=W0611
import six

from .exceptions import IAPError
from . import config, tools

warnings.filterwarnings('error', category=MySQLdb.Warning)
logger = logging.getLogger(__name__)


def connect():
    """Connnect to the database and close if necesarry"""

    conv_dict = MySQLdb.converters.conversions
    conv_dict[type(None)] = lambda a, b: str("DEFAULT")

    if config.CURSOR is not None:
        close()
    try:
        conn = MySQLdb.connect(host=config.LOCAL["db"]["host"],
                               user=config.LOCAL["db"]["user"],
                               passwd=config.LOCAL["db"]["pass"],
                               db=config.LOCAL["db"]["db"],
                               use_unicode=1,
                               conv=conv_dict)
    except MySQLdb.Error as inst:
        raise IAPError("{0}".format(inst))
    config.CURSOR = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    conn.autocommit(True)
    config.CURSOR.execute('set sql_mode=\'\'')


def get_tbl(table, orig, period):
    """Return the name of the table"""
    if orig == "new":
        return "{0}_{1}".format(table, period)
    elif orig == "orig":
        return "orig_{0}_{1}".format(table, period)
    else:
        raise IAPError("orig {0} should be new/orig".format(orig))


def close():
    """Close db connection"""
    if config.CURSOR is not None:
        try:
            if hasattr(config.CURSOR.connection, "commit"):
                config.CURSOR.connection.commit()
                config.CURSOR.connection.close()
            else:
                config.CURSOR.connection().commit()
                config.CURSOR.connection().close()
        except MySQLdb.ProgrammingError:
            pass


def get_default(table, column):
    """Return the default column value"""

    ini = config.TABLE[table]
    if column in ini:
        if "default" in ini[column]:
            return ini[column]["default"]
        else:
            return "NULL"
    elif "_" in column:
        return False
    else:
        raise IAPError("No default for column {0} in table {1}".format(
            column, table))


def period_available(period):
    """Return if a period is locally available"""
    if "available" not in config.PERIODS:
        period_valid(None)
        tables = get_tables()
        config.PERIODS["available"] = []
        for valid_period in config.PERIODS["valid"]:
            if (get_tbl("intake", "new", valid_period) in tables and
                    get_tbl("survey", "new", valid_period) in tables):
                config.PERIODS["available"].append(valid_period)
    return period in config.PERIODS["available"]


def period_valid(period):
    """Return if during a period influenzanet was active"""
    if "valid" not in config.PERIODS:
        config.PERIODS["valid"] = []
        for country, values in config.CONFIG["country"].items():
            if "inet" not in values:
                continue
            for season in values["inet"].keys():
                config.PERIODS["valid"].append(
                    country_season_to_period(country, season))
    return period in config.PERIODS["valid"]


def season_to_years(season):
    """Convert a seaon to the years"""
    return int(season[0:4]), int(season[0:4]) + 1


def year_to_season(year):
    """Convert a seaon to the years"""
    return "{0}/{1:02d}".format(year, (year + 1) % 100)


def prev_season(season):
    """Return the previous season"""
    years = season_to_years(season)
    return year_to_season(years[0] - 1)


def get_seasons(country):
    """Return all available seasons for a country"""
    if country in config.CONFIG["country"] \
            and "inet" in config.CONFIG["country"][country]:
        return config.CONFIG["country"][country]["inet"].keys()
    else:
        return []


def country_season_to_period(country, season):
    """Return period based on the country and season"""
    years = season_to_years(season)
    return "{0}{1:02d}".format(country, years[0] % 100)


def period_to_country_season(period):
    """Return country/season based on the period"""
    cache = tools.Cache()

    if cache(re.search(r"^(\w+)(\d\d)$", period)):
        country, yearshort = cache.output.groups()
        if int(yearshort) < 50:
            year = 2000 + int(yearshort)
        else:
            year = 1900 + int(yearshort)
        season = year_to_season(year)
        return country, season
    else:
        raise IAPError("Not a valid period: {0}".format(period))


def get_value(section, key, current=None):
    """Return section[key] or section[key][current] or section[key][default]"""

    if key in section.sections:
        if "{0}".format(current) in section[key]:
            return section[key]["{0}".format(current)]
        elif "default" in section[key]:
            return section[key]["default"]
        else:
            return None
    elif key in section:
        return section[key]
    else:
        return None


def period_to_src(period):
    """Return the db based on country and season"""
    country, season = period_to_country_season(period)
    tblsrc = get_value(config.CONFIG["country"][country], "src", season)
    if tblsrc and season in config.CONFIG["country"][country]["inet"]:
        return country_season_to_period(tblsrc, season)
    else:
        raise IAPError("No source for period {0}".format(period))


def get_times(times, min_year=2003, max_year=None):
    """Return all countries, periods and seasons"""
    # (too many branches)  pylint: disable=R0912

    cache = tools.Cache()
    if max_year is None:
        max_year = int(config.CONFIG["settings"]["max_year"])

    complete = {"countries": config.CONFIG["country"].keys(),
                "seasons": [year_to_season(year)
                            for year in range(max_year - 1, min_year - 1, -1)],
                "years": range(max_year, min_year - 1, -1)}
    complete["periods"] = [country_season_to_period(country, season)
                           for country in complete["countries"]
                           for season in complete["seasons"]]
    selected = {"countries": tools.SetList(),
                "seasons": tools.SetList(),
                "periods": tools.SetList(),
                "years": tools.SetList()}
    errors = []
    for key in times:
        if key.isdigit():
            key = int(key)

        if key == "ALL":
            selected["countries"].extend(complete["countries"])
            selected["seasons"].extend(complete["seasons"])
        elif key == "INET":
            selected["periods"] = tools.SetList()
            for country, values in config.CONFIG["country"].items():
                if "inet" not in values:
                    continue
                for season in values["inet"].keys():
                    selected["periods"].append(
                        country_season_to_period(country, season))
        elif key == "CURRENT":
            selected["seasons"].append(year_to_season(max_year - 1))
            selected["countries"].extend(complete["countries"])
        elif key in complete["countries"]:
            selected["countries"].append(key)
        elif key in complete["seasons"]:
            selected["seasons"].append(key)
        elif key in complete["periods"]:
            selected["periods"].append(key)
        elif key in complete["years"]:
            selected["years"].append(key)
        elif (isinstance(key, six.string_types) and
              cache(re.match(r"(\d+)-(\d+)$", key))):
            selected["years"].extend([
                year for year in range(int(cache.output.group(1)),
                                       int(cache.output.group(2)) + 1)
                if year in complete["years"]])
        else:
            errors.append("{0}".format(key))

    update_selected(selected, complete)
    return selected, errors


def update_selected(selected, complete):
    """Update the selected times"""

    extra_seasons = [
        season for season in complete["seasons"]
        if set(season_to_years(season)).issubset(selected["years"])]
    for season in selected["seasons"]:
        selected["years"].extend(season_to_years(season))
    selected["seasons"].extend(extra_seasons)

    extra_periods = [country_season_to_period(country, season)
                     for country in selected["countries"]
                     for season in selected["seasons"]]
    for period in selected["periods"]:
        country, season = period_to_country_season(period)
        selected["countries"].append(country)
        selected["seasons"].append(season)
        selected["years"].extend(season_to_years(season))
    selected["periods"].extend(extra_periods)


def get_date(datestring, season=None):
    """Return a date, given in the format
            YYYY-MM-DD
            MM-DD + period
            WW + period
            "week" + period
            "0" + period (return last available date)
    """

    try:
        elements = [int(a) for a in re.split("[-/]", "{0}".format(datestring))]
    except ValueError:
        raise IAPError("Invalid date string {0}".format(datestring))

    if len(elements) == 3:
        return datetime.date(elements[0], elements[1], elements[2])
    elif len(elements) == 2:
        if season is None:
            year1, year2 = season_to_years(
                config.CONFIG["settings"]["reference_season"])
        else:
            year1, year2 = season_to_years(season)
        if elements[0] >= 8:
            return datetime.date(year1, elements[0], elements[1])
        else:
            return datetime.date(year2, elements[0], elements[1])
    raise IAPError("No date {0} in season {1}".format(datestring, season))


def translate(label, lang="en", latex=True, extra=None):
    """Translate labels"""

    cache = tools.Cache()

    if isinstance(label, list):
        translation = [translate(lab, lang, latex, extra) for lab in label]
    elif isinstance(label, dict):
        translation = {translate(key, lang, latex, extra):
                       translate(value, lang, latex, extra)
                       for key, value in label.items()}
    elif isinstance(label, tuple):
        translation = tuple(translate(lab, lang, latex, extra)
                            for lab in label)

    elif isinstance(label, (int, float, bool)):
        translation = label
    elif cache(re.match(r"(\d+):(\d+)", label)):
        min_val, max_val = cache.output.groups()
        translation = "{0}-{1}".format(min_val, max_val)
#     elif cache(re.match(r"([<>]{1})(\d+)", label)):
#         symbol, val = cache.output.groups()
#         if latex:
#             translation = "${{{0}}}{1}$".format(symbol, val)
#         else:
#             translation = "{0}{1}".format(symbol, val)
    elif extra is not None and label in extra:
        translation = extra[label]
    else:
        translation = translate_string(label, lang, latex)

    return translation


def translate_string(label, lang, latex):
    """Translate a string by replacing elements between << and >>"""

    # replace occurance of <<word>> by translate_word(word)
    # re can not select for "not(<<)", so replace <<, >> first
    start2, end2 = chr(1), chr(2)
    label = re.sub(config.SEP["translate_start"], start2,
                   re.sub(config.SEP["translate_end"], end2, label))
    pattern = re.compile("{0}([^{0}{1}]*){1}".format(start2, end2))
    while pattern.search(label):
        label = pattern.sub(
            lambda match: translate_word(match.group(1), lang), label)
    label = re.sub(start2, config.SEP["translate_start"],
                   re.sub(end2, config.SEP["translate_end"], label))

    # strip, removing space,newline,colom from both sides
    label = re.sub("^[\n :]+|[\n :]+$", "", label)

    # strip trailing __ from both sides
    label = re.sub("__$|^__", "", label)

    # remove double spaces
    label = re.sub(" +", " ", label)

    if not latex:
        label = re.sub(r"\$\^\{(.*?)\}\$", "-\\1", label)

    return label


def translate_word(label, lang):
    """Translate a label"""
    section, word = (label.split(config.SEP["translate"], 1)
                     if config.SEP["translate"] in label else
                     ("extra", label))
    lower = word.lower()

    if section == "control":
        section = "casedef"

    if (section == "casedef" and "_" in word and
            not (word.startswith("ili") or word.startswith("inf"))):
        column, lower = lower.split("_", 1)
        section = "{0}_{1}".format("survey", column)

    fname, section = (section.split("_", 1) if "_" in section
                      else ("all", section))

    fname, section, lower = (
        ("all", "extra", "dontknow") if lower == "d"
        else ("all", "extra", "none") if lower in ("n", "nn")
        else ("all", "extra", "other") if lower == "o"
        else (fname, section, lower))

    if fname == "all" and section == "season":
        if lower in ("all", "title"):
            pass
        elif lower.startswith("short_"):
            lower = lower[6:]
            years = season_to_years(lower)
            return "{year1:02d}/{newline}{year2:02d}".format(
                year1=years[0] % 100,
                year2=years[1] % 100,
                newline=config.SEP["newline"])
        elif lower.startswith("slash_"):
            lower = lower[6:]
            years = season_to_years(lower)
            return "{0:02d}/{1:02d}".format(years[0], years[1] % 100)
        else:
            years = season_to_years(lower)
            return "{0} - {1}".format(*years)

    if (fname == "intake" and
            section in config.TABLE["intake"] and
            "type" in config.TABLE["intake"][section] and
            lower != "title" and
            config.TABLE["intake"][section]["type"] not in (
                "radio", "checkbox", "options")):
        translation = lower
    elif (lang in config.TRANSLATE and
          fname in config.TRANSLATE[lang] and
          section in config.TRANSLATE[lang][fname] and
          lower in config.TRANSLATE[lang][fname][section]):
        translation = config.TRANSLATE[lang][fname][section][
            "{0}_short".format(lower) if "{0}_short".format(lower)
            in config.TRANSLATE[lang][fname][section] else
            lower]
    elif lower.startswith("short_"):
        translation = translate_word(label.replace("short_", ""), lang)
    elif lang != "en":
        translation = translate_word(label, "en")
    else:
        translation = word
        raise IAPError((
            "Not translated: <<{label}>>\n" +
            "  section: {section}\n" +
            "  fname: {fname}\n" +
            "  lower: {lower}").format(label=label, section=section,
                                       fname=fname, lower=lower))

    return translation


def get_direct(label, options):
    """Return the label in options, and if it should be translated"""

    if ("{0}_label".format(label) in options and
            options["{0}_label".format(label)] != ""):
        return (options["{0}_label".format(label)], True,
                "{0}_label".format(label))
    elif ("{0}_id".format(label) in options and
          options["{0}_id".format(label)] != ""):
        return (options["{0}_id".format(label)], False,
                "{0}_id".format(label))
    elif label in options and options[label] != "":
        return options[label], False, label
    else:
        return "", False, ""


def debug_query(sql, params, many):
    """Show debug messages about the query"""
    if many:
        logger.debug(sql)
    elif params:
        if hasattr(params, "dict") or isinstance(params, dict):
            params = dict(zip(
                params.keys(),
                ["'{0}'".format(value) for value in params.values()]))
        elif isinstance(params, (list, tuple)):
            params = tuple(["'{0}'".format(elem) for elem in params])
        elif isinstance(params, six.string_types):
            params = "'" + params + "'"
        sql = sql % params
        logger.debug(sql)
    else:
        logger.debug(sql)


def query_many(sql, params=None, reconnect=False, sql_warnings=True):
    """Query with many params"""

    try:
        sql = re.sub(r"(\s)VALUES(\s)", "\\1values\\2", sql)
        config.CURSOR.executemany(sql, params)
    except MySQLdb.Error as inst:
        if not reconnect:
            # also check if code 2006
            connect()
            return query_many(sql, params, reconnect=True)
        raise IAPError(""""SQL error:
                IAPError: {inst}
                Query : {sql}
                """.format(inst=inst, sql=sql))
    except MySQLdb.Warning as inst:
        if sql_warnings:
            raise IAPError(""""SQL warning: {msg}
                    Query : {sql}
                    """.format(msg=inst.message, sql=sql))
    return config.CURSOR


def query(sql, params=None, many=False, reconnect=False, sql_warnings=True):
    """Perform the sql query. If mysql is away, try once reconnecting"""

    debug_query(sql, params, many)
    if config.CURSOR is None:
        connect()

    if many:
        return query_many(sql, params, reconnect, sql_warnings)

    try:
        if params:
            if hasattr(params, "dict"):
                params = params.dict()
            elif isinstance(params, tuple):
                params = list(params)
            config.CURSOR.execute(sql, params)
        else:
            config.CURSOR.execute(sql)
    except MySQLdb.Error as error:
        if not reconnect:
            # todo: also check if error code = 2006
            connect()
            return query(sql, params, many, reconnect=True)
        else:
            raise IAPError(""""SQL error:
                    IAPError: {error}
                    Query : {sql}
                    Params: {params}
                    """.format(error=error, sql=sql, params=params))
    except MySQLdb.Warning as error:
        if sql_warnings:
            raise IAPError(""""SQL warning: {msg}
                    Query : {sql}
                    Params: {params}
                    """.format(msg=error, sql=sql, params=params))
    return config.CURSOR


def get_limits(season, country=None, average=None):
    """Return the first and last day of a season.
        If country is given and inet data is available,
        check the database
        else: return 1/8 - 31/7"""

    if season == "":
        return None, None
    if country:
        period = country_season_to_period(country, season)
    if not country or not period_available(period):
        year1, year2 = season_to_years(season)
        return (get_date("{0}/8/1".format(year1)),
                get_date("{0}/7/31".format(year2)))

    if period not in config.LIMITS:
        min_date, max_date = (
            get_date(date)
            for date in config.CONFIG["country"][country]["inet"][season])
        cursor = query("""SELECT
                MIN(sdate) AS min_date,
                MAX(sdate) AS max_date
            FROM
                {tbl_survey}
            """.format(tbl_survey=get_tbl("survey", "new", period)))

        row = cursor.fetchone()
        if row["min_date"] is not None:
            min_date = max(min_date,
                           row["min_date"] + datetime.timedelta(days=1))
            max_date = min(max_date,
                           row["max_date"] -
                           datetime.timedelta(days=1))
        config.LIMITS[period] = (min_date, max_date)

    min_date, max_date = config.LIMITS[period]
    if average is not None:
        min_date += datetime.timedelta(days=6 + (average - 7) // 2)
        max_date -= datetime.timedelta(days=(average - 7) // 2)

    return min_date, max_date


def table_exists(table):
    """A table exists in the database"""
    cursor = query("SHOW TABLES LIKE %s", (table,))
    if cursor.rowcount > 0:
        return True
    else:
        return False


def get_columns(table):
    """Return all the fields of a table"""
    if table not in config.COLUMNS:
        if table_exists(table):
            cursor = query("SHOW FIELDS FROM {0}".format(table))
#             config.COLUMNS[table] = natsort.natsorted([row["Field"]
#                     for row in cursor.fetchall()])
            config.COLUMNS[table] = [row["Field"] for row in cursor.fetchall()]
        else:
            config.COLUMNS[table] = []
    return list(config.COLUMNS[table])


def add_columns(table, columns):
    """Add various columns to a table"""

    add_cols = ["ADD COLUMN {0} {1}".format(column, coltype)
                for (column, coltype) in columns
                if column not in get_columns(table)]
    if len(add_cols) == 0:
        return
    query("ALTER TABLE {table} {add_cols}".format(
        table=table, add_cols=",".join(add_cols)))
    if table in config.COLUMNS:
        del config.COLUMNS[table]


def drop_columns(table, columns):
    """Add various columns to a table"""

    drop_cols = ["DROP COLUMN {0}".format(column)
                 for column in columns
                 if column in get_columns(table)]
    if len(drop_cols) == 0:
        return
    query("ALTER TABLE {table} {drop_cols}".format(
        table=table, drop_cols=",".join(drop_cols)))
    if table in config.COLUMNS:
        del config.COLUMNS[table]


def get_tables():
    """Return all (non-temporary) tables"""
    cursor = query("""SHOW TABLES""")
    return [next(six.itervalues(row)) for row in cursor.fetchall()]


def drop_table(table):
    """Drop a table, securily without warning"""
    query("DROP TABLE IF EXISTS {0}".format(table), sql_warnings=False)


def table_index2(table, index):
    """Add index to a table, if not already exists"""
    cursor = query("""SHOW INDEX FROM {0}
            WHERE Column_name=%s""".format(table), index)
    if cursor.rowcount == 0:
        query("ALTER TABLE {0} ADD INDEX({1})".format(table, index))
        try:
            query("ALTER TABLE {0} ADD INDEX({1})".format(table, index))
        except IAPError:
            query("ALTER TABLE {0} ADD INDEX({1}({2}))".format(
                table, index, 200))


def table_index(table, index):
    """Add index to a table, if not already exists"""
    index = set(re.split(", *", index))

    cursor = query("SHOW INDEX FROM {0}".format(table))
    index_dict = collections.defaultdict(set)
    all_index = []
    for row in cursor.fetchall():
        if row["Key_name"] == "PRIMARY":
            all_index.append(set([row["Column_name"]]))
        else:
            index_dict[row["Key_name"]].add(row["Column_name"])
    all_index.extend(index_dict.values())
    if index not in all_index:
        try:
            query("ALTER TABLE {0} ADD INDEX({1})".format(
                table, ",".join(index)))
        except IAPError:
            query("ALTER TABLE {0} ADD INDEX({1})".format(
                table, ",".join(["{0}(200)".format(col) for col in index])))


def column_type(table, column, coltype):
    """Change column type if not already"""
    cursor = query("""SHOW FIELDS FROM {0}
            WHERE Field=%s""".format(table), (column,))
    row = cursor.fetchone()
    if coltype.lower() != row["Type"]:
        query("""ALTER TABLE {0}
                CHANGE {1} {1} {2}""".format(table, column, coltype))


def create_table(table):
    """Create a table"""

    if table in config.TABLES:
        drop_table(table)
        query("CREATE TABLE {table} ({tbl_def})".format(
            table=table, tbl_def=config.TABLES[table]))
    else:
        raise IAPError("Unknown table: {0}".format(table))


def get_perc_a(country, year, date_start=None, date_end=None):
    """Get the percentage of Inf. A in a certain season"""

    if date_start is None:
        date_start = datetime.date(year, 8, 1)
    if date_end is None:
        date_end = datetime.date(year + 1, 4, 30)

    cursor = query("""SELECT
            label, SUM(value) AS total
        FROM
            other
        WHERE
            source=%(source)s AND
            label IN (%(infa)s, %(infb)s) AND
            country=%(country)s AND
            date>=%(date_start)s AND
            date<=%(date_end)s
        GROUP BY
            label
        """, {"source": "eiss",
              "infa": "Inf.Type A",
              "infb": "Inf.Type B",
              "country": country,
              "date_start": date_start,
              "date_end": date_end})
    for row in cursor.fetchall():
        if row["label"] == "Inf.Type A":
            infa = row["total"]
        elif row["label"] == "Inf.Type B":
            infb = row["total"]

    return infa / (infa + infb)


def split_qa(question_answer, split_list):
    """Split the question up"""
    cache = tools.Cache()
    if isinstance(split_list, six.string_types):
        split_list = [split_list]
    question_answer = re.sub("_*$", "", question_answer)
    for split in split_list:
        if cache(re.search("^(.+)({0})(.+)$".format(split), question_answer)):
            return cache.output.groups()
    return question_answer, None, None


def check_db(sql, period):
    """Replace non-existing column-checks with False"""

    columns = (get_columns(get_tbl("intake", "new", period)) +
               get_columns(get_tbl("survey", "new", period)))

    def repl(match):
        """Replace non-existing column-checks with False"""
        table, column, formula = match.groups()
        if column not in columns:
            return "False"
        return table + column + formula

    # replace [qs]<number> questions
    sql = re.sub(r"([a-zA-Z_]*\.?)([sq][\d]+_?[\da-z]*)([><=]*[\d]*)",
                 repl, sql)

    # replace [vaccin]=1 questions
    sql = re.sub(r"(\[.+?\]_?[\da-z]*)([><=]*[\d]*)", repl, sql)

    return sql


def dates2reference_season(dates, season):
    """Convert the date to the season self.reference_season"""

    if season == config.CONFIG["settings"]["reference_season"]:
        return dates

    orig_years = season_to_years(season)
    new_years = season_to_years(config.CONFIG["settings"]["reference_season"])

    change_years = orig_years[0] - new_years[0]
    new_dates = []
    for date in dates:
        try:
            new_date = date.replace(year=date.year - change_years)
        except ValueError:
            # converting 29 februari sometimes breaks
            new_date = date.replace(year=date.year - change_years,
                                    day=date.day - 1)
        new_dates.append(new_date)

    return new_dates


def sql_to_csv(tbl_name, fname, columns=None, order_id=None):
    """Dump an sql table to csv"""

    if columns is None:
        columns = get_columns(tbl_name)
    if order_id is None or order_id not in columns:
        order_id = columns[0]

    tmpname = "/tmp/mysql/tmp.csv"
    tools.create_dir(tmpname, remove=True)
    os.chmod(os.path.dirname(tmpname), 0O777)
    sql = """
        SELECT
            {columns}
        INTO OUTFILE "{tmpname}"
        CHARACTER SET utf8
        FIELDS TERMINATED BY ","
        OPTIONALLY ENCLOSED BY '"'
        ESCAPED BY ''
        LINES TERMINATED BY "\n"
        FROM
            {tbl_name}
        ORDER BY
            {id}
    """.format(
        columns=", ".join(["IFNULL(REPLACE({0}, '\"', '\"\"'), '')".format(col)
                           for col in columns]),
        # ("IF({col}='0', '', IFNULL({col}, ''))").format(col=col)
        tbl_name=tbl_name,
        id=order_id,
        tmpname=tmpname)
    query(sql)
    with tools.csvopen(fname, "w") as csvobj_write:
        writer = tools.uwriter(csvobj_write)
        with tools.csvopen(tmpname, "r") as csvobj_read:
            reader = tools.ureader(csvobj_read)
            writer.writerow(columns)
            for line in reader:
                writer.writerow(line)
        # csvobj_write.write(csvobj_read.read())

#     cmd = """mysql -u {db_user} -p{db_pass} {db} \
#         --skip-column-names -B \
#         -e "{sql}" >> {fname}""".format(
#         db_user=config.LOCAL["db"]["user"],
#         db_pass=config.LOCAL["db"]["pass"],
#         db=config.LOCAL["db"]["db"],
#         sql=sql,
#         fname=fname)
#     try:
#         subprocess.check_call(cmd, shell=True)
#         subprocess.check_call("todos {0}".format(fname), shell=True)
#     except subprocess.CalledProcessError:
#         logger.error("Failed csv export {0}".format(tbl_name))


def get_dbini(src):
    """Return db ini file"""

    ininame = os.path.join(config.CONFIG_DIR, "db", "{0}.ini".format(src))
    if not os.path.exists(ininame):
        raise IAPError("No db language file: {0}".format(ininame))

    dbini = configobj.ConfigObj(
        ininame,
        configspec=os.path.join(config.CONFIG_DIR, "db.spec"))
    tools.cobj_check(dbini, exception=IAPError)
    return dbini


def get_datasets_keys(datasets, keys):
    """Get the datasets based on the keys"""

    selected = configobj.ConfigObj()
    for key, values in datasets.items():
        for dataset in keys:
            if ((dataset.endswith("!") and key == dataset[:-1]) or
                    (not dataset.endswith("!") and key.startswith(dataset))):
                selected[key] = values
    return selected


def get_avg(value, max_plus=1):
    """Get the average from a label string"""
    cache = tools.Cache()

    if cache(re.match(r"<(\d+)", value)):
        max_val = int(cache.output.group(1)) - 1
        return max_val / 2
    if cache(re.match(r">(\d+)", value)):
        return int(cache.output.group(1)) + max_plus
    if cache(re.match(r"(\d+):(\d+)", value)):
        min_val, max_val = cache.output.groups()
        return (int(min_val) + int(max_val)) / 2
    else:
        return int(value)
