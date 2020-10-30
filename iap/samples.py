#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Get data range when enough positive influenza samples are detected"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import collections
import datetime
import numpy
import sys  # pylint: disable=W0611

from . import utils, tools
from .inibase import IniBase  # no samples_period in options
from .database import DataBase  # no combi incidence for samples_period

RELOAD = False


def get_range_sql(country, season, threshold):
    """Get date range from database"""

    if RELOAD:
        return None, None

    cursor = utils.query("""
        SELECT
            min_date, max_date
        FROM
            samples
        WHERE
            country = %(country)s AND
            season = %(season)s AND
            threshold = %(threshold)s
        """, {"country": country, "season": season, "threshold": threshold})

    if cursor.rowcount == 0:
        return None, None
    row = cursor.fetchone()
    return row["min_date"], row["max_date"]


def save_sql(country, season, threshold, min_date, max_date):
    """Get date range from database"""

    utils.query("""
        REPLACE INTO
            samples
            (country, season, threshold, min_date, max_date)
            VALUES
            (%(country)s, %(season)s, %(threshold)s,
             %(min_date)s, %(max_date)s)
        """, {"country": country, "season": season, "threshold": threshold,
              "min_date": min_date, "max_date": max_date})


def get_datadict(country, season):
    """Get a datadict with the total number of samples"""

    datadict = collections.defaultdict(int)
    inistring = """
        [datasets]
            [[infa]]
                source_measure = eiss_samples
                country = {country}
                season = {season}
                casedef = infa
            [[infb]]
                source_measure = eiss_samples
                country = {country}
                season = {season}
                casedef = infb
        """.format(country=country, season=season)
    ini = IniBase(inistring)
    for options in ini.datasets.values():
        for date, daydata in DataBase(options).get_datadict().items():
            if "eiss_samples" in daydata and daydata["eiss_samples"] > 0:
                datadict[date] += daydata["eiss_samples"]
                datadict[date + datetime.timedelta(days=7)] += (
                    daydata["eiss_samples"])
                datadict[date - datetime.timedelta(days=7)] += (
                    daydata["eiss_samples"])
    return datadict


def get_range(country, season, threshold, average=None, inet=False):
    """Return date range for which the samples are above threshold"""

    if threshold == 100:
        return None, None
    elif threshold == 0:
        return utils.get_limits(season)
    elif season in ("2013/14", "2014/15", "2015/16"):
        return utils.get_limits(season, country, None)

    # min_date, max_date = None, None
    min_date, max_date = get_range_sql(country, season, threshold)

    if min_date is None:
        datadict = get_datadict(country, season)
        if len(datadict) == 0:
            return None, None
        max_val = max(datadict.values())
        critical = threshold * max_val / 100
        min_date, max_date = None, None
        top = False
        for date, value in tools.sort_iter(datadict):
            if value == max_val:
                top = True

            if value >= critical:
                if min_date is None:
                    min_date = date
                if top:
                    max_date = date
            else:
                if top:
                    break
                else:
                    min_date = None
                    max_date = None

        # min_date starts on Monday
        min_date -= datetime.timedelta(days=6)

        save_sql(country, season, threshold, min_date, max_date)

    if average is not None:
        min_date += datetime.timedelta(days=6 + (average - 7) // 2)
        max_date -= datetime.timedelta(days=(average - 7) // 2)

    if inet:
        min_date2, max_date2 = utils.get_limits(season, country, 7)
        return max(min_date, min_date2), min(max_date, max_date2)
    else:
        return min_date, max_date


def get_map_range(country, season, source_measure, casedef,
                  threshold=0.02, average=7):
    """Determine epidemic period based on (Vega et al, 2014)"""

    inistring = (
        """[datasets]
            [[default]]
                source_measure = {source_measure}
                country = {country}
                season = {season}
                casedef = {casedef}
                daily = False
                average = {average}
        """).format(
            source_measure=source_measure,
            country=country,
            season=season,
            average=average,
            casedef=casedef)

    ini = IniBase(inistring)
    datadict = DataBase(ini.datasets["default"]).get_datadict()
    min_date, max_date = utils.get_limits(season, country, average)
    date_ilis = [
        (date, daydata[source_measure])
        for date, daydata in tools.sort_iter(datadict)
        if (date.isoweekday() == 7 and
            date >= min_date and date <= max_date and
            date.month)]
    min_date = date_ilis[0][0]
    start, length = get_epidemic_weeks(
        [ili for date, ili in date_ilis], threshold)
    return (min_date + datetime.timedelta(days=start * 7),
            min_date + datetime.timedelta(days=(start + length) * 7))


def get_epidemic_weeks(ilis, threshold):
    """Return the epidemic weeks for certain threshold"""
    size = len(ilis)
    percs = [max([sum(ilis[k: k + r]) for k in range(size + 1)]) / sum(ilis)
             for r in range(size + 1)]

#     import statsmodels.api
#     lowess = statsmodels.api.nonparametric.lowess
#     sm_percs = lowess(percs, range(size + 1))[:, 1]
#     percs = sm_percs
    difs = [percs[i + 1] - percs[i]
            for i in range(size)]
    rmax = min([
        index
        for index, dif in enumerate(difs)
        if dif < threshold])
    onset = int(numpy.array([
        sum(ilis[k: k + rmax]) for k in range(size + 1)]).argmax())
    return onset, rmax


def get_limits(season, country, samples_onsets, average=None):
    """Get limits, limiting on the sample range"""
    min_date, max_date = utils.get_limits(season, country, average)
    min_date2, max_date2 = get_range(
        country, season, samples_onsets, average=average)
    min_date = max(min_date, min_date2)
    max_date = min(max_date, max_date2)
    return min_date, max_date
