# #!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Maps"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import collections
import datetime
import os
import PIL
import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
import locale
import sys  # pylint: disable=W0611
import io

from . import utils, config, tools
from .data import Data


class FigMap(object):
    """Class to make maps"""

    def __init__(self, settings):
        self.settings = settings["map"]
        self.translate = lambda text: utils.translate(
            text, settings["map"]["lang"])

        if self.settings["lang"] == "pt":
            locale.setlocale(locale.LC_ALL, str("pt_PT.UTF-8"))
        elif self.settings["lang"] == "nl":
            locale.setlocale(locale.LC_ALL, str("nl_NL.UTF-8"))
        elif self.settings["lang"] == "en":
            locale.setlocale(locale.LC_ALL, str("C"))

        basename = os.path.join(config.CONFIG["dir"]["data"], "maps",
                                self.settings["mapname"])
        self.imgname = os.path.join(basename, "map.png")

        self.settings["fontfile"] = os.path.join(
            config.CONFIG["dir"]["data"],
            "{0}.ttf".format(self.settings["fontfamily"]))
        if not os.path.exists(self.settings["fontfile"]):
            self.settings["fontfile"] = os.path.join(
                config.CONFIG["dir"]["data"], "Arial.ttf")
        self.settings["fontfile_italic"] = os.path.join(
            config.CONFIG["dir"]["data"], "Arial_Italic.ttf")

        for key, value in self.settings.items():
            if key.endswith("_color"):
                self.settings[key] = tuple(value)

        self.img = PIL.Image.open(self.imgname)
        pixdata = self.img.load()
        self.regions = collections.defaultdict(list)
        for xval in range(self.img.size[0]):
            for yval in range(self.img.size[1]):
                color = pixdata[xval, yval]
                self.regions[pixdata[xval, yval]].append([xval, yval])

        regionname = os.path.join(basename, "regions.csv")
        if os.path.exists(regionname):
            with io.open(regionname, "r") as csvobj:
                reader = tools.ureader(csvobj)
                for line in reader:
                    color = tuple(int(col) for col in line[0].split("_"))
                    if color in self.regions:
                        self.regions[line[1]] = self.regions[color]
        self.draw = PIL.ImageDraw.Draw(self.img)
        self.maps = {}

    def add_logo(self):
        """Add logo in lower left corner"""

        logo = PIL.Image.open(
            os.path.join(config.CONFIG["dir"]["data"], "logo.png"))
        self.img.paste(
            logo,
            (self.settings["margin"]["logo"],
             (self.img.size[1] - logo.size[1] -
              self.settings["margin"]["logo"]),
             logo.size[0] + self.settings["margin"]["logo"],
             self.img.size[1] - self.settings["margin"]["logo"]))
        self.draw.text(
            (logo.size[0] + self.settings["margin"]["date"],
             (self.img.size[1] - self.settings["font"]["logo"] -
              self.settings["margin"]["logo"])),
            self.translate("<<url>>"),
            (0, 0, 0),
            font=PIL.ImageFont.truetype(
                self.settings["fontfile_italic"],
                size=self.settings["font"]["logo"]))

    def make_black_regions(self, blackdir):
        """Create images with black regions"""

        tools.create_dir(blackdir, remove=True)
        with io.open(os.path.join(blackdir, "regions.csv"), "w") as csvobj:
            writer = tools.uwriter(csvobj)
            for color, pixels in self.regions.items():
                if not isinstance(color, tuple):
                    continue

                # exclude small regions
                if len(pixels) < self.settings["min_pixels"]:
                    continue

                # exclude black/white
                if (sum(color[0:3]) < self.settings["max_black"] or
                        sum(color[0:3]) > self.settings["min_white"]):
                    continue

                img = PIL.Image.open(self.imgname)
                pixdata = img.load()
                for xval, yval in pixels:
                    pixdata[xval, yval] = (0, 0, 0, 255)
                color_string = "_".join(["{0}".format(col) for col in color])
                imgname = os.path.join(blackdir,
                                       "{0}.png".format(color_string))
                img.save(imgname)
                writer.writerow([color_string, ""])

    def get_color(self, incidence):
        """The color of the activity"""

        if incidence >= self.settings["min_incidence"]:
            incidence = min(self.settings["max_incidence"], incidence)
            relative = ((incidence - self.settings["min_incidence"]) /
                        (self.settings["max_incidence"] -
                         self.settings["min_incidence"]))
            return tuple(min_color + int(relative * (max_color - min_color))
                         for min_color, max_color in zip(
                             self.settings["min_color"],
                             self.settings["max_color"]))
        else:
            return self.settings["none_color"]

    def add_bar(self):
        """Add a legend bar"""

        ymin = self.settings["legend"]["ymin"]
        ymax = int(ymin + 0.8 * self.settings["legend"]["height"])
        ynone = ymin + self.settings["legend"]["height"]
        xmin = self.settings["margin"]["date"]
        xmax = xmin + self.settings["legend"]["width"]
        margin = self.settings["margin"]["legend"]

        pixdata = self.img.load()
        for xval in range(xmin, xmax):
            for yval in range(ymin, ymax):
                relative = 1 - (yval - ymin) / (ymax - ymin)
                pixdata[xval, yval] = tuple(
                    min_color + int(relative * (max_color - min_color))
                    for min_color, max_color in zip(
                        self.settings["min_color"],
                        self.settings["max_color"]))
        for xval in range(xmin, xmax):
            for yval in range(ymax, ynone):
                pixdata[xval, yval] = self.settings["none_color"]

        self.draw.text(
            (xmin, ymin - self.settings["font"]["legend"] - margin),
            self.translate("<<casedef:ili>> / 100,000"),
            (0, 0, 0),
            font=PIL.ImageFont.truetype(
                self.settings["fontfile"],
                size=self.settings["font"]["legend"]))
        self.draw.text(
            (xmax + margin, ymin),
            "> {0}".format(self.settings["max_incidence"]),
            (0, 0, 0),
            font=PIL.ImageFont.truetype(
                self.settings["fontfile"],
                size=self.settings["font"]["legend"]))
        self.draw.text(
            (xmax + margin, ymax - self.settings["font"]["legend"]),
            "> {0}".format(self.settings["min_incidence"]),
            (0, 0, 0),
            font=PIL.ImageFont.truetype(
                self.settings["fontfile"],
                size=self.settings["font"]["legend"]))
        self.draw.text(
            (xmax + margin, ymax + (ynone - ymax -
                                    self.settings["font"]["legend"]) // 2),
            "< {0}".format(self.settings["min_incidence"]),
            (0, 0, 0),
            font=PIL.ImageFont.truetype(
                self.settings["fontfile"],
                size=self.settings["font"]["legend"]))

    def savefig(self, *args, **kwargs):
        """savefig not implemented for maps (separate pdfs)"""
        # (Unused argument) pylint: disable=W0613
        # (Method could be function) pylint: disable=R0201
        return

    def save(self, figname=None):
        """Save all the maps"""

        if figname is None:
            figname = self.settings["figname"]
        tools.create_dir(figname, remove=True)
        for key, img in self.maps.items():
            imgname = os.path.join(figname, "{0}.png".format(key))
            tools.create_dir(imgname)
            img.save(imgname)


class Map(object):
    """Class to make maps"""

    def __init__(self, fig, settings, datasets):
        self.fig = fig
        self.settings = settings
        self.datasets = datasets
        self.translate = lambda text: utils.translate(
            text, self.fig.settings["lang"])

    def get_data(self):
        """Return the regional data as a date-region-value dict"""

        all_data = {}
        for options in self.datasets.values():
            region = self.translate(options["label"])
            start_date, end_date = utils.get_limits(
                options["season"], options["country"], options["average"])
            data = Data(options)
            datadict = data.get_datadict()
            dates = sorted([
                date for date, values in datadict.items()
                if "inet_actives" in values and "inet_cases" in values and
                date >= start_date and date <= end_date and
                date.isoweekday() == 7])
            if end_date.isoweekday() in range(self.fig.settings["pre_days"],
                                              7):
                datadict[end_date]["inet_actives"] = data.participant_days(
                    end_date, end_date.isoweekday())
                datadict[end_date]["inet_cases"] = sum([
                    datadict[end_date - datetime.timedelta(days=day)]["cases"]
                    for day in range(end_date.isoweekday())])
                dates.append(end_date)
            for bigregion, regions in self.settings["regions"].items():
                if region not in regions:
                    continue
                for date in dates:
                    if date not in all_data:
                        all_data[date] = collections.defaultdict(
                            lambda: tools.AddList([0, 0]))
                    all_data[date][bigregion] += [
                        int(datadict[date]["inet_actives"]),
                        datadict[date]["inet_cases"]]
        return all_data

    def draw(self):
        """Draw the map"""
        self.fig.add_bar()
        self.fig.add_logo()

        for date, daydata in tools.sort_iter(self.get_data()):
            regions = set()
            img = self.fig.img.copy()
            draw = PIL.ImageDraw.Draw(img)

            draw.text(
                (self.fig.settings["margin"]["date"],
                 self.fig.settings["margin"]["date"]),
                tools.dates_string(
                    date - datetime.timedelta(days=date.isoweekday() - 1),
                    date),
                (0, 0, 0),
                font=PIL.ImageFont.truetype(
                    self.fig.settings["fontfile"],
                    size=self.fig.settings["font"]["date"]))

            pixdata = img.load()
            for bigregion, (actives, cases) in daydata.items():
                incidence = 100000 * cases * 7 // (actives * date.isoweekday())
                color = self.fig.get_color(incidence)
                for region in self.settings["regions"][bigregion]:
                    regions.add(region)
                    for xval, yval in self.fig.regions[region]:
                        pixdata[xval, yval] = color
            self.fig.maps[date] = img
            for region in set(self.fig.regions.keys()) - regions:
                if isinstance(region, tuple) or "_" in region:
                    continue
                for xval, yval in self.fig.regions[region]:
                    pixdata[xval, yval] = self.fig.settings["unknown_color"]

        return True
