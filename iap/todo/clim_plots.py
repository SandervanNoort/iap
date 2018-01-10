    def weather_cor(self):
        """Attack rate based on S0"""

        ax, = self.fig.add_ax()

        for country in self.countries:
            ahum = inet.get_climate(country, "avg", "ahum")
            temp = inet.get_climate(country, "avg", "temp")

            days = set(ahum.keys()).intersection(temp.keys())
            ax.plot([temp[day] for day in days if day % 2 == 0],
                    [ahum[day] for day in days if day % 2 == 0],
                    linewidth=0,
                    marker="mix",
                    markersize=4,
                    color="mix",
                    markeredgecolor="mix",
                    label=translate("<<country:{0}>>".format(country)))

        ax.set_xlabel(iap.utils.translate(
            "<<measure:temp>> <<measure:temp_unit>>"))
        ax.set_ylabel(iap.utils.translate(
            "<<measure:ahum>> <<measure:ahum_unit>>"))

    def ratios_week(self, simul_dict, clim_log):
        """Draw correlation between climate and ratios"""

        ax, = self.fig.add_ax()
        for country in self.countries:
            simul = simul_dict[country]
            weeks = []
            for season in self.seasons:
                day = simul.get_peaks()[season][0]
                weeks.append((day - simul.ini["model0"]) / 7)
            _beta, pvals = model.betas_to_pvals(
                [simul.get_paramdict()[season]["beta"]
                 for season in self.seasons])
            for week, pval, season in zip(weeks, pvals, self.seasons):

                # legend
                ax.plot([week],
                        [pval],
                        marker="mix({0})".format(season),
                        markersize=4,
                        color="black",
                        linewidth=0,
                        label=translate("<<season:{0}>>".format(season)),
                        leg_place="fig2")

                ax.plot([week],
                        [pval],
                        marker="mix({0})".format(season),
                        markersize=4,
                        color="mix({0})".format(country),
                        linewidth=0,
                        markeredgecolor="mix({0})".format(country))

            lparams = model.climate_regression(weeks, pvals, clim_log)
            minmax_climate = numpy.linspace(
                min(min(weeks), model.pvals_to_climates(
                    min(pvals), lparams["gradient"], lparams["intercept"],
                    clim_log)),
                max(max(weeks), model.pvals_to_climates(
                    max(pvals), lparams["gradient"], lparams["intercept"],
                    clim_log)),
                10)
            ax.plot(minmax_climate,
                    model.climates_to_pvals(
                        minmax_climate, lparams["gradient"],
                        lparams["intercept"], clim_log),
                    linewidth=1,
                    color="mix({0})".format(country),
                    label=translate("<<country:{0}>>".format(country)))
            ax.text(0.9,
                    0.46 - self.countries.index(country) * 0.14,
                    "$\\mathbf{R}^2$\\textbf{=%.2f}" % lparams["r2"],
                    transform=ax.transAxes,
                    va="top",
                    ha="right",
                    fontsize=9,
                    color="mix({0})".format(country))

        ax.set_ylabel("ILI factor")
        ax.set_xlabel("Weeks since Sep, 1st")

        if clim_log:
            ax.set_yscale("log")
            ax.set_ylim(ymin=0.1, ymax=1.1)
            ax.set_yticks([0.1, 0.2, 0.5, 1])
            ax.set_yticklabels([str(ytick) for ytick in ax.get_yticks()])
