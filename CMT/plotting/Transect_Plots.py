# import modules
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
    NumericDates = np.array([date.toordinal() for date in Dates])
    Positions = Transect.HistoricShorelinesDistance
    Errors = Transect.HistoricShorelinesErrors

    if show_errors:
        ax.errorbar(Dates,Positions,yerr=Errors,
            fmt="o",ecolor='gray', elinewidth=1, capsize=3, 
            label="Shoreline Positions with Errors'")
        
    else:
        ax.plot(Dates,Positions,fmt="o",
            label="Shoreline Positions")

    if Regression:
        RegressionLine = Transect.RegressionSlope*NumericDates + Transect.RegressionIntercept
        plt.fill_between(Dates, RegressionLine-Transect.RegressionConfidence, RegressionLine+Transect.RegressionConfidence,
                         color='gray', alpha=0.3, label='95% Confidence Interval')
            
        plt.plot(Dates, RegressionLine, color='k', linestyle='--', label='Time-weighted Regression')

        # label line
        DatesMidpoint = NumericDates[0] + (NumericDates[-1]-NumericDates[0])/2
        
        # get angle from axis transformed coordinates
        x0, y0 = ax.transData.transform((NumericDates[-2], RegressionLine[-2]))
        x1, y1 = ax.transData.transform((NumericDates[-1], RegressionLine[-1]))
        Angle = np.degrees(np.arctan2(y1-y0,x1-x0))

        ax.text(mdates.num2date(DatesMidpoint), Transect.RegressionSlope*DatesMidpoint + Transect.RegressionIntercept,
                "Time-weigted Historic Rate" +str(Transect.ChangeRates[-1]) + "m yr$^{-1}$",
                rotation=Angle, rotation_mode='anchor',
                fontsize=11, ha='center', va='center')
                
    # add text labels for title and axes     
    ax.set_title(f"Transect {Transect.ID}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Relative Shoreline Position (m)")
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3)

    # add legend
    ax.legend(frameon=False)

    # label erosion and accretion
    # Upward arrow = accretion
    ax.annotate("Accretion (+)", xy=(0.02, 0.85), xytext=(0.02, 0.6),
            xycoords="axes fraction", textcoords="axes fraction",
            arrowprops=dict(arrowstyle="->", lw=1), fontsize=11, ha="left")

    # Downward arrow = erosion
    ax.annotate("Erosion (–)", xy=(0.02, 0.15), xytext=(0.02, 0.4), 
                xycoords="axes fraction",textcoords="axes fraction", 
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=11, ha="left")

    return fig, ax

            