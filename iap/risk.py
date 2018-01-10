#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Calculate odds ratios"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import numpy
import scipy.stats
import json
import rpy2.robjects
import collections
import re
import os
import logging
import six
import io
import natsort

from .exceptions import IAPError
from . import utils, config, split, samples, tools
from .ini import Ini
from .series import Series

NONCUTTER = ["country", "season", "surveys"]
logger = logging.getLogger(__name__)
run_r = rpy2.robjects.r


class Risk(object):
    """Class to calculate odds ratios"""

    def __init__(self, fig_settings, settings, datasets):
        self.fig_settings = fig_settings
        self.settings = settings
        datasets = (utils.get_datasets_keys(datasets, settings["datasets"])
                    if len(settings["datasets"]) > 0 else
                    datasets)
        if len(datasets) != 1:
            raise IAPError("More than one dataset for risk model")
        self.dataset = next(six.itervalues(datasets))

        self.results = None
        self.cutters = None
        self.headers = None
        self.subs = None

        if self.settings["output"] != "":
            tools.create_dir(self.settings["output"], remove=True)

    def translate(self, text):
        """translate based on set language"""
        return utils.translate(text, self.fig_settings["lang"])

    def load(self, only_fill=False):
        """Load results previously cached in the database"""

        self.init()
        cursor = utils.query(
            """SELECT
                results, model
            FROM
                risks
            WHERE
                countries = %(countries)s AND
                seasons = %(seasons)s AND
                cutters = %(cutters)s AND
                casedef = %(casedef)s AND
                control = %(control)s AND
                min_surveys = %(min_surveys)s AND
                family = %(family)s AND
                intake = %(intake)s AND
                samples_onsets = %(samples_onsets)s AND
                samples_period = %(samples_period)s
            """,
            {
                "countries": config.SEP["params"].join(
                    self.dataset["country_values"]),
                "seasons": config.SEP["params"].join(
                    self.dataset["season_values"]),
                "cutters": config.SEP["params"].join(sorted(
                    self.dataset["cutter_values"] +
                    self.dataset["extras"])),
                "casedef": self.dataset["casedef"],
                "control": self.dataset["control"],
                "min_surveys": self.dataset["min_surveys"],
                "family": self.settings["family"],
                "intake": self.dataset["intake"],
                "samples_period": self.dataset["samples_period"],
                "samples_onsets": self.dataset["samples_onsets"]})

        if cursor.rowcount > 0 and not self.dataset["reload"]:
            row = cursor.fetchone()
            for key, value in json.loads("{0}".format(row["results"])).items():
                self.results[key] = collections.defaultdict(list)
                self.results[key].update(value)
        else:
            self.create()
            self.save_csv()
            if only_fill:
                return
            # self.clear()
            participants = self.get_participants()
            self.add_participants(participants)
            model = self.get_model()
            self.save_rcode(model)
            model_output = self.run_model(model)

            summary = run_r.summary(model_output)

            run_r.library("pscl")
            print("pscl - pR2")
            print(run_r.pR2(model_output))

#             run_r.library("BaylorEdPsych")
#             print("BaylorEdPsych - PseudoR2")
#             print(run_r.PseudoR2(model_output))

            print("logLik")
            print(run_r.logLik(model_output))

            coefficients = summary.rx2("coefficients")
            aliased = summary.rx2("aliased")

            vif = run_r.vif(model_output)

            self.save(model)
            self.add_coefficients(coefficients, aliased, vif)
            self.save(model)
        self.uni()

    def get_model(self):
        """Return the R model"""

        return "got_ili ~ {0}".format(" + ".join([
            self.results[cutter]["model"]
            for cutter in self.cutters
            if "model" in self.results[cutter]]))

    def init(self):
        """Initialize cutters"""

        cache = tools.Cache()
        self.cutters = []
        self.headers = []
        self.subs = {}
        for cutter in self.dataset["cutter_values"]:
            if re.match("sql", cutter):
                self.headers.append(cutter)
                self.cutters.append(cutter)
            elif cache(re.match(r"(.*){0}(.*)".format(
                    config.SEP["risk_cutter"]), cutter)):
                cutter, split_var = cache.output.groups()
                if not self.settings["show_unknown"]:
                    self.headers.append(cutter)
                    self.subs[cutter] = []
                split_vals = (self.dataset["{0}_values".format(split_var)]
                              if split_var in ("country", "season") else
                              [utils.country_season_to_period(
                                  country, season)
                               for country in self.dataset["country_values"]
                               for season in self.dataset["season_values"]])
                for split_elem in split_vals:
                    sub_cutter = "{cutter}{sep}{period}".format(
                        cutter=cutter,
                        sep=config.SEP["period_cutter"],
                        period=split_elem)
                    self.cutters.append(sub_cutter)
                    if self.settings["show_unknown"]:
                        self.headers.append(sub_cutter)
                    else:
                        self.subs[cutter].append((sub_cutter, "1"))
            elif cache(re.match(r"(.*)\((.*)\)", cutter)):
                question, answers = cache.output.groups()
                self.headers.append(question)
                self.subs[question] = []
                for answer in re.split("-", answers):
                    sub_cutter = "{0}_{1}".format(question, answer)
                    self.cutters.append(sub_cutter)
                    self.subs[question].append((sub_cutter, "1"))
                    self.subs[question].append((sub_cutter, "2"))
            else:
                self.headers.append(cutter)
                self.cutters.append(cutter)
        self.cutters.append("country")
        self.cutters.append("season")

        if "surveys" in self.dataset["extras"]:
            self.cutters.append("surveys")
            self.headers.append("surveys")

        self.results = {}
        for cutter in self.cutters:
            self.results[cutter] = collections.defaultdict(list)
            self.results[cutter]["sql_col"] = tools.sql_col(cutter)

    def add_participants(self, participants):
        """Add participants to self.results"""

        for cutter in self.cutters:
            cvalues = self.results[cutter]
            if cutter == "surveys":
                cvalues["participants"] = {}
                cvalues["model"] = "surveys"
                cvalues["label"] = ["all"]
                cvalues["reference"] = None
                continue
            cvalues["participants"] = participants[cutter]
            cvalues["label"] = natsort.natsorted(
                participants[cutter].keys())
            if cutter == "country":
                cvalues["label"] = self.dataset["country_values"]
            cvalues["reference"] = (
                cvalues["label"][0] if cutter in NONCUTTER
                else split.get_reference(cutter))
            if cvalues["reference"] not in cvalues["label"]:
                cvalues["reference"] = cvalues["label"][0]

            if len(cvalues["label"]) > 1:
                levels = sorted(
                    cvalues["label"],
                    key=lambda i, cv=cvalues: i != cv["reference"])
                if cutter == "season":
                    continue
                cvalues["model"] = (
                    "factor({col}, levels = c({levels}))").format(
                        col=cvalues["sql_col"],
                        levels=", ".join(["\"{0}\"".format(label)
                                          for label in levels]))

    def create(self):
        """Create the table tmp_risk"""

        utils.drop_table("tmp_risk")
        utils.query("CREATE TABLE tmp_risk ({columns})".format(
            columns=",\n".join(
                ["country VARCHAR(10)",
                 "season VARCHAR(10)",
                 "{0} VARCHAR(40)".format(
                     "uid" if self.dataset["control"] == "" else "sid"),
                 "got_ili BOOL",
                 "surveys INT"] +
                ["{0} VARCHAR(10)".format(self.results[cutter]["sql_col"])
                 for cutter in self.cutters
                 if cutter not in NONCUTTER])))

        for country in self.dataset["country_values"]:
            for season in self.dataset["season_values"]:
                self._fill(country, season)

    def _fill(self, country, season):
        """Fill tmp_risk for a period"""

        inistring = tools.Format("""
            [datasets]
                [[default]]
                    country = {country}
                    season = {season}
                    min_surveys = {min_surveys}
                    intake  = {intake}
                    source_measure = inet_incidence
                    casedef = {casedef}
                    samples_period = {samples_period}
                    samples_onsets = {samples_onsets}
                    ignore_multiple = {ignore_multiple}
                    first_survey = {first_survey}
                    ignore_double = {ignore_double}
            """).format(country=country, season=season, extra=self.dataset)
        ini = Ini(inistring)
        if len(ini.datasets.keys()) == 0:
            return

        logger.info("Getting risk data for {0}{1}".format(country, season))
        options = ini.datasets["default"]
        series = Series(options, "cases")
        series.fill_intake()
        series.fill_survey()

        min_date, max_date = samples.get_limits(
            season, country, self.dataset["samples_onsets"])
        utils.query(
            """DELETE FROM tmp_survey
            WHERE
                {onset_column} < %(min_date)s OR
                {onset_column} > %(max_date)s
            """.format(onset_column=series.options["onset_column"]),
            {"min_date": min_date, "max_date": max_date})

        if self.dataset["control"] == "":
            utils.query(
                """INSERT INTO tmp_risk
                    SELECT
                        {coldef_list}
                    FROM
                        tmp_intake
                """.format(coldef_list=",".join(
                    ["%(country)s", "%(season)s", "uid", "0", "surveys"] +
                    [re.sub("'(MULTIPLE|NONE|e|d|ERROR)'", "'UNKNOWN'",
                            split.get_sql(cutter, options["period"]))
                     for cutter in self.cutters
                     if cutter not in NONCUTTER])),
                {"country": country, "season": season})

            utils.query(
                """UPDATE tmp_risk
                    SET got_ili = (
                        SELECT
                             COUNT({distinct} uid)
                         FROM
                             tmp_survey
                         WHERE
                            tmp_survey.uid = tmp_risk.uid)
                    WHERE
                        country = %(country)s AND
                        season = %(season)s
                """.format(
                    distinct="DISTINCT"
                    if "binomial" in self.settings["family"] else
                    "" if "poisson" in self.settings["family"] else
                    "ERROR"),
                {"country": country, "season": season})
        else:
            utils.query(
                """INSERT INTO tmp_risk
                    SELECT
                        %(country)s,
                        %(season)s,
                        sid,
                        0,
                        surveys,
                        {coldef_list}
                    FROM
                        tmp_survey
                    LEFT JOIN
                        tmp_intake USING (uid)
                """.format(
                    coldef_list=",".join([
                        re.sub("'(MULTIPLE|NONE|e|d|ERROR)'", "'UNKNOWN'",
                               split.get_sql(cutter, options["period"]))
                        for cutter in self.cutters
                        if cutter not in NONCUTTER])),
                {"country": country, "season": season})

            utils.query(
                """UPDATE tmp_risk
                LEFT JOIN
                    tmp_survey USING (sid)
                SET
                    got_ili = {control}
                WHERE
                    country = %(country)s AND
                    season = %(season)s
                """.format(control=self.dataset["control"]),
                {"country": country, "season": season})

#         utils.drop_table("tmp_intake")
#         utils.drop_table("tmp_survey")

    def save_csv(self):
        """Save the file as a csv to read in R"""
        if self.settings["output"] == "":
            return
        fname = os.path.join(self.settings["output"], "data.csv")
        tools.create_dir(fname)
        utils.sql_to_csv("tmp_risk", fname)

    def save_rcode(self, model):
        """Save R code to a file"""
        if self.settings["output"] == "":
            return

        fname = os.path.join(self.settings["output"], "code.R")
        tools.create_dir(fname)
        with io.open(fname, "w") as fobj:
            fobj.write("data <- read.csv(\"data.csv\")\n")
            fobj.write("model <- {0}\n".format(model))
            fobj.write("output <- glm(model, family={0}, data=data)\n".format(
                self.settings["family"]))
            fobj.write("library(pscl)\n")
            fobj.write("pR2(output)\n")

    def run_model(self, model):
        """Do the odd's ratio in R"""

        if self.settings["output"] != "":
            data = run_r("read.csv")(
                os.path.join(self.settings["output"], "data.csv"), sep=',')
        else:
            with tools.Capturing():
                run_r.library("RMySQL")

            con = run_r.dbConnect(
                run_r.dbDriver("MySQL"),
                dbname=config.LOCAL["db"]["db"],
                host=config.LOCAL["db"]["host"],
                user=config.LOCAL["db"]["user"],
                password=config.LOCAL["db"]["pass"])
            data = run_r.dbGetQuery(con, "SELECT * FROM tmp_risk")
            run_r.dbDisconnect(con)

        logger.info(model)
        # glmm(model, random=id)
        model_output = run_r.glm(model, family=run_r(self.settings["family"]),
                                 data=data)

        with tools.Capturing():
            run_r.library("rms")
            # run_r.library("car")

        return model_output

    @staticmethod
    def _get_ili(participants):
        """Return total with/without ili"""
        ili = [0, 0]
        for _country, country_values in participants.items():
            for _season, season_values in country_values.items():
                for got_ili, value in season_values.items():
                    ili[int(got_ili)] += value
        return ili

    def uni(self):
        """Do univariate analyses"""

        for cutter in self.cutters:
            cvalues = self.results[cutter]
            if "reference" not in cvalues:
                continue
            if "participants" not in cvalues:
                continue

            for label in cvalues["label"]:
                non_ili, ili = self._get_ili(cvalues["participants"][label])
                cvalues["ili"].append(ili)
                cvalues["non_ili"].append(non_ili)
                if label == cvalues["reference"]:
                    ref_non_ili, ref_ili = non_ili, ili

            for label in cvalues["label"]:
                # if label == "UNKNOWN":
                #    continue

                if label == cvalues["reference"]:
                    cvalues["uni_rr"].append(None)
                    cvalues["uni_rr_lower"].append(None)
                    cvalues["uni_rr_upper"].append(None)
                    cvalues["uni_oddr"].append(None)
                    cvalues["uni_oddr_lower"].append(None)
                    cvalues["uni_oddr_upper"].append(None)
                else:
                    non_ili, ili = self._get_ili(
                        cvalues["participants"][label])
                    min_val, val, max_val = tools.get_rr(
                        ili, non_ili + ili, ref_ili, ref_ili + ref_non_ili)
                    cvalues["uni_rr"].append(val)
                    cvalues["uni_rr_lower"].append(min_val)
                    cvalues["uni_rr_upper"].append(max_val)

                    min_val, val, max_val = tools.get_oddr(
                        ili, non_ili + ili, ref_ili, ref_ili + ref_non_ili)
                    cvalues["uni_oddr"].append(val)
                    cvalues["uni_oddr_lower"].append(min_val)
                    cvalues["uni_oddr_upper"].append(max_val)

    def add_coefficients(self, coefficients, aliased, vif):
        """Add the glm-determined risk to results"""
        alpha = 1 - 0.95
        qnorm = scipy.stats.distributions.norm.ppf
        zvalue = qnorm(1 - alpha / 2)
        for cutter in self.cutters:
            cvalues = self.results[cutter]
            for label in cvalues["label"]:
                if "model" in cvalues and label != cvalues["reference"]:
                    rkey = "{0}{1}".format(cvalues["model"], label)
                else:
                    rkey = None

                # an aliased key has no vif or coefficient
                if rkey is not None and aliased.rx2(rkey)[0]:
                    rkey = None

                cvalues["vif"].append(
                    None if rkey is None else
                    vif.rx2(rkey)[0])

                cvalues["pvalue"].append(
                    None if rkey is None else
                    coefficients.rx2(rkey, "Pr(>|z|)")[0])

                # log(risk) = Estimate +/- zvalue * (std. error)
                cvalues["risk"].append(
                    None if rkey is None else
                    numpy.exp(coefficients.rx2(rkey, "Estimate")[0]))
                cvalues["error"].append(
                    None if rkey is None else
                    coefficients.rx2(rkey, "Std. Error")[0])
                cvalues["lower"].append(
                    None if rkey is None else
                    cvalues["risk"][-1] /
                    numpy.exp(cvalues["error"][-1] * zvalue))
                cvalues["upper"].append(
                    None if rkey is None else
                    cvalues["risk"][-1] *
                    numpy.exp(cvalues["error"][-1] * zvalue))

    def get_participants(self):
        """Add the participants"""

        cursor = utils.query("""SELECT
                {cutters}, got_ili, count(*) AS total
            FROM
                tmp_risk
            GROUP BY
                country, season, got_ili, {cutters}
        """.format(cutters=",".join([
            self.results[cutter]["sql_col"]
            for cutter in self.cutters])))

        participants = {}
        for row in cursor.fetchall():
            for cutter in self.cutters:
                sql_col = self.results[cutter]["sql_col"]
                label = row[sql_col]
                country = row["country"]
                season = row["season"]
                got_ili = row["got_ili"]

                if cutter not in participants:
                    participants[cutter] = {}
                if label not in participants[cutter]:
                    participants[cutter][label] = {}
                if country not in participants[cutter][label]:
                    participants[cutter][label][country] = {}
                if season not in participants[cutter][label][country]:
                    participants[cutter][label][country][season] = {}
                if got_ili not in participants[cutter][label][country][season]:
                    participants[cutter][label][country][season][got_ili] = 0
                participants[cutter][label][country][season][got_ili] += (
                    row["total"])
        return participants

    def save(self, model):
        """Save the results to the database"""

        utils.connect()
        utils.query(
            """REPLACE INTO risks
                (countries, seasons, casedef, control, min_surveys, intake,
                 samples_period, samples_onsets,
                 family,
                 cutters, results, model)
            VALUES
                (%(countries)s, %(seasons)s, %(casedef)s, %(control)s,
                 %(min_surveys)s,
                 %(intake)s,
                 %(samples_period)s, %(samples_onsets)s,
                 %(family)s,
                 %(cutters)s, %(results)s, %(model)s)
            """,
            {
                "countries": config.SEP["params"].join(
                    self.dataset["country_values"]),
                "seasons": config.SEP["params"].join(
                    self.dataset["season_values"]),
                "cutters": config.SEP["params"].join(sorted(
                    self.dataset["cutter_values"] + self.dataset["extras"])),
                "casedef": self.dataset["casedef"],
                "control": self.dataset["control"],
                "min_surveys": self.dataset["min_surveys"],
                "intake": self.dataset["intake"],
                "family": self.settings["family"],
                "samples_period": self.dataset["samples_period"],
                "samples_onsets": self.dataset["samples_onsets"],
                "results": json.dumps(self.results),
                "model": model})

    def get_value(self, cutter, label):
        """Get the values for a cutter and a label"""
        cvalues = self.results[cutter]
        index = cvalues["label"].index(label)
        vals = {}
        for key, value in cvalues.items():
            if isinstance(value, list):
                vals[key] = value[index]
            else:
                vals[key] = value
        return vals

    def get_title(self, cutter):
        """Get the title of a cutter"""
        if cutter == "surveys":
            return "Surveys"
        elif cutter in NONCUTTER:
            return self.translate("<<all_{0}:title>>".format(cutter))
        else:
            return self.translate(cutter.get_cutter_label(cutter))

    def get_label(self, cutter, label):
        """Get the label of a cutter"""
        if cutter == "surveys":
            return ""
        elif cutter in NONCUTTER:
            return self.translate("<<{0}:{1}>>".format(cutter, label))
        else:
            return self.translate(cutter.get_answer_label(
                cutter, label, self.fig_settings))

    def get_totals(self, participants):
        """Get the totals for each country/label"""

        total_lists = collections.defaultdict(
            lambda: collections.defaultdict(list))
        for label, country_values in participants.items():
            if label == "UNKNOWN" and not self.settings["show_unknown"]:
                continue
            for country, season_values in country_values.items():
                for season, total in season_values.items():
                    total_lists[country][season].append(sum(total.values()))

        totals = collections.defaultdict(
            lambda: collections.defaultdict(int))
        for country, season_values in total_lists.items():
            for season, values in season_values.items():
                totals[country][season] = (
                    sum(values) if
                    len(values) > 1 and
                    max(values) < 0.999 * sum(values) else
                    0)
        return totals

    def add_perc(self):
        """Add percentages"""

        if self.settings["show_perc"] not in ("country", "full"):
            return

        for cutter in self.cutters:
            cvalues = self.results[cutter]

            totals = self.get_totals(cvalues["participants"])
            cvalues["perc"] = {}

            for label in cvalues["label"]:
                if label == "UNKNOWN" and not self.settings["show_unknown"]:
                    continue

                cvalues["perc"][label] = {}
                for country in self.results["country"]["label"]:
                    vals = []
                    for season in self.results["season"]["label"]:
                        value = (
                            cvalues["participants"][label][country][season] if
                            (label in cvalues["participants"] and
                             country in cvalues["participants"][label] and
                             season in cvalues["participants"][label][country])
                            else None)
                        total = totals[country][season]
                        vals.append("-" if total == 0 else
                                    0 if value is None else
                                    100 * sum(value.values()) / total)

                    if self.settings["show_perc"] == "country":
                        vals = [val for val in vals
                                if val != "-"]
                        #       and val != 0]
                        val = ("-" if len(vals) == 0 else
                               "{0:.1g}".format(numpy.average(vals))
                               if numpy.average(vals) < 0.95 else
                               "{0:.0f}".format(numpy.average(vals)))

                    elif self.settings["show_perc"] == "full":
                        val = ",".join([
                            "{0:>2s}".format("{0:.0f}".format(val)
                                             if val != "-" else "-")
                            for val in vals])
                    cvalues["perc"][label][country] = val

    def add_extra(self):
        """Add some extra calculated values"""
        for cutter in self.cutters:
            cvalues = self.results[cutter]
            colors = []
            for label in cvalues["label"]:
                val = self.get_value(cutter, label)
                colors.append("black" if val["risk"] is None else
                              "red" if val["lower"] > 1 else
                              "blue" if val["upper"] < 1 else
                              "black")
            cvalues["color"] = colors
            cvalues["effect"] = ["+" if color == "red" else
                                 "-" if color == "blue" else
                                 " "
                                 for color in colors]

    def make_csv(self):
        """Textual barplot"""

        self.add_extra()
        self.add_perc()
        risk = "RR" if "link=log" in self.settings["family"] else "OR"

        columns = ["Question", "Answer"]
        if self.settings["show_perc"] in ("full", "country"):
            columns.extend(self.results["country"]["label"])
        if self.settings["show_multi"]:
            columns.append(risk)
        if self.settings["show_uni"]:
            columns.append("{0} (univariate)".format(risk))
        if self.settings["show_vif"]:
            columns.append("VIF")

        tools.create_dir(self.settings["csvname"])
        csvobj = tools.csvopen("{0}.csv".format(self.settings["csvname"]), "w")
        writer = tools.UniDictWriter(csvobj, columns, extrasaction="ignore")
        writer.writerow(dict(zip(writer.fieldnames, writer.fieldnames)))

        for cutter in self.headers:
            line = {"Question": self.get_title(cutter)}
            labels = (self.subs[cutter] if cutter in self.subs else
                      [(cutter, label)
                       for label in self.results[cutter]["label"]])

            for sub_cutter, label in labels:
                if (sub_cutter not in self.results or
                        label not in self.results[sub_cutter]["label"] or
                        (label == "UNKNOWN" and
                         not self.settings["show_unknown"])):
                    continue

                if (
                        (sub_cutter in config["cutter"] and
                         "nohist" in config["cutter"][sub_cutter] and
                         label in config["cutter"][sub_cutter]["nohist"]) or
                        (re.match(r"^.*_(\d+|n|o|d)$", sub_cutter) and
                         label != "1")):
                    continue

                line["Answer"] = ("Unknown" if label == "UNKNOWN" else
                                  self.get_label(sub_cutter, label))

                val = self.get_value(sub_cutter, label)
                line[risk] = (
                    "*" if val["risk"] is None else
                    tools.Format(
                        "{risk:<3.2f} ({lower:<3.2f} - {upper:<3.2f})").format(
                            extra=val) if label != "UNKNOWN" else "")
                if "perc" in val:
                    line.update(val["perc"][label])
                line["VIF"] = ("{0:<2.1f}".format(val["vif"])
                               if "vif" in val and val["vif"] is not None
                               else "-")
                line["RR (univariate)"] = (
                    "*" if val["uni_rr"] is None else
                    tools.Format(
                        "{uni_rr:<3.2f} ({uni_rr_lower:<3.2f} -" +
                        " {uni_rr_upper:<3.2f})").format(extra=val))
                line["OR (univariate)"] = (
                    "*" if val["uni_oddr"] is None else
                    tools.Format(
                        "{uni_oddr:<3.2f} ({uni_oddr_lower:<3.2f} -" +
                        " {uni_oddr_upper:<3.2f})").format(extra=val))

                writer.writerow(line)
                line = {"Question": ""}
        csvobj.close()

#     def clear(self):
#         """Clear the unknown values"""
#         utils.query("""DELETE FROM tmp_risk
#             WHERE
#                 {col_unknown}
#         """.format(col_unknown=" OR ".join([
#             "{0}='UNKNOWN'".format(self.results[cutter]["sql_col"])
#             for cutter in self.cutters
#             if cutter not in NONCUTTER])))
