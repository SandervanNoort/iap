#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Get data from the database and calculated values"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import collections
import natsort

from . import samples, utils, split, baseline, tools
from .data import Data


class Venn(object):
    """Class to calculate venn diagrams"""
    # (Too few public methods) pylint: disable=R0903

    def __init__(self, settings, datasets):
        self.settings = settings
        self.datasets = datasets

    def get_venn(self):
        """Get Venn data"""
        set0 = self.datasets[self.settings["datasets"][0]]
        total0 = Data(options=set0).get_totals()["cases"]
        set1 = self.datasets[self.settings["datasets"][1]]
        total1 = Data(options=set1).get_totals()["cases"]
        overlap = self.datasets[self.settings["datasets"][2]]
        overlap = Data(options=overlap).get_totals()["cases"]

        surveys = self.datasets[self.settings["datasets"][3]]
        surveys = Data(options=surveys).get_totals()["cases"]

        data = [total0, total1, overlap, surveys]
        names = (set0["label"], set1["label"])
        return data, names


class BarData(object):
    """Class to make a table-dict from datasets"""
    # R0903 = Too few public methods

    def __init__(self, settings, datasets, all_datasets=None):
        self.settings = settings
        self.datasets = datasets
        self.all_datasets = (all_datasets if all_datasets is not None else
                             datasets)

    def get_date_range(self, options):
        """Get the date range for the barplot"""

        min_date, max_date = None, None
        if self.settings["bars"] in ("compare", "attack", "surveys"):
            min_date, max_date = samples.get_limits(
                options["season"], options["country"],
                options["samples_onsets"])
        return min_date, max_date

    def get_table(self):
        """Return table of values"""

        table = collections.defaultdict(lambda: collections.defaultdict(int))
        baseline_datasets = utils.get_datasets_keys(
            self.all_datasets, self.settings["baseline"])
        baseline_dict = baseline.get_dict(baseline_datasets)
        citylabels = tools.SetList()
        for options in self.datasets.values():
            cell = table[(options["label"], options["citylabel"])]

            min_date, max_date = self.get_date_range(options)

            data = Data(options=options)
            totals = data.get_totals(min_date, max_date)
            if options["source_measure"] == "eiss_incidence":
                cell["value"] += totals["cases"]
                cell["denominator"] += 100000
            elif self.settings["bars"] in ("compare", "attack"):
                cell["value"] += totals["cases"]
                cell["denominator"] += (
                    totals["actives"] if self.settings["full_denominator"] else
                    data.participant_days(max_date,
                                          (max_date - min_date).days))
                if baseline_dict and "baseline" not in cell:
                    cell["baseline"] = int(
                        sum([value
                             for date, value in zip(*baseline.get_baseline(
                                 baseline_dict, options["season"]))
                             if date >= min_date and date <= max_date]) /
                        7)
            elif self.settings["bars"] == "control":
                cell["value"] += totals["control"]
                cell["denominator"] += totals["cases"]
            elif self.settings["bars"] == "surveys":
                cell["value"] += totals["cases"]
                cell["denominator"] += ((max_date - min_date).days + 1) / 7
            elif self.settings["bars"] == "percentage_by_answer":
                if not split.show_hist(
                        options["full_cutter"], options["full_answer"]):
                    continue

                cell["value"] += totals["actives"]

                # replace all label pieces with "all(...)"
                options = options.copy()
                options["answer"] = split.get_all(options["cutter"])
                split.set_full(options)
                totals = Data(options=options).get_totals(min_date, max_date)
                cell["denominator"] = totals["actives"]
            elif "actives" in totals:
                # "pie", "percentage_by_city", "absolute"
                # "percentage_by_label"
                cell["value"] += totals["actives"]
            else:
                for key, value in totals.items():
                    cell = table[(options["label"], key)]
                    cell["value"] = value
                    citylabels.append(key)

        citylabels = natsort.natsorted(
            citylabels, key=tools.key_bigsmall)

        # note: self.get_labels modifies table (removes non-zeros)
        return table, self.get_labels(table, citylabels)

    def get_labels(self, table, citylabels=None):
        """Return the non-empty house and citylabels"""

        datasets = (self.all_datasets if self.settings["all_labels"] else
                    self.datasets)
        all_houselabels = tools.SetList(
            [options["label"] for options in datasets.values()])
        all_citylabels = tools.SetList([
            options["citylabel"] for options in datasets.values()])

        if citylabels is not None:
            all_citylabels.extend(citylabels)

        for label in self.settings["ignore_labels"]:
            if label in all_houselabels:
                all_houselabels.remove(label)
            if label in all_citylabels:
                all_citylabels.remove(label)

        labels = {"house": [], "city": []}

        for houselabel in all_houselabels:
            nominator = sum([table[(houselabel, citylabel)]["value"]
                             for citylabel in all_citylabels]) > 0
            denominator = sum([
                table[(houselabel, citylabel)]["denominator"]
                for citylabel in all_citylabels]) > 0
            if (self.settings["all_houses"] or
                    nominator > 0 or
                    (denominator > 0 and
                     self.settings["house_zero_nominator"])):
                labels["house"].append(houselabel)
            # ?? labels["city"] = all_citylabels
        for citylabel in all_citylabels:
            nominator = sum([table[(houselabel, citylabel)]["value"]
                             for houselabel in all_houselabels]) > 0
            denominator = sum([
                table[(houselabel, citylabel)]["denominator"]
                for houselabel in all_houselabels]) > 0
            if (self.settings["all_cities"] or
                    nominator > 0 or
                    (denominator > 0 and
                     self.settings["city_zero_nominator"])):
                labels["city"].append(citylabel)

#         if len(self.settings["city_labels"]) > 0:
#             labels["city"] = self.settings["city_labels"]

        for (houselabel, citylabel) in list(table.keys()):
            if houselabel not in labels["house"] \
                    or citylabel not in labels["city"]:
                del table[(houselabel, citylabel)]

        return labels
