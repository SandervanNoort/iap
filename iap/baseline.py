#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Do baseline calculation (+cache)"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import collections
import datetime
import numpy
import sys  # pylint: disable=W0611
import scipy.stats

from . import utils, config, samples, tools
from .data import Data

AVERAGE = 7


def get_sql_values(datasets):
    """Get the sql values to query database"""

    if len(datasets) == 0:
        return None

    def get_val(key):
        """Return the value if it's unique"""
        values = [options[key] for options in datasets.values()]
        if len(set(values)) == 1:
            return values[0]
        else:
            return None

    sql_values = {
        "seasons": sorted([options["season"]
                           for options in datasets.values()]),
        "country": get_val("country"),
        "casedef": get_val("casedef"),
        "source_measure": get_val("source_measure"),
        "threshold": get_val("samples_onsets")}

    if (sql_values["country"] is None or
            sql_values["casedef"] is None or
            sql_values["source_measure"] is None or
            sql_values["threshold"] is None):
        return None

    return sql_values


def get_sql_dict(sql_values):
    """Get the dict from the database"""

    if sql_values is None:
        return None

    cursor = utils.query("""
        SELECT
            params, min_date, max_date
        FROM
            baseline
        WHERE
            country = %(country)s AND
            source_measure = %(source_measure)s AND
            casedef = %(casedef)s AND
            seasons = %(seasons_)s AND
            threshold = %(threshold)s
        """, dict(sql_values,
                  seasons_=tools.co_join(sql_values["seasons"])))
    if cursor.rowcount > 0:
        row = cursor.fetchone()
        return {
            "min_date": row["min_date"],
            "max_date": row["max_date"],
            "params": [float(param)
                       for param in row["params"].split(config.SEP["params"])]}
    else:
        return None


def datasets_to_dict(datasets):
    """Calculated the params"""

    data = get_data(datasets)
    min_date = min(data.keys())

    days = []
    values = []
    for date, date_values in tools.sort_iter(data):
        if isinstance(date_values[0], tuple):
            values.append(
                100000 * sum([cases for cases, _ in date_values]) /
                sum([actives for _, actives in date_values]))
        else:
            values.append(numpy.median(date_values))
        days.append((date - min_date).days)

    # pfactor guess: [150, 0.5, 0.01, 0.01]
    # sinfactor guess: [100, 0, 0]
    params = tools.fit_params(values, days, tools.sinfactor,
                              [100, 0, 0])

    return {"min_date": min(data.keys()).strftime("%m/%d"),
            "max_date": max(data.keys()).strftime("%m/%d"),
            "params": numpy.around(numpy.array(params), 2)}


def get_data(datasets):
    """Get the data"""

    data = collections.defaultdict(list)
    for options in datasets.values():
        dates = []
        values = []
        min_date, max_date = (
            utils.get_limits(options["season"], options["country"])
            if options["source_measure"] == "inet_incidence" else
            (None, None))
        min_date_samples, max_date_samples = samples.get_range(
            options["country"], options["season"],
            options["samples_onsets"], None)  # options["average"])
        for date, daydata in Data(options=options).get_datadict().items():
            if (date is None or
                    (min_date is not None and
                     (date < min_date or date > max_date)) or
                    (min_date_samples is not None and
                     (date >= min_date_samples and date <= max_date_samples))):
                continue
            if options["source_measure"] in daydata:
                dates.append(date)
                values.append(
                    (daydata["inet_cases"], daydata["inet_actives"])
                    if options["source_measure"] == "inet_incidence" else
                    daydata[options["source_measure"]])
        dates = utils.dates2reference_season(dates, options["season"])
        for date, value in zip(dates, values):
            data[date].append(value)
    return data


def get_dict(datasets):
    """Return baseline_dict for datasets"""

    if len(datasets) == 0:
        return None

    sql_values = get_sql_values(datasets)
    baseline_dict = get_sql_dict(sql_values)
    if baseline_dict is None:
        baseline_dict = datasets_to_dict(datasets)
        save_sql_dict(baseline_dict, sql_values)

    if sql_values is not None:
        baseline_dict.update(sql_values)
    baseline_dict["datasets"] = datasets
    return baseline_dict


def save_sql_dict(baseline_dict, sql_values):
    """Save the baseline dict in the database"""

    if baseline_dict is None or sql_values is None:
        return

    utils.query(
        """REPLACE INTO
            baseline
        (country, casedef, seasons, source_measure, threshold,
         params, min_date, max_date)
        VALUES
        (%(country)s, %(casedef)s, %(seasons_)s, %(source_measure)s,
         %(threshold)s, %(params_)s, %(min_date)s, %(max_date)s)
        """,
        dict(
            sql_values,
            seasons_=tools.co_join(sql_values["seasons"]),
            params_=config.SEP["params"].join(
                ["{0}".format(param) for param in baseline_dict["params"]]),
            min_date=baseline_dict["min_date"],
            max_date=baseline_dict["max_date"]))


def get_baseline(baseline_dict, season):
    """Return the baseline for a specific season"""
    date = utils.get_date(baseline_dict["min_date"], season)
    max_date = utils.get_date(baseline_dict["max_date"], season)

    day = 0
    dates = []
    values = []
    while date <= max_date:
        values.append(tools.sinfactor(day, baseline_dict["params"]))
        dates.append(date)
        day += 1
        date += datetime.timedelta(days=1)
    return dates, values


def get_threshold(baseline_dict, season, active_options):
    """Return epidemic threshold, based on active participants"""

    baseline = dict(zip(*get_baseline(baseline_dict, season)))
    dates = []
    values = []
    options = active_options.copy()
    options["source_measure"] = "inet_actives"
    datadict = Data(options).get_datadict()
    min_date, max_date = utils.get_limits(
        options["season"], options["country"], options["average"])
    for date, daydata in tools.sort_iter(datadict):
        if (date < min_date or date > max_date or
                "inet_actives" not in daydata or
                date not in baseline):
            continue
        dates.append(date)
        values.append(
            100000 * scipy.stats.distributions.gamma.ppf(
                0.95, daydata["inet_actives"] * baseline[date] / 100000) /
            daydata["inet_actives"])
    return dates, values
