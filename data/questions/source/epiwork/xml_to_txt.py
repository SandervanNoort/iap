#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Convert epiwork xml files to readable text"""

from __future__ import division, absolute_import, unicode_literals

import xml.etree.ElementTree as ET
import re
import collections
import os
import codecs
import sys  # pylint: disable=W0611
import io

pat = re.compile(r"\{.*\}(.*)")


class EpiXml:
    """Class which read xml questionnaires from epiwork"""

    def __init__(self, xml_name):
        print("Converting {0}".format(xml_name))
        self.xml_name = xml_name
        with io.open(self.xml_name, "r") as fobj:
            contents = fobj.read()
        self.tree = ET.fromstring(re.sub("xmlns=", "_xmlns=", contents))
        self.trans = self.get_trans()

    @staticmethod
    def get_tag(elem):
        """Get value for elem, without the namespace"""
        result = pat.search(elem.tag)
        return result.group(1) if result else elem.tag

    def get_trans(self):
        """Get translations from """

        trans = collections.defaultdict(dict)
        for translation in self.tree.findall("translations/translation"):
            lang = translation.get("lang")
            for question in translation.find("questions"):
                ref = question.get("ref")
                value = question.find("title").text
                trans[lang][ref] = value
            for option in translation.find("options"):
                ref = option.get("ref")
                value = option.find("text").text
                trans[lang][ref] = value
        return trans

    def write_survey(self, lang=None):
        """Return the survey"""

#             print "  => {0}".format(txt_name)
        basename = os.path.splitext(os.path.basename(self.xml_name))[0]
        if lang is not None:
            basename = "{0}_{1}".format(lang, basename)
            trans = self.trans[lang]
        txt_name = os.path.join(os.path.dirname(self.xml_name),
                                basename + ".txt")

        fobj = codecs.open(txt_name, "w", "utf-8")
        for question in self.tree.findall("questions/question"):
            question_id = question.get("id")
            question_type = question.find("type").text
            data_name = question.find("data_name").text
            title = question.find("title").text

            if lang is not None and question_id in trans:
                title = trans[question_id]

            if (question_type in ("multiple-choice", "single-choice",
                                  "matrix-select")
                    and len(question.findall("options/option")) == 0):
                continue
            fobj.write("{0}: {1}\n".format(data_name, title))

            for option in question.findall("options/option"):
                option_id = option.get("id")
                value_elem = option.find("value")
                if value_elem is None:
                    continue
                value = value_elem.text
                answer = option.find("text").text
                if lang is not None and option_id in trans:
                    answer = trans[option_id]
                fobj.write("{0:>4s}: {1}\n".format(value, answer))
            if question_type == "builtin":
                fobj.write("  builtin\n")
            elif question_type == "text":
                fobj.write("  {0}\n".format(question.find("data_type").text))
            fobj.write("\n")
        fobj.close()

    def convert(self):
        """Convert xml to txt files"""
        self.write_survey()
        for lang in self.trans.keys():
            self.write_survey(lang)


if __name__ == "__main__":
    xml = EpiXml("intake_2012.xml")
    xml.convert()
    for dirpath, dirnames, fnames in os.walk("."):
        for fname in fnames:
            if os.path.splitext(fname)[1] == ".xml":
                xml = EpiXml(os.path.join(dirpath, fname))
                xml.convert()
