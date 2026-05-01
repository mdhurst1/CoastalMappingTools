# import modules
import matplotlib.pyplot as plt

def PlotShorelineTimeseries(Transect, ax=None, show_errors=True, show_weights=False, StartDate=None, Regression=True):
    
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

    if Regression:
         RegressionLine = Transect.RegressionSlope*Dates + Transect.RegressionIntersect
         plt.fill_between(Dates, RegressionLine-Transect.RegressionConfidence, RegressionLine+Transect.RegressionConfidence,            regression_line3 - conf_interval,
                            color='gray', alpha=0.3, label='95% Confidence Interval')
            
            plt.plot(self.HistoricShorelinesYears, regression_line3, color='m', linestyle='--', label='Time-weighted Regression')
            plt.plot([self.HistoricShorelinesYears[0], self.HistoricShorelinesYears[-1]],[self.HistoricShorelinesDistance[0], self.HistoricShorelinesDistance[-1]],linestyle=':', color='g',label='Overall Rate')
            
            # Add labels and title
            plt.title("Montrose - Transect: " + str(self.ID))
            plt.xlabel('Dates')
            plt.ylabel('Relative Distance along transect (m)')
            
            # Rotate the x-axis labels for better visibility
            plt.xticks(rotation=45)
            
            # invert y-axis to more clearly demonstrate negative rates as erosional (further from offshore baseline)
            plt.gca().invert_yaxis()
            
            # Add legend
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=10)
            
         
    ax.set_title(f"Transect {transect.ID}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Relative Shoreline Position (m)")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)

    return fig, ax

            