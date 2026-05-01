# import modules
import matplotlib.pyplot as plt

def PlotShorelineTimeseries(Transect, ax=None, show_errors=True, show_weights=False):
    
    """
    Plot shoreline position through time for a Transect object.

    MDH, May 2026
    """

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    else:
        fig = ax.figure

    Dates = transect.HistoricShorelinesDates
    Positions = transect.HistoricShorelinesDistances

    if show_errors:
        ax.errorbar(Dates,Positions,yerr=Transect.HistoricShorelinesErrors,
            fmt="o",ecolor='gray', elinewidth=1, capsize=3, 
            label="Shoreline Positions with Errors'")
        
    else:
        ax.plot(Dates,Positions,fmt="o",
            label="Shoreline Positions")

    ax.set_title(f"Transect {transect.ID}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Relative Shoreline Position (m)")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    return fig, ax