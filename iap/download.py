#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2013 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Download data from various sources"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import datetime
import re
import os
import zipfile
import gzip
import xml.etree.ElementTree as ET
import socket
import collections
import sys  # pylint: disable=W0611
import logging
import io

from six import StringIO
from six.moves import urllib  # pylint: disable=F0401
from six.moves import http_cookiejar  # pylint: disable=F0401

from .exceptions import IAPError
from . import config, utils, tools

TIMEOUT = 60
MAX_TIMEOUT = 80
REPORTS = ["DINFL03", "DINFL04"]
logger = logging.getLogger(__name__)


def google_download(country):
    """Download data from Google"""

    action = "Google {0}".format(country)
    if country not in config.CONFIG["country"]:
        logger.error("No valid country: {0}".format(country))
        return

    google = utils.get_value(config.CONFIG["country"][country], "google")
    if not google:
        logger.error("Not configured: {0}".format(action))
        return

    logger.info("Downloading: {0}".format(action))
    url = "http://www.google.org/flutrends/intl/en_us/{0}/data.txt".format(
        google)
    logger.debug("Downloading: {0}".format(url))
    google_file = os.path.join(config.LOCAL["dir"]["download"], "google",
                               "{0}.txt".format(country))
    tools.create_dir(google_file)
    try:
        urllib.request.urlretrieve(url, google_file)
    except IOError:
        logger.error("Failed download: {0}".format(action))


def google_fill(country):
    """Fill the table google"""

    action = "Google {0}".format(country)
    google_file = os.path.join(config.LOCAL["dir"]["download"], "google",
                               "{0}.txt".format(country))
    if not os.path.exists(google_file):
        logger.error("Not local: {0}".format(action))
        return

    logger.info("Filling data: {0}".format(action))
    rows = []
    with io.open(google_file, "r") as csvobj:
        reader = tools.ureader(csvobj)
        for line in reader:
            if len(line) > 0 and line[0] == "Date":
                break
        for line in reader:
            date = datetime.datetime.strptime(line[0], "%Y-%m-%d").date()
            if line[1] != "":
                rows.append([country, "google", "", date, line[1]])

    utils.query("""REPLACE INTO other
            (country, source, label, date, value)
        VALUES
            (%s, %s, %s, %s, %s)
        """, rows, many=True)


def eiss_download(period, overwrite=False, timeout=TIMEOUT):
    """Download various eiss data"""
    for report in REPORTS:
        eiss_download_report(period, overwrite, timeout, report)


def eiss_download_report(period, overwrite=False, timeout=TIMEOUT,
                         report="DINFL04"):
    """Download all XML files"""

    country, season = utils.period_to_country_season(period)
    action = "EISS {0} - {1}".format(period, report)
    years = utils.season_to_years(season)
    eiss_season = "{0}/{1:02d}".format(years[0], years[1] % 100)

    if country not in config.CONFIG["country"]:
        logger.error("No valid country: {0}".format(country))
        return

    eiss_country = utils.get_value(
        config.CONFIG["country"][country], "eiss", season)
    if not eiss_country:
        logger.error("Not configured: {0}".format(action))
        return

    eiss_file = os.path.join(
        config.LOCAL["dir"]["download"], "eiss",
        "{period}{extra}.xml".format(
            period=period, extra="" if report == "DINFL04" else "_" + report))

    if os.path.exists(eiss_file) and not overwrite:
        logger.info("Already local: {0}".format(action))
        return

    logger.info("Downloading: {0}".format(action))
    tools.create_dir(eiss_file)
    urllib.request.install_opener(
        urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(
                http_cookiejar.LWPCookieJar())))

    params = (("report", report),
              ("Country", eiss_country),
              ("Season40", eiss_season),
              ("ShowILI", "true"),
              ("ShowARI", "false"))
    url = "{base}?{params}".format(
        base="http://ecdc.europa.eu/_layouts/tessypdf.aspx",
        params=urllib.parse.urlencode(params))

    logger.debug("1st eiss url: {0}".format(url))
    req = urllib.request.Request(url)
    req.add_header('User-agent', 'Mozilla/5.0 (Linux i686)')
    try:
        html = urllib.request.urlopen(
            req, timeout=timeout).read().decode("utf8")
    except (urllib.error.HTTPError,
            urllib.error.URLError, socket.error):
        logger.error("Failed downloading: {0}".format(action))
        return
#     except socket.timeout:
#         if timeout < MAX_TIMEOUT:
#             logger.info("Retrying with {0} timeout".format(timeout * 2))
#             eiss_download(period, overwrite, 2 * timeout)
#         else:
#             logger.error("Timeout downloading: {0}".format(action))
#         return

    match = re.search(r"\"ExportUrlBase\":\"(.*?)\"", html)
    # with io.open("/tmp/eiss.html", "w") as fobj:
    #     fobj.write(html)
    if not match:
        logger.error(("Element ExportUrlBase not found for Tessy html" +
                      " output for: {action}").format(action=action))
        return
    url = "{base}{export}{fileformat}".format(
        base="http://ecdc.europa.eu",
        export=match.group(1).replace("FL03", "FL04"),
        fileformat="XML")

#     params = {"OpType": "Export",
#             "FileName": "test",
#             "ContentDisposition": "OnlyHtmlInline",
#             "Format": "XML"}
#     for var in ["ReportSession", "ControlID", "UICulture", "Culture",
#             "ReportStack", "StreamID"]:
#         if re2.search(r"{0}=([^&\"]*)".format(var), html):
#             params[var] = re2.result.groups()[0]
#         else:
#             logger.error(("Element {var} not found for Tessy html output" +
#                           " for: {action}").format(var=var, action=action))
#             return
#     url = "{base}?{params}".format(
#             base="http://ecdc.europa.eu/Reserved.ReportViewerWebControl.axd",
#             params=urllib.urlencode(params))

    logger.debug("2nd eiss url: {0}".format(url))
    req = urllib.request.Request(url)
    try:
        html = urllib.request.urlopen(
            req, timeout=timeout).read().decode("utf8")
    except (urllib.error.HTTPError, socket.error):
        logger.error("Failed downloading: {0}".format(action))
        return

    with io.open(eiss_file, "w") as fobj:
        fobj.write(html)


def get_eiss_rows(eiss_file, country, season):
    """Get rows from parsing the xml EISS file"""

    prev_week, prev_label = 0, None
    rows = []
    for report, report_label, label, week, value in (
            (report.get("Name"), report.get("textbox6"), line.get("Label"),
             group.get("Label"), group)
            for subreport in ET.parse(eiss_file).getroot()
            for report in subreport
            for chart in report
            for line in chart
            for collection in line
            for group in collection):
        try:
            # sometimes there is a xml-subgroup for the DataValue
            if "DataValue0" in value.keys():
                value = value.get("DataValue0")
            else:
                for subgroup in value:
                    if "DataValue0" in subgroup.keys():
                        value = subgroup.get("DataValue0")
            value = float(value)
            week = int(round(float(week)))
        except (ValueError, TypeError):
            continue

        new_label = (
            config.CONFIG["eiss"][report][label]
            if (report in config.CONFIG["eiss"] and
                label in config.CONFIG["eiss"][report] and
                config.CONFIG["eiss"][report][label] != "") else
            config.CONFIG["eiss"][report][report_label][label]
            if (report in config.CONFIG["eiss"] and
                report_label in config.CONFIG["eiss"][report] and
                label in config.CONFIG["eiss"][report][report_label] and
                config.CONFIG["eiss"][report][report_label][label] != "") else
            None)

        if (country in ("uk", "eng", "sct", "nir", "mt", "lu") and
                new_label in ("ili", "ari")):
            value = value * 1000

        if week < prev_week:
            year = utils.season_to_years(season)[1]
        if label != prev_label:
            year = utils.season_to_years(season)[0]
        try:
            date = tools.year_week_to_date(year, week, IAPError)
        except IAPError:
            # example of fail: baseline of non-existing week 53
            continue

        if new_label is not None:
            rows.append([country, "eiss", date, new_label, int(value)])
        else:
            logger.debug("Not defined: {0} in {1}".format(label, report))
        prev_label, prev_week = label, week
    return rows


def eiss_fill(period):
    """Fill the eiss table"""

    for report in REPORTS:
        action = "EISS {0} {1}".format(period, report)
        country, season = utils.period_to_country_season(period)
        eiss_file = os.path.join(
            config.LOCAL["dir"]["download"], "eiss",
            "{period}{extra}.xml".format(
                period=period,
                extra="" if report == "DINFL04" else "_" + report))
        if not os.path.exists(eiss_file):
            logger.error("Not local: {0}".format(action))
            return
        logger.info("Filling data: {0}".format(action))

        rows = get_eiss_rows(eiss_file, country, season)
        utils.query("""REPLACE INTO other
                (country, source, date, label, value)
            VALUES
                (%s, %s, %s, %s, %s)
            """, rows, many=True)


def geo_download(country, overwrite=False):
    """Download geo data"""

    action = "Zipcodes {0}".format(country)
    if country not in config.CONFIG["country"]:
        logger.error("No valid country: {0}".format(country))
        return

    geo = utils.get_value(config.CONFIG["country"][country], "geo")
    if not geo:
        logger.error("Not configured: {0}".format(action))
        return

    geo_file = os.path.join(config.LOCAL["dir"]["download"], "geo",
                            "{0}.zip".format(country))
    if os.path.exists(geo_file) and not overwrite:
        logger.info("Already local: {0}".format(action))
        return

    logger.info("Downloading: {0}".format(action))
    url = "http://download.geonames.org/export/zip/{0}.zip".format(geo)
    tools.create_dir(geo_file)
    try:
        urllib.request.urlretrieve(url, geo_file)
    except IOError:
        logger.error("Failed download: {0}".format(action))


def geo_fill(country):
    """Fill geo data"""

    action = "Zipcodes {0}".format(country)
    geo_file = os.path.join(config.LOCAL["dir"]["download"], "geo",
                            "{0}.zip".format(country))
    if not os.path.exists(geo_file):
        logger.error("Not local: {0}".format(action))
        return

    logger.info("Filling data: {0}".format(action))

    rows = []
    csvobj = StringIO()
    zipobj = zipfile.ZipFile(geo_file)
    csvobj.write(zipobj.read("{0}.txt".format(
        config.CONFIG["country"][country]["geo"])))
    csvobj.seek(0)

    reader = tools.ureader(csvobj, delimiter="\t")
    lats = collections.defaultdict(list)
    lngs = collections.defaultdict(list)
    for line in reader:
        zipcode = line[1].split("-")[0]
        if line[9] != "" and line[10] != "":
            lats[zipcode].append(float(line[9]))
            lngs[zipcode].append(float(line[10]))
    for zipcode, lat in tools.sort_iter(lats):
        lng = lngs[zipcode]
        rows.append([
            country, zipcode,
            "{0:.2f}".format(sum(lat) / len(lat)),
            "{0:.2f}".format(sum(lng) / len(lng))])

    utils.query("""REPLACE INTO geo
            (country, zipcode, lat, lng)
        VALUES
            (%s, %s, %s, %s)
        """, rows, many=True)


def noaa_stations(overwrite=False):
    """Download NOAA stations data"""

    action = "NOAA stations"
    stations_file = os.path.join(config.LOCAL["dir"]["download"], "noaa",
                                 "stations.txt")
    if os.path.exists(stations_file) and not overwrite:
        logger.info("Already local: {0}".format(action))
        return

    logger.info("Downloading: {0}".format(action))
    tools.create_dir(stations_file)
    url = "ftp://ftp.ncdc.noaa.gov/pub/data/gsod/ish-history.txt"
    try:
        urllib.request.urlretrieve(url, stations_file)
    except IOError:
        logger.error("Failed downloading: {0}".format(action))


def noaa_download(country, year, overwrite=False):
    """Download the NOAA data"""

    action = "NOAA {0}-{1}".format(country, year)
    noaa_file, station = get_noaa_file(country, year)
    if noaa_file is None:
        logger.info("Not configured: {0}".format(action))
        return
    if os.path.exists(noaa_file) and not overwrite:
        logger.info("Already local: {0}".format(action))
        return

    logger.info("Downloading: {0}".format(action))
    tools.create_dir(noaa_file)
#     time.sleep(6)
    url = ("ftp://ftp.ncdc.noaa.gov/pub/data/gsod/{year}/" +
           "{station}-99999-{year}.op.gz").format(station=station, year=year)
    try:
        # urllib.urlretrieve does not close connection
        req = urllib.request.Request(url)
        fdurl = urllib.request.urlopen(req)
        with io.open(noaa_file, "wb") as zipobj:
            zipobj.write(fdurl.read())
        # (access to protected member) pylint: disable=W0212
        try:
            fdurl.fp.fp._sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            print("TODO: force shutdown")
        # (access to protected member) pylint: enable=W0212
    except IOError as err:
        logger.error("Failed download {0}: {1}".format(action, err))


def get_noaa_headers():
    """Get the NOAA headers"""
    header_file = os.path.join(config.LOCAL["dir"]["data"], "noaa_headers.csv")
    if not os.path.exists(header_file):
        return None

    headers = {}
    with io.open(header_file, "r") as fobj:
        fobj.readline()  # ignore header
        for line in fobj:
            if line.startswith(" "):
                continue
            data = line.split()
            if len(data) > 1:
                headers[data[0]] = [int(val) for val in data[1].split("-")]
    return headers


def get_noaa_file(country, year):
    """Get the name of the local noaa file"""

    action = "NOAA {0}-{1}".format(country, year)
    if country not in config.CONFIG["country"]:
        logger.error("No valid country: {0}".format(country))
        return None, None

    station = utils.get_value(
        config.CONFIG["country"][country], "noaa", year)
    if not station:
        logger.error("Not configured: {0}".format(action))
        return None, None

    noaa_file = os.path.join(
        config.LOCAL["dir"]["download"], "noaa",
        "{0}-{1}-{2}.csv.gz".format(country, station, year))
    return noaa_file, station


def noaa_fill(country, year):
    """Fill the noaa table"""

    cache = tools.Cache()
    headers = get_noaa_headers()
    if not headers:
        logger.error("No NOAA headers")
        return

    action = "NOAA {0}-{1}".format(country, year)
    noaa_file, _station = get_noaa_file(country, year)

    if noaa_file is None:
        logger.info("Not configured: {0}".format(action))
        return

    if not os.path.exists(noaa_file):
        logger.error("No local data: {0}".format(action))
        return

    logger.info("Filling data: {0}".format(action))
    rows = []

    fobj = gzip.open(noaa_file, "rt")
    fobj.readline()  # ignore header
    for line in fobj:
        values = {}
        for column in ["YEAR", "MODA", "TEMP", "MAX", "MIN", "DEWP", "PRCP"]:
            values[column] = (line[headers[column][0] - 1: headers[column][1]])
        date = datetime.date(int(values["YEAR"]),
                             int(values["MODA"][0:2]),
                             int(values["MODA"][2:4]))

        if values["TEMP"] != "9999.9":
            temp = tools.fahr_to_celsius(float(values["TEMP"]))
            rows.append([country, "noaa", date, "temp", temp])
        else:
            temp = None

        if cache(re.search(r"([\d\.]+)", values["PRCP"])):
            prcp = float(cache.output.group()) * 25.4
            rows.append([country, "noaa", date, "prcp", prcp])

        if values["PRCP"].endswith("G"):
            values["PRCP"] = values["PRCP"][-1]

        if values["DEWP"] != "9999.9":
            dewp = tools.fahr_to_celsius(float(values["DEWP"]))
            rows.append([country, "noaa", date, "dewp", dewp])
        else:
            dewp = None
        if dewp is not None and temp is not None:
            rows.append([country, "noaa", date, "ahum",
                         1000 * tools.dewp_temp_to_ah(dewp, temp)])
            rows.append([country, "noaa", date, "rhum",
                         100 * tools.dewp_temp_to_rh(dewp, temp)])
    fobj.close()
    utils.query("""REPLACE INTO other
            (country, source, date, label, value)
        VALUES
            (%s, %s, %s, %s, %s)
        """, rows, many=True)


def age_fill():
    """Fill the table age"""
    age_file = os.path.join(config.LOCAL["dir"]["data"], "age_dist.csv")

    if not os.path.exists(age_file):
        logger.error("No age data: {0}".format(age_file))
        return
    logger.info("Fill age data")

    maximum_age = 100
    rows = []
    with io.open(age_file, "r") as csvobj:
        reader = tools.UniDictReader(csvobj)
        for line in reader:
            age_range = line["age"]
            min_age, max_age = re.search(r"Y(.+)_(.+)", age_range).groups()
            if max_age == "MAX":
                max_age = maximum_age
            rows.append([line["geo"].lower(),
                         int(min_age),
                         int(max_age),
                         int(line["INDICATORS_VALUE"])])

    utils.query("""REPLACE INTO age
            (country, min_age, max_age, persons)
        VALUES
            (%s, %s, %s, %s)
        """, rows, many=True)


def fr_fill():
    """Fill the EISS table with french sentinel data"""

    fr_file = os.path.join(config.LOCAL["dir"]["data"], "fr.csv")
    if not os.path.exists(fr_file):
        logger.error("No french data: {0}".format(fr_file))
        return
    logger.info("Fill french data")

    rows = []
    with io.open(fr_file, "r") as csvobj:
        reader = tools.UniDictReader(csvobj)
        for line in reader:
            yearweek = int(line["week"])
            try:
                ili = int(line["inc"])
            except ValueError:
                continue
            year = yearweek // 100
            week = yearweek - 100 * year
            date = tools.year_week_to_date(year, week, IAPError)
            rows.append(["fr", "fr", date, "ILI", ili])

    utils.query("""REPLACE INTO other
            (country, source, date, label, value)
        VALUES
            (%s, %s, %s, %s, %s)
        """, rows, many=True)


def mexico_fill():
    """Mexican flu reports in nl/be"""

    if not utils.table_exists("orig_mexico_nb09"):
        logger.error("No orig mexico data")
        return

    logger.info("Fill mexico data")
    utils.query("""REPLACE INTO other
            (country, source, date, label, value)
        SELECT
            'nlbe'
            ,'mexico'
            ,datum
            ,''
            ,SUM(mexico.300000)
        FROM
            orig_mexico_nb09 AS mexico
        GROUP BY
            mexico.datum
        """)
