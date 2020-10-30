import os
import logging
import gc
import rpy2.robjects
# import csv
# import pandas


def stata_to_csv(stata_fname, csv_fname, force=False):
    """Convert Butantan Stata to csv file"""

    if os.path.exists(csv_fname):
        if force:
            os.remove(csv_fname)
        else:
            logging.info("CSV %s already exists", csv_fname)
            return
    logging.info("Importing stata file %s", stata_fname)
    rpy2.robjects.r.library("foreign")
    # run_r.library("haven")
    rpy2.robjects.r("data = read.dta('{0}')".format(stata_fname))
    logging.info("Exporting to csv file %s", csv_fname)
    rpy2.robjects.r(
        "write.csv(data, file='{0}', row.names=FALSE)".format(csv_fname))
    gc.collect()
    rpy2.robjects.r('rm(a)')
    rpy2.robjects.r('gc()')
    gc.collect()
    # on bo_dengue2013 this crashes
    # dataframe = pandas.read_stata(stata_fname)
    # pylint: disable=E1101
    #     dataframe.to_csv(
    #         csv_fname,
    #         index=False,
    #         doublequote=True,
    #         escapechar=None,
    #         quoting=csv.QUOTE_NONNUMERIC)
    # pylint: enable=E1101
