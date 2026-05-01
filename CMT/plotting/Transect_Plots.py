# import modules
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyArrowPatch
import matplotlib.patheffects as pe
from datetime import date
import sys

plt.rcParams.update({
    "font.size": 12,          # base size
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
})

def PlotShorelineTimeseries(Transect, ax=None, show_errors=True, show_weights=False, StartDate=None, Regression=True):
    
    """
    Plot shoreline position through time for a Transect object.

    MDH, May 2026
    """

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    else:
        fig = ax.figure

    Dates = Transect.HistoricShorelinesDates
    OrdinalDates = np.array([date.toordinal() for date in Dates])
    PlotDates = mdates.date2num(Dates)

    Positions = Transect.HistoricShorelinesDistance
    Errors = Transect.HistoricShorelinesErrors

    # format date axis
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # add text labels for title and axes     
    ax.set_title(f"Transect {Transect.ID}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Distance Inland (m)")

    ax.grid(True, alpha=0.3)

    if show_errors:
        ax.errorbar(PlotDates,Positions,yerr=Errors,
            fmt="o",ecolor='gray', elinewidth=1, capsize=3, 
            label="Shoreline Positions with Errors")
        
    else:
        ax.plot(PlotDates,Positions,fmt="o",
            label="Shoreline Positions")

    
    
    if Regression:

        # fix axis limits based on data
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        # calculate regression
        RegressionLine = Transect.RegressionSlope*OrdinalDates + Transect.RegressionIntercept
        ax.fill_between(PlotDates, RegressionLine-Transect.RegressionConfidence, RegressionLine+Transect.RegressionConfidence,
                         color='gray', alpha=0.3, label='95% Confidence Interval')
            
        ax.plot(PlotDates, RegressionLine, color='k', linestyle='--', label='Time-weighted Regression')

        # label line
        # check whether regression line intersects x or y axis
        y_at_xmin = Transect.RegressionSlope * mdates.num2date(xmin).toordinal() + Transect.RegressionIntercept
        y_at_xmax = Transect.RegressionSlope * mdates.num2date(xmax).toordinal() + Transect.RegressionIntercept

        if ymin > y_at_xmin:
            MidPointDist = (ymin + ymax)/2.
            OrdinalMidpoint = (MidPointDist-Transect.RegressionIntercept)/Transect.RegressionSlope

        else:
            MidPointDate = (xmax +xmin)/2.
            OrdinalMidpoint = mdates.num2date(MidPointDate).toordinal()
        try:
            MidDate = date.fromordinal(int(round(OrdinalMidpoint)))
        except:
            print(Transect.ID)
            print(MidPointDist)
            print(OrdinalMidpoint)
        
        # add legend
        ax.legend(frameon=False)

        # fix axis limits based on data not regression
        ax.set_ylim(ymin, ymax)

        # get angle from axis transformed coordinates
        fig.tight_layout()
        fig.canvas.draw()
        x0, y0 = ax.transData.transform((PlotDates[0], RegressionLine[0]))
        x1, y1 = ax.transData.transform((PlotDates[-1], RegressionLine[-1]))
        Angle = np.degrees(np.arctan2(y1-y0,x1-x0))
        
        ax.text(MidDate, Transect.RegressionSlope*OrdinalMidpoint + Transect.RegressionIntercept,
                "Rate: " + str(Transect.ChangeRates[-1]) + " m yr$^{-1}$",
                rotation=Angle, rotation_mode='anchor',
                fontsize=10, ha='center', va='bottom',
                path_effects = [pe.withStroke(linewidth=4, foreground="white", alpha=0.7)]
                # bbox=dict(
                #             facecolor="white",
                #             alpha=0.7,        # transparency (0–1)
                #             edgecolor="none")
                )

    else:
        # add legend
        ax.legend(frameon=False)    
    

    # label erosion and accretion
    # Upward arrow = accretion
    # Top arrow (vertical)

    # Create Arrow
    EColour = [0.7,0.1,0.1]
    arrow1 = FancyArrowPatch(
        (0.05, 0.8), (0.05, 0.9),
        transform=ax.transAxes,
        arrowstyle='-|>',
        mutation_scale=15,  
        linewidth=1.5,
        color=EColour
    )
    ax.add_patch(arrow1)

    ax.text(
        0.06, 0.85,
        "Erosion (-)",
        transform=ax.transAxes,
        color=EColour,
        fontsize=10,
        va='center',
        ha='left'
    )

    # Bottom arrow (vertical)
    AColour = [0.1,0.1,0.6]
    arrow2 = FancyArrowPatch(
        (0.05, 0.15), (0.05, 0.05),
        transform=ax.transAxes,
        arrowstyle='-|>',
        mutation_scale=15,
        linewidth=1.5,
        color=AColour
    )
    ax.add_patch(arrow2)

    ax.text(
        0.06, 0.1,
        "Accretion (+)",
        transform=ax.transAxes,
        color=AColour,
        fontsize=10,
        va='center',
        ha='left'
    )

    return fig, ax

            