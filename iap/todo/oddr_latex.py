    def error_bars(self, cutters, ticks, tbldir, tblname):
        """Make the graphical oddrs"""
#
        line = 18.75
        linesc = 18.75
        lineskip = 7.5
#
        fig = pyfig.Figure("""
            [fig]
                figname = {figname}
                figsize = 1.1, 6
                fig_margins = 0, 0, 0, 0
                ax_margins = {top_margin}, 5, {bottom_margin}, 10
                xscale = log
                [[rc]]
                    xtick.labelsize = 8
            """.format(figname=os.path.join(tbldir, tblname + ".pdf"),
                       top_margin=int(line),
                       bottom_margin=0))
#
        ax, = fig.add_ax()
        ax.set_xscale("log")
        for spine in ax.spines.keys():
            ax.spines[spine].set_linewidth(0)
        ax.invert_yaxis()
        ax.set_yticks([])
        ax.xaxis.tick_top()
        ax.xaxis.set_ticks_position("top")
#
        row = line
        for cutter in cutters:
            if cutter not in self.results:
                continue
            row += linesc
            for label in self.results[cutter]["labels"]:
#                 if [cutter, label["label"]] in self.ignores:
#                     continue
                if "oddr" in label:
                    color = "red" if label["lower"] > 1 \
                        else "blue" if label["upper"] < 1 \
                        else "black"
                    ax.errorbar([label["oddr"]],
                                [row + 0.6 * line],
                                xerr=[[label["oddr"] - label["lower"]],
                                      [label["upper"] - label["oddr"]]],
                                color=color,
                                marker="s",
                                markersize=2.5)
                row += line
            row += lineskip
        row -= lineskip
#
        fig.fig.set_figheight(row / 100)
#
        ax.set_ylim(ymax=line, ymin=row)
        ax.axvline(x=1, linestyle=":", color="gray", linewidth=1)
        ax.set_xticks(ticks)
        ax.set_xticklabels(list("{0:d}".format(int(tick))
                           if round(tick) == tick
                           else "{0:.1f}".format(tick) for tick in ticks))
        ax.set_xlim(xmin=min(ticks), xmax=max(ticks))
        fig.save()

    def latex(self, plot_settings):
        """Return tabular + figure"""
#
        tbldir = os.path.dirname(self.ini.settings["fig"]["figname"])
        tblname = os.path.basename(self.ini.settings["fig"]["figname"])
        if not os.path.exists(tbldir):
            os.makedirs(tbldir)
#
        cutters = (self.dataset["cutter_values"]
                   if len(plot_settings["oddr_cutters"]) == 0
                   else plot_settings["oddr_cutters"])
        countries = (self.dataset["country_values"]
                     if len(plot_settings["oddr_countries"]) == 0
                     else plot_settings["oddr_countries"])
#
        ticks = plot_settings["oddr_ticks"]
#         self.ignores = [cutter_label.split("-")
#                 for cutter_label in plot_settings["oddr_ignores"]]
#
        self.error_bars(cutters, ticks, tbldir, tblname)
#
        tabular = r"""
            \begin{{tabular}}{{l@{{}}c@{{}}c{c_countries}}}
            \toprule
            \multirow{{2}}{{*}}{{\textsc{{Question}}}}
            & \multicolumn{{2}}{{c}}{{\multirow{{2}}{{*}}{{
                \textsc{{OR (95\% CI)}}}}}}
            & \multicolumn{{{num_countries}}}{{c}}{{
                \textsc{{Frequency (\%)}}}} \\
            & & & {country_names} \\
            \midrule
            & \multirow{{{num_rows}}}{{*}}
                    {{\includegraphics{{\figpath/{tblname}}}}} \\
            """.format(c_countries=len(countries) * "c",
                       num_countries=len(countries),
                       country_names=" & ".join([
                           r"\textsc{{{0}}}".format(c.upper())
                           for c in countries]),
                       num_rows=sum([
                           1 for cutter in cutters
                           if cutter in self.results
                           for label in self.results[cutter]["labels"]]) + 1,
                       tblname=tblname)
#
        for cutter in cutters:
            if cutter not in self.results:
                continue
            tabular += r"\textsc{{{title}}} \\".format(
                title=trans(iap.cutter.get_cutter_label(cutter))) + "\n"
            for label in self.results[cutter]["labels"]:
#                 if [cutter, label["label"]] in self.ignores:
#                     continue
                labelstr = trans(iap.cutter.get_portion_label(
                    cutter, label["label"], self.ini.settings["style"]))
                if "oddr" in label:
                    color = "red" if label["lower"] > 1 \
                        else "blue" if label["upper"] < 1 \
                        else "black"
                    if plot_settings["oddr_color"]:
                        tabular += (r"\ind \textcolor{{{color}}}" +
                                    r"{{{label}}} & & ").format(color=color,
                                                            label=labelstr)
                    else:
                        tabular += r"\ind {0} & & ".format(labelstr)
#
                    # http://bugs.python.org/issue7094
                    # alternative format not implemented with format()
                    # "#.2g" => display trailing zeros
                    tabular += (r"%(oddr)#.2g (%(lower)#.2g" +
                                r" - %(upper)#.2g)") % label
                    #if upper > 100:
                    #    upper = 100
                else:
                    tabular += r"\ind {0}$^*$ & & - ".format(labelstr)
                if cutter not in ["season", "country"]:
                    tabular += " & " + " & ".join([
                        self.perc(cutter, label["label"], country)
                        for country in countries])
                tabular += r"\\" + "\n"
            tabular += r"\addlinespace" + "\n"
#
        tabular += r"""\bottomrule
            \end{tabular}"""
#
        with open(os.path.join(tbldir, tblname + ".tex"), "w") as fobj:
            fobj.write(tabular)
