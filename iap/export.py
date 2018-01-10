# !/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Export the data to various formats"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import re
import collections
import os
import zipfile
import subprocess
import copy
import logging
import six

from .exceptions import IAPError
from . import utils, config, baseline, tools
from .series import Series
from .data import Data
from .bardata import BarData

logger = logging.getLogger(__name__)


class Export(object):
    """Class which exports the data in various formats"""

    def __init__(self, ini, force_daily=False):
        self.datasets = ini.datasets
        self.settings = ini.settings

        self.translate = lambda text, latex=False: utils.translate(
            text, self.settings["fig"]["lang"], latex=latex)

        self.rounds = ["inet_actives", "inet_incidence", "control_week",
                       "inet_control", "inet_cases", "eiss_incidence",
                       "eiss_samples", "google_trends"]
        self.rounds1 = ["climate_temp"]
        self.force_daily = force_daily

    def write_csv(self, fname, plotname=None, onefile=True):
        """Write csv for a complete inifile"""
        if isinstance(fname, six.string_types) and onefile:
            basename, ext = os.path.splitext(fname)
            if ext != ".csv":
                fname = basename + ".csv"
            tools.create_dir(fname)
            csvobj = tools.csvopen(fname, "w")
        else:
            csvobj = fname

        for plot, plot_settings in self.settings["plots"].items():
            if plotname and plot != plotname:
                continue
            datasets = (
                utils.get_datasets_keys(
                    self.datasets, plot_settings["datasets"])
                if len(plot_settings["datasets"]) > 0 else
                self.datasets)
            if plot_settings["type"] == "barplot":
                self.write_csv_bar(plot_settings, datasets, csvobj)
            elif plot_settings["type"] in ("plot", "map"):
                self.write_csv_plot(plot_settings, datasets, csvobj)
            elif plot_settings["type"] in ("venn",):
                pass
            elif plot_settings["type"] == "weeks":
                self.write_csv_weeks(fname[:-4], datasets)

            if onefile:
                csvobj.write("\n\n")

        if isinstance(fname, six.string_types) and onefile:
            csvobj.close()

    def get_all_data_weeks(self, datasets):
        """Get all_data for csv_weeks"""

        all_data = collections.defaultdict(
            lambda: collections.defaultdict(dict))
        columns = tools.SetList()

        size = len(datasets)
        threshold = 0
        for index, options in enumerate(self.datasets.values()):
            if 100 * index / size >= threshold:
                logger.info("{0:.1f}%".format(100 * index / size))
                threshold += 0.5
            columns.append(options["label"])
            min_date, max_date = utils.get_limits(
                options["season"], options["country"], options["average"])

            # determine all labels
            for options["answer"] in Series(options, "joins").get_labels():
                for date, daydata in Data(options).get_datadict().items():
                    if (date.isoweekday() != 7 or date < min_date or
                            date > max_date):
                        continue
                    val = daydata[options["source_measure"]]
                    if options["source_measure"] == "inet_actives":
                        val = round(val, 2)
                    all_data[date][options["answer"]][options["label"]] = val

        return all_data, columns

    def write_csv_weeks(self, datasets, dirname):
        """Write the weeks"""

        csvdir = os.path.join(dirname, "{0}".format(
            utils.season_to_years(
                next(six.itervalues(datasets))["season"])[0]))
        tools.create_dir(csvdir)

        all_data, columns = self.get_all_data_weeks(datasets)
        options = next(six.itervalues(datasets))
        labels = options["cutter"].split(config.SEP["cutter"])
        columns = labels + columns

        zipobj = zipfile.ZipFile(
            os.path.join(dirname, "{period}.zip".format(**options)),
            "w",
            zipfile.ZIP_DEFLATED)
        for date, daydata in all_data.items():
            csvname = os.path.join(csvdir, date.strftime("%Y%m%d") + ".csv")
            with tools.csvopen(csvname, "w") as csvobj:
                writer = tools.UniDictWriter(csvobj, columns, restval=0)
                writer.writerow(
                    dict(zip(columns, self.translate(columns, latex=False))))
                for label, value in tools.sort_iter(daydata):
                    writer.writerow(
                        dict(value, **dict(zip(
                            labels, label.split(config.SEP["cutter"])))))
            zipobj.write(csvname.encode("ascii"),
                         arcname=os.path.basename(csvname.encode("ascii")))
        zipobj.close()

    def write_csv_bar(self, plot_settings, datasets, csvobj):
        """Write csv for a barplot"""
        table = BarData(plot_settings, datasets)
        bar_data, labels = table.get_table()

        columns = ["houselabel"] + labels["city"]
        writer = tools.UniDictWriter(csvobj, columns)

#         left_corner = ("Attack rate"
#                        if plot_settings["bars"] == "attack" else
#                        "Pie diagram" if plot_settings["bars"] == "pie" else
#                        "")
#         writer.writerow(dict(zip(
#             columns, [left_corner] + self.translate(labels["city"]))))
        writer.writerow(dict(zip(columns, self.translate(
            ["", "<<measure:attack>>"]
            if plot_settings["bars"] == "attack" else
            ["", "<<measure:participants>>"]
            if plot_settings["bars"] == "pie" else
            # ["", "<<measure:risk>>"]
            # if plot_settings["bars"] == "compare" else
            [""] + labels["city"]))))

        for house in labels["house"]:
            if plot_settings["bars"] in ("attack", "control", "surveys",
                                         "percentage_by_answer", "compare"):
                writer.writerow(
                    dict([(city,
                           tools.Format("{value} / {denominator:.0f}").format(
                               extra=bar_data[(house, city)]))
                          for city in labels["city"]] +
                         [("houselabel", self.translate(house))]))
                if ("baseline" in bar_data[(house, labels["city"][0])] and
                        house == labels["house"][-1]):
                    writer.writerow(
                        dict(
                            [(city, "{0:.0f} / 100000".format(
                                bar_data[(house, city)]["baseline"]))
                             for city in labels["city"]] +
                            [("houselabel", "Baseline")]))
            else:
                writer.writerow(
                    dict(
                        [(city, bar_data[(house, city)]["value"])
                         for city in labels["city"]] +
                        [("houselabel", self.translate(house))]))

    def write_csv_plot(self, _plot_settings, datasets, csvobj):
        """Write CSV lines for a line plot"""

        # baseline_dict = baseline.get_dict(plot_settings)
        baseline_dict = None
        all_vals = collections.defaultdict(dict)
        columns = tools.SetList(["<<xlabel:date>>"])
        for options in datasets.values():
            options = copy.copy(options)
            options["average"] = 7
            if self.force_daily:
                options["daily"] = True
            datadict = Data(options).get_datadict()
            min_date, max_date = (
                utils.get_limits(
                    options["season"], options["country"], options["average"])
                if options["limits"] == "hide" else
                (None, None))

            if baseline_dict:
                for date, value in zip(*baseline.get_baseline(
                        baseline_dict, options["season"])):
                    if ((min_date and (date < min_date or date > max_date)) or
                            (not options["daily"] and date.isoweekday() != 7)):
                        continue
                    column = "Baseline"
                    columns.append(column)
                    all_vals[date][column] = int(value)

            for date, values in datadict.items():
                if ((min_date and (date < min_date or date > max_date)) or
                        (not options["daily"] and date.isoweekday() != 7)):
                    continue
                self.add_value(all_vals[date], values, options, columns)

        writer = tools.UniDictWriter(csvobj, columns)
        writer.writerow(dict(zip(columns, self.translate(columns))))
        for date, values in tools.sort_iter(all_vals):
            if len(values) == 0:
                continue
            writer.writerow(dict(values, **{"<<xlabel:date>>": date}))

    def get_val(self, values, source):
        """Return the value, and round if necessary"""
        val = values[source]
        if source in self.rounds:
            val = int(val)
        elif source in self.rounds1:
            val = round(val, 1)
        if source == "inet_reporting":
            val = "{0:.1f}".format(val)
        return val

    def add_value(self, daydata, values, options, columns):
        """Add value to all_vals"""

        if options["source_measure"] in values:
            base = options["csvlabel"]
            if options["source_measure"] in ("inet_incidence",
                                             "inet_reporting"):
                column = base + " [<<measure:actives_short>>]"
                columns.append(column)
                daydata[column] = self.get_val(values, "inet_actives")

                column = base + " [<<measure:cases>>]"
                columns.append(column)
                daydata[column] = self.get_val(values, "inet_cases")

            elif options["source_measure"] == "inet_control":
                column = base + " [<<label:denominator>>]"
                columns.append(column)
                daydata[column] = self.get_val(values, "inet_cases")

                column = base + " [<<label:numerator>>]"
                columns.append(column)
                daydata[column] = self.get_val(values, "control_week")

                # columns.append(column + " [<<measure:control>>]")
                # daydata[columns[-1]] = self.get_val(values, "inet_control")
            else:
                column = base
                columns.append(column)
                daydata[column] = self.get_val(values,
                                               options["source_measure"])

    @staticmethod
    def dump_csv(period):
        """Dump the data for the specific period"""

        if not utils.period_available(period):
            logger.error("Period {0} not available".format(period))
            return

        logger.info("Dumping csv for {0}".format(period))

        csvdir = os.path.join(config.LOCAL["dir"]["export"], "csv")
        tools.create_dir(csvdir)

        zipobj = zipfile.ZipFile(
            os.path.join(config.LOCAL["dir"]["export"],
                         "{0}.zip".format(period)),
            "w",
            zipfile.ZIP_DEFLATED)

        for table in ["intake", "survey"]:
            tbl = utils.get_tbl(table, "new", period)

            sql_columns = utils.get_columns(tbl)
            columns = tools.SetList()
            for column, options in config.TABLE[table].items():
                if "src" in options and column != "surveys":
                    continue
                if column not in sql_columns:
                    continue
                columns.append(column)

            fname = os.path.join(csvdir, "{0}_{1}.csv".format(table, period))
            order_id = "qid" if table == "intake" else "sid"
            tbl_name = utils.get_tbl(table, "new", period)
            utils.sql_to_csv(tbl_name, fname, columns, order_id)
            zipobj.write(fname.encode("ascii"),
                         arcname=os.path.basename(fname.encode("ascii")))
        zipobj.close()

    @staticmethod
    def dump_orig(period):
        """Dump the original data as csv files"""

        cache = tools.Cache()
        privacy = collections.defaultdict(list)
        if not utils.period_available(period):
            logger.error("Period {0} not available".format(period))
            return
        logger.info("Dumping orig csv for {0}".format(period))

        src = utils.period_to_src(period)
        dbini = utils.get_dbini(src)

        tables = tools.SetList()
        for table in ["intake", "survey"]:
            tables.append(utils.get_tbl(
                table, "orig",
                dbini["{0}_orig".format(table)]
                if "{0}_orig".format(table) in dbini
                else src))

            if table + "2" in dbini:
                tables.append(utils.get_tbl(
                    table + "2", "orig",
                    dbini["{0}_orig".format(table)]
                    if "{0}_orig".format(table) in dbini
                    else src))

            if table + "_joins" in dbini:
                for join in dbini[table + "_joins"]:
                    if cache(re.search(r"(.*)\[(.*)\]", join)):
                        tables.append(cache.output.group(1))

        if "privacy" not in dbini:
            for tbl in tables:
                logger.error("{0}: {1}".format(tbl,
                                               utils.get_columns(tbl)))
            raise IAPError("Add privacy for {0}".format(period))

        for tbl_column in dbini["privacy"]:
            tbl, column = tbl_column.split(config.SEP["privacy"])
            privacy[tbl].append(column)

        zipobj = zipfile.ZipFile(
            os.path.join(config.LOCAL["dir"]["export"],
                         "orig_{0}.zip".format(src)),
            "w",
            zipfile.ZIP_DEFLATED)

        csvdir = os.path.join(config.LOCAL["dir"]["export"], "csv")
        tools.create_dir(csvdir)
        for tbl in tables:
            fname = os.path.join(csvdir, tbl + ".csv")
            columns = [column for column in utils.get_columns(tbl)
                       if column not in privacy[tbl]]
            utils.sql_to_csv(tbl, fname, columns)
            zipobj.write(fname.encode("ascii"),
                         arcname=os.path.basename(fname.encode("ascii")))
        zipobj.close()

    @staticmethod
    def dump_sql(period):
        """Save an zipped sql for the specific period"""

        tables = []
        if len(tables) == 0:
            return "Define which tables to dump"

        sqlfile = os.path.join(config.LOCAL["dir"]["export"],
                               "{0}.sql".format(period))
        tools.create_dir(sqlfile)

        logger.info("Export sql for {0}".format(period))
        cmd = ("mysqldump -u {mysql_user} -p{mysql_pass}" +
               " --quote-names --opt" +
               " {mysql_db} {tables} > {sqlfile}").format(
                   sqlfile=sqlfile,
                   mysql_user=config.LOCAL["db"]["user"],
                   mysql_pass=config.LOCAL["db"]["pass"],
                   mysql_db=config.LOCAL["db"]["db"],
                   tables=" ".join(tables))
        try:
            subprocess.check_call(cmd, shell=True)
            subprocess.check_call("bzip2 -f {0}".format(sqlfile), shell=True)
        except subprocess.CalledProcessError:
            logger.error("Failed sql export {0}".format(period))
            return
