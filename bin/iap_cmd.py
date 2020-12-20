#!/usr/bin/env python3
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Command line iap"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import sys  # pylint: disable=W0611
import argparse
import getpass
import logging

import iap

logger = logging.getLogger(__name__)


def get_cmd_options():
    """Get cmd options"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-table", nargs="+", action="store", dest="table")
    parser.add_argument("-fill", nargs="+", action="store", dest="fill")
    parser.add_argument("-noaa", nargs="+", action="store", dest="noaa")
    parser.add_argument("-eiss", nargs="+", action="store", dest="eiss")
    parser.add_argument("-google", nargs="+", action="store", dest="google")
    parser.add_argument("-export", nargs="+", action="store", dest="export")
    parser.add_argument("-inet", nargs="+", action="store", dest="inet")
    parser.add_argument("-geo", nargs="+", action="store", dest="geo")
    parser.add_argument("-ini", nargs="+", action="store", dest="ini")
    parser.add_argument("-missing", nargs="+", action="store", dest="missing")

    parser.add_argument("-noaa-stations", action="store_true", default=False)
    parser.add_argument("-download", action="store_true", default=False)
    parser.add_argument("-ifill", action="store_true", default=False)
    parser.add_argument("-delete", action="store_true", default=False)
    parser.add_argument("-overwrite", action="store_true", default=False)
    parser.add_argument("-sql", action="store_true", default=False)
    parser.add_argument("-force", action="store_true", default=False)
    parser.add_argument("-d", action="store", dest="debug", default="warning")
    return parser.parse_args()


def do_table(table_list):
    """(re)create tables in the database"""

    groups = {
        "cache": ["linreg", "baseline", "samples"],
        "complete": ["datasets", "series", "risks"],
        "download": ["other", "age", "geo"]}

    for table in table_list:
        if table == "help":
            print("Tables options:\n{options}\n".format(
                options="\n".join([
                    "Group {0}: {1}".format(key, ", ".join(values))
                    for key, values in groups.items()])))
        elif table == "ALL":
            do_table(iap.config.TABLES.keys())
        elif table in groups:
            do_table(groups[table])
        elif table in iap.config.TABLES:
            logger.info("Creating table {0}".format(table))
            iap.utils.create_table(table)
        else:
            logger.error("No such table: {0}".format(table))


def do_eiss(eiss_list, download, overwrite):
    """Download EISS data"""
    times, errors = iap.utils.get_times(eiss_list)
    if len(errors) > 0:
        logger.error("Unknown eiss times: {0}".format(", ".join(errors)))
    for period in times["periods"]:
        if download:
            iap.download.eiss_download(period, overwrite)
        iap.download.eiss_fill(period)


def do_google(google_list, download):
    """Download Google data"""
    times, errors = iap.utils.get_times(google_list)
    if len(errors) > 0:
        logger.error("Unknown google times: {0}".format(", ".join(errors)))
    for country in times["countries"]:
        if download:
            iap.download.google_download(country)
        iap.download.google_fill(country)


def do_geo(geo_list, download, overwrite):
    """Download Geo postal code data"""
    times, errors = iap.utils.get_times(geo_list)
    if len(errors) > 0:
        logger.error("Unknown geo times: {0}".format(", ".join(errors)))
    for country in times["countries"]:
        if download:
            iap.download.geo_download(country, overwrite)
        iap.download.geo_fill(country)


def do_noaa(noaa_list, download, overwrite):
    """Download noaa data"""
    times, errors = iap.utils.get_times(noaa_list, min_year=1950)
    if len(errors) > 0:
        logger.error("Unknown noaa times: {0}".format(", ".join(errors)))
    for country in times["countries"]:
        for year in times["years"]:
            if download:
                iap.download.noaa_download(country, year, overwrite)
            iap.download.noaa_fill(country, year)


def do_inet(inet_list, download, ifill, delete):
    """Import inet data"""
    times, errors = iap.utils.get_times(inet_list)
    if len(errors) > 0:
        logger.error("Unknown inet times: {0}".format(", ".join(errors)))
    downloaded = []
    for period in times["periods"]:
        convert = iap.Convert(period)
        update = iap.Update(period)

        if download or ifill:
            if convert.src and convert.src not in downloaded:
                if download:
                    convert.download()
                # if download, also always ifill
                imported = convert.sqlimport()
                if not imported:
                    continue
                downloaded.append(convert.src)

        convert.fill("intake")
        update.intake_update()
        convert.fill("survey")
        update.survey_update()
        update.both_update()

        update.datasets_delete()
        update.implode_columns("intake")
        update.implode_columns("survey")
        if delete:
            convert.delete_orig("intake")
            convert.delete_orig("survey")


def do_export(export_list):
    """Export inet data"""
    times, errors = iap.utils.get_times(export_list)
    if len(errors) > 0:
        logger.error("Unknown export times: {0}".format(", ".join(errors)))
    for period in times["periods"]:
        # iap.Export.dump_sql(period)
        iap.Export.dump_csv(period)
        iap.Export.dump_orig(period)


def do_fill(fill_list):
    """Fill certain tables"""

    groups = {"fr": "French ILI data",
              "age": "Age data (Eurostat)",
              "mexico": "Mexico flu data (GGM 2009/10)"}

    if "ALL" in fill_list:
        fill_list = groups.keys()

    for fill in fill_list:
        if fill == "help":
            print("Fill options:")
            for key, value in groups.items():
                print("{0}: {1}".format(key, value))
            print("")
        elif fill == "age":
            iap.download.age_fill()
        elif fill == "fr":
            iap.download.fr_fill()
        elif fill == "mexico":
            iap.download.mexico_fill()
        else:
            logger.error("No such fill: {0}".format(fill))


def do_missing(missing_list):
    """Show missing database columns"""
    times, errors = iap.utils.get_times(missing_list)
    if len(errors) > 0:
        logger.error("Unknown missing times: {0}".format(", ".join(errors)))
    for period in times["periods"]:
        check = iap.Check(period)
        check.missing()


def do_ini(ini_list):
    """Convert ini file to png"""
    for ininame in ini_list:
        if not os.path.exists(ininame):
            logger.error("No such file: {0}".format(ininame))
        elif os.path.isdir(ininame):
            do_ini([os.path.join(ininame, fname)
                    for fname in os.listdir(ininame)
                    if fname.endswith(".ini")])
        elif ininame.endswith(".ini"):
            try:
                ini = iap.Ini(ininame)
                if len(ini.datasets.keys()) == 0:
                    raise iap.IAPError("No datasets")
                fig = iap.fig.Fig(ini.settings)
                for plot_settings in ini.settings["plots"].values():
                    if not iap.fig.dia(fig, plot_settings,
                                       ini.datasets).draw():
                        raise iap.IAPError("No data in plot")
                figname = ininame[:-4]
                fig.save(figname + ".png")
                fig.savefig(figname + ".pdf")
                export = iap.Export(ini)
                export.write_csv(figname)
            except iap.IAPError as error:
                logger.error("Error in ini file: {ini}\n{error}".format(
                    ini=ininame, error=error))
        else:
            logger.error("No ini file: {0}".format(ininame))


def do_sql(force=False):
    """Create mysql database and users"""

    logger.info("Creating IAP database access (based on local.ini)")

    params = iap.config.LOCAL["db"]
    passwd = getpass.getpass("MySQL root password: ")
    params["root"] = passwd

    if not iap.tools.sql_check_root(params["root"]):
        return
    if not iap.tools.sql_create_db(params["db"], params["root"], force):
        return
    if not iap.tools.sql_create_user(params["user"], params["pass"],
                                 params["root"], params["db"], force):
        return


def do_noaa_stations(overwrite):
    """Download noaa stations file"""
    iap.download.noaa_stations(overwrite)

if __name__ == "__main__":
    cmd_options = get_cmd_options()
    iap.tools.set_debug_level(cmd_options.debug)
    try:
        if cmd_options.sql:
            do_sql(cmd_options.force)
        if cmd_options.table:
            do_table(cmd_options.table)
        if cmd_options.fill:
            do_fill(cmd_options.fill)
        if cmd_options.noaa:
            do_noaa(cmd_options.noaa, cmd_options.download,
                    cmd_options.overwrite)
        if cmd_options.eiss:
            do_eiss(cmd_options.eiss, cmd_options.download,
                    cmd_options.overwrite)
        if cmd_options.google:
            do_google(cmd_options.google, cmd_options.download)
        if cmd_options.geo:
            do_geo(cmd_options.geo, cmd_options.download,
                   cmd_options.overwrite)
        if cmd_options.inet:
            do_inet(cmd_options.inet, cmd_options.download, cmd_options.ifill,
                    cmd_options.delete)
        if cmd_options.missing:
            do_missing(cmd_options.missing)
        if cmd_options.export:
            do_export(cmd_options.export)
        if cmd_options.ini:
            import iap.fig  # pylint: disable=W0404
            do_ini(cmd_options.ini)
        if cmd_options.noaa_stations:
            do_noaa_stations(cmd_options.overwrite)

    except iap.IAPError as error:
        logger.error(error)
    except:
        iap.utils.close()
        raise
    iap.utils.close()
