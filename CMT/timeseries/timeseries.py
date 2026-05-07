# import module
import numpy as np

# new object to store generic timeseries data
# MDH May 2026

class TimeSeriesSignal:
    def __init__(self, name, dates=None, positions=None, errors=None, sources=None):
        
        # name here, could be MHWS, VEdge etc.
        self.name = name

        # set up object attributes and default if empty
        self.Dates = dates if dates is not None else []
        self.Positions = np.asarray(positions) if positions is not None else np.array([])
        self.Errors = np.asarray(errors) if errors is not None else None
        self.Sources = sources if sources is not None else []

        self.OrdinalDates = None
        self.Results = {}

    def Dates2Ordinal(self):
        self.OrdinalDates = np.array([d.toordinal() for d in self.Dates])
        return self.OrdinalDates

    #def has_data(self):
     #   return len(self.dates) > 1 and len(self.positions) > 1