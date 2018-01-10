#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Plots in time"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import collections
import datetime
import matplotlib
import logging
import six

from .data import Data
from .exceptions import IAPError
from . import utils, samples, linreg, baseline, config, tools

logger = logging.getLogger(__name__)


class Base(object):
    """Base class for figures"""
    def __init__(self, fig, settings, datasets):
        self.fig = fig
        self.settings = settings
        self.translate = lambda text: utils.translate(
            text,
            self.fig.settings["lang"] if fig is not None else None)

        self.all_datasets = datasets
        self.datasets = (
            utils.get_datasets_keys(datasets, settings["datasets"])
            if len(settings["datasets"]) > 0 else
            datasets)

        self.ax = None
        self.ax2 = None
        # self.set_samples_range()

    def set_ylabels(self):
        """Set the ylabels"""
        if self.ax:
            if self.settings["ylabel"] == "auto":
                ylabel = self.get_ylabel(self.ax.name)
            else:
                ylabel = self.settings["ylabel"]
            if ylabel is not None:
                self.ax.set_ylabel(
                    tools.wrap(
                        self.translate(ylabel), self.settings["wrap"]),
                    multialignment="center")
        if self.ax2 and not hasattr(self.ax2, "empty"):
            if self.settings["ylabel2"] == "auto":
                ylabel2 = self.get_ylabel(self.ax2.name)
            else:
                ylabel2 = self.settings["ylabel2"]
            if ylabel is not None:
                self.ax2.set_ylabel(
                    tools.wrap(
                        self.translate(ylabel2), self.settings["wrap"]),
                    multialignment="center")

    def get_ylabel(self, ax_name):
        """Default empty ylabel"""
        # (Method could be function) pylint: disable=R0201
        # (Unused argument) pylint: disable=W0613
        return ""

    def set_labels(self):
        """Set the labels of the plot"""
        self.set_ylabels()

        if self.settings["xlabel"] == "auto" and "xlabel_id" in self.settings:
            self.ax.set_xlabel(self.translate("<<xlabel:{0}>>".format(
                self.settings["xlabel_id"])))
        elif self.settings["xlabel"] != "auto":
            self.ax.set_xlabel(self.translate(self.settings["xlabel"]))

        if self.settings["xangle"] > 0:
            for label in self.ax.get_xticklabels():
                label.set_rotation(self.settings["xangle"])

        if self.settings["label"] != "":
            self.ax.label = self.translate(self.settings["label"])
        if self.settings["topright"] != "":
            self.ax.topright = self.translate(self.settings["topright"])

    def get_ax(self, name):
        """Return the ax with this name"""
        if self.ax and self.ax.name == name:
            return self.ax
        elif self.ax2 and self.ax2.name == name:
            return self.ax2
        else:
            raise IAPError("Unknown ax {0}".format(name))

    def set_ylim(self):
        """Set the y-ax limits, based on the linear regression"""

        if self.settings["ymax"] is not None:
            if (hasattr(self.ax, "ymax") and
                    self.ax.ymax > self.settings["ymax"]):
                self.ax.set_ylim(None, self.ax.ymax)
            else:
                self.ax.set_ylim(None, self.settings["ymax"])
        if self.ax2 and self.settings["ymax2"] is not None:
            if (hasattr(self.ax2, "ymax") and
                    self.ax2.ymax > self.settings["ymax2"]):
                self.ax2.set_ylim(None, self.ax2.ymax)
            else:
                self.ax2.set_ylim(None, self.settings["ymax2"])
        if self.settings["ymin"] is not None:
            self.ax.set_ylim(self.settings["ymin"], None)
        if self.ax2 and self.settings["ymin2"] is not None:
            self.ax2.set_ylim(self.settings["ymin2"], None)

        if self.settings["yticks"] is not None:
            self.ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(
                self.settings["yticks"]))
        if self.ax2 and self.settings["yticks2"] is not None:
            self.ax2.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(
                self.settings["yticks2"]))


class XYPlot(Base):
    """The plot class to make timeseries"""

    def __init__(self, fig, settings, datasets):
        Base.__init__(self, fig, settings, datasets)

        source_measures = tools.SetList()
        ax_names = tools.SetList()
        for options in self.datasets.values():
            source_measures.append(options["source_measure"])
            ax_names.append(options["ax_name"])

        if len(ax_names) == 0:
            logger.warning("No axes available")
        elif len(ax_names) == 1:
            self.ax = self.fig.add_ax(settings["row"], settings["col"])
            self.ax.name = ax_names[0]
        elif len(ax_names) == 2:
            ax_names.sort(key=lambda ax: ax == settings["left_ax"],
                          reverse=True)
            self.ax2 = self.fig.add_ax(settings["row"], settings["col"])
            self.ax = self.fig.add_ax2(self.ax2)
            self.ax.name = ax_names[0]
            self.ax2.name = ax_names[1]
        else:
            raise IAPError("Number of axes exceeds two: {0} - {1}".format(
                source_measures, ax_names))

        self.datadicts = {plot_name: Data(options).get_datadict()
                          for plot_name, options in self.datasets.items()}

        self.fill = {"bottom": collections.defaultdict(int),
                     "upper": collections.defaultdict(int)}
        self.last = {}
        self.periods = {}

        if (len(ax_names) != 0 and
                (settings["grid"] or settings["xgrid"] or settings["ygrid"])):
            self.ax.grid(
                axis=("both" if (settings["grid"] or
                                 settings["xgrid"] and settings["ygrid"]) else
                      "x" if settings["xgrid"] else
                      "y"))
        if len(ax_names) != 0:
            self.ax.ncol = settings["ncol"]

    def draw(self):
        """Plot all the plotnames"""

        xlimits = self.get_xlimits()
        plots = []
        for plot_name, options in self.datasets.items():
            datadict = self.datadicts[plot_name]
            if options["label"] == "Unknown":
                continue
            dates, values = self.get_data(options, xlimits, datadict)
            if dates is None or len(dates) == 0:
                continue
            dates, values, start, end = self.get_start_end(dates, values,
                                                           options)
            if dates is None or len(dates) == 0:
                continue
            result = self.plot_data(dates, values, start, end, options)
            plots.append(options["ax_name"])
            self.periods[utils.country_season_to_period(
                options["country"], options["season"])] = options
            self.plot_band(dates[start:end], options, datadict, result)
        if len(set([ax.name for ax in (self.ax, self.ax2) if ax is not None]) -
               set(plots)) > 0:
            if len(plots) == 0:
                return False
            elif self.ax.name not in plots:
                # The main ax is empty, so break
                return False
            elif self.ax2.name in self.settings["allow_empty"]:
                self.ax2.empty = True
                self.ax2.set_yticks([])
                self.ax2.set_ylabel("")
            else:
                return False

        self.set_labels()
        self.set_xlim()
        self.set_ylim()
        self.set_ranges()
        self.set_yticks()

        return len([plot for plot in plots if plot is not None])

    def set_yticks(self):
        """Set the yticks to be integers"""

        for ax in self.ax, self.ax2:
            if ax is None:
                continue

            if not self.settings["yfractions"]:
                ymin, ymax = ax.get_ylim()
                ax.set_yticks([ytick for ytick in ax.get_yticks()
                               if ytick == round(ytick)])
                ax.set_ylim(ymin, ymax)

    def plot_band(self, dates, options, datadict, result):
        """Plot a band with the confidence interval"""

        if (options["source_measure"] != "inet_incidence" or
                options["band_color"] == ""):
            return

        ax = self.get_ax(options["ax_name"])
        min_values = [datadict[date]["min_incidence"]
                      for date in dates]
        max_values = [datadict[date]["max_incidence"]
                      for date in dates]
#         ax.ymax = (max(ax.ymax, max(max_values)) if hasattr(ax, "ymax") else
#                    max(max_values))

        if self.settings["date_format"] != "year":
            dates = utils.dates2reference_season(dates, options["season"])
        fill_dates, fill_values = matplotlib.mlab.poly_between(
            dates, min_values, max_values)

        color = ("{0}-{1}".format(result[0].get_color(),
                                  options["band_color"])
                 if options["band_color"].startswith("a(") else
                 options["band_color"])
        ax.fill(fill_dates, fill_values,
                color=color,
                label=options["band_label"],
                zorder=-10)

    def set_ranges(self):
        """Grey out regions with low influenza activity"""

        if (self.settings["samples_period"] == 0 and
                self.settings["samples_casedef"] == ""):
            return

        # multiple years cannot show grey bar
        if len(self.periods) > 1 and self.settings["date_format"] != "year":
            return

        xmin, xmax = self.ax.get_xlim()
        grey_range = []

        all_dates = []
        for period in sorted(self.periods.keys()):
            country, season = utils.period_to_country_season(period)
            if self.settings["samples_casedef"] != "":
                dates = samples.get_map_range(
                    country, season, "inet_incidence",
                    self.settings["samples_casedef"],
                    self.settings["samples_pdif"],
                    self.settings["samples_average"])
            else:
                dates = samples.get_range(
                    country, season, self.settings["samples_period"], None,
                    True)
            if self.settings["date_format"] != "year":
                dates = utils.dates2reference_season(dates, season)
            all_dates.append(dates)
        for min_date, max_date in sorted(
                all_dates, key=lambda dates: dates[0]):
            grey_range.append([xmin, utils.get_date(min_date).toordinal()])
            xmin = utils.get_date(max_date).toordinal()
        grey_range.append([xmin, xmax])
        for xmin, xmax in grey_range:
            ax = self.ax2 if self.ax2 is not None else self.ax
            ax.axvspan(
                xmin=xmin, xmax=xmax,
                facecolor=self.fig.settings["samples_color"],
                edgecolor=self.fig.settings["samples_color"],
                zorder=-20,
                label=(self.fig.settings["samples_label"]
                       if "samples_label" in self.fig.settings else
                       self.translate("<<label:low_influenza>>")))

    def get_xlimits(self):
        """Set the xlimits"""

        xlimits = []
        for plotname, options in self.datasets.items():
            if not options["xmaster"]:
                continue

            datadict = self.datadicts[plotname]
            dates = sorted([date for date, values in datadict.items()
                            if options["source_measure"] in values])
            values = [datadict[date][options["source_measure"]]
                      for date in dates]
            if options["min_value"] is not None:
                while len(values) > 0 \
                        and values[0] < options["min_value"]:
                    values.pop(0)
                    dates.pop(0)
                while len(values) > 0 \
                        and values[-1] < options["min_value"]:
                    values.pop(-1)
                    dates.pop(-1)

            if len(dates) == 0:
                continue
            xlimits.append((min(dates), max(dates)))
        return xlimits

    def get_data(self, options, xlimits, datadict):
        """Get the data"""
        dates = sorted([date for date, values in datadict.items()
                        if options["source_measure"] in values])
        values = [datadict[date][options["source_measure"]]
                  for date in dates]

        if (len([date for date in dates if date.isoweekday() == 7]) == 0 or
                sum(values) == 0):
            return None, None

        if not options["daily"]:
            dates, values = (
                list(a) for a in zip(
                    *[(date, value)
                      for date, value in zip(dates, values)
                      if date.isoweekday() == 7]))

        if options["min_value"] is not None:
            while len(values) > 0 and values[0] < options["min_value"]:
                values.pop(0)
                dates.pop(0)
            while len(values) > 0 \
                    and values[-1] < options["min_value"]:
                values.pop(-1)
                dates.pop(-1)

        # xmaster defines the x-range
        if len(xlimits) > 0:
            new_dates, new_values = [], []
            for date, value in zip(dates, values):
                for min_date, max_date in xlimits:
                    if date >= min_date and date <= max_date:
                        new_dates.append(date)
                        new_values.append(value)
                        break
            dates, values = new_dates, new_values

        if len(dates) == 0 or sum(values) == 0:
            return None, None

        # Connecting two datasets if less than one month apart
        label = options["label"]
        if label in self.last \
                and (dates[0] - self.last[label][0]).days <= 30 \
                and (dates[0] - self.last[label][0]).days > 0:
            dates.insert(0, self.last[label][0])
            values.insert(0, self.last[label][1])
        self.last[label] = (dates[-1], values[-1])

        return dates, values

    def get_start_end(self, dates, values, options):
        """Get the index within the limits"""

        start, end = 0, len(dates)
        if options["limits"] in ("dotted", "hide"):
            start_date, end_date = utils.get_limits(
                options["season"], options["country"], options["average"])
            start = None
            for index, date in enumerate(dates):
                if date >= start_date and start is None:
                    start = index
                if start is not None and date > end_date:
                    end = index
                    break

        if start is None or start == end:
            return None, None, None, None

        if self.settings["plot_start"] != "":
            index = len([
                date for date in dates
                if date < utils.get_date(self.settings["plot_start"],
                                         options["season"])])
            dates = dates[index:]
            values = values[index:]
            start = max(0, start - index)
            end -= index
        if self.settings["plot_end"] != "":
            index = len([
                date for date in dates
                if date <= utils.get_date(
                    self.settings["plot_end"], options["season"])])
            dates = dates[0:index]
            values = values[0:index]
            end = min(end, index)

        if "max_date" in options and options["max_date"] != "":
            index = len([
                date for date in dates
                if date <= utils.get_date(
                    options["max_date"], options["season"])])
            dates = dates[0:index]
            values = values[0:index]
            end = min(end, index)
        if "min_date" in options and options["min_date"] != "":
            index = len([
                date for date in dates
                if date < utils.get_date(
                    options["min_date"], options["season"])])
            dates = dates[index:]
            values = values[index:]
            start = max(0, start - index)
            end -= index

        return dates, values, start, end

    def plot_fill(self, ax, plotdates, values, options):
        """Fill a plot"""
        previous_points = len(self.fill["bottom"])
        date_dict = collections.defaultdict(int)
        for date, value in zip(plotdates, values):
            date_dict[date] = value
            if date not in self.fill["bottom"] and previous_points == 0:
                self.fill["bottom"][date] = 0
        for date in self.fill["bottom"].keys():
            self.fill["upper"][date] = (self.fill["bottom"][date] +
                                        date_dict[date])

        fill_dates, fill_values = matplotlib.mlab.poly_between(
            sorted(self.fill["upper"].keys()),
            [self.fill["bottom"][date]
             for date in sorted(self.fill["upper"].keys())],
            [self.fill["upper"][date]
             for date in sorted(self.fill["upper"].keys())])
        result = ax.fill(
            fill_dates,
            fill_values,
            color=options["color"],
            label=self.translate(options["label"]))
        self.fill["bottom"] = dict(self.fill["upper"])
        return result

    def plot_data(self, dates, values, start, end, options):
        """Plot the data"""
        # (too many arguments) pylint: disable=R0913

        ax = self.get_ax(options["ax_name"])

        ymax = (max(values) if options["limits"] == "dotted"
                else max(values[start:end]))
        ax.ymax = (max(ax.ymax, ymax) if hasattr(ax, "ymax") else
                   ymax)

        plotdates = (utils.dates2reference_season(dates, options["season"])
                     if self.settings["date_format"] != "year" else
                     list(dates))
        if self.settings["fill"]:
            result = self.plot_fill(ax, plotdates, values, options)

        elif options["bar"]:
            result = ax.bar(
                [date - datetime.timedelta(days=6)
                 for date in plotdates[start:end]],
                values[start:end],
                bottom=[self.fill["bottom"][date]
                        for date in plotdates[start:end]],
                width=6,
                linewidth=0,
                color=options["color"],
                edgecolor="white",
                zorder=options["zorder"],
                label=self.translate(options["label"]),
                leg_place=self.settings["leg_place"])
            if self.settings["bar_stack"]:
                for date, value in zip(plotdates[start:end],
                                       values[start:end]):
                    self.fill["bottom"][date] += value
        else:
            result = ax.plot(
                plotdates[start:end],
                values[start:end],
                color=options["color"],
                linestyle=options["linestyle"],
                linewidth=options["linewidth"],
                zorder=options["zorder"],
                markerfacecolor=(
                    "None" if options["linestyle"] == "" else
                    options["color"]),
                markeredgewidth=options["markersize"] / 10,
                markeredgecolor=options["color"],
                markersize=options["markersize"],
                marker="" if options["daily"] else options["marker"],
                label=self.translate(options["label"]),
                leg_place=self.settings["leg_place"])

            if options["daily"] and options["marker"] != "":
                markerdates, markervalues = zip(
                    *[(date, value) for date, value in zip(
                        dates[start:end], values[start:end])
                      if date.isoweekday() == 7])
                markerdates = utils.dates2reference_season(
                    markerdates, options["season"])
                result = ax.plot(
                    markerdates,
                    markervalues,
                    color=options["color"],
                    linestyle="",
                    linewidth=0,
                    zorder=options["zorder"],
                    markerfacecolor=(
                        "None" if options["linestyle"] == "" else
                        options["color"]),
                    markeredgewidth=options["markersize"] / 10,
                    markeredgecolor=options["color"],
                    markersize=options["markersize"],
                    marker=options["marker"]
                    )

        if options["limits"] == "dotted":
            ax.plot(plotdates[0:start],
                    values[0:start],
                    color=options["color"],
                    linestyle=":",
                    linewidth=options["linewidth"],
                    marker="",
                    zorder=options["zorder"])
            ax.plot(plotdates[end:],
                    values[end:],
                    color=options["color"],
                    linestyle=":",
                    linewidth=options["linewidth"],
                    marker="",
                    zorder=options["zorder"])
        return result

    def get_linreg_values(self, linreg_settings):
        """Get the linreg coefficients"""

        if len(linreg_settings["linreg_sources"]) != 2:
            return None

        if linreg_settings["linreg_gradient"] != 0:
            linreg_values = {
                "gradient": linreg_settings["linreg_gradient"],
                "intercept": linreg_settings["linreg_intercept"]}
        elif len(linreg_settings["linreg_seasons"]) > 0:
            linreg_dict = linreg.get_dict(linreg_settings)
            if linreg_dict is None:
                linreg_dict = linreg.datasets_to_dict(
                    self.datasets, linreg_settings)
            if linreg_dict is None:
                return None
            linreg_values, _delta = linreg.max_delta(linreg_dict)
        else:
            return None
        return linreg_values

    def get_linreg_axes(self, linreg_settings):
        """Get the axes to apply the linear regression to"""

        # no axes for all linreg sources
        if len(tools.SetList(linreg_settings["linreg_sources"]) -
               [options["source_measure"]
                for options in self.datasets.values()]) > 0:
            return None, None

        # get the ax names
        linreg_axes = []
        for source_measure in linreg_settings["linreg_sources"]:
            axes = tools.SetList([
                options["ax_name"]
                for options in self.datasets.values()
                if options["source_measure"] == source_measure])
            if len(axes) == 1:
                linreg_axes.append(self.get_ax(axes[0]))
            else:
                return None, None
        return linreg_axes[0], linreg_axes[1]

    def set_baseline(self):
        """Drawing a baseline"""

        datasets = utils.get_datasets_keys(
            self.all_datasets, self.settings["baseline"])
        baseline_labels = set([options["csvlabel"]
                               for options in datasets.values()])
        for label in baseline_labels:
            baseline_datasets = {
                key: options
                for key, options in datasets.items()
                if options["csvlabel"] == label}
            baseline_dict = baseline.get_dict(baseline_datasets)
            if (baseline_dict and
                    len(baseline_datasets) >= self.settings["baseline_min"]):
                options = next(six.itervalues(baseline_datasets))
                for period in sorted(self.periods.keys()):
                    season = utils.period_to_country_season(period)[1]
                    dates, values = baseline.get_baseline(
                        baseline_dict, season)
                    if self.settings["date_format"] != "year":
                        dates = utils.dates2reference_season(dates, season)
                    # self.get_ax("inet_incidence")
                    self.ax.plot(
                        dates, values,
                        label=(self.translate("<<label:baseline>>")
                               if len(baseline_labels) == 1 else
                               label),
                        color=options["color"],
                        linewidth=options["linewidth"],
                        linestyle=options["linestyle"],
                        leg_place=self.settings["leg_place"],
                        zorder=-10)

        if self.settings["baseline_eiss"] > 0:
            self.get_ax("eiss_incidence").axhline(
                y=self.settings["baseline_eiss"],
                label=self.translate("<<label:baseline>>"),
                color=self.fig.settings["baseline_color"],
                linewidth=self.fig.settings["baseline_width"],
                leg_place=self.settings["leg_place"],
                zorder=-1)

    def set_threshold(self):
        """Drawing a baseline"""

        datasets = utils.get_datasets_keys(
            self.all_datasets, self.settings["threshold"])
        baseline_labels = set([options["csvlabel"]
                               for options in datasets.values()])
        for label in baseline_labels:
            baseline_datasets = {
                key: options
                for key, options in datasets.items()
                if options["csvlabel"] == label}
            baseline_dict = baseline.get_dict(baseline_datasets)
            if (baseline_dict and
                    len(baseline_datasets) >= self.settings["baseline_min"]):
                options = next(six.itervalues(baseline_datasets))
                for period, active_options in tools.sort_iter(
                        self.periods):
                    season = utils.period_to_country_season(period)[1]
                    dates, values = baseline.get_threshold(
                        baseline_dict, season, active_options)
                    if self.settings["date_format"] != "year":
                        dates = utils.dates2reference_season(
                            dates, season)
                    self.get_ax("inet_incidence").plot(
                        dates,
                        values,
                        label=self.translate("<<label:threshold>>"),
                        color=options["color"],
                        linewidth=options["linewidth"],
                        linestyle=options["linestyle"],
                        leg_place=self.settings["leg_place"],
                        zorder=-10)

        if self.settings["baseline_eiss"] > 0:
            self.get_ax("eiss_incidence").axhline(
                y=self.settings["baseline_eiss"],
                label=self.translate("<<label:baseline>>"),
                color=self.fig.settings["baseline_color"],
                linewidth=self.fig.settings["baseline_width"],
                leg_place=self.settings["leg_place"],
                zorder=-1)

    def set_linreg(self):
        """Scale the axes based on the linreg"""

        linreg_values = self.get_linreg_values(self.settings)
        if linreg_values is None:
            return

        ax1, ax2 = self.get_linreg_axes(self.settings)
        if ax1:
            min1, max1 = ax1.get_ylim()
            min2 = ((min1 - linreg_values["intercept"]) /
                    linreg_values["gradient"])
            max2 = ((max1 - linreg_values["intercept"]) /
                    linreg_values["gradient"])
            if hasattr(ax2, "ymax") and max2 < ax2.ymax:
                max2 = ax2.ymax
                min1 = (min2 * linreg_values["gradient"] +
                        linreg_values["intercept"])
                max1 = (max2 * linreg_values["gradient"] +
                        linreg_values["intercept"])
                ax1.set_ylim(min1, max1)
                ax2.set_ylim(min2, max2)
            else:
                ax2.set_ylim(min2, max2)
        elif self.settings["linreg_ymax"] != 0:
            for options in self.datasets.values():
                if (options["source_measure"] ==
                        self.settings["linreg_sources"][1]):
                    ax = self.get_ax(options["ax_name"])
                    ymax = ((self.settings["linreg_ymax"] -
                             linreg_values["intercept"]) /
                            linreg_values["gradient"])
                elif (options["source_measure"] ==
                      self.settings["linreg_sources"][0]):
                    ax = self.get_ax(options["ax_name"])
                    ymax = (self.settings["linreg_ymax"] *
                            linreg_values["gradient"] +
                            linreg_values["intercept"])
                else:
                    continue
                ax.set_ylim(ymax=ymax)

        # show the max R2 (with a possible shift)
        if self.settings["linreg_r2"]:
            linreg_settings = dict(self.settings)
            linreg_settings["linreg_intercept0"] = False
            linreg_settings["linreg_days"] = [-14, 15]
            linreg_values = self.get_linreg_values(linreg_settings)
            ax1, ax2 = self.get_linreg_axes(linreg_settings)
            ax1.text(
                0.99,
                0.99,
                "$R^2 = {0:.2f}$".format(linreg_values["r2"]),
                va="top", ha="right", fontsize=8, transform=ax1.transAxes)

    def set_ylim(self):
        """Set the y-ax limits, based on the linear regression"""

        Base.set_ylim(self)

        self.set_linreg()
        self.set_baseline()
        self.set_threshold()

#         # Alternative MaxNLocator
#         max = ax.get_ylim()[1]
#         distance = (max // (yticks + 1) // 100 + 1) * 100
#         ax.set_yticks([distance * i for i in range(6)
#                 if i * distance < max])

    def set_xlim(self):
        """Set the x-ax limits"""

        interval = self.ax.get_xaxis().get_data_interval()
        if "get_bounds" in dir(interval):
            xmin, xmax = interval.get_bounds()
        else:
            xmin, xmax = interval

        # this happens when no date points are plotted
        if xmin < 10 or xmax < 10:
            return

        xmin = datetime.datetime.fromordinal(int(xmin))
        xmax = datetime.datetime.fromordinal(int(xmax))

        xmin = xmin.replace(day=1)
        if xmax.day != 1:
            if xmax.month == 12:
                xmax = xmax.replace(day=1, month=1, year=xmax.year + 1)
            else:
                xmax = xmax.replace(day=1, month=xmax.month + 1)

        if self.settings["plot_start"] != "":
            xmin = utils.get_date(self.settings["plot_start"])
        if self.settings["plot_end"] != "":
            xmax = utils.get_date(self.settings["plot_end"])
        self.ax.set_xlim(xmin, xmax)

    def get_ylabel(self, ax_name):
        """Set the ylabel"""

        source, measure = ax_name.split("_", 1)

        if config.SEP["measure_label"] in measure:
            measure, label = measure.split(config.SEP["measure_label"])
        else:
            label = None

        if measure in ("incidence", "scaled"):
            casedef_ids = tools.SetList([
                options["casedef_id"]
                for options in self.datasets.values()
                if (options["source"] == source and
                    options["measure"] == measure and
                    "casedef_id" in options)])

            if len(casedef_ids) == 1 and "ili" in casedef_ids[0]:
                measure = "ili"
            elif len(casedef_ids) == 1 and "ari" in casedef_ids[0]:
                measure = "ari"

        ylabel = "<<measure:{0}>> <<measure:{0}_unit>>".format(measure)
        if label:
            ylabel = "{0}: {1}".format(label, ylabel)
#                 title = self.fig.settings["title"]
#                 if measure_label in title:
#                     if unit_label not in title:
#                         self.fig.settings["title"] = title.replace(
#                                 measure_label,
#                                 measure_label + " " + unit_label)
#                     ylabel = label
        if (self.ax2 is not None and
                "source" not in self.fig.settings["title_labels"]):
            ylabel = "<<source:{0}>>: {1}".format(source, ylabel)

        return ylabel

    def set_labels(self):
        """Set the labels of the x-ax, y-ax, title...."""
        date_format = self.settings["date_format"]
        self.ax.set_xstyle(date_format)
        self.settings["xlabel_id"] = date_format
        Base.set_labels(self)
