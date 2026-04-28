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
from .Node import *

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
        self.HistoricShorelinesYears = []
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
        self.MinChangeRate = None
        self.MaxChangeRate = None
        self.DeleteFlag = False

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
        String += self.HistoricShorelinesYears
        String += self.HistoricalShorelinesDistances

        return String
    
    def ResetHistoricShorelines(self):
        
        # historic shoreline positions, distances and change rates
        self.HistoricFlag = False
        self.HistoricShorelinesSources = []
        self.HistoricShorelinesYears = []
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
        
        if self.Future:
            self.PredictFutureShorelineUncertainty(Year)
        else:
            return
            
        # get all distances
        DistancesList = []
        
        #if self.LineID == "24" and self.ID == "28":
            #import pdb
            #pdb.set_trace()
        
        for i in range(0,len(self.HistoricShorelinesYears)):
            
            # add nodes to lists
            DistancesList.append(self.HistoricShorelinesDistances[i][0])
            DistancesList.append(self.HistoricShorelinesDistances[i][0]+self.HistoricShorelinesErrors[i])
            DistancesList.append(self.HistoricShorelinesDistances[i][0]-self.HistoricShorelinesErrors[i])
        
        # need a condition here to ignore distances from future where accretion is occuring
        
        for i in range(0, len(self.FutureSeaLevelYears)):
            
            # add nodes to lists
            if self.FutureShorelinesDistances[i] > self.HistoricShorelinesDistances[-1][0]:
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
        
    def CalculateHistoricalRates(self):

        """
        Function to calculate historical rates of shoreline change based on
        historical shoreline positions

        This function requires several funcions with the Coast object to have been run
        first but the Coast wrapper should/could check for this.
        
        By convention, negative values indicate erosion and positive indicate accretion

        MDH, October 2020

        """

        # cant make calculations without some historical shorelines
        if not self.HistoricShorelinesYears:
            self.Future = False
            return
    
        # need at least two for a rate
        elif len(self.HistoricShorelinesYears) < 2:
            self.Future = False
            return        

        # reset change rates in case already calculated
        self.ChangeRates = []
        self.ChangeRateErrors = []
        
        # historic shoreline positions and change rates
        for i in range(0,len(self.HistoricShorelinesYears)):
            
            # first do the whole length of the record
            if i == 0:
                dEta = (self.HistoricShorelinesDistance[-1] - self.HistoricShorelinesDistance[0])
                ErrorSum = self.HistoricShorelinesErrors[-1] + self.HistoricShorelinesErrors[0]
                dT = float(((self.HistoricShorelinesYears[-1] - self.HistoricShorelinesYears[0]).days)/365.2425)
                
            
            # otherwise do the shorter period
            else:
                j = 1
                while True:
                    dT = float(((self.HistoricShorelinesYears[i] - self.HistoricShorelinesYears[i-j]).days)/365.2425)
                    if (i-j == 0):
                        dEta = self.HistoricShorelinesDistance[i] - self.HistoricShorelinesDistance[i-j]
                        ErrorSum = self.HistoricShorelinesErrors[i] + self.HistoricShorelinesErrors[i-j]
                        break
                    elif dT < 4:
                        j += 1
                        continue
                    else:
                        dEta = self.HistoricShorelinesDistance[i] - self.HistoricShorelinesDistance[i-j]
                        ErrorSum = self.HistoricShorelinesErrors[i] + self.HistoricShorelinesErrors[i-j]
                        break
                
            self.ChangeRates.append(-dEta/dT)
            self.ChangeRateErrors.append(ErrorSum/dT)

        self.HistoricFlag = True

        # add logic here to get best change rate and min/max?
        # get min 
        
        min_max_date = '2000-01-01'
        
        TempIndex = np.argmin(np.array(self.ChangeRates)[np.array(self.HistoricShorelinesYears) > (datetime.strptime(min_max_date, "%Y-%m-%d"))])
        IndexMin = np.where(np.array(self.HistoricShorelinesYears) > (datetime.strptime(min_max_date, "%Y-%m-%d")))[0][TempIndex]
        self.MinChangeRate = self.ChangeRates[IndexMin]

        # and max rates
        TempIndex = np.argmax(np.array(self.ChangeRates)[np.array(self.HistoricShorelinesYears) > (datetime.strptime(min_max_date, "%Y-%m-%d"))])
        IndexMax = np.where(np.array(self.HistoricShorelinesYears) > (datetime.strptime(min_max_date, "%Y-%m-%d")))[0][TempIndex]
        self.MaxChangeRate = self.ChangeRates[IndexMax]

    def CalculateHistoricalRegression(self):
    
        """
        Function to calculate historical rates of shoreline change based on
        historical shoreline positions. 
        
        Modified from original DC2 methodology (Transect.py function
        CalculateHistoricalRates) by Craig MacDonell to use weighted
        regression instead of most recent line and next 4 or 5 years prior.
    
        This function requires several funcions with the Coast object to have been run
        first but the Coast wrapper should/could check for this.
        
        By convention, negative values indicate erosion and positive indicate accretion
    
        CM, January 2025
    
        """

        # cant make calculations without some historical shorelines
        if not self.HistoricShorelinesYears:
            self.Future = False
            return
    
        # need at least two for a rate
        elif len(self.HistoricShorelinesYears) < 2:
            self.Future = False
            return        

        # reset change rates in case already calculated
        self.ChangeRates = []
        self.ChangeRateErrors = []
        
        ### REGRESSION RATE CALCULATIONS - Recency Proportional Weights ###       
        
        # Convert dates to numerical values for regression
        dates_numeric = np.array([date.toordinal() for date in self.HistoricShorelinesYears])
        
        # Get the current date
        current_date = datetime.now().date()
        # Convert the date to ordinal
        ordinal_value = current_date.toordinal()
        
        max_date = max(dates_numeric)
        scale_factor = 365.2425 * 10  # variable to smooth or strengthen recent-time weighting
    
        # Calculate weights using the smoother function
        weights = np.exp(-(max_date - dates_numeric) / scale_factor)
        # Normalize weights
        weights /= np.sum(weights)
        
        incErrors_weighting = 0
        if incErrors_weighting == 1:
            # Calculate recency weights
            recency_weights = np.exp(-(max_date - dates_numeric) / scale_factor)
            recency_weights /= np.sum(recency_weights)  # Normalize weights
            
            # Incorporate shoreline errors as weights
            error_weights = 1 / (np.array(self.HistoricShorelinesErrors) ** 2)
            combined_weights = recency_weights * error_weights
            combined_weights /= np.sum(combined_weights)  # Normalize weights
            weights = combined_weights
        
        # Perform weighted regression
        coefficients = np.polyfit(dates_numeric, self.HistoricShorelinesDistance, 1, w=weights)
        slope, intercept = coefficients
        slope_yr = round(slope*365.2425,3)*-1
        
        # Calculate the regression line
        regression_line = slope * dates_numeric + intercept
        
        # Calculate R-squared
        residuals = self.HistoricShorelinesDistance - regression_line
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((self.HistoricShorelinesDistance - np.mean(self.HistoricShorelinesDistance)) ** 2)
        r_sq = round(1 - (ss_res / ss_tot), 3)
        
        # Calculate confidence intervals
        n = len(dates_numeric)
        mean_x = np.mean(dates_numeric)
        alpha = 0.05
        t_value = t.ppf(1 - alpha / 2, n - 2)  # 95% confidence interval
        
        # Weighted residual standard error
        weighted_residuals = residuals * weights
        rss = np.sum(weighted_residuals ** 2)
        if n <= 2: 
            stderr = 0
        else:    
            stderr = np.sqrt(rss / (n - 2))
        
        # Confidence interval for regression line
        conf_interval = t_value * stderr * np.sqrt(
            1 / n + (dates_numeric - mean_x) ** 2 / np.sum((dates_numeric - mean_x) ** 2))
        
        self.ChangeRates.append(slope_yr)
        self.ChangeRateErrors.append(stderr)
        
    def CalculateHistoricalRegression_testing(self):
    
        """
        Function to calculate historical rates of shoreline change based on
        historical shoreline positions. 
        
        THIS FUNCTION WILL NOT UPDATE self.ChangeRates or self.ChangeRateErrors,
        it is simply used for TESTING the regression fit
        
        Modified from original DC2 methodology (Transect.py function
        CalculateHistoricalRates) by Craig MacDonell to use weighted
        regression instead of most recent line and next 4 or 5 years prior.
    
        This function requires several funcions with the Coast object to have been run
        first but the Coast wrapper should/could check for this.
        
        By convention, negative values indicate erosion and positive indicate accretion
    
        CM, January 2025
    
        """
        
        """Type here
        result_ratess = []
        resuts_errors = []
        for timeweighting in timeweightings:
            do regression and get rate and error
            add to list of results and errors
            
        plt.plot(timeweightings, results,'ko--')
        
        """

        # cant make calculations without some historical shorelines
        if not self.HistoricShorelinesYears:
            self.Future = False
            return
    
        # need at least two for a rate
        elif len(self.HistoricShorelinesYears) < 2:
            self.Future = False
            return        

        # reset change rates in case already calculated
        self.ChangeRates = []
        self.ChangeRateErrors = []
        
        # Convert dates to numerical values for regression
        dates_numeric = np.array([date.toordinal() for date in self.HistoricShorelinesYears])
                
        # overall rate
        dateDiff0 = self.HistoricShorelinesYears[-1] - self.HistoricShorelinesYears[0]
        dt0 = dateDiff0.total_seconds() / (365.2425 * 24 * 3600)
        dD0 = self.HistoricShorelinesDistance[-1] - self.HistoricShorelinesDistance[0]
        rate0 = round((dD0 / dt0),3)*-1
        
        # rate after 2000
        # Find the index of the first date after 1st January 2000
        threshold_date = datetime(2000, 1, 1)
        index2000 = next(
            (i for i, date in enumerate(self.HistoricShorelinesYears) if date > threshold_date), 
            None
        )
        
        if index2000 is not None:
            # Get the corresponding datetime and value from the separate list
            date2000 = self.HistoricShorelinesYears[index2000]
            dist2000 = self.HistoricShorelinesDistance[index2000]
            
            dateList2000 = self.HistoricShorelinesYears[index2000:]
            distList2000 = self.HistoricShorelinesDistance[index2000:]
            
            # Calculate the difference in years
            dt1 = (self.HistoricShorelinesYears[-1] - date2000).total_seconds() / (
                365.2425 * 24 * 3600
            )
            
            dD1 = self.HistoricShorelinesDistance[-1] - dist2000
            rate1 = round((dD1 /dt1),3)*-1
        else:
            print("No date found after 1st Jan 2000")
            
        # Perform linear regression
        slope0, intercept0 = np.polyfit(dates_numeric, self.HistoricShorelinesDistance, 1)  # 1 = degree of the polynomial
        regression_line0 = slope0 * np.array(dates_numeric) + intercept0
        # Calculate R-squared
        residuals0 = self.HistoricShorelinesDistance - regression_line0
        ss_res0 = np.sum(residuals0 ** 2)
        ss_tot0 = np.sum((self.HistoricShorelinesDistance - np.mean(self.HistoricShorelinesDistance)) ** 2)
        r_sq0 = round(1 - (ss_res0 / ss_tot0),3)

# WEIGHTED REGRESSIONS
        # Linearly Increasing Weights
        weights1 = np.linspace(1, 10, len(self.HistoricShorelinesYears))  # Adjust the range if needed
        coefficients1 = np.polyfit(dates_numeric, self.HistoricShorelinesDistance, 1, w=weights1)  # 1 = degree of the polynomial
        slope1, intercept1 = coefficients1
        regression_line1 = slope1 * dates_numeric + intercept1
        # Calculate R-squared
        residuals1 = self.HistoricShorelinesDistance - regression_line1
        ss_res1 = np.sum(residuals1 ** 2)
        ss_tot1 = np.sum((self.HistoricShorelinesDistance - np.mean(self.HistoricShorelinesDistance)) ** 2)
        r_sq1 = round(1 - (ss_res1 / ss_tot1),3)
        
        # Recency Proportional Weights
        result_rates = []
        result_errors = []
        result_weights = []
        
        max_date3 = max(dates_numeric)

        timeweightings = np.arange(2,20,1)
            
        for tw in timeweightings:
            sf = 365.2425*tw
            weights3t = np.exp(-(max_date3 - dates_numeric) / sf)
            weights3t /= np.sum(weights3t)
            
            if tw == 10:
                wTableReport = weights3t
                print(self.HistoricShorelinesYears)
                print(wTableReport)
                sys.exit(-1)
        
            incErrors_weighting = 0        
            if incErrors_weighting == 1:
                # Calculate recency weights
                recency_weights = np.exp(-(max_date3 - dates_numeric) / sf)
                recency_weights /= np.sum(recency_weights)  # Normalize weights
                
                # Incorporate shoreline errors as weights
                error_weights = 1 / (np.array(self.HistoricShorelinesErrors) ** 2)
                combined_weights = recency_weights * error_weights
                combined_weights /= np.sum(combined_weights)  # Normalize weights
                weights3t = combined_weights
                
            result_weights.append(weights3t)
 
            coefficients3t = np.polyfit(dates_numeric, self.HistoricShorelinesDistance, 1, w=weights3t)
            slope3t, intercept3t = coefficients3t
            slope3t_yr = round(slope3t*365.2425,3)*-1
            
            # Calculate the regression line
            regression_line3t = slope3t * dates_numeric + intercept3t
            if tw == 10:
                regression_line3 = regression_line3t
            
            # Calculate R-squared
            residuals3t = self.HistoricShorelinesDistance - regression_line3t
            ss_res3t = np.sum(residuals3t ** 2)
            ss_tot3t = np.sum((self.HistoricShorelinesDistance - np.mean(self.HistoricShorelinesDistance)) ** 2)
            r_sq3t = round(1 - (ss_res3t / ss_tot3t), 3)
            
            # Calculate R-squared for data after 2000 only
            residuals3tt = distList2000 - regression_line3t[index2000:]
            ss_res3tt = np.sum(residuals3tt ** 2)
            ss_tot3tt = np.sum((distList2000 - np.mean(distList2000)) ** 2)
            r_sq3tt = round(1 - (ss_res3tt / ss_tot3tt),3)
            
            # Calculate confidence intervals
            n = len(dates_numeric)
            mean_x = np.mean(dates_numeric)
            alpha = 0.05
            t_value = t.ppf(1 - alpha / 2, n - 2)  # 95% confidence interval
            
            # Weighted residual standard error
            weighted_residuals3t = residuals3t * weights3t
            rss = np.sum(weighted_residuals3t ** 2)
            stderr = np.sqrt(rss / (n - 2))
            
            # Confidence interval for regression line
            conf_interval = t_value * stderr * np.sqrt(
                1 / n + (dates_numeric - mean_x) ** 2 / np.sum((dates_numeric - mean_x) ** 2)
    )
            
            result_rates.append(slope3t_yr)
            result_errors.append(stderr)
        
        plotWeightings = 1    
        if plotWeightings == 1:
            plt.clf()
            plt.plot(timeweightings, result_rates,'ko-')
            #plt.plot(timeweightings, result_errors,'co--')
            plt.xlabel('Weighting Scale Factor (yrs)')
            plt.ylabel('Coastal Change Rates (m/yr)')
            titleText = "Montrose - Transect: " + str(self.ID)
            plt.title(titleText)
            
            
            plt.savefig("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS2_National_Scale_Change/Supersites/Montrose_2024/CMT/test" + str(self.ID)+ ".png")
            
        #return
        #sys.exit(-1)
    
# Plot transect plots to test regression
        plotTransect = 1
        if plotTransect == 1:
            plt.clf()
            plt.errorbar(
                self.HistoricShorelinesYears, 
                self.HistoricShorelinesDistance, 
                yerr=self.HistoricShorelinesErrors,  # Use the errors directly
                fmt='o',  # Marker for the data points
                ecolor='gray',  # Color of the error bars
                elinewidth=1,  # Line width of the error bars
                capsize=3,  # Caps at the end of error bars
                label='Shoreline Positions with Errors'
            )
            plt.plot(self.HistoricShorelinesYears, self.HistoricShorelinesDistance, marker='o', linestyle='-', color='b', label='Shoreline Positions')
            
            # Plot the regression lines
            plt.plot(self.HistoricShorelinesYears, regression_line0, color='r', linestyle='--', label='Linear Regression')
            
            plt.fill_between(
                self.HistoricShorelinesYears,
                regression_line3 - conf_interval,
                regression_line3 + conf_interval,
                color='gray',
                alpha=0.3,
                label='95% Confidence Interval'
            )
            plt.plot(self.HistoricShorelinesYears, regression_line3, color='m', linestyle='--', label='Recency Proportional Weights')
            
            #plt.plot(self.HistoricShorelinesYears, regression_line3a, color='m', linestyle='--', label='RPW 5yrs')
            #plt.plot(self.HistoricShorelinesYears, regression_line3b, color='g', linestyle='--', label='RPW 10yrs')
            #plt.plot(self.HistoricShorelinesYears, regression_line3c, color='k', linestyle='--', label='RPW 15yrs')
            #plt.plot(self.HistoricShorelinesYears, regression_line3d, color='y', linestyle='--', label='RPW 20yrs')
            
            #plt.plot(date2000,dist2000,marker='+',color='r',label='First shoreline after 2000')
            
            plt.plot([self.HistoricShorelinesYears[0], self.HistoricShorelinesYears[-1]],[self.HistoricShorelinesDistance[0], self.HistoricShorelinesDistance[-1]],linestyle=':', color='g',label='Overall Rate')
            #plt.plot([date2000, self.HistoricShorelinesYears[-1]],[dist2000, self.HistoricShorelinesDistance[-1]],linestyle=':', color='r',label='Rate since 2000')
            
# =============================================================================
#             slope0_yr = round(slope0*365.2425,3)*-1
#                     
#             slope_text = (
#                         "Overall Rate: " + str(rate0) + " m/yr\n"
#                         "Rate since 2000: " + str(rate1) + " m/yr\n"
#                         f"Slope 0 (LR): {slope0_yr:.3f} m/yr ($R^2 = {r_sq0:.3f}$)\n"
#                         f"Slope 3 (RPW 5yrs): {(-1*slope3a*365.2425):.3f} m/yr ($R^2 = {r_sq3a:.3f}$) ($R^2 (2000) = {r_sq3aa:.3f}$)\n"
#                         f"Slope 3 (RPW 10yrs): {(-1*slope3b*365.2425):.3f} m/yr ($R^2 = {r_sq3b:.3f}$) ($R^2 (2000) = {r_sq3bb:.3f}$)\n"
#                         f"Slope 3 (RPW 15yrs): {(-1*slope3c*365.2425):.3f} m/yr ($R^2 = {r_sq3c:.3f}$) ($R^2 (2000) = {r_sq3cc:.3f}$)\n"
#                         f"Slope 3 (RPW 20yrs): {(-1*slope3d*365.2425):.3f} m/yr ($R^2 = {r_sq3d:.3f}$) ($R^2 (2000) = {r_sq3dd:.3f}$)\n"
#                         )
#             
#             plt.text(max(self.HistoricShorelinesYears) + timedelta(days=2500), y_ave, slope_text, color='r', fontsize=10, ha='left', va='center')
# =============================================================================
            
            y_min, y_max = plt.gca().get_ylim()
            y_ave = y_min + ((y_max - y_min)/2)
            
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
            
            fig_fn = '/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS2_National_Scale_Change/Supersites/Montrose_2024/CMT/regressionFigures/Montrose_Transect_' + str(self.ID) + '.png'
            plt.savefig(fig_fn, dpi=300, bbox_inches='tight')
            
        return
        sys.exit(-1)

# Weighted regression spreadsheet writing (for testing)
        # Path to the existing Excel file
        excel_file_path = '/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS2_National_Scale_Change/Supersites/Montrose_2024/CMT/regressionFigures/regressionAnalysis.xlsx'
        
        # Try reading the existing Excel file
        try:
            existing_df = pd.read_excel(excel_file_path)
        except FileNotFoundError:
            # If the file doesn't exist, create an empty DataFrame with the column names
            columns = ["Location", "ID", 
                       "First Shoreline", "Overall Rate", "Recent Shoreline",
                       "Current CMT rate",
                       "First shoreline after 2000", "Rate since 2000",
                       "Linear Regression", "LR R2",
                       #"Linearly Increasing Weights", "LIW R2",
                       #"Recency Proportional Weights", "RPW R2",
                       "RPW5","RPW5 R2","RPW5 R2000",
                       "RPW10","RPW10 R2","RPW10 R2000",
                       "RPW15","RPW15 R2","RPW15 R2000",
                       "RPW20","RPW20 R2","RPW20 R2000"]
                       
            
            existing_df = pd.DataFrame(columns=columns)
            
        
        row = {"Location": loc, "ID": self.ID, 
                   "First Shoreline":self.HistoricShorelinesYears[0], "Overall Rate":rate0, "Recent Shoreline":self.HistoricShorelinesYears[-1],
                   "Current CMT rate":self.ChangeRates[-1],
                   "First shoreline after 2000":date2000, "Rate since 2000":rate1,
                   "Linear Regression":slope0_yr, "LR R2":r_sq0,
                   #"Linearly Increasing Weights":slope1_yr, "LIW R2":r_sq1,
                   #"Recency Proportional Weights":slope3_yr, "RPW R2":r_sq3,
                   "RPW5":-1*slope3a*365.2425,"RPW5 R2":r_sq3a,"RPW5 R2000":r_sq3aa,
                   "RPW10":-1*slope3b*365.2425,"RPW10 R2":r_sq3b,"RPW10 R2000":r_sq3bb,
                   "RPW15":-1*slope3c*365.2425,"RPW15 R2":r_sq3c,"RPW15 R2000":r_sq3cc,
                   "RPW20":-1*slope3d*365.2425,"RPW20 R2":r_sq3d,"RPW20 R2000":r_sq3dd,
            }
         
        # Convert the row to a DataFrame
        row_df = pd.DataFrame([row])
        
        # Append the row DataFrame to the existing DataFrame
        existing_df = pd.concat([existing_df, row_df], ignore_index=True)
        #print(existing_df)
        # Save the updated DataFrame back to the Excel file
        with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:
            # Open the existing workbook and append the new data to the same sheet
            existing_df.to_excel(writer, index=False,sheet_name='Sheet1')

        sys.exit('Transect.CalculateHistoricRegression_testing: completed testing, please check transect plots and spreadsheet for regression fit')

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
    
    def PredictFutureShorelines(self, MaxRockHeadErosionDistance=25., MinMaxFlag=None):

        """
        Function to predict the future position of the shoreline based on
        historical shoreline positions, historical rates of sea level change
        and future rates of sea level change following a calibrated Bruun Rule
        type approach.

        This function requires several functions with the Coast object to have been run
        first but the Coast wrapper should/could check for this.

        MDH, September 2019

        """
        
        # reset outputs incase already has been run
        self.FutureShorelinesPositions = []
        self.FutureShorelinesRates = []
        self.FutureShorelinesDistances = []
        self.InterpolatedRSLR = []
        
        # boolean flag if making prediction
        self.Future = True
        
        # cant make predictions without some historical shorelines
        if not self.HistoricShorelinesYears:
            self.Future = False
            return

        # dont let 1970s be calibration year if younger than modern soft
        if len(self.HistoricShorelinesYears) > 2:
            if self.HistoricShorelinesSources[-2].endswith("1970.shp") and self.HistoricShorelinesSources[-3].endswith("Soft.shp"):
                self.HistoricShorelinesSources.pop(-2)
                self.HistoricShorelinesDistances.pop(-2)
                self.HistoricShorelinesPositions.pop(-2)
                self.HistoricShorelinesErrors.pop(-2)
                self.HistoricShorelinesYears.pop(-2)

# =============================================================================
#         # check if the two most recent positions are closer than 4 years together
#         while (float(((self.HistoricShorelinesYears[-1] - self.HistoricShorelinesYears[-2]).days)/365.2425) < 4):
#             self.HistoricShorelinesSources.pop(-2)
#             self.HistoricShorelinesDistances.pop(-2)
#             self.HistoricShorelinesPositions.pop(-2)
#             self.HistoricShorelinesErrors.pop(-2)
#             self.HistoricShorelinesYears.pop(-2)
# =============================================================================
        
        # some logic here to check if its sensible to make predictions
        if len(self.HistoricShorelinesYears) < 2:
            self.Future = False
            return
        
        # do not make predicitions if there are multiple lines on a single day (prev. single year)???
        
        
        for i in range(0,len(self.HistoricShorelinesYears)):
            self.HistoricShorelinesDistance.append(self.HistoricShorelinesDistances[i][0])
            self.HistoricShorelinesPosition.append(self.HistoricShorelinesPositions[i][0])

        NoPositions = [len(Distances) for Distances in self.HistoricShorelinesDistances]
        EqualBool = NoPositions[1:] == NoPositions[:-1]

        if not EqualBool:
            self.Future = False
            return

        # calculate historical rates
        if not self.HistoricFlag:
            #self.CalculateHistoricalRates() # old DC2 method
            self.CalculateHistoricalRegression() # updated regression method
        
        # interpolate to get average RSLR in each time stamp between 1870s and 2020
        FutureSeaLevelYears_diff = (self.FutureSeaLevelYears[1] - self.FutureSeaLevelYears[0]).days / 365.2425
        FutureSeaLevelRate = (self.FutureSeaLevels[1] - self.FutureSeaLevels[0])/(FutureSeaLevelYears_diff)
        RSLRDiff= FutureSeaLevelRate-self.HistoricalRSLR/1000.
        
        InterpolationYears = []
        for i in range(0,len(self.HistoricShorelinesYears)):
            if i == 0:
                base_date = self.HistoricShorelinesYears[0]
                decYrs = 0.5*float(((self.HistoricShorelinesYears[-1] - self.HistoricShorelinesYears[0]).days)/365.2425)
                
                full_years = int(decYrs)
                fractional_years = decYrs - full_years

                # Add full years first
                new_date = base_date + relativedelta(years=full_years)
                # Convert fractional years into days (accounting for leap years)
                additional_days = int(round(fractional_years * 365.2425))
                # Add the fractional days
                new_date = new_date + relativedelta(days=additional_days)
                
                InterpolationYears.append(new_date)
            else:
                base_date = self.HistoricShorelinesYears[i-1]
                decYrs = 0.5*float(((self.HistoricShorelinesYears[i] - self.HistoricShorelinesYears[i-1]).days)/365.2425)
                
                full_years = int(decYrs)
                fractional_years = decYrs - full_years

                # Add full years first
                new_date = base_date + relativedelta(years=full_years)
                # Convert fractional years into days (accounting for leap years)
                additional_days = int(round(fractional_years * 365.2425))
                # Add the fractional days
                new_date = new_date + relativedelta(days=additional_days)
                
                InterpolationYears.append(new_date)
                
# =============================================================================
#                 InterpolationYears.append((self.HistoricShorelinesYears[0]+self.HistoricShorelinesYears[i-1]-self.HistoricShorelinesYears[0])+
#                                           0.5*(self.HistoricShorelinesYears[i]-self.HistoricShorelinesYears[i-1]))
# =============================================================================

        InterpFractions = np.array([
            (interp_year - self.HistoricShorelinesYears[0]) / (self.FutureSeaLevelYears[0] - self.HistoricShorelinesYears[0])
            for interp_year in InterpolationYears
        ], dtype=float)
        
        self.InterpolatedRSLR = self.HistoricalRSLR/1000.+RSLRDiff*InterpFractions
        
        # get slope from intertidal zoneif we dont already have it
        if not self.ShorefaceSlope:
            self.ShorefaceDistance = self.MLWS.get_Distance(self.HistoricShorelinesPosition[-1])
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
        self.VolumetricCalibrationRates = self.ShorefaceDepth*np.array(self.ChangeRates) + (self.ShorefaceDepth/self.BruunSlope)*(self.InterpolatedRSLR)
        self.VolumetricCalibrationErrors = self.ShorefaceDepth*np.array(self.ChangeRateErrors) + (self.ShorefaceDepth/self.BruunSlope)*(self.InterpolatedRSLR)

        # get sea level at latest time
        if self.HistoricShorelinesYears[-1] < self.FutureSeaLevelYears[0]:
            self.LatestRSL = self.FutureSeaLevels[0]
        else:
            Interp = (self.FutureSeaLevelYears[1]-self.HistoricShorelinesYears[-1])/(self.FutureSeaLevelYears[1]-self.FutureSeaLevelYears[0])
            self.LatestRSL = self.FutureSeaLevels[1]-Interp*(self.FutureSeaLevels[1]-self.FutureSeaLevels[0])

        # print(MinMaxFlag)
        
        # set index for calibration
        if self.LongTermOnly:
            CalibrationRate = self.VolumetricCalibrationRates[0]
            self.ChangeRate = self.ChangeRates[0]
            self.MinChangeRate = self.ChangeRate
            self.MaxChangeRate = self.ChangeRate
            self.CalibrationYear = self.HistoricShorelinesYears[0]

# =============================================================================
### EXCLUDE BEST/WORST CALCULATIONS INITIALLY WITH DATETIME UPGRADES - SEPARATE UPGRADE WORK ALONG WITH WEIGHTED REGRESSION
#         # get min 
#         TempIndex = np.argmin(self.VolumetricCalibrationRates[np.array(self.HistoricShorelinesYears) > 2000])
#         IndexMin = np.where(np.array(self.HistoricShorelinesYears) > 2000)[0][TempIndex]
#         
#         # and max rates
#         TempIndex = np.argmax(self.VolumetricCalibrationRates[np.array(self.HistoricShorelinesYears) > 2000])
#         IndexMax = np.where(np.array(self.HistoricShorelinesYears) > 2000)[0][TempIndex]
# 
#         if ((MinMaxFlag == "Min") or (MinMaxFlag == "min")):
#             CalibrationRate = self.VolumetricCalibrationRates[IndexMin]
#             self.ChangeRate = self.ChangeRates[IndexMin]
#             self.CalibrationYear = self.HistoricShorelinesYears[IndexMin]
# 
#         elif ((MinMaxFlag == "Max") or (MinMaxFlag == "max")):
#             CalibrationRate = self.VolumetricCalibrationRates[IndexMax]
#             self.ChangeRate = self.ChangeRates[IndexMax]
#             self.CalibrationYear = self.HistoricShorelinesYears[IndexMax]
# 
#         else:
#             CalibrationRate = self.VolumetricCalibrationRates[-1]
#             self.ChangeRate = self.ChangeRates[-1]
#             self.CalibrationYear = self.HistoricShorelinesYears[-2]
# =============================================================================
        
        CalibrationRate = self.VolumetricCalibrationRates[-1]
        self.ChangeRate = self.ChangeRates[-1]
        self.CalibrationYear = self.HistoricShorelinesYears[-2]

        # Future shoreline positions
        for i in range(0, len(self.FutureSeaLevelYears)):

            dT = (self.FutureSeaLevelYears[i]-self.HistoricShorelinesYears[-1]).days / 365.2425

            # catch the condition where observed shorelines are more recent than those we're trying to make predictions for
            if dT <= 0:
                #print('Predict Future Shorelines - observed shorelines are more recent than predictions:', str(self.FutureSeaLevelYears[i]), '-', self.HistoricShorelinesYears[-1])
                X1 = self.HistoricShorelinesPosition[-1].X
                Y1 = self.HistoricShorelinesPosition[-1].Y

                self.FutureShorelinesPositions.append(Node(X1,Y1))
                self.FutureShorelinesRates.append(self.ChangeRates[-1])
                self.FutureShorelinesDistances.append(self.HistoricShorelinesDistances[-1][0])

                continue
            
            # self.InterpolatedRSLR
            BruunRuleComponent = -(1./self.BruunSlope)*(self.FutureSeaLevels[i]-self.LatestRSL)
            CalibrationComponent = (1./self.ShorefaceDepth)*CalibrationRate*dT
            ShorelinePositionChange = BruunRuleComponent+CalibrationComponent
            
            # check rock head position not exceeded
            HistoricShorelineDistance = self.StartNode.get_Distance(self.HistoricShorelinesPosition[-1])
            FutureShorelineDistance = HistoricShorelineDistance - ShorelinePositionChange
            
            if self.DefencesDistance and (FutureShorelineDistance > self.DefencesDistance):

                # if landward of
                self.FutureShorelinesPositions.append(self.DefencesPosition)
                
                ShorelinePositionChange = HistoricShorelineDistance - self.DefencesDistance
                self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
                self.FutureShorelinesDistances.append(self.DefencesDistance)
            
            elif self.RockHeadDistance and (FutureShorelineDistance > self.RockHeadDistance):

                # if landward of
                self.FutureShorelinesPositions.append(self.RockHeadPosition)
                
                ShorelinePositionChange = HistoricShorelineDistance - self.RockHeadDistance
                self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
                self.FutureShorelinesDistances.append(self.RockHeadDistance)
            
            # otherwise write new shoreline position as appropriate
            else:
                X1 = self.HistoricShorelinesPosition[-1].X - ShorelinePositionChange * np.sin( np.radians( self.Orientation ) )
                Y1 = self.HistoricShorelinesPosition[-1].Y - ShorelinePositionChange * np.cos( np.radians( self.Orientation ) )

                self.FutureShorelinesPositions.append(Node(X1,Y1))
                self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
                self.FutureShorelinesDistances.append(FutureShorelineDistance)

        # add analysis of 2100 uncertainty based on historical position change
        self.VolumetricCalibrationRates = np.append(self.VolumetricCalibrationRates, 0.)
        
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
            dT = Year-self.HistoricShorelinesYears[-1]

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
                X1 = self.HistoricShorelinesPosition[-1].X + ShorelinePositionChange * np.sin( np.radians( self.Orientation ) )
                Y1 = self.HistoricShorelinesPosition[-1].Y + ShorelinePositionChange * np.cos( np.radians( self.Orientation ) )

                self.FutureShorelinesPositions.append(Node(X1,Y1))
                self.FutureShorelinesRates.append(ShorelinePositionChange/dT)
                self.FutureShorelinesDistances.append(FutureShorelineDistance)

                

    def PredictFutureShorelineUncertainty(self, Year=2100):

        """
        Function to map uncertainty for shoreline position in a certain year based on range 
        of historical coastal changes

        MDH March 2020

        """
        
        # get future sea level and time difference
        Index = [i for i, x in enumerate(self.FutureSeaLevelYears) if x == Year]
        FutureSeaLevel = self.FutureSeaLevels[Index[0]]
        dT = Year-self.HistoricShorelinesYears[-1]

        # reset min and max in case uncertainty has been previously assessed
        self.FutureShorelineMinDistance = 9999999.
        self.FutureShorelineMaxDistance = -9999999.

        # get sea level at latest time
        if self.HistoricShorelinesYears[-1] < self.FutureSeaLevelYears[0]:
            self.LatestRSL = self.FutureSeaLevels[0]
        else:
            Interp = (self.FutureSeaLevelYears[1]-self.HistoricShorelinesYears[-1])/(self.FutureSeaLevelYears[1]-self.FutureSeaLevelYears[0])
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
        dT = Year-self.HistoricShorelinesYears[-1]

        # reset min and max in case uncertainty has been previously assessed
        self.FutureShorelineMinDistance = 9999999.
        self.FutureShorelineMaxDistance = -9999999.

        # get sea level at latest time
        if self.HistoricShorelinesYears[-1] < self.FutureSeaLevelYears[0]:
            self.LatestRSL = self.FutureSeaLevels[0]
        else:
            Interp = (self.FutureSeaLevelYears[1]-self.HistoricShorelinesYears[-1])/(self.FutureSeaLevelYears[1]-self.FutureSeaLevelYears[0])
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
        Offset = self.HistoricShorelinesDistances[-1][0] - self.VegEdgeDistance

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
        for i in range(0,len(self.HistoricShorelinesYears)):
            
            ax.plot(self.HistoricShorelinesPositions[i][0].X,self.HistoricShorelinesPositions[i][0].Y,'bo')
            ax.text(self.HistoricShorelinesPositions[i][0].X,self.HistoricShorelinesPositions[i][0].Y,str(self.HistoricShorelinesYears[i]))
        
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
        
        ax.plot(self.HistoricShorelinesYears,self.HistoricShorelinesDistances,'ko')
        
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
    
    def get_FutureDistance(self, Year):

        """

        Get the future cposition of the coast in distance along transect
        from Bruun Rule predictions

        MDH, November 2020

        """

        # check there are predictions for this transect
        if self.Future:

            # find year index
            Index = [i for i, x in enumerate(self.FutureSeaLevelYears) if x == Year]
            
            if len(Index) == 0:
                print("ERROR: Transect.get_FutureDistance - length of Index == 0")
                sys.exit()
                return

            # use to access future position
            try:
                self.FutureShorelinesDistances[Index[0]]
            except:
                import pdb
                pdb.set_trace()

            return self.FutureShorelinesDistances[Index[0]]
           
        else:
            return

    def get_FuturePositionChange(self, Year1, Year2):

        """

        Get the future change in  position of the coast over a particular number of years
        from Bruun Rule predictions

        MDH, October 2019

        """

        # check there are predictions for this transect
        if self.Future:
            
            # Check and if required, change the type of Year1 to datetime
            if isinstance(Year1, datetime):
                pass  # Do nothing if Year1 is already a datetime
            elif isinstance(Year1, int):  # If it's an integer year, convert to datetime
                Year1 = datetime(Year1, 1, 1)
            else:
                raise ValueError(f"Unsupported type: {type(Year1)}. Expected datetime or int.")
            
            # Check and if required, change the type of Year2 to datetime
            if isinstance(Year2, datetime):
                pass  # Do nothing if Year2 is already a datetime
            elif isinstance(Year2, int):  # If it's an integer year, convert to datetime
                Year2 = datetime(Year2, 1, 1)
            else:
                raise ValueError(f"Unsupported type: {type(Year2)}. Expected datetime or int.")
            
            # add a check in here if Year1 <= Latest Shoreline
            if Year1 <= self.HistoricShorelinesYears[-1]:
                Distance1 = self.HistoricShorelinesDistances[-1][0]

            else:
                # find year index
                Index1 = [i for i, x in enumerate(self.FutureSeaLevelYears) if x == Year1]
                if len(Index1) == 0:
                    print("ERROR: Transect.get_FuturePositionChange - length of Index1 == 0 - Year=" + str(Year1))
                    import pdb
                    pdb.set_trace()
                    
                Distance1 = self.FutureShorelinesDistances[Index1[0]]
            
            # find year index for second year
            Index2 = [i for i, x in enumerate(self.FutureSeaLevelYears) if x == Year2]
            
            if len(Index2) == 0:
                print("ERROR: Transect.get_FuturePositionChange - length of Index2 == 0 - Year=" + str(Year2))
                sys.exit()

            # add a check in here if Year1 < Latest Shoreline
            Distance2 = self.FutureShorelinesDistances[Index2[0]]
            
            return Distance1-Distance2

        else:
            return
        
    def get_ExtrapDistance(self, Year):

        """

        Get the extrapolated future position of the coast by extrapolating
        historical rate of shoreline change

        MDH, October 2020

        """

        # check there are predictions for this transect
        if self.Future:

            # extrapolate future position on transect
            extrapPeriodYrs = (datetime(Year,1,1) - self.HistoricShorelinesYears[-1]).days / 365.2425
            Distance = self.ChangeRates[-1]*extrapPeriodYrs
            return Distance

        else:
            return
    
    def get_FutureRate(self, Year1, Year2):

        """

        Get the future erosion rate of the coast for a particular period of years
        from Bruun Rule predictions. Rates are negative for erosion, positive
        for accretion

        MDH, January 2020

        """

        # check there are predictions for this transect
        if self.Future:
            
            # Check and if required, change the type of Year1 to datetime
            if isinstance(Year1, datetime):
                pass  # Do nothing if Year1 is already a datetime
            elif isinstance(Year1, int):  # If it's an integer year, convert to datetime
                Year1 = datetime(Year1, 1, 1)
            else:
                raise ValueError(f"Unsupported type: {type(Year1)}. Expected datetime or int.")
            
            # Check and if required, change the type of Year2 to datetime
            if isinstance(Year2, datetime):
                pass  # Do nothing if Year2 is already a datetime
            elif isinstance(Year2, int):  # If it's an integer year, convert to datetime
                Year2 = datetime(Year2, 1, 1)
            else:
                raise ValueError(f"Unsupported type: {type(Year2)}. Expected datetime or int.")
            
            # check year1 isnt less than an historic shoreline
            if Year1 < self.HistoricShorelinesYears[-1]:
                Year1 = self.HistoricShorelinesYears[-1]

            # get the position change
            Distance = self.get_FuturePositionChange(Year1, Year2)

            # calculate average rate
            YrDiff = (Year2-Year1).days / 365.2425
            Rate = Distance/YrDiff
            return Rate

        else:
            return

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
            self.OSYear = self.HistoricShorelinesYears[Index[0]]
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

    def get_RecentPosition(self):

        """

        Get the most recent position of the coast 
        
        MDH, January 2020

        """

        # catch if no shoreline
        if len(self.HistoricShorelinesYears) == 0:
            return
            #raise Exception("self.get_RecentPosition: No recent position")

        # find index of most recent historical shoreline
        Index = np.argmax(self.HistoricShorelinesYears)
        Position = self.HistoricShorelinesPositions[Index][0]
        Year = self.HistoricShorelinesYears[Index]
            
        return Position
    
    def get_RecentYear(self):

        """
        
        Get the year of the most recent position of the coast
        
        MDH, March 2021
        
        """

        # catch if no shoreline
        if len(self.HistoricShorelinesYears) == 0:
            return
            #raise Exception("self.get_RecentPosition: No recent position")

        # find index of most recent historical shoreline
        Index = np.argmax(self.HistoricShorelinesYears)
        Year = self.HistoricShorelinesYears[Index]
            
        return Year

    def get_RecentDistance(self):

        """

        Get the most recent position of the coast 

        MDH, November 2020

        """

        # catch if no shoreline
        if len(self.HistoricShorelinesYears) == 0:
            raise Exception("self.get_RecentPosition: No recent position")

        # find index of most recent historical shoreline
        Index = np.argmax(self.HistoricShorelinesYears)
        
        return self.HistoricShorelinesDistances[Index][0]

    def get_OldestPosition(self):

        """

        Get the most oldest position of the coast 

        MDH, January 2020

        """

        # find index of most recent historical shoreline
        Index = np.argmin(self.HistoricShorelinesYears)
        Position = self.HistoricShorelinesPositions[Index][0]
        return Position 
    
    

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


    
    
    
    