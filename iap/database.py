#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Get data from the database and calculated values"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import numpy
import datetime
import collections

from . import utils, config, tools
from .series import Series


class DataBase(object):
    """Contains all the function to query the database"""
    # no combi_incidence, age_correction, extra_countries

    def __init__(self, options):
        self.options = options
        self.datadict = collections.defaultdict(tools.MDict)
        self.labels = set()

    def add_series(self, category):
        """Fill the self.datadict for category"""

        for label, date, value in Series(self.options, category).get_series():
            # people stay active 7 days after last survey
            if category == "leaves" and self.options["grace_period"] > 0:
                date += datetime.timedelta(days=self.options["grace_period"])
#                 self.datadict[date + datetime.timedelta(days=7)][
#                       category] = value
            daydata = self.datadict[date]
            self.labels.add(label)
            daydata[category] += value

    def add_inet(self):
        """Add influenzanet data series"""

        if self.options["measure"] in ["reporting"]:
            new_values = {"casedef": "",
                          "intake": "",
                          "onset": "survey",
                          "ignore_double": False,
                          "ignore_multiple": False}
            orig_values = {key: self.options[key]
                           for key in new_values.keys()}
            for key, value in new_values.items():
                self.options[key] = value
            self.add_series("cases")
            for values in self.datadict.values():
                if "cases" in values:
                    values["surveys"] = values["cases"]
                    del values["cases"]
            for key, value in orig_values.items():
                self.options[key] = value
        if self.options["measure"] in ["incidence", "actives", "participants",
                                       "control", "cases"]:
            self.add_series("joins")
            # always add leaves, but ignore if self.options["always_active"]
            self.add_series("leaves")
        if self.options["measure"] in ["cases", "cum", "incidence", "surveys",
                                       "control", "reporting"]:
            self.add_series("cases")
        if self.options["measure"] == "control":
            self.add_series("control")

    def fill(self, add_calculated=True):
        """Fill the self.datadict"""

        # datadict is already filled
        if len(self.datadict) > 0:
            return

        if self.options["source"] == "europe":
            return

        elif (self.options["source"] == "inet" and
              self.options["period"] is not None):
            self.add_inet()
        elif self.options["source"] == "eiss":
            self.add_other("eiss", self.options["casedef"])
        elif (self.options["source"] == "climate" and
              self.options["measure"] == "sun"):
            self.add_sun()
        elif self.options["source"] == "climate":
            self.add_other("noaa", self.options["measure"])
        elif self.options["source"] == "google":
            self.add_other("google", "")
        elif self.options["source"] == "mexico":
            self.add_other("mexico", "")

        if add_calculated and len(self.datadict.keys()) > 0:
            self.add_calculated()

        # Griepmeting prijsvraag plots on Mondays
        # if self.options["measure"] == "reporting":
        #     for date, daydata in tools.sort_iter(self.datadict):
        #         self.datadict[date - datetime.timedelta(days=6)] \
        #                 = daydata
        #         del(self.datadict[date])

    def get_datadict(self):
        """Get the data"""

        self.fill()
        return self.datadict

    @property
    def population(self):
        """Return population size"""

        min_age, max_age = self.options["full_answer"].split(
            config.SEP["range"])

        if min_age == "min":
            min_age = 0
        if max_age == "max":
            max_age = 120
        min_age = int(min_age)
        max_age = int(max_age)

        min_age -= min_age % 5
        max_age -= max_age % 5

        cursor = utils.query("""SELECT
                SUM(persons) AS population
            FROM
                age
            WHERE
                country = %(country)s AND
                min_age >= %(min_age)s AND
                max_age < %(max_age)s
            """, {"country": self.options["country"],
                  "min_age": min_age,
                  "max_age": max_age})
        row = cursor.fetchone()
        population = row["population"]

        if population is None:
            return 0
        else:
            return int(population)

    def participant_days(self, date, days):
        """Number of participant-days, in the <days> before <date>"""

        self.fill()
        participant_days = (
            # => active full period, counted as '1'
            # active before, and did not leave
            self.datadict[date - datetime.timedelta(days=days - 1)]["active"] -
            (sum([self.datadict[date - datetime.timedelta(days=day)]["leaves"]
                  for day in range(days - 1)])
             if not self.options["always_active"] else 0) +

            # => joined during period  => counted as fraction
            sum([
                (day + 1) / days * self.datadict[
                    date - datetime.timedelta(days=day)]["joins"]
                for day in range(days - 1)]) +

            # left during period => counted as fraction
            (sum([
                (days - day - 1) / days * self.datadict[
                    date - datetime.timedelta(days=day)]["leaves"]
                for day in range(days - 1)])
             if not self.options["always_active"] else 0))

        # count as half:
        participant_days -= self.datadict[
            date + datetime.timedelta(days=1)]["leaves"] / 14
        return participant_days

    def get_date_range(self, source_measure, average):
        """Return the date range for which to calculate source_measure"""

        min_date = min(self.datadict.keys())
        max_date = max(self.datadict.keys())

        # min_date: first date datadict
        # max_date: last date datadict

        if (source_measure in ["inet_cases", "inet_actives", "inet_incidence",
                               "inet_control"]):
            # all source_measures which calculate the total over the
            # previous 7 days
            max_date += datetime.timedelta(days=average - 1)
        if source_measure in ["eiss_incidence"]:
            min_date -= datetime.timedelta(days=6)

        if self.options["snapshot"] is not None:
            max_date = min(max_date,
                           self.options["snapshot"] -
                           datetime.timedelta(days=1))

        return min_date, max_date + datetime.timedelta(days=1)
        # TODO: think hard if adding 1 day (inet_incidence, climate)

    def add_calculated(self):
        """Add an calculated values"""
        # (too many branches) pylint: disable=R0912

        source_measure = self.options["source_measure"]
        average = self.options["average"]
        active = 0
        cum = 0

        # active: active participants
        # inet_cases: cases over the last 7 days
        # inet_incidence: incidence over the last 7 days
        # inet_control: percentage of control over last 7 days
        # control_week: control cases over the last 7 days

        min_date, max_date = self.get_date_range(source_measure, average)
        for date in tools.daterange(min_date, max_date):
            dates = (None
                     if date - datetime.timedelta(days=average-1) < min_date
                     else list(tools.daterange(
                         date, date - datetime.timedelta(days=average), -1)))
            daydata = self.datadict[date]

            if source_measure in ["inet_actives", "inet_participants",
                                  "inet_incidence"]:
                active += daydata["joins"]
                if not self.options["always_active"]:
                    active -= daydata["leaves"]
                daydata["active"] = active
                if date + datetime.timedelta(days=6) < max_date:
                    self.datadict[date + datetime.timedelta(days=6)][
                        "inet_participants"] = daydata["active"]

            if source_measure == "inet_cum":
                cum += daydata["cases"]
                daydata["inet_cum"] = cum

            if source_measure == "inet_surveys" and dates is not None:
                daydata["inet_surveys"] = sum([
                    self.datadict[date2]["cases"]
                    for date2 in dates])

            if (source_measure in ("inet_cases", "inet_incidence",
                                   "inet_control", "inet_reporting") and
                    dates is not None):
                daydata["inet_cases"] = sum([
                    self.datadict[date2]["cases"] for date2 in dates])
#                 if (self.options["snapshot"] is not None and
#                         (self.options["snapshot"] -
#                          datetime.timedelta(days=1)) == date):
#                     daydata["inet_cases"] *= 1.05

            if source_measure in ("inet_reporting") and dates is not None:
                daydata["inet_actives"] = sum([
                    self.datadict[date2]["surveys"] for date2 in dates])
            if source_measure in ("inet_actives", "inet_incidence"):
                daydata["inet_actives"] = self.participant_days(date, average)

            if (source_measure == "inet_incidence" and
                    daydata["inet_actives"] >
                    self.options["min_participants"]):
                daydata["inet_incidence"] = int(
                    100000 * daydata["inet_cases"] /
                    daydata["inet_actives"] * 7 / average)
                print(daydata)
                props = tools.get_prop(daydata["inet_cases"],
                                       daydata["inet_actives"],
                                       method="jeffreys")
                print(props)
                # method="wilson-continuity")
                daydata["inet_incidence"] = int(props[1] * 100000 * 7 /
                                                average)
                daydata["min_incidence"] = int(props[0] * 100000 * 7 / average)
                daydata["max_incidence"] = int(props[2] * 100000 * 7 / average)
            if (source_measure == "inet_reporting" and
                    daydata["inet_actives"] >
                    self.options["min_participants"]):
                daydata["inet_reporting"] = (
                    100000 * daydata["inet_cases"] /
                    daydata["inet_actives"] * 7 / average)

            if (source_measure == "inet_control" and
                    daydata["inet_cases"] > 0 and
                    dates is not None):
                daydata["control_week"] = sum([
                    self.datadict[date2]["control"] for date2 in dates])
                daydata["inet_control"] = (100 * daydata["control_week"] /
                                           daydata["inet_cases"])

            if source_measure.startswith("climate") and dates is not None:
                if source_measure == "climate_prcp":
                    values = sum([
                        self.datadict[date2]["real_{0}".format(source_measure)]
                        for date2 in dates]) * 7 / average  # TODO
                else:
                    values = [
                        self.datadict[date2]["real_{0}".format(source_measure)]
                        for date2 in dates]
                    if len(values) - values.count(0) > 0:
                        daydata[source_measure] = (
                            sum(values) / (len(values) - values.count(0)))

            if (source_measure in ("eiss_incidence") and
                    "eiss_incidence" in daydata and
                    dates is not None):
                daydata["eiss_incidence_avg"] = numpy.average([
                    self.datadict[date2]["eiss_incidence"]
                    for date2 in dates
                    if "eiss_incidence" in self.datadict[date2]])
            date += datetime.timedelta(days=1)

        if source_measure == "eiss_incidence":
            for date, daydata in self.datadict.items():
                if "eiss_incidence" in daydata:
                    daydata["real_eiss_incidence"] = daydata["eiss_incidence"]
                if "eiss_incidence_avg" in daydata:
                    daydata["eiss_incidence"] = daydata["eiss_incidence_avg"]

        self._shift(average)

    def _shift(self, average):
        """Shift the days because of the average"""

        shift = (average - 7) // 2
        if shift > 0:
            for date, daydata in tools.sort_iter(self.datadict):
                date_future = date + datetime.timedelta(days=shift)
                if date_future in self.datadict:
                    daydata_future = self.datadict[date_future]
                    for column in ["inet_incidence", "eiss_incidence",
                                   "climate_temp", "climate_sun",
                                   "climate_ahum"]:
                        if column in daydata_future:
                            daydata[column] = daydata_future[column]
                            del daydata_future[column]
                date += datetime.timedelta(days=1)

    def add_sun(self):
        """Add sunlight hours"""
        min_date, max_date = utils.get_limits(self.options["season"])
        average = self.options["average"]
        min_date -= datetime.timedelta(days=6 + (average - 7) // 2)
        max_date += datetime.timedelta(days=(average - 7) // 2)

        date = min_date
        while date < max_date:
            self.datadict[date]["real_{0}".format(
                self.options["source_measure"])] = tools.get_sun(
                    self.options["country"], date)
            date += datetime.timedelta(days=1)

    def add_other(self, source, label):
        """Add columns from table, as datadict[key]"""

#         if source == "eiss" and label == "inf":
#             self.add_other("eiss", "infa")
#             self.add_other("eiss", "infb")
#             return

        min_date, max_date = utils.get_limits(self.options["season"])
        if (self.options["source"] == "eiss" and
                self.options["snapshot"] is not None):
            max_date = min(max_date,
                           self.options["snapshot"] -
                           datetime.timedelta(days=3))

        if source == "noaa":
            average = self.options["average"]
            min_date -= datetime.timedelta(days=6 + (average - 7) // 2)
            max_date += datetime.timedelta(days=(average - 7) // 2)

        if (source == "eiss" and label == "ili" and
                self.options["country"] in ["fr"]):
            label = "ari"
        if (source == "eiss" and label == "ili" and
                self.options["country"] == "se" and
                self.options["season"] in ["2003/04", "2004/05"]):
            return
        cursor = utils.query("""SELECT
                date,
                value
            FROM
                other
            WHERE
                country = %(country)s AND
                source = %(source)s AND
                label = %(label)s AND
                date >= %(min_date)s AND
                date <= %(max_date)s
            """, {"country": self.options["country"],
                  "source": source,
                  "label": label,
                  "min_date": min_date,
                  "max_date": max_date})
        for row in cursor.fetchall():
            if "factor" in self.options:
                value = row["value"] * self.options["factor"]
            else:
                value = row["value"]
            if self.options["source"] == "climate":
                self.datadict[row["date"]]["real_{0}".format(
                    self.options["source_measure"])] = value
            else:
                self.datadict[row["date"]][
                    self.options["source_measure"]] = value

    def get_totals_other(self, min_date=None, max_date=None):
        """Add columns from table, as datadict[key]"""

        if (self.options["source"] == "eiss" and
                self.options["casedef"] == "ili" and
                self.options["country"] in ["fr"]):
            self.options["casedef"] = "ari"
        min_date2, max_date2 = utils.get_limits(self.options["season"])
        if min_date is None:
            min_date = min_date2
        if max_date is None:
            max_date = max_date2

        cursor = utils.query("""SELECT
                SUM(value) AS total
            FROM
                other
            WHERE
                country = %(country)s AND
                source = %(source)s AND
                label = %(label)s AND
                date >= %(min_date)s AND
                date <= %(max_date)s
            """, {"country": self.options["country"],
                  "source": self.options["source"],
                  "label": self.options["casedef"],
                  "min_date": min_date,
                  "max_date": max_date})
        row = cursor.fetchone()
        return 0 if row["total"] is None else int(row["total"])

    def get_totals(self, min_date=None, max_date=None):
        """Return totals"""

        totals = {}
        if ("date_range" in self.options and
                min_date is None and max_date is None):
            totals = collections.defaultdict(int)
            date_ranges = self.options["date_range"].split(config.SEP["dates"])
            # del self.options["date_range"]
            for date_range in date_ranges:
                min_date, max_date = date_range.split(config.SEP["daymonth"])
                if min_date == "":
                    min_date = None
                if max_date == "":
                    max_date = None
                for key, value in self.get_totals(min_date, max_date).items():
                    totals[key] += value
            return totals

        if self.options["source"] == "europe":
            totals["actives"] = self.population
        elif self.options["source"] == "eiss":
            totals["cases"] = self.get_totals_other(min_date, max_date)
        elif self.options["survey_cutter"] != "":
            series = Series(
                self.options,
                "control" if self.options["measure"] == "control" else
                "cases")
            totals = series.get_total_survey_cutter(min_date=min_date,
                                                    max_date=max_date)
        else:
            if self.options["measure"] in ("incidence", "actives",
                                           "participants"):
                series = Series(self.options, "joins")

                # active is everybody who ever joined (no min/max date)
                # is never used together with cases, in which case
                # data.participant_days() is to be used
                totals["actives"] = series.get_total(None, None)
            if self.options["measure"] in ("cases", "incidence", "control",
                                           "surveys"):
                series = Series(self.options, "cases")
                totals["cases"] = series.get_total(min_date, max_date)

            if self.options["measure"] == "control":
                series = Series(self.options, "control")
                totals["control"] = series.get_total(min_date, max_date)
        return totals
