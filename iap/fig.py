#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Various plots"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import collections
import matplotlib
import os
import numpy

import pyfig

from .maps import Map, FigMap
from .xyplot import XYPlot, Base
from .exceptions import IAPError
from .bardata import BarData, Venn
from . import split, utils, config, tools


class Barplot(Base):
    """Class to make barplots"""

    def __init__(self, fig, settings, datasets):
        Base.__init__(self, fig, settings, datasets)

        self.fig.settings["rc"]["legend.handletextpad"] = 0.3
        matplotlib.rcParams.update(self.fig.settings["rc"])

        self.ax = self.fig.add_ax(settings["row"], settings["col"])
        if self.settings["horizontal"]:
            self.ax.horizontal = True

    def get_barplot_data_compare(self, table, labels):
        """Set the table for risk plot"""

        barplot_data = {}
        cutter = set([options["cutter"]
                      for options in self.datasets.values()])
        if len(cutter) != 1:
            raise IAPError("Multiple cutters defined in the datasets")
        cutter = cutter.pop()
        ref_label = split.get_answer_label(
            cutter, split.get_reference(cutter))

        labels["house"].remove(ref_label)
        for city in labels["city"]:
            ref_cases = table[(ref_label, city)]["value"]
            ref_active = table[(ref_label, city)]["denominator"]
            if "baseline" in table[(ref_label, city)]:
                ref_cases -= int(table[(ref_label, city)]["baseline"] *
                                 ref_active / 100000)
                ref_cases = max(0, ref_cases)
            for house in labels["house"]:
                new_cases = table[(house, city)]["value"]
                new_active = table[(house, city)]["denominator"]
                if "baseline" in table[(house, city)]:
                    new_cases -= int(table[(ref_label, city)]["baseline"] *
                                     new_active / 100000)
                    new_cases = max(0, new_cases)
                if new_active == 0:
                    continue
                if self.settings["compare"] == "rrr":
                    vals = tools.get_rrr(
                        new_cases, new_active, ref_cases, ref_active)
                    barplot_data[(house, city)] = (
                        100 * vals[1], 100 * (vals[1] - vals[0]),
                        100 * (vals[2] - vals[1]))
                elif self.settings["compare"] == "oddr":
                    vals = tools.get_oddr(
                        new_cases, new_active, ref_cases, ref_active)
                    barplot_data[(house, city)] = (vals[1], vals[1] - vals[0],
                                                   vals[2] - vals[1])
                elif self.settings["compare"] == "rr":
                    vals = tools.get_rr(
                        new_cases, new_active, ref_cases, ref_active)
                    barplot_data[(house, city)] = (vals[1], vals[1] - vals[0],
                                                   vals[2] - vals[1])
                else:
                    raise IAPError(
                        "compare {0} should be rrr/compare".format(
                            self.settings["compare"]))
        if self.settings["ymin"] == 0:
            self.settings["ymin"] = None
        return barplot_data

    def get_barplot_data(self, table, labels):
        """Create bar data"""

        barplot_data = collections.defaultdict(int)
        for (house, city), values in table.items():
            if self.settings["bars"] in ("attack", "compare", "control",
                                         "percentage_by_answer"):
                if "prop" not in values:
                    values["min_prop"], values["prop"], values["max_prop"] = \
                        tools.get_prop(values["value"],
                                       values["denominator"])
                barplot_data[(house, city)] = (
                    [100 * values["prop"],
                     100 * (values["prop"] - values["min_prop"]),
                     100 * (values["max_prop"] - values["prop"])]
                    if self.settings["errors"] else
                    100 * values["prop"])
            elif self.settings["bars"] == "surveys":
                barplot_data[(house, city)] = (
                    values["value"] / values["denominator"])
            else:
                barplot_data[(house, city)] = values["value"]

        if self.settings["bars"] == "percentage_by_city":
            for city in labels["city"]:
                sumval = sum([
                    value for (house2, city2), value in barplot_data.items()
                    if city == city2])
                for house in labels["house"]:
                    barplot_data[(house, city)] = (
                        100 * barplot_data[(house, city)] / sumval)
        elif self.settings["bars"] == "percentage_by_label":
            for house in labels["house"]:
                sumval = sum([
                    value for (house2, city2), value in barplot_data.items()
                    if house == house2])
                for city in labels["city"]:
                    barplot_data[(house, city)] = (
                        100 * barplot_data[(house, city)] / sumval)
        return barplot_data

    def get_compare_colors(self, barplot_data, labels):
        """Get the city colors for the compare plot"""

        threshold = 0 if self.settings["compare"] == "rrr" else 1

        house = labels["house"][0]
        colors = self.settings["compare_colors"]
        city_colors = []
        for city in labels["city"]:
            val, ci_down, ci_up = barplot_data[(house, city)]
            min_val = val - ci_down
            max_val = val + ci_up
            city_colors.append(
                colors[3] if val > threshold and min_val > threshold else
                colors[2] if val > threshold else
                colors[0] if val < threshold and max_val < threshold else
                colors[1])
        return city_colors

    def draw(self):
        """draw the barplot"""

        bardata = BarData(self.settings, self.datasets, self.all_datasets)
        table, labels = bardata.get_table()

        labels["city"] = (self.settings["all_city_labels"] if
                          len(self.settings["all_city_labels"]) > 0 else
                          labels["city"])

        if len(labels["house"]) == 0 or len(labels["city"]) == 0:
            return False

        barplot_data = (self.get_barplot_data_compare(table, labels)
                        if self.settings["bars"] == "compare"
                        else self.get_barplot_data(table, labels))

        # removing the reference could lead to zero labels
        if len(labels["house"]) == 0 or len(labels["city"]) == 0:
            return False

        colors = {}
        colors["house"] = [
            [options["color"]
             for options in self.datasets.values()
             if house == options["label"]][0]
            for house in labels["house"]]

        if (self.settings["bars"] == "compare" and
                len(labels["house"]) < 2 and
                len(self.settings["compare_colors"]) > 0):
            colors["city"] = self.get_compare_colors(barplot_data, labels)

        if self.settings["citylabels"]:
            labels = {"house": labels["city"], "city": labels["house"]}
            barplot_data = dict([
                ((city, house), values)
                for (house, city), values in barplot_data.items()])
            colors["city"] = colors["house"]

        if self.settings["city_sort"]:
            labels["city"].sort(
                key=lambda citylabel: sum([
                    value[0] if isinstance(value, list) else value
                    for (house, city), value in barplot_data.items()
                    if city == citylabel]),
                reverse=self.settings["reverse_sort"])
        if self.settings["house_sort"]:
            labels["house"].sort(
                key=lambda houselabel: sum([
                    value[0] if isinstance(value, list) else value
                    for (house, city), value in barplot_data.items()
                    if house == houselabel]),
                reverse=self.settings["reverse_sort"])

        if self.settings["bars"] == "pie":
            self.make_pie(barplot_data, labels, colors)
        else:
            self.make_bar(barplot_data, labels, colors)
        self.set_labels()
        self.set_ylim()
        self.ax.yaxis.grid(self.settings["grid"])
        self.ax.ncol = self.settings["ncol"]
        if self.settings["bars"] == "attack":
            baseline_data = {}
            for key, values in table.items():
                if "baseline" in values:
                    baseline_data[key] = values["baseline"] / 1000
            if len(baseline_data) > 0:
                colors = {
                    "house": (len(labels["house"]) *
                              [self.fig.settings["baseline_color"]]),
                    "city": (len(labels["city"]) *
                             [self.fig.settings["baseline_color"]])}
                self.ax.barplot(
                    self.translate(baseline_data),
                    self.translate(labels),
                    colors,
                    city_distance=self.settings["citydistance"],
                    house_distance=self.settings["housedistance"],
                    alpha=0.8)

#         if (self.settings["bars"] == "compare" and
#                 self.settings["compare"] == "oddr"):
#             self.ax.axhline(1.0, ymax=0.85, linestyle="--", color="black")
        return True

    def set_ylim(self):
        """Set the yax limits"""

        Base.set_ylim(self)

        # add 5% space to prevent errorbars to be aligend with axes
        if not self.ax.horizontal:
            ymin, ymax = self.ax.get_ylim()
            self.ax.set_ylim(ymin * 1.05, ymax * 1.05)
        else:
            pass
#             ymin, ymax = self.ax.get_xlim()
#             self.ax.set_ylim(ymin * 1.05, ymax * 1.05)

    def make_bar(self, barplot_data, labels, colors):
        """Make a barplot"""
        if self.settings["floors"]:
            if "house" in labels:
                labels["floor"] = labels["house"]
                del labels["house"]
            if "house" in colors:
                colors["floor"] = colors["house"]
                del colors["house"]

        self.ax.barplot(
            self.translate(barplot_data),
            self.translate(labels),
            colors,
            city_distance=self.settings["citydistance"],
            house_distance=self.settings["housedistance"],
            leg_place=(None
                       if ("house" in labels and len(labels["house"]) == 1)
                       else self.settings["leg_place"]))
#         if old_labels is not None:
#             labels["house"] = old_labels

    def make_pie(self, bar_data, labels, colors):
        """Make a single pie"""

        pievalues = [sum([value for (house, _city), value in bar_data.items()
                          if house == house2])
                     for house2 in labels["house"]]
        pielabels = (labels["house"] if self.settings["pietext"] else
                     [""] * len(labels["house"]))

        _patches, texts, autotexts = self.ax.pie(
            pievalues,
            colors=colors["house"],
            labels=tools.wrap(self.translate(pielabels)),
            legends=self.translate(labels["house"]),
            labeldistance=1.05,
            autopct="%1.0f%%",
            pctdistance=0.7,
            radius=1 if self.settings["pietext"] else 1.24)
        for text in autotexts:
            text.set_fontsize(self.settings["piefont"])
        self.fig.texts.extend(texts)
        for text in texts:
            if text.get_position()[1] > 0:
                text.set_va("bottom")
            else:
                text.set_va("top")
        self.settings["ymin"] = None

    def get_ylabel(self, _ax_name):
        """Return the ylabel"""
        if self.settings["bars"] == "attack":
            ylabel = "attack"
        elif self.settings["bars"] == "control":
            ylabel = "control"
        elif self.settings["bars"] == "absolute":
            ylabel = "participants"
        elif self.settings["bars"] == "compare":
            ylabel = self.settings["compare"]
        elif self.settings["bars"] == "surveys":
            ylabel = "surveys"
        elif self.settings["bars"] == "pie":
            ylabel = None
        elif self.settings["bars"] == "percentage_by_city" \
                or self.settings["bars"] == "percentage_by_label" \
                or self.settings["bars"] == "percentage_by_answer":
            ylabel = "control"
        else:
            raise IAPError("Unknown settings[bars]: {0}".format(
                self.settings["bars"]))

        if ylabel:
            ylabel = "<<measure:{0}>> <<measure:{0}_unit>>".format(ylabel)
        return ylabel


class VennPlot(Base):
    """Make a venn diagram"""

    def __init__(self, fig, settings, datasets):
        Base.__init__(self, fig, settings, datasets)

        self.alphas = [0.8, 0.8]
        self.fig.settings["rc"]["legend.handletextpad"] = 0.3
        matplotlib.rcParams.update(self.fig.settings["rc"])

        self.ax = self.fig.add_ax(settings["row"], settings["col"])

    def draw(self):
        """Draw the venn diagram"""

        venn = Venn(self.settings, self.datasets)
        data, names = venn.get_venn()

        sizes = numpy.array(data[0:2])
        radius = numpy.sqrt(sizes / numpy.pi)
        distance = self.get_distance(radius, data[2])

        colors = [[options["color"]
                   for options in self.datasets.values()
                   if house == options["label"]][0]
                  for house in names]
        names = self.translate(names)

        kwargs = self.ax.parse_color(colors[0])
        self.ax.add_artist(
            matplotlib.patches.Circle(
                (0, 0),
                radius=radius[0],
                alpha=self.alphas[0],
                **kwargs))
        self.fig.add_line(
            matplotlib.patches.Circle(
                (0, 0), 1,
                alpha=self.alphas[0],
                **kwargs),
            names[0])

        kwargs = self.ax.parse_color(colors[1])
        self.ax.add_artist(
            matplotlib.patches.Circle(
                (distance, 0),
                radius=radius[1],
                alpha=self.alphas[1],
                **kwargs))
        self.fig.add_line(
            matplotlib.patches.Circle(
                (0, 0), 1,
                alpha=self.alphas[1],
                **kwargs),
            names[1])

        pad_x, pad_y = self.set_lim(radius, distance)

        sens, spec = self.get_sens_spec(data)
        # "{0:.1f}% / {1:.1f}%".format(100 * sens, 100 * spec)

        self.ax.text(distance + radius[1] + pad_x, pad_y,
                     "Sensitivity: {0:.1f}%".format(100 * sens),
                     fontsize=8,
                     verticalalignment="bottom",
                     horizontalalignment="left")
        self.ax.text(distance + radius[1] + pad_x, -pad_y,
                     "Specificity: {0:.1f}%".format(100 * spec),
                     fontsize=8,
                     verticalalignment="top",
                     horizontalalignment="left")
        # center = radius[0] - (sum(radius) - distance) / 2

        return True

    def set_lim(self, radius, distance):
        """Set the ax limites"""

        xmin, ymin = self.ax.transAxes.transform((0, 0))
        xmax, ymax = self.ax.transAxes.transform((1, 1))
        scale = (ymax - ymin) / (xmax - xmin)

        self.ax.set_frame_on(False)
        self.ax.set_yticks([])
        self.ax.set_xticks([])

        textsize = 20

        xmin = -radius[0]
        xmax = distance + radius[1]

        textsize = (xmax - xmin) * 0.5
        xmax += textsize
        pad_x = (xmax - xmin) / 50
        pad_y = scale * pad_x

        xmin -= pad_x
        xmax += pad_x

        self.ax.set_xlim(xmin, xmax)
        self.ax.set_ylim(-scale * (xmax - xmin) / 2,
                         scale * (xmax - xmin) / 2)

        return (pad_x, pad_y)

    @staticmethod
    def get_sens_spec(data):
        """Calculate sensitivity / specificitiy"""
        selfdiag, casedef, overlap, surveys = data
        true_pos = overlap
        false_neg = selfdiag - overlap
        true_neg = surveys + overlap - selfdiag - casedef
        false_pos = casedef - overlap

        spec = true_neg / (true_neg + false_pos)
        sens = true_pos / (true_pos + false_neg)
        return (sens, spec)

    @staticmethod
    def get_overlap(radius, distance):
        """Calculate the overlap of two spheres"""
        alpha = ((distance ** 2 + radius[0] ** 2 - radius[1] ** 2) /
                 (2 * radius[0] * distance))
        alpha = 2 * numpy.arccos(alpha)
        beta = ((distance ** 2 + radius[1] ** 2 - radius[0] ** 2) /
                (2 * radius[1] * distance))
        beta = 2 * numpy.arccos(beta)
        return (0.5 * radius[0] ** 2 * (alpha - numpy.sin(alpha)) +
                0.5 * radius[1] ** 2 * (beta - numpy.sin(beta)))

    def get_distance(self, radius, overlap):
        """Return distance between the two spheres"""

        lower = abs(radius[0] - radius[1])  # fully overlap
        upper = radius[0] + radius[1]  # no overlap
        distance = (lower + upper) / 2
        test_overlap = self.get_overlap(radius, distance)
        while abs(test_overlap - overlap) > 0.5:
            if test_overlap > overlap:
                lower = distance
            else:
                upper = distance
            distance = (lower + upper) / 2
            test_overlap = self.get_overlap(radius, distance)
        return distance


def Fig(settings):
    """Return correct Fig object (factory function)"""
    # (Invalid name) pylint: disable=C0103

    if "map" in settings and "mapname" in settings["map"]:
        return FigMap(settings)
    elif "fig" in settings:
        return Figure(settings)
    else:
        return None


class Figure(pyfig.Figure):
    """A figure extension for IAP figures"""
    # (too many plublic) pylint: disable=R0904

    def __init__(self, settings):
        if "fig" in settings:
            settings = settings["fig"]
        pyfig.Figure.__init__(self, settings)
        self.translate = lambda text: utils.translate(
            text, self.settings["lang"])

    def save(self, figname=None, **kwargs):
        """Save the figure, with url and info"""

        self.settings["url"] = self.translate(self.settings["url"])
        if self.settings["logo"] == "inet":
            self.settings["logo"] = "{0}".format(
                os.path.join(config.LOCAL["dir"]["data"], "logo.png"))

        self.settings["title"] = self.translate(self.settings["title"])

        pyfig.Figure.save(self, figname, **kwargs)


def dia(fig, settings, datasets):
    """Dia instance, which depending on settings is a plot or a barplot"""

    if settings["type"] == "plot":
        return XYPlot(fig, settings, datasets)
    elif settings["type"] == "barplot":
        return Barplot(fig, settings, datasets)
    elif settings["type"] == "map":
        return Map(fig, settings, datasets)
    elif settings["type"] == "venn":
        return VennPlot(fig, settings, datasets)
    else:
        raise IAPError("Unknown plottype: {0}".format(settings["type"]))
