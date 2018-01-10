#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Fit a model to the data (including weather)"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import numpy
import sys
import os
import hashlib
import scipy.integrate
import datetime
import collections
import difflib
import io
import six
import configobj

from . import utils, baseline, tools
from .data import Data
from .ini import Ini

BASELINE = {}
DSOLVE = {}
PVALS = {}
SOLVE = {}
ERROR_VALUES = {}
DATA = {}
CLIMATE = {}

CUR_TOL = 30
TOL = 15
MIN_VAL = -15
MAX_VAL = 15
MODEL_KEYS = "reload".split(" ")
PLOT_KEYS = ("color band_color band_label band_width marker question_title" +
             " linestyle linewidth citylabel" +
             " label zorder markersize min_value ax_name xmaster bar limits" +
             " casedef_id csvlabel reload subset_label ili" +
             " source measure src country season" +
             " city_cutter cutter age_cutter" +
             " city_answer answer age_answer" +
             " min_surveys max_freq expand").split(" ")

# min_date: first day (based on baseline)
# model_start: first day of model
# model0: model_start - min_date


def clear_cache():
    """Clear cache values"""
    global DSOLVE, SOLVE, ERROR_VALUES, PVALS  # (global) pylint: disable=W0603
    DSOLVE = {}
    SOLVE = {}
    ERROR_VALUES = {}
    PVALS = {}


class SimulDict(object):
    """Simulation functions"""

    def __init__(self, model, datasets, cachedir):
        self.model = model
        self.scaled = None
        self.paramdict = None
        self.cachedir = cachedir

        self.datasets = utils.get_datasets_keys(datasets, model["datasets"])
        self.baseline = utils.get_datasets_keys(datasets, model["baseline"])
        if len(self.datasets) == 0:
            return

        self.model["seasons"] = [options["season"]
                                 for options in self.datasets.values()]
        self.model["country"] = next(six.itervalues(self.datasets))["country"]
        self.model["srcme"] = next(six.itervalues(self.datasets))[
            "source_measure"]
        self.set_model0()

    def set_model0(self):
        """Set the model start and end date"""
        min_date = tools.get_date(
            "{0}/{1}".format(2002, self.model["min_date"]))
        max_date = tools.get_date(
            "{0}/{1}".format(2003, self.model["max_date"]))
        model_start = tools.get_date(
            "{0}/{1}".format(2002, self.model["model_start"]))
        self.model["days"] = (max_date - min_date).days + 1
        self.model["model0"] = (model_start - min_date).days

# Bounds/symbols functions

    def extract(self, paramdict, symbols):
        """Extract values from other paramdict"""
        for symbol in symbols:
            values = [paramdict[season][symbol]
                      for season in self.model["seasons"]]
            self.model["bounds"][symbol] = [0.9 * min(values),
                                            1.1 * max(values)]
            self.model["defaults"][symbol] = numpy.average(values)
            for season in self.model["seasons"]:
                if (symbol in self.model["symbols"]["season"] and
                        season in paramdict):
                    self.model["defaults"][symbol + "_" + season] = \
                        paramdict[season][symbol]

    def get_cachedir(self):
        """The dir to save the fitted solution"""
        inifile = io.BytesIO()
        ini = configobj.ConfigObj()
        ini["model"] = {}
        model = tools.deepcopy(self.model)
        for key in model.keys():
            if key in MODEL_KEYS:
                del model[key]
        tools.add_section(ini["model"], model)

        ini["datasets"] = {}
        datasets = tools.deepcopy(self.datasets)
        for options in datasets.values():
            for key in options.keys():
                if key in PLOT_KEYS:
                    del options[key]
        tools.add_section(ini["datasets"], datasets)

        # baseline already included in params
        # ini["baseline"] = {}
        # baseline = configobj.copy(self.baseline)
        # for options in baseline.values():
        #    for key in options.keys():
        #        if key in PLOT_KEYS:
        #            del options[key]
        # tools.add_section(ini["baseline"], baseline)
        ini.write(inifile)
        inistring = inifile.getvalue()
        inistring = tools.ini_align(inistring)

        # (Module has no member) pylint: disable=E1101
        md5 = hashlib.md5(inistring.encode("utf8")).hexdigest()
        # (Module has no member) pylint: enable=E1101
        return os.path.join(self.cachedir, md5), inistring

    def save(self):
        """Save the fitted scaled"""
        cachedir, inistring = self.get_cachedir()
        tools.create_dir(cachedir, remove=True)

        numpy.save(os.path.join(cachedir, "scaled.npy"), self.scaled)
        with io.open(os.path.join(cachedir, "simul.ini"), "w") as fobj:
            fobj.write(inistring)
        tools.touch(os.path.join(cachedir, "stamp"))

    def load(self):
        """Load the fitted scaled"""
        if self.model["reload"]:
            return False
        cachedir, inistring = self.get_cachedir()
        if not os.path.exists(cachedir):
            return False

            # (unreachable) pylint: disable=W0101
            min_difs = None
            best_match = None
            for md5 in os.listdir(self.cachedir):
                fname = os.path.join(self.cachedir, md5, "simul.ini")
                if not os.path.exists(fname):
                    continue
                cached_inistring = open(fname, "r").read()
                difs = list(difflib.unified_diff(
                    inistring.split("\n"), cached_inistring.split("\n"), n=0))
                if min_difs is None or len(difs) < len(min_difs):
                    best_match = cached_inistring
                    min_difs = difs
            sys.exit("{0}\n===\n{1}\n===\n{2}".format(
                inistring, best_match, "\n".join(min_difs)))
        else:
            tools.touch(os.path.join(cachedir, "stamp"))
            self.set_scaled(numpy.load(os.path.join(cachedir, "scaled.npy")))
            return True

    def set_baseline(self):
        """Get the baseline params"""
        baseline_dict = baseline.get_dict(self.baseline)
        self.model["min_date"] = baseline_dict["min_date"]
        self.model["max_date"] = baseline_dict["max_date"]
        self.set_model0()
        for index, value in enumerate(baseline_dict["params"]):
            symbol = "baseline_{0}".format(index)
            self.model["defaults"][symbol] = value
            self.model["symbols"]["constant"].append(symbol)

    def set_default(self):
        """Set the default scaled"""
        scaled = []
        for symbol in self.model["symbols"]["var"]:
            scaled.append(self.get_scaled(self.model["defaults"][symbol],
                                          symbol))
        for season in self.model["seasons"]:
            for symbol in self.model["symbols"]["season"]:
                value = (self.model["defaults"][symbol + "_" + season] if
                         symbol + "_" + season in self.model["defaults"] else
                         self.model["defaults"][symbol])
                scaled.append(self.get_scaled(value, symbol))
        self.set_scaled(scaled)

    def check_bounds(self):
        """Check the bounds"""
        for _symbol, values in self.model["bounds"].items():
            if values[0] > values[1]:
                values[0], values[1] = values[1], values[0]

# scaled function

    def get_value(self, scaled, symbol):
        """ (-inf, inf) -> (min, max) """
        min_val, max_val = self.model["bounds"][symbol]
        if scaled == MIN_VAL:
            return min_val
        elif scaled == MAX_VAL:
            return max_val
        else:
            return min_val + (max_val - min_val) * tools.ilogit(scaled)

    def get_scaled(self, value, symbol):
        """ (min, max) -> (-inf, inf) """
        min_val, max_val = self.model["bounds"][symbol]
        if max_val == min_val:
            return 0
        elif value == min_val:
            return MIN_VAL
        elif value == max_val:
            return MAX_VAL
        elif value > min_val and value < max_val:
            return tools.logit((value - min_val) / (max_val - min_val))
        else:
            sys.exit("{symbol}={value} not in ({min_val}, {max_val})".format(
                symbol=symbol, value=value, min_val=min_val, max_val=max_val))

    def scaled_to_params(self, scaled_season, season):
        """Return params for a season"""
        params = {}
        for symbol in self.model["symbols"]["constant"]:
            params[symbol] = self.model["defaults"][symbol]
        for symbol, value in zip(self.model["symbols"]["var"] +
                                 self.model["symbols"]["season"],
                                 scaled_season):
            params[symbol] = self.get_value(value, symbol)
        if "s0" not in params:
            params["s0"] = params["r_eff"] * params["tau"] / params["beta"]
        elif "beta" not in params:
            params["beta"] = params["r_eff"] * params["tau"] / params["s0"]
        elif "r_eff" not in params:
            params["r_eff"] = params["s0"] * params["beta"] / params["tau"]

        for key in self.model.scalars:
            if key in ["seasons", "datasets", "baseline"]:
                continue
            params[key] = self.model[key]
        params["season"] = season
        params["min_date_"] = utils.get_date(self.model["min_date"], season)
        return params

    def set_scaled(self, scaled):
        """Set the scaled"""
        self.scaled = numpy.array(scaled)
        self.paramdict = {}
        pmax = []
        for season, scaled_season in self.get_scaled_season(self.scaled):
            params = self.scaled_to_params(scaled_season, season)
            if "clim_intercept" in params:
                pmax.append(max(Simul(params).get_pvals().values()))
            self.paramdict[season] = params
        if len(pmax) > 0:
            for params in self.paramdict.values():
                params["s0"] *= max(pmax)
                params["beta"] /= max(pmax)
                params["clim_intercept"] -= numpy.log(max(pmax))

    def get_scaled_season(self, scaled):
        """Return the scaled params for just one season"""
        len_var = len(self.model["symbols"]["var"])
        len_season = len(self.model["symbols"]["season"])
        return [[season, scaled[list(range(len_var)) +
                                list(range(
                                    len_var + season_no * len_season,
                                    len_var + (season_no + 1) * len_season))]]
                for season_no, season in enumerate(self.model["seasons"])]

# misc functions

    def get_rss(self):
        """Return rss (residual sum squares)"""
        rss = 0
        n = 0
        for _season, simul in self.items():
            data = simul.get_data(self.datasets)
            model = simul.solve()
            for day in data.keys():
                rss += (data[day] - model[day]) ** 2
                n += 1
        return rss, n

    def get_aic(self, corrected=True):
        """Return akaike info criterium"""
        # (invalid name) pylint: disable=C0103
        rss, n = self.get_rss()
        p = len(self.scaled)
        return tools.get_aic(rss, n, p, corrected)

    def data_r2(self, ax=None, scaled=None):
        """Return the full correlation between src and model"""
        model_data = []
        real_data = []

        def get_simuls():
            """Return simul objects, from self or based on scale"""
            if scaled is None:
                for _season, simul in self.items():
                    yield simul
            else:
                for season, scaled_season in self.get_scaled_season(scaled):
                    yield Simul(self.scaled_to_params(scaled_season, season))

        for simul in get_simuls():
            solution = simul.solve()
            data = simul.get_data(self.datasets)
            model_data.extend([solution[day]
                               for day in sorted(data.keys())])
            real_data.extend([data[key] for key in sorted(data.keys())])

        r2 = tools.linreg_wiki(model_data, real_data)[0]

        if ax is not None:
            ax.text(0.99,
                    0.97,
                    "$R^2={0:.2f}$".format(r2),
                    transform=ax.transAxes,
                    color="black",
                    fontsize=7,
                    va="top",
                    ha="right")
        return r2

    def error_value_dif(self, scaled_season, season):
        """Return the sum-squared of one season"""

        key = (tuple(scaled_season) +
               (self.model["country"], season,
                self.model["clim_var"], self.model["clim_season"]))
        if key not in ERROR_VALUES:
            simul = Simul(self.scaled_to_params(scaled_season, season))
            solution = simul.solve()
            data = simul.get_data(self.datasets)
            error = sum([(solution[day] - value) ** 2
                         for day, value in data.items()])

            # Big error penalty if peakday of simulation and data
            # differs by more than 30 days
            tol = (CUR_TOL if self.model["clim_season"] == "current" else
                   TOL)
            max_day = max(data.keys(), key=(lambda key: data[key]))
            peak_dif = abs(solution.argmax() - max_day)
            peak_dif = max(0, peak_dif - tol)
            error *= (1 + peak_dif)

            ERROR_VALUES[key] = error

        return ERROR_VALUES[key].copy()

    def errors(self, scaled):
        """Return the errors (for least square algo)"""
        errors = []
        for season, scaled_season in self.get_scaled_season(scaled):
            simul = Simul(self.scaled_to_params(scaled_season, season))
            solution = simul.solve()
            data = simul.get_data(self.datasets)
            errors += [(solution[day] - value)
                       for day, value in data.items()]
        return errors

    def error_value(self, scaled):
        """The error of the season"""
        return sum([
            self.error_value_dif(scaled_season, season)
            for season, scaled_season in self.get_scaled_season(scaled)])

    def items(self):
        """Return season/simul pairs"""
        for season, params in tools.sort_iter(self.paramdict):
            yield season, Simul(params)


class Simul(object):
    """Class which simulates one season"""

    def __init__(self, params):
        self.params = params

    def get_dates(self, days=None):
        """Return all the dates"""
        if days is None:
            days = range(self.params["days"])
        return [self.params["min_date_"] + datetime.timedelta(days=int(day))
                for day in days]

    def get_key(self, function):
        """Return the key for a function"""

        if function == "baseline":
            if "baseline_0" not in self.params:
                key = ()
            else:
                key = tuple(
                    params
                    for key, params in tools.sort_iter(self.params)
                    if key.startswith("baseline_"))

        elif function == "pvals":
            if self.params["clim_var"] == "":
                key = ()
            else:
                key = (self.get_key("climate") +
                       (self.params["clim_intercept"],
                        self.params["clim_gradient"],
                        self.params["clim_log"]))

        elif function == "dsolve":
            key = (self.params["s0"], self.params["beta"],
                   self.params["migration"])

        elif function == "data":
            key = (self.params["country"], self.params["season"],
                   self.params["min_date"])

        elif function == "climate":
            key = (self.params["country"],
                   self.params["clim_var"],
                   (self.params["season"]
                    if self.params["clim_season"] == "current" else
                    self.params["clim_season"]),
                   self.params["min_date"],
                   self.params["clim_avg"])

        elif function == "solve":
            key = (self.get_key("dsolve") + self.get_key("pvals") +
                   self.get_key("baseline"))

        else:
            sys.exit("Unknown function: {0}".format(function))

        return key

    def get_baseline(self):
        """Number of baseline cases"""

        key = self.get_key("baseline")
        if key == ():
            return None

        if key not in BASELINE:
            baseline_dict = {"params": list(key),
                             "min_date": self.params["min_date"],
                             "max_date": self.params["max_date"]}
            values = baseline.get_baseline(baseline_dict, "2002/03")[1]
            BASELINE[key] = numpy.array(values)
        return BASELINE[key].copy()

    def get_pvals(self):
        """Return pvals"""

        key = self.get_key("pvals")
        if key == ():
            return None
        if key not in PVALS:
            climates = self.get_climate()
            pvals = climates_to_pvals(
                climates,
                self.params["clim_gradient"],
                self.params["clim_intercept"],
                self.params["clim_log"])
            PVALS[key] = pvals
        return PVALS[key].copy()

    def dval(self, var, _time):
        """Main diff eqn"""
        try:
            # if "vacrate" in self.params and self.params["vacrate"] > 0 \
            #         and t >= self.params["tvac"] \
            #         and t < self.params["tvac"] + clim.vactemp:
            #     vacrate = self.params["vacrate"]
            # else:
            vacrate = 0
            sus, inf = var
            force = self.params["beta"] * inf + self.params["migration"]
            return [-(force + vacrate) * sus,
                    force * sus - self.params["tau"] * inf]
        except KeyboardInterrupt:
            sys.exit("Keyboard interrupt")

    def dsolve(self):
        """Solve diff eqn"""
        key = self.get_key("dsolve")
        if key not in DSOLVE:
            # (module has not member) pylint: disable=E1101
            solution = scipy.integrate.odeint(
                self.dval, [self.params["s0"], 0], range(365))
            DSOLVE[key] = solution
        return DSOLVE[key].copy()

    def solve(self):
        """Solve main diff eqn from 0 - end"""

        key = self.get_key("solve")
        if key not in SOLVE:
            # incidence = tau * prev
            # tau_week = 7 * tau
            onsets = numpy.concatenate((
                numpy.zeros(self.params["model0"]),
                100000 * self.dsolve()[
                    0:self.params["days"] - self.params["model0"], 1] *
                self.params["tau"] * 7))

            pvals = self.get_pvals()
            if pvals is not None:
                onsets *= numpy.array([pvals[day]
                                       for day in range(len(onsets))])
            SOLVE[key] = self.get_baseline() + onsets

        return SOLVE[key].copy()

    def get_peak(self):
        """Peak ILI incidence"""
        solution = self.solve()
        return solution.argmax(), solution.max()

    def get_data(self, datasets):
        """Return inet/eiss data for certain season"""

        key = self.get_key("data")
        if key not in DATA:
            data = {}
            options = [options for options in datasets.values()
                       if options["season"] == self.params["season"]][0]
            min_date, max_date = utils.get_limits(
                options["season"], options["country"], options["average"])
            for date, daydata in Data(options).get_datadict().items():
                if (date.weekday() != 6 or
                        options["source_measure"] not in daydata):
                    continue
                if (options["source"] == "inet" and
                        (date < min_date or date > max_date)):
                    continue
                data[(date - self.params["min_date_"]).days] = daydata[
                    options["source_measure"]]
            DATA[key] = data
        return DATA[key].copy()

    def get_climate_avg(self):
        """Get average climate"""
        climate = {}
        climate_list = collections.defaultdict(list)

        clim_season = self.params["clim_season"]
        season = self.params["season"]
        for year in range(*[int(year)
                            for year in
                            self.params["clim_season"].split(":")]):
            self.params["season"] = utils.year_to_season(year)
            self.params["clim_season"] = "current"
            for day, value in self.get_climate().items():
                climate_list[day].append(value)
        for day, values in climate_list.items():
            climate[day] = numpy.average(values)
        self.params["clim_season"] = clim_season
        self.params["season"] = season
        return climate

    def get_climate(self, clim_var=None, clim_season=None, clim_avg=None):
        """The climate at the peak"""
        if clim_var is not None:
            orig = {ckey: self.params[ckey]
                    for ckey in ["clim_var", "clim_season", "clim_avg"]
                    if ckey in self.params}
            self.params["clim_var"] = clim_var
            self.params["clim_season"] = clim_season
            self.params["clim_avg"] = clim_avg
        key = self.get_key("climate")
        if key not in CLIMATE and ":" in self.params["clim_season"]:
            CLIMATE[key] = self.get_climate_avg()
        elif key not in CLIMATE:
            climate = {}
            inistring = tools.Format("""
                [datasets]
                    [[climate]]
                        source_measure = climate_{clim_var}
                        country = {country}
                        season = {season}
                        average = {clim_avg}
                """).format(extra=self.params)
            ini = Ini(inistring)
            options = ini.datasets["climate"]
            datadict = Data(options).get_datadict()
            for date, daydata in datadict.items():
                if ("climate_{0}".format(self.params["clim_var"])
                        not in daydata):
                    continue
                day = (
                    date -
                    utils.get_date(self.params["min_date"],
                                   self.params["season"])).days
                if day < 0:
                    continue
                climate[day] = daydata["climate_{0}".format(
                    self.params["clim_var"])]
            CLIMATE[key] = climate
        if clim_var is not None:
            for ckey in ["clim_var", "clim_season", "clim_avg"]:
                if ckey in orig:
                    self.params[ckey] = orig[ckey]
                else:
                    del self.params[ckey]
        return CLIMATE[key].copy()


def climates_to_pvals(climates, gradient, intercept, clim_log):
    """Convert climate to pvals"""
#     if isinstance(climates, list):
#         climates = numpy.array(climates)

    if isinstance(climates, dict):
        clims = numpy.array(list(climates.values()))
    elif isinstance(climates, list):
        clims = numpy.array(climates)
    elif isinstance(climates, numpy.ndarray):
        clims = climates
    else:
        sys.exit("Unknown type for climates: {0}".format(climates))

    pvals = gradient * clims + intercept
    if clim_log:
        pvals = numpy.exp(pvals)

    if isinstance(climates, dict):
        return dict(zip(climates.keys(), pvals))
    elif isinstance(climates, list):
        return list(pvals)
    else:
        return pvals


def pvals_to_climates(pvals, gradient, intercept, clim_log):
    """Calculate climate from the pval"""
    if isinstance(pvals, list):
        pvals = numpy.array(pvals)
    if clim_log:
        return (numpy.log(pvals) - intercept) / gradient
    else:
        return (pvals - intercept) / gradient


def climate_regression(climates, pvals, clim_log):
    """Linear regression between climate and the values"""

    if clim_log:
        r2, gradient, _sd_gradient, intercept, _sd_intercept = \
            tools.linreg_wiki(climates,
                              [numpy.log(pval) for pval in pvals])
    else:
        r2, gradient, _sd_gradient, intercept, _sd_intercept = \
            tools.linreg_wiki(climates, pvals)
    return {"r2": r2, "gradient": gradient, "intercept": intercept}


# def get_vac(country):
#     """Return the day and rate of vaccination"""
#
#     if country in clim.vacdates:
#         coverage, date = clim.vacdates[country]
#         day = date_to_season_day(date)[1]
#         vacrate = - numpy.log(1 - coverage)
#         return day, vacrate
#     else:
#         return None, None
#
#
# def load_fname(fname):
#     """Load data from a fname"""
#     fullname = os.path.join(CACHEDIR, fname)
#     if not os.path.exists(fullname):
#         return {}
#     else:
#         with io.open(fullname, "r", encoding="utf8") as fobj:
#             return pickle.load(fobj)
#
#
# def load():
#     """Load cache data"""
#     CLIMATE.update(load_fname("inet_climate.pck"))
#     DATA.update(load_fname("inet_data.pck"))
#
#
# def save():
#     """Save cached data"""
#     with io.open(os.path.join(CACHEDIR, "inet_climate.pck"),
#                      "w", encoding="utf8") as fobj:
#         pickle.dump(CLIMATE, fobj)
#     with io.open(os.path.join(CACHEDIR, "inet_data.pck"),
#                      "w", encoding="utf8") as fobj:
#         pickle.dump(DATA, fobj)
