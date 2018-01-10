#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Read configuration files"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import os
import re
import io
import logging
import six
import configobj

import pyfig

from . import split, config, utils, tools
from .exceptions import IAPError

logger = logging.getLogger(__name__)


class IniBase(object):
    """Class to load the ini files"""
    # not allow samples_period

    def __init__(self, ini_input, settings=False):
        if isinstance(ini_input, configobj.ConfigObj):
            inifile = ini_input
        elif isinstance(ini_input, io.StringIO):
            inifile = ini_input
            inifile.seek(0)
        elif isinstance(ini_input, six.string_types):
            if os.path.exists(ini_input):
                inifile = io.open(ini_input, "r", encoding="utf8")
            else:
                inifile = io.BytesIO()
                ini_input = re.sub(r" *\\\n *", " ", ini_input)
                inifile.write(ini_input.encode("utf8"))
                inifile.seek(0)
        try:
            self.settings = configobj.ConfigObj(
                inifile,
                configspec=os.path.join(config.CONFIG_DIR, "settings.spec"),
                file_error=True)
        except configobj.DuplicateError as inst:
            inifile.seek(0)
            raise IAPError(
                "".join(["{0:>3d}. {1}".format(line_no + 1, line)
                         for line_no, line in enumerate(inifile)]) +
                "Duplicate key in ini: {0}".format(inst))
        except configobj.ConfigObjError as inst:
            inifile.seek(0)
            raise IAPError(
                "".join(["{0:>3d}. {1}".format(line_no + 1, line)
                         for line_no, line in enumerate(inifile)]) +
                "Parsing error in ini: {0}".format(inst))
        try:
            self.settings.configspec["fig"].merge(configobj.ConfigObj(
                os.path.join(pyfig.config.CONFIG_DIR, "settings.spec"),
                _inspec=True))
            tools.cobj_check(self.settings, exception=IAPError)
        except IAPError as error:
            raise IAPError(
                "\n".join(["{0:>3d}. {1}".format(line_no + 1, line.rstrip())
                           for line_no, line in enumerate(inifile)]) +
                "\n\n{0}".format(error))

        # self.ini_obj = io.BytesIO()
        # self.settings.write(self.ini_obj)

        self.datasets = self.settings["datasets"]
        if not settings:
            if len(self.datasets.sections) > 0:
                self.update_multiple()
                self.update_extra()
                self.update_period()
                self.update_cutter()
            if len(self.datasets.sections) > 0:
                self.update_subsets()
                self.update_missing()
                self.update_intake()
                self.update_labels()
                # error with snapshot: string=>date
                # tools.cobj_check(
                #    self.settings, exception=IAPError, copy=True)

    def write(self, ininame):
        """Write the INI file to the same directory as the image file"""

        fname = "{0}.ini".format(ininame)
        # new_content = self.ini_obj.getvalue()
        tools.create_dir(fname)
        with io.open(fname, "wb") as fobj:
            self.settings.write(fobj)
            # fobj.write(new_content)

    def update_missing(self):
        """Some data is missing from the database"""
        for options in self.datasets.values():
            if not options["expand"]:
                continue
            # subgroup who participated in gastronet
            if options["period"] == "pt08":
                if (
                        ("s100_13" in options["casedef"] or
                         (options["measure"] == "control" and
                          "s100_13" in options["control"])) or
                        ("s100_7" in options["casedef"] or
                         (options["measure"] == "control" and
                          "s100_7" in options["control"])) or
                        ("s100_9" in options["casedef"] or
                         (options["measure"] == "control" and
                          "s100_9" in options["control"])) or
                        ("s100_8" in options["casedef"] or
                         (options["measure"] == "control" and
                          "s100_8" in options["control"]))):
                    options["intake"] += tools.sql_and(
                        options["intake"], "nogastro=0")

            if (options["measure"] == "control" and
                    options["src"] == "nb09" and
                    "s300" in options["control"]):
                # first survey done with good gp on 2009/10/24
                options["date_range"] = "2009/10/25-"
            if (options["measure"] == "control" and
                    options["src"] == "nb08" and
                    "s300" in options["control"]):
                # latest survey done with good gp on 2009/6/24
                options["date_range"] = "-2009/6/14"

            if (options["measure"] == "control" and
                    options["period"] == "pt09" and
                    ("s300" in options["control"] or
                     "s400" in options["control"])):
                # last on 2 dec 2009
                # first on 8 jan 2010
                options["date_range"] = "-2009/11/22,2010/01/09-"

    def update_subsets(self):
        """Set the subset of a country"""

        for plotname, options in self.datasets.items():
            if not options["expand"]:
                continue
            if options["subset"] == "" or options["subset_label"] != "":
                continue
            if options["period"] is None:
                options["subset"] = ""
                continue

            match = re.search(r"([a-z0-9_]*)\[(.*?)\]", options["subset"])
            if not match:
                raise IAPError("Unparsable subset: {0}".format(
                    options["subset"]))
            cutter, answer = match.groups()
            answers, intakes = split.get_intakes(cutter, options["period"])
            if answer in answers:
                options["intake"] = tools.sql_and(
                    options["intake"],
                    intakes[answers.index(answer)])
                options["subset_label"] = split.get_answer_label(
                    cutter, answer)
            else:
                del self.datasets[plotname]

    def update_extra(self):
        """Some sane defaults for options"""
        # (too many branches) pylint: disable=R0912

        for options in self.datasets.values():
            if not options["expand"]:
                continue
            options["snapshot"] = (None if options["snapshot"] == "" else
                                   utils.get_date(options["snapshot"]))

            if "source_measure" in options:
                try:
                    options["source"], options["measure"] = \
                        options["source_measure"].split("_")
                except ValueError:
                    raise IAPError("Unknown source_measure: {0}".format(
                        options["source_measure"]))
            elif "source" in options and "measure" in options:
                options["source_measure"] = tools.Format(
                    "{source}_{measure}").format(extra=options)
            else:
                raise IAPError("No source_measure supplied")
            if (options["source_measure"] in ("inet_incidence",
                                              "inet_control",
                                              "inet_reporting") and
                    options["limits"] == "incidence"):
                options["limits"] = "hide"

            if options["measure"] == "control":
                options["min_participants"] = 0
            else:
                options["control_days"] = 0
            if options["measure"] == "participants":
                options["always_active"] = True
                options["first_survey"] = 1
                options["max_freq"] = 0
            if options["measure"] == "surveys":
                options["casedef"] = ""
                if "surveys" in options["intake"]:
                    logger.warning("inet_surveys with intake: {0}".format(
                        options["intake"]))
                options["onset"] = "survey"
                options["ignore_double"] = False
                options["ignore_multiple"] = False
                options["first_survey"] = 1
                options["last_survey"] = 0
                options["max_freq"] = 0
            if options["ax_name"] == "":
                options["ax_name"] = options["source_measure"]
            if options["source"] == "combi":
                options["daily"] = False
#             if options["daily"]:
#                 options["marker"] = ""
            if options["season"] == "2013/14":
                options["samples_period"] = 0

    def update_period(self):
        """Add the options["period"]"""

        for plotname, options in self.datasets.items():
            if not options["expand"]:
                continue
            if options["source"] == "europe":
                options["period"] = None
                options["src"] = None
                continue
            options["period"] = utils.country_season_to_period(
                options["country"], options["season"])
            try:
                options["src"] = utils.period_to_src(options["period"])
            except IAPError:
                options["src"] = None
            if ((options["source"] == "inet" or options["inet_only"]) and
                    not utils.period_available(options["period"])):
                del self.datasets[plotname]

    def update_multiple(self):
        """Create multiple datasets when country, season or source
           are lists"""
        # (too many branches) pylint: disable=R0912

        for key in ["source_measure", "country", "season",
                    "cutter", "city_cutter", "casedef", "intake", "control",
                    "answer", "city_answer"]:
            for plotname, options in self.datasets.items():
                if not options["expand"]:
                    continue
                if "{0}_values".format(key) in options:
                    size = len(options["{0}_values".format(key)])
                    if size == 0:
                        continue

                    values = {}
                    for ltype in ["values", "labels", "ids"]:
                        subkey = "{0}_{1}".format(key, ltype)
                        values[ltype] = (list(options[subkey])
                                         if subkey in options else
                                         size * [None])
                        if subkey in options:
                            del options[subkey]

                    index = self.datasets.sections.index(plotname)
                    for value, label, myid in zip(
                            reversed(values["values"]),
                            reversed(values["labels"]),
                            reversed(values["ids"])):

                        new_plotname = "{0}_{1}".format(plotname, value)
                        new_options = tools.deepcopy(options)
                        if key == "intake":
                            if value != "":
                                new_options["intake"] = tools.sql_and(
                                    new_options["intake"],
                                    "({0})".format(value))
                        else:
                            new_options[key] = value
                        if label is not None:
                            new_options["{0}_label".format(key)] = label
                        if myid is not None:
                            new_options["{0}_id".format(key)] = myid

                        self.datasets[new_plotname] = new_options
                        self.datasets.sections.insert(index + 1, new_plotname)
                        self.datasets.sections.pop()
                    del self.datasets[plotname]
                    # del self.datasets.sections[index]

    def update_cutter(self):
        """Split the datasets up by cutter and city_cutter"""

        self.split_cutter("cutter", "answer")
        self.split_cutter("city_cutter", "city_answer")
        for options in self.datasets.values():
            if not options["expand"]:
                continue
            split.set_full(options)

    def split_cutter(self, cutter_key, answer_key):
        """Split the source up by the cutter"""

        for plotname, options in self.datasets.items():
            if not options["expand"]:
                continue
            if (options["source"] not in ("inet", "europe") or
                    options[cutter_key] == "" or
                    options[answer_key] != ""):
                continue
            #  try:
            cutters, answers = split.get_answers(
                options[cutter_key], options["period"])
            # except IAPError:
            #     options[cutter_key] = ""
            #     continue
            index = self.datasets.sections.index(plotname)
            offset = 0
            for cutter, answer in zip(cutters, answers):
                new_plotname = "{0}_{1}_{2}".format(plotname, cutter, answer)
                new_options = options.dict()
#                 if (new_options["color"] == "mix" and
#                         answer in config.CONFIG["colors"]):
#                     new_options["color"] = config.CONFIG["colors"][answer]
                new_options[cutter_key] = cutter
                new_options[answer_key] = answer
                new_options["intake"] = tools.sql_and(
                    new_options["intake"],
                    split.get_intake(options[cutter_key]))

                self.datasets[new_plotname] = new_options
                self.datasets.sections.insert(
                    index + 1 + offset, new_plotname)
                self.datasets.sections.pop()
                offset += 1
            if len(cutters) > 0:
                del self.datasets.sections[index]

    def update_intake(self):
        """Update intake based on other options"""

        for options in self.datasets.values():
            if not options["expand"]:
                continue
            if options["min_surveys"] > 0:
                options["intake"] = tools.sql_and(
                    options["intake"],
                    "surveys>='{0}'".format(options["min_surveys"]))
            if options["max_freq"] > 0 and options["min_surveys"] > 0:
                options["intake"] = tools.sql_and(
                    options["intake"],
                    "freq<='{0}'".format(options["max_freq"]))

            if options["active_before"] != "":
                options["intake"] = tools.sql_and(
                    options["intake"],
                    "start_date<='{0}'".format(
                        utils.get_date(
                            options["active_before"], options["season"])))
            if options["active_after"] != "":
                options["intake"] = tools.sql_and(
                    options["intake"],
                    "end_date>='{0}'".format(
                        utils.get_date(
                            options["active_after"], options["season"])))

    def get_extra(self, label, labeltype, options):
        """Return a label of the value"""

        value, direct, _key = utils.get_direct(label, options)
        if label == "measure" and value == "control":
            extra = ""
        elif value == "":
            extra = ""
        elif (label == "source" and value == "inet" and
              labeltype == "title"):
            # Influenzanet not in title
            extra = ""
        elif direct:
            extra = value
        elif label in ("city_answer", "answer"):
            cutter = "city_cutter" if label.startswith("city_") else "cutter"
            cutter = options[cutter]
            extra = split.get_answer_label(cutter, value, self.settings["fig"])
        elif label in ("cutter", "city_cutter"):
            # get cutter title
            extra = split.get_cutter_label(value)
        elif label == "season" and self.settings["fig"]["short"] is True:
            # short season form for bar plots
            extra = ("<<season:short_{0}>>".format(value)
                     if labeltype == "citylabel" else
                     "<<season:slash_{0}>>".format(value))
        elif "<<" in value:
            extra = value
        elif label == "country" and options["extra_countries"] != []:
            extra = " <<extra:and>> ".join(
                ["<<{0}:{1}>>".format(label, value)] +
                ["<<{0}:{1}>>".format(label, value)
                 for value in options["extra_countries"]])
        else:
            extra = "<<{0}:{1}>>".format(label, value)
        return extra

    def get_label(self, labels, options, labeltype="label"):
        """Add some extra keys to a label"""

        extra_dict = {}
        for label in labels:
            if ((labeltype == "label" and
                 (label.startswith("city_") or
                  label in self.settings["fig"]["city_labels"])) or
                    (labeltype == "citylabel" and
                     not (label.startswith("city_") or
                          label in self.settings["fig"]["city_labels"]))):
                continue

            extra = self.get_extra(label, labeltype, options)
            if extra != "":
                # put some extra words around it
                if label == "season" and "country" in labels:
                    # season in brackets if country in label
                    extra = "({0})".format(extra)
                if label == "control" and "casedef" in labels:
                    # <gp/home> rate with <disease>
                    extra = "{0} <<extra:with>>".format(extra)

                if (label == "city_cutter" and
                        "city_answer" not in labels):
                    extra = ("{0} <<extra:distribution>>".format(extra)
                             if ("cutter" not in labels and
                                 "measure" not in labels) else
                             "<<extra:by>> {0}".format(extra))
                if (label == "cutter" and
                        "answer" not in labels and
                        "measure" in labels):
                    extra = "<<extra:by>> {0}".format(extra)

                if ((label == "city_cutter" and "city_answer" in labels) or
                        (label == "cutter" and "answer" in labels)):
                    extra = "{0}: ".format(extra)

            extra_dict[label] = extra

        labelfmt = ("{subset} {country} {extra_country} {season}\n" +
                    "{subtitle} {control} {source} {casedef} {measure}" +
                    " {cutter} {answer} {city_cutter} {city_answer}"
                    if labeltype == "title" else
                    "{answer} {city_answer} {control} {source}" +
                    " {casedef} {measure} {subset} {country} {season}")

        if ("subset" in extra_dict and "country" in extra_dict and
                extra_dict["subset"] != ""):
            del extra_dict["country"]

        label = tools.Format(labelfmt, default="").format(extra=extra_dict)

        # strip, removing space,newline,colom from both sides
        label = re.sub("^[\n :]+|[\n :]+$", "", label)

        # remove double spaces
        label = re.sub(" +", " ", label)
        return label

    def update_labels(self):
        """Update the extra items of all labels"""

        labels = set(self.settings["fig"]["legend_labels"])
        title_labels = set()

        if len(self.settings["fig"]["datasets"]) > 0:
            keys = self.settings["fig"]["datasets"]
        else:
            keys = set()
            for plot_settings in self.settings["plots"].values():
                if len(plot_settings["datasets"]) > 0:
                    keys.update(plot_settings["datasets"])
                else:
                    keys = set()
                    break
        datasets = (utils.get_datasets_keys(self.datasets, keys)
                    if len(keys) > 0 else
                    self.datasets)

        for label in ["season", "control", "country", "subset",
                      "cutter", "city_cutter", "answer", "city_answer",
                      "source", "measure", "casedef"]:
            if (label in self.settings["fig"]["legend_labels"] or
                    label in self.settings["fig"]["sum_labels"] or
                    label in self.settings["fig"]["ignore_labels"]):
                continue
            all_options = tools.SetList()
            for options in datasets.values():
                all_options.append(
                    options["{0}_label".format(label)]
                    if "{0}_label".format(label) in options else
                    options["{0}_id".format(label)]
                    if "{0}_id".format(label) in options else
                    options[label])
            if len(all_options) > 1:
                labels.add(label)
            else:
                title_labels.add(label)

#         if "ili" in title_labels and "measure" in labels:
#             labels.remove("measure")
#         if "control" in labels and "casedef" not in labels:
#             labels.add("casedef")
#             title_labels.remove("casedef")
#         if "casedef" in labels and "measure" in title_labels:
#             labels.add("measure")
#             title_labels.remove("measure")

#         together = set(["casedef", "measure", "control"])
#         if len(together.intersection(labels)) > 0:
#             labels = labels.union(together)
#             title_labels -= together

        if "cutter" in labels and "answer" in title_labels:
            labels.add("answer")
            title_labels.remove("answer")
            title_labels.add("cutter")

        self.set_title(title_labels, datasets)
        self.set_labels(labels)

    def set_title(self, title_labels, datasets):
        """Set the title based on the labels"""
        self.settings["fig"]["title_labels"] = list(sorted(
            title_labels.union(
                self.settings["fig"]["title_labels"])))
        title_options = {}

        for label in self.settings["fig"]["title_labels"]:
            extras = tools.SetList()
            for options in datasets.values():
                extras.append(self.get_extra(label, "title", options))
#             while "" in extras:
#                 extras.remove("")
            title_options[label + "_label"] = " <<extra:and>> ".join(
                extra for extra in extras if extra != "")
        for key, value in self.settings["fig"].items():
            if key.endswith("_label") or key.endswith("_id"):
                title_options[key] = value
        if "subtitle" in self.settings["fig"]:
            title_options["subtitle"] = self.settings["fig"]["subtitle"]
            self.settings["fig"]["title_labels"].append("subtitle")

        if self.settings["fig"]["title"] == "auto":
            self.settings["fig"]["title"] = self.get_label(
                self.settings["fig"]["title_labels"],
                title_options, "title")

    def set_labels(self, labels):
        """Set the labels"""

        for options in self.datasets.values():
            if options["label"] == "":
                options["label"] = self.get_label(labels, options)
                csv_labels = list(labels)
                if "season" in csv_labels:
                    csv_labels.remove("season")
                options["csvlabel"] = self.get_label(csv_labels, options)
            else:
                options["csvlabel"] = options["label"]

            if options["citylabel"] == "":
                options["citylabel"] = self.get_label(labels, options,
                                                      "citylabel")
