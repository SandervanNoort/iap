[map]
    min_pixels = integer(default=10)
    min_white = integer(default=750)
    max_black = integer(default=30)
    min_incidence = integer(default=500)
    max_incidence = integer(default=1500)
    max_color = int_list(min=4, max=4, default=list(255, 0, 0, 255))
    min_color = int_list(min=4, max=4, default=list(255, 0, 0, 255))
    none_color = int_list(min=4, max=4, default=list(200, 200, 200, 255))
    unknown_color = int_list(min=4, max=4, default=list(200, 200, 200, 255))
    pre_days = integer(default=7) # no earlier maps

    lang = option("nl", "en", "pt", default="en")

    fontfamily = string(default="Arial")
    [[font]]
        __many__ = integer
    [[margin]]
        __many__ = integer
    [[legend]]
        __many__ = integer
    
[fig]
    # which labels have to appear in the legend
    legend_labels = string_list(default=list())

    # make shorter labels if possible
    short = boolean(default=False)

    # labels that have to appear in the title
    title_labels = string_list(default=list())

    # labels that are part of the x-labels in a barplot
    city_labels = string_list(default=list())

    # labels that should be summed in a barplo
    sum_labels = string_list(default=list())

    # labels that should be ignored
    ignore_labels = string_list(default=list())

    # language of the labels ("nl"="Netherlands" or "Nederland")
    lang = option("en", "nl", "pt", default="en")

    # whether to show influenzanet.eu + logo in the lower-left corner
    inet_url = option("inet", "", default="")

    # whether to print a data in lower right corner
    inet_date = boolean(default=False)

    # how to display ranges
    full_range = string(default="{min_val}-{max_val_1}")
    first_range = string(default="{min_val}-{max_val_1}")
    last_range = string(default="{min_val}-{max_val_1}")
    first_range_min = string(default="<{max_val}")
    last_range_max = string(default="{min_val}+")

    baseline_color = string(default="0.3")
    baseline_width = integer(default=1)
    baseline_style = string(default="-")

    samples_color = string(default="0.7")

    # datasets for the labels
    datasets = string_list(default=list())
[plots]
    [[__many__]]
        # the type of plot
        type = option("plot", "barplot", "map", "venn", "weeks", default="plot")

        # datasets included in this plot
        datasets = string_list(default=list())

        # the ax margins for this plot
        ax_margins = int_list(min=4, max=4, default=list(0, 0, 0, 0))

        # reserve space for a non-existent right-hand ax
        ax2 = boolean(default=False)

        # the row/col number in the figure
        row = integer(default=0)
        col = integer(default=0)

        # place of the legends
        leg_place = string(default="fig")

        # number of columns for ax
        ncol = integer(default=1)

        # wrapping of the ylabels
        wrap = integer(default=0)

        # whether to draw a grid
        grid = boolean(default=False)
        xgrid = boolean(default=False)
        ygrid = boolean(default=False)

        # the source_measure of the ax on the left side
        left_ax = string(default="")

        # the axes which can be empty (in 2-ax plot)
        allow_empty = string_list(default=list())

        # the min/max of left (ax1) and right (ax2) axes
        ymax = float(default=None)
        ymax2 = float(default=None)
        ymin = float(default=None)
        ymin2 = float(default=None)
        yfractions = boolean(default=False)

        # The number of yticks
        yticks = integer(default=None)
        yticks2 = integer(default=None)

        # rotate the xlabels a number of degrees
        xangle = integer(default=0)

        # the xlabel
        xlabel = string(default="auto")

        # the ylabel, if set to auto dynamically determine it
        ylabel = string(default="auto")
        ylabel2 = string(default="auto")

        # the ax label
        label = string(default="")

        # the top right label
        topright = string(default="")


        # the date formt of the x-axis
        date_format = option("year", "week", "month", "month2", "month3", "month4", default="year")

        # the start/end of the plot
        # for year-axes plots: given as YYYY/MM/DD or YYYY-MM-DD
        # For other plots (months), given as MM/DD or MM-DD
        plot_start = string(default="")
        plot_end = string(default="")

        bar_start = string(default="")
        bar_end = string(default="")

        # grey out period with few influenza viruses
        samples_period = integer(default=0)

        # case definition used for determining epidemic period
        samples_casedef = string(default="")

        # average over <> days
        samples_average = integer(default=7)

        # pdif threshold (vega et al) for onset
        samples_pdif = float(default=0.02)

        baseline = string_list(default=list())
        threshold = string_list(default=list())
        # minimal number of datasets to show baseline
        baseline_min = integer(default=4)

        baseline_country = string(default="")
        baseline_seasons = string_list(default=list())
        baseline_casedef = string(default="")
        baseline_srcme   = string(default="")
        baseline_combi_seasons = string_list(default=list())
        baseline_threshold = integer(default=15)

        baseline_eiss = integer(default=0)

        # Stack the data on top of eachother and fill in with color
        fill = boolean(default=False)

        # Use a linear regression between to scale the axes
        linreg_gradient = float(default=0)
        linreg_intercept = float(default=0)
        linreg_sources = string_list(min=2, max=2, default=list("",""))
        linreg_seasons = string_list(default=list())
        linreg_casedef = string(default="")
        linreg_country = string(default="")
        linreg_intercept0 = boolean(default=False)
        linreg_days = int_list(default=list(0,1))
        linreg_min_surveys = integer(default=3)

        # the height of one incidence, recalucated for the other
        linreg_ymax = integer(default=0)

        # display the R2 in the upper right corner
        linreg_r2 = boolean(default=False)

        # if a bar plot, what kind of barplot
        #   attack: cases / participants
        #   control: cases & control / cases
        #   compare: rrr or oddr
        #
        #   absolute: number of participants (barplot)
        #   pie: participants (pie plot)
        #
        #   surveys: number of surveys per week
        #
        #   percentage_by_city: all cities sum up to 100%
        #   percentage_by_label: all labels sum to 100%
        #   percentage_by_answer: each bar an individual percentage
        bars = option("attack", "compare", "control", "pie", "percentage_by_city", "absolute", "percentage_by_label", "percentage_by_answer", "surveys", default="absolute")

        # for xy-plot with bars, stack on top of each other
        bar_stack = boolean(default=True)

        # the denominator in the attack rate includes all participants
        full_denominator = boolean(default=False)

        compare = option("rrr", "oddr", "rr", default="oddr")
        # relative risk reduction (rrr) or odds ratio (oddr

        # negative (significant), neg (not sig), pos (not sig), pos (sig)
        compare_colors = string_list(default=list())


        # together with percentage_by_answer
        answer = string(default="")

        # display errors on the bars
        errors = boolean(default=True)

        # display all cities/houses, even those which are empty
        all_cities = boolean(default=False)
        all_houses = boolean(default=False)
        
        # display all cities/houses from all datasets
        all_labels = boolean(default=False)

        # display houses/cities with positive denominator but empty nominator
        city_zero_nominator = boolean(default=True)
        house_zero_nominator = boolean(default=True)

        # sort the cities from low to high
        city_sort = boolean(default=False)
        house_sort = boolean(default=False)
        reverse_sort = boolean(default=False)

        # labels that should be ignored
        ignore_labels = string_list(default=list())

        # labels that should be ignored
        city_labels = string_list(default=list())

        # use floors instead of houses in barplot
        floors = boolean(default=False)

        # flip labels and citylabels
        citylabels = boolean(default=False)

        # the default citylabels and houselabels
        all_city_labels = string_list(default=list())
        all_house_labels = string_list(default=list())

        # distance between houses/cities in barplot
        housedistance = float(default=0)
        citydistance = float(default=0.2)

        # a horizontal barplot
        horizontal = boolean(default=False)

        # the fontsize in the pie plots
        piefont = integer(default=8)

        # Write next to the pieces of the pieplot
        pietext = boolean(default=True)


[datasets]
    [[__many__]]
        # label for the line
        label = string(default="")

        # citylabel in a barplot (if empty, filled by style["city_labels"]
        citylabel = string(default="")

        # country, season, source, and measure of the datasource
        country = string(default="")
        # option("nl", "be", "pt", "it", "uk", "fr", "de", "es", "se", "hu", "ch", "pl", "at", "no")

        # split into multiple for <key>_values
        expand = boolean(default=True)

        subset = string(default="")
        subset_label = string(default="")

        season = string(default="")
        source = option("inet", "eiss", "europe", "climate", "google", "mexico", "combi", "", default="")
        measure = option("", "incidence", "scaled", "reporting", "actives", "cases", "control", "cum", "population", "surveys", "temp", "ahum", "rhum", "prcp", "participants", "trends", "ili", "ili_0-4", "ili_5-14", "ili_15-64", "ili_65+", "infa", "infb", "ari", "samples", default="")
        ili = boolean(default=False)

        # The various data types from EISS

        # normally, the ax_name is set to source_measure, but for example
        # google_incidence can be override to for example eiss_incidence
        ax_name = string(default="")

        # all data available until this date
        snapshot = string(default="")

        # assume participants are always active
        always_active = boolean(default=False)

        # extra country
        extra_countries = string_list(default=list())

        # if always_active is False, how many days a non-reporting
        # participant is assumed healthy
        grace_period = integer(default=0)

        # the day when an onset is marked
        onset = option("fever","symptoms","survey", default="fever")

        # first_survey=2 => ignore the first survey of every participant
        first_survey = integer(default=2)
        last_survey = integer(default=0)

        # ignore all cases after the first
        ignore_double = boolean(default=True)

        # ignore case when reported right after the another survey
        ignore_multiple = boolean(default=False)

        # case definition
        casedef = string(default="")
        # casedef_label = string(default="")

        # persons who fit casedef, how many also fit control definition
        control = string(default="")

        # number of days until control is valid
        control_days = integer(default=15)

        # age corrected incidence (for example: 1-15-65-100)
        age_correction = string(default="")

        # data outside of the define range (in config/config.ini)
        # is shown or not
        # incidence: not shown for incidence, for other it is shown
        limits = option("incidence", "dotted", "hide", "show", default="incidence")
        # Show the inet_incidence as a band
        band_color = string(default="")

        # Show the inet_incidence as a band
        band_label = string(default="")

        # Show the inet_incidence as a band
        band_width = integer(default=3)
        
        # the minimal number of surveys to be included
        min_surveys = integer(min=0, default=3)

        # the maximum number of days between surveys
        max_freq = integer(min=0, default=0)

        # only consider participant with this intake profile
        intake = string(default="")

        # only participant which registered before/after a date
        active_before = string(default="")
        active_after = string(default="")

        # only participants who were active the whole period
        # that significant viruses were around
        samples_period = integer(default=0)

        # only onsets when significant viruses were around
        samples_onsets = integer(default=0)

        # average the incidence of <> days
        average = integer(default=7)

        # minimal number of participants to calculate incidence
        min_participants = integer(default=20)
       
        # plot incidence daily (or weekly)
        daily = boolean(default=True)

        # some specific plot options
        linestyle = string(default="-")
        linewidth = float(default=1)
        markersize = float(default=2.5)
        marker = string(default="")
        color = string(default="mix")

        # the zorder of the line
        zorder = integer(default=0)

        # a barplot or a line lineplot
        bar = boolean(default=False)

        # reload the data
        reload = boolean(default=False)

        # split up the particants by question
        cutter = string(default="")
        city_cutter = string(default="")
        age_cutter = string(default="")

        # split up the participants by column
        survey_cutter = string(default="")

        # the answer of the question
        answer = string(default="")
        city_answer = string(default="")
        age_answer = string(default="")

        # the question_title which appears in the figure title
        question_title = string(default="")

        # the min_value to plot the line
        min_value = integer(default=None)

        # the line which has xmaster, decides the limits (by min_value)
        xmaster = boolean(default=False)

        # if inet_only, seasons without inet data are ignored
        inet_only = boolean(default=False)

        combi_seasons = string_list(default=list())
        combi_intercept0 = boolean(default=False)

[models]
    [[__many__]]
        clim_var = string(default="")
        clim_season = string(default="current")
        clim_log = boolean(default=True)
        model_start = string(default="9/1")
        datasets = string_list(default=list())
        baseline = string_list(default=list())
        min_date = string(default="8/1")
        max_date = string(default="7/31")
        reload = boolean(default=False)
        [[[defaults]]]
            __many__ = float
        [[[bounds]]]
            __many__ = float_list
        [[[symbols]]]
            var = string_list(default=list())
            season = string_list(default=list())
            constant = string_list(default=list())


[risk]
    [[__many__]]
        family = string(default=binomial)

        # whether to show the unknown category
        show_unknown = boolean(default=True)

        # percentage by country, full or none
        show_perc = string(default="")
    
        # show vif
        show_vif = boolean(default=False)

        # show multivariate
        show_multi = boolean(default=True)

        # show univariate
        show_uni = boolean(default=False)

        # the datasets to use for risk model
        datasets = string_list(default=list())

        output = string(default="")
