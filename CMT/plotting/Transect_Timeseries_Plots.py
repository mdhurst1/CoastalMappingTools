"""
Function to plot timeseries object results and regression results

MDH, May 2026

"""

# import modules
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe
from datetime import date
import sys

plt.rcParams.update({
    "font.family": ["Arial"],
    "font.size": 12,          # base size
    "axes.titlesize": 16,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
})

LineColours = {
    "VEdge": [0.4, 0.8, 0.4],
    "MHWS": [0.4, 0.4, 0.9]
}

MarkerStyles = {
    "VEdge": "s",
    "MHWS": "o",
}

LineStyles = {
    "EPR": ":",
    "OLS": "-",
    "TheilSen": "--",
    "TWR": "-.",
}

AllRegressionMethods = ("EPR", "OLS", "TheilSen", "TWR")

# plot timeseries
def PlotTimeSeriesSignals(Signals, ax=None, ShowErrors=True, RegressionMethods=("TWR",), Title=None):

    """
    
    Plot timeseries and regression

    MDH, May 2026

    """

    if not isinstance(RegressionMethods,tuple):
        if RegressionMethods.lower() == "all":
            RegressionMethods=("EPR", "OLS", "TheilSen", "TWR")
        elif RegressionMethods in AllRegressionMethods:
            RegressionMethods = (RegressionMethods,)
        else:
            sys.exit(r"Unknown regression method [RegressionMethods]")

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    else:
        fig = ax.figure

    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.set_xlabel("Date")
    ax.set_ylabel("Distance Inland (m)")
    ax.grid(True, alpha=0.3)

    if Title is not None:
        ax.set_title(Title)

    for Signal in Signals:

        Dates = Signal.Dates
        PlotDates = mdates.date2num(Dates)
        Distances = Signal.DistancesArray()
        Errors = Signal.ErrorsArray()
        Colour = LineColours.get(Signal.Name)
        Marker = MarkerStyles.get(Signal.Name, "o")

        if ShowErrors and Errors is not None:
            ax.errorbar(
                PlotDates,
                Distances,
                yerr=Errors,
                fmt=Marker,
                color=Colour,
                capsize=3,
                elinewidth=1,
                label=f"{Signal.Name} observations"
            )
        else:
            ax.plot(
                PlotDates,
                Distances,
                Marker,
                color=Colour,
                label=f"{Signal.Name} observations"
            )

        for Method in RegressionMethods:

            if Method not in Signal.Results:
                continue

            Result = Signal.Results[Method]
            LineStyle=LineStyles.get(Method, "-")

            if Method == "EPR":
                ax.plot(
                    [Result["StartDate"], Result["EndDate"]],
                    [Result["StartDistance"], Result["EndDistance"]],
                    linestyle=LineStyle,
                    linewidth=2,
                    color=Colour,
                    label=f"{Signal.Name} {Method}: {Result['Rate']:.2f} m yr$^{{-1}}$"
                )
            else:
                ax.plot(
                    PlotDates,
                    Result["Fitted"],
                    linestyle=LineStyle,
                    linewidth=2,
                    color=Colour,
                    label=f"{Signal.Name} {Method}: {Result['Rate']:.2f} m yr$^{{-1}}$"
                )

    ax.legend(frameon=False)
    fig.tight_layout()

    return fig, ax