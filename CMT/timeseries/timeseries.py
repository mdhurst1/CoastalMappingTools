# import module
import numpy as np
import bisect
from scipy.stats import theilslopes
# new object to store generic timeseries data
# MDH May 2026

class TimeSeriesSignal:
    def __init__(self, Name, Dates=None, Values=None, Errors=None, Sources=None):
        
        """

        Timeseries data object with methods for analysing the changing
        position of coastal change indicators

        MDH, May 2026

        """
        # name here, could be MHWS, VEdge etc.
        self.Name = Name

        # set up object attributes and default if empty
        self.Dates = list(Dates) if Dates is not None else []
        self.Values = list(Values) if Values is not None else []
        self.Errors = list(Errors) if Errors is not None else []
        self.Sources = list(Sources) if Sources is not None else []

        self.OrdinalDates = None

        self.PreferredRate=None

        self.Results = {}

    def AddObservation(self, Date, Value, Error=None, Source=None):
        
        if Date in self.Dates:
            Index = self.Dates.index(Date)

            self.Values[Index] = Value
            self.Errors[Index] = Error
            self.Sources[Index] = Source

            return
        
        # find position
        Index = bisect.bisect(self.Dates, Date)

        self.Dates.insert(Index, Date)
        self.Values.insert(Index, Value)
        self.Errors.insert(Index, Error)
        self.Sources.insert(Index, Source)

    def CalcEndPointRate(self):

        """
        End Point rate based on first and last observations in the timeseries

        MDH, May 2026

        """
    
        if not self.HasData(Minimum=2):
            return

        if self.OrdinalDates is None:
            self.Dates2Ordinal()

        # get total length of record in decimal years
        TotalDt = (self.OrdinalDates[-1] - self.OrdinalDates[0]) / 365.25

        if TotalDt == 0:
            return

        #Calculate rate
        Rate = (self.Values[-1] - self.Values[0]) / TotalDt

        # Calculate rate uncertainty
        Errors = self.ErrorsArray()
        if Errors is not None:
            RateUncertainty = np.sqrt(Errors[0]**2.+Errors[-1]**2.) / TotalDt
        else:
            RateUncertainty = None

        # save results
        self.Results["EPR"] = {
            "Method": "EPR",
            "Rate": Rate,
            "RateUncertainty": RateUncertainty,
            "StartDate": self.Dates[0],
            "EndDate": self.Dates[-1],
            "StartValue": self.Values[0],
            "EndValue": self.Values[-1],
        }
    
    def CalcOLSRate(self, Years=None, ResultName="OLS"):

        """
        Rate based on slope of ordinary least squares regression through timeseries

        If Years is provided, only observations within the last `Years`
        years of the timeseries are used.

        MDH, May 2026

        """

        if not self.HasData(Minimum=2):
            return

        if self.OrdinalDates is None:
            self.Dates2Ordinal()

        # convert lists to arrays
        DatesArray = self.OrdinalDates.astype(float)
        ValuesArray = self.ValuesArray()

        # optional recent-window filtering
        if Years is not None:

            EndDate = DatesArray[-1]
            StartDate = EndDate - Years * 365.25

            Mask = DatesArray >= StartDate

            DatesArray = DatesArray[Mask]
            ValuesArray = ValuesArray[Mask]

            if len(DatesArray) < 2:
                return
            
        # perform OLS
        Slope, Intercept = np.polyfit(DatesArray, ValuesArray, 1)

        # Calculate residuals and rate
        FittedValues = Slope*DatesArray + Intercept
        Residuals = ValuesArray - FittedValues
        Rate = Slope * 365.25

        # Calculate uncertainty
        NObs = len(ValuesArray)

        if NObs > 2:
            
            #Get variance in residuals
            Residual_SS = np.sum(Residuals**2) 
            Residual_Variance = Residual_SS / (NObs - 2)
            Sxx = np.sum((DatesArray-np.mean(DatesArray))**2)
            
            # get temporal spread
            Total_SS = np.sum((ValuesArray - np.mean(ValuesArray))**2)

            # calculate R2
            R2 = round(1. - (Residual_SS / Total_SS), 3)
            
            # get standard error on the Slope
            Rate_SE = np.sqrt(Residual_Variance / Sxx) * 365.25
            Rate_CI95 = 1.96 * Rate_SE

        else:
            # no errors if only 2 data points
            Rate_SE = None
            Rate_CI95 = None
            R2 = None

        # save results
        self.Results[ResultName] = {
            "Method": "Ordinary Least Squares" if Years is None else f"OLS last {Years} years",
            "Rate": Rate,
            "RateSE": Rate_SE,
            "RateUncertainty": Rate_CI95,
            "Intercept": Intercept,
            "Fitted": FittedValues,
            "Residuals": Residuals,
            "R2": R2,
            "N": NObs,
            "Years": Years,
            "StartDate": DatesArray[0],
            "EndDate": DatesArray[-1],
        }
    
    def CalcTheilSenRate(self):

        """
        Rate based on median slopes

        MDH, May 2026

        """

        if not self.HasData(Minimum=2):
            return

        if self.OrdinalDates is None:
            self.Dates2Ordinal()

        # convert lists to arrays
        DatesArray = self.OrdinalDates.astype(float)
        ValuesArray = self.ValuesArray()

        # perform theil sen rate analysis
        Slope_Days, Intercept, Slope_Low, Slope_High = theilslopes(ValuesArray, DatesArray, alpha=0.95)

        # get rates in per year
        Rate = Slope_Days * 365.25
        Rate_Low = Slope_Low * 365.25
        Rate_High = Slope_High * 365.25

        # Calculate residuals and rate
        FittedValues = Slope_Days*DatesArray + Intercept
        Residuals = ValuesArray - FittedValues

        # Calculate uncertainty
        NObs = len(ValuesArray)

        if NObs > 2:
            
            #Get variance in residuals
            Residual_SS = np.sum(Residuals**2) 
            Residual_Variance = Residual_SS / (NObs - 2)
            Sxx = np.sum((DatesArray-np.mean(DatesArray))**2)
            
            # get temporal spread
            Total_SS = np.sum((ValuesArray - np.mean(ValuesArray))**2)

            # calculate R2
            R2 = round(1. - (Residual_SS / Total_SS), 3)

        else:
            # no R2
            R2 = None


        self.Results["TheilSen"] = {
            "Method": "Theil-Sen Regression",
            "Rate": Rate,
            "RateCI95": (Rate_Low, Rate_High),
            "Intercept": Intercept,
            "Fitted": FittedValues,
            "Residuals": Residuals,
            "R2": R2,
            "N": len(self.Values),
        }    
    
    def CalcTimeWeightedRegression(self, TauYears):
        
        """
        Rate based on time-weighted regression as first implemented by Craig Macdonell

        TauYears is the scaling_factor i.e. e-folding timescale looking backward

        MDH, May 2026

        """
    
        if not self.HasData(Minimum=2):
            return None

        if self.OrdinalDates is None:
            self.Dates2Ordinal()

        # convert lists to arrays
        DatesArray = self.OrdinalDates.astype(float)
        ValuesArray = self.ValuesArray()

        # Calculate Time-Weights
        MaxDate = np.max(DatesArray)
        TauDays = TauYears * 365.25
        RecencyWeights = np.exp(-(MaxDate - DatesArray) / TauDays)

        # Caluclate uncertainty-weights
        Errors = self.ErrorsArray()
        if Errors is not None:
            ErrorWeights = 1.0 / Errors**2
        else:
            ErrorWeights = np.ones_like(DatesArray)
        
        # Combine weights
        Weights = RecencyWeights * ErrorWeights
        Weights = Weights / np.sum(Weights)

        # perform time-weighted OLS
        Slope, Intercept = np.polyfit(DatesArray, ValuesArray, 1, w=Weights)

        # Calculate residuals and rate
        FittedValues = Slope*DatesArray + Intercept
        Residuals = ValuesArray - FittedValues
        Rate = Slope * 365.25

        # Calculate uncertainty
        NObs = len(ValuesArray)

        if NObs > 2:
            
            #Get variance in weighted residuals
            Residual_SS = np.sum(Weights*Residuals**2) 
            Residual_Variance = Residual_SS / (NObs - 2)
            Sxx = np.sum((DatesArray-np.mean(DatesArray))**2)
            
            # get temporal spread
            Total_SS = np.sum((ValuesArray - np.mean(ValuesArray))**2)

            # calculate R2
            R2 = round(1. - (Residual_SS / Total_SS), 3)
            
            # get standard error on the Slope
            Rate_SE = np.sqrt(Residual_Variance / Sxx) * 365.25
            Rate_CI95 = 1.96 * Rate_SE

        else:
            # no errors if only 2 data points
            R2 = None
            Rate_SE = None
            Rate_CI95 = None

        # save results
        self.Results["TWR"] = {
            "Method": "Time-weighted Regression",
            "Rate": Rate,
            "RateSE": Rate_SE,
            "RateUncertainty": Rate_CI95,
            "Intercept": Intercept,
            "Fitted": FittedValues,
            "Residuals": Residuals,
            "R2": R2,
            "Weights": Weights,
            "TauYears": TauYears,
            "N": NObs,
        }

    def Analyse(self, TauYears=10):
        """
        Wrapper function to launch all forms of regression analysis
        
        MDH, May 2026
        
        """
        self.CalcEndPointRate()
        self.CalcOLSRate()
        self.CalcOLSRate(Years=5, ResultName="OLS5")
        self.CalcOLSRate(Years=10, ResultName="OLS10")
        self.CalcTheilSenRate()
        self.CalcTimeWeightedRegression(TauYears)

    """ FIGURE THESE OUT LATER"""
    def Dates2Ordinal(self):
        self.OrdinalDates = np.array([d.toordinal() for d in self.Dates])
        return self.OrdinalDates

    def HasData(self, Minimum=2):
        return len(self.Dates) >= Minimum and len(self.Values) >= Minimum
    
    def ValuesArray(self):
        return np.asarray(self.Values, dtype=float)

    def ErrorsArray(self):
        if len(self.Errors) == 0 or all(Error is None for Error in self.Errors):
            return None
        return np.asarray(self.Errors, dtype=float)