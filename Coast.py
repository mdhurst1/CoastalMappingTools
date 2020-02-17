"""
Coast object for analysing coastal morphology and predicting future coastal change

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import os, sys, time, pickle
from pathlib import Path
import numpy as np
from scipy.interpolate import splprep, splev
import numpy.ma as ma
from sklearn.cluster import KMeans

import shapefile
import itertools
import rasterio
import geopandas as gp
from shapely.geometry import Point, LineString, MultiLineString, MultiPoint
from shapely.ops import nearest_points, linemerge

from Line import *
from IPython.display import clear_output

# might do some multiprocessing?
from multiprocessing import Pool

class Coast:
    """
    Description of object goes here

    """

    def __init__(self, CoastShp=""):
        """
        MDH, June 2019
        """

        print("Coast: Initialising Coast object")

        self.Cell = None
        self.SubCell = None
        self.CMU = None
        self.CoastShp = CoastShp
        self.NoCoastLines = 0
        self.CoastLines = []
        self.Contours = []
        self.CliffTopLines = []
        self.CliffToeLines = []
        self.BarrierFrontTopLines = []
        self.BarrierFrontToeLines = []
        self.BarrierBackTopLines = []
        self.BarrierBackToeLines = []
        self.CrestLines = []
        self.ExtFrontLines_Low = []
        self.ExtFrontLines_Med = []
        self.ExtFrontLines_High = []
        self.ExtBackLines_Low = []
        self.ExtBackLines_Med = []
        self.ExtBackLines_High = []
        self.FutureShoreLinesYears = []
        self.FutureShoreLines = []
        self.WriteFutureLines = []
        self.WriteRecentLines = []
        self.Projection = ""
        self.OverallOrientation = 0.
        self.TransectsSpacing = 10.
        self.NodeSpacing = 10.
        self.TransectsLength2Sea = 200.
        self.TransectsLength2Land = 1000.
        self.ExtremeWaterLevels = []
        self.MHWS = None

        if CoastShp:
            self.ReadCoastShp(CoastShp)
            
        else:
            print("Coast: Generating empty coast object")

    def __str__(self):
        String = "Coast Object:\n\tFile: %s\n\tNumber of Coastlines:%d\n\t" % (str(self.CoastShp), self.NoCoastLines)
        return String

    # a function to save to a pickle file
    def Save(self, PickleFile):

        """
        """
        print("Coast.Save: Saving Coast Object")
        with open(PickleFile, 'wb') as PFile:
            pickle.dump(self, PFile)

    # read coast from a shapefile
    def ReadCoastShp(self,CoastShp, MinLength=200.):
        
        """
        """

        # Open coast polyline file for reading
        SF = shapefile.Reader(CoastShp)
        Shapes = SF.shapes()
        
        # I HAVE DELETED THE RECORDING OF SHAPES AND RECORDS INTO THE OBJECT DUE TO COMPATIBILITY ISSUES
        # WITH PICKLING THAT I CANT UNDERSTAND!!!!

        # Get number of coast segments to work on
        self.NoCoastLines = len(Shapes)
        print("Coast.ReadCoastShp: Read Coastline, no of coast segments is", self.NoCoastLines)
    
        # Generate coast nodes for each segment
        for i in range(0,self.NoCoastLines):
            
            print(" \r\tCoastline %4d / %4d" % (i+1, self.NoCoastLines), end="")

            # get X and Y coordinates of segment
            X, Y = np.array(Shapes[i].points).T
            
            # Set up a line object for each
            ThisLine = Line(str(i), X, Y)

            # append to list of coast lines
            if ThisLine.TotalLength > MinLength:
                self.CoastLines.append(ThisLine)

        # get new number of coastal segments based on the list built
        self.NoCoastLines = len(self.CoastLines)

        print("")    

        # get projection strings
        f = open(CoastShp.rstrip("shp")+"prj")
        self.Projection = f.read()
        f.close()

 
    def WriteCoastShp(self, CoastShp):
        
        """
        Writes the contents of a list of coast line objects to polyline shape file

        MDH, June 2019

        """
        # print action to screen
        print("Coast.WriteCoastShp: Writing coast line to a shapefile")

        self.WriteLinesShp("CoastLines", CoastShp)

    def WriteCliffShp(self, CliffShp):
        
        """
        Writes the contents of a list of cliff line objects to polyline shape file

        MDH, June 2019

        """
        
        # print action to screen
        print("Coast.WriteCliffShp: Writing cliffs to shapefiles")

        if len(self.CliffTopLines) == 0:
            self.GetCliffLines()

        CliffTopShp = CliffShp.split(".")[0]+"_Top.shp"
        CliffToeShp = CliffShp.split(".")[0]+"_Toe.shp"
        self.WriteLinesShp("CliffTopLines", CliffTopShp)
        self.WriteLinesShp("CliffToeLines", CliffToeShp)
        self.WritePatchesShp("CliffTopLines", "CliffToeLines", CliffShp)

    def WriteBarrierShp(self, BarrierShp):

        """
        Writes the contents of a list of barrier line objects to polyline shape file

        MDH, June 2019

        """

        # print action to screen
        print("Coast.WriteBarrierShp: Writing barrier line objects to polyline a shapefile")

        if len(self.BarrierFrontTopLines) == 0:
            self.GetBarrierLines()

        # set up individual file names
        BarrierFrontTopShp = BarrierShp.split(".")[0]+"_Front_Top.shp"
        BarrierFrontToeShp = BarrierShp.split(".")[0]+"_Front_Toe.shp"
        BarrierBackTopShp = BarrierShp.split(".")[0]+"_Back_Top.shp"
        BarrierBackToeShp = BarrierShp.split(".")[0]+"_Back_Toe.shp"
        BarrierTopPatchesShp = BarrierShp.split(".")[0]+"_Top.shp"
        BarrierToePatchesShp = BarrierShp.split(".")[0]+"_Toe.shp"
                
        # launch polyline shapefile writer
        self.WriteLinesShp("BarrierFrontTopLines", BarrierFrontTopShp)
        self.WriteLinesShp("BarrierFrontToeLines", BarrierFrontToeShp)
        self.WriteLinesShp("BarrierBackTopLines", BarrierBackTopShp)
        self.WriteLinesShp("BarrierBackToeLines", BarrierBackToeShp)

        # launch polygon patches shapefile writer
        self.WritePatchesShp("BarrierFrontTopLines", "BarrierBackTopLines", BarrierTopPatchesShp)
        self.WritePatchesShp("BarrierFrontToeLines", "BarrierBackToeLines", BarrierToePatchesShp)

    def WriteExtremeLevelsShp(self, ExtremeShp):

        """
        Writes the contents of a list of barrier line objects to polyline shape file

        MDH, June 2019

        """

        if len(self.ExtFrontLines_Low) == 0:
            self.GetExtremeLines()

        # print action to screen
        print("Coast.WriteExtremeLevelsShp: Writing extreme water line objects to polyline and polygon shapefile")

        # loop through extreme water levels
        for i, Level in enumerate(["Low", "Med","High"]):

            # set up individual file names
            ExtFrontShp = ExtremeShp.split(".")[0]+"_"+Level+"_Front.shp"
            ExtBackShp = ExtremeShp.split(".")[0]+"_"+Level+"_Back.shp"
            ExtPatchesShp = ExtremeShp.split(".")[0]+"_"+Level+".shp"
                
            # launch polyline shapefile writer
            self.WriteLinesShp("ExtFrontLines_"+Level, ExtFrontShp)
            self.WriteLinesShp("ExtBackLines_"+Level, ExtBackShp)
            
            # launch polygon patches shapefile writer
            self.WritePatchesShp("ExtFrontLines_"+Level, "ExtBackLines_"+Level, ExtPatchesShp)
    
    def WriteErodedAreaShp(self, ErosionShp, Year):
        
        """
        Writes future shorelines to polygon patches

        MDH, Jan 2020

        """
        
        # print action to screen
        print("Coast.WriteErodedAreaShp: Writing predicted erosion area to polygon file")

        # get lists of lines for year of prediction and most recent shoreline position
        self.WriteFutureLines = self.FutureShorelines[self.FutureShorelines.Year == Year]
        self.WriteRecentLines = self.FutureShorelines[self.FutureShorelines.Year == 2020]
        
        # set up files to write
        ErosionFrontShp = ErosionShp.split(".")[0]+"_2020.shp"
        ErosionBackShp = CliffShp.split(".")[0]+"_"+str(Year)+".shp"

        # write lines then patches
        self.WriteLinesShp("WriteFutureLines", ErosionBackShp)
        self.WriteLinesShp("WriteRecentLines", ErosionFrontShp)
        self.WritePatchesShp("WriteFutureLines", "WriteRecentLines", ErosionShp)

    def WriteFutureShorelinesShp(self, FutureShoreLinesShp, Smooth=True):

        """
        Writes the contents of a list of future shoreline objects to polyline shape file

        MDH, June 2019

        Added functionality to write spline of future line prediction to get smoothed
        shape that is faithful to predictions

        MDH, Jan 2020

        """

        # extract future shoreline positions from transect
        self.GetFutureShoreLines()

        # print action to screen
        print("Coast.WriteFutureShorelinesShp: Writing future MHWS line objects to polyline shapefiles")

        # open new shapefile        
        WL = shapefile.Writer(FutureShoreLinesShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 20, 0],['Year','N', 4, 0]]
        WL.fields = self.Fields[1:] 

        for Line in self.FutureShoreLines:
            
            # get line node positions
            X, Y = Line.get_XY()

            if Smooth and len(X) > 5:

                XSmooth = X[1:-1]
                YSmooth = Y[1:-1]
                # calculate distance
                Dist = np.zeros(XSmooth.shape)
                Dist[1:] = np.sqrt((XSmooth[1:] - XSmooth[:-1])**2 + (YSmooth[1:] - YSmooth[:-1])**2)
                Dist = np.cumsum(Dist)
                
                # build a spline representation of the line
                Spline, u = splprep([XSmooth, YSmooth], u=Dist, s=0)

                # resample it at smaller distance intervals
                Interp_Dist = np.arange(0, Dist[-1], 1.)
                XSmooth, YSmooth = splev(Interp_Dist, Spline)

                XSmooth = np.insert(XSmooth,0,X[0])
                YSmooth = np.insert(YSmooth,0,Y[0])
                X = np.append(XSmooth,X[-1])
                Y = np.append(YSmooth,Y[-1])
            
            # convert to list for writing to shapefile
            WriteLine = [np.column_stack([X,Y]).tolist()]
            
            # generate record
            Record = [str(Line.ID),str(Line.Year)]

            # write line and record
            WL.line(WriteLine)
            WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(FutureShoreLinesShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteFutureShorelineSegmentsShp(self, FutureShoreLinesShp):

        """
        Writes the contents of a list of future shoreline objects to polyline shape file
        organised into individual segments with attributes

        PLAN FOR DOING THIS ON A SPLINE
        loop through future shoreline lines and get the spline
        loop through transects and intersect with historic shoreline position and then get nearerst nodes from spline??

        MDH, January 2020

        """

        # print action to screen
        print("Coast.WriteFutureShorelineSegmentsShp: Writing future MHWS line objects to polyline shapefiles")
        
        
        self.GetFutureShoreLines()
        
        # open new shapefile        
        WL = shapefile.Writer(FutureShoreLinesShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C', 1, 0), ['Line_ID', 'C', 3, 0], ['Transect_ID','C', 5, 0],
                        ['Cell','C', 2, 0], ['SubCell','C', 2, 0], ['CMU','C', 3, 0],
                        ['Year','N', 4, 0], ['Distance','N', 6, 2], ['Rate','N', 4, 4]]
        WL.fields = self.Fields[1:] 

        # Loop through prediction years
        for i, Line in enumerate(self.FutureShoreLines):
            
            # keep track of no of coastal segments for IDs
            FutureCount = 0
            
            # get line node positions
            X, Y = Line.get_XY()
            
            # get nodes for spline
            Interp_X = X[1:-1]
            Interp_Y = Y[1:-1]

            # calculate distance
            Dist = np.zeros(Interp_X.shape)
            Dist[1:] = np.sqrt((Interp_X[1:] - Interp_X[:-1])**2 + (Interp_Y[1:] - Interp_Y[:-1])**2)
            Dist = np.cumsum(Dist)
            
            # build a spline representation of the line
            K = 3 # by default

            if len(Interp_X) < 2:
                continue

            elif len(Interp_X) < 4:
                K = len(Interp_X)-1

            Spline, u = splprep([Interp_X, Interp_Y], u=Dist, s=0, k=K)

            # resample it at smaller distance intervals
            Interp_Dist = np.arange(0, Dist[-1], 1.)
            Interp_X, Interp_Y = splev(Interp_Dist, Spline)

            # add start and end nodes back on
            Interp_X = np.insert(Interp_X, 0, (X[0]+X[1])/2.)
            Interp_Y = np.insert(Interp_Y, 0, (Y[0]+Y[1])/2.)
            Interp_X = np.append(Interp_X, (X[-1]+X[-2])/2.)
            Interp_Y = np.append(Interp_Y, (Y[-1]+Y[-2])/2.)
            
            # convert to a linestring
            SplineLine = LineString((tuple(zip(Interp_X,Interp_Y))))
            SplinePoints = MultiPoint((tuple(zip(Interp_X,Interp_Y))))
            
            # loop through transects and get contiguous future prediction lines
            for CoastLine in self.CoastLines:
                
                # set up empty list of intersection indices with spline
                TransectsList = []
                IntersectionIndices = []

                # get a list of nearest indices on interpolated lines
                for j, Transect in enumerate(CoastLine.Transects):
                    
                    # intersect extended transect with spline to find index
                    X1 = Transect.EndNode.X + 1000 * np.sin( np.radians( Transect.Orientation ) )
                    Y1 = Transect.EndNode.Y + 1000 * np.cos( np.radians( Transect.Orientation ) )
                    
                    TransectLine = LineString(((Transect.StartNode.X,Transect.StartNode.Y),(X1,Y1)))
                    Intersection = TransectLine.intersection(SplineLine)

                    # catch no intersections and flag for deletion?
                    if Intersection.geom_type == "GeometryCollection":
                        continue

                    # check there arent multiple intersections, if there are just get the nearest
                    elif Intersection.geom_type == "MultiPoint":
                        Intersection = Intersection[0]

                    Distances = [SplinePoint.distance(Intersection) for SplinePoint in SplinePoints]
                    TransectsList.append(j)
                    IntersectionIndices.append(Distances.index(min(Distances)))
                
                # loop across transects again
                for j in range(0, len(TransectsList)):
                    
                    if j == 0:
                        StartIndex = IntersectionIndices[j]
                    else:
                        StartIndex = EndIndex
                    
                    if j == len(TransectsList)-1:
                        EndIndex = IntersectionIndices[j]
                    else:
                        EndIndex = int((IntersectionIndices[j+1]+IntersectionIndices[j])/2)
                    
                    if StartIndex == EndIndex:
                        continue

                    # initiate dummy lists for nodes
                    X = Interp_X[StartIndex:EndIndex]
                    Y = Interp_Y[StartIndex:EndIndex]
                    
                    # get shoreline position in the future
                    Transect = CoastLine.Transects[TransectsList[j]]
                    FutureNode = Transect.get_FuturePosition(Line.Year)

                    # get line node positions
                    WriteLine = [np.column_stack([X,Y]).tolist()]
            
                    # calculate additional attributes
                    RecentNode = Transect.get_RecentPosition()
                    
                    if not FutureNode:
                        continue

                    if not FutureNode:
                        continue

                    Distance = np.sqrt((FutureNode.X-RecentNode.X)**2. + (FutureNode.Y-RecentNode.Y)**2.)
                    Rate = Transect.get_FutureShorelineRate(Line.Year)

                    # generate record (strs?)
                    Record = [str(CoastLine.ID), str(Transect.ID), str(Transect.Cell), str(Transect.SubCell),
                    str(Transect.CMU), str(Line.Year), str(Distance), str(Rate)]

                    # write line and record
                    WL.line(WriteLine)
                    WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########

        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file 
        f = open(FutureShoreLinesShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteErodedAreaShp(self, ErodedAreaShp, Year=2100):

        """
        Writes the contents of a list of future shoreline objects to a polygon showing area eroded

        MDH, January 2020

        """

        # print action to screen
        print("Coast.WriteFutureShorelineSegmentsShp: Writing future MHWS line objects to polyline shapefiles")

        # open new shapefile        
        WL = shapefile.Writer(ErodedAreaShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C', 1, 0), ['Line_ID', 'C', 3, 0],
                        ['Cell','N', 2, 0], ['SubCell','C', 2, 0]]
        WL.fields = self.Fields[1:] 

        # loop through transects and get contiguous future prediction lines
        for CoastLine in self.CoastLines:
            for i, Transect in enumerate(CoastLine.Transects):
                    
                    # check for prediction
                    if not Transect.Future:
                        continue
                    
                    # initiate dummy lists for nodes
                    X = []
                    Y = []
                    
                    # get shoreline position in the future
                    FutureNode = Transect.get_FuturePosition(Year)

                    # get previous and next nodes (either future or current)
                    # might need some logic for start and end nodes here
                    PreviousTransect = CoastLine.Transects[i-1]
                    NextTransect = CoastLine.Transects[i+1]
                    
                    if (i == 0):
                        PreviousNode = FutureNode
                    elif CoastLine.Transects[i-1].Future:
                        PreviousNode = CoastLine.Transects[i-1].get_FuturePosition(Year)
                    else:
                        PreviousNode = FutureNode
                    
                    if (i == len(CoastLine.Transects)-1):
                        NextNode = FutureNode
                    elif CoastLine.Transects[i+1].Future:
                        NextNode = CoastLine.Transects[i+1].get_FuturePosition(Year)
                    else:
                        NextNode = FutureNode

                    # build line segments from the three nodes
                    X.append((PreviousNode.X+FutureNode.X)/2.)
                    Y.append((PreviousNode.Y+FutureNode.Y)/2.)
                    X.append(FutureNode.X)
                    Y.append(FutureNode.Y)
                    X.append((NextNode.X+FutureNode.X)/2.)
                    Y.append((NextNode.Y+FutureNode.Y)/2.)
                    
                    self.Fields = [('DeletionFlag','C', 1, 0),['Line_ID', 'C', 20, 0],
                        ['Cell','N', 2, 0],['SubCell','C', 2, 0],['CMU','C', 3, 0],
                        ['Year','N', 4, 0],['EDist','N', 6, 2],['Rate','N', 4, 4]]

                    # get line node positions
                    WriteLine = [np.column_stack([X,Y]).tolist()]
            
                    # calculate additional attributes
                    RecentNode = Transect.get_RecentPosition()
                    Distance = np.sqrt((FutureNode.X-RecentNode.X)**2. + (FutureNode.Y-RecentNode.Y)**2.)
                    Rate = Transect.get_FutureShorelineRate(Year)

                    # generate record (strs?)
                    Record = [str(Line.ID), str(Transect.ID), str(Transect.Cell), str(Transect.SubCell),
                    str(Transect.CMU), str(Year), str(Distance), str(Rate)]

                    # write line and record
                    WL.line(WriteLine)
                    WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(ErodedAreaShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteLinesShp(self, DictionaryKey, CoastShp):
        
        """
        Writes the contents of a list of line objects to polyline shape file
        List of line objects is part of the Coast object and identified by 
        the dictionary key

        Need to add optional conditional statement?

        MDH, June 2019

        """

        # print action to screen
        print("Coast.WriteLinesShp: Writing a list of lines to a polyline shapefile")

        # open new shapefile        
        WL = shapefile.Writer(CoastShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0]]
        WL.fields = self.Fields[1:] 

        for Line in self.__dict__[DictionaryKey]:
            
            # get line node positions
            X, Y = Line.get_XY()
            WriteLine = [np.column_stack([X,Y]).tolist()]
            
            # generate record
            Record = [str(Line.ID)]

            # write line and record
            WL.line(WriteLine)
            WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(CoastShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()
    
    def WritePatchesShp(self, DictionaryKey1, DictionaryKey2, PatchShp):

        """

        Writes polygon patches between two lines to a polygon shapefile

        Dictionary Key refers

        MDH, June 2019

        """

        # print action to screen
        print("Coast.WritePathchesShp: Writing patch between two lines to a polygon shapefile")

        if len(self.__dict__[DictionaryKey1]) == 0:
            print("Coast.WritePatchesShp (Error): Trying to write from empty list of lines", DictionaryKey1, DictionaryKey2)

        # open new shapefile        
        WS = shapefile.Writer(PatchShp,shapeType=shapefile.POLYGON)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Poly_ID', 'C', 3, 0]]
        WS.fields = self.Fields[1:] 

        for Line1, Line2 in zip(self.__dict__[DictionaryKey1],self.__dict__[DictionaryKey2]):
            
            # get line node positions for cliff top and toe lines
            X1, Y1 = Line1.get_XY()
            X2, Y2 = Line2.get_XY()

            # combine, reversing the order of the second line to make a patch
            X = np.concatenate((X1,X2[::-1]))
            Y = np.concatenate((Y1,Y2[::-1]))
            WritePoly = [np.column_stack([X,Y]).tolist()]
            
            # generate record
            Record = [str(Line1.ID)]

            # write line and record
            WS.poly(WritePoly)
            WS.record(*Record) 
        
        # close the shapefiles and clean up
        WS.close()
            
        # create the projection file    
        f = open(PatchShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WritePointsShp(self, PointsShp):
        """
        Function to write transect points to a point shape file

        MDH, June 2019
        
        """

        # print action to screen
        print("Coast.WritePointsShp: Writing points to a shapefile")

        WP = shapefile.Writer(PointsShp, shapeType=shapefile.POINT)
        
        # Create Fields
        Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0],['Transect_ID', 'C', 5, 0]] #['Segment_ID','C', 3, 0], might add 
        WP.fields = Fields[1:]

        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # Create the record
                Record = [str(Line.ID), str(Transect.ID)]

                # add the line and record
                WP.point(Transect.CoastNode.X, Transect.CoastNode.Y)
                WP.record(*Record)

        # close the shapefiles and clean up
        WP.close()
            
        # create the projection file    
        f = open(PointsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteTransectsShp(self, TransectsShp):

        """
        Writes the transects of a Coast object to polyline shape file

        builds a large attribute table with all transect properties

        MDH, June 2019

        """

        # print action to screen
        print("Coast.WriteTransectShp: Writing coastal transects and attributes to a shapefile")

        # open new shapefile        
        WL = shapefile.Writer(TransectsShp,shapeType=shapefile.POLYLINE)
        
        # Check length of extreme water levels
        if len(self.ExtremeWaterLevels) != 3:
            print("Coast.WriteTransectsShp (Error): No extreme water levels info to write to attributes")
            self.ExtremeWaterLevels = [[],[],[]]

        # Create Fields
        Fields = [('DeletionFlag','C',1,0), ['LineID', 'C', 3, 0], ['TransectID', 'C', 5, 0], 
        ['Cliff_H','N', 5, 2],['Cliff_S','N', 5, 2],
        ['Rocky','N', 2, 1], 
        ['Bar_FH','N', 5, 2], ['Bar_FS','N', 5, 2],
        ['Bar_BH','N', 5, 2], ['Bar_BS','N', 5, 2],
        ['Bar_ToeW','N', 6, 2], ['Bar_TopW','N', 6, 2],
        ['Bar_Volume','N', 7, 2], ['Crest_Elev','N', 5, 2], 
        ['ST_W_low','N', 6, 2], ['ST_V_low','N', 7, 2],
        ['ST_W_med','N', 6, 2], ['ST_V_med','N', 7, 2],
        ['ST_W_high','N', 6, 2], ['ST_V_high','N', 7, 2],
        ['LT_W_low','N', 6, 2], ['LT_V_low','N', 7, 2],
        ['LT_W_med','N', 6, 2], ['LT_V_med','N', 7, 2],
        ['LT_W_high','N', 6, 2], ['LT_V_high','N', 7, 2]]
        
        WL.fields = Fields[1:]

        
        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # get transect node positions
                X, Y = Transect.get_XY()
                
                WriteTransect = [np.column_stack([X,Y]).tolist()]

                # Create the record this could become a function in transect object...
                Record = [str(Line.ID), str(Transect.ID), Transect.CliffHeight, Transect.CliffSlope, 
                            Transect.Rocky,
                            Transect.FrontHeight, Transect.FrontSlope, 
                            Transect.BackHeight, Transect.BackSlope,
                            Transect.ToeWidth, Transect.TopWidth,
                            Transect.BarrierVolume, Transect.CrestElevation,
                            Transect.ExtremeWidths[0], Transect.ExtremeVolumes[0],
                            Transect.ExtremeWidths[1], Transect.ExtremeVolumes[1],
                            Transect.ExtremeWidths[2], Transect.ExtremeVolumes[2],
                            Transect.ExtremeTotalWidths[0], Transect.ExtremeTotalVolumes[0],
                            Transect.ExtremeTotalWidths[1], Transect.ExtremeTotalVolumes[1],
                            Transect.ExtremeTotalWidths[2], Transect.ExtremeTotalVolumes[2]]

                # write transect and record
                WL.line(WriteTransect)
                try:
                    WL.record(*Record) 
                except:
                    print(Transect.ID)
                    print(Record)
                    #print(Transect.ExtremeWidths)
                    sys.exit()
                
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(TransectsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()
    
    def WriteCrestLinesShp(self, CrestLineShp):

        """
        Writes the crest line of barriers to shape file

        MDH, July 2019

        """

        print("Coast.WriteCrestLinesShp: Writing barrier crest locations to polyline shapefile")
        
        if len(self.CrestLines) == 0:
            self.GetBarrierLines()

        # launch polyline shapefile writer
        self.WriteLinesShp("CrestLines", CrestLineShp)

    def WriteCrestPointsShp(self, CrestPointsShp):

        """
        Writes the crest lines points of barriers to shape file

        builds a large attribute table with all transect properties

        MDH, July 2019

        """

        print("Coast.WriteCrestPointsShp: Writing barrier crest locations to point shapefile")

        # open new shapefile        
        WP = shapefile.Writer(CrestPointsShp,shapeType=shapefile.POINTZ)
        
        # Check length of extreme water levels
        if len(self.ExtremeWaterLevels) != 3:
            print("Coast.WriteTransectsShp (Error): No extreme water levels info to write to attributes")
            self.ExtremeWaterLevels = [[],[],[]]

        # Create Fields
        Fields = [('DeletionFlag','C',1,0), ['LineID', 'C', 3, 0], ['TransectID', 'C', 5, 0], 
        ['Cliff_H','N', 5, 2],['Cliff_S','N', 5, 2],
        ['Rocky','N', 2, 1], 
        ['Bar_FH','N', 5, 2], ['Bar_FS','N', 5, 2],
        ['Bar_BH','N', 5, 2], ['Bar_BS','N', 5, 2],
        ['Bar_ToeW','N', 6, 2], ['Bar_TopW','N', 6, 2],
        ['Bar_Volume','N', 7, 2], ['Crest_Elev','N', 5, 2], 
        ['ST_W_low','N', 6, 2], ['ST_V_low','N', 7, 2],
        ['ST_W_med','N', 6, 2], ['ST_V_med','N', 7, 2],
        ['ST_W_high','N', 6, 2], ['ST_V_high','N', 7, 2],
        ['LT_W_low','N', 6, 2], ['LT_V_low','N', 7, 2],
        ['LT_W_med','N', 6, 2], ['LT_V_med','N', 7, 2],
        ['LT_W_high','N', 6, 2], ['LT_V_high','N', 7, 2]]

        WP.fields = Fields[1:]

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # get crest position
                try:
                    X, Y, Z = Transect.get_CrestPosition()
                except:
                    continue
                
                # Create the record
                Record = [str(Line.ID), str(Transect.ID), Transect.CliffHeight, Transect.CliffSlope, 
                            Transect.Rocky,
                            Transect.FrontHeight, Transect.FrontSlope, 
                            Transect.BackHeight, Transect.BackSlope,
                            Transect.ToeWidth, Transect.TopWidth,
                            Transect.BarrierVolume, Transect.CrestElevation,
                            Transect.ExtremeWidths[0], Transect.ExtremeVolumes[0],
                            Transect.ExtremeWidths[1], Transect.ExtremeVolumes[1],
                            Transect.ExtremeWidths[2], Transect.ExtremeVolumes[2],
                            Transect.ExtremeTotalWidths[0], Transect.ExtremeTotalVolumes[0],
                            Transect.ExtremeTotalWidths[1], Transect.ExtremeTotalVolumes[1],
                            Transect.ExtremeTotalWidths[2], Transect.ExtremeTotalVolumes[2]]


                # write transect and record
                WP.pointz(X, Y, Z)
                WP.record(*Record) 
        
        # close the shapefiles and clean up
        WP.close()
            
        # create the projection file    
        f = open(CrestPointsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()
  
    def WriteFrontPointsShp(self, FrontPointsShp):

        """
        Writes the front lines points of barriers to shape file

        builds a large attribute table with all transect properties

        MDH, July 2019

        """

        print("Coast.WriteFrontPointsShp: Writing barrier front locations to point shapefile")

        # open new shapefile        
        WP = shapefile.Writer(FrontPointsShp,shapeType=shapefile.POINTZ)
        
        # Check length of extreme water levels
        if len(self.ExtremeWaterLevels) != 3:
            print("Coast.WriteTransectsShp (Error): No extreme water levels info to write to attributes")
            self.ExtremeWaterLevels = [[],[],[]]

        # Create Fields
        Fields = [('DeletionFlag','C',1,0), ['LineID', 'C', 3, 0], ['TransectID', 'C', 5, 0], 
        ['Cliff_H','N', 5, 2],['Cliff_S','N', 5, 2],
        ['Rocky','N', 2, 1], 
        ['Bar_FH','N', 5, 2], ['Bar_FS','N', 5, 2],
        ['Bar_BH','N', 5, 2], ['Bar_BS','N', 5, 2],
        ['Bar_ToeW','N', 6, 2], ['Bar_TopW','N', 6, 2],
        ['Bar_Volume','N', 7, 2], ['Crest_Elev','N', 5, 2], 
        ['ST_W_low','N', 6, 2], ['ST_V_low','N', 7, 2],
        ['ST_W_med','N', 6, 2], ['ST_V_med','N', 7, 2],
        ['ST_W_high','N', 6, 2], ['ST_V_high','N', 7, 2],
        ['LT_W_low','N', 6, 2], ['LT_V_low','N', 7, 2],
        ['LT_W_med','N', 6, 2], ['LT_V_med','N', 7, 2],
        ['LT_W_high','N', 6, 2], ['LT_V_high','N', 7, 2]]

        WP.fields = Fields[1:]

        for Line in self.CoastLines:
            for Transect in Line.Transects:


                # get crest position
                try:
                    X, Y, Z = Transect.get_FrontPosition()
                except:
                    continue
                
                # Create the record
                Record = [str(Line.ID), str(Transect.ID), Transect.CliffHeight, Transect.CliffSlope, 
                            Transect.Rocky,
                            Transect.FrontHeight, Transect.FrontSlope, 
                            Transect.BackHeight, Transect.BackSlope,
                            Transect.ToeWidth, Transect.TopWidth,
                            Transect.BarrierVolume, Transect.CrestElevation,
                            Transect.ExtremeWidths[0], Transect.ExtremeVolumes[0],
                            Transect.ExtremeWidths[1], Transect.ExtremeVolumes[1],
                            Transect.ExtremeWidths[2], Transect.ExtremeVolumes[2],
                            Transect.ExtremeTotalWidths[0], Transect.ExtremeTotalVolumes[0],
                            Transect.ExtremeTotalWidths[1], Transect.ExtremeTotalVolumes[1],
                            Transect.ExtremeTotalWidths[2], Transect.ExtremeTotalVolumes[2]]

                # write transect and record
                WP.pointz(X, Y, Z)
                WP.record(*Record) 
        
        # close the shapefiles and clean up
        WP.close()
            
        # create the projection file    
        f = open(FrontPointsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteTransectsCSV(self,Folder=os.getcwd()):

        """

        Writes all transects to csv files in the folder specified or
        by default in the current working directory

        args: Folder in which to put files

        MDH, July 2019

        """
        
        print("Coast.WriteTransectsCSV: Writing all topographic transects to csv files")
        
        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])
        CurrentTransect = 0

        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # print progress to screen
                print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")

                # write transect    
                Transect.Write(Folder)

                # update counter
                CurrentTransect += 1

        print("")

    def MergeReverseCoastLines(self):

        """
        Identifies individual coast Lines that are touching at one end 
        and combines them into a single Line

        Reversal of line directions might cause bugs, works so far

        MDH, June 2019
        """

        print("Coast.MergeCoastLines: Merging coastlines")

        # set up Flag for lines being flipped
        FlagReverse = 1

        Pass = 0

        while FlagReverse:

            # print progress to screen
            print(" \r\tPass %3d" % (Pass))
            Pass += 1

            # Update Flag
            FlagReverse = 0

            # Empty lists to populate with new shapes and records
            NewCoastLines = []
            
            # create list of joins
            JoinsList = np.zeros(self.NoCoastLines,dtype=int)-9999
            JoinedByList = np.zeros(self.NoCoastLines,dtype=int)-9999
            ReversedList = []
            
            # get start and end nodes from line sections
            StartNodes = [CoastLine.Nodes[0] for CoastLine in self.CoastLines]
            EndNodes = [CoastLine.Nodes[-1] for CoastLine in self.CoastLines]
            
            # compare start nodes and end nodes to populate join list
            # this could probably be done better!
            for i, StartNode in enumerate(StartNodes):
                for j, EndNode in enumerate(EndNodes):
                    if i == j:
                        continue
                    elif StartNode == EndNode:
                        JoinsList[j] = i
                        JoinedByList[i] = j

                # check for line direction reversals
                for k, TestNode in enumerate(StartNodes):
                    if i == k:
                        continue
                    elif StartNode == TestNode:
                        if not i in ReversedList:
                            ReversedList.append(k)
                            FlagReverse = 1
            
            # get list of line sections to start at
            StartList = np.where(JoinedByList < 0)[0]
            
            for i, StartLine in enumerate(StartList):
                
                # print progress to screen
                print(" \r\tLine %4d / %4d" % (i, len(StartList)), end="")
                
                # get vector of line section
                X1, Y1 = self.CoastLines[StartLine].get_XY()
                
                # get first line section to join
                JoinLine = JoinsList[StartLine]

                while JoinLine > -1:
                    
                    # get next line
                    X2, Y2 = self.CoastLines[JoinLine].get_XY()

                    # join the lines
                    X1 = np.concatenate((X1,X2[1:]))
                    Y1 = np.concatenate((Y1,Y2[1:]))

                    # get next n
                    JoinLine = JoinsList[JoinLine]

                # reverse any vectors needing reversing
                if StartLine in ReversedList:
                    X1 = X1[::-1]
                    Y1 = Y1[::-1]

                # write new line, and update shape and records lists
                NewCoastLines.append(Line(self.CoastLines[StartLine].ID, X1, Y1))

            # update object properties with merged geometries
            self.CoastLines = NewCoastLines
            
            # update number of shapes
            self.NoCoastLines = len(self.CoastLines)
        
        print("\r\t Done.")

    def MergeCoastLines(self, SnapDistance=5):

        """
        Identifies individual coast Lines that are touching at one end 
        and combines them into a single Line using shapely

        Distance to snap end points in m

        MDH, Feb, 2020
        """

        print("Coast.MergeCoastLines: Merging coastlines...")

        # get start and end nodes from line sections
        StartNodes = [CoastLine.Nodes[0] for CoastLine in self.CoastLines]
        EndNodes = [CoastLine.Nodes[-1] for CoastLine in self.CoastLines]

        # first check if any start nodes are the same within tolerance
        Distances = np.ones(len(StartNodes))*-9999.
        for i, StartNode in enumerate(StartNodes):
            for ii, StartNode2 in enumerate(StartNodes):
                if i == ii:
                    continue
                Distance = StartNode.get_Distance(StartNode2)
                if Distance < SnapDistance:
                    print("Snapping")
                    self.CoastLines[ii].Nodes[0] = StartNode

        # now check if any end nodes are the same within tolerance
        for i, StartNode in enumerate(StartNodes):
            for j, EndNode in enumerate(EndNodes):
                if i == j:
                    continue
                Distance = StartNode.get_Distance(EndNode)
                if Distance < SnapDistance:
                    print("Snapping")
                    self.CoastLines[j].Nodes[-1] = StartNode

        # create a list of linestrings to merge
        #LineString((tuple(zip(Interp_X,Interp_Y))))
        LinesList = []
        for TempLine in self.CoastLines:
            X,Y = TempLine.get_XY()
            LinesList.append(LineString((tuple(zip(X,Y)))))
        
        # LinesList = [LineString(tuple(zip(Line.get_XY()))) for Line in self.CoastLines]
        MultiLine = MultiLineString(LinesList)
        MergedLine = linemerge(MultiLine.simplify(0.2))

        #reset object
        self.CoastLines = []

        # add line or multiple lines depending on result of merge
        if MergedLine.geom_type == "LineString":
            
            # get x and y and add to CoastLine object as Line
            X, Y = MergedLine.xy
            self.CoastLines.append(Line("0", X, Y))
            
        elif MergedLine.geom_type == "MultiLineString":
            
            # loop through lines in MultiLineString
            for i, TempLine in enumerate(MergedLine):
                
                # get x and y and add to CoastLine object as Line
                X, Y = TempLine.xy
                self.CoastLines.append(Line(str(i), X, Y))

        else:
            print("Geometry not recognised!")
            sys.exit()
        
        # update no of coastlines
        self.NoCoastLines = len(self.CoastLines)

    def SmoothCoastLines(self, WindowSize=1001, NoSmooths=2, Resample=True, NodeSpacing=10., PolyOrder=4):
        
        """
        Smooths the CoastLines contained in Coast object
        Wrapper to the function in the Line object
        Calls scipy.signal.savgol_filter

        Savitzky and Golay (1964) smoothing filter
    
        Savitzky, A. and Golay, M. J.: Smoothing and differentiation of data
        by simplified least squares procedures, Anal. Chem., 36, 1627-
        1639, 1964.

        https://docs.scipy.org/doc/scipy-0.15.1/reference/generated/scipy.signal.savgol_filter.html

        MDH, June 2019

        Parameters
        ----------
        WindowLength : int
            The length of the filter window (i.e. the number of coefficients). 
            WindowLength must be a positive odd integer.
        PolyOrder : int
            The order of the polynomial used to fit the samples. 
            PolyOrder must be less than window_length.
        NoSmooths : int
            Default is 1
        Resampling : bool
            Whether or not to resample the line to regular spaced nodes
            Default is True
        NodeSpacing : float
            Node spacing for resampleing
            Default is 10 m
        
        """

        print("Coast: Smoothing CoastLines")

        for i in range(0, NoSmooths):
            for Line in self.CoastLines:
            
                # smooth the line
                Line.SmoothLine(WindowSize, PolyOrder)

                if Resample:
                    Line.ResampleNodes(NodeSpacing)


    def ReverseCoastLines(self):
        """
        Function to reverse lines are ordered along the coast
        and line segments progress along the coast. The "along coast" direction
        is always that which results in the water being on the left as you look
        down the coastal vector.

        This might be buggy as anything and need lots more work. Should be run
        after MergeCoast and SmoothCoast but before Transects are built, though 
        if Transects have been built they will get rebuilt

        ***add argument to include shoreline shape then for each node
            find nearest on shoreline shape and calc orientation
            then use mean orientation to assess MDH, Feb 2020

        MDH, Feb 2020
        """

        for Line in self.CoastLines:
            Line.ReverseLine()

        # could add something here to do look up based on distance from starts to ends

    def ReconfigureCoastLines(self, Direction2OpenWater):
        """
        Function to arrange coastline so that lines are ordered along the coast
        and line segments progress along the coast. The "along coast" direction
        is always that which results in the water being on the left as you look
        down the coastal vector.

        This might be buggy as anything and need lots more work. Should be run
        after MergeCoast and SmoothCoast but before Transects are built, though 
        if Transects have been built they will get rebuilt

        ***add argument to include shoreline shape then for each node
            find nearest on shoreline shape and calc orientation
            then use mean orientation to assess MDH, Feb 2020

        MDH, June 2019

        Parameters
        ----------
        Direction2OpenWater: str
            Text-based description of the general direction to open water
            Cardinal direction
            e.g. "E", "east", "East"
        """

        # get start nodes and end nodes of each line
        StartNodes = []
        EndNodes = []

        for Line in self.CoastLines:

            # check line is oriented in the correct order
            StartNode = Line.Nodes[0]
            EndNode = Line.Nodes[-1]

            if str(Direction2OpenWater).lower()[0] == "e":
                
                # reverse the line and update start and end nodes if required
                if StartNode.Y < EndNode.Y:
                    Line.ReverseLine()
                    StartNode = Line.Nodes[0]
                    EndNode = Line.Nodes[-1]
                
            elif Direction2OpenWater.lower()[0] == "s":
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "This direction top open water [s] has not been implemented yet")
                sys.exit(ErrorString)

            elif Direction2OpenWater.lower()[0] == "w":
                if StartNode.Y > EndNode.Y:
                    Line.ReverseLine()
                    StartNode = Line.Nodes[0]
                    EndNode = Line.Nodes[-1]
                
            elif Direction2OpenWater.lower()[0] == "n":
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "This direction top open water [n] has not been implemented yet")
                sys.exit(ErrorString)

            else:
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "The string representing direction to open water not recognised; "
                    "\n\tshould be [e]ast, [s]outh, [w]est or [n]orth")
                sys.exit(ErrorString)

            StartNodes.append(Line.Nodes[0])
            EndNodes.append(Line.Nodes[-1])
        
        # check the lines are organised in the correct order
        if Direction2OpenWater.lower()[0] == "e":
            
            # sort the lines based on Y or their start node
            # needs to be an array to apply negative sign in order to get descending order
            DescendingIndices = np.argsort(-np.array([Node.Y for Node in StartNodes]))
            
            # here comes some bullshit to convert list to numpy array 
            # in order to sort and then turn back into a list :(
            self.CoastLines = list(np.array(self.CoastLines)[DescendingIndices])
            for i, Line in enumerate(self.CoastLines):
                Line.ID = str(i)

        if len(self.CoastLines[0].Transects) != 0:
            self.GenerateTransectsNormals(self.TransectsSpacing, self.TransectsLength2Sea, self.TransectsLength2Land)

        # calculate overall orientation
        StartNode = self.CoastLines[0].Nodes[0]
        EndNode = self.CoastLines[-1].Nodes[-1]

        #calculate the spatial change
        dx = EndNode.X - StartNode.X
        dy = EndNode.Y - StartNode.Y

        #Calculate the orientation of the line from ThisNode to NextNode
        if dx > 0 and dy > 0:
            self.OverallOrientation = np.degrees( np.arctan( dx / dy ) )
        elif dx > 0 and dy < 0:
            self.OverallOrientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy < 0:
            self.OverallOrientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy > 0:
            self.OverallOrientation = 360 + np.degrees( np.arctan( dx / dy ) )

    # function to do something    
    def GenerateTransectsNormals(self, TransectSpacing, TransectLength2Sea, TransectLength2Land, CheckTopology=True):
        """
        Wrapper to the function in the Line object

        Generates transects perpendicular to the coastline

        MDH, June 2019

        Parameters
        ----------
        TransectSpacing : float
            The distance between consecutive transects along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]
        TransectLength2Sea : float
            The length of the transect in the direction of sea in map units, 
            spatial units depend on units of the CoastLine read in, Should be [m]
        TransectLength2Land : float
            The length of the transect in the direction of land in map units, 
            spatial units depend on units of the CoastLine read in, Should be [m]
        CheckTopology : bool
            Whether to check for overlapping transects and correct. Default is true.
                    
        """
        print("Coast.GenerateTransectNormals: Generating CoastLine transects perpendicular to the coast")

        self.TransectsSpacing = TransectSpacing
        self.TransectsLength2Sea = TransectLength2Sea
        self.TransectsLength2Land = TransectLength2Land

        # generate transects along each line
        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateTransects(TransectSpacing, TransectLength2Sea, TransectLength2Land, CheckTopology)

    def GenerateTransectsNormal2Shp(self, ContourShp1, ContourShp2, Distance2Sea=8000., Distance2Land=8000., TransectSpacing=20., CheckTopology=True):
        """
        Wrapper to the function in the Line object

        Generates transects perpendicular to the coastline and extends them to 
        the nearest point on another shapefile line

        MDH, September 2019

        Parameters
        ----------
        ContourShp : str
            The name of a shapefile containing a contour/contours 
            to base transects on.
        TransectSpacing : float
            The distance between consecutive transects along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]
        """
        print("Coast.GenerateTransectsNormal2Shp: Generating CoastLine transects perpendicular to the coast")

        self.TransectsSpacing = TransectSpacing
        
        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateTransectsNormal2Contours(ContourShp1,ContourShp2,TransectSpacing,Distance2Sea,Distance2Land,CheckTopology)

    def GenerateTransectsFromContours(self,ContourShp,TransectSpacing=10.):

        """

        Loops along Coast line object and creates transects between coast and nearest
        point on adjacent contour lines

        MDH September 2019

        Parameters
        ----------
        ContourShp : str
            The name of a shapefile containing a contour/contours 
            to base transects on.
        TransectSpacing : float
            The distance between consecutive transects along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]
        """

        self.TransectsSpacing = TransectSpacing

        for Line in self.CoastLines:
            Line.GenerateTransectsFromContour(ContourShp, TransectSpacing)

    def CheckTransectTopology(self):

        """
        Wrapper function to check for overlapping transects and collect
        Run this after transects have been updated for historical shoreline positions.
        Will then need to rerun historical shoreline position analysis

        MDH, Feb 2020

        """

        for Line in self.CoastLines:
            Line.CheckTransectTopology()

    def RemoveNoHistoricalTransects(self):
        """
        Deletes transects with no historical shoreline positions at any time?

        """

    def GenerateNodes(self, NodeSpacing):

        """
        Wrapper to the function in the Line object

        Generates nodes the coastline

        MDH, August 2019

        Parameters
        ----------
        NodeSpacing : float
            The distance between consecutive nodes along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]
        
        """
        print("Coast.GenerateNodes: Generating CoastLine nodes")

        self.NodeSpacing = TransectSpacing
        
        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateNodes(NodeSpacing)

    def ExtractHistoricalShorelinePositions(self,HistoricalShorelinesShp):

        """
        Function to find nearest historic shoreline position on each transect
        and add nodes to transect dictionary by date

        MDH, August 2019

        Parameters
        ----------
        HistoricalShorelineShp : string
            Filename for polyline shapfile containing historical shoreline positions
        
        """
        print("Coast.ExtractHistoricalShorelinePositions: Finding historical shoreline positions from ", end="")
        print(Path(HistoricalShorelinesShp).name)

        # set a distance to look inland to check for intersections
        LookDistance = 500.

        # read shapefile using geopandas
        GDF = gp.read_file(HistoricalShorelinesShp)
        Lines = GDF['geometry']
        
        # catch situation where only one line
        if len(Lines) == 1:
            MultiLines = Lines[0]
        else:
            MultiLines = MultiLineString([Line for Line in Lines])
            

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # extend transect line inland to look for intersection
                #Calculate start and end nodes and generate Transect
                X1 = Transect.EndNode.X + LookDistance * np.sin( np.radians( Transect.Orientation ) )
                Y1 = Transect.EndNode.Y + LookDistance * np.cos( np.radians( Transect.Orientation ) )
                TransectLine = LineString(((Transect.StartNode.X,Transect.StartNode.Y),(X1,Y1)))
            
                # intersect with historical shoreline
                Intersections = TransectLine.intersection(MultiLines)

                # catch no intersections and flag for deletion?
                if Intersections.geom_type == "GeometryCollection":
                    Transect.DeleteFlag = True
                    continue

                # check there arent multiple intersections
                # store multiple intersections if so
                if Intersections.geom_type is "MultiPoint":
                    StartPoint = Point(Transect.StartNode.X, Transect.StartNode.Y)
                    Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersections]
                    Index = Distances.index(min(Distances))
                    IntersectionsList = Intersections
                    Intersection = Intersections[Index]
                    Distance = Distances[Index]
                
                else:
                    # check if this is a new endnode by intersecting with line from startnode to endnode
                    Distance = Transect.LineString.distance(Intersections)
                    Intersection = Intersections
                    IntersectionsList = [Intersection,]
                    
                if Distance > 0.001:
                    
                    # set this as the new end node
                    NewEndNode = Node(Intersection.x,Intersection.y)
                    Transect.Redraw(Transect.StartNode, NewEndNode)

                # use minimum of line.distance to find line
                # need date attribute if rates are to be calculated
                Distances = Lines.distance(Intersection)
                NearestLine = GDF.iloc[Distances.idxmin()]
                
                # check it hasnt already been read
                if "Surv_End_A" in NearestLine:
                    Year = int(NearestLine.Surv_End_A)
                elif "Surv_End_B" in NearestLine:
                    Year = int(NearestLine.Surv_End_B)
                elif "Surv_End_C" in NearestLine:
                    Year = int(NearestLine.Surv_End_C)
                elif "Surv_End_D" in NearestLine:
                    Year = int(NearestLine.Surv_End_D)
                elif "versiondat" in NearestLine:
                    Year = int(NearestLine.versiondat[0:4])
                else:
                    sys.exit("Couldnt find survey year for MHWS historic shoreline position")

                if Year not in Transect.HistoricShorelinesYears:
                    
                    # generate lists of positions and distances
                    Positions = []
                    Distances = []

                    for Intersection in IntersectionsList:
                        Position = Node(Intersection.x,Intersection.y)
                        Positions.append(Position)
                        Distances.append(Transect.StartNode.get_Distance(Position))

                    # add to transect
                    Transect.HistoricShorelinesPositions.append(Positions)
                    Transect.HistoricShorelinesDistances.append(Distances)
                    Transect.HistoricShorelinesYears.append(Year)

                else:
                    
                    # find and replace
                    Index = Transect.HistoricShorelinesYears.index(Year)

                    # add points to transect
                    Positions = []
                    Distances = []
                    
                    for Intersection in Intersections:
                        Position = Node(Intersection.x,Intersection.y)
                        Positions.append(Position)
                        Distances.append(Transect.StartNode.get_Distance(Position))

                    # add to transect
                    Transect.HistoricShorelinesPositions[Index] = Positions
                    Transect.HistoricShorelinesDistances[Index] = Transect.StartNode.get_Distance(Positions)

    def ExtractContours(self,ContourShp):

        """
        Function to find nearest location of -10 m depth contour
        from contour shapefile for each transect

        MDH, August 2019

        Parameters
        ----------
        ContourShp : string
            Filename for polyline shapfile containing depth contours
        
        """
        print("Coast.ExtractContours: Finding nearest depth contours")
        
        # read shapefile using geopandas
        GDF = gp.read_file(ContourShp)
        
        for Contour in GDF.level.unique():
        
            # isolate closure depth contour
            GDFtemp = GDF[GDF.level == Contour]
        
            # get lines geometry
            Lines = GDFtemp['geometry']
            MultiLines = MultiLineString([Line for Line in Lines])

            for i, ContourLine in enumerate(MultiLines):
                x, y = ContourLine.xy
                TempLine = Line(str(i),x,y,Contour)
                self.Contours.append(TempLine)
            
            for ThisLine in self.CoastLines:
                for Transect in ThisLine.Transects:
                    
                    # shapely goes here
                    BasePoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                    NearestPoint = nearest_points(MultiLines, BasePoint)[0]
                    Transect.Contours.append(Node(str(Contour), NearestPoint.x,NearestPoint.y, Contour))

    


    def SampleHistoricalRSLR(self, PastRSLRRaster):

        """ 
        
        Samples a raster of most recent rates of relative sea level change (rise/fall)
        at each transect location on coast. 

        Gets the nearest point for now, rather than any interpolation

        Parameters
        ----------
        PastRSLRRaster : string
            Filename for raster to be sampled
        
        MDH, September 2019

        """

        print("Coast.SampleHistoricalRSLR: Sampling historical Relative Sea Level raster dataset")

        # open the raster dataset to work on
        with rasterio.open(PastRSLRRaster) as RSLRDataset:
        
            # loop through transects and sample
            for Line in self.CoastLines:
                for i, Transect in enumerate(Line.Transects[:]):
                    for val in RSLRDataset.sample([(Transect.CoastNode.X,Transect.CoastNode.Y)]):
                        Transect.HistoricalRSLR = val[0]

    def SampleMHWSElevation(self,MHWSRaster):

        """
        Samples a raster of MHWS elevation at each transect location on the coast

        Parameters
        ----------

        MHWSRaster : string
            Filename for raster to be sampled
        
        MDH, January 2020

        """

        print("Coast.SampleMHWSElevation: Sampling MHWS elevation raster dataset")

        # open the raster dataset to work on
        with rasterio.open(MHWSRaster) as MHWSDataset:
        
            # loop through transects and sample
            for Line in self.CoastLines:
                for i, Transect in enumerate(Line.Transects[:]):
                    for val in MHWSDataset.sample([(Transect.CoastNode.X,Transect.CoastNode.Y)]):
                        Transect.MHWS = val[0]


    def SampleFutureRSL(self, FutureRSLFolder, Percentile=95, Years=[2010,2020,2030,2040,2050,2060,2070,2080,2090,2100]):

        """ 
        
        Samples a raster of future rates of relative sea level change (rise/fall)
        at each transect location on coast

        Parameters
        ----------
        FutureRSLFolder : string
            Folder containing future sea level elevation rasters for Scotland
        Percentile : int
            Percentile scenario to use
        Years : list
            List of integers corresponding to the years to be analysed
        
        MDH, September 2019

        """

        print("Coast.SampleFutureRSL: Sampling future Relative Sea Level raster dataset")

        if self.FutureShoreLinesYears:
            print("\tFuture sea levels already sampled")
            return

        self.FutureShoreLinesYears = Years

        for Year in Years:
            FutureRSLRaster = FutureRSLFolder + "/RCP8_" + str(Percentile) + "th_" + str(Year) + "_OSGB_filled.tif"

            # open the raster dataset to work on
            with rasterio.open(FutureRSLRaster) as RSLDataset:
            
                # loop through transects and sample
                for Line in self.CoastLines:
                    for i, Transect in enumerate(Line.Transects[:]):
                        for val in RSLDataset.sample([(Transect.CoastNode.X,Transect.CoastNode.Y)]):
                            Transect.FutureSeaLevels.append(val[0])
                            Transect.FutureSeaLevelYears.append(Year)

    def SampleRockHeadPosition(self, UPSMRaster):

        """
        Function to check values of UPSM and identify if a limit on shoreline erosion position 
        is required based on a threshold value of 0.4

        MDH, January 2020

        """

        # open the raster dataset to work on
        with rasterio.open(UPSMRaster) as RockHeadDataset:
        
            # loop through transects and sample
            for Line in self.CoastLines:
                for i, Transect in enumerate(Line.Transects[:]):
                    
                    # generate a list of tuples to sample UPSM
                    X1 = Transect.StartNode.X
                    Y1 = Transect.StartNode.Y
                    X2 = Transect.EndNode.X
                    Y2 = Transect.EndNode.Y
                    X = np.linspace(X1,X2,50.)
                    Y = np.linspace(Y1,Y2,50.)
                    NodeList = tuple(zip(X, Y))

                    # build a list of X,Y values to check along transect to find position of rock head if present
                    #for val in RSLRDataset.sample([(Transect.CoastNode.X,Transect.CoastNode.Y)]):
                    RockHeadVector = np.array([val[0] for val in RockHeadDataset.sample(NodeList)])
                    RockHeadVector[RockHeadVector < 0] = np.nan
                    
                    # if everything is soft, carry on
                    # ignore errors caused by NaNs
                    with np.errstate(invalid='ignore'):
                        RockBool = RockHeadVector < 0.4
        
                    if not RockBool.any():
                        continue
                    
                    # else find the position of the first appearance of 0.4
                    JInd = np.argmax(RockBool)
                    
                    if JInd == len(RockHeadVector)-1:
                        continue

                    # repeat to find to the nearest meter
                    dX = (X[JInd-1] - X[JInd+1])
                    dY = (Y[JInd-1] - Y[JInd+1])
                    NVals = np.int(np.sqrt(dX**2. + dY**2.))
                    
                    X = np.linspace(X[JInd-1], X[JInd+1], NVals)
                    Y = np.linspace(Y[JInd-1], Y[JInd+1], NVals)
                    NodeList = tuple(zip(X, Y))

                    # build a list of X,Y values to check along transect to find position of rock head if present
                    RockHeadVector = np.array([val[0] for val in RockHeadDataset.sample(NodeList)])
                    RockHeadVector[RockHeadVector < 0] = np.nan

                    # else find the position of the first appearance of 0.4
                    # ignore errors caused by NaNs
                    with np.errstate(invalid='ignore'):
                        RockBool = RockHeadVector < 0.4
                    JInd = np.argmax(RockBool)

                    # flag position as attribute of transect
                    Transect.RockHeadPosition = Node(X[JInd],Y[JInd])
                    Transect.RockHeadDistance = Transect.StartNode.get_Distance(Transect.RockHeadPosition)

    def PredictFutureShorelines(self):

        """

        Wrapper to call Transects function to predict future shoreline positions

        MDH, September 2019

        """
        print("Coast.PredictFutureShorelines: predicting future shoreline positions")
        # loop through transects and sample
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.PredictFutureShorelines()

    def WriteFutureShorelines(self):

        """

        Wrapper to write future shoreline positions to individual shapefiles

        MDH, September 2019

        """

        
    
    def ExtractTransectTopography(self, DTMFile, SwathDistance=-9999):
        """
        Profile to populate transects with topographic data
        Uses swath profile routine to collect elevations within a certain distance
        of each transect line then takes IDW values for the transect topography

        ADD FUNCTIONALITY TO CATCH WHEN DEM EDGE HAS BEEN EXCEEDED? NO TRANSECTS IN THIS CASE

        MDH, June 2019
        
        Parameters
        ----------
        DTMFile : str
            Name of DTM File, must be a *.tif

        SwathDistance : float
            Distance away from transect line to sample elevations in DEM
            Default is 2 times the resolution of the DTM

        """
        
        print("Coast.EstractTransectTopography: Sampling the DTM for each transect")
        
        # load the DTM and get its properties
        print("\tLoading DTM... ", end="")
        DTM_Dataset = rasterio.open(DTMFile)
        DTMArray = DTM_Dataset.read(1)
        NCols = DTM_Dataset.width
        NRows = DTM_Dataset.height
        NDV = DTM_Dataset.nodata
        Resolutions = DTM_Dataset.res
        print("Done")

        # check for square pixels
        if not DTM_Dataset.res[0] == DTM_Dataset.res[1]:
            raise SystemExit("DTM has non-square cells")
        
        # get resolution
        DTM_Resolution = DTM_Dataset.res[0]

        # check swath distance
        if SwathDistance < 0:
            SwathDistance = DTM_Resolution*2.

        # get extent of DTM
        XMin = DTM_Dataset.bounds[0]
        XMax = DTM_Dataset.bounds[2]
        YMin = DTM_Dataset.bounds[1]
        YMax = DTM_Dataset.bounds[3]

        # Get vectors of X and Y coordinates, NB reversal of Y in line with 
        # DTM indexing from top left
        XVector = XMin+np.arange(0,NCols)*DTM_Resolution+0.5*DTM_Resolution
        YVector = YMin+DTM_Resolution*np.arange(0,NRows)[::-1]+0.5*DTM_Resolution

        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])
        CurrentTransect = 0
        for Line in self.CoastLines:
            for i, Transect in enumerate(Line.Transects[:]):
                
                #Get line points
                X1, Y1 = Transect.StartNode.get_XY()
                X2, Y2 = Transect.EndNode.get_XY()

                # check transect lies within DEM extent
                #if X1 < XMin or X2 < XMin:
                
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                # pass DTM
                # this needs to be changed to pass to transect object
                # fix this later

                # print progress to screen
                print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")

                #Get line points
                X1, Y1 = Transect.StartNode.get_XY()
                X2, Y2 = Transect.EndNode.get_XY()

                #find indices for bounding box
                #need to be careful with reverse indexing
                iStart = np.argmin(np.abs(YVector-np.max([Y1,Y2])))-1
                iEnd = np.argmin(np.abs(YVector-np.min([Y1,Y2])))+1
                jStart = np.argmin(np.abs(XVector-np.min([X1,X2])))-1
                jEnd = np.argmin(np.abs(XVector-np.max([X1,X2])))+1

                #Get Vector X and Y
                dX12 = X2-X1
                dY12 = Y2-Y1

                #Declare list holders for profile data
                X = []
                Y = []
                Z = []
                DistAlong = []
                DistTo = []
                
                for i in range(iStart,iEnd):

                    #get Y position
                    YNode = YMax-DTM_Resolution*i-0.5*DTM_Resolution

                    for j in range(jStart,jEnd):
                        
                        #get X position
                        XNode = XMin + j*DTM_Resolution + 0.5*DTM_Resolution;

                        #Get 2nd Vector Properties in Array
                        dX13 = XNode-X1
                        dY13 = YNode-Y1

                        #Find Dot Product
                        DotProduct = dX12*dX13 + dY12*dY13;

                        #calculate fraction of distance along line
                        t = DotProduct/(dX12*dX12 + dY12*dY12)
                        if ((t < 0.) or (t > 1.)):
                            continue
                    
                        #Find point along line
                        XLine = X1 + t*dX12
                        YLine = Y1 + t*dY12
                        DistanceAlongLine = t*np.sqrt(dX12*dX12 + dY12*dY12)

                        #find distance to point
                        DistanceToLine = np.sqrt((XLine-XNode)*(XLine-XNode) + (YLine-YNode)*(YLine-YNode))

                        if ((DistanceToLine < SwathDistance) and (DTMArray[i][j] != NDV)):
                            X.append(XNode)
                            Y.append(YNode)
                            DistAlong.append(DistanceAlongLine)
                            DistTo.append(DistanceToLine)
                            Z.append(DTMArray[i][j])
                                
                #Sort by distance along line, need to convert to numpy arrays as we go to sort
                Sortedi = np.argsort(DistAlong)
                X = np.asarray(X)[Sortedi]
                Y = np.asarray(Y)[Sortedi]
                DistAlong = np.asarray(DistAlong)[Sortedi]
                DistTo = np.asarray(DistTo)[Sortedi]
                Z = np.asarray(Z)[Sortedi]
                
                #if (WriteSwathDataFlag):
                    # Write results to text file using pandas (easier) for each profile
                    #DF = pd.DataFrame({"X": X, "Y": Y, "Z": Z, "DistAlong": DistAlong, "DistTo": DistTo})
                    #DF.to_pickle(SwathProfsFolder+"Swath_"+str(Transect.ID)+".pkl")
                
                #Create a line for interpolating to
                # determination of distance spacing should be externalised
                LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
                NoPoints = (int)(LineLength/(DTM_Resolution*2.))
                Transect.DistanceSpacing = DTM_Resolution*2.
                XLine = np.linspace(X1,X2,NoPoints)
                YLine = np.linspace(Y1,Y2,NoPoints)
                DistAlongTransect = np.zeros(len(XLine))
                ZIDW = np.zeros(len(XLine))
                ZMin = np.zeros(len(XLine))
                ZMax = np.zeros(len(XLine))
                ZStd = np.zeros(len(XLine))
                                
                #Loop along line
                for i in range(0,NoPoints):
                    
                    #Calculate distance along the line
                    DistAlongTransect[i] = i*DTM_Resolution*2.
                    
                    # Sample a reduced array here i.e. a neighbourhood to reduce computation time
                    Neighbourhood = np.abs(DistAlongTransect[i]-DistAlong) < DTM_Resolution*2.
                    ZLocal = Z[Neighbourhood]
                    
                    if len(ZLocal) == 0:
                        
                        # Set to NDV
                        ZIDW[i] = NDV
                        ZMin[i] = NDV
                        ZMax[i] = NDV
                        ZStd[i] = NDV
                        
                        continue
                    
                    # Do IDW
                    # Create a distance vector
                    Dist = np.sqrt(DistAlong[Neighbourhood]**2. + DistTo[Neighbourhood]**2.)
                    
                    # Weights are inverse
                    Weights = 1./Dist**2.
                    
                    # Interpolate Z
                    ZIDW[i]  = np.sum(Z[Neighbourhood]*Weights)/np.sum(Weights)
                    
                    # Other Z Values
                    ZMin[i] = np.min(ZLocal)
                    ZMax[i] = np.max(ZLocal)
                    ZStd[i] = np.std(ZLocal)
                    
                # Set up the mask from NDVs
                Mask = ZIDW == NDV
                DistAlongTransect = ma.masked_where(Mask,DistAlongTransect)
                ZIDW = ma.masked_where(Mask,ZIDW)
                ZMin = ma.masked_where(Mask,ZMin)
                ZMax = ma.masked_where(Mask,ZMax)
                ZStd = ma.masked_where(Mask,ZStd)
                
                Transect.Distance = DistAlongTransect
                Transect.DistanceSpacing = DistAlongTransect[1]-DistAlongTransect[0]
                Transect.Elevation = ZIDW
                Transect.ElevationMin = ZMin
                Transect.ElevationMax = ZMax
                Transect.ElevStd = ZStd

                # update transect no
                CurrentTransect += 1
        
        print("")

    def AnalyseTransectMorphology(self):

        """

        Barrier focus for now

        MDH, June 2019

        """

        print("Coast.AnalyseTransectMorphology: Finding cliff and barrier positions and calculating metrics")

        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1
        CurrentTransect = 0

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # print progress to screen
                print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")
                
                # # Call analyses
                #if Transect.ID == "13":
                Transect.FindCliff()
                Transect.FindBarrier()
                
                # update transect progress no
                CurrentTransect += 1
        
        print("")

    def AnalyseBarrierWidths(self, WaterElevs):
        
        """
        
        Extracts barrier width at given elevations e.g. high water

        MDH, June 2019

        """

        print("Coast.AnalyseBarrierWidth: Finding barrier positions at a given elevations and calculating metrics")

        # update extreme water levels
        self.ExtremeWaterLevels = WaterElevs

        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1
        CurrentTransect = 0

        # loop through transects and get contiguous barrier lines
        for CoastLine in self.CoastLines:
            for Transect in CoastLine.Transects:
                
                # print progress to screen
                print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")
                    
                # extract barrier width
                #if Transect.ID == "138":
                #    Transect.ExtractBarrierWidths(WaterElevs)
                Transect.ExtractBarrierWidths(WaterElevs)

                # update transect progress no
                CurrentTransect += 1

        print("")
    
    def MapBarrierFeatureExtents(self, WaterElevs, DTM):
        """
        Function to contour the DEM to map extent of elevations above extreme water levels
        but within the zone of analysis from the first to the last topographic intersection

        MDH, October 2019
        
        Parameters
        ----------
        WaterElevsL : list(float)
            List of extreme water surface elevations
        
        DTMFile : str
            Name of DTM File, must be a *.tif

        """
        
        print("Coast.MapBarrierFeatureExtents: Extracting features from DTM")

        # get the max extent of flood protection features

        
        # load the DTM and get its properties
        print("\tLoading DTM... ", end="")
        DTM_Dataset = rasterio.open(DTMFile)
        DTMArray = DTM_Dataset.read(1)
        NCols = DTM_Dataset.width
        NRows = DTM_Dataset.height
        NDV = DTM_Dataset.nodata
        Resolutions = DTM_Dataset.res
        print("Done")

        # check for square pixels
        if not DTM_Dataset.res[0] == DTM_Dataset.res[1]:
            raise SystemExit("DTM has non-square cells")
        
        # get resolution
        DTM_Resolution = DTM_Dataset.res[0]

        # check swath distance
        if SwathDistance < 0:
            SwathDistance = DTM_Resolution*2.

        # get extent of DTM
        XMin = DTM_Dataset.bounds[0]
        XMax = DTM_Dataset.bounds[2]
        YMin = DTM_Dataset.bounds[1]
        YMax = DTM_Dataset.bounds[3]

        # Get vectors of X and Y coordinates, NB reversal of Y in line with 
        # DTM indexing from top left
        XVector = XMin+np.arange(0,NCols)*DTM_Resolution+0.5*DTM_Resolution
        YVector = YMin+DTM_Resolution*np.arange(0,NRows)[::-1]+0.5*DTM_Resolution

        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])
        CurrentTransect = 0

    def FindRockyCoast(self, TidalElevation=2.):

        """
        
        Calculates roughness up to a fixed tidal elevation as the standard deviation of 
        slope and the average standard deviation of local elevations

        uses a kmeans clustering algorithm to split in two based on these in order to split
        rocky from sandy

        MDH, July 2019

        """

        # loop through transects and get contiguous barrier lines
        for CoastLine in self.CoastLines:
            for Transect in CoastLine.Transects:
                Transect.AnalyseRoughness(TidalElevation)
        
        #NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1

        # Get roughness values as arrays
        SlopeRoughness = np.array([Transect.SlopeRoughness for Line in self.CoastLines for Transect in Line.Transects])
        ValueLocs = (np.isnan(SlopeRoughness) == False)
        Locations = np.argwhere(ValueLocs)
        SlopeRoughness = SlopeRoughness[ValueLocs]
        ElevationRoughness = np.array([Transect.ElevationRoughness for Line in self.CoastLines for Transect in Line.Transects])
        ElevationRoughness = ElevationRoughness[ValueLocs]
        Data = np.column_stack((SlopeRoughness,ElevationRoughness))
        
        # perform k-means clustering assuming two clusters
        # set up a KMeans object
        ThisKMeans = KMeans(n_clusters=2)
        ThisKMeans.fit(Data)
        GroupList = ThisKMeans.fit_predict(Data)
        
        # check which way round and correct
        if np.mean(ElevationRoughness[GroupList == 0]) > np.mean(ElevationRoughness[GroupList == 1]):
            GroupList = abs(GroupList-1)
        
        # loop through transects and get contiguous barrier lines
        Counter = 0
        for CoastLine in self.CoastLines:
            for i, Transect in enumerate(CoastLine.Transects):
                #print(str(Transect.ID) + " " + str(Counter)+"/"+str(NoTransects))
                Transect.Rocky = GroupList[Counter]
                Counter += 1
                #print(len(GroupList))

    def GetFutureShoreLines(self):

        """

        Extracts contiguous lines of future predicted MHWS

        """
        self.FutureShoreLines = []

        # Loop through prediction years
        for Year in self.FutureShoreLinesYears[1:]:

            # keep track of no of coastal segments for IDs
            FutureCount = 0
            
            # loop through transects and get contiguous cliff lines
            for CoastLine in self.CoastLines:
                
                # find transects with future predictions
                FutureBool = [Transect.Future for Transect in CoastLine.Transects]
                FutureBool.insert(0, False)
                FutureBool = np.array(FutureBool).astype(int)

                # check for lines with no predictions
                if not any(FutureBool):
                    continue
                
                # get a list of the start and end points of contiguous cliff lines
                StartEndFlags = np.diff(FutureBool)

                # if last line finishes on a cliff flag the last element as the end of the cliff
                if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                    StartEndFlags[-1] = -1

                StartList = np.argwhere(StartEndFlags == 1).flatten()
                EndList = np.argwhere(StartEndFlags == -1).flatten()
                if not len(StartList) == len(EndList):
                    print("Start and End lists not the same length")
                    print(len(StartList),len(EndList))
                    
                for i in range(0,len(StartList)):
                    
                    # catch single node cliff lines and ignore
                    if (EndList[i]-StartList[i]<2):
                        continue

                    # create empty lists for storing future nodes
                    FutureList = []
                    
                    # add latest MHWS from previous node to start
                    # might need some logic here for first transect
                    if StartList[i] == 0:
                        FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                    else:
                        try:
                            FirstNode = CoastLine.Transects[StartList[i]-1].get_RecentPosition()
                        except:
                            FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                    
                    FutureList.append(FirstNode)
                    # loop through transects and get future positions
                    for Transect in CoastLine.Transects[StartList[i]:EndList[i]]:
                        FutureNode = Transect.get_FuturePosition(Year)
                        FutureList.append(FutureNode)
                        
                    # add latest MHWS from next node to end
                    # might need some logic here to finish
                    if EndList[i] == CoastLine.NoTransects-1:
                        LastNode = CoastLine.Transects[EndList[i]-1].get_RecentPosition()
                    else:
                        try:
                            LastNode = CoastLine.Transects[EndList[i]].get_RecentPosition()
                        except:
                            LastNode = CoastLine.Transects[EndList[i]-1].get_RecentPosition()
                    
                    FutureList.append(LastNode)
                    
                    # create new line object for top
                    X = [FutureNode.X for FutureNode in FutureList]
                    Y = [FutureNode.Y for FutureNode in FutureList]
                    
                    TempLine = Line("FutureCoast_"+str(FutureCount), X, Y, Year=Year)
                    self.FutureShoreLines.append(TempLine)
                    
                    # update counter
                    FutureCount += 1


    def GetBarrierWidth(self):

        """
        
        Gets barrier at a given elevation e.g. high water

        MDH, June 2019

        """
        
        # keep track of no of barrier locations for IDs
        BarrierCount = 0

        # loop through transects and get contiguous barrier lines
        for CoastLine in self.CoastLines:
            
            # find transects with cliffs
            BarrierBool = [Transect.Intersection for Transect in CoastLine.Transects]
            BarrierBool.insert(0, False)
            BarrierBool = np.array(BarrierBool).astype(int)
            
            # get a list of the start and end points of contiguous barrier lines
            StartEndFlags = np.diff(BarrierBool)
            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()
            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                print(len(StartList),len(EndList))

            for i in range(0,len(StartList)):
                
                # catch single node cliff lines and ignore
                if (EndList[i]-StartList[i]<2):
                    continue

                # create empty lists for storing clifftop and clifftoe nodes
                FrontList = []
                BackList = []

                # loop through transects and get top and toe positions
                
                for Transect in CoastLine.Transects[StartList[i]:EndList[i]]:
                    FrontNode, BackNode = Transect.get_CliffPosition()
                    FrontList.append(FrontNode)
                    BackList.append(BackNode)
                
                # create new line object for front
                X = [FrontNode.X for FrontNode in FrontList]
                Y = [FrontNode.Y for FrontNode in FrontList]
                
                TempLine = Line("Front_"+str(BarrierCount), X, Y)
                self.ExtremeFrontLines.append(TempLine)
                
                # create new line object for toe
                X = [BackNode.X for BackNode in BackList]
                Y = [BackNode.Y for BackNode in BackList]
                
                TempLine = Line("Back_"+str(BarrierCount), X, Y)
                self.ExtremeBackLines.append(TempLine)

                # update counter
                BarrierCount += 1

    def GetCliffLines(self):
        
        """

        Generate line objects from cliff top and cliff toe positions on transects

        MDH, June 2019

        """

        # keep track of no of cliffs for IDs
        CliffCount = 0

        # loop through transects and get contiguous cliff lines
        for CoastLine in self.CoastLines:
            
            # find transects with cliffs
            CliffBool = [Transect.Cliff for Transect in CoastLine.Transects]
            CliffBool.insert(0, False)
            CliffBool = np.array(CliffBool).astype(int)

            # check for transects with no cliffs
            if not any(CliffBool):
                print("No Cliffs on Line")
                continue
            
            # get a list of the start and end points of contiguous cliff lines
            StartEndFlags = np.diff(CliffBool)

            # if last line finishes on a cliff flag the last element as the end of the cliff
            if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                StartEndFlags[-1] = -1

            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()
            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                print(len(StartList),len(EndList))
                
            for i in range(0,len(StartList)):
                
                # catch single node cliff lines and ignore
                if (EndList[i]-StartList[i]<2):
                    continue

                # create empty lists for storing clifftop and clifftoe nodes
                CliffTopList = []
                CliffToeList = []

                # loop through transects and get top and toe positions
                
                for Transect in CoastLine.Transects[StartList[i]:EndList[i]]:
                    TempTop, TempToe = Transect.get_CliffPosition()
                    CliffTopList.append(TempTop)
                    CliffToeList.append(TempToe)
                
                # create new line object for top
                X = [TempTop.X for TempTop in CliffTopList]
                Y = [TempTop.Y for TempTop in CliffTopList]
                
                TempLine = Line("Cliff_"+str(CliffCount), X, Y)
                self.CliffTopLines.append(TempLine)
                
                # create new line object for toe
                X = [TempToe.X for TempToe in CliffToeList]
                Y = [TempToe.Y for TempToe in CliffToeList]
                
                TempLine = Line("Cliff_"+str(CliffCount), X, Y)
                self.CliffToeLines.append(TempLine)

                # update counter
                CliffCount += 1

    def GetBarrierLines(self):
        
        """

        Generate line objects from cliff top and cliff toe positions on transects,
        Also get crest line

        MDH, June 2019

        """

        # keep track of no of cliffs for IDs
        BarrierCount = 0

        # loop through transects and get contiguous barrier lines
        for CoastLine in self.CoastLines:
            
            # find transects with barriers
            BarrierBool = [Transect.Barrier for Transect in CoastLine.Transects]
            BarrierBool.insert(0, False)
            BarrierBool = np.array(BarrierBool).astype(int)
            
            # get a list of the start and end points of contiguous cliff lines
            StartEndFlags = np.diff(BarrierBool)
            
            # get last non zero element
            Last = [Ind for Ind, Flag in enumerate(StartEndFlags) if Flag != 0][-1]
            
            # if last line finishes on a start barrier flag then ignore
            if Last != len(StartEndFlags)-1:
                if StartEndFlags[Last] == 1:
                    StartEndFlags[-1] = -1
            elif StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
                
                
            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()

            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                
            for i in range(0,len(StartList)):
                
                # catch single node cliff lines and ignore
                if (EndList[i]-StartList[i]<2):
                    continue

                # create empty lists for storing barrier front and back top and toe nodes
                """
                THIS WHOLE THING COULD PROBABLY BE SIMPLIFIED MASSIVELY BY USING __DICT__
                """
                BarrierFrontTopList = []
                BarrierFrontToeList = []
                BarrierBackTopList = []
                BarrierBackToeList = []
                CrestList = []

                # loop through transects and get top and toe positions
                
                for Transect in CoastLine.Transects[StartList[i]:EndList[i]]:
                    TempFrontTop, TempFrontToe, TempBackTop, TempBackToe, TempCrest = Transect.get_BarrierPosition()
                    BarrierFrontTopList.append(TempFrontTop)
                    BarrierFrontToeList.append(TempFrontToe)
                    BarrierBackTopList.append(TempBackTop)
                    BarrierBackToeList.append(TempBackToe)
                    CrestList.append(TempCrest)
                
                # create new line object for front top
                X = [TempTop.X for TempTop in BarrierFrontTopList]
                Y = [TempTop.Y for TempTop in BarrierFrontTopList]
                
                TempLine = Line("Barrier_"+str(BarrierCount), X, Y)
                self.BarrierFrontTopLines.append(TempLine)
                
                # create new line object for front toe
                X = [TempToe.X for TempToe in BarrierFrontToeList]
                Y = [TempToe.Y for TempToe in BarrierFrontToeList]
                
                TempLine = Line("Barrier_"+str(BarrierCount), X, Y)
                self.BarrierFrontToeLines.append(TempLine)

                # create new line object for back top
                X = [TempTop.X for TempTop in BarrierBackTopList]
                Y = [TempTop.Y for TempTop in BarrierBackTopList]
                
                TempLine = Line("Barrier_"+str(BarrierCount), X, Y)
                self.BarrierBackTopLines.append(TempLine)
                
                # create new line object for back toe
                X = [TempToe.X for TempToe in BarrierBackToeList]
                Y = [TempToe.Y for TempToe in BarrierBackToeList]
                
                TempLine = Line("Barrier_"+str(BarrierCount), X, Y)
                self.BarrierBackToeLines.append(TempLine)

                # create new line object for crest
                X = [TempCrest.X for TempCrest in CrestList]
                Y = [TempCrest.Y for TempCrest in CrestList]
                
                TempLine = Line("Crest_"+str(BarrierCount), X, Y)
                self.CrestLines.append(TempLine)

                # update counter
                BarrierCount += 1

    def GetExtremeLines(self):
        
        """

        Generate line objects from extreme water positions on transects for front feature,
        
        MDH, July 2019

        """

        # loop through extreme water levels
        for i, Level in enumerate(["Low", "Med","High"]):
            
            # keep track of no of cliffs for IDs
            Count = 0
            
            # loop through transects and get contiguous extreme lines
            for CoastLine in self.CoastLines:
            
                # find transects with cliffs
                Widths = np.array([Transect.ExtremeWidths[i] for Transect in CoastLine.Transects])
                ExtremeBool = np.array([False if Width is None else True for Width in Widths])
                ExtremeBool[Widths==0] = False
                ExtremeBool = np.insert(ExtremeBool, 0, False)
                ExtremeBool = np.array(ExtremeBool).astype(int)
                
                # get a list of the start and end points of contiguous cliff lines
                StartEndFlags = np.diff(ExtremeBool)
                
                # get last non zero element
                Last = [Ind for Ind, Flag in enumerate(StartEndFlags) if Flag != 0][-1]
                
                # if last line finishes on a start barrier flag then ignore
                if Last != len(StartEndFlags)-1:
                    if StartEndFlags[Last] == 1:
                        StartEndFlags[-1] = -1
                elif StartEndFlags[-1] == 1:
                    StartEndFlags[-1] = 0
                    
                StartList = np.argwhere(StartEndFlags == 1).flatten()
                EndList = np.argwhere(StartEndFlags == -1).flatten()

                if not len(StartList) == len(EndList):
                    print("Start and End lists not the same length")


                for j in range(0,len(StartList)):
                    
                    # catch single node cliff lines and ignore
                    if (EndList[j]-StartList[j]<2):
                        continue

                    # create empty lists for storing barrier front and back top and toe nodes
                    """
                    THIS WHOLE THING COULD PROBABLY BE SIMPLIFIED MASSIVELY BY USING __DICT__
                    """
                    ExtremeFrontList = []
                    ExtremeBackList = []
                    
                    # loop through transects and get front and back positions
                    for Transect in CoastLine.Transects[StartList[j]:EndList[j]]:
                        try:
                            TempFront, TempBack  = Transect.get_ExtremePosition(i)
                            ExtremeFrontList.append(TempFront)
                            ExtremeBackList.append(TempBack)
                        except:
                            continue
                    
                    if len(ExtremeFrontList) < 2:
                        continue
                        
                    # create new line object for front 
                    X = [TempFront.X for TempFront in ExtremeFrontList]
                    Y = [TempFront.Y for TempFront in ExtremeFrontList]
                    
                    TempLine = Line("Ext_"+Level+str(Count), X, Y)
                    self.__dict__["ExtFrontLines_"+Level].append(TempLine)
                    
                    # create new line object for back
                    X = [TempBack.X for TempBack in ExtremeBackList]
                    Y = [TempBack.Y for TempBack in ExtremeBackList]
                    
                    TempLine = Line("Ext_"+Level+str(Count), X, Y)
                    self.__dict__["ExtBackLines_"+Level].append(TempLine)

                    # update counter
                    Count += 1

    def GetExtremeExtent(self):

        """
        Generates shapefiles of the lowest elevation extreme water
        extent that is providing some sort of protective function

        MDH, October 2019

        """

        # loop through extreme water levels
        i = 0
        Level = "Low"
        
        # keep track of no of lines for IDs
        Count = 0
            
        # loop through transects and get contiguous extreme lines
        for CoastLine in self.CoastLines:
        
            # find transects with coastal protection
            ExtremeBool = ([any(isinstance(Transect.Intersections,float)) for Transect in CoastLine.Transect])
            ExtremeBool = np.insert(ExtremeBool, 0, False)
            ExtremeBool = np.array(ExtremeBool).astype(int)
            
            # get a list of the start and end points of contiguous sections with protection
            StartEndFlags = np.diff(ExtremeBool)
            
            # get last non zero element
            Last = [Ind for Ind, Flag in enumerate(StartEndFlags) if Flag != 0][-1]
            
            # if last line finishes on a start flag then ignore
            if Last != len(StartEndFlags)-1:
                if StartEndFlags[Last] == 1:
                    StartEndFlags[-1] = -1
            elif StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
            
            # start flag is gradient = 1, end flag where gradient = -1
            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()

            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")


            for j in range(0,len(StartList)):
                
                # catch single node cliff lines and ignore
                if (EndList[j]-StartList[j]<2):
                    continue

                # create empty lists for storing barrier front and back top and toe nodes
                """
                THIS WHOLE THING COULD PROBABLY BE SIMPLIFIED MASSIVELY BY USING __DICT__
                """
                ExtremeFrontList = []
                ExtremeBackList = []
                
                # loop through transects and get front and back positions
                for Transect in CoastLine.Transects[StartList[j]:EndList[j]]:
                    try:
                        TempFront, TempBack  = Transect.get_ExtremePosition(i)
                        ExtremeFrontList.append(TempFront)
                        ExtremeBackList.append(TempBack)
                    except:
                        continue
                
                if len(ExtremeFrontList) < 2:
                    continue
                    
                # create new line object for front 
                X = [TempFront.X for TempFront in ExtremeFrontList]
                Y = [TempFront.Y for TempFront in ExtremeFrontList]
                
                TempLine = Line("Ext_"+Level+str(Count), X, Y)
                self.__dict__["ExtFrontLines_"+Level].append(TempLine)
                
                # create new line object for back
                X = [TempBack.X for TempBack in ExtremeBackList]
                Y = [TempBack.Y for TempBack in ExtremeBackList]
                
                TempLine = Line("Ext_"+Level+str(Count), X, Y)
                self.__dict__["ExtBackLines_"+Level].append(TempLine)

                # update counter
                Count += 1

    def SetMHWS(self,MHWS):

        """
        Sets MHWS on all lines and transects
        Could be replaced with spatially dynamic data later

        MDH, July 2019

        """
        # set MHWS
        self.MHWS = MHWS

        # loop through lines and plot profiles #
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.MHWS = MHWS

    def SetShorefaceDepth(self,Dsf):

        """
        Sets shoreface depth on all lines and transects
        Could be replaced with spatially dynamic data later

        MDH, November 2019

        """
        # set Shoreface Depth
        self.Dsf = Dsf

        # loop through lines and 
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.ClosureDepth = Dsf

    def PlotTransects(self, PlotFolder, ReverseFlag=False):
        
        """

        Description goes here

        MDH, June 2019

        """

        #import figure plotting stuff here not globally!
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt

        print("Coast.PlotTransects: Plotting each transect topographic profile")

        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1
        CurrentTransect = 0

        # loop through lines and plot profiles #
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # print progress to screen
                print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")

                # call plotting function
                if (Line.ID == 1) and (Transect.ID == 969):
                    Transect.Plot(PlotFolder, ReverseFlag)
                    
                CurrentTransect += 1

        print("")

    def PlotBarrierProperties(self, PlotFolder):
        """
        """

        #import figure plotting stuff here not globally!
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt

        # set up a figure
        # in time might want to automatically adjust figure for coast orientation
        fig, ax = plt.figure(figsize=(8,4))
        
        for Line in self.Coastlines:
            
            # get property to plot
            W  = [Transect.ToeWidth for Transect in Line.Transects]
            ax.plot(W,range(0,len(W)),'k-',lw=2)
        
        ax.set_xlabel("Barrier Width at Toe (m)")
        ax.set_ylabel("Transect ID")
        fig.savefig(PlotFolder + "BarrierWidth.png")

        fig.clear()
        plt.close(fig)
    
    def PlotPositions():

        #import figure plotting stuff here not globally!
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pyplot as plt

        print("Coast.PlotPositions: Plotting transect positions")

        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1
        CurrentTransect = 0

        # loop through lines and plot profiles #
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # print progress to screen
                print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")

                # call plotting function
                #if Transect.ID == "0":
                Transect.PlotPositions(PlotFolder)
                    
                CurrentTransect += 1

        print("")
        