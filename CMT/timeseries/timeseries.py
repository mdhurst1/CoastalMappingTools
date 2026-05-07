# import module
import numpy as np
import bisect
# new object to store generic timeseries data
# MDH May 2026

class TimeSeriesSignal:
    def __init__(self, Name, Dates=None, Positions=None, Distances=None, Errors=None, Sources=None):
        
        # name here, could be MHWS, VEdge etc.
        self.Name = Name

        # set up object attributes and default if empty
        self.Dates = Dates if Dates is not None else []
        self.Positions = np.asarray(Positions) if Positions is not None else np.array([])
        self.Distances = np.asarray(Distances) if Distances is not None else np.array([])
        self.Errors = np.asarray(Errors) if Errors is not None else None
        self.Sources = Sources if Sources is not None else []

        self.OrdinalDates = None
        self.Results = {}

    def AddObservation(self, Date, Position, Distance, Error=None, Source=None):
        
        # find position
        Index = bisect.bisect(self.Dates, Date)

        self.Dates.insert(Index, Date)
        self.Positions.insert(Index, Position)
        self.Distances.insert(Index, Distance)
        self.Errors.insert(Index, Error)
        self.Sources.insert(Index, Source)

    def Dates2Ordinal(self):
        self.OrdinalDates = np.array([d.toordinal() for d in self.Dates])
        return self.OrdinalDates

    #def has_data(self):
     #   return len(self.dates) > 1 and len(self.positions) > 1