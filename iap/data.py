#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Get data from the database and calculated values"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import collections

from .exceptions import IAPError
from . import utils, linreg, split, tools
from .ini import Ini
from .database import DataBase


class Data(DataBase):
    """Contains all the function to query the database"""
    # allow combi_incidence, age_correction, extra_countries

    def set_combi(self, only_eiss=False):
        """average of inet and (scaled) eiss incidence: combi_incidence """

        self.datadict = collections.defaultdict(tools.MDict)
        min_date, max_date = utils.get_limits(
            self.options["season"], self.options["country"],
            self.options["average"])
        options = tools.deepcopy(self.options)
        inistring = tools.Format("""
            [plots]
                [[default]]
                    linreg_seasons = {combi_seasons:co}
                    linreg_sources = inet_incidence, eiss_incidence
                    linreg_casedefs = {casedef}, ili
                    linreg_intercept0 = {combi_intercept0}
                    linreg_country = {country}
                    linreg_min_surveys = {min_surveys}
                    linreg_days = 0, 1
            """).format(extra=options)
        ini = Ini(inistring)
        linreg_dict = linreg.get_dict(ini.settings["plots"]["default"])
        if linreg_dict is None:
            raise IAPError(tools.Format(
                "No linreg for eiss and inet over seasons" +
                " {combi_seasons} for {country}").format(extra=options))

        for options["source_measure"] in ["inet_incidence", "eiss_incidence"]:
            options["source"], options["measure"] = \
                options["source_measure"].split("_")

            if ((options["source"] == "inet" and only_eiss) or
                    (options["source"] == "inet" and
                     not utils.period_available(options["period"]))):
                continue
            options["casedef"] = ("ili" if options["source"] == "eiss" else
                                  self.options["casedef"])

            datadict = Data(options).get_datadict()
            for date, daydata in datadict.items():
                if (date.isoweekday() != 7 or
                        (options["source"] == "inet" and
                         (date < min_date or date > max_date))):
                    continue
                for key, value in daydata.items():
                    if key in self.datadict[date]:
                        self.datadict[date][key] += value
                    else:
                        self.datadict[date][key] = value
        for date, daydata in self.datadict.items():
            if "eiss_incidence" in daydata:
                daydata["eiss_scaled"] = (
                    linreg_dict[0]["gradient"] * daydata["eiss_incidence"] +
                    linreg_dict[0]["intercept"])
            if not only_eiss:
                daydata["combi_incidence"] = (
                    (daydata["inet_incidence"] + daydata["eiss_scaled"]) / 2
                    if ("inet_incidence" in daydata and
                        "eiss_incidence" in daydata) else
                    daydata["inet_incidence"]
                    if "inet_incidence" in daydata else
                    daydata["eiss_scaled"])

    def set_extra_countries(self):
        """Multiple countries in one datadict"""

        options = self.options.copy()
        options["extra_countries"] = []
        self.datadict = collections.defaultdict(tools.MDict)
        for options["country"] in (self.options["extra_countries"] +
                                   [options["country"]]):
            options["period"] = utils.country_season_to_period(
                options["country"], options["season"])
            if (options["source"] == "inet" and
                    not utils.period_available(options["period"])):
                return
            datadict = Data(options).get_datadict()
            # self.fill(add_calculated=False)
            for date, daydata in datadict.items():
                for key, value in daydata.items():
                    if key in self.datadict[date]:
                        self.datadict[date][key] += value
                    else:
                        self.datadict[date][key] = value
        if len(self.datadict.keys()) > 0:
            self.add_calculated()

    def set_age_correction(self):
        """Return the dates, incidences for a dataset
           does also age-correction when options["age_correction"]"""

        dates_dict = collections.defaultdict(list)
        cutter = "age=>{0}".format(self.options["age_correction"])
        options = self.options.copy()
        for answer in split.get_answers(cutter, None)[1]:
            options["age_correction"] = ""
            options["age_cutter"] = cutter
            options["age_answer"] = answer
            options["min_participants"] = 1
            split.set_full(options)
            data = Data(options)
            factor = data.population
            if factor == 0:
                continue
            for date, daydata in data.get_datadict().items():
                if "inet_incidence" in daydata and "inet_actives" in daydata:
                    dates_dict[date].append([daydata["inet_cases"],
                                             daydata["inet_actives"], factor])

        for date, daydata in tools.sort_iter(dates_dict):
            self.datadict[date]["inet_incidence"] = (
                100000 * sum([factor * cases / actives
                              for cases, actives, factor
                              in daydata]) /
                sum([factor
                     for _cases, _actives, factor in daydata]))
            # (100000 * tools.get_conf_poisson(
            #        [val[0] for val in dates_dict[date]],
            #        [val[1] for val in dates_dict[date]],
            #        [val[2] for val in dates_dict[date]])[1])

    def get_datadict(self):
        """Get the data"""

        if len(self.options["extra_countries"]) > 0:
            self.set_extra_countries()
        elif self.options["source_measure"] == "combi_incidence":
            self.set_combi()
        elif self.options["source_measure"] == "eiss_scaled":
            self.set_combi(True)
        elif self.options["age_correction"] != "":
            self.set_age_correction()
        else:
            self.fill()
        return self.datadict
