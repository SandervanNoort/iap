#!/usr/bin/env python

"""Generate csv/latex tables"""

import os
import csv

import clim
from .utils import get_conf


class Table:
    """Class which generate tables"""

    def __init__(self, simul, csvdir):
        self.simul = simul
        self.idata = simul.inet.data
        self.skip = True
        self.csvdir = csvdir

    def r2(self, together, climate):
        """Create a csv of the r2 values"""
        if os.path.exists(os.path.join(self.csvdir, "r2.csv")) and self.skip:
            return
        fobj = open(os.path.join(self.csvdir, "r2.csv"), "w")

        columns = ["country", "together"] + clim.aclabels
        writer = csv.DictWriter(fobj, columns, extrasaction="ignore")
        writer.writerow(dict(zip(columns, columns)))
        for country in clim.countries:
            values = {"country": get_conf("word", country)}
            values["together"] = self.simul.data_r2(together[country],
                    country, clim.src)
            for aclabel in clim.aclabels:
                paramdict = climate[aclabel][country]
                values[aclabel] = self.simul.data_r2(
                        paramdict, country, clim.src)
            writer.writerow(values)
        fobj.close()

    def latex_r2(self):
        """Make a latex table for the R2"""

        csvname = os.path.join(self.csvdir, "r2.csv")
        csvobj = open(csvname, "r")
        texname = os.path.join(self.csvdir, "r2.tex")
        texobj = open(texname, "w")
        reader = csv.DictReader(csvobj)

        for line in reader:
            row = []
            row.append(line["country"])
            row.append("%.2f" % float(line["together"]))
            row.append("%.2f" % float(line["ahum_avg"]))
            row.append("%.2f" % float(line["ahum_real"]))
            row.append("%.2f" % float(line["temp_avg"]))
            row.append("%.2f" % float(line["temp_real"]))
            texobj.write(" & ".join(row) + "\\\\ \n")

        csvobj.close()
        texobj.close()

    def latex_params(self, country):
        """Make a latex params table for the generated csv file"""
        csvname = os.path.join(self.csvdir, "params_%s.csv" % country)
        texname = os.path.join(self.csvdir, "params_%s.tex" % country)
        csvobj = open(csvname, "r")
        texobj = open(texname, "w")
        reader = csv.DictReader(csvobj)

        end = ""
        for line in reader:
            row = []
            if line["season"] == "all_1":
                row.append("\\ind All seasons")
                row.append("$\\frac{\\beta}{p} = %.1f$" % \
                        float(line["model1"]))
                row.append("\\multicolumn{2}{l}"
                        + "{$\\beta^* = %.1f$}" % float(line["model2"]))
                row.append("\\multicolumn{3}{l}"
                        + "{$\\beta^* = %.1f$}" % float(line["model3"]))
                end += " & ".join(row) + "\\\\ \n"
            elif line["season"] == "all_2":
                row.extend([" "] * 4)
                row.append("\\multicolumn{3}{l}"
                        + "{$k = %.2f$}" % float(line["model3"]))
                end += " & ".join(row) + "\\\\ \n"
            elif line["season"] == "all_3":
                row.extend([" "] * 4)
                row.append("\\multicolumn{3}{l}"
                        + "{$\\epsilon^* = %.1f$}" % float(line["model3"]))
                end += " & ".join(row) + "\\\\ \n"
            else:
                row.append("\ind %s" % get_conf("word", line["season"]))
                row.append("%.3f" % float(line["model1"]))
                row.append("%.2f" % float(line["model2b"]))
                row.append("%.2f" % float(line["model2"]))
                row.append("%.2f" % float(line["model3"]))
                row.append("%.2f" % float(line["model3b"]))
                row.append("%.1f" % float(line["model3c"]))
                texobj.write(" & ".join(row) + "\\\\ \n")

        texobj.write("\\addlinespace\n %s" % end)
        texobj.close()
        csvobj.close()

    def params(self, together, separate, climate, aclabel, country):
        """All parameters in big table"""

        filename = os.path.join(self.csvdir, "params_%s.csv" % country)
        if os.path.exists(filename) and self.skip:
            return
        fobj = open(filename, "w")

        columns = ["season", "model1", "model2", "model2b",
                "model3", "model3b", "model3c"]
        writer = csv.DictWriter(fobj, columns, extrasaction="ignore")
        writer.writerow(dict(zip(columns, columns)))

        row = {"season": "all_1"}
        params = together[country][clim.PARAMS["seasons"][0]]
        row["model1"] = params["beta"] * 7  # day -> week

        beta, pvals = self.simul.betas_to_pvals([
                separate[country][myseason]["beta"]
                for myseason in clim.PARAMS["seasons"]])
        row["model2"] = beta * 7  # day -> week

        params = climate[aclabel][country][clim.PARAMS["seasons"][0]]
        row["model3"] = params["beta"] * 7  # day -> week
        writer.writerow(row)

        row = {"season": "all_2"}
        row["model3"] = params["clim_gradient"]
        writer.writerow(row)

        row = {"season": "all_3"}
        row["model3"] = params["clim_intercept"]
        writer.writerow(row)

        peaks = self.simul.get_peaks(climate[aclabel][country])
        climates = self.simul.peaks_to_climates(peaks, country, aclabel)
        pvals_clim = self.simul.climates_to_pvals(climates,
                params["clim_gradient"], params["clim_intercept"])

        for season, pval, myclimate, pval_clim in zip(clim.PARAMS["seasons"]),
                pvals, climates, pvals_clim):
            row = {"season": season}

            params = together[country][season]
            row["model1"] = params["s0"]

            params = separate[country][season]
            row["model2"] = pval
            row["model2b"] = params["s0"] / pval

            params = climate[aclabel][country][season]

            row["model3"] = params["s0"]
            row["model3b"] = pval_clim
            row["model3c"] = myclimate

            writer.writerow(row)

        fobj.close()
