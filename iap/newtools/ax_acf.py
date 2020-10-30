def ax_acf(ax, data, ccf=False, **kwargs):
    """Plot autocorrelation"""

    options = {"nonzero_color": "0.5",
               "significant_color": "0.4",
               "significant_width": 1}
    options.update(kwargs)

    ax.vlines(data["x"], len(data["y"]) * [0], data["y"],
              color=options["nonzero_color"] if ccf else "black")
    if data["type"] == "ccf":
        ax.vlines(0, 0, data["y"][data["x"].index(0)],
                  color="black", linewidth=2)

    ax.axhline(y=data["significant"],
               color=options["significant_color"],
               linewidth=options["significant_width"],
               linestyle="--")
    ax.axhline(y=-data["significant"],
               color=options["significant_color"],
               linewidth=options["significant_width"],
               linestyle="--")

    ax.axhline(y=0, color="black", linestyle="-", linewidth=1)
    # ax.set_ylim(ymax=1 if ccf else 1.2)
    # ax.set_xlim(xmin=min(data["x"]) - 1, xmax=max(data["x"]) + 1)

    ax.set_ylabel("Cross correlation" if data["type"] == "ccf" else
                  "Auto correlation" if data["type"] == "acf" else
                  "Partial ACF" if data["type"] == "pacf" else
                  "")
    ax.set_xlabel("Lag")
