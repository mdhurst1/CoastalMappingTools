"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

import numpy as np
import numpy.ma as ma
from scipy.stats import t
import os, sys

#import figure plotting stuff here not globally!
import matplotlib
#matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams, cm

import rasterio
import pandas as pd
import geopandas as gp
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from shapely.geometry import Point, Polygon, LineString, MultiLineString, MultiPoint

from openpyxl import load_workbook

# import other custom classes
from CMT.Node import *
from CMT.timeseries.timeseries import *

from shapely.geometry import Point, LineString

# Customise figure font style
# Set up fonts for plots
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['arial']
rcParams['font.size'] = 10
rcParams['text.usetex'] = False ##True  NH: SET TO FALSE as don't have latex installed. Else plot fails

class Transect:
    """
    Description of object goes here

    """
    def __init__(self, CoastNode, StartNode, EndNode, LineID, ID, Cell=None, SubCell=None, CMU=None):
        
        self.ID = ID
        self.LineID = LineID
        self.Cell = Cell
        self.SubCell = SubCell
        self.CMU = CMU
        
        # transect positioning
        self.CoastNode = CoastNode
        self.StartNode = StartNode
        self.EndNode = EndNode
        self.HinterlandNode = None
        self.LineString = LineString(((self.StartNode.X,self.StartNode.Y),(self.EndNode.X,self.EndNode.Y)))
        self.Orientation = self.CalculateOrientation(self.StartNode, self.EndNode)
        self.Length = self.CalculateLength(self.StartNode, self.EndNode)
        self.Overlaps = False
        
        # historic shoreline positions, distances and change rates
        
        self.HistoricFlag = False
        self.HistoricShorelinesSources = []
        self.HistoricShorelinesDates = []
        self.OSYear = False
        self.HistoricShorelinesPositions = [] # do we need both of these
        self.HistoricShorelinesDistances = [] #
        self.HistoricShorelinesPosition = [] #
        self.HistoricShorelinesDistance = [] #
        self.HistoricShorelinesErrors = []
        self.DC1 = []
        
        # change rates will be 1 less than no of positions
        self.ChangeRates = []
        self.ChangeRateErrors = []
        self.ChangeRate = None      # value used in calibration
        self.MinChangeRate = None
        self.MaxChangeRate = None
        self.DeleteFlag = False

        # Regression info
        self.RegressionIntercept = None
        self.RegressionSlope = None
        self.RegressionConfidence = None

        # historic vegetation edge positions, distances and change rates
        self.VEdgeFlag = False
        self.HistoricVEdgeSources = []
        self.HistoricVEdgeDates = []
        self.HistoricVEdgePositions = [] 
        self.HistoricVEdgeDistances = [] 
        self.HistoricVEdgeErrors = []
        
        # set up dictionary to store all timeseries info
        self.Timeseries = {}

        # rock head info
        self.RockHeadDistance = None
        self.RockHeadPosition = None

        # defences info
        self.Defences = False
        self.DefencesDistance = None
        self.DefencesPosition = None

        # location of -10m depth contour
        self.Contours = []
        self.ClosureDepth = 10.
        self.ShorefaceDistance = None
        self.ShorefaceSlope = None
        self.HinterlandSlope = None

        # relative sea level rise history (rate in mm/year)
        self.HistoricalRSLR = None
        self.InterpolatedRSLR = []
        
        # future sea level rise
        self.Future = False
        self.LongTermOnly = False
        self.CalibrationYear = None
        self.FutureSeaLevelYears = []
        self.FutureSeaLevels = []
        self.FutureShorelinesPositions = []
        self.FutureShorelinesRates = []
        self.FutureShorelinesDistances = []
        self.FutureShorelineMinDistance = None
        self.FutureShorelineMaxDistance = None
        self.VegEdge = False

        # transect data
        self.HaveTopography = False
        self.NoValues = None
        self.DistanceSpacing = None
        self.DistanceNodes = None
        self.Distance = None
        self.Elevation = None
        self.Distance2 = None
        self.Elevation2 = None
        self.ElevationMin = None
        self.ElevationMax = None
        self.ElevStd = None
        
        # Elevation interpolation
        self.InterpolationIncomplete = False
        self.X = None
        self.Y = None
        self.Z = None
        self.DistAlong = None
        self.DistTo = None

        # cliff metrics
        self.Cliff = False
        self.CliffTopInd = None
        self.CliffToeInd = None
        self.CliffHeight = None
        self.CliffSlope = None
        self.Rocky = False
        self.RockHeadPosition = None
        
        # intertidal
        self.SlopeRoughness = None
        self.ElevationRoughness = None
        self.MLWSIntersect = None
        self.MHWSIntersect = None
        self.ForeshoreSlope = None
        self.IntertidalSlope = None
        self.IntertidalDepth = None
        self.IntertidalDistance = None

        # barrier metrics
        self.Barrier = False
        self.FrontHeight = None
        self.FrontTopInd = None
        self.FrontToeInd = None
        self.BackHeight = None
        self.BackTopInd = None
        self.BackToeInd = None
        self.CrestInd = None
        self.CrestElevation = None
        self.ToeWidth = None
        self.TopWidth = None
        self.FrontSlope = None
        self.BackSlope = None
        self.BarrierVolume = None
        self.HinterlandHigher = False

        # other barrier metrics for extreme water levels
        # will need short term and long term here?
        self.MHWS = None
        self.ExtremeWaterLevels = None
        self.Intersection = None
        self.IntersectionIndices = None
        self.IntersectionNodes = []
        self.InterpolateFractions = None
        self.FrontNode = None
        self.BackNode = None
        self.ExtremeFrontNodes = ["","",""]
        self.ExtremeBackNodes = ["","",""]
        self.ExtremeDistance = None
        self.ExtremeIndices = []
        self.ExtremeIndicesLists = ["","",""]
        self.ExtremeDistances = ["","",""]
        self.ExtremeInterpFractions = ["","",""]
        self.ExtremeWidth = None
        self.ExtremeWidthTotal = None
        self.ExtremeWidths = ["","",""]
        self.ExtremeTotalWidths = ["","",""]
        self.ExtremeVolume = None
        self.ExtremeVolumeTotal = None
        self.ExtremeVolumes = ["","",""]
        self.ExtremeTotalVolumes = ["","",""]
        
        # storm impact analysis
        # H=historic, M=mid-century, E=end-century, 45=RCP4.5, 85=RCP8.5
        # wave parameters: peak wave period Tp, significant wave height Hs
        self.H_Tp_p99 = None
        self.M45_Tp_p99 = None
        self.E45_Tp_p99 = None
        self.M85_Tp_p99 = None
        self.E85_Tp_p99 = None
        self.H_Hs_p99 = None
        self.M45_Hs_p99 = None
        self.E45_Hs_p99 = None
        self.M85_Hs_p99 = None
        self.E85_Hs_p99 = None
        # derived wave parameters
        self.H_WaveSteepness = None
        self.M45_WaveSteepness = None
        self.E45_WaveSteepness = None
        self.M85_WaveSteepness = None
        self.E85_WaveSteepness = None
        self.H_Iribarren = None
        self.M45_Iribarren = None
        self.E45_Iribarren = None
        self.M85_Iribarren = None
        self.E85_Iribarren = None
        # extreme wave runup
        self.H_R2 = None
        self.M45_R2 = None
        self.M85_R2 = None
        self.E45_R2 = None
        self.E85_R2 = None
        self.H_setup = None
        self.M45_setup = None
        self.M85_setup = None
        self.E45_setup = None
        self.E85_setup = None
        self.H_Dissipative = None
        self.M45_Dissipative = None
        self.M85_Dissipative = None
        self.E45_Dissipative = None
        self.E85_Dissipative = None
        self.PureGravel = None
        # extreme still water level
        self.H_ESL = None
        self.H_ESL_c1 = None
        self.H_ESL_c3 = None
        self.M45_ESL = None
        self.M45_ESL_c1 = None
        self.M45_ESL_c3 = None
        self.M85_ESL = None
        self.M85_ESL_c1 = None
        self.M85_ESL_c3 = None
        self.E45_ESL = None
        self.E45_ESL_c1 = None
        self.E45_ESL_c3 = None
        self.E85_ESL = None
        self.E85_ESL_c1 = None
        self.E85_ESL_c3 = None
        # extreme total water level
        self.H_TWL = None
        self.M45_TWL = None
        self.M85_TWL = None
        self.E45_TWL = None
        self.E85_TWL = None
        self.H_TWL_setup = None
        self.M45_TWL_setup = None
        self.M85_TWL_setup = None
        self.E45_TWL_setup = None
        self.E85_TWL_setup = None
        # Storm impact scale
        self.H_StormImpactScale = None
        self.M45_StormImpactScale = None
        self.M85_StormImpactScale = None
        self.E45_StormImpactScale = None
        self.E85_StormImpactScale = None
        self.NearestDC2Idx = None
        self.M45_Erosion = None
        self.M85_Erosion = None
        self.E45_Erosion = None
        self.E85_Erosion = None
        self.M45_SLR = None
        self.M85_SLR = None
        self.E45_SLR = None
        self.E85_SLR = None
        # Present day dune elevations
        self.H_FrontToe = None
        self.H_FrontTop = None
        self.H_BackToe = None
        self.H_BackTop = None
        self.H_Crest = None
        # Estimated future dune front toe and crest elevations
        self.M45_FrontToe = None
        self.M85_FrontToe = None
        self.E45_FrontToe = None
        self.E85_FrontToe = None
        self.M45_Crest = None
        self.M85_Crest = None
        self.E45_Crest = None
        self.E85_Crest = None
        # Esimated headroom: difference between dune crest elev and total water level
        self.H_Headroom = None
        self.M45_Headroom = None
        self.M85_Headroom = None
        self.E45_Headroom = None
        self.E85_Headroom = None
        self.HinterlandElev = None
        # Barrier drowned if future toe exceeds future crest elevation
        self.M45_BarrierDrowning = None
        self.E45_BarrierDrowning = None
        self.M85_BarrierDrowning = None
        self.E85_BarrierDrowning = None
        # shingle habitat intersected
        self.Shingle = None
        # Asset location
        self.RoadsIntersect = None
        self.RailIntersect = None
        self.FirstAssetDist = None
        self.FirstRoadDist = None
        self.FirstRailDist = None
        self.FirstPropertyDist = None
        self.FirstAssetElev = None
        self.FirstRoadElev = None
        self.FirstRailElev = None
        self.FirstPropertyElev = None
        # Barrier search window
        self.SeawardMask = None
        self.LandwardMask = None
    
    def __str__(self):
        String = "Transect Object:\nID: %s\n" % (str(self.ID))
        String += "StartNode: "
        String += self.StartNode.__str__()
        String += "EndNode: "
        String += self.EndNode.__str__()

        String += "Historical shorelines years and distances"
        String += self.HistoricShorelinesDates
        String += self.HistoricalShorelinesDistances

        return String
    
    def ResetHistoricShorelines(self):
        
        # historic shoreline positions, distances and change rates
        self.HistoricFlag = False
        self.HistoricShorelinesSources = []
        self.HistoricShorelinesDates = []
        self.OSYear = False
        self.HistoricShorelinesPositions = []
        self.HistoricShorelinesDistances = []
        self.HistoricShorelinesPosition = []
        self.HistoricShorelinesDistance = []
        self.HistoricShorelinesErrors = []
        self.DC1 = []

        # change rates will be 1 less than no of positions
        self.ChangeRates = []
        self.ChangeRateErrors = []
        self.ChangeRate = None      # value used in calibration
        self.DeleteFlag = False

    def Redraw(self, StartNode, EndNode):
        
        self.StartNode = StartNode
        self.EndNode = EndNode
        self.LineString = LineString(((self.StartNode.X,self.StartNode.Y),(self.EndNode.X,self.EndNode.Y)))
        self.Orientation = self.CalculateOrientation(self.StartNode, self.EndNode)
        self.Length = self.CalculateLength(self.StartNode, self.EndNode)

    def CalculateOrientation(self, Node1, Node2):
        
        """
        
        Maybe this could be a more general function external to class?
        
        MDH
        
        """
        
        #calculate the spatial change
        dx = Node2.X - Node1.X
        dy = Node2.Y - Node1.Y

        #Calculate the orientation of the line
        #N.B. this will depend on where the start segment is
        #so that 270 is esseintially the same as 90 but depends
        #which end of the line the cycle starts at
        if dx > 0 and dy > 0:
            Orientation = np.degrees( np.arctan( dx / dy ) )
        elif dx > 0 and dy < 0:
            Orientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy < 0:
            Orientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy > 0:
            Orientation = 360 + np.degrees( np.arctan( dx / dy ) )
            
        return Orientation
    
    def CalculateLength(self, Node1, Node2):
        
        """
        
        Maybe this could be a more general function external to class?
        
        MDH
        
        """
        
        #calculate the spatial change
        dx = Node2.X - Node1.X
        dy = Node2.Y - Node1.Y
        
        return np.sqrt(dx**2 + dy**2.)

    def ExtendTransect(self, Distance2Land=0, Distance2Sea=0):

        """

        Function to extend transects

        MDH, August 2019

        """
        
        # extend transect landward and seaward?
        X1 = self.StartNode.X - Distance2Sea * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y - Distance2Sea * np.cos( np.radians( self.Orientation ) )
        self.StartNode = Node(X1,Y1)
        
        X1 = self.EndNode.X + Distance2Land * np.sin( np.radians( self.Orientation ) )
        Y1 = self.EndNode.Y + Distance2Land * np.cos( np.radians( self.Orientation ) )
        self.EndNode = Node(X1,Y1)

        self.Length = self.CalculateLength(self.StartNode, self.EndNode)
        
    def Truncate(self, MinLength=25., Year=2100):
        
        """
        Function to truncate transects to limits of historical and future 
        shoreline positions and uncertainty
        
        MDH, November 2020
        
        """
        
        # if self.Future:
        #     self.PredictFutureShorelineUncertainty(Year)
        # else:
        #     return
            
        # get all distances
        DistancesList = []
        
        #if self.LineID == "24" and self.ID == "28":
            #import pdb
            #pdb.set_trace()
        
        for i in range(0,len(self.HistoricShorelinesDates)):
            
            # add nodes to lists
            DistancesList.append(self.HistoricShorelinesDistances[i][0])
            DistancesList.append(self.HistoricShorelinesDistances[i][0]+self.HistoricShorelinesErrors[i])
            DistancesList.append(self.HistoricShorelinesDistances[i][0]-self.HistoricShorelinesErrors[i])
        
        # need a condition here to ignore distances from future where accretion is occuring
        
        for i in range(0, len(self.FutureSeaLevelYears)):
            
            # add nodes to lists
            if self.FutureShorelinesDistances[i] > TS.Distances[-1][0]:
                DistancesList.append(self.FutureShorelinesDistances[i])
                    
        # find index of min distance
        MinDistance = np.min(np.array(DistancesList))
        MaxDistance = np.max(np.array(DistancesList))
        
        # find new end position
        X1 = self.StartNode.X + MaxDistance * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + MaxDistance * np.cos( np.radians( self.Orientation ) )
        self.EndNode = Node(X1,Y1)
    
        X1 = self.StartNode.X + MinDistance * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + MinDistance * np.cos( np.radians( self.Orientation ) )
        self.StartNode = Node(X1,Y1)
        
        # check length and extend in either direction if needs be
        Length = self.StartNode.get_Distance(self.EndNode)
        
        if Length < MinLength:
            
            Difference = MinLength - Length
            
            # find new end position
            X1 = self.EndNode.X + 0.5*Difference * np.sin( np.radians( self.Orientation ) )
            Y1 = self.EndNode.Y + 0.5*Difference * np.cos( np.radians( self.Orientation ) )
            self.EndNode = Node(X1,Y1)
        
            # find new start position
            X1 = self.StartNode.X - 0.5*Difference * np.sin( np.radians( self.Orientation ) )
            Y1 = self.StartNode.Y - 0.5*Difference * np.cos( np.radians( self.Orientation ) )
            self.StartNode = Node(X1,Y1)

    def Truncate2Coast(self, D_start, D_end):
        
        """
        Function to truncate transects between specified
        start and end distances either side of CoastNode.
        Can also extend transects.
        
        D_start: distance (m) seaward of CoastNode
        D_end: distance (m) landward of CoastNode
        
        NH, September 2024
        
        """
        
        # error check input params. Limit upper values to the current entire transect length
        if (D_start < 0 or D_start > self.Length):
            sys.exit("Transect.Truncate2Coast: Invalid start distance")
        if (D_end < 0 or D_end > self.Length):
            sys.exit("Transect.Truncate2Coast: Invalid end distance")
        
        # find new start position
        X1 = self.CoastNode.X - D_start * np.sin( np.radians( self.Orientation ) )
        Y1 = self.CoastNode.Y - D_start * np.cos( np.radians( self.Orientation ) )
        self.StartNode = Node(X1,Y1)
        
        # find new end position
        X1 = self.CoastNode.X + D_end * np.sin( np.radians( self.Orientation ) )
        Y1 = self.CoastNode.Y + D_end * np.cos( np.radians( self.Orientation ) )
        self.EndNode = Node(X1,Y1)
    
    def GenerateSampleNodes(self,Spacing=None):

        """ 
        Function to generate regularly spaced nodes along the transect

        MDH, March 2020
        
        """

        if Spacing:
            self.DistanceSpacing = Spacing
        
        self.NoNodes = int(np.ceil(self.Length/self.DistanceSpacing))

        # create nodes
        XNodes = np.linspace(self.StartNode.X, self.EndNode.X, self.NoNodes-1)
        YNodes = np.linspace(self.StartNode.Y, self.EndNode.Y, self.NoNodes-1)
        self.DistanceNodes = [Node(X,Y) for X, Y in zip(XNodes,YNodes)]
        self.Distance = [self.StartNode.get_Distance(ThisNode) for ThisNode in self.DistanceNodes]

    def SampleDEM(self,DEM):

        """
        Function to sample elevations from a single DEM on a single transect
        
        MDH, July, 2022
        
        """
        DTM_Dataset = rasterio.open(DEM)
        DTMArray = DTM_Dataset.read(1)
        NCols = DTM_Dataset.width
        NRows = DTM_Dataset.height
        NDV = DTM_Dataset.nodata
        Resolutions = DTM_Dataset.res
        
        # check if we're missing no data
        if not DTM_Dataset.nodata:
            raise SystemExit("DTM missing no data value")

        # check for square pixels
        if not DTM_Dataset.res[0] == DTM_Dataset.res[1]:
            raise SystemExit("DTM has non-square cells")
    
        # get resolution
        DTM_Resolution = DTM_Dataset.res[0]

        # get extent of DTM and set up polygon of extent
        XMin = DTM_Dataset.bounds[0]
        XMax = DTM_Dataset.bounds[2]
        YMin = DTM_Dataset.bounds[1]
        YMax = DTM_Dataset.bounds[3]
        DTM_Extent = Polygon([[XMin, YMin], [XMin, YMax], [XMax, YMax], [XMax, YMin]])

        # Get vectors of X and Y coordinates, NB reversal of Y in line with 
        # DTM indexing from top left
        XVector = XMin+np.arange(0,NCols)*DTM_Resolution+0.5*DTM_Resolution
        YVector = YMin+DTM_Resolution*np.arange(0,NRows)[::-1]+0.5*DTM_Resolution
        # check we have nodes to sample
        if not self.DistanceNodes:
            self.DistanceSpacing = DTM_Dataset.res[0]
            self.GenerateSampleNodes()

        # check for intersection
        if not self.LineString.intersects(DTM_Extent):
            print("Transect does not intersect DTM")
            return
        
        # get list of points that intersect DTM only
        Points = [Point(ThisNode.X,ThisNode.Y) for ThisNode in self.DistanceNodes]
        Points = [ThisPoint if ThisPoint.within(DTM_Extent) else Point((0,0)) for ThisPoint in Points]
        Coords = [(Point.x, Point.y) for Point in Points]
        Elevations = [Sample[0] for Sample in DTM_Dataset.sample(Coords)]
        
        # problem here gettign back to transects
        for i, ThisNode in enumerate(self.DistanceNodes):
            
            if not ThisNode.Z and Elevations[i] > 0:
                self.DistanceNodes[i].Z = Elevations[i]

        # Set up the mask from NDVs
        Mask = Elevations == NDV
        self.Distance2 = ma.masked_where(Mask,self.Distance)
        self.Elevation2 = ma.masked_where(Mask,Elevations)

        # self.HaveTopography = True


    def CalculateHinterlandSlope(self):

        """
        function to calculate the mean hinterland slope for transects with hinterland topography
        extracted. Fits linear regression to elevation as function of distance

        MDH, April 2020

        """

        if not self.HaveTopography:
            self.HinterlandSlope = 1.
            return

        # isolate distance and elevation
        Nodes = [ThisNode for ThisNode in self.DistanceNodes if ThisNode.Z]
        Distances = np.array([ThisNode.get_Distance(self.StartNode) for ThisNode in Nodes if ThisNode.Z > 0])
        Elevations = np.array([ThisNode.Z for ThisNode in Nodes if ThisNode.Z > 0])

        # normalise distances to minimum value (i.e. make lowest = zero)
        if len(Distances) == 0:
            self.HinterlandSlope = 1.
            return
            
        Distances = Distances-np.min(Distances)

        # weight solution inversely with distance
        Weights = np.sqrt(np.max(Distances)-Distances)

        # claculated weighted values
        WeightedDistances = Distances * Weights
        WeightedElevations = Elevations * Weights

        # weighted linear regression with forced intercept of zero
        Slope = np.linalg.lstsq(WeightedDistances[:,np.newaxis],WeightedElevations,rcond=None)[0]
        #Slope = np.linalg.lstsq(Distances[:,np.newaxis], Elevations)[0]
        
        if Slope[0] <= 0:
            print("Zero or negative Hinterland Slope")
            self.HinterlandSlope = 0.001
        else:
            self.HinterlandSlope = Slope[0]
    
    def AddTimeseries(self, Name, Dates=None, Positions=None, Distances=None, Errors=None, Sources=None):
    
        """
        Add a time series signal to this transect, e.g. MHWS or vegetation edge.

        MDH May 2026

        """
        self.Timeseries[Name] = TimeSeriesSignal(
            Name=Name,
            Dates=Dates,
            Positions=Positions,
            Distances=Distances,
            Errors=Errors,
            Sources=Sources)
        
    def AddTimeseriesObservation(self, Name, Date, Position, Distance, Error=None, Source=None):
        
        """
        Add timeseries observation to object

        MDH, May 2026

        """
        # create timeseries object if it doesnt already exist
        if Name not in self.Timeseries:
            self.AddTimeseries(Name)

        self.Timeseries[Name].AddObservation(
            Date=Date,
            Position=Position,
            Distance=Distance,
            Error=Error,
            Source=Source
        )

    def AnalyseTimeseries(self, TauYears=10):

        """
        Function to call all regression analyses on all timeseries
        
        MDH, May 2026
        
        """
        
        for Signal in self.Timeseries.values():
            Signal.Analyse(TauYears=TauYears)

    """
    def get_signal(self, name):
        return self.signals.get(name, None)


    def iter_signals(self):
        return self.signals.values()
    """

    def CalculateIntertidalSlope(self):
        
        if not self.MLWS:
            print("No MLWS data")
            import pdb
            pdb.set_trace()
            
        elif not self.HistoricShorelinesPositions:
            return

        else:
            self.ShorefaceDistance = self.MLWS.get_Distance(self.HistoricShorelinesPositions[-1][0])
            self.ShorefaceDepth = 2.*self.MHWS
            self.ShorefaceSlope = self.ShorefaceDepth/self.ShorefaceDistance
        
        # set minimum shoreface slope to 0.001
        if self.ShorefaceSlope < 0.001:
            self.ShorefaceSlope = 0.001
            
            
    def CalculateIntertidalSlope2(self):
    
        """
        
        Function to extract transect's slope between MHWS and MLWS intersect nodes. 
        If no MLWS intersect node, use nearest MLWS node (from ExtractMLWS()). 
        
        NH Spetembeer 2023

        (NOW SUPERSEDED BY CalculateIntertidalSlope3())

        """
        
        # Check if the nodes exist
        if not self.MLWSIntersect.X:
            print(self.LineID, self.ID, "CalculateIntertidalSlope2: No MLWS intersect data")
            if not self.MLWS.X:
                print(self.LineID, self.ID, "CalculateIntertidalSlope2: No MLWS nearest data either!")
                self.IntertidalSlope = -1
                return
            else:
                # Use MLWS data
                MLWSNode = self.MLWS
                print("\t\t\t\tUsing nearest MLWS node")
        else:
            # use MLWSIntersect data
            MLWSNode = self.MLWSIntersect
            
        if not self.MHWSIntersect.X:
            print(self.LineID, self.ID, "CalculateIntertidalSlope2: No MHWSIntersect!")
            self.IntertidalSlope = -1
            return

        # check if elevation data exists
        if not MLWSNode.Z:
            print(self.LineID, self.ID, "CalculateIntertidalSlope2: No MLWS elevation!")
            self.IntertidalSlope = -1
            return
        if not self.MHWSIntersect.Z:
            print(self.LineID, self.ID, "CalculateIntertidalSlope2: No MHWS elevation!")
            self.IntertidalSlope = -1
            return   
        
        self.IntertidalDistance = MLWSNode.get_Distance(self.MHWSIntersect)
        self.IntertidalDepth = self.MHWSIntersect.Z - MLWSNode.Z
        self.IntertidalSlope = self.IntertidalDepth/self.IntertidalDistance
        
        # set minimum shoreface slope to 0.001
        if self.IntertidalSlope < 0.001:
            self.IntertidalSlope = 0.001
    
    def CalculateIntertidalSlope3(self):
    
        """
        
        Function to extract transect's slope between MHWS and MLWS contours. 
        dz = 2*MWHS elevation, assuming sinusoidal tidal elevations
        dx = distance between MHWS and MLWS contour intersections
        If no MLWS intersect node, use nearest MLWS node (from ExtractMLWS()). 
        
        This code improves v2 of the function, as the elevation data is only really
        valid landward of MHWS. Seaward elevations do exist in OST5 and LiDAR, but
        are either the water level elevations (LiDAR) or linear line to a predifined min
        (OST5), thus not a representation of nearshore bathymetry.
        
        NH Jan 2024
        
        """
        
        # Check if the nodes exist
        # If MLWS intersections does not exist, use nearest point to MLWS contour
        if not self.MLWSIntersect.X:
            print(self.LineID, self.ID, "CalculateIntertidalSlope3: No MLWS intersect data")
            if not self.MLWS.X:
                print(self.LineID, self.ID, "CalculateIntertidalSlope3: No MLWS nearest data either!")
                self.IntertidalSlope = -1
                sys.exit()
            else:
                # Use MLWS data
                MLWSNode = self.MLWS
                print("\t\t\t\tUsing nearest MLWS node")
        else:
            # use MLWSIntersect data
            MLWSNode = self.MLWSIntersect
            
        if not self.MHWSIntersect.X:
            print(self.LineID, self.ID, "CalculateIntertidalSlope3: No MHWSIntersect!")
            self.IntertidalSlope = -1
            sys.exit()

        # Check if MHWS elevation data exists
        if not self.MHWS:
            print(self.LineID, self.ID, "CalculateIntertidalSlope3: No MHWS elevation data!")
            self.IntertidalSlope = -1
            sys.exit()
        
        self.IntertidalDistance = MLWSNode.get_Distance(self.MHWSIntersect)
        self.IntertidalDepth = 2*self.MHWS
        self.IntertidalSlope = self.IntertidalDepth/self.IntertidalDistance
        
        # set minimum shoreface slope to 0.001
        if self.IntertidalSlope < 0.001:
            self.IntertidalSlope = 0.001
            
            
    def ExtractIndex(self, Elev=None, Landward=True):
    
        """
        Starting at the seaward end, function to return the index of the 
        node in Transect.Elevation that is immediately landward or seaward 
        of the specified elevation.
        
        Returns -1 if no elevation specified, or no elevation greater than Elev found.
        
        Parameters
        ----------
        Elev - float
            Decimal number of the elevation of interest
        Landward - boolean
            Flag to specifiy whether to return the first elevation landward (or seaward)
            of the elevation of interest
        
        NH, October 2023
        
        Works
    
        """
        
        # Check parameters were passed
        if Elev is None:
            print("\tTransect.ExtractIndex: Elev not specified!")
            return -1
        
        # Find indexes of transect elevations greater than Elev: boolean array
        elev_of_interest = self.Elevation > Elev
        
        # Check anything was found
        if sum(elev_of_interest) == 0:
            print(f"\tTransect.ExtractIndex: No Elevation above {Elev} m!")
            return -1
        
        # Find the smallest index (most seaward)
        for i in range(0, len(elev_of_interest)):
            if elev_of_interest[i]:
                if Landward:
                    return i
                else:
                    if i > 0:
                        return i-1
                    else:
                        return i
            else:
                continue
    
    def PredictFutureShorelines(self, MaxRockHeadErosionDistance=25., MinMaxFlag=None, Timeseries="MHWS", RateMethod="TWR"):

        """
        Function to predict the future position of the shoreline based on
        historical shoreline positions, historical rates of sea level change
        and future rates of sea level change following a calibrated Bruun Rule
        type approach.

        This function requires several functions with the Coast object to have been run
        first but the Coast wrapper should/could check for this.

        Updated to work with timeseries objects 13/7/26
        Default is to work with MHWS data
        Default rate method is time-weighted regression

        MDH, September 2019

        """
        
        # boolean flag if making prediction
        self.Future = False
        self.FutureShorelinesPositions = []
        self.FutureShorelinesRates = []
        self.FutureShorelinesDistances = []

        # cant make predictions without some historical shorelines
        if Timeseries not in self.Timeseries:
            print("No historic positions in timeseries object")
            self.Future = False
            return

        # get timeseries object to work with
        TS = self.Timeseries[Timeseries]

        # some logic here to check if its sensible to make predictions
        if not TS.HasData(Minimum=2):
            print("Not enough historic positions to base predictions")                
            self.Future = False
            return
        
        # check we have future sea levels MOVE THIS ONTO TIMESEREIES
        if not self.FutureSeaLevelYears or not self.FutureSeaLevels:
            return

        # calculate historical rates from timeseries if not already existing
        if RateMethod not in TS.Results:
            TS.Analyse()

        # retrieve results
        HistoricRate = -TS.Results[RateMethod]["Rate"]
        self.ChangeRate = HistoricRate
        LatestDate = TS.Dates[-1]
        LatestPosition = TS.Positions[-1]
        LatestDistance = float(TS.Distances[-1])
        
        # sense check
        if HistoricRate is None or not np.isfinite(HistoricRate):
            print("No rate or nan/inf")
            return
        
        # Get rate of sea level rise during historic record for bruun rule calibration

        # sea level rise over most recent 10 years
        EndDate = TS.Dates[-1]
        StartDate = EndDate - relativedelta(years=10)
        CalibrationDate = EndDate - relativedelta(years=5)

        # get historic RSLR and future RSLR to interpolate between
        HistoricalRSLRate = self.HistoricalRSLR / 1000.0
        FutureSeaLevelYears_diff = (self.FutureSeaLevelYears[1] - self.FutureSeaLevelYears[0]).days / 365.2425
        FutureRSLRate = (self.FutureSeaLevels[1] - self.FutureSeaLevels[0])/(FutureSeaLevelYears_diff)

        # get one associated rate of RSLR associated with CalibrationDate
        self.CalibrationRSLR = np.interp(CalibrationDate.toordinal(),
                                     [StartDate.toordinal(), self.FutureSeaLevelYears[1].toordinal()],
                                     [HistoricalRSLRate, FutureRSLRate])

        # get slope from intertidal zone if we dont already have it
        if not self.ShorefaceSlope:
            self.ShorefaceDistance = self.MLWS.get_Distance(TS.Positions[-1])
            self.ShorefaceDepth = self.ClosureDepth + self.MHWS
            self.ShorefaceSlope = self.ShorefaceDepth/self.ShorefaceDistance
        
        self.ShorefaceDepth = self.ClosureDepth + self.MHWS
        
        # get hinterland slope 
        self.CalculateHinterlandSlope()

        # set slope for Bruun Rule    
        if self.HinterlandSlope < self.ShorefaceSlope:
            self.BruunSlope = self.HinterlandSlope
        else:
            self.BruunSlope = self.ShorefaceSlope
        
        # set minimum shoreface slope to 0.001
        if self.BruunSlope < 0.001:
            self.BruunSlope = 0.001

        # Calibration term, remembering to convert relative sea level change rates to m/yr
        CalibrationRate = (self.ShorefaceDepth * HistoricRate + (self.ShorefaceDepth / self.BruunSlope) * self.CalibrationRSLR)
        
        # get sea level at latest time
        self.LatestRSL = np.interp(LatestDate.toordinal(),[Date.toordinal() for Date in self.FutureSeaLevelYears], self.FutureSeaLevels,)
        
        # Future shoreline positions
        for FutureDate, FutureSeaLevel in zip(self.FutureSeaLevelYears, self.FutureSeaLevels):

            dT = (FutureDate - LatestDate).days / 365.2425

            # catch the condition where observed shorelines are more recent than those we're trying to make predictions for
            if dT <= 0:

                #print('Predict Future Shorelines - observed shorelines are more recent than predictions:', str(self.FutureSeaLevelYears[i]), '-', TS.Dates[-1])
                self.FutureShorelinesPositions.append(Node(LatestPosition.X, LatestPosition.Y))
                self.FutureShorelinesRates.append(HistoricRate)
                self.FutureShorelinesDistances.append(LatestDistance)
                continue
            
            BruunRuleComponent = -(1./self.BruunSlope)*(FutureSeaLevel-self.LatestRSL)
            CalibrationComponent = (1./self.ShorefaceDepth)*CalibrationRate*dT
            ShorelinePositionChange = BruunRuleComponent+CalibrationComponent
            
            # check rock head position not exceeded
            FutureShorelineDistance = LatestDistance - ShorelinePositionChange
            
            if self.DefencesDistance and (FutureShorelineDistance > self.DefencesDistance):

                FutureShorelineDistance = self.DefencesDistance
                ShorelinePositionChange = LatestDistance - FutureShorelineDistance
                FuturePosition = self.DefencesPosition
                
            elif self.RockHeadDistance and (FutureShorelineDistance > self.RockHeadDistance):

                # if landward of
                FutureShorelineDistance = self.RockHeadDistance
                ShorelinePositionChange = LatestDistance - FutureShorelineDistance
                FuturePosition = self.RockHeadPosition
                
            # otherwise write new shoreline position as appropriate
            else:
                X1 = LatestPosition.X - ShorelinePositionChange * np.sin( np.radians( self.Orientation ) )
                Y1 = LatestPosition.Y - ShorelinePositionChange * np.cos( np.radians( self.Orientation ) )
                FuturePosition = Node(X1, Y1)
                
            self.FutureShorelinesPositions.append(FuturePosition)
            self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
            self.FutureShorelinesDistances.append(FutureShorelineDistance)
        
        self.Future = True

    def PredictFutureShorelineBathtub(self):

        """
        Function to predict the future shoreline position by drowning topography on the transect

        MDH, March 2021

        """

        # reset outputs incase already has been run
        self.FutureShorelinesPositions = []
        self.FutureShorelinesRates = []
        self.FutureShorelinesDistances = []
        self.InterpolatedRSLR = []


        # loop across sea level predictions
        for Year, SeaLevel in zip(self.FutureSeaLevelYears,self.FutureSeaLevels):
        
            # time
            dT = Year-TS.Dates[-1]

            # vector at fixed elevation running the length of the transect
            Start, End = ma.notmasked_edges(self.Distance)
            X1, Y1 = self.Distance[Start], Elev
            X2, Y2 = self.Distance[End], Elev
        
            dX12 = X2-X1
            dY12 = Y2-Y1
        
            # count and record locations of intersection
            IntersectionCounter = 0
            self.IntersectionIndices = []
            InterpolateFractions = []
        
            # temporary fix for no assignment, need a function for reading in transect topo
            # rather than having it set externally?
            self.NoValues = len(self.Distance)
            self.DistanceSpacing = self.Distance[End]-self.Distance[End-1]
        
            # loop across barrier topography
            for i in range(Start, self.NoValues-1):

                # cut and paste interesction analysis
                # do we want this to be a separate function somewhere?
                # Loop through transects and count no of intersections with the barrier
                # get transect line ends        
                X3,Y3 = self.Distance[i], self.Elevation[i]
                X4,Y4 = self.Distance[i+1], self.Elevation[i+1]
                
                dX34 = X4-X3
                dY34 = Y4-Y3
                
                #Find the cross product of the two vectors
                XProd = dX12*dY34 - dX34*dY12
                    
                if (XProd != 0):
                    if (XProd > 0):
                        XProdPos = 1
                    else:
                        XProdPos = 0
                        
                    #assign third test segment
                    dX31 = X1-X3
                    dY31 = Y1-Y3
                        
                    #get cross products
                    S = dX12*dY31 - dY12*dX31
                    T = dX34*dY31 - dY34*dX31
                    
                    #logic for collision occurence
                    if ((S < 0) == XProdPos):
                        continue
                    elif ((T < 0) == XProdPos):
                        continue
                    elif ((S > XProd) == XProdPos):
                        continue
                    elif ((T > XProd) == XProdPos):
                        continue
                    else:
                        IntersectionCounter += 1
                        self.IntersectionIndices.append(i)
                        Fraction = np.abs((Elev-Y3)/dY34)
                        InterpolateFractions.append(Fraction)
        
            # flag if no intersection 
            if IntersectionCounter == 0:
                import pdb
                pdb.set_trace()
                continue

            # else use first intersection as shoreline position
            # get future shoreline positions
            FutureShorelineDistance = Distance[self.IntersectionIndices[0]]+InterpolateFranctions[0]*(Distance[self.IntersectionIndices[0]+1]-Distance[self.IntersectionIndices[0]])
                
            if self.RockHeadDistance and (FutureShorelineDistance > self.RockHeadDistance):
                
                # if landward of
                self.FutureShorelinesPositions.append(self.RockHeadPosition)
                
                ShorelinePositionChange = HistoricShorelineDistance-self.RockHeadDistance
                self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
                self.FutureShorelinesDistances.append(self.RockHeadDistance)

            elif self.DefencesDistance and (FutureShorelineDistance > self.DefencesDistance):
                
                # if landward of
                self.FutureShorelinesPositions.append(self.DefencesPosition)
                
                ShorelinePositionChange = HistoricShorelineDistance - self.DefencesDistanced
                self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
                self.FutureShorelinesDistances.append(self.DefencesDistance)
            
            # otherwise write new shoreline position as appropriate
            else:
                
                # may be a sign issue in here will need to check
                ShorelinePositionChange = HistoricShorelineDistance-FutureShorelineDistance
                X1 = TS.Positions[-1].X + ShorelinePositionChange * np.sin( np.radians( self.Orientation ) )
                Y1 = TS.Positions[-1].Y + ShorelinePositionChange * np.cos( np.radians( self.Orientation ) )

                self.FutureShorelinesPositions.append(Node(X1,Y1))
                self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
                self.FutureShorelinesDistances.append(FutureShorelineDistance)

                

    def PredictFutureShorelineUncertainty(self, Year=2100):

        """
        Function to map uncertainty for shoreline position in a certain year based on range 
        of historical coastal change

        This needs updating for datetimes MDH Apr 2026

        MDH March 2020

        """
        
        # get future sea level and time difference
        Index = [i for i, x in enumerate(self.FutureSeaLevelYears) if x == Year]
        FutureSeaLevel = self.FutureSeaLevels[Index[0]]
        dT = Year-TS.Dates[-1]

        # reset min and max in case uncertainty has been previously assessed
        self.FutureShorelineMinDistance = 9999999.
        self.FutureShorelineMaxDistance = -9999999.

        # get sea level at latest time
        if TS.Dates[-1] < self.FutureSeaLevelYears[0]:
            self.LatestRSL = self.FutureSeaLevels[0]
        else:
            Interp = (self.FutureSeaLevelYears[1]-TS.Dates[-1])/(self.FutureSeaLevelYears[1]-self.FutureSeaLevelYears[0])
            self.LatestRSL = self.FutureSeaLevels[1]-Interp*(self.FutureSeaLevels[1]-self.FutureSeaLevels[0])

        for VolumetricCalibrationRate in self.VolumetricCalibrationRates:
            
            BruunRuleComponent = (-1./self.BruunSlope)*(FutureSeaLevel-self.LatestRSL)
            CalibrationComponent = (1./self.ShorefaceDepth)*VolumetricCalibrationRate*dT
            ShorelinePositionChange = BruunRuleComponent+CalibrationComponent

            # check rock head position not exceeded
            HistoricShorelineDistance = self.StartNode.get_Distance(self.HistoricShorelinesPosition[-1])
            FutureShorelineDistance = HistoricShorelineDistance - ShorelinePositionChange
            
            X1 = self.HistoricShorelinesPosition[-1].X - ShorelinePositionChange * np.sin( np.radians( self.Orientation ) )
            Y1 = self.HistoricShorelinesPosition[-1].Y - ShorelinePositionChange * np.cos( np.radians( self.Orientation ) )
            
            if FutureShorelineDistance < self.FutureShorelineMinDistance:
                self.FutureShorelineMinDistance = FutureShorelineDistance
                self.FutureShorelinesMinNode = Node(X1,Y1)

            if FutureShorelineDistance > self.FutureShorelineMaxDistance:
                self.FutureShorelineMaxDistance = FutureShorelineDistance
                self.FutureShorelinesMaxNode = Node(X1, Y1)
                
            # need some logic here to extend transects?
    
    def PredictFutureShorelineError(self, Year=2100):

        """
        Function to map error for shoreline position in a certain year based on
        propagation of error in historical shoreline positions

        MDH October 2020

        """

        # get future sea level and time difference
        FutureSeaLevel = self.FutureSeaLevels[self.FutureSeaLevelYears == Year]
        dT = Year-TS.Dates[-1]

        # reset min and max in case uncertainty has been previously assessed
        self.FutureShorelineMinDistance = 9999999.
        self.FutureShorelineMaxDistance = -9999999.

        # get sea level at latest time
        if self.HistoricShorelinesDates[-1] < self.FutureSeaLevelYears[0]:
            self.LatestRSL = self.FutureSeaLevels[0]
        else:
            Interp = (self.FutureSeaLevelYears[1]-self.HistoricShorelinesDates[-1])/(self.FutureSeaLevelYears[1]-self.FutureSeaLevelYears[0])
            self.LatestRSL = self.FutureSeaLevels[1]-Interp*(self.FutureSeaLevels[1]-self.FutureSeaLevels[0])

        # set index for calibration
        if self.LongTermOnly:
            Index = 0
        else:
            Index = -1

        CalibrationRatesErrors = [  self.VolumetricCalibrationRates[Index] - self.VolumetricCalibrationErrors[Index],
                                    self.VolumetricCalibrationRates[Index],
                                    self.VolumetricCalibrationRates[Index] + self.VolumetricCalibrationErrors[Index] ]

        for VolumetricCalibrationRate in CalibrationRatesErrors:
            
            BruunRuleComponent = (-1./self.BruunSlope)*(FutureSeaLevel-self.LatestRSL)

            CalibrationComponent = (1./self.ShorefaceDepth)*VolumetricCalibrationRate*dT
            ShorelinePositionChange = BruunRuleComponent+CalibrationComponent
            
            # check rock head position not exceeded
            HistoricShorelineDistance = self.StartNode.get_Distance(self.HistoricShorelinesPosition[-1])
            FutureShorelineDistance = HistoricShorelineDistance - ShorelinePositionChange
            
            X1 = self.HistoricShorelinesPosition[-1].X - ShorelinePositionChange * np.sin( np.radians( self.Orientation ) )
            Y1 = self.HistoricShorelinesPosition[-1].Y - ShorelinePositionChange * np.cos( np.radians( self.Orientation ) )

            if FutureShorelineDistance < self.FutureShorelineMinDistance:
                self.FutureShorelineMinDistance = FutureShorelineDistance
                self.FutureShorelinesMinNode = Node(X1,Y1)

            if FutureShorelineDistance > self.FutureShorelineMaxDistance:
                self.FutureShorelineMaxDistance = FutureShorelineDistance
                self.FutureShorelinesMaxNode = Node(X1, Y1)

    def PredictFutureVegEdge(self):

        """

        Function to predict future vegetation edge positions
        requires veg edge has been already added to transect attributes
        requires PredictFutureShorelinePositions has already been run

        MDH, Feb 2020
        
        """
        # calculate distance along transect to veg edge
        self.VegEdgeDistance = self.StartNode.get_Distance(self.VegEdgePosition)

        # measure difference between latest MHWS and veg edge
        Offset = TS.Distances[-1][0] - self.VegEdgeDistance

        # use difference to map future vegetation edges based on future MHWS
        self.FutureVegEdgePositions = []
        for i in range(1, len(self.FutureSeaLevelYears)):

            X1 = self.FutureShorelinesPositions[-1].X - Offset * np.sin( np.radians( self.Orientation ) )
            Y1 = self.FutureShorelinesPositions[-1].Y - Offset * np.cos( np.radians( self.Orientation ) )

            self.FutureVegEdgePositions.append(Node(X1,Y1))
            

        
            
    def FindCliff(self):

        """

        Function to identify whether the coastal transect has a cliff
        and find the position of a cliff on a coastal transect
        records the position of the cliff top and cliff toe

        MDH, June 2019

        """
        
        # Find the last point on the Transect
        LastInd = np.transpose(self.Elevation.nonzero())[-1][0]
        self.CliffTopInd = LastInd
            
        # Find first real elevation location in masked array
        FirstInd = np.transpose(self.Elevation.nonzero())[0][0]

        # Find the minumum and maximum elevation in the masked array
        MaxInd = np.argmax(self.Elevation)
        MinInd = np.argmin(self.Elevation)
        self.CliffToeInd = MinInd
        
        # mask distances and elevations seaward of minimum and landward of last real value
        Mask = self.Elevation.mask.copy()
        Mask[0:MinInd] = True
        if LastInd < len(self.Elevation):
            Mask[LastInd+1:] = True
        self.Elevation = ma.masked_where(Mask, self.Elevation)
        self.Distance = ma.masked_where(Mask, self.Distance)

        # cliffed coast will have elevations > 10 m
        # this threshold could be flexible in future
        if np.max(self.Elevation) < 10.:
            self.Cliff = False
            return

        # flag for changing position
        CliffPositionChangeFlag = True

        while CliffPositionChangeFlag:

            # reset flag
            CliffPositionChangeFlag = False

            # FIRST CLIFF TOP

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if self.Distance[self.CliffToeInd] == self.Distance[LastInd]:
                print(self.ID)
                print("Divide by zero!")
                sys.exit()

            Angle = np.degrees(np.arctan((self.Elevation[LastInd]-self.Elevation[self.CliffToeInd]) 
                                        / (self.Distance[LastInd]-self.Distance[self.CliffToeInd])))
            
            # Get detrended elevation
            ElevDetrend = ((self.Elevation-self.Elevation[self.CliffToeInd])+(self.Distance[self.CliffToeInd]-self.Distance) \
                            * np.tan(np.radians(Angle)))

            # mask values beyond the peak elevation and seaward of the toe
            Mask = self.Elevation.mask.copy()
            Mask[0:self.CliffToeInd] = True
            Mask[LastInd:] = True
            ElevDetrend = ma.masked_where(Mask,ElevDetrend)
            
            # Find Maximum detrended elevation. Must be positive to be considered a change in cliff top position
            if ((np.argmax(ElevDetrend) < self.CliffTopInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                self.CliffTopInd = np.argmax(ElevDetrend)
                CliffPositionChangeFlag = True
             
            # THEN CLIFF TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if self.Distance[self.CliffTopInd] == self.Distance[MinInd]:
                print(self.ID)
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((self.Elevation[self.CliffTopInd]-self.Elevation[MinInd]) 
                                        / (self.Distance[self.CliffTopInd]-self.Distance[MinInd])))
            
            # Get detrended elevation
            ElevDetrend = ((self.Elevation-self.Elevation[MinInd]) + (self.Distance[MinInd] - self.Distance) \
                            * np.tan(np.radians(Angle)))

            # mask values beyond the cliff top
            Mask = self.Elevation.mask.copy()
            Mask[self.CliffTopInd:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
                            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if ((np.argmin(ElevDetrend) > self.CliffToeInd) and (ElevDetrend[np.argmin(ElevDetrend)] < -0.001)):
                #print("Cliff Toe change from", self.Distance[self.CliffToeInd],"to", self.Distance[np.argmin(ElevDetrend)])
                self.CliffToeInd = np.argmin(ElevDetrend)
                CliffPositionChangeFlag = True

        # Check if found a cliff
        self.CliffHeight = self.Elevation[self.CliffTopInd]-self.Elevation[self.CliffToeInd]
        self.CliffSlope = self.CliffHeight/(self.Distance[self.CliffTopInd]-self.Distance[self.CliffToeInd])
        
        #plt.plot(self.Distance[self.CliffTopInd],self.Elevation[self.CliffTopInd],'go')
        #plt.plot(self.Distance[self.CliffToeInd],self.Elevation[self.CliffToeInd],'go')

        # if cliff top is highest point, not a cliff, likely a barrier
        if self.CliffTopInd == MaxInd:
            self.Cliff = False

        elif np.abs(self.Distance[self.CliffTopInd]-self.Distance[MaxInd]) < 10.:
            self.Cliff = False

        elif (self.CliffSlope > 0.6) or (self.CliffHeight > 15.):
            self.Cliff = True
            #print(" ", self.LineID, self.ID, "Cliff:", self.Distance[self.CliffToeInd], self.Distance[self.CliffTopInd])
                    
        else:
            self.Cliff = False
            
    def FindCliff2(self):

        """

        Function to identify whether the coastal transect has a cliff
        and find the position of a cliff on a coastal transect
        records the position of the cliff top and cliff toe

        MDH, June 2019 (original)
        NH modified, Mar 2024: Search landward of 0 m; Seaward of 200 m 

        """
        
        # Find the last point on the Transect
        # LastInd = np.transpose(self.Elevation.nonzero())[-1][0]
        dist_inland = 200                   # distance landward of coastline within which to search for cliff
        
        LastInd = np.argmin(abs(self.Distance - (round(self.Length/2) + dist_inland)))
        #print(" ", self.LineID, self.ID, "LastInd=", LastInd)
        self.CliffTopInd = LastInd
            
        # NH: Find first real elevation location in masked array (without creating new mask) KEEP THIS
        idx = np.where(self.Elevation > 0)
        idx = idx[0]                        # np.where returns tuple of array + datatype; Choose array.
        FirstInd = idx[0]
        #print(" ", self.LineID, self.ID, "idx=", idx, "FirstInd=", FirstInd)
        
        # mask distances and elevations seaward of minimum and landward of last real value
        #Mask = self.Elevation.mask.copy()              # old bug of returning single boolean, and not array if completely unmasked
        Mask = ma.getmaskarray(self.Elevation)          # return array of False if no mask
        Mask[0:FirstInd] = True
        if LastInd < len(self.Elevation):
            Mask[LastInd+1:] = True
        self.Elevation = ma.masked_where(Mask, self.Elevation)
        self.Distance = ma.masked_where(Mask, self.Distance)
        
        # Find the minumum and maximum elevation in the masked array
        MaxInd = np.argmax(self.Elevation)
        MinInd = np.argmin(self.Elevation)
        self.CliffToeInd = MinInd

        # cliffed coast will have elevations > 10 m
        # this threshold could be flexible in future
        if np.max(self.Elevation) < 10.:
            self.Cliff = False
            print("Not a cliff 1")
            return

        # flag for changing position
        CliffPositionChangeFlag = True

        while CliffPositionChangeFlag:

            # reset flag
            CliffPositionChangeFlag = False

            # FIRST CLIFF TOP

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if self.Distance[self.CliffToeInd] == self.Distance[LastInd]:
                print(self.ID)
                print("Divide by zero getting cliff top!")
                self.Cliff = False                              # NH change: dont exit analysis, just set to false and continue. Case where hinterland is lowlying
                return
                #sys.exit()

            Angle = np.degrees(np.arctan((self.Elevation[LastInd]-self.Elevation[self.CliffToeInd]) 
                                        / (self.Distance[LastInd]-self.Distance[self.CliffToeInd])))
            
            # Get detrended elevation
            ElevDetrend = ((self.Elevation-self.Elevation[self.CliffToeInd])+(self.Distance[self.CliffToeInd]-self.Distance) \
                            * np.tan(np.radians(Angle)))

            # mask values beyond the peak elevation and seaward of the toe
            Mask = self.Elevation.mask.copy()
            Mask[0:self.CliffToeInd] = True
            Mask[LastInd:] = True
            ElevDetrend = ma.masked_where(Mask,ElevDetrend)
            
            # Find Maximum detrended elevation. Must be positive to be considered a change in cliff top position
            if ((np.argmax(ElevDetrend) < self.CliffTopInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                self.CliffTopInd = np.argmax(ElevDetrend)
                CliffPositionChangeFlag = True
             
            # THEN CLIFF TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if self.Distance[self.CliffTopInd] == self.Distance[MinInd]:
                print(self.ID)
                print("Divide by zero getting cliff toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((self.Elevation[self.CliffTopInd]-self.Elevation[MinInd]) 
                                        / (self.Distance[self.CliffTopInd]-self.Distance[MinInd])))
            
            # Get detrended elevation
            ElevDetrend = ((self.Elevation-self.Elevation[MinInd]) + (self.Distance[MinInd] - self.Distance) \
                            * np.tan(np.radians(Angle)))

            # mask values beyond the cliff top
            Mask = self.Elevation.mask.copy()
            Mask[self.CliffTopInd:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
                            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if ((np.argmin(ElevDetrend) > self.CliffToeInd) and (ElevDetrend[np.argmin(ElevDetrend)] < -0.001)):
                #print("Cliff Toe change from", self.Distance[self.CliffToeInd],"to", self.Distance[np.argmin(ElevDetrend)])
                self.CliffToeInd = np.argmin(ElevDetrend)
                CliffPositionChangeFlag = True

        # Check if found a cliff
        self.CliffHeight = self.Elevation[self.CliffTopInd]-self.Elevation[self.CliffToeInd]
        self.CliffSlope = self.CliffHeight/(self.Distance[self.CliffTopInd]-self.Distance[self.CliffToeInd]) 
        
        # if cliff top is highest point, not a cliff, likely a barrier
        if self.CliffTopInd == MaxInd:
            self.Cliff = False
            print(" ", self.LineID, self.ID, "Not a cliff 2:", self.Distance[self.CliffTopInd])

        elif np.abs(self.Distance[self.CliffTopInd]-self.Distance[MaxInd]) < 10.:
            self.Cliff = False
            print(" ", self.LineID, self.ID, "Not a cliff 3:", self.Distance[self.CliffTopInd])
        
        elif (self.CliffSlope > 0.6) or (self.CliffHeight > 15.):
            self.Cliff = True
            print(" ", self.LineID, self.ID, "CLIFF:", self.Distance[self.CliffToeInd], self.Distance[self.CliffTopInd])
                    
        else:
            self.Cliff = False
            print(" ", self.LineID, self.ID, "Not a cliff 4")

    def AnalyseRoughness(self, Elev):

        """
        Isolates intertidal elevations and looks at their roughness to determine
        if rocky (rough) or sandy (smooth)

        MDH, July 2019

        """

        # mask by elevation
        if not ma.is_masked(self.Elevation):
            Mask = np.where(self.Elevation > Elev, True, False)
        else:
            Mask = self.Elevation.mask.copy()
            Mask[self.Elevation > Elev] = True
       
        try:
            Mask[self.Elevation < -1] = True
        except:
            import pdb
            pdb.set_trace()
        # apply mask
        ElevMasked = ma.masked_where(Mask, self.Elevation)
        
        # calculate slope along the transect
        Start, End = ma.notmasked_edges(self.Distance)
        self.DistanceSpacing = self.Distance[Start+1]-self.Distance[Start] # temporary fix
        Slope = np.diff(ElevMasked)/self.DistanceSpacing
        Slope = Slope.compressed()

        # calculate roughness and take mean value
        #self.SlopeRoughness = np.max(Slope)-np.min(Slope)
        #print(np.percentile(Slope, 95),np.percentile(Slope, 5),np.std(Slope))
        self.SlopeRoughness = np.percentile(Slope, 95) - np.percentile(Slope, 5)
        self.ElevationRoughness = np.std(self.Elevation)

        if self.SlopeRoughness > 10.:
            print("ARGH!!!")

        
        #print(self.SlopeRoughness, self.ElevationRoughness)
        if (self.SlopeRoughness > 0.05) and (self.ElevationRoughness > 0.2):
            self.Rocky = True

    def FindBarrier(self):
        
        """
        Description goes here
        MDH, June 2019
        """
        
        # Check if rocky and dont look for barrier on rocky coast
        if self.Rocky:
            print("\n\tNot a barrier 1")
            self.Barrier = False
            return

        # Check if a cliff is present and only analyse topography up to the cliff toe
        # when looking for a barrier
        #Mask = self.Elevation.mask.copy()              # Problem: this returns boolean value (not array) of False when no masked elements
        Mask = ma.getmaskarray(self.Elevation)          # Return the mask of a masked array, or full boolean array of False.
        if self.Cliff:
            Mask[self.CliffToeInd+1:] = True
        
        # mask below sea level, including tide, in future
        Mask[self.Elevation < 0] = True

        # apply mask
        ElevMasked = ma.masked_where(Mask, self.Elevation)
        DistanceMasked = ma.masked_where(Mask, self.Distance)

        # check that the whole topography has not been masked
        # this would indicate there is no barrier
        if ElevMasked.mask.all():
            print("\n\tNot a barrier 2")
            self.Barrier = False
            return

        # Find the highest point to start from
        MaxInd = np.argmax(ElevMasked)
        self.FrontTopInd = MaxInd

        # if highest point is not above MHWS then cant be a barrier
        if not self.MHWS:
            print("No MHWS data for " + self.LineID + ", " + self.ID)
            sys.exit()
        elif not ElevMasked[MaxInd]:
            print("No value for ElevMasked[MaxInd]" + self.LineID + ", " + self.ID)
            sys.exit()
        if ElevMasked[MaxInd] < self.MHWS:
            print("\n\tNot a barrier 3")
            self.Barrier = False
            return

        # Find first real elevation location in masked array
        FirstInd = np.transpose(ElevMasked.nonzero())[0][0]
        self.FrontToeInd = FirstInd
        
        # Find last real elevation location in masked array
        LastInd = np.transpose(ElevMasked.nonzero())[-1][0]

        # check highest point is not on seaward end
        if MaxInd == FirstInd:
            print("\n\tNot a barrier 4")
            self.Barrier = False
            return

        # flag for changing position
        # we'll keep applygin the barrier finder until the 
        # top and toe positions dont change
        BarrierPositionChangeFlag = True

        Counter = 0
        MHWSFlag = False

        while BarrierPositionChangeFlag:

            Counter += 1                            # NH DEBUG
            
            # reset flag
            BarrierPositionChangeFlag = False

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[MaxInd] == DistanceMasked[self.FrontToeInd]:
                print("")
                print(self.ID)
                print("Divide by zero getting top!")
                print(DistanceMasked)
                print(MaxInd, self.FrontToeInd)
                sys.exit()

            # Get Angle to detrend towards the coast
            Angle = np.degrees(np.arctan((ElevMasked[self.FrontTopInd]-ElevMasked[FirstInd]) 
                                        / (DistanceMasked[self.FrontTopInd]-DistanceMasked[FirstInd])))
        
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[FirstInd])+(DistanceMasked[FirstInd]-DistanceMasked) \
                                * np.tan(np.radians(Angle)))

            # mask values beyond the peak
            Mask = ElevMasked.mask.copy()
            Mask[0:FirstInd] = True
            if self.FrontTopInd < LastInd:          ## NH ADD: Catch when highest elevation is the last node (self.FrontTopInd=MaxInd=LastInd). Prevents corrupt indexing.
                Mask[self.FrontTopInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            NewInd = np.argmax(ElevDetrend)
            
            #print(Counter)                         # NH DEBUG
            #print(f"a)FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}") 
            #print(f"FrontTopInd={self.FrontTopInd}, FrontToeInd={self.FrontToeInd}, BackTopInd={self.BackTopInd}")
            
            if (NewInd == FirstInd):
                #print(f"{Counter}, Setting NewInd = MaxInd")
                NewInd = MaxInd
            
            # Find Maximum detrended elevation. Original: If at end of transect then not a barrier
            # NH edit: rather than discard transect, keep as potential barrier and set flag that hinterland is higher than barrier crest.
            if (NewInd == LastInd):
                print("\n\tNot a barrier 5")
                
                #print(self.LineID, self.ID)         # NH DEBUG
                #print(f"FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}")
                #print(f"FrontTopInd={self.FrontTopInd}, FrontToeInd={self.FrontToeInd}")
                #plt.plot(self.Distance,ElevMasked,'k-')
                #plt.plot(self.Distance[self.FrontTopInd],self.Elevation[self.FrontTopInd],'bo')
                #plt.plot(self.Distance[self.FrontToeInd],self.Elevation[self.FrontToeInd],'bs')
                #plt.plot(self.Distance[self.BackTopInd],self.Elevation[self.BackTopInd],'ro')
                #plt.plot(self.Distance[self.BackToeInd],self.Elevation[self.BackToeInd],'rs')
                #plt.plot(self.Distance,ElevDetrend,'r-')
                #plt.show()
                #sys.exit()
                
                #self.Barrier = False
                #return
                self.HinterlandHigher = True

            # Must be above MHWS to be considered a barrier top
            # NH edit: Replace elif with if to align with not treating previous if statement as error.
            if ((NewInd < self.FrontTopInd) and (ElevDetrend[NewInd] > 0.001) and (ElevMasked[NewInd] > self.MHWS)):
                self.FrontTopInd = np.argmax(ElevDetrend)
                BarrierPositionChangeFlag = True

            # THEN Barrier TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[FirstInd]:
                print(self.ID)
                print(DistanceMasked[self.FrontTopInd], DistanceMasked[FirstInd])
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((ElevMasked[self.FrontTopInd]-ElevMasked[FirstInd]) 
                                        / (DistanceMasked[self.FrontTopInd]-DistanceMasked[FirstInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[FirstInd]) \
             + (DistanceMasked[FirstInd] - DistanceMasked) * np.tan(np.radians(Angle)))

            # mask values beyond the barrier front top
            Mask = ElevMasked.mask.copy()
            #Mask[:self.FrontToeInd] = True
            if self.FrontTopInd < LastInd:            ## NH ADD: Catch when highest elevation is the last node (self.FrontTopInd=MaxInd=LastInd). Prevents corrupt indexing.
                Mask[self.FrontTopInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            NewInd = np.argmin(ElevDetrend)
            
            #print(Counter)                         # NH DEBUG
            #print(ElevDetrend)
            #print(f"b)FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}") 
            
            # Find Minimum detrended elevation, must be negative to be considered a low 
            if ((NewInd > self.FrontToeInd) and (ElevDetrend[NewInd] < -0.001)):
                self.FrontToeInd = NewInd
                BarrierPositionChangeFlag = True
                #print("*")                         # NH DEBUG
            
            # Must also be above MHWS 
            # # only check this once   
            if (ElevMasked[self.FrontToeInd] < self.MHWS) and (MHWSFlag == False):
                
                MHWSFlag = True
                #print("%")                         # NH DEBUG

                # find MHWS as minimum point and check index is one node seaward of MHWS mark
                Mask[:self.FrontToeInd] = True
                NewInd = np.argmin(np.abs(ma.masked_where(Mask, ElevMasked)-self.MHWS))
                if ElevMasked[NewInd] > self.MHWS:
                    NewInd -= 1

                self.FrontToeInd = NewInd
                BarrierPositionChangeFlag = True
            
            # NH DEBUG
            #print(f"c)FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}") 
            #print(f"FrontTopInd={self.FrontTopInd}, FrontToeInd={self.FrontToeInd}, BackTopInd={self.BackTopInd}")  
            
        # check toe is not inland of barrier due to MHWS     
        if not self.FrontTopInd > self.FrontToeInd:
            print("\n\tNot a barrier 6")
            self.Barrier = False
            return

        # Check if coincides with a cliff
        if self.FrontTopInd == LastInd:
            print("\n\tNot a barrier 7")
            self.Barrier = False
            return

        # this needs more work
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        
        # default back barrier positions
        self.BackTopInd = self.FrontTopInd
        Mask = ElevMasked.mask.copy()
        Mask[0:self.FrontTopInd] = True
        ElevMasked = ma.masked_where(Mask,ElevMasked)

        # MIN IND OR LAST IND HERE?
        MinInd = np.argmin(np.abs(self.Distance-(self.Distance[self.FrontTopInd]+300)))
        if MinInd > LastInd:
            MinInd = LastInd
        self.BackToeInd = MinInd
        #plt.plot(DistanceMasked[MinInd],ElevMasked[MinInd],'k+',ms=20)

        # catch where Minimum Elevation coincides with "barrier" front
        if MinInd == self.FrontTopInd:
            self.BackToeInd = LastInd
        
        # flag for changing position
        BarrierPositionChangeFlag = True
        
        while BarrierPositionChangeFlag:
            
            # FIRST Back Barrier TOE
            
            # reset flag
            BarrierPositionChangeFlag = False
            
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[MinInd]:
                print(self.LineID, self.ID)
                print(DistanceMasked[self.FrontTopInd], DistanceMasked[MinInd], self.FrontTopInd, MinInd, LastInd)
                print("Divide by zero getting back toe!")
                sys.exit()

            # Get Angle to detrend towards the coast
            Angle = np.degrees(np.arctan((ElevMasked[MinInd]-ElevMasked[self.FrontTopInd]) 
                                        / (DistanceMasked[MinInd]-DistanceMasked[self.FrontTopInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontTopInd]) + (DistanceMasked[self.FrontTopInd] - DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values seaward of the barrier front top
            Mask = ElevMasked.mask.copy()
            Mask[0:self.BackTopInd] = True
            Mask[MinInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            NewInd = np.argmin(ElevDetrend)
            #plt.plot(DistanceMasked,ElevDetrend,'r-')
            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if not NewInd == self.BackToeInd:
                if ((NewInd < self.BackToeInd) and (ElevDetrend[NewInd] < -0.001) and (NewInd > self.BackTopInd)):
                    self.BackToeInd = NewInd
                    BarrierPositionChangeFlag = True

            # THEN Back Top
            
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[self.BackToeInd]:
                print(self.LineID, self.ID)
                print(DistanceMasked[self.FrontTopInd], DistanceMasked[self.BackToeInd], self.FrontTopInd, self.BackToeInd, LastInd)
                print("Divide by zero getting back top!")
                sys.exit()
            
            # Get Angle to detrend towards away from the coast
            Angle = np.degrees(np.arctan((ElevMasked[self.BackToeInd]-ElevMasked[self.FrontTopInd])
                                        / (DistanceMasked[self.BackToeInd]-DistanceMasked[self.FrontTopInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontTopInd])+(DistanceMasked[self.FrontTopInd]-DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values up to the peak
            Mask = ElevMasked.mask.copy()
            Mask[0:self.FrontTopInd] = True
            Mask[self.BackToeInd+1:] = True
            ElevDetrend = ma.masked_where(Mask,ElevDetrend)
            NewInd = np.argmax(ElevDetrend)
            
            # Find Maximum detrended elevation. Must be positive to be considered a change in barrier back top position
            if not self.BackTopInd == NewInd:
                if ((NewInd < self.BackToeInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                    self.BackTopInd = np.argmax(ElevDetrend)
                    BarrierPositionChangeFlag = True
                    
        if self.BackTopInd == LastInd:
            print("\n\tNot a barrier 8")
            self.Barrier = False
            return        
            
        # Get Barrier Crest
        #Mask = self.Elevation.mask.copy()              # Problem: this returns boolean value (not array) of False when no masked elements
        Mask = ma.getmaskarray(self.Elevation)          # Return the mask of a masked array, or full boolean array of False.
        Mask[0:self.FrontToeInd] = True
        Mask[self.BackToeInd+1:] = True                 # NH bug fix: exclude all elevations beyond BackToeInd, not just the single elev at BackToeInd
        ElevMasked = ma.masked_where(Mask,self.Elevation)
        self.CrestInd = ma.argmax(ElevMasked)
        self.CrestElevation = ElevMasked[self.CrestInd]
            
        # Calculate Barrier Height, front and back
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.BackHeight = self.Elevation[self.BackTopInd]-self.Elevation[self.BackToeInd]
        
        # Calculate Barrier Width, top and bottom
        self.ToeWidth = np.abs(self.Distance[self.FrontToeInd]-self.Distance[self.BackToeInd])
        self.TopWidth = np.abs(self.Distance[self.FrontTopInd]-self.Distance[self.BackTopInd])
        
        # Calculate Slope, front and back
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        self.BackSlope = self.BackHeight/(self.Distance[self.BackTopInd]-self.Distance[self.BackToeInd])
        
        # Volume m3/m
        Start, End = ma.notmasked_edges(self.Distance)
        self.DistanceSpacing = self.Distance[Start+1]-self.Distance[Start] # temporary fix
        
        self.BarrierVolume = ma.sum(ElevMasked)*self.DistanceSpacing
        
        self.BarrierVolume -= 0.5 * (ElevMasked[self.FrontToeInd] + ElevMasked[self.BackToeInd-1]) \
                                 * np.abs(self.Distance[self.BackToeInd-1] - self.Distance[self.FrontToeInd])
        
        # switch flag to indicate a barrier has been found
        self.Barrier = True
    
    def FindBarrier2(self, FrontToeMin=None): #(self, SeawardMask=None, LandwardMask=None, FrontToeMin=None):
        
        """
        Description goes here
        MDH, June 2019
        
        Toe detection revised
        NH Dec 2023
        
        SeawardMask: Distance from the start of the transect up to which to mask (not look for barrier)
        LandwardMask: Distance from the start of the transect beyond which NOT to search for coastal barrier
        FrontToeMin: Minimum negative detrended elevation for new front toe
        
        """
        
        # Check if rocky and dont look for barrier on rocky coast
        if self.Rocky:
            print("\n\tNot a barrier 1")
            self.Barrier = False
            return

        # Check if a cliff is present and only analyse topography up to the cliff toe
        # when looking for a barrier
        #Mask = self.Elevation.mask.copy()              # Problem: this returns boolean value (not array) of False when no masked elements
        Mask = ma.getmaskarray(self.Elevation)          # Return the mask of a masked array, or full boolean array of False.
        if self.Cliff:
            Mask[self.CliffToeInd+1:] = True
        
        # mask below sea level, including tide, in future
        Mask[self.Elevation < 0] = True
        
        # Bodge: set first (most seaward) element's mask to avoid compile error when no mask is set
        Mask[0] = True
        
        # Mask seaward and landward, if set. To accommodate long transects and low coastal barriers that are hard to detect
        if (self.SeawardMask > 0):
            Mask[self.Distance < self.SeawardMask] = True
        if (self.LandwardMask > 0):
            Mask[self.Distance > self.LandwardMask] = True
            
        # Minimum negative detrended elevation for new FrontToe. Default is -0.001 m. 
        # Larger values (-0.2) work better for dunes with clear inflections. Smaller values (-0.001) better for flat berms.
        if (FrontToeMin < 0):
            Tmin = FrontToeMin
        else:
            Tmin = -0.001

        # apply mask
        ElevMasked = ma.masked_where(Mask, self.Elevation)
        DistanceMasked = ma.masked_where(Mask, self.Distance)

        # check that the whole topography has not been masked
        # this would indicate there is no barrier
        if ElevMasked.mask.all():
            print("\n\tNot a barrier 2")
            self.Barrier = False
            return

        # Find the highest point to start from
        MaxInd = np.argmax(ElevMasked)
        self.FrontTopInd = MaxInd

        # if highest point is not above MHWS then cant be a barrier
        if not self.MHWS:
            print("No MHWS data for " + self.LineID + ", " + self.ID)
            sys.exit()
        elif not ElevMasked[MaxInd]:
            print("No value for ElevMasked[MaxInd]" + self.LineID + ", " + self.ID)
            sys.exit()
        if ElevMasked[MaxInd] < self.MHWS:
            print("\n\tNot a barrier 3")
            self.Barrier = False
            return

        # Find first real elevation location in masked array
        FirstInd = np.transpose(ElevMasked.nonzero())[0][0]
        self.FrontToeInd = MaxInd ##FirstInd
        
        # Find last real elevation location in masked array
        LastInd = np.transpose(ElevMasked.nonzero())[-1][0]

        # check highest point is not on seaward end
        if MaxInd == FirstInd:
            print("\n\tNot a barrier 4")
            self.Barrier = False
            return

        # flag for changing position
        # we'll keep applygin the barrier finder until the 
        # top and toe positions dont change
        BarrierPositionChangeFlag = True

        Counter = 0
        MHWSFlag = False

        while BarrierPositionChangeFlag:

            Counter += 1                            # NH DEBUG
            
            # reset flag
            BarrierPositionChangeFlag = False

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[FirstInd]:
                print("")
                print(self.ID)
                print("Divide by zero getting top!")
                print(DistanceMasked)
                print(self.FrontTopInd, FirstInd)
                sys.exit()

            # Get Angle to detrend towards the coast
            Angle = np.degrees(np.arctan((ElevMasked[self.FrontTopInd]-ElevMasked[FirstInd]) 
                                        / (DistanceMasked[self.FrontTopInd]-DistanceMasked[FirstInd])))
        
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[FirstInd])+(DistanceMasked[FirstInd]-DistanceMasked) \
                                * np.tan(np.radians(Angle)))

            # mask values beyond the peak
            Mask = ElevMasked.mask.copy()              # Problem: this returns boolean value (not array) of False when no masked elements
            Mask[0:FirstInd] = True
            if self.FrontTopInd < LastInd:          ## NH ADD: Catch when highest elevation is the last node (self.FrontTopInd=MaxInd=LastInd). Prevents corrupt indexing.
                Mask[self.FrontTopInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            NewInd = np.argmax(ElevDetrend)
            
            #print(Counter)                         # NH DEBUG
            #print(f"a)FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}") 
            #print(f"FrontTopInd={self.FrontTopInd}, FrontToeInd={self.FrontToeInd}, BackTopInd={self.BackTopInd}")
            
            if (NewInd == FirstInd):
                #print(f"{Counter}, Setting NewInd = MaxInd")
                NewInd = MaxInd
            
            # Find Maximum detrended elevation. Original: If at end of transect then not a barrier
            # NH edit: rather than discard transect, keep as potential barrier and set flag that hinterland is higher than barrier crest.
            if (NewInd == LastInd):
                print("LastInt highest") #("\n\tNot a barrier 5")
                
                #print(self.LineID, self.ID)         # NH DEBUG
                #print(f"FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}")
                #print(f"FrontTopInd={self.FrontTopInd}, FrontToeInd={self.FrontToeInd}")
                #plt.plot(self.Distance,ElevMasked,'k-')
                #plt.plot(self.Distance[self.FrontTopInd],self.Elevation[self.FrontTopInd],'bo')
                #plt.plot(self.Distance[self.FrontToeInd],self.Elevation[self.FrontToeInd],'bs')
                #plt.plot(self.Distance[self.BackTopInd],self.Elevation[self.BackTopInd],'ro')
                #plt.plot(self.Distance[self.BackToeInd],self.Elevation[self.BackToeInd],'rs')
                #plt.plot(self.Distance,ElevDetrend,'r-')
                #plt.show()
                #sys.exit()
                
                #self.Barrier = False
                #return
                self.HinterlandHigher = True

            # Must be above MHWS to be considered a barrier top
            # NH edit: Replace elif with if to align with not treating previous if statement as error.
            if ((NewInd < self.FrontTopInd) and (ElevDetrend[NewInd] > 0.001) and (ElevMasked[NewInd] > self.MHWS)):
                self.FrontTopInd = np.argmax(ElevDetrend)
                BarrierPositionChangeFlag = True

            # THEN Barrier TOE

            # Get Angle to detrend towards the coast
            # catch divide by zero
            if DistanceMasked[self.FrontToeInd] == DistanceMasked[FirstInd]:
                print(self.ID)
                print(DistanceMasked[self.FrontToeInd], DistanceMasked[FirstInd])
                print("Divide by zero getting toe!")
                sys.exit()

            Angle = np.degrees(np.arctan((ElevMasked[self.FrontToeInd]-ElevMasked[FirstInd]) 
                                        / (DistanceMasked[self.FrontToeInd]-DistanceMasked[FirstInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[FirstInd]) \
             + (DistanceMasked[FirstInd] - DistanceMasked) * np.tan(np.radians(Angle)))

            # mask values beyond the barrier front top
            Mask = ElevMasked.mask.copy()              
            #Mask[:self.FrontToeInd] = True
            if self.FrontToeInd < LastInd:            ## NH ADD: Catch when highest elevation is the last node (self.FrontTopInd=MaxInd=LastInd). Prevents corrupt indexing.
                Mask[self.FrontToeInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            NewInd = np.argmin(ElevDetrend)
            
            #print(Counter)                         # NH DEBUG
            #print(ElevDetrend)
            #print(f"b)FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}") 
            
            # Find Minimum detrended elevation, must be negative to be considered a low 
            if ((NewInd < self.FrontToeInd) and (ElevDetrend[NewInd] < Tmin) and (MHWSFlag == False)):       # don't keep searching below current toe elevation if previous toe was < MHWS elevation
                self.FrontToeInd = NewInd
                BarrierPositionChangeFlag = True
                #print("*")                         # NH DEBUG
            
            # Must also be seaward of FrontTopInd (NH). If toe landward of top, set toe index to front top index.
            if self.FrontToeInd > self.FrontTopInd:
                self.FrontToeInd = self.FrontTopInd
                BarrierPositionChangeFlag = True
            
            # Must also be above MHWS 
            # # only check this once   
            if (ElevMasked[self.FrontToeInd] < self.MHWS) and (MHWSFlag == False):
                
                MHWSFlag = True
                #print("%")                         # NH DEBUG

                # find MHWS as minimum point and check index is one node seaward of MHWS mark
                Mask[:self.FrontToeInd] = True
                NewInd = np.argmin(np.abs(ma.masked_where(Mask, ElevMasked)-self.MHWS))
                if ElevMasked[NewInd] > self.MHWS:
                    NewInd -= 1

                self.FrontToeInd = NewInd
                BarrierPositionChangeFlag = True
            
            # NH DEBUG
            #print(f"c)FirstInd={FirstInd}, LastInd={LastInd}, MaxInd={MaxInd}, NewInd={NewInd}") 
            #print(f"FrontTopInd={self.FrontTopInd}, FrontToeInd={self.FrontToeInd}, BackTopInd={self.BackTopInd}")
           
            
        # check toe is not inland of barrier due to MHWS     
        if not self.FrontTopInd > self.FrontToeInd:
            print("\n\tNot a barrier 6")
            self.Barrier = False
            return

        # Check if coincides with a cliff
        if self.FrontTopInd == LastInd:
            print("\n\tNot a barrier 7")
            self.Barrier = False
            return

        # this needs more work
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        
        # default back barrier positions
        self.BackTopInd = self.FrontTopInd
        Mask = ElevMasked.mask.copy()                      
        Mask[0:self.FrontTopInd] = True
        ElevMasked = ma.masked_where(Mask,ElevMasked)

        # NH: Back barrier detection: Choose MinInd=LastInd (most landward unmasked data, thus within 200 m of coast)
        MinInd = LastInd
        self.BackToeInd = MinInd
            
        
        
        # flag for changing position
        BarrierPositionChangeFlag = True
        
        while BarrierPositionChangeFlag:
            
            # FIRST Back Barrier TOE
            
            # reset flag
            BarrierPositionChangeFlag = False
            
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[MinInd]:
                print(self.LineID, self.ID)
                print(DistanceMasked[self.FrontTopInd], DistanceMasked[MinInd], self.FrontTopInd, MinInd, LastInd)
                print("Divide by zero getting back toe!")
                sys.exit()

            # Get Angle to detrend towards the coast - NH: This will only execute once as FrontTopInd and MinInd don't change. If same as FindCliff, this should be between MinInd and BackTopInd
            Angle = np.degrees(np.arctan((ElevMasked[MinInd]-ElevMasked[self.FrontTopInd]) 
                                        / (DistanceMasked[MinInd]-DistanceMasked[self.FrontTopInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontTopInd]) + (DistanceMasked[self.FrontTopInd] - DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values seaward of the barrier front top
            Mask = ElevMasked.mask.copy()              
            Mask[0:self.BackTopInd] = True
            Mask[MinInd+1:] = True
            ElevDetrend = ma.masked_where(Mask, ElevDetrend)
            NewInd = np.argmin(ElevDetrend)
            #plt.plot(DistanceMasked,ElevDetrend,'r-')
            
            # Find Minimum detrended elevation, must be negative to be considered a low (probably never a worry)
            if not NewInd == self.BackToeInd:
                if ((NewInd < self.BackToeInd) and (ElevDetrend[NewInd] < -0.001) and (NewInd > self.BackTopInd)):
                    self.BackToeInd = NewInd
                    BarrierPositionChangeFlag = True

            # THEN Back Top
            
            # catch divide by zero
            if DistanceMasked[self.FrontTopInd] == DistanceMasked[self.BackToeInd]:
                print(self.LineID, self.ID)
                print(DistanceMasked[self.FrontTopInd], DistanceMasked[self.BackToeInd], self.FrontTopInd, self.BackToeInd, LastInd)
                print("Divide by zero getting back top!")
                sys.exit()
            
            # Get Angle to detrend towards away from the coast
            Angle = np.degrees(np.arctan((ElevMasked[self.BackToeInd]-ElevMasked[self.FrontTopInd])
                                        / (DistanceMasked[self.BackToeInd]-DistanceMasked[self.FrontTopInd])))
            
            # Get detrended elevation
            ElevDetrend = ((ElevMasked-ElevMasked[self.FrontTopInd])+(DistanceMasked[self.FrontTopInd]-DistanceMasked) \
                            * np.tan(np.radians(Angle)))

            # mask values up to the peak
            Mask = ElevMasked.mask.copy()
            Mask[0:self.FrontTopInd] = True
            Mask[self.BackToeInd+1:] = True
            ElevDetrend = ma.masked_where(Mask,ElevDetrend)
            NewInd = np.argmax(ElevDetrend)
            
            # Find Maximum detrended elevation. Must be positive to be considered a change in barrier back top position
            if not self.BackTopInd == NewInd:
                if ((NewInd < self.BackToeInd) and (ElevDetrend[np.argmax(ElevDetrend)] > 0.001)):
                    self.BackTopInd = np.argmax(ElevDetrend)
                    BarrierPositionChangeFlag = True
                    
        if self.BackTopInd == LastInd:
            print("\n\tNot a barrier 8")
            self.Barrier = False
            return        
            
        # Get Barrier Crest
        #Mask = self.Elevation.mask.copy()              # Problem: this returns boolean value (not array) of False when no masked elements
        Mask = ma.getmaskarray(self.Elevation)          # Return the mask of a masked array, or full boolean array of False.
        Mask[0:self.FrontToeInd] = True
        Mask[self.BackToeInd+1:] = True                 # NH bug fix: exclude all elevations beyond BackToeInd, not just the single elev at BackToeInd
        ElevMasked = ma.masked_where(Mask,self.Elevation)
        self.CrestInd = ma.argmax(ElevMasked)
        self.CrestElevation = ElevMasked[self.CrestInd]
            
        # Calculate Barrier Height, front and back
        self.FrontHeight = self.Elevation[self.FrontTopInd]-self.Elevation[self.FrontToeInd]
        self.BackHeight = self.Elevation[self.BackTopInd]-self.Elevation[self.BackToeInd]
        
        # Calculate Barrier Width, top and bottom
        self.ToeWidth = np.abs(self.Distance[self.FrontToeInd]-self.Distance[self.BackToeInd])
        self.TopWidth = np.abs(self.Distance[self.FrontTopInd]-self.Distance[self.BackTopInd])
        
        # Calculate Slope, front and back
        self.FrontSlope = self.FrontHeight/(self.Distance[self.FrontTopInd]-self.Distance[self.FrontToeInd])
        self.BackSlope = self.BackHeight/(self.Distance[self.BackTopInd]-self.Distance[self.BackToeInd])
        
        # Volume m3/m
        Start, End = ma.notmasked_edges(self.Distance)
        self.DistanceSpacing = self.Distance[Start+1]-self.Distance[Start] # temporary fix
        
        self.BarrierVolume = ma.sum(ElevMasked)*self.DistanceSpacing
        
        self.BarrierVolume -= 0.5 * (ElevMasked[self.FrontToeInd] + ElevMasked[self.BackToeInd-1]) \
                                 * np.abs(self.Distance[self.BackToeInd-1] - self.Distance[self.FrontToeInd])
        
        # switch flag to indicate a barrier has been found
        self.Barrier = True
    
    def SaveBarrierElevations(self):
        
        """
        Use the dune toe and crest indexes from FindBarrier2 to save elevations to Transect
        Only save if transect is a barrier. Else keep as None.
        
        NH, Jan 2024
        
        """
        if self.Barrier:
            self.H_FrontToe = self.Elevation[self.FrontToeInd]
            self.H_FrontTop = self.Elevation[self.FrontTopInd]
            self.H_BackToe = self.Elevation[self.BackToeInd]
            self.H_BackTop = self.Elevation[self.BackTopInd]
            self.H_Crest = self.Elevation[self.CrestInd]
    
    def ExtractHinterlandElevSlope(self):
    
        """
        Extract mean elevation of hinterland landward of 
        back barrier toe
        
        NH, Feb 2024
        
        """
        
        if not self.Barrier:
            return
        
        # If barrier, create new unmasked Elevation array 
        data = self.Elevation
        x = np.ma.array(data, mask = False)             # This still has original mask as applied in FindBarrier2. self.Elevation is still masked!
        x.mask = False                                  # force mask reset. unmasked Elevation data now in x.data
        #print(x.data)
        
        # Create new mask: all seaward of BackToe is masked
        Mask = ma.getmask(x)
        Mask[0:self.BackToeInd] = True
        HinterlandElev = np.ma.array(x, mask=Mask) 
        #print(HinterlandElev)
        
        # Calcualte mean
        self.HinterlandElev = np.mean(HinterlandElev)
        #print(" ",self.HinterlandElev)
        
        # Create new unmasked Distance array
        data = self.Distance
        x = np.ma.array(data, mask = False)             # This still has original mask as applied in FindBarrier2. self.Elevation is still masked!
        x.mask = False 
        
        # Use above mask to mask all points seaward of back toe
        HinterlandDist = np.ma.array(x, mask=Mask) 
        
        # Calculate slope
        self.HinterlandSlope = (HinterlandElev[-1] - HinterlandElev[self.BackToeInd+1])/(HinterlandDist[-1] - HinterlandDist[self.BackToeInd+1])
        #print(" ", self.HinterlandSlope)
    
    def ClearTopographyMasks(self):
        
        """
        Clear Transect.Distance and Transect.Elevation masks set during FindCliff2 and FindBarrier2
        NH, June 2024
        
        """
        
        # Create new unmasked Elevation array
        data = self.Elevation
        x = np.ma.array(data, mask = False)       
        x.mask = False                                  # force mask reset. unmasked Elevation data now in x.data
        self.Elevation = x.data
        
        # Create new unmasked Distance array
        data = self.Distance
        x = np.ma.array(data, mask = False)             
        x.mask = False 
        self.Distance = x.data
        
        #print("E=", self.Elevation)                    # works
        #print("D=", self.Distance)
        
    
    def ExtractBarrierWidthVolume(self,Elevation=None):

        """
        Extract barrier width at a given elevation, 
        default is elevation of back barrier toe

        MDH, July 2020

        """

        if not self.Barrier:
            return
        
        # default elevation is the back barrier toe
        if not Elevation:
            Elevation = self.Elevation[self.BackToeInd]
        
        # vector at fixed elevation running the length of the transect
        Start, End = ma.notmasked_edges(self.Distance)
        X1, Y1 = self.Distance[Start], Elevation
        X2, Y2 = self.Distance[End], Elevation
        
        # calculate differences
        dX12 = X2-X1
        dY12 = Y2-Y1
        
        # count and record locations of intersection
        IntersectionCounter = 0
        IntersectionIndices = []
        InterpolateFractions = []
        
        # temporary fix for no assignment, need a function for reading in transect topo
        # rather than having it set externally?
        # self.NoValues = len(self.Distance)
        # self.DistanceSpacing = self.Distance[End]-self.Distance[End-1]
        
        # loop across barrier topography
        for i in range(Start, End):

            # cut and paste interesction analysis
            # do we want this to be a separate function somewhere?
            # Loop through transects and count no of intersections with the barrier
            # get transect line ends        
            X3,Y3 = self.Distance[i], self.Elevation[i]
            X4,Y4 = self.Distance[i+1], self.Elevation[i+1]
            
            # differences
            dX34 = X4-X3
            dY34 = Y4-Y3
            
            #Find the cross product of the two vectors
            XProd = dX12*dY34 - dX34*dY12
                
            if (XProd != 0):
                if (XProd > 0):
                    XProdPos = 1
                else:
                    XProdPos = 0
                    
                #assign third test segment
                dX31 = X1-X3
                dY31 = Y1-Y3
                    
                #get cross products
                S = dX12*dY31 - dY12*dX31
                T = dX34*dY31 - dY34*dX31
                
                #logic for collision occurence
                if ((S < 0) == XProdPos):
                    continue
                elif ((T < 0) == XProdPos):
                    continue
                elif ((S > XProd) == XProdPos):
                    continue
                elif ((T > XProd) == XProdPos):
                    continue
                else:
                    IntersectionCounter += 1
                    IntersectionIndices.append(i)
                    Fraction = np.abs((Elevation-Y3)/dY34)
                    InterpolateFractions.append(Fraction)
                    if IntersectionCounter == 2:
                        break
        
        # calculate width and volume at this elevation
        # if no intersection then either barrier crest is too low
        # or back barrier is too high
        if IntersectionCounter == 0:
            return 0, 0
        
        elif IntersectionCounter == 1:
            return -9999, -9999

        elif IntersectionCounter > 1:

            # Define Intersection Distance and Elevation by Interpolating
            Dist1 = self.Distance[IntersectionIndices[0]] + InterpolateFractions[0]*self.DistanceSpacing
            Dist2 = self.Distance[IntersectionIndices[1]] + InterpolateFractions[1]*self.DistanceSpacing
            
            Width = Dist2-Dist1
            Volume = np.sum(self.Elevation[IntersectionIndices[0]+1:IntersectionIndices[1]+1]-Elevation)*self.DistanceSpacing

            return Width, Volume

    

    def FindExtremeWaterIntersections(self, WaterElevations=[0, 2.5, 5]):
        """
        Find Extreme Water Intersections
        Doesnt require there to be a barrier
        This is a quick fix for now

        MDH, June 2022

        """

        # check if WaterElevs is single value or list
        if not isinstance(WaterElevations, list):
            self.ExtremeWaterLevels = [WaterElevations]
        else:
            self.ExtremeWaterLevels = WaterElevations
        
        # setup empty lists
        self.ExtremeDistances = ["","",""]
        self.ExtremeIndicesLists = ["","",""]
        self.ExtremeInterpFractions = ["","",""]
        self.Intersections = ["","",""]

        # loop across elevations and perform analysis
        for i, Elevation in enumerate(self.ExtremeWaterLevels):
            
            self.FindExtremeWaterIntersection(Elevation)

            # add results to lists
            self.ExtremeDistances[i] = self.ExtremeDistance
            self.ExtremeIndicesLists[i] = self.ExtremeIndices
            self.ExtremeInterpFractions[i] = self.InterpolateFractions
            self.Intersections[i] = self.Intersection

    def FindExtremeWaterIntersection(self, Elev):
        """
        Find Extreme Water Intersections
        Doesnt require there to be a barrier
        This is a quick fix for now

        MDH, June 2022
        
        """

        # add results to lists
        # NEED TO FIX NDV AS GLOBAL FROM DEM
        NDV = -10000
        self.ExtremeDistance = [None,None]
        self.ExtremeIndex = [None,None]
        self.InterpolateFractions = [None,None]
        self.ExtremeWidth = None
        self.ExtremeVolume = None
        self.FrontNode = None
        self.BackNode = None
        
        # vector at fixed elevation running the length of the transect
        Start, End = ma.notmasked_edges(self.Distance)
        X1, Y1 = self.Distance[Start], Elev
        X2, Y2 = self.Distance[End], Elev
        
        dX12 = X2-X1
        dY12 = Y2-Y1
        
        # count and record locations of intersection
        IntersectionCounter = 0
        self.IntersectionIndices = []
        InterpolateFractions = []
        
        # temporary fix for no assignment, need a function for reading in transect topo
        # rather than having it set externally?
        self.NoValues = len(self.Distance)
        self.DistanceSpacing = self.Distance[End]-self.Distance[End-1]
        
        # loop across barrier topography
        for i in range(Start, End-1):

            # cut and paste interesction analysis
            # do we want this to be a separate function somewhere?
            # Loop through transects and count no of intersections with the barrier
            # get transect line ends        
            X3,Y3 = self.Distance[i], self.Elevation[i]
            X4,Y4 = self.Distance[i+1], self.Elevation[i+1]
            
            dX34 = X4-X3
            dY34 = Y4-Y3
            
            #Find the cross product of the two vectors
            XProd = dX12*dY34 - dX34*dY12
                
            if (XProd != 0):
                if (XProd > 0):
                    XProdPos = 1
                else:
                    XProdPos = 0
                    
                #assign third test segment
                dX31 = X1-X3
                dY31 = Y1-Y3
                    
                #get cross products
                S = dX12*dY31 - dY12*dX31
                T = dX34*dY31 - dY34*dX31
                
                #logic for collision occurence
                if ((S < 0) == XProdPos):
                    continue
                elif ((T < 0) == XProdPos):
                    continue
                elif ((S > XProd) == XProdPos):
                    continue
                elif ((T > XProd) == XProdPos):
                    continue
                else:
                    IntersectionCounter += 1
                    self.IntersectionIndices.append(i)
                    Fraction = np.abs((Elev-Y3)/dY34)
                    InterpolateFractions.append(Fraction)
        
        # calculate width and volume at this elevation
        # if no intersection then either barrier crest is too low
        # or back barrier is too high
        if IntersectionCounter == 0:
            if (self.CrestElevation < Elev):
                self.ExtremeWidth = 0.
                self.ExtremeVolume = 0.
                self.ExtremeIndices = []
                self.Intersection = False
        
        elif IntersectionCounter == 1:
            
            # no width or volume but get index
            self.ExtremeWidth = -99
            self.ExtremeVolume = -99
            self.ExtremeIndices = []
            
            # calculate intersection distance and elevation
            ExtremeDist = self.Distance[self.IntersectionIndices[0]] + InterpolateFractions[0]*self.DistanceSpacing
            self.ExtremeIndices.append(self.IntersectionIndices[0])
            self.InterpolationFractions = [InterpolateFractions[0]]

            # get position of intersection
            X1 = self.StartNode.X + ExtremeDist * np.sin( np.radians( self.Orientation ) )
            Y1 = self.StartNode.Y + ExtremeDist * np.cos( np.radians( self.Orientation ) )
            IntersectionNode = Node(X1,Y1,Elev)
            self.IntersectionNodes.append(IntersectionNode)

            # flag that an intersection has occurred
            self.Intersection = True            

    def ExtractBarrierWidths(self,WaterElevations=[0, 2.5, 5]):

        """
        Extract Barrier widths at all given elevations
        e.g. variable extreme water or projected extreme water

        This needs rewritten to be simpler and more flexible

        MDH, June 2019
        
        """

        # check if WaterElevs is single value or list
        if not isinstance(WaterElevations, list):
            self.ExtremeWaterLevels = [WaterElevations]
        else:
            self.ExtremeWaterLevels = WaterElevations
        
        # setup empty lists
        self.ExtremeDistances = ["","",""]
        self.ExtremeIndicesLists = ["","",""]
        self.ExtremeInterpFractions = ["","",""]
        self.ExtremeWidths = ["","",""]
        self.ExtremeVolumes = ["","",""]
        self.ExtremeTotalWidths = ["","",""]
        self.ExtremeTotalVolumes = ["","",""]
        self.ExtremeFrontNodes = ["","",""]
        self.ExtremeBackNodes = ["","",""]
        self.Intersections = ["","",""]

        # loop across elevations and perform analysis
        for i, Elevation in enumerate(self.ExtremeWaterLevels):
            
            self.ExtractBarrierWidth(Elevation)

            # add results to lists
            self.ExtremeDistances[i] = self.ExtremeDistance
            self.ExtremeIndicesLists[i] = self.ExtremeIndices
            self.ExtremeInterpFractions[i] = self.InterpolateFractions
            self.ExtremeWidths[i] = self.ExtremeWidth
            self.ExtremeVolumes[i] = self.ExtremeVolume
            self.ExtremeTotalWidths[i] = self.ExtremeWidthTotal
            self.ExtremeTotalVolumes[i] = self.ExtremeVolumeTotal
            self.ExtremeFrontNodes[i] = self.FrontNode
            self.ExtremeBackNodes[i] = self.BackNode
            self.Intersections[i] = self.Intersection

    
    
    def ExtractBarrierWidth(self, Elev):

        """
        Extract barrier width at a given elevation (e.g. extreme water level)

        MDH, June 2019
        """

        # add results to lists
        NDV = -9999
        self.ExtremeDistance = [None,None]
        self.ExtremeIndex = [None,None]
        self.InterpolateFractions = [None,None]
        self.ExtremeWidth = None
        self.ExtremeVolume = None
        self.FrontNode = None
        self.BackNode = None
        
        if self.Barrier == False:
            return

        # vector at fixed elevation running the length of the transect
        Start, End = ma.notmasked_edges(self.Distance)
        X1, Y1 = self.Distance[Start], Elev
        X2, Y2 = self.Distance[End], Elev
        
        dX12 = X2-X1
        dY12 = Y2-Y1
        
        # count and record locations of intersection
        IntersectionCounter = 0
        self.IntersectionIndices = []
        InterpolateFractions = []
        
        # temporary fix for no assignment, need a function for reading in transect topo
        # rather than having it set externally?
        self.NoValues = len(self.Distance)
        self.DistanceSpacing = self.Distance[End]-self.Distance[End-1]
        
        # loop across barrier topography
        for i in range(Start, self.NoValues-1):

            # cut and paste interesction analysis
            # do we want this to be a separate function somewhere?
            # Loop through transects and count no of intersections with the barrier
            # get transect line ends        
            X3,Y3 = self.Distance[i], self.Elevation[i]
            X4,Y4 = self.Distance[i+1], self.Elevation[i+1]
            
            dX34 = X4-X3
            dY34 = Y4-Y3
            
            #Find the cross product of the two vectors
            XProd = dX12*dY34 - dX34*dY12
                
            if (XProd != 0):
                if (XProd > 0):
                    XProdPos = 1
                else:
                    XProdPos = 0
                    
                #assign third test segment
                dX31 = X1-X3
                dY31 = Y1-Y3
                    
                #get cross products
                S = dX12*dY31 - dY12*dX31
                T = dX34*dY31 - dY34*dX31
                
                #logic for collision occurence
                if ((S < 0) == XProdPos):
                    continue
                elif ((T < 0) == XProdPos):
                    continue
                elif ((S > XProd) == XProdPos):
                    continue
                elif ((T > XProd) == XProdPos):
                    continue
                else:
                    IntersectionCounter += 1
                    self.IntersectionIndices.append(i)
                    Fraction = np.abs((Elev-Y3)/dY34)
                    InterpolateFractions.append(Fraction)
        
        # calculate width and volume at this elevation
        # if no intersection then either barrier crest is too low
        # or back barrier is too high
        if IntersectionCounter == 0:
            if (self.CrestElevation < Elev):
                self.ExtremeWidth = 0.
                self.ExtremeVolume = 0.
                self.ExtremeIndices = []
                self.Intersection = False
        
        elif IntersectionCounter == 1:
            self.ExtremeWidth = -99
            self.ExtremeVolume = -99
            self.ExtremeIndices = []
            self.Intersection = False

        elif IntersectionCounter > 1:

            # modify this to get first set of interesections and full sets of intersections...
            self.ExtremeIndices = []
            self.ExtremeWidthTotal = 0
            self.ExtremeVolumeTotal = 0

            # loop through intersections in pairs that define positive features relative to elevation
            for i in range(0,len(self.IntersectionIndices),2):

                # catch if we're at the end of the intersection list
                if ((i+1) >= len(self.IntersectionIndices)):
                    continue

                # Define Intersection Distance and Elevation by Interpolating
                ExtremeDist1 = self.Distance[self.IntersectionIndices[i]] + InterpolateFractions[i]*self.DistanceSpacing
                ExtremeDist2 = self.Distance[self.IntersectionIndices[i+1]] + InterpolateFractions[i+1]*self.DistanceSpacing
            
                # Record distances
                self.ExtremeDistance = [ExtremeDist1,ExtremeDist2]
                self.ExtremeIndex = [self.IntersectionIndices[i], self.IntersectionIndices[i+1]]
                self.ExtremeIndices.append(self.IntersectionIndices[i])
                self.ExtremeIndices.append(self.IntersectionIndices[i+1])
                self.InterpolationFractions = [InterpolateFractions[i], InterpolateFractions[i+1]]
                
                # Define Intersection X and Y coordinates by Interpolating
                # Calculate position of front intersection
                X1 = self.StartNode.X + ExtremeDist1 * np.sin( np.radians( self.Orientation ) )
                Y1 = self.StartNode.Y + ExtremeDist1 * np.cos( np.radians( self.Orientation ) )
                FrontNode = Node(X1,Y1,Elev)

                # Calculate position of back intersection
                X2 = self.StartNode.X + ExtremeDist2 * np.sin( np.radians( self.Orientation ) )
                Y2 = self.StartNode.Y + ExtremeDist2 * np.cos( np.radians( self.Orientation ) )
                BackNode = Node(X2,Y2,Elev)

                # append intersection nodes
                self.IntersectionNodes.append(FrontNode)
                self.IntersectionNodes.append(BackNode)

                # Calculate Width
                self.ExtremeWidthTotal += self.Distance[self.IntersectionIndices[1]] + InterpolateFractions[1]*self.DistanceSpacing \
                                    - self.Distance[self.IntersectionIndices[0]] + InterpolateFractions[0]*self.DistanceSpacing
                
                # Calculate Volume
                self.ExtremeVolumeTotal += np.sum(self.Elevation[self.IntersectionIndices[0]+1:self.IntersectionIndices[1]+1]-Elev)*self.DistanceSpacing
            
                # flag that an intersection has occurred
                self.Intersection = True

                # catch the first topographic feature for the short term resilliance
                if (i==0):
                    self.FrontNode = FrontNode
                    self.BackNode = BackNode
                    self.ExtremeWidth = self.ExtremeWidthTotal
                    self.ExtremeVolume = self.ExtremeVolumeTotal
            

    def SimplePlot(self, PlotFolder, ReverseFlag=False):

        """
        
        Function to plot transects topography

        MDH, October 2019

        """

        # catch no data cases
        if self.Elevation.count() == 0:
            print("\n\tNo data to plot")
            print(self.Elevation)
            print(self.Distance)
            return

        # grab colour map
        ColourMap = cm.viridis

        # create figure
        fig = plt.figure(1,figsize=(6,3))
                
        # create 4 subplots
        ax = fig.add_subplot(111)
                
        # plot raw, unmasked data
        ax.plot(self.Distance, self.Elevation, '-', lw=1., c=[0.5,0.5,0.5], zorder=21)
        
        # set up text alignment depending on figure orientation
        if ReverseFlag:
            Alignment="left"
        else:
            Alignment="right"
        
        # add water to MHWS
        self.ExtractBarrierWidth(self.MHWS)
        if self.IntersectionIndices:
            plt.fill_between(self.Distance[0:self.IntersectionIndices[0]],  
                            self.Elevation[0:self.IntersectionIndices[0]], np.ones(self.IntersectionIndices[0])*self.MHWS,
                            color=(0.6,0.8,1.0))
            plt.text(50., self.MHWS+0.5, "MHWS", ha='center',color=[0.4,0.6,0.8])
        
        if ReverseFlag:
            plt.text(0.9, 0.9,'Sea', ha='center', va='center', transform=ax.transAxes)
            plt.text(0.05, 0.9,'Land', ha='center', va='center', transform=ax.transAxes)
        else:
            plt.text(0.05, 0.9,'Sea', ha='center', va='center', transform=ax.transAxes)
            plt.text(0.9, 0.9,'Land', ha='center', va='center', transform=ax.transAxes)

        # label axes
        ax.set_aspect(10.)
        ax.set_ylabel("Elevation (m OD)")
        ax.set_xlabel("Distance toward land (m)")

        # set axis limits 
        Start, End = ma.notmasked_edges(self.Distance)
        if Start != End:
            ax.set_xlim([self.Distance[Start],self.Distance[End]])
            ax.set_ylim([self.Elevation[Start],np.max(self.Elevation[Start:End])+1])
        
        # temporary over-ride to fix axis limits
        #ax.set_xlim([0.,600.])
        #ax.set_ylim([0.,15.])

        # flip the plot in the horizontal?
        if ReverseFlag:
            xmin, xmax = ax.get_xlim()
            ax.set_xlim([xmax,xmin])

        # add text
        plt.title("Line " + str(self.LineID) + "; Transect " + str(self.ID))

        if self.Rocky:
            plt.text(0.2, 0.9,'Rocky', ha='center', va='center', transform=ax.transAxes)

        # tight layout!
        plt.tight_layout()

        # save the figure        
        fig.savefig(PlotFolder+"SimpleTransect_"+ str(self.LineID) + "_" +str(self.ID)+".png", dpi=300)

        # close the figure
        plt.close(fig)

    def Plot(self, PlotFolder, ReverseFlag=False):
        
        """
        
        Function to plot transects analysed for topographic barriers

        MDH, June 2019

        """

        # catch no data cases
        if self.Elevation.count() == 0:
            print("\n\tNo data to plot")
            print(self.Elevation)
            print(self.Distance)
            return

        # grab colour map
        ColourMap = cm.viridis

        # create figure
        fig = plt.figure(1,figsize=(6,3))
                
        # create 4 subplots
        ax = fig.add_subplot(111)
                
        # plot raw, unmasked data
        ax.plot(self.Distance, self.Elevation, '-', lw=1., c=[0.5,0.5,0.5], zorder=21)
        
        # set up text alignment depending on figure orientation
        if ReverseFlag:
            Alignment="left"
        else:
            Alignment="right"
            
        # add cliff details here
        if self.Cliff:
            
            # plot top to toe
            CliffColour = [0.6,0.4,0.1]
            ax.plot(self.Distance[self.CliffToeInd:self.CliffTopInd], self.Elevation[self.CliffToeInd:self.CliffTopInd], '-', c=CliffColour, lw=1., zorder=22)
            ax.plot(self.Distance[self.CliffTopInd], self.Elevation[self.CliffTopInd], 'ko', mfc=CliffColour, zorder=31)
            ax.plot(self.Distance[self.CliffToeInd], self.Elevation[self.CliffToeInd], 'ko', mfc=CliffColour, zorder=31)

        # # add barrier details here
        if self.Barrier:
        
            # create array for filling in geometry
            DistFill = self.Distance[self.FrontToeInd:self.BackToeInd+1]
            ElevFill = self.Elevation[self.FrontToeInd:self.BackToeInd+1]
            LowerFill = np.linspace(ElevFill[0],ElevFill[-1],len(ElevFill)) 
        
            # plot the barrier profile and points
            ax.fill_between(DistFill, ElevFill, LowerFill, color=[0.8,0.8,0.8], zorder=10)
            ax.plot(DistFill, ElevFill, 'k-', lw=1., zorder=22)
            ax.plot(self.Distance[self.FrontTopInd], self.Elevation[self.FrontTopInd], 'ko', ms=2, zorder=32)
            ax.plot(self.Distance[self.FrontToeInd], self.Elevation[self.FrontToeInd], 'ko', ms=2, zorder=32)
            ax.plot(self.Distance[self.BackTopInd], self.Elevation[self.BackTopInd], 'ko', ms=2, zorder=32)
            ax.plot(self.Distance[self.BackToeInd], self.Elevation[self.BackToeInd], 'ko', ms=2, zorder=32)
        
        # add extreme water lines and volumes
        #self.ExtremeWaterLevels = None
        if not self.ExtremeWaterLevels:
            Blah = "hello"
        else:
            for i, WaterLevel in enumerate(self.ExtremeWaterLevels):
                
                if self.Intersections[i]:

                    # plot line and extend seaward
                    LineDists = self.ExtremeDistances[i].copy()
                    LineDists[0] -= 20.
                    ax.plot(LineDists, [WaterLevel,WaterLevel], '-', lw=1., color=LineColour, zorder=20)
                    
                    if (self.ExtremeWidths[i] is None) or (self.ExtremeWidths[i] == -99):
                        continue
    
                    # get colour
                    Colour = 1.5*float(i)/(len(self.ExtremeWaterLevels))
                    LineColour = ColourMap(Colour)
        
                    
                    
                    # colour in, this will have minor bug for now due to abs argmin returning either node before or node after
                    Inds = self.ExtremeIndicesLists[i]
                    DistFill = np.insert(self.ExtremeDistances[i], 1, self.Distance[Inds[0]+1:Inds[1]])
                    ElevFill = np.insert(np.array([WaterLevel, WaterLevel]), 1, self.Elevation[Inds[0]+1:Inds[1]])
                    LowerFill = np.linspace(ElevFill[0],ElevFill[-1],len(ElevFill))
                    
                    # lighten the colour slightly
                    LighterColour = ColourMap(Colour+0.1)
                    
                    # and shade in the region above the extreme elevation
                    ax.fill_between(DistFill, ElevFill, LowerFill, color=LighterColour, zorder=11+i)
    
                    # label elevations
                    plt.text(LineDists[0],WaterLevel,
                            str(WaterLevel)+" m OD", 
                            color=ColourMap(Colour), ha=Alignment,size="smaller")

            # add label for volume
            #plt.text(LineDists[0],WaterLevel,
            #            "$V_B$ = " + "{:.1f}".format(self.ExtremeVolumes[-1]) + " m$^3$ m$^{-1}$", 
            #            color=[0.5,0.4,0.3], ha=Alignment)

        # add water to MHWS
        self.ExtractBarrierWidth(self.MHWS)
        if self.IntersectionIndices:
            plt.fill_between(self.Distance[0:self.IntersectionIndices[0]],  
                            self.Elevation[0:self.IntersectionIndices[0]], np.ones(self.IntersectionIndices[0])*self.MHWS,
                            color=(0.6,0.8,1.0))
            plt.text(50., self.MHWS+0.5, "MHWS", ha='center',color=[0.4,0.6,0.8])
        
        if ReverseFlag:
            plt.text(0.9, 0.9,'Sea', ha='center', va='center', transform=ax.transAxes)
            plt.text(0.05, 0.9,'Land', ha='center', va='center', transform=ax.transAxes)
        else:
            plt.text(0.05, 0.9,'Sea', ha='center', va='center', transform=ax.transAxes)
            plt.text(0.9, 0.9,'Land', ha='center', va='center', transform=ax.transAxes)

        # label axes
        ax.set_aspect(2.)
        ax.set_ylabel("Elevation (m OD)")
        ax.set_xlabel("Distance toward land (m)")

        # set axis limits 
        Start, End = ma.notmasked_edges(self.Elevation)
        
        if Start != End:
            ax.set_xlim([self.Distance[Start],self.Distance[End]])
            ax.set_ylim([self.Elevation[Start],np.max(self.Elevation[Start:End])+1])
        
        # temporary over-ride to fix axis limits
        ax.set_xlim([150.,300.])
        ax.set_ylim([0.,15.])

        # flip the plot in the horizontal?
        if ReverseFlag:
            xmin, xmax = ax.get_xlim()
            ax.set_xlim([xmax,xmin])

        # add text
        plt.title("Line " + str(self.LineID) + "; Transect " + str(self.ID))

        if self.Rocky:
            plt.text(0.2, 0.9,'Rocky', ha='center', va='center', transform=ax.transAxes)

        # tight layout!
        plt.tight_layout()

        # save the figure   
        fig.savefig(PlotFolder+"/Transect_"+ str(self.LineID) + "_" +str(self.ID)+".png", dpi=300)

        # close the figure
        plt.close(fig)

        

    def PlotFuturePositions(self, PlotFolder):

        """
        
        Plots a transect line and future shoreline positions, labelled by year

        MDH, September 2019

        """

        fig = plt.figure(1,figsize=(6.,6.))

        # create 4 subplots
        ax = fig.add_subplot(111)
                
        # plot transect line
        ax.plot([self.StartNode.X,self.EndNode.X], [self.StartNode.Y,self.EndNode.Y], 'ko--', lw=1.)

        # plot historic shoreline positions
        for i in range(0,len(self.HistoricShorelinesDates)):
            
            ax.plot(self.HistoricShorelinesPositions[i][0].X,self.HistoricShorelinesPositions[i][0].Y,'bo')
            ax.text(self.HistoricShorelinesPositions[i][0].X,self.HistoricShorelinesPositions[i][0].Y,str(self.HistoricShorelinesDates[i]))
        
        # plot future shoreline positions
        
        for i in range(0,len(self.FutureSeaLevelYears)):
            Colour = [float(i)/len(self.FutureSeaLevelYears),0.5,0.5]
            ax.plot(self.FutureShorelinesPositions[i].X,self.FutureShorelinesPositions[i].Y,'o',color=Colour)
            ax.text(self.FutureShorelinesPositions[i].X,self.FutureShorelinesPositions[i].Y,str(self.FutureSeaLevelYears[i]))

        plt.axis("equal")
        plt.xlabel("X [m]")
        plt.ylabel("Y [m]")

        # save the figure        
        fig.savefig(PlotFolder / "TempTransectPlot.png", dpi=300)

        # close the figure
        plt.close(fig)

    def PlotShorelineDistances(self, PlotFolder):

        """
        Plots shoreline positions through time for historic and future shorelines

        MDH, Sept 2023

        """

        # Create figure and axis
        fig = plt.figure(1,figsize=(6.,3.))
        ax = fig.add_subplot(111)
        
        ax.plot(self.HistoricShorelinesDates,self.HistoricShorelinesDistances,'ko')
        
        #labels
        plt.xlabel("Year")
        plt.ylabel("Distance Landward (m)")

        #finalise
        plt.tight_layout()
        fig.savefig(PlotFolder / "ShorelineDist.png", dpi=300)

        # close the figure
        plt.close(fig)

    def get_XY(self):
        
        """
        Returns X and Y coordinates of start and end nodes

        MDH, June 2019
        
        """

        X = [self.StartNode.X, self.EndNode.X]
        Y = [self.StartNode.Y, self.EndNode.Y]
        
        return np.array(X), np.array(Y)

    def get_Midpoint(self):
        """
        Returns a node object for the midpoint on a transect
        MDH, July 2020

        """
        MidX = (self.StartNode.X + self.EndNode.X)/2.
        MidY = (self.StartNode.Y + self.EndNode.Y)/2.
        return Node(MidX, MidY)

    def get_CliffPosition(self):

        if not self.Cliff:
            sys.exit("self.get_CliffPosition: Not a cliff!")

        # calculate X and Y
        CliffTopDist = self.Distance[self.CliffTopInd]
        CliffToeDist = self.Distance[self.CliffToeInd]
        
        # Calculate position of cliff top
        X1 = self.StartNode.X + CliffTopDist * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + CliffTopDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of cliff toe
        X2 = self.StartNode.X + CliffToeDist * np.sin( np.radians( self.Orientation ) )
        Y2 = self.StartNode.Y + CliffToeDist * np.cos( np.radians( self.Orientation ) )
        
        return Node(X1, Y1), Node(X2, Y2)

    def get_BarrierPosition(self):

        """
        Calculates the position of nodes that define the barrier based on the top and toe
        on the front and back side, plus the crest of the barrier

        MDH, July 2019

        """

        if not self.Barrier:
            sys.exit("self.get_BarrierPosition: Not a barrier!")

        # get distances
        BarrierFrontTopDist = self.Distance[self.FrontTopInd]
        BarrierFrontToeDist = self.Distance[self.FrontToeInd]
        BarrierBackTopDist = self.Distance[self.BackTopInd]
        BarrierBackToeDist = self.Distance[self.BackToeInd]
        CrestDist = self.Distance[self.CrestInd]
        
        # Calculate position of barrier front top
        X1 = self.StartNode.X + BarrierFrontTopDist * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + BarrierFrontTopDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier front toe
        X2 = self.StartNode.X + BarrierFrontToeDist * np.sin( np.radians( self.Orientation ) )
        Y2 = self.StartNode.Y + BarrierFrontToeDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier back top
        X3 = self.StartNode.X + BarrierBackTopDist * np.sin( np.radians( self.Orientation ) )
        Y3 = self.StartNode.Y + BarrierBackTopDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier back toe
        X4 = self.StartNode.X + BarrierBackToeDist * np.sin( np.radians( self.Orientation ) )
        Y4 = self.StartNode.Y + BarrierBackToeDist * np.cos( np.radians( self.Orientation ) )
        
        # Calculate position of crest
        X5 = self.StartNode.X + CrestDist * np.sin( np.radians( self.Orientation ) )
        Y5 = self.StartNode.Y + CrestDist * np.cos( np.radians( self.Orientation ) )
        Z5 = self.Elevation[self.CrestInd]

        return Node(X1, Y1), Node(X2, Y2), Node(X3, Y3), Node(X4, Y4), Node(X5, Y5, Z5)

    def get_ExtremePosition(self,Ind):
        
        """
        return nodes for extreme front position and back position and index Ind
        Ind must be 0, 1, or 2, for low, medium and high water levels

        MDH, July 2019
        
        """
        if not Ind in [0,1,2]:
            sys,exit("self.get_ExtremePosition (Error): mist be an integer for extreme water (0,1, or 2)") 
            
        FrontDist = self.ExtremeDistances[Ind][0]
        BackDist = self.ExtremeDistances[Ind][1]

        if not isinstance(FrontDist,float):
            return
        elif not isinstance(BackDist,float):
            return

        # Calculate position of barrier front top
        X1 = self.StartNode.X + FrontDist * np.sin( np.radians( self.Orientation ) )
        Y1 = self.StartNode.Y + FrontDist * np.cos( np.radians( self.Orientation ) )

        # Calculate position of barrier front top
        X2 = self.StartNode.X + BackDist * np.sin( np.radians( self.Orientation ) )
        Y2 = self.StartNode.Y + BackDist * np.cos( np.radians( self.Orientation ) )

        return Node(X1,Y1), Node(X2,Y2)

    def get_CrestPosition(self):

        """
        MDH, July 2019
        
        """
        if self.Barrier:

            # Get Distance
            CrestDistance = self.Distance[self.CrestInd]

            # Calculate position of barrier front top
            X = self.StartNode.X + CrestDistance * np.sin( np.radians( self.Orientation ) )
            Y = self.StartNode.Y + CrestDistance * np.cos( np.radians( self.Orientation ) )
            Z = self.Elevation[self.CrestInd]
            return X, Y, Z
        
        else:
            return

    def get_FrontPosition(self):

        """
        MDH, July 2019
        
        """
        if self.Barrier:

            # Get Distance
            FrontDistance = self.Distance[self.FrontTopInd]

            # Calculate position of barrier front top
            X = self.StartNode.X + FrontDistance * np.sin( np.radians( self.Orientation ) )
            Y = self.StartNode.Y + FrontDistance * np.cos( np.radians( self.Orientation ) )
            Z = self.Elevation[self.FrontTopInd]
            return X, Y, Z
        
        else:
            return

    def get_FuturePosition(self, Year):

        """

        Get the future position of the coast for a particular year
        from Bruun Rule predictions

        MDH, October 2019

        """

        # check there are predictions for this transect
        if self.Future:

            # find year index
            Index = [i for i, x in enumerate(self.FutureSeaLevelYears) if x == Year]
            
            if len(Index) == 0:
                return

            # use to access future position
            Position = self.FutureShorelinesPositions[Index[0]]
            return Position

        else:
            return
    
    def get_FutureDistance(self, Year, Timeseries="MHWS"):

        """

        Get the future cposition of the coast in distance along transect
        from Bruun Rule predictions

        Updated July 2026 to work with Timeseries object

        MDH, November 2020

        """

        # check there are predictions for this transect
        if not self.Future:
            return None

        # retrieve timeseries
        TS = self.Timeseries[Timeseries]

        # convert to datetime if an integer
        if isinstance(Year, int):
            Year = datetime(Year, 1, 1)

        # find year index
        LatestDate = TS.Dates[-1]

        # Before (or at) latest observation -> observed shoreline
        if Year <= LatestDate:
            return TS.Distances[-1]

        # Find index of future
        Index = self.FutureSeaLevelYears.index(Year)

        # use to access future position
        return self.FutureShorelinesDistances[Index]
    
    def get_FuturePositionChange(self, Year1, Year2, Timeseries="MHWS"):

        """

        Get the future change in  position of the coast over a particular number of years
        from Bruun Rule predictions

        Updated July 2026 to work with timeseries object

        MDH, October 2019

        """
        if not self.Future:
            return None

        Distance1 = self.get_FutureDistance(Year1, Timeseries="MHWS")
        Distance2 = self.get_FutureDistance(Year2, Timeseries="MHWS")

        if Distance1 is None or Distance2 is None:
            return None

        return Distance1 - Distance2
        
    def get_ExtrapDistance(self, Year, Timeseries="MHWS", RateMethod="TWR"):

        """

        Get the extrapolated future position of the coast by extrapolating
        historical rate of shoreline change

        Updated to use TS objects July 2026

        MDH, October 2020

        """

        if self.Future:
            
            TS = self.Timeseries[Timeseries]
            LatestDate = TS.Dates[-1]
            Rate = TS.Results[RateMethod]["Rate"]

            # extrapolate future position on transect
            ExtrapYears = (datetime(Year,1,1) - LatestDate).days / 365.2425
            Distance = ExtrapYears*Rate
            return Distance

        else:
            return
    
    def get_FutureRate(self, Year1, Year2, Timeseries="MHWS"):

        """

        Get the future erosion rate of the coast for a particular period of years
        from Bruun Rule predictions. Rates are negative for erosion, positive
        for accretion

        MDH, January 2020

        """

        # check there are predictions for this transect
        if not self.Future:
            return None

        # check the timeseries specified exists probably redundant
        if Timeseries not in self.Timeseries:
            raise ValueError(f"Timeseries '{Timeseries}' does not exist")
        
        # convert to datetime if an integer
        if isinstance(Year1, int):
            Year1 = datetime(Year1, 1, 1)
        if isinstance(Year2, int):
            Year2 = datetime(Year2, 1, 1)

        # get date of most recent observation
        LatestDate = self.Timeseries[Timeseries].Dates[-1]

            
        # check year1 isnt less than an historic shoreline
        if Year1 < LatestDate:
            Year1 = LatestDate

        # get the position change
        PositionChange = self.get_FuturePositionChange(Year1, Year2, Timeseries=Timeseries)

        if PositionChange is None:
            return None
        
        # calculate average rate
        YrDiff = (Year2-Year1).days / 365.2425
        return PositionChange/YrDiff
            

    def get_TotalErosion(self, Year1, Year2):

        """
        
        Get the total amount of erosion that has taken place by a given decade 
        in the future predictions
        
        MDH, March 2021
        
        """

        # check there are predictions for this transect
        if self.Future:
            
            # get the position change
            Distance = self.get_FuturePositionChange(Year1, Year2)
            return Distance

        else:
            return
            
    def get_FirstFutureErosionYear(self):

        """
        Martin Hurst, October 2020
        
        """
        for i in range(1, len(self.FutureSeaLevelYears)):

            Change = self.get_FuturePositionChange(self.FutureSeaLevelYears[i-1], self.FutureSeaLevelYears[i])
            
            if Change < 0:
                return self.FutureSeaLevelYears[i-1].year
        
        return

    def get_FutureMaxRate(self, Year1, Year2):

        """

        Get the future erosion rate of the coast for a particular year
        from Bruun Rule predictions

        MDH, January 2020

        """

        # check there are predictions for this transect
        if self.Future:

            # use to access future position
            self.PredictFutureShorelineUncertainty(Year1)
            Distance1 = self.FutureShorelineMinDistance
            self.PredictFutureShorelineUncertainty(Year2)
            Distance2 = self.FutureShorelineMinDistance
            MaxRate = (Distance2-Distance1)/(Year2-Year1)
            return MaxRate

        else:
            return

    def Check_OS_Year(self):
        
        """
        
        Get the year of the Historic shoreline position from OS 2020 smart
        
        MDH, November 2020
        
        """
        
        Index = [i for i, x in enumerate(self.HistoricShorelinesSources) if x.endswith("Modern_Soft.shp")]
        try:
            self.OSYear = self.HistoricShorelinesDates[Index[0]]
        except:
            self.OSYear = -9999
    
    def get_FutureVegEdge(self, Year):

        """

        Get the future position of the vegetation edge for a particular year
        from Bruun Rule predictions

        MDH, February 2020

        """

        # check there are predictions for this transect
        if self.VegEdge:

            # find year index
            Index = [i for i, x in enumerate(self.FutureSeaLevelYears[1:]) if x == Year]
            
            if len(Index) == 0:
                return

            # use to access future position
            Position = self.FutureVegEdgePositions[Index[0]]
            return Position

        else:
            return

    def get_Position(self, Distance):

        """

        Returns a node of the position at a set distance along the transect

        MDH, September 2020

        """

        # extend transect landward and seaward?
        X = self.StartNode.X + Distance * np.sin( np.radians( self.Orientation ) )
        Y = self.StartNode.Y + Distance * np.cos( np.radians( self.Orientation ) )
        
        return Node(X,Y)

    def get_RecentPosition(self, Timeseries="MHWS"):

        """

        Get the most recent position of the coast 
        
        Updated July 2026 to work with timeseries objects

        MDH, January 2020

        """

        # catch if no shoreline
        if Timeseries not in self.Timeseries:
            return None

        TS = self.Timeseries[Timeseries]

        if not TS.HasData(Minimum=1):
            return None

        return TS.Positions[-1]
    
    def get_RecentYear(self):

        """
        
        Get the year of the most recent position of the coast
        
        MDH, March 2021
        
        """

        # catch if no shoreline
        if len(self.HistoricShorelinesDates) == 0:
            return
            #raise Exception("self.get_RecentPosition: No recent position")

        # find index of most recent historical shoreline
        Index = np.argmax(self.HistoricShorelinesDates)
        Year = self.HistoricShorelinesDates[Index]
            
        return Year

    def get_RecentDistance(self, Timeseries="MHWS"):

        """

        Get the most recent position of the coast 

        Updated July 2026 to work with timeseries objects
        
        MDH, November 2020

        """

        # catch if no timeseries
        if Timeseries not in self.Timeseries:
            raise ValueError(f"Timeseries '{Timeseries}' does not exist")

        TS = self.Timeseries[Timeseries]

        # catch if no shoreline
        if not TS.HasData(Minimum=1):
            raise ValueError("No recent shoreline distance")

        return TS.Distances[-1]

    def get_OldestPosition(self):

        """

        Get the most oldest position of the coast 

        MDH, January 2020

        """

        # find index of most recent historical shoreline
        Index = np.argmin(self.HistoricShorelinesDates)
        Position = self.HistoricShorelinesPositions[Index][0]
        return Position 

    def get_Geometry(self):

        """
        Return the transect geometry as a Shapely LineString.

        MDH, July 2026

        """

        # get coordinates
        X = np.asarray([self.StartNode.X, self.EndNode.X])
        Y = np.asarray([self.StartNode.Y, self.EndNode.Y])

        # check length
        if len(X) < 2:
            return None

        # return linestring object
        return LineString(zip(X, Y))
    
    def get_Record(self):

        """
        Return the standard output attributes for the transect.
        MDH, July 2026
        """
        
        return {
            "Cell": str(self.Cell), "SubCell": str(self.SubCell), "CMU": str(self.CMU), "LineID": int(self.LineID), "TransectID": int(self.ID),
            "Cliff_H": self.CliffHeight, "Cliff_S": self.CliffSlope,
            "Rocky": int(self.Rocky),
            "Bar_FH": self.FrontHeight, "Bar_FS": self.FrontSlope,
            "Bar_BH": self.BackHeight, "Bar_BS": self.BackSlope,
            "Bar_ToeW": self.ToeWidth, "Bar_TopW": self.TopWidth,
            "Bar_Volume": self.BarrierVolume, "Crest_Elev": self.CrestElevation,
            "ST_W_low": self.ExtremeWidths[0], "ST_V_low": self.ExtremeVolumes[0],
            "ST_W_med": self.ExtremeWidths[1], "ST_V_med": self.ExtremeVolumes[1],
            "ST_W_high": self.ExtremeWidths[2], "ST_V_high": self.ExtremeVolumes[2],
            "LT_W_low": self.ExtremeTotalWidths[0], "LT_V_low": self.ExtremeTotalVolumes[0],
            "LT_W_med": self.ExtremeTotalWidths[1], "LT_V_med": self.ExtremeTotalVolumes[1],
            "LT_W_high": self.ExtremeTotalWidths[2], "LT_V_high": self.ExtremeTotalVolumes[2]
        }

    def get_FutureRecord(self):

        """
        Return the future output attributes for the transect.
        MDH, July 2026
        """

        # Might need to add dict for TS type
        TS = self.Timeseries["MHWS"]
        LatestDateString = str(TS.Dates[-1])
        LatestSourceString = str(TS.Sources[-1])

        return {
            "Cell": str(self.Cell), "SubCell": str(self.SubCell), "CMU": str(self.CMU), "LineID": int(self.LineID), "TransectID": int(self.ID),
            "Hist_Rate": self.ChangeRate,
            "LatestYr": LatestDateString, "LatestSrc": LatestSourceString, "FirstEYr": self.get_FirstFutureErosionYear(),
            "Extrap2050": self.get_ExtrapDistance(2050), "Extrap2100": self.get_ExtrapDistance(2100),
            "pDist_2030": self.get_FuturePositionChange(2020, 2030), "pRate_2030": self.get_FutureRate(2020, 2030), 
            "Dist_2040": self.get_FuturePositionChange(2030, 2040), "Rate_2040": self.get_FutureRate(2030, 2040),
            "Dist_2050": self.get_FuturePositionChange(2040, 2050), "Rate_2050": self.get_FutureRate(2040, 2050),
            "Dist_2060": self.get_FuturePositionChange(2050, 2060), "Rate_2060": self.get_FutureRate(2050, 2060),
            "Dist_2070": self.get_FuturePositionChange(2060, 2070), "Rate_2070": self.get_FutureRate(2060, 2070),
            "Dist_2080": self.get_FuturePositionChange(2070, 2080), "Rate_2080": self.get_FutureRate(2070, 2080),
            "Dist_2090": self.get_FuturePositionChange(2080, 2090), "Rate_2090": self.get_FutureRate(2080, 2090),
            "Dist_2100": self.get_FuturePositionChange(2090, 2100), "Rate_2100": self.get_FutureRate(2090, 2100),
            "RCP85_2050": self.FutureSeaLevels[2], "RCP85_2100": self.FutureSeaLevels[7]}
        
    def Write(self, Folder=os.getcwd(), Filename="", delimiter=","):
        
        """
        
        Write transect topography to file

        Can sepcify filename or create using default name + ID
        
        MDH, July 2019
        
        NH mod October 2023:
        - Change filename to include coastline number and transect number.
          This fixes problem where csv files get overwritten in the case of 
          multiple coastlines.
        - Add parameter for user-defined filename
        
        Parameters
        ----------
        Folder : str
            Folder path of where the .csv files will be written 
            
        Filename : str
            Start of the filename, before coastline ID and transect ID

        delimiter : str
            Delimiter used in csv output files
            
        Output
        ------
        One .csv file for each transect written to destination folder
        
        """

        # define filename and open for writing
        if not Filename:
            Filename = Folder+"/Transect_"+str(self.LineID)+"_"+str(self.ID)+".csv"
        else:
            Filename = Folder+"/"+str(Filename)+"_"+str(self.LineID)+"_"+str(self.ID)+".csv"
        f = open(Filename,'w')
        
        # write headers
        f.write("X" + delimiter + "Y" + "\n")
        f.write(str(self.StartNode.X) + delimiter + str(self.StartNode.Y) + "\n")
        f.write(str(self.EndNode.X) + delimiter + str(self.EndNode.Y) + "\n")
        f.write("Distance" + delimiter + "Z" + "\n")

        #loop through transect and write data
        for (dist, z) in zip(self.Distance, self.Elevation):
            f.write(str(dist) + delimiter + str(z) + "\n")

        f.close()
        
        
    def WriteSwath(self, Folder=os.getcwd(), Filename="", delimiter=","):
    
        """
        Write tranect swath topography to file
        Can sepcify filename or create using default name + ID
        
        NH, October 2023
        
        Parameters
        ----------
        Folder : str
            Folder path of where the .csv files will be written 
            
        Filename : str
            Start of the filename, before coastline ID and transect ID

        delimiter : str
            Delimiter used in csv output files
            
        Output
        ------
        One .csv file for each transect written to destination folder
    
        """
    
        # define filename and open for writing
        if not Filename:
            Filename = Folder+"/Transect_"+str(self.LineID)+"_"+str(self.ID)+".csv"
        else:
            Filename = Folder+"/"+str(Filename)+"_"+str(self.LineID)+"_"+str(self.ID)+".csv"
        f = open(Filename,'w')
        
        # write headers
        #f.write("X" + delimiter + "Y" + "\n")
        #f.write(str(self.StartNode.X) + delimiter + str(self.StartNode.Y) + "\n")
        #f.write(str(self.EndNode.X) + delimiter + str(self.EndNode.Y) + "\n")
        f.write("Distance" + delimiter + "ZIDW" + delimiter + "ZMin" + delimiter + "ZMax" +"\n")

        #loop through transect and write data
        for (dist, z, zmin, zmax) in zip(self.Distance, self.Elevation, self.ElevationMin, self.ElevationMax):
            f.write(str(dist) + delimiter + str(z) + delimiter + str(zmin) + delimiter + str(zmax) + "\n")

        f.close()


    
    
    
    