#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Do linear regression between two sources"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import collections
import datetime
import logging

from . import utils, config, tools
from .database import DataBase
from .ini import Ini

logger = logging.getLogger(__name__)


def get_dict(settings):
    """Return gradient and intercept between srcme1 and srcme2"""

    cursor = utils.query(
        """SELECT
            delta, gradient, intercept, r2, sd_gradient, sd_intercept
        FROM
            linreg
        WHERE
            country = %(country)s AND
            srcme1 = %(srcme1)s AND
            srcme2 = %(srcme2)s AND
            casedef1 = %(casedef1)s AND
            casedef2 = %(casedef2)s AND
            min_surveys = %(min_surveys)s AND
            seasons = %(seasons)s AND
            intercept0 = %(intercept0)s AND
            delta IN ({delta_values})
        """.format(
            delta_values=config.SEP["params"].join([
                "{0}".format(delta)
                for delta in range(settings["linreg_days"][0],
                                   settings["linreg_days"][1])])),
        {"country": settings["linreg_country"],
         "srcme1": settings["linreg_sources"][0],
         "srcme2": settings["linreg_sources"][1],
         "casedef1": settings["linreg_casedefs"][0],
         "casedef2": settings["linreg_casedefs"][1],
         "min_surveys": settings["linreg_min_surveys"],
         "seasons": config.SEP["params"].join(
             sorted(settings["linreg_seasons"])),
         "intercept0": settings["linreg_intercept0"]})
    if settings["linreg_days"][1] - settings["linreg_days"][0] \
            == cursor.rowcount:
        linreg_dict = dict([(row["delta"], row)
                            for row in cursor.fetchall()])
    else:
        linreg_dict = params_to_dict(settings)
        if linreg_dict is None:
            return None
        for delta, linreg_values in linreg_dict.items():
            utils.query("""REPLACE INTO
                    linreg
                (country, srcme1, srcme2,
                    casedef1, casedef2, min_surveys, seasons,
                    delta, intercept0,
                    gradient, intercept, r2,
                    sd_gradient, sd_intercept)
                VALUES
                (%(country)s, %(srcme1)s, %(srcme2)s,
                    %(casedef1)s, %(casedef2)s, %(min_surveys)s, %(seasons)s,
                    %(delta)s, %(intercept0)s,
                    %(gradient)s, %(intercept)s, %(r2)s,
                    %(sd_gradient)s, %(sd_intercept)s)
                """, {"country": settings["linreg_country"],
                      "srcme1": settings["linreg_sources"][0],
                      "srcme2": settings["linreg_sources"][1],
                      "min_surveys": settings["linreg_min_surveys"],
                      "casedef1": settings["linreg_casedefs"][0],
                      "casedef2": settings["linreg_casedefs"][1],
                      "seasons": config.SEP["params"].join(
                          sorted(settings["linreg_seasons"])),
                      "intercept0": settings["linreg_intercept0"],
                      "gradient": linreg_values["gradient"],
                      "intercept": linreg_values["intercept"],
                      "sd_gradient": linreg_values["sd_gradient"],
                      "sd_intercept": linreg_values["sd_intercept"],
                      "r2": linreg_values["r2"],
                      "delta": delta})
    return linreg_dict


def params_to_dict(settings):
    """Set gradient and intercept between srcme1 and srcme2"""

    inistring = "[datasets]"
    for srcme, casedef in zip(settings["linreg_sources"],
                              settings["linreg_casedefs"]):
        inistring += tools.Format("""
            [[default_{srcme}]]
            source_measure = {srcme}
            season_values = {seasons:co}
            country = {country}
            casedef = {casedef}
            min_surveys = {min_surveys}
            """).format(srcme=srcme,
                        casedef=casedef,
                        min_surveys=settings["linreg_min_surveys"],
                        country=settings["linreg_country"],
                        seasons=settings["linreg_seasons"])
    ini = Ini(inistring)
    return datasets_to_dict(ini.datasets, settings)


def get_data(datasets, settings):
    """Get the data to do the linear regression on"""

    data = collections.defaultdict(dict)
    for options in datasets.values():
        # if options["answer"] != "":
        #     continue
        if options["period"]:
            start, end = utils.get_limits(
                options["season"], options["country"], options["average"])
        dates = collections.defaultdict(list)
        values = collections.defaultdict(list)
        for date, daydata in DataBase(options=options).get_datadict().items():
            if options["period"] and (date < start or date > end):
                continue
            if settings["linreg_sources"][0] in daydata:
                dates["srcme1"].append(date)
                values["srcme1"].append(daydata[settings["linreg_sources"][0]])
            if settings["linreg_sources"][1] in daydata:
                dates["srcme2"].append(date)
                values["srcme2"].append(daydata[settings["linreg_sources"][1]])

        # check that it is not an empty set (like ILI_e)
        for srcme in ["srcme1", "srcme2"]:
            if len(dates[srcme]) > 0 and sum(values[srcme]) > 0:
                for date, value in zip(dates[srcme], values[srcme]):
                    data[srcme][date] = value
    return data


def datasets_to_dict(datasets, settings):
    """Do the linear regression between two datasources
            allowing a timeshift in days"""

    linreg_dict = {}
    data = get_data(datasets, settings)
    if len(data["srcme1"]) < 2 or len(data["srcme2"]) < 2:
        logger.info("Not enough linreg data")
        return None

    for delta in range(*settings["linreg_days"]):
        values = collections.defaultdict(list)
        for date1, daydata1 in tools.sort_iter(data["srcme1"]):
            date2 = date1 + datetime.timedelta(days=delta)
            if date2 in data["srcme2"]:
                values[1].append(daydata1)
                values[2].append(data["srcme2"][date2])

        if len(values[1]) < 2:
            continue

        linreg_dict[delta] = dict(zip(
            ("r2", "gradient", "sd_gradient", "intercept", "sd_intercept"),
            tools.linreg_wiki(values[2], values[1],
                              settings["linreg_intercept0"])))
        linreg_dict[delta]["delta"] = delta
    if len(linreg_dict) == 0:
        return None
    return linreg_dict


def max_delta(linreg_dict):
    """Return the best linreg"""
    delta = max(linreg_dict.items(), key=lambda y: y[1]["r2"])[0]
    return linreg_dict[delta], delta
