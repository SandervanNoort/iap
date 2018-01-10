#!/usr/bin/env python

"""Fstat"""

from __future__ import division

import os
import collections
import numpy
import csv

import clim
from . import tools


class Fstat:
    """Class to do some basic (f) statistics"""

    def __init__(self, simul, csvdir):
        self.rss = collections.defaultdict(dict)
        self.rss_lin = collections.defaultdict(dict)
        self.dots = collections.defaultdict(dict)
        self.sst = collections.defaultdict(dict)
        self.gradients = collections.defaultdict(dict)
        self.intercepts = collections.defaultdict(dict)
        self.no_params = {"climate": 7 + 7 + 2,
                "constant": 7 + 7,
                "season": 7 + 7 + 7}

        self.simul = simul
        self.csvdir = csvdir
        self.skip = True

    def fill(self, together, separate, climate):
        """Fill the dicts"""

        for name, country_paramdict in [("constant", together),
                ("season", separate),
                ("climate", climate)]:
            for country in clim.countries:
                paramdict = country_paramdict[country]
                data = []
                model = []
                for season, params in paramdict.items():
                    days = self.simul.inet.compare_days(country, clim.src,
                            season)
                    model.extend(self.simul.solve(params)[days - clim.model0])
                    data.extend([self.simul.inet.data[country][
                            clim.src][season][day]
                            for day in days])
                model = numpy.array(model)
                data = numpy.array(data)
                _r2, gradient, _sd_gradient, intercept, _sd_intercept \
                        = tools.linreg_wiki(model, data)
                self.rss[country][name] = sum((data - model) ** 2)
                self.rss_lin[country][name] \
                        = sum((data - (gradient * model + intercept)) ** 2)
                self.sst[country][name] = sum((data - data.mean()) ** 2)
                self.gradients[country][name] = gradient
                self.intercepts[country][name] = intercept
                self.dots[country][name] = len(model)

    def write(self):
        """Write the results to csv files"""
        for country in clim.countries:
            fname = os.path.join(self.csvdir, 
                        "clim_%s.csv" % country)
            if os.path.exists(fname) and self.skip:
                continue
            fobj = open(fname, "w")
            writer = csv.writer(fobj)
            writer.writerow(["Model", "Params", "RSS", "R2",
                    "Grad", "Interc", "RSS (lin)", "R2 (lin)",
                    "F (Cons)", "F (Seas)", "F (Clim)"])
            for model in ["constant", "season", "climate"]:
                line = []
                line.append(model.capitalize())
                line.append(self.no_params[model])
                line.append(self.rss[country][model])
                line.append(1 - self.rss[country][model]
                        / self.sst[country][model])
                line.append(self.gradients[country][model])
                line.append(self.intercepts[country][model])
                line.append(self.rss_lin[country][model])
                line.append(1 - self.rss_lin[country][model]
                        / self.sst[country][model])
                for model2 in ["constant", "season", "climate"]:
                    if self.no_params[model] <= self.no_params[model2]:
                        line.append("-")
                    else:
                        rss1 = self.rss[country][model2]
                        rss2 = self.rss[country][model]
                        pp1 = self.no_params[model2]
                        pp2 = self.no_params[model]
                        n = self.dots[country][model2]
                        line.append(((rss1 - rss2) / (pp2 - pp1))
                                / (rss2 / (n - pp2)))
                writer.writerow(line)
            fobj.close()

    def csv_to_tex(self):
        """Convert csv files to tex"""

        for country in clim.countries:
            fobj = open(os.path.join(self.csvdir, "clim_%s.csv" % country),
                    "r")
            tex = open(os.path.join(self.csvdir, "clim_%s.tex" % country), "w")

            reader = csv.reader(fobj)
            for line in reader:
                vals = []
                for val in line:
                    try:
                        val = int(val)
                    except:
                        try:
                            val = float(val)
                            if val > 10 and val < 1000:
                                val = "%s" % int(val)
                            else:
                                val = "%.2g" % float(val)
                        except:
                            pass
                    vals.append(str(val))
                tex.write(" & ".join(vals) + "\\\\" + "\n")
            tex.close()
            fobj.close()
