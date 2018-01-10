#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Split the participants by their intake questionnaire"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import re
import sys  # pylint: disable=W0611

from .exceptions import IAPError
from . import config, utils, tools

SPECIAL_KEYS = ("type", "country", "reference", "nohist")


def set_full(options):
    """Set the full cutter/answer"""

    options["full_cutter"] = combine(
        options["cutter"], options["city_cutter"], options["age_cutter"])

    if (options["full_cutter"] != "" and
            options["survey_cutter"] != ""):
        raise IAPError(tools.Format(
            "full_cutter {full_cutter} and" +
            " survey_cutter ({survey_cutter})" +
            " cannot be both non-empty").format(extra=options))

    options["full_answer"] = combine(
        options["answer"], options["city_answer"], options["age_answer"])


def get_period_cutter(cutter, period):
    """Get cutter if it is fixed to a period"""
    if config.SEP["period_cutter"] in cutter:
        cutter, cutter_in = cutter.split(config.SEP["period_cutter"])
        country, season = utils.period_to_country_season(period)
        if cutter_in in (country, season, period):
            return cutter
        else:
            return None
    else:
        return cutter


def get_answers(cutter, period):
    """Return the cutters + answers"""

    if config.SEP["cutter"] in cutter:
        return get_answers_double(cutter, period)

    cutter = get_period_cutter(cutter, period)
    if cutter is None:
        cutters, answers = [], []
    elif (cutter in config.TABLE["intake"] and
          config.TABLE["intake"][cutter]["type"] == "checkbox"):
        answers = get_intakes(cutter, period)[0]
        if "n" in answers:
            answers.remove("n")
        cutters = ["{0}_{1}".format(cutter, answer)
                   for answer in answers]
        answers = len(answers) * ["1"]
    else:
        answers = get_intakes(cutter, period)[0]
        cutters = len(answers) * [cutter]

    return cutters, answers


def get_answers_double(cutter, period):
    """When the cutter has multiple parts"""

    cutters = None
    answers = None
    for sub_cutter in cutter.split(config.SEP["cutter"]):
        sub_cutters, sub_answers = get_answers(sub_cutter, period)
        if cutters is None:
            answers = sub_answers
            cutters = sub_cutters
        else:
            cutters = [config.SEP["cutter"].join([old, new])
                       for old in cutters
                       for new in sub_cutters]
            answers = [config.SEP["cutter"].join([old, new])
                       for old in answers
                       for new in sub_answers]
    return cutters, answers


def get_intakes(cutter, period):
    """Return labels, pieces, intakes for a cutter"""

    cache = tools.Cache()
    if config.SEP["cutter"] in cutter:
        return get_intakes_double(cutter, period)

    cutter = get_period_cutter(cutter, period)
    if cutter is None:
        answers, intakes = [], []
    elif "=>" in cutter:
        answers, intakes = get_intakes_value(cutter)
    elif cutter in config.TABLE["intake"]:
        answers, intakes = get_intakes_intake(cutter, period)
    elif cutter in config.TABLE["cutter"]:
        qobj = config.TABLE["cutter"][cutter]
        answers, intakes = get_intakes_cutter(qobj, period)
    elif cache(re.match(r"^(.*)_(\d+|n|o|d)$", cutter)):
        cutter, answer = cache.output.groups()
        answers, intakes = get_intakes_sub(cutter, answer, period)
    elif cache(re.match(r"sql\((.*)\)$", cutter)):
        sql = cache.output.group(1)
        intakes = [sql] + ["NOT({0})".format(sql)]
        answers = ["1", "2"]
    else:
        raise IAPError("Unknown cutter: {0}".format(cutter))

#     if overlap:
#         pieces = [labels_to_piece(label_set)
#                   for label_set in tools.get_subsets(labels)]
#         intakes = [" AND ".join(intake_set)
#                    for intake_set in tools.get_subsets(intakes)]
#         intakes[intakes.index("")] = "1=1"
#     else:
#         # pieces = labels + ["0"]
#         # intakes.append("1=1")
#         pieces = labels

    return answers, intakes


def get_intakes_value(cutter):
    """Split up by specific values"""

    var, value_string = cutter.split("=>", 1)

    # remove the syntax for default value
    value_string = re.sub(r"\[(.*)\]", r"\1", value_string)

    values = value_string.split("-")
    min_val = values.pop(0)
    intakes = []
    labels = []

    for max_val in values:
        intakes.append(("{var}<{max_val}" if min_val == "min" else
                        "{var}>={min_val}" if max_val == "max" else
                        "{var}>={min_val} AND {var}<{max_val}").format(
                            var=var, min_val=min_val, max_val=max_val))
        labels.append(min_val + config.SEP["range"] + max_val)
        min_val = max_val

    return labels, intakes


def get_intakes_cutter(section, period):
    """Return all labels/keys for a section"""
    country = "country" in section and section["country"]
    for sub_section in section.sections:
        if period in sub_section.split("-"):
            section = section[sub_section]
            break
    answers = [answer for answer in section.scalars
               if answer not in SPECIAL_KEYS]
    if country:
        country = utils.period_to_country_season(period)[0]
        answers = [answer for answer in answers
                   if answer.startswith(country)]
    intakes = [section[answer] for answer in answers]
    return answers, intakes


def get_intakes_intake(cutter, period):
    """Return all labels/keys if cutter is an intake question"""
    qobj = config.TABLE["intake"][cutter]
    if qobj["type"] in ("radio", "checkbox"):
        columns = utils.get_columns(
            utils.get_tbl("intake", "new", period))
        answers = [column[len(cutter) + 1:]
                   for column in columns
                   if column.startswith(cutter + "_")]
        intakes = ["{0}_{1}".format(cutter, answer)
                   for answer in answers]
    else:
        answers, intakes = get_intakes_free(cutter, period)

    return answers, intakes


def get_intakes_sub(cutter, answer, period):
    """Get intakes when cutter of the form <cut>_<answer>"""

    answers = ["1", "2"]
    if cutter in config.TABLE["intake"]:
        intakes = ["{0}_{1}".format(cutter, answer),
                   "NOT({0}_{1})".format(cutter, answer)]
    elif cutter in config.TABLE["cutter"]:
        all_answers, all_intakes = get_intakes(cutter, period)
        if answer in all_answers:
            intake = all_intakes[all_answers.index(answer)]
            intakes = [intake, "NOT({0})".format(intake)]
        else:
            raise IAPError(
                "Unknown answer {answer} for cutter {cutter}".format(
                    answer=answer, cutter=cutter))
    else:
        raise IAPError("Unknown cutter: {0}".format(cutter))
    return answers, intakes


def get_intakes_free(cutter, period):
    """Split up by question with free value"""

    tbl_intake = utils.get_tbl("intake", "new", period)
    if cutter not in utils.get_columns(tbl_intake):
        return [], []

    query = """
        SELECT
            DISTINCT {col} as val
        FROM
            {tbl_intake}
        ORDER BY
            {col}
        """.format(tbl_intake=tbl_intake, col=cutter)
    cursor = utils.query(query)
    answers = ["{0}".format(row["val"]) for row in cursor.fetchall()]
    intakes = [("{0} IS NULL" if answer == "None" else
                "IFNULL({0}, 'None')='{1}'").format(cutter, answer)
               for answer in answers]
    return answers, intakes


def get_intakes_double(cutter, period):
    """Full crossover of two cutters"""

    answers = None
    intakes = None
    for sub_cutter in cutter.split(config.SEP["cutter"]):
        sub_answers, sub_intakes = get_intakes(sub_cutter, period)
#         if sub_labels is None:
#             sub_labels = ["FREE"]
#             sub_pieces = ["FREE"]
#             sub_intakes = ["1=1"]

        if answers is None:
            answers = sub_answers
            intakes = sub_intakes
        else:
            answers = [config.SEP["cutter"].join([old, new])
                       for old in answers
                       for new in sub_answers]
            intakes = [
                "{old} AND {new}".format(
                    old=tools.sql_bracket(old),
                    new=tools.sql_bracket(new))
                for old in intakes
                for new in sub_intakes]
    return answers, intakes


def get_reference(cutter):
    """Return the reference label"""
    cache = tools.Cache()
    if config.SEP["period_cutter"] in cutter:
        cutter = cutter.split(config.SEP["period_cutter"])[0]
        reference = get_reference(cutter)
    elif (cutter in config.TABLE["cutter"] and
          "reference" in config.TABLE["cutter"][cutter]):
        reference = config.TABLE["cutter"][cutter]["reference"]
    elif (cutter in config.TABLE["intake"] and
          "reference" in config.TABLE["intake"][cutter]):
        reference = config.TABLE["intake"][cutter]["reference"]
    elif re.match(r"^(.*)_(\d+|n|o|d)$", cutter):
        reference = "2"
    # elif re.match(r"q[\d]+_[\da-z]+$", cutter):
    #     reference = "2"
    elif "=>" in cutter:
        if cache(re.search(r"\[(.*)\]", cutter)):
            min_val, max_val = cache.output.group(1).split("-")
            reference = min_val + config.SEP["range"] + max_val
        else:
            reference = "1"
    else:
        reference = "1"
    return reference


def get_intake(cutter):
    """Return the intake sql for a cutter"""

    cache = tools.Cache()

    if config.SEP["period_cutter"] in cutter:
        cutter = cutter.split(config.SEP["period_cutter"])[0]
        intake = get_intake(cutter)

    if cache(re.match(r"^(.*)_(\d+|n|o|d)$", cutter)):
        cutter = cache.output.group(1)

    if (cutter in config.TABLE["cutter"] and
            "intake" in config.TABLE["cutter"][cutter]):
        intake = config.TABLE["cutter"][cutter]["intake"]
    elif (cutter in config.TABLE["intake"] and
          "intake" in config.TABLE["intake"][cutter]):
        intake = config.TABLE["intake"][cutter]["intake"]
    else:
        intake = ""
    return intake


def get_range_label(cutter, answer, settings):
    """Return the label for a range"""

    min_val, max_val = answer.split(config.SEP["range"])
    try:
        max_val = int(max_val)
        max_val_1 = max_val - 1
    except ValueError:
        max_val_1 = max_val
    answers = get_answers(cutter, None)[1]

    if settings is None:
        settings = {
            "first_range": "{min_val}-{max_val_1}",
            "last_range": "{min_val}-{max_val_1}",
            "last_range_max": "{min_val}+",
            "full_range": "{min_val}-{max_val_1}"}

    label = (settings["last_range_max"] if max_val == "max" else
             settings["first_range_min"] if min_val == "min" else
             "{min_val}" if int(min_val) == max_val_1 else
             settings["first_range"] if answers[0] == answer else
             settings["last_range"] if answers[-1] == answer else
             settings["full_range"]).format(
                 min_val=min_val, max_val=max_val, max_val_1=max_val_1)

    return label


def get_answer_label(cutter, answer, settings=None):
    """Return answer label"""
    cache = tools.Cache()

    if config.SEP["cutter"] in cutter:
        return " <<extra:and>> ".join([
            get_answer_label(sub_cutter, sub_answer, settings)
            for (sub_cutter, sub_answer) in
            zip(cutter.split(config.SEP["cutter"]),
                answer.split(config.SEP["cutter"]))])

    if config.SEP["period_cutter"] in cutter:
        cutter, cutter_in = cutter.split(config.SEP["period_cutter"])
        return "{0} in {1}".format(
            get_answer_label(cutter, answer, settings), cutter_in)
    if "=>" in cutter:
        label = get_range_label(cutter, answer, settings)
    elif answer == "0":
        label = "<<extra:none>>"
    elif answer == "all":
        label = "<<extra:all>>"
#     elif "&" in answer:
#         label = " <<extra:and>> ".join([
#             get_answer_label(cutter, sub_answer, settings)
#             for sub_answer in answer.split("&")])
    elif cutter in config.TABLE["intake"]:
        label = "<<intake_{0}:{1}>>".format(cutter, answer)
    elif cutter in config.TABLE["cutter"]:
        label = "<<cutter_{0}:{1}>>".format(cutter, answer)
    elif cache(re.match(r"^(.*)_(\d+|n|o|d)$", cutter)):
        label = get_answer_label(*cache.output.groups())
        if answer == "2":
            label = "<<extra:not>> " + label
    elif re.match(r"^sql\(.*\)$", cutter):
        label = "<<extra:yes>>" if answer == "1" else "<<extra:no>>"
    else:
        raise IAPError("Unknown cutter: {0}".format(cutter))

    return label


def get_all(cutter):
    """Get the answer for all (denominator)"""
    return config.SEP["cutter"].join(
        len(cutter.split(config.SEP["cutter"])) * ["all"])


def get_labels(cutter, answer, period):
    """Return all answers, substituting "all" in the answers"""

    if config.SEP["cutter"] in cutter:
        return get_labels_double(cutter, answer, period)

    if answer == "all":
        labels = get_answers(cutter, period)[1]
    else:
        labels = [answer]
    return labels


def get_labels_double(cutter, answer, period):
    """When the cutter has multiple parts"""

    answers = None
    for sub_cutter, sub_answer in zip(cutter.split(config.SEP["cutter"]),
                                      answer.split(config.SEP["cutter"])):
        sub_answers = get_labels(sub_cutter, sub_answer, period)
        if answers is None:
            answers = sub_answers
        else:
            answers = [config.SEP["cutter"].join([old, new])
                       for old in answers
                       for new in sub_answers]
    return answers


def get_cutter_label(cutter):
    """Return question title"""
    cache = tools.Cache()

    if config.SEP["cutter"] in cutter:
        label = " <<extra:by>> ".join(
            [get_cutter_label(sub_cutter)
             for sub_cutter in cutter.split(config.SEP["cutter"])])
    elif config.SEP["period_cutter"] in cutter:
        cutter, cutter_in = cutter.split(config.SEP["period_cutter"])
        return "{0} in {1}".format(get_cutter_label(cutter), cutter_in)
    elif "=>" in cutter:
        cutter = cutter.split("=>", 1)[0]
        label = "<<intake_{0}:title>>".format(cutter)
    elif cutter in config.TABLE["intake"]:
        label = "<<intake_{0}:title>>".format(cutter)
    elif cutter in config.TABLE["cutter"]:
        label = "<<cutter_{0}:title>>".format(cutter)
    elif cache(re.match(r"^(.*)_(\d+|n|o|d)$", cutter)):
        question = cache.output.group(1)
        label = "<<intake_{0}:title>>".format(question)
    elif re.match(r"^sql\(.*\)$", cutter):
        label = re.match(r"^sql\((.*)\)$", cutter).group(1)
    else:
        raise IAPError("Unknown cutter: {0}".format(cutter))

    return label


def combine(*labels):
    """Combine city_label and label"""
    return config.SEP["cutter"].join(label for label in labels if label != "")
    # return re.sub("^_+|_+$", "", label)


def get_sql(cutter, period):
    """Get the sql for the cutter"""
    if cutter == "":
        return "''"

#     if period in ("nl11", "nl12", "pt10") and cutter == "q1100":
#         return "'EMPTY'"

    answers, intakes = get_intakes(cutter, period)

    if len(intakes) == 0:
        return "'UNKNOWN'"  # cutter

    def substitute_var(match):
        """Subtitute for example q500[1-2] by sql"""
        cutter, value_string = match.groups()
        values = value_string.split("-")
        answers, intakes = get_intakes(cutter, period)
        if len(intakes) == 0:
            return "False"

        sql = tools.sql_bracket(
            " OR ".join([tools.sql_bracket(intake)
                         for answer, intake in zip(answers, intakes)
                         if answer in values]))
        return sql

    # recursively replace <cutter>[answer1-answer2-..]
    orig_intakes = None
    while orig_intakes != intakes:
        orig_intakes = intakes
        intakes = [re.sub(r"([a-z0-9_]*)\[(.*?)\]", substitute_var, intake)
                   for intake in intakes]

    intakes_answers = [(intake, answer)
                       for intake, answer in zip(intakes, answers)
                       if intake not in ("", "NOT()")]
    intakes, answers = (zip(*intakes_answers) if len(intakes_answers) > 0 else
                        ([], []))
    intakes = [utils.check_db(intake, period)
               for intake in intakes]

    if len(set(intakes)) <= 1:
        return "'UNKNOWN'"

    sql = "'MULTIPLE'"
    for answer, intake in zip(answers, intakes):
        # match = pat.search(piece)
        # while match:
        #     piece = "CONCAT('{0}', {1}, '{2}')".format(*match.groups())
        #     sql_string = True
        #     match = pat.search(piece)
        # if not sql_string:
        #     piece = "\"{0}\"".format(piece)
        sql = sql.replace(
            "'MULTIPLE'",
            "IF({intake} AND NOT({other}), '{answer}', 'MULTIPLE')".format(
                intake=tools.sql_bracket(intake),
                answer=answer,
                other=" OR ".join([
                    tools.sql_bracket(other_intake)
                    for other_intake in intakes
                    if other_intake != intake])))
    sql = sql.replace(
        "'MULTIPLE'",
        "IF(NOT({other}), 'NONE', 'MULTIPLE')".format(
            other=" OR ".join([tools.sql_bracket(intake)
                               for intake in intakes])))

    return sql


def show_hist(cutter, answer):
    """To show the cutter in a histogram"""

    if config.SEP["cutter"] in cutter:
        for sub_cutter, sub_answer in zip(
                cutter.split(config.SEP["cutter"]),
                answer.split(config.SEP["cutter"])):
            if not show_hist(sub_cutter, sub_answer):
                return False
        return True

    if cutter in config.TABLE["cutter"]:
        if ("nohist" in config.TABLE["cutter"][cutter] and
                answer in config.TABLE["cutter"][cutter]["nohist"]):
            return False
    elif cutter in config.TABLE["intake"]:
        if ("nohist" in config.TABLE["intake"][cutter] and
                answer in config.TABLE["intake"][cutter]["nohist"]):
            return False

    return True
