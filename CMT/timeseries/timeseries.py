# import module
import numpy as np
import bisect
# new object to store generic timeseries data
# MDH May 2026

class TimeSeriesSignal:
    def __init__(self, Name, Dates=None, Positions=None, Distances=None, Errors=None, Sources=None):
        
        """

        Timeseries data object with methods for analysing the changing
        position of coastal change indicators

        MDH, May 2026

        """
        # name here, could be MHWS, VEdge etc.
        self.Name = Name

        # set up object attributes and default if empty
        self.Dates = list(Dates) if Dates is not None else []
        self.Positions = list(Positions) if Positions is not None else []
        self.Distances = list(Distances) if Distances is not None else []
        self.Errors = list(Errors) if Errors is not None else []
        self.Sources = list(Sources) if Sources is not None else []

        self.OrdinalDates = None

        self.PreferredRate=None

        self.Results = {}

    def AddObservation(self, Date, Position, Distance, Error=None, Source=None):
        
        # find position
        Index = bisect.bisect(self.Dates, Date)

        self.Dates.insert(Index, Date)
        self.Positions.insert(Index, Position)
        self.Distances.insert(Index, Distance)
        self.Errors.insert(Index, Error)
        self.Sources.insert(Index, Source)

    def CalcEndPointRate(self):

        """
        End Point rate based on first and last observations in the timeseries

        MDH, May 2026

        """
    
        if not self.HasData(Minimum=2):
            return

        if not self.OrdinalDates:
            Dates2Ordinal()

        # get total length of record in decimal years
        TotalDt = (self.OrdinalDates[-1] - self.OrdinalDates[0]) / 365.25

        if TotalDt == 0:
            return

        #Calculate rate
        Rate = (self.Distances[-1] - self.Distances[0]) / TotalDt

        # Calculate rate uncertainty
        if self.Errors is not None:
            RateUncertainty = np.sqrt(self.Errors[0]**2.+self.Errors[-1]**2.) / TotalDt

        # save results
        self.Results["EPR"] = {
            "Method": "EPR",
            "Rate": Rate,
            "RateUncertainty": RateUncertainty
            "StartDate": self.Dates[0],
            "EndDate": self.Dates[-1],
            "StartDistance": self.Distances[0],
            "EndDistance": self.Distances[-1],
        }
    
    def CalcOLSRate(self):

        """
        Rate based on slope of ordinary least squares regression through timeseries

        MDH, May 2026

        """

        if not self.HasData(Minimum=2):
            return

        if not self.OrdinalDates:
            Dates2Ordinal()

        # perform OLS
        Slope, Intercept = np.polyfit(self.OrdinalDates, self.Distances, 1)

        # Calculate residuals and rate
        FittedDistances = Slope*self.OrdinalDates + Intercept
        Residuals = self.Distances - FittedDistances
        Rate = Slope * 365.25

        # Calculate uncertainty
        NObs = len(self.Distances)

        if NObs > 2:
            
            #Get variance in residuals
            ResidualVariance = np.sum(Residuals**2) / (NObs - 2)

            # get temporal spread
            sxx = np.sum((self.OrdinalDates - np.mean(self.OrdinalDates))**2)

            # get standard error on the Slope
            Rate_SE = np.sqrt(residual_variance / sxx) * 365.25
            Rate_CI95 = 1.96 * Rate_SE

        else:
            # no errors if only 2 data points
            Rate_SE = None
            Rate_CI95 = None

        # save results
        self.Results["OLS"] = {
            "Method": "Ordinary Least Squares",
            "Rate": Rate,
            "RateSE": Rate_SE,
            "RateCI95": Rate_CI95,
            "Intercept": Intercept,
            "Fitted": FittedDistances,
            "Residuals": Residuals,
            "N": NObs,
        }
    
    def CalcTheilSenRate(self):

        """
        Rate based on median slopes

        MDH, May 2026

        """
    
    def CalcTimeWeightedRegression(self):
        """
        Rate based on time-weighted regression as implemented by Craig Macdonell

        MDH, May 2026

        """
    

    """ FIGURE THESE OUT LATER"""
    def Dates2Ordinal(self):
        self.OrdinalDates = np.array([d.toordinal() for d in self.Dates])
        return self.OrdinalDates

    def HasData(self, Minimum=2):
        return len(self.Dates) >= Minimum and len(self.Distances) >= Minimum
    
    def DistancesArray(self):
        return np.asarray(self.Distances, dtype=float)

    def ErrorsArray(self):
        if len(self.Errors) == 0 or all(Error is None for Error in self.Errors):
            return None