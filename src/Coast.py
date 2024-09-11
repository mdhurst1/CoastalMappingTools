"""
Coast object for analysing coastal morphology and predicting future coastal change

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import os, sys, time, pickle, bisect, pdb
from pathlib import Path
import numpy as np
from scipy.interpolate import splprep, splev
import numpy.ma as ma
from sklearn.cluster import KMeans

import shapefile
import itertools
import rasterio
import geopandas as gp
import pandas as pd
from shapely.geometry import Point, Polygon, LineString, MultiLineString, MultiPoint
from shapely.ops import nearest_points, linemerge

from Line import *

# might do some multiprocessing?
from multiprocessing import Pool

class Coast:
    """
    Description of object goes here

    """

    def __init__(self, CoastShp="", MinLength=0.):
        
        """
        MDH, June 2019
        """

        print("Coast: Initialising Coast object")

        self.Cell = None
        self.SubCell = None
        self.CMU = None
        self.Method = None
        self.CoastShp = CoastShp
        self.NoCoastLines = 0
        self.CoastLines = []
        self.Contours = []
        self.MLWSLines = []
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
        self.FutureVegEdgeLines = []
        self.FutureMinUncertainty = []
        self.FutureMaxUncertainty = []
        self.FutureMinError = []
        self.FutureMaxError = []
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
        self.UniqueDEMList = []
            
        # some tracking bools
        self.BuiltTransects = False
        self.GotHistoricShorelines = False
        self.SampledDEMs = False
        self.PredictedFutureShorelines = False
        self.MorphologyAnalysed = False

        if CoastShp:
            self.ReadCoastShp(CoastShp, MinLength)
            
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
    def ReadCoastShp(self, CoastShp, MinLength=0.):
        
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
            try:
                X, Y = np.array(Shapes[i].points).T
            except:
                continue
                
            # Set up a line object for each
            ThisLine = Line(str(i), X, Y)
            
            # append to list of coast lines
            if ThisLine.TotalLength > MinLength:
                self.CoastLines.append(ThisLine)
                print("\t Adding", i+1) 
            else:
                print("\t %4d shorther than MinLength of %3d m" % (i+1, MinLength))

        # get new number of coastal segments based on the list built
        self.NoCoastLines = len(self.CoastLines)
        print("Number of coast segments added:", self.NoCoastLines) 

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
    
    def WriteErodedAreaShp(self, ErosionShp, StartYear=2020, Year=2100,Smooth=True):
        
        """
        Writes future shorelines to polygon patches

        MDH, Jan 2020

        """
        
        # print action to screen
        #print("Coast.WriteErodedAreaShp: Writing predicted erosion area to polygon file")
        
        # retrieve future shorelines
        self.GetFutureShoreLines()

        # get lists of lines for year of prediction and most recent shoreline position
        Indices = [i for i, Line in enumerate(self.FutureShoreLines) if Line.Year == Year]
        self.WriteFutureLines = [self.FutureShoreLines[i] for i in Indices]
        Indices = [i for i, Line in enumerate(self.FutureShoreLines) if Line.Year == StartYear]
        self.WriteRecentLines = [self.FutureShoreLines[i] for i in Indices]
        
        # set up files to write
        ErosionFrontShp = ErosionShp.split(".")[0]+"_temp.shp"
        ErosionBackShp = ErosionShp.split(".")[0]+"_temp2.shp"

        # write lines then patches
        self.WriteLinesShp("WriteFutureLines", ErosionBackShp, Smooth)
        self.WriteLinesShp("WriteRecentLines", ErosionFrontShp, Smooth)
        self.WritePatchesShp("WriteFutureLines", "WriteRecentLines", ErosionShp, Smooth)

    def WriteErosionProximityShp(self, ProximityShp, BufferDistance=10., Year=2100, Smooth=True):

        """
        Writes Erosion Proximity polygon patches for a given decade

        MDH, Feb, 2021
        
        """

        # retrieve future shorelines
        self.GetFutureShoreLines()
        Lines = self.GetFutureShoreLinesProximity(BufferDistance)

        # get lists of lines for year of prediction and most recent shoreline position
        Indices = [i for i, Line in enumerate(self.FutureShoreLines) if Line.Year == Year]
        self.WriteFutureLines = [self.FutureShoreLines[i] for i in Indices]
        Indices = [i for i, Line in enumerate(Lines) if Line.Year == Year]
        self.WriteBufferLines = [Lines[i] for i in Indices]
        
        # set up files to write
        ErosionFutureShp = ProximityShp.split(".")[0]+"_temp.shp"
        ErosionBufferShp = ProximityShp.split(".")[0]+"_temp2.shp"

        # write lines then patches
        self.WriteLinesShp("WriteFutureLines", ErosionFutureShp, Smooth)
        self.WriteLinesShp("WriteBufferLines", ErosionBufferShp, Smooth)
        self.WritePatchesShp("WriteFutureLines", "WriteBufferLines", ProximityShp, Smooth)
    
    
    def WriteFutureShorelinesShp(self, FutureShoreLinesShp, Smooth=True):

        """
        Writes the contents of a list of future shoreline objects to polyline shape file

        MDH, June 2019

        Added functionality to write spline of future line prediction to get smoothed
        shape that is faithful to predictions

        MDH, Jan 2020

        """

        # extract future shoreline positions from transects
        self.GetFutureShoreLines()

        # print action to screen
        print("Coast.WriteFutureShorelinesShp: Writing future MHWS line objects to polyline shapefiles")

        # open new shapefile        
        WL = shapefile.Writer(FutureShoreLinesShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Cell','C', 2, 0], ['SubCell','C', 2, 0], ['Line_ID', 'C', 20, 0],['Year','N', 4, 0],['Method','C', 5, 0]]
        WL.fields = self.Fields[1:] 

        for Line in self.FutureShoreLines:
            
            if Smooth:
                Line.SmoothLine(WindowSize=11)

            # Find Loops
            Line.MakeSimple()
                
            # get line node positions
            # why are we not just recalling Line.SmoothLine here? What is different?
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
            if self.Method == None:
                import pdb
                pdb.set_trace()
             
            Record = [str(Line.Cell), str(Line.SubCell),str(Line.ID),str(Line.Year), str(self.Method)]

            # write line and record
            WL.line(WriteLine)
            WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(FutureShoreLinesShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteFutureUncertaintyShp(self, UncertaintyShp, Year=2100):

        """
        Writes future shoreline uncertainty estimates to a polygon
        for a particular year

        MDH, March 2020

        """
        
        self.FutureMinUncertainty = []
        self.FutureMaxUncertainty = []
        
        # predict and extract future shoreline positions from transects
        self.PredictFutureShorelinesUncertainty(Year)
        self.GetFutureShorelineUncertainty(Year)

        # print action to screen
        print("Coast.WriteFutureUncertaintyShp: Writing uncertainty area to polygon file")
        
        # set up files to write
        FutureMinShp = UncertaintyShp.split(".")[0]+"_Min.shp"
        FutureMaxShp = UncertaintyShp.split(".")[0]+"_Max.shp"

        # spleen for smooth line?
        
        # write lines then patches
        self.WriteLinesShp("FutureMinUncertainty", FutureMinShp)
        self.WriteLinesShp("FutureMaxUncertainty", FutureMaxShp)
        self.WritePatchesShp("FutureMinUncertainty", "FutureMaxUncertainty", UncertaintyShp)

    def WriteFutureErrorShp(self, ErrorShp, Year=2100):

        """
        Writes future shoreline error estimates to a polygon
        for a particular year

        MDH, October 2020

        """

        # predict and extract future shoreline positions from transects
        self.PredictFutureShorelinesError(Year)
        self.GetFutureShorelineError(Year)

        # print action to screen
        print("Coast.WriteFutureErrorShp: Writing uncertainty area to polygon file %d", Year)

        # set up files to write
        FutureMinShp = ErrorShp.split(".")[0]+"_Min.shp"
        FutureMaxShp = ErrorShp.split(".")[0]+"_Max.shp"

        # spleen for smooth line?
        
        # write lines then patches
        self.WriteLinesShp("FutureMinError", FutureMinShp)
        self.WriteLinesShp("FutureMaxError", FutureMaxShp)
        self.WritePatchesShp("FutureMinError", "FutureMaxError", ErrorShp)

    def WriteFutureVegEdgeShp(self, FutureVegEdgeShp, Smooth=False):

        """
        Writes the contents of a list of future veg edge objects to polyline shape file

        MDH, Feb 2020

        Added functionality to write spline of future line prediction to get smoothed
        shape that is faithful to predictions

        MDH, Jan 2020

        """

        if len(self.FutureVegEdgeLines) == 0:
            self.GetFutureVegEdgeLines()

        # print action to screen
        print("Coast.WriteFutureVegEdgeShp: Writing future veg edge line objects to polyline shapefiles")

        # open new shapefile        
        WL = shapefile.Writer(FutureVegEdgeShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 20, 0],['Year','N', 4, 0]]
        WL.fields = self.Fields[1:] 

        for Line in self.FutureVegEdgeLines:
            
            if Smooth:
                Line.SplineLine()

            # get line node positions
            X, Y = Line.get_XY()
            
            # convert to list for writing to shapefile
            WriteLine = [np.column_stack([X, Y]).tolist()]
            
            # generate record
            Record = [str(Line.ID),str(Line.Year)]

            # write line and record
            WL.line(WriteLine)
            WL.record(*Record) 
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(FutureVegEdgeShp.rstrip("shp")+"prj","w")
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
                    if Intersection.is_empty:
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

    
    def WriteLinesShp(self, DictionaryKey, CoastShp, Smooth=False):
        
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
        print("a")
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0],['Method', 'C', 5, 0]]
        WL.fields = self.Fields[1:] 
        print("b")
        i=0

        for Line in self.__dict__[DictionaryKey]:
            
            print(i)
            i = i+1
            print(Line)
            
            if Smooth:
                Line.SmoothLine(WindowSize=11)
            print("\tc")
            # Find Loops
            Line.MakeSimple()
            print("\td")   
            # get line node positions
            X, Y = Line.get_XY()
            print("\te")
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
            print("\tf")
            # get line node positions
            WriteLine = [np.column_stack([X,Y]).tolist()]
            print("\tg")
            # generate record
            Record = [str(Line.ID),str(self.Method)]
            print("\th")
            # write line and record
            WL.line(WriteLine)
            WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########
            print("\ti")
        # close the shapefiles and clean up
        WL.close()
        print("j")  
        # create the projection file    
        f = open(CoastShp.rstrip("shp")+"prj","w")
        print("k")
        f.write(self.Projection)
        print("l")
        f.close()
        print("m")
    
    def WritePatchesShp(self, DictionaryKey1, DictionaryKey2, PatchShp, Smooth=False):

        """

        Writes polygon patches between two lines to a polygon shapefile

        Dictionary Key refers

        MDH, June 2019

        """

        # print action to screen
        #print("Coast.WritePatchesShp: Writing patch between two lines to a polygon shapefile")

        if len(self.__dict__[DictionaryKey1]) == 0:
            print("Coast.WritePatchesShp (Error): Trying to write from empty list of lines", DictionaryKey1, DictionaryKey2)
            
        # open new shapefile        
        WS = shapefile.Writer(PatchShp,shapeType=shapefile.POLYGON)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Poly_ID', 'C', 3, 0],['Method', 'C', 5, 0]]
        WS.fields = self.Fields[1:] 

        for Line1, Line2 in zip(self.__dict__[DictionaryKey1],self.__dict__[DictionaryKey2]):
            
            # get line node positions
            X1, Y1 = Line1.get_XY()

            if Smooth and len(X1) > 5:

                XSmooth = X1[1:-1]
                YSmooth = Y1[1:-1]
                
                # calculate distance
                Dist = np.zeros(XSmooth.shape)
                Dist[1:] = np.sqrt((XSmooth[1:] - XSmooth[:-1])**2 + (YSmooth[1:] - YSmooth[:-1])**2)
                Dist = np.cumsum(Dist)
                
                # build a spline representation of the line
                Spline, u = splprep([XSmooth, YSmooth], u=Dist, s=0)

                # resample it at smaller distance intervals
                Interp_Dist = np.arange(0, Dist[-1], 1.)
                XSmooth, YSmooth = splev(Interp_Dist, Spline)

                XSmooth = np.insert(XSmooth,0,X1[0])
                YSmooth = np.insert(YSmooth,0,Y1[0])
                X1 = np.append(XSmooth,X1[-1])
                Y1 = np.append(YSmooth,Y1[-1])

            # get line node positions
            X2, Y2 = Line2.get_XY()

            if Smooth and len(X2) > 5:

                XSmooth = X2[1:-1]
                YSmooth = Y2[1:-1]
                # calculate distance
                Dist = np.zeros(XSmooth.shape)
                Dist[1:] = np.sqrt((XSmooth[1:] - XSmooth[:-1])**2 + (YSmooth[1:] - YSmooth[:-1])**2)
                Dist = np.cumsum(Dist)
                
                # build a spline representation of the line
                Spline, u = splprep([XSmooth, YSmooth], u=Dist, s=0)

                # resample it at smaller distance intervals
                Interp_Dist = np.arange(0, Dist[-1], 1.)
                XSmooth, YSmooth = splev(Interp_Dist, Spline)

                XSmooth = np.insert(XSmooth,0,X2[0])
                YSmooth = np.insert(YSmooth,0,Y2[0])
                X2 = np.append(XSmooth,X2[-1])
                Y2 = np.append(YSmooth,Y2[-1])

            # combine, reversing the order of the second line to make a patch
            X = np.concatenate((X1,X2[::-1]))
            Y = np.concatenate((Y1,Y2[::-1]))
            WritePoly = [np.column_stack([X,Y]).tolist()]
            
            # generate record
            Record = [str(Line1.ID), str(self.Method)]

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
        print("Coast.WriteTransectsShp: Writing coastal transects and attributes to a shapefile")

        # open new shapefile        
        WL = shapefile.Writer(TransectsShp,shapeType=shapefile.POLYLINE)
        
        # Check length of extreme water levels
        if len(self.ExtremeWaterLevels) != 3:
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
    
    def WriteFutureTransectsShp(self, TransectsShp):

        """
        Writes the transects of a Coast object to polyline shape file

        builds a large attribute table with all future shoreline info

        MDH, Sept 2020

        """

        # print action to screen
        print("Coast.WriteFutureTransectsShp: Writing coastal transects and attributes to a shapefile")

        # open new shapefile        
        WL = shapefile.Writer(TransectsShp,shapeType=shapefile.POLYLINE)
        
        # Check length of extreme water levels
        if len(self.ExtremeWaterLevels) != 3:
            self.ExtremeWaterLevels = [[],[],[]]

        # Create Fields
        Fields = [('DeletionFlag','C',1,0), 
        ['Cell', 'C', 3, 0], ['SubCell', 'C', 3, 0], ['CMU','C', 20, 0],
        ['LineID', 'N', 3, 0], ['TransectID', 'N', 5, 0], ['Min_Rate','N', 6, 4], ['Max_Rate','N', 6, 4], ['Hist_Rate','N', 6, 4], 
        ['CalibYr','N', 4, 0], ['BaseLYr','N', 4, 0], ['BaseLSrc','C', 50, 0], 
        ['Extrap2050','N', 6, 4], ['Extrap2100','N', 6, 4], ['FirstEYr','N',4, 4],
        ['Dist_2030', 'N', 6, 4], ['Rate_2030', 'N', 6, 4], 
        ['Dist_2040', 'N', 6, 4], ['Rate_2040', 'N', 6, 4], 
        ['Dist_2050', 'N', 6, 4], ['Rate_2050', 'N', 6, 4], 
        ['Dist_2060', 'N', 6, 4], ['Rate_2060', 'N', 6, 4], 
        ['Dist_2070', 'N', 6, 4], ['Rate_2070', 'N', 6, 4], 
        ['Dist_2080', 'N', 6, 4], ['Rate_2080', 'N', 6, 4], 
        ['Dist_2090', 'N', 6, 4], ['Rate_2090', 'N', 6, 4], 
        ['Dist_2100', 'N', 6, 4], ['Rate_2100', 'N', 6, 4], 
        ['RCP85_2100', 'N', 4, 3],
        ['DC1_SvEn_B','N', 4, 0], ['DC1_SvEn_C','N', 4, 0], 
        ['DC1_DistV','N', 6, 4], ['DC1_RateBC','N', 6, 4],
        ['OS_2020_Yr','N',4,0], ['Method','C', 5, 0]
        ]
        
        WL.fields = Fields[1:]

        
        for Line in self.CoastLines:
            for Transect in Line.Transects:

                if Transect.Future:
                    # get transect node positions
                    X, Y = Transect.get_XY()
                    
                    WriteTransect = [np.column_stack([X,Y]).tolist()]
                    
                    if not Transect.DC1:
                        Transect.DC1 = ["","","",""]
                    else:
                        try:
                            Transect.DC1[3] = Transect.DC1[2]/(Transect.DC1[1]-Transect.DC1[0])
                        except:
                            Transect.DC1 = ["","","",""]
                    
                    # Create the record this could become a function in transect object...
                    Record = [str(self.Cell), str(self.SubCell), str(self.CMU), str(Line.ID), str(Transect.ID),
                                Transect.MinChangeRate, Transect.MaxChangeRate, Transect.ChangeRate, 
                                Transect.CalibrationYear, Transect.HistoricShorelinesYears[-1], Transect.HistoricShorelinesSources[-1], 
                                Transect.get_ExtrapDistance(2050), Transect.get_ExtrapDistance(2100), Transect.get_FirstFutureErosionYear(),
                                Transect.get_FuturePositionChange(2020, 2030), Transect.get_FutureRate(2020, 2030),
                                Transect.get_FuturePositionChange(2030, 2040), Transect.get_FutureRate(2030, 2040),
                                Transect.get_FuturePositionChange(2040, 2050), Transect.get_FutureRate(2040, 2050),
                                Transect.get_FuturePositionChange(2050, 2060), Transect.get_FutureRate(2050, 2060),
                                Transect.get_FuturePositionChange(2060, 2070), Transect.get_FutureRate(2060, 2070),
                                Transect.get_FuturePositionChange(2070, 2080), Transect.get_FutureRate(2070, 2080),
                                Transect.get_FuturePositionChange(2080, 2090), Transect.get_FutureRate(2080, 2090),
                                Transect.get_FuturePositionChange(2090, 2100), Transect.get_FutureRate(2090, 2100),
                                Transect.FutureSeaLevels[-1],
                                
                                Transect.DC1[0], Transect.DC1[1], Transect.DC1[2], Transect.DC1[3],
                                Transect.OSYear, self.Method]
                    
                                
    
                    # write transect and record
                    WL.line(WriteTransect)
                    WL.record(*Record) 
                                    
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(TransectsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def WriteStormImpactTransectsShp(self, TransectsShp, Cell):
        
        """
        Write Tranects with storm impact scale data to shapefile
        
        NH, Novembeer 2023
        
        """
        
        print("Coast.WriteStormImpactTransectsShp: Writing coastal transects and storm impact data to shapefile for Cell", Cell)
        
        # open new shapefile        
        WL = shapefile.Writer(TransectsShp,shapeType=shapefile.POLYLINE)
        
        # Create Fields
        Fields = [('DeletionFlag','C',1,0), 
        ['Cell', 'C', 4, 0], ['LineID', 'N', 3, 0], ['TransectID', 'N', 5, 0], ['ID', 'C', 12, 0],
        ['Shingle', 'B', 7, 0],
        ['Hist_Rate','N', 5, 2],
        ['Slope_Int','N', 5, 3], 
        ['H_Hs','N', 5, 2],['H_Tp','N', 5, 2], ['H_Diss','B', 7, 0], ['H_R2','N', 5, 2], ['H_setup','N', 5, 2], 
        ['H_ESL_c3','N', 5, 2], ['H_TWL','N', 5, 2], ['H_TWL_su','N', 5, 2], 
        ['H_Toe','N', 5, 2],['H_Crest','N', 5, 2],
        ['H_SIS', 'C', 14, 0],['H_HRoom','N', 5, 2], ['Barr_Vol','N', 5, 2], 
        ['Hint_Elev','N', 5, 2], ['Hint_Slope','N', 5, 2],
        ['Ass1_Dist','N', 5, 2], ['Ass1_Elev','N', 5, 2], ['Rd1_Dist','N', 5, 2], ['Rd1_Elev','N', 5, 2],
        ['Rail1_Dist','N', 5, 2], ['Rail1_Elev','N', 5, 2], ['Prop1_Dist','N', 5, 2], ['Prop1_Elev','N', 5, 2],
        ['M45_Hs','N', 5, 2],['M45_Tp','N', 5, 2], ['M45_Diss','B', 7, 0], ['M45_R2','N', 5, 2], ['M45_setup','N', 5, 2], 
        ['M45_ESL_c3','N', 5, 2], ['M45_TWL','N', 5, 2], ['M45_TWL_su','N', 5, 2], 
        ['M45_Toe','N', 5, 2],['M45_Crest','N', 5, 2],['M45_Drown','B', 7, 0],
        ['M45_SIS', 'C', 14, 0],['M45_HRoom','N', 5, 2],
        ['E45_Hs','N', 5, 2],['E45_Tp','N', 5, 2], ['E45_Diss','B', 7, 0], ['E45_R2','N', 5, 2], ['E45_setup','N', 5, 2], 
        ['E45_ESL_c3','N', 5, 2], ['E45_TWL','N', 5, 2], ['E45_TWL_su','N', 5, 2], 
        ['E45_Toe','N', 5, 2],['E45_Crest','N', 5, 2],['E45_Drown','B', 7, 0],
        ['E45_SIS', 'C', 14, 0],['E45_HRoom','N', 5, 2],
        ['M85_Hs','N', 5, 2],['M85_Tp','N', 5, 2], ['M85_Diss','B', 7, 0], ['M85_R2','N', 5, 2], ['M85_setup','N', 5, 2], 
        ['M85_ESL_c3','N', 5, 2], ['M85_TWL','N', 5, 2], ['M85_TWL_su','N', 5, 2], 
        ['M85_Toe','N', 5, 2],['M85_Crest','N', 5, 2],['M85_Drown','B', 7, 0],
        ['M85_SIS', 'C', 14, 0],['M85_HRoom','N', 5, 2],
        ['E85_Hs','N', 5, 2],['E85_Tp','N', 5, 2], ['E85_Diss','B', 7, 0], ['E85_R2','N', 5, 2], ['E85_setup','N', 5, 2], 
        ['E85_ESL_c3','N', 5, 2], ['E85_TWL','N', 5, 2], ['E85_TWL_su','N', 5, 2], 
        ['E85_Toe','N', 5, 2],['E85_Crest','N', 5, 2],['E85_Drown','B', 7, 0],
        ['E85_SIS', 'C', 14, 0],['E85_HRoom','N', 5, 2]
        ]
        
        WL.fields = Fields[1:]
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # get transect node positions
                X, Y = Transect.get_XY()
                
                WriteTransect = [np.column_stack([X,Y]).tolist()]

                # Create the record this could become a function in transect object...
                if Transect.Barrier:
                    Record = [str(Cell), str(Line.ID), str(Transect.ID), str(Cell) + "_" + str(Line.ID) + "_" + str(Transect.ID),
                                Transect.Shingle,
                                Transect.Hist_Rate,                
                                Transect.IntertidalSlope, 
                                Transect.H_Hs_p99, Transect.H_Tp_p99, Transect.H_Dissipative, Transect.H_R2, Transect.H_setup, 
                                Transect.H_ESL_c3, Transect.H_TWL, Transect.H_TWL_setup,
                                Transect.H_FrontToe, Transect.H_Crest,
                                Transect.H_StormImpactScale, Transect.H_Headroom, Transect.BarrierVolume, 
                                Transect.HinterlandElev, Transect.HinterlandSlope,
                                Transect.FirstAssetDist, Transect.FirstAssetElev, Transect.FirstRoadDist, Transect.FirstRoadElev,
                                Transect.FirstRailDist, Transect.FirstRailElev, Transect.FirstPropertyDist, Transect.FirstPropertyElev,
                                Transect.M45_Hs_p99, Transect.M45_Tp_p99, Transect.M45_Dissipative, Transect.M45_R2, Transect.M45_setup, 
                                Transect.M45_ESL_c3, Transect.M45_TWL, Transect.M45_TWL_setup,
                                Transect.M45_FrontToe, Transect.M45_Crest, Transect.M45_BarrierDrowning,
                                Transect.M45_StormImpactScale, Transect.M45_Headroom,
                                Transect.E45_Hs_p99, Transect.E45_Tp_p99, Transect.E45_Dissipative, Transect.E45_R2, Transect.E45_setup, 
                                Transect.E45_ESL_c3, Transect.E45_TWL, Transect.E45_TWL_setup,
                                Transect.E45_FrontToe, Transect.E45_Crest, Transect.E45_BarrierDrowning, 
                                Transect.E45_StormImpactScale, Transect.E45_Headroom,
                                Transect.M85_Hs_p99, Transect.M85_Tp_p99, Transect.M85_Dissipative, Transect.M85_R2, Transect.M85_setup, 
                                Transect.M85_ESL_c3, Transect.M85_TWL, Transect.M85_TWL_setup,
                                Transect.M85_FrontToe, Transect.M85_Crest, Transect.M85_BarrierDrowning, 
                                Transect.M85_StormImpactScale, Transect.M85_Headroom,
                                Transect.E85_Hs_p99, Transect.E85_Tp_p99, Transect.E85_Dissipative, Transect.E85_R2, Transect.E85_setup, 
                                Transect.E85_ESL_c3, Transect.E85_TWL, Transect.E85_TWL_setup,
                                Transect.E85_FrontToe, Transect.E85_Crest, Transect.E85_BarrierDrowning, 
                                Transect.E85_StormImpactScale, Transect.E85_Headroom]
                else:
                    Record = [str(Cell), str(Line.ID), str(Transect.ID), str(Cell) + "_" + str(Line.ID) + "_" + str(Transect.ID),
                                Transect.Shingle,
                                Transect.Hist_Rate,                
                                Transect.IntertidalSlope,
                                Transect.H_Hs_p99, Transect.H_Tp_p99, Transect.H_Dissipative, Transect.H_R2, Transect.H_setup, 
                                Transect.H_ESL_c3, Transect.H_TWL, Transect.H_TWL_setup,
                                "", "",
                                Transect.H_StormImpactScale, "", "", 
                                "", "",
                                Transect.FirstAssetDist, Transect.FirstAssetElev, Transect.FirstRoadDist, Transect.FirstRoadElev,
                                Transect.FirstRailDist, Transect.FirstRailElev, Transect.FirstPropertyDist, Transect.FirstPropertyElev,
                                Transect.M45_Hs_p99, Transect.M45_Tp_p99, Transect.M45_Dissipative, Transect.M45_R2, Transect.M45_setup, 
                                Transect.M45_ESL_c3, Transect.M45_TWL, Transect.M45_TWL_setup,
                                "", "",  "",
                                Transect.M45_StormImpactScale, "",
                                Transect.E45_Hs_p99, Transect.E45_Tp_p99, Transect.E45_Dissipative, Transect.E45_R2, Transect.E45_setup, 
                                Transect.E45_ESL_c3, Transect.E45_TWL, Transect.E45_TWL_setup,
                                "", "", "",
                                Transect.E45_StormImpactScale, "", 
                                Transect.M85_Hs_p99, Transect.M85_Tp_p99, Transect.M85_Dissipative, Transect.M85_R2, Transect.M85_setup, 
                                Transect.M85_ESL_c3, Transect.M85_TWL, Transect.M85_TWL_setup,
                                "", "", "",
                                Transect.M85_StormImpactScale, "", 
                                Transect.E85_Hs_p99, Transect.E85_Tp_p99, Transect.E85_Dissipative, Transect.E85_R2, Transect.E85_setup, 
                                Transect.E85_ESL_c3, Transect.E85_TWL, Transect.E85_TWL_setup,
                                "", "", "", 
                                Transect.E85_StormImpactScale, ""]

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

    def WriteTransectsCSV(self, Folder=os.getcwd(), Filename="", Swath=False):

        """

        Writes all transects to csv files in the folder specified or
        by default in the current working directory

        args: Folder in which to put files

        MDH, July 2019
        
        NH modification Octber 2023:
        - Add Filename
        - Add flag Swath for saving additional swath data

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
                if Swath:
                    Transect.WriteSwath(Folder, Filename)
                else:
                    Transect.Write(Folder, Filename)

                # update counter
                CurrentTransect += 1

        print("")

    def WriteBarriersTextFile(self, Filename, delimiter=","):
        
        """
        MDH, July 2020
        """
        
        print("Coast.WriteBarriersTextFile: Writing transects barrier toe and crest elevations to .csv file")
        
        # define filename and open for writing
        f = open(Filename,'w')
        
        # write headers
        f.write("LineID" + delimiter + "TransectID" + delimiter + "FrontToeElev" + delimiter + "BackToeElev" + delimiter + "FrontTopElev" + delimiter + "CrestElev" + "\n")#"ToeWidth" + delimiter + "Volume" + "\n")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                if Transect.Barrier:
                    Width, Volume = Transect.ExtractBarrierWidthVolume()
                    f.write(str(Line.ID) + delimiter)
                    f.write(str(Transect.ID) + delimiter)
                    f.write(str(Transect.Elevation[Transect.FrontToeInd]) + delimiter)
                    f.write(str(Transect.Elevation[Transect.BackToeInd]) + delimiter)
                    f.write(str(Transect.Elevation[Transect.FrontTopInd]) + delimiter)
                    f.write(str(Transect.Elevation[Transect.CrestInd]) + "\n") #delimiter)
                    #f.write(str(Width) + delimiter)
                    #f.write(str(Volume) + "\n")
                else:
                    print(f"\t{Transect.LineID} {Transect.ID}: Not a barrier")
                
        f.close()
        
    def WriteSlopesTextfile(self, Filename, delimiter=","):
        
        """
        NH, November 2023
        """
        
        # define filename and open for writing
        f = open(Filename,'w')
        
        # write headers
        f.write("LineID" + delimiter + "TransectID" + delimiter + "ForeshoreSlope" + delimiter + "IntertidalSlope" + "\n")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                f.write(str(Line.ID) + delimiter)
                f.write(str(Transect.ID) + delimiter)
                f.write(str(Transect.ForeshoreSlope) + delimiter)   # slope between 0 m and MHWS (interpolated elevations)
                f.write(str(Transect.IntertidalSlope) + "\n")       # slope between MHWSIntersect and MLWSIntersect (sampled elevations)
                
        f.close()
        
    def WriteSlopesDuneParamsTextfile(self, Filename, delimiter=","):
        
        """
        Writes all transect slopes and dune parameters to .csv file
        
        NH, Novembeer 2023
        
        """
        
        print("Coast.WriteSlopesDuneParamsTextfile: Writing transects slopes, barrier toe and crest elevations to .csv file")
        
        # define filename and open for writing
        f = open(Filename,'w')
        
        # write headers
        f.write("LineID" + delimiter + "TransectID" + delimiter + "IntertidalSlope" + delimiter +\
                "FrontToeElev" + delimiter + "BackToeElev" + delimiter + "FrontTopElev" + delimiter + "BackTopElev" + delimiter + "CrestElev" + delimiter +\
                "FrontToeDist" + delimiter + "BackToeDist" + delimiter + "FrontTopDist" + delimiter + "BackTopDist" + delimiter + "CrestDist" + delimiter +\
                "CliffToeDist" + delimiter + "CliffTopDist" + "\n")
                
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                f.write(str(Line.ID) + delimiter)
                f.write(str(Transect.ID) + delimiter)
                f.write(str(Transect.IntertidalSlope) + delimiter)      # slope between MHWSIntersect and MLWSIntersect
                #f.write(str(Transect.ForeshoreSlope) + delimiter)       # slope between 0 m and MHWS (interpolated elevations)
                if Transect.Barrier:
                    f.write(str(Transect.H_FrontToe) + delimiter)
                    f.write(str(Transect.H_BackToe) + delimiter)
                    f.write(str(Transect.H_FrontTop) + delimiter)
                    f.write(str(Transect.H_BackTop) + delimiter)
                    f.write(str(Transect.H_Crest) + delimiter)
                    f.write(str(Transect.Distance[Transect.FrontToeInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.BackToeInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.FrontTopInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.BackTopInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.CrestInd]) + delimiter) # "\n")
                else:
                    f.write("NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + \
                            "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter) #"\n")
                            
                if Transect.Cliff:
                    f.write(str(Transect.Distance[Transect.CliffToeInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.CliffTopInd]) + "\n")
                else:
                    f.write("NaN" + delimiter + "NaN" + "\n")
                    
        f.close()
        
    def WriteSlopesDuneParSISTextfile(self, Filename, Cell, delimiter=","):
        
        """
        Writes all transect slopes and dune parameters to .csv file
        Water levels and storm impacts for Historical (present day) scenario
        
        Input parameters: Filename = output filename; Cell = coastal cell name
        
        NH, Novembeer 2023
        Revised July 2024
        
        """
        
        print("Coast.WriteSlopesDuneParSISTextfile: Writing transects slopes, barrier toe and crest elevations and water levels to .csv file")
        
        # define filename and open for writing
        f = open(Filename,'w')
        
        # write headers
        f.write("Cell" + delimiter + "LineID" + delimiter + "TransectID" + delimiter + "ID" + delimiter + "IntertidalSlope" + delimiter + "Shingle" + delimiter +\
                "MHWS" + delimiter + "H_ESL_c3" + delimiter + "H_R2" + delimiter + "H_TWL" + delimiter + "H_TWL_setup" + delimiter +\
                "H_Hs" + delimiter + "H_Tp" + delimiter + "H_Steepness" + delimiter + "H_Iribarren" + delimiter +\
                "SeawardMask" + delimiter + "LandwardMask" + delimiter +\
                "FrontToeElev" + delimiter + "BackToeElev" + delimiter + "FrontTopElev" + delimiter + "BackTopElev" + delimiter + "CrestElev" + delimiter +\
                "FrontToeDist" + delimiter + "BackToeDist" + delimiter + "FrontTopDist" + delimiter + "BackTopDist" + delimiter + "CrestDist" + delimiter +\
                "StormRegime" + delimiter + "CliffToeDist" + delimiter + "CliffTopDist" + delimiter + "Asset1Dist" + delimiter + "Asset1Elev" + "\n")
                
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                f.write(str(Cell) + delimiter)
                f.write(str(Line.ID) + delimiter)
                f.write(str(Transect.ID) + delimiter)
                f.write(str(Cell) + "_" + str(Line.ID) + "_" + str(Transect.ID) + delimiter)
                f.write(str(Transect.IntertidalSlope) + delimiter)      # slope between MHWSIntersect and MLWSIntersect
                f.write(str(Transect.Shingle) + delimiter)
                f.write(str(Transect.MHWS) + delimiter)
                f.write(str(Transect.H_ESL_c3) + delimiter)
                f.write(str(Transect.H_R2) + delimiter)
                f.write(str(Transect.H_TWL) + delimiter)
                f.write(str(Transect.H_TWL_setup) + delimiter)
                f.write(str(Transect.H_Hs_p99) + delimiter)
                f.write(str(Transect.H_Tp_p99) + delimiter)
                f.write(str(Transect.H_WaveSteepness) + delimiter)
                f.write(str(Transect.H_Iribarren) + delimiter)
                f.write(str(Transect.SeawardMask) + delimiter)
                f.write(str(Transect.LandwardMask) + delimiter)
                
                if Transect.Barrier:
                    f.write(str(Transect.H_FrontToe) + delimiter)
                    f.write(str(Transect.H_BackToe) + delimiter)
                    f.write(str(Transect.H_FrontTop) + delimiter)
                    f.write(str(Transect.H_BackTop) + delimiter)
                    f.write(str(Transect.H_Crest) + delimiter)
                    f.write(str(Transect.Distance[Transect.FrontToeInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.BackToeInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.FrontTopInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.BackTopInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.CrestInd]) + delimiter)
                else:
                    f.write("NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + \
                            "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter + "NaN" + delimiter)
                
                f.write(str(Transect.H_StormImpactScale) + delimiter)
                
                if Transect.Cliff:
                    f.write(str(Transect.Distance[Transect.CliffToeInd]) + delimiter)
                    f.write(str(Transect.Distance[Transect.CliffTopInd]) + delimiter)
                else:
                    f.write("NaN" + delimiter + "NaN" + delimiter)
                    
                if Transect.AssetPresent:
                    f.write(str(Transect.FirstAssetDist) + delimiter)
                    f.write(str(Transect.FirstAssetElev) + "\n")
                else:
                    f.write("NaN" + delimiter + "NaN" + "\n")
                    
        f.close()
    
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

    def MergeCoastLines(self, SnapDistance=0.1):

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
        SimplifiedMultiLine = MultiLine.simplify(0.2)

        # check geom_type before attempting merge
        if SimplifiedMultiLine.geom_type == "MultiLineString": 
            MergedLine = linemerge(SimplifiedMultiLine)
        else:
            MergedLine = SimplifiedMultiLine

        #reset object
        self.CoastLines = []

        # add line or multiple lines depending on result of merge
        if MergedLine.geom_type == "LineString":
            
            # get x and y and add to CoastLine object as Line
            X, Y = MergedLine.xy
            self.CoastLines.append(Line("0", X, Y))
            
        elif MergedLine.geom_type == "MultiLineString":
            
            # loop through lines in MultiLineString
            # NH change to fix compile error: MultiLineString not iterable. Original: for i, TempLine in enumerate(MergedLine):
            i = 0
            for TempLine in MergedLine.geoms:
                
                # get x and y and add to CoastLine object as Line
                X, Y = TempLine.xy
                self.CoastLines.append(Line(str(i), X, Y))
                i = i+1

        else:
            print("Geometry not recognised!")
            sys.exit()
        
        # update no of coastlines
        self.NoCoastLines = len(self.CoastLines)

    def SmoothCoastLines(self, WindowSize=1001, NoSmooths=2, Resample=True, NodeSpacing=5., PolyOrder=4):
        
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
                
                if Resample:
                    Line.ResampleNodes(NodeSpacing)
                    
                # smooth the line
                Line.SmoothLine(WindowSize, PolyOrder)

                

    def SplineCoastLines(self):
        
        """
        Splines and resamples the CoastLines contained in Coast object
        Wrapper to the function in the Line object
        
        MDH, March 2020

        """

        print("Coast: Generating Spline of CoastLines")

        for Line in self.CoastLines:
            
            # smooth the line
            Line.SplineLine()


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
            self.GenerateTransects(self.TransectsSpacing, self.TransectsLength2Sea, self.TransectsLength2Land)

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

    def CheckOrientation(self, ShorelineShp, OffshoreShp):

        """
        Wrapper to function in the line object to check and correct coast orientation
        relative to a shoreline and a deeper contour e.g. a bathy line or MLWS

        MDH, May 2020

        """

        print("Coast.CheckOrientation: Checking CoastLine Orientation Geometry")
        
        # generate transects along each line
        for Line in self.CoastLines:
            
            # generate transects along each line
            Line.CheckLineOrientation(ShorelineShp, OffshoreShp)

    # function to do something    
    def GenerateTransects(self, TransectSpacing, TransectLength2Sea=5000, TransectLength2Land=5000, CheckTopology=True):
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

    def GetShorefaceSlopes(self,BathyShp):
        
        """
        
        Wrapper to the function in the Line object
        
        MDH, August 2020
    
        """
        print("Coast.GetShorefaceSlope: Finding distance between shoreline and -10m bathy contour to calculate slope")
        
        for Line in self.CoastLines:
            Line.GetShorefaceSlope(BathyShp)

    def GetShorefaceSlopesMLWS(self):

        """

        Wrapper to function in the Transect object

        MDH, Dec 20202

        """
        
        print("Coast.GetShorefaceSlopeMLWS: Finding distance between shoreline and -10m bathy contour to calculate slope")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.CalculateIntertidalSlope()            
            
    def GetIntertidalSlopes(self):
        """
        
        Function to extract the slope between MHWS and MLWS node for each transect.
        If no MLWS intersect, use nearest MLWS node (from ExtractMLWS()). 
        
        Wrapper to function in the Transect object
        
        NH Spetembeer 2023
        
        """
        
        print("Coast.GetIntertidalSlopes: Finding distance between MHWSIntersect and MLWSIntersect to calculate slope")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.CalculateIntertidalSlope3()  
                
    def GetForeshoreSlopes(self):
    
        """
        Function to extract the upper shoreface slope for each transect
        between the 0 m and MHWS elevations. 
        Uses Transect.Elevation, so slopes can be from either the sampeld DTM elevations,
        or the interpolated swath elevations.
        
        NH, October 2023
        
        """
        
        print("Coast.GetForeshoreSlopes: Slope = dz/dx between 0 m and MHWS elevation")
        
        # Extract indexes
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                ihigh = Transect.ExtractIndex(Elev=Transect.MHWS, Landward=False)
                ilow = Transect.ExtractIndex(Elev=0.0, Landward=True)
                
                # check indexes valid
                if (ihigh == -1 or ilow == -1):
                    print(f"\t{Transect.LineID}, {Transect.ID}: Indexes not valid!", ihigh, ilow)
                    Transect.ForeshoreSlope = -1
                    continue
                if ihigh < ilow:
                    print(f"\t{Transect.LineID}, {Transect.ID}: MHWS index < coastline index!")
                    Transect.ForeshoreSlope = -1
                    continue
                
                # Calculate slopes
                dz = Transect.Elevation[ihigh] - Transect.Elevation[ilow]
                dx = Transect.Distance[ihigh] - Transect.Distance[ilow]
                
                # Catch divide by zero
                if dx == 0:
                    print(f"\t{Transect.LineID}, {Transect.ID}: \tdx = 0!")
                    Transect.ForeshoreSlope = -1
                    continue
                    
                else:
                    Transect.ForeshoreSlope = dz/dx
                
                #if __debug__:
                    #print(f"\t{Transect.LineID}, {Transect.ID}: \tihigh={ihigh}, ilow={ilow}, \tdz={dz}, \tdx={dx}, \tslope={Transect.ForeshoreSlope}")
        
    def CheckForeshoreSlopes(self):
    
        """
        Check for invalid Transect.ForeshoreSlopes (negative)
        Set to Transect.IntertidalSlope, if this is valid
        Else, set to None and throw exception
        
        NH, Jan 2024
    
        """
        
        print("Coast.CheckForeshoreSlopes: Checking foreshoreslopes are greater than 0")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
            
                # Foreshoreslope could not be extracted, or is actually negative (also wrong)
                if Transect.ForeshoreSlope < 0:
                    # if valid IntertidalSlope, copy to ForeshoreSlope
                    if Transect.IntertidalSlope > 0:
                        Transect.ForeshoreSlope = Transect.IntertidalSlope
                        print(f"\t{Transect.LineID}, {Transect.ID}: \tForeshoreSlope set to IntertidalSlope = {Transect.ForeshoreSlope}")
                    else:
                        Transect.ForeshoreSlope = None
                        print(f"\t{Transect.LineID}, {Transect.ID}: No valid foreshore/intertidal slopes!!")
                        sys.exit()
        
    
    def GenerateTransectsBetweenContoursShp(self, ContourShp1, ContourShp2, Distance2Sea=8000., Distance2Land=8000., TransectSpacing=20., CheckTopology=True):
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
        print("Coast.GenerateTransectsBetweenContoursShp: Generating CoastLine transects perpendicular to the coast")

        self.TransectsSpacing = TransectSpacing
        
        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateTransectsBetweenContours(ContourShp1,ContourShp2,TransectSpacing,Distance2Sea,Distance2Land,CheckTopology)

    def GenerateMidpointLinesBetweenContoursShp(self, ContourShp1, ContourShp2, Distance2Sea=8000., Distance2Land=8000., TransectSpacing=20., CheckTopology=True):
        """
        Wrapper to the function in the Line object

        Generates a midpoint line between two contours for use as a base line
        required to help adjust for differences between bathy and coastal orientations

        MDH, July 2020

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
        print("Coast.GenerateTransectsBetweenContoursShp: Generating CoastLine transects perpendicular to the coast")

        self.TransectsSpacing = TransectSpacing
        
        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateMidpointLineBetweenContours(ContourShp1,ContourShp2,TransectSpacing,Distance2Sea,Distance2Land,CheckTopology)

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

    def IntersectTransectsWithIntertidal(self, IntertidalPolyShp):

        """
        Wrapper function to loop through transects and intersect with 
        a polygon defining the intertidal zone

        MDH, June 2020

        """
        print("Coast.IntersectTransectsWithIntertidal: Truncating transects to polygons")
        for Line in self.CoastLines:
            print("Line", Line.ID)
            Line.IntersectTransectsWithIntertidal(IntertidalPolyShp)

    def CheckTransectTopology(self):

        """
        Wrapper function to check for overlapping transects and collect
        Run this after transects have been updated for historical shoreline positions.
        Will then need to rerun historical shoreline position analysis

        MDH, Feb 2020

        """

        print("\nCoast.CheckTransectTopology: Checking for overlapping transects")
        for Line in self.CoastLines:
            Line.FindOverlappingTransects()
            #CheckTransectTopology()

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

    def SampleDC1Data(self,DC1Shp):
        
        """
        Function to extract info from DC1 analysis
        
        MDH, November 2020
        
        """
        
        print("Coast.SampleDC1Data: Sampling data from DC1 to add to transects")
        # read shapefile using geopandas
        GDF = gp.read_file(DC1Shp)
        Lines = GDF['geometry']
        
        if len(Lines) == 0:
            print("No Lines")
            return
        
        # catch situation where only one line
        MultiLines = []

        if len(Lines) == 1:
            MultiLines = Lines[0]

        # deal with invalid geometries on the fly? This is messy!
        else:
            for Line in Lines:
                if not Line:
                    continue
                elif Line.geom_type == "LineString":
                    MultiLines.append(Line)
                elif Line.geom_type == "MultiLineString":
                    for SubLine in Line:
                        if SubLine.geom_type == "LineString":
                            MultiLines.append(SubLine)

            MultiLines = MultiLineString(MultiLines)    
            
        if not MultiLines:
            print("No Lines")
            return
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # extend transect line inland to look for intersection
                #Calculate start and end nodes and generate Transect
                TransectLine = LineString(((Transect.StartNode.X,Transect.StartNode.Y),(Transect.EndNode.X,Transect.EndNode.Y)))
            
                # intersect with historical shoreline
                try:
                    Intersections = TransectLine.intersection(MultiLines)
                except:
                    import pdb
                    pdb.set_trace()
                    
                # catch no intersections and flag for deletion?
                if Intersections.is_empty:
                    Transect.DeleteFlag = True
                    continue

                # check there arent multiple intersections
                # get first intersection if so
                if Intersections.geom_type == "MultiPoint":
                    StartPoint = Point(Transect.StartNode.X, Transect.StartNode.Y)
                    Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersections.geoms]
                    Index = Distances.index(min(Distances))
                    Intersection = Intersections.geoms[Index]
                    
                else:
                    # check if this is a new endnode by intersecting with line from startnode to endnode
                    Intersection = Intersections
                                    
                # use minimum of line.distance to find line
                # need date attribute if rates are to be calculated
                Distances = Lines.distance(Intersection)
                NearestLine = GDF.iloc[Distances.idxmin()]
                
                Transect.DC1 = []
                Transect.DC1.append(int(NearestLine.Surv_End_B))
                Transect.DC1.append(int(NearestLine.Surv_End_C))
                Transect.DC1.append(float(NearestLine.DIST_V))
                Transect.DC1.append(float(NearestLine.Rate_B_C))
                
        
        # sort out delete flags???
                
    def Check_OS_Years(self):
        
        """
        Function to get and populate OS years from smarter 2020 dataset
        """
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.Check_OS_Year()
        
        
    def ExtractHistoricalShorelinePositions(self,HistoricalShorelinesShp,Reset=False, AllowMultiples=False):

        """
        Function to find nearest historic shoreline position on each transect
        and add nodes to transect dictionary by date

        MDH, August 2019

        Parameters
        ----------
        HistoricalShorelineShp : string
            Filename for polyline shapfile containing historical shoreline positions
        Reset : bool
            Resets all historical shoreline positions
        """
        print("Coast.ExtractHistoricalShorelinePositions: Finding historical shoreline positions from ", end="")
        print(Path(HistoricalShorelinesShp).name)

        # set a distance to look inland to check for intersections
        LookDistance = 0.

        # read shapefile using geopandas
        GDF = gp.read_file(HistoricalShorelinesShp)
        Lines = GDF['geometry']
        
        if len(Lines) == 0:
            print("No Lines")
            import pdb
            pdb.set_trace()
            return
        
        # catch situation where only one line
        MultiLines = []

        if len(Lines) == 1:
            MultiLines = Lines[0]

        # deal with invalid geometries on the fly? This is messy!
        else:
            for Line in Lines:
                if not Line:
                    continue
                elif Line.geom_type == "LineString":
                    MultiLines.append(Line)
                elif Line.geom_type == "MultiLineString":
                    for SubLine in Line.geoms:
                        if SubLine.geom_type == "LineString":
                            MultiLines.append(SubLine)

            MultiLines = MultiLineString(MultiLines)    
            #MultiLines = MultiLineString([Line for Line in Lines if Line.geom_type == "LineString"])
            
        if not MultiLines:
            print("No Lines")
            return
        
        for Line in self.CoastLines:
            
            for Transect in Line.Transects:
                
                if Reset:
                    Transect.ResetHistoricShorelines()
                    
                # extend transect line inland to look for intersection
                #Calculate start and end nodes and generate Transect
                X1 = Transect.EndNode.X + LookDistance * np.sin( np.radians( Transect.Orientation ) )
                Y1 = Transect.EndNode.Y + LookDistance * np.cos( np.radians( Transect.Orientation ) )
                TransectLine = LineString(((Transect.StartNode.X,Transect.StartNode.Y),(X1,Y1)))
            
                # intersect with historical shoreline
                Intersections = TransectLine.intersection(MultiLines)
                
                # catch no intersections and flag for deletion? updated all references to GeometryCollection with isempty, CM 09/23
                if Intersections.is_empty:
                    Transect.DeleteFlag = True
                    continue

                # check there arent multiple intersections
                """
                # store multiple intersections if so
                if Intersections.geom_type is "MultiPoint":
                    StartPoint = Point(Transect.StartNode.X, Transect.StartNode.Y)
                    Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersections]
                    Index = Distances.index(min(Distances))
                    Indices = np.argsort(np.array(Distances))
                    Distances = np.array(Distances)[Indices]
                    IntersectionsList = [Intersections[i] for i in Indices]
                    
                else:
                    # check if this is a new endnode by intersecting with line from startnode to endnode
                    Distance = Transect.LineString.distance(Intersections)
                    Intersection = Intersections
                    IntersectionsList = [Intersection,]
                """

                # store multiple intersections if so
                if Intersections.geom_type == "MultiPoint":
                    CoastPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                    Distances = [IntersectPoint.distance(CoastPoint) for IntersectPoint in Intersections.geoms]
                    Index = Distances.index(min(Distances))
                    Indices = np.argsort(np.array(Distances))
                    Distances = np.array(Distances)[Indices]
                    IntersectionsList = [Intersections.geoms[i] for i in Indices]
                    
                else:
                    # check if this is a new endnode by intersecting with line from startnode to endnode
                    Distance = Transect.LineString.distance(Intersections)
                    Intersection = Intersections
                    IntersectionsList = [Intersection,]
                
                IntersectionYears = []
                
                # loop through intersections and add to struct
                for Intersection in IntersectionsList:
                    #print(Intersection.wkt, end=", ")
                    # use minimum of line.distance to find line
                    # need date attribute if rates are to be calculated
                    Distances = Lines.distance(Intersection)
                    NearestLine = GDF.iloc[Distances.idxmin()]
                    
                    # check it hasnt already been read
                    if "FULLSHP_YR" in NearestLine:
                        IntersectionYears.append(int(NearestLine.FULLSHP_YR))
                    elif "Surv_EndYr" in NearestLine:
                        IntersectionYears.append(int(NearestLine.Surv_EndYr))
                    elif "Surv_End_A" in NearestLine:
                        IntersectionYears.append(int(NearestLine.Surv_End_A))
                    elif "Surv_End_B" in NearestLine:
                        IntersectionYears.append(int(NearestLine.Surv_End_B))
                    elif "Surv_End_C" in NearestLine:
                        IntersectionYears.append(int(NearestLine.Surv_End_C))
                    elif "Surv_End_D" in NearestLine:
                        IntersectionYears.append(int(NearestLine.Surv_End_D))
                    elif "versiondat" in NearestLine:
                        IntersectionYears.append(int(NearestLine.versiondat[0:4]))
                    elif "Year" in NearestLine:
                        IntersectionYears.append(int(NearestLine.Year))
                    elif "YEAR" in NearestLine:
                        IntersectionYears.append(int(NearestLine.YEAR))
                    else:
                        sys.exit("Couldnt find survey year for MHWS historic shoreline position")
                
                # delete intersections for years that already exist?
                if len(IntersectionYears) == 1:
                    if IntersectionYears[0] in Transect.HistoricShorelinesYears:
                        continue
                        
                elif len(IntersectionYears) > 1:
                    Indices = [i for i, Year in enumerate(IntersectionYears) if Year not in Transect.HistoricShorelinesYears]
                    IntersectionsList = [IntersectionsList[i] for i in Indices]
                    IntersectionYears = [IntersectionYears[i] for i in Indices]
                
                if len(IntersectionYears) == 0:
                    continue
                
                if not AllowMultiples:
                    
                    CoastPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                    TempDistances = [IntersectionPoint.distance(CoastPoint) for IntersectionPoint in IntersectionsList]
                    IntersectionIndex = TempDistances.index(min(TempDistances))
                    Intersection = IntersectionsList[IntersectionIndex]
                    Year = IntersectionYears[IntersectionIndex]
                    
                    if Year not in Transect.HistoricShorelinesYears:
                        
                        # add year to transect
                        Index = bisect.bisect(Transect.HistoricShorelinesYears, Year)
                        Transect.HistoricShorelinesYears.insert(Index, Year)
                        
                        # add shoreline position
                        Position = Node(Intersection.x,Intersection.y)
                        Positions = [Position,]
                        Transect.HistoricShorelinesPositions.insert(Index, Positions)
                        
                        # add distance
                        Distances = [Transect.StartNode.get_Distance(Position),]
                        Transect.HistoricShorelinesDistances.insert(Index, Distances)
                        
                        # add source info
                        Transect.HistoricShorelinesSources.insert(Index, Path(HistoricalShorelinesShp).name)
                        
                        # retrieve positional error
                        if Year < 1970:
                            Error = 5.
                        elif Year < 2000:
                            Error = 2.
                        else:
                            Error = 1.
                            
                        # add error
                        Transect.HistoricShorelinesErrors.insert(Index, Error)
                        
                    else:
                        
                        # find and either add or replace depending on proximity
                        Index = Transect.HistoricShorelinesYears.index(Year)
                        Position = Node(Intersection.x,Intersection.y)
                        
                        MinDistance = 1000.
                        
                        for OldPosition in Transect.HistoricShorelinesPositions[Index]:
                            Distance = OldPosition.get_Distance(Position)
                            if Distance < MinDistance:
                                MinDistance = Distance
                        
                        if MinDistance > 1.:
                        
                            # add to transect
                            Transect.HistoricShorelinesPositions[Index].append(Position)
                            Transect.HistoricShorelinesDistances[Index].append(Distance)

                else:
                
                    # loop through unique years
                    UniqueYears = list(set(IntersectionYears))
                    for Year in UniqueYears:
    
                        # retrieve positional error
                        if Year < 1970:
                            Error = 5.
                        elif Year < 2000:
                            Error = 2.
                        else:
                            Error = 1.
    
                        
                        # isolate intersections for this year
                        Indices = [i for i, ThisYear in enumerate(IntersectionYears) if ThisYear == Year]
                        TempIntersectionsList = [IntersectionsList[i] for i in Indices]
                        CoastPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                        TempDistances = [IntersectionPoint.distance(CoastPoint) for IntersectionPoint in TempIntersectionsList]
                        IntersectionIndex = TempDistances.index(min(TempDistances))
                        Intersection = TempIntersectionsList[IntersectionIndex]
    
                        if Year not in Transect.HistoricShorelinesYears:
                            
                            # add year to transect
                            Index = bisect.bisect(Transect.HistoricShorelinesYears, Year)
                            Transect.HistoricShorelinesYears.insert(Index, Year)
                            
                            # add shoreline position
                            Position = Node(Intersection.x,Intersection.y)
                            Positions = [Position,]
                            Transect.HistoricShorelinesPositions.insert(Index, Positions)
                            
                            # add distance
                            Distances = [Transect.StartNode.get_Distance(Position),]
                            Transect.HistoricShorelinesDistances.insert(Index, Distances)
                            
                            # add source info
                            Transect.HistoricShorelinesSources.insert(Index, Path(HistoricalShorelinesShp).name)
                            
                            # add error
                            Transect.HistoricShorelinesErrors.insert(Index, Error)
                            
                        else:
                            
                            # find and either add or replace depending on proximity
                            Index = Transect.HistoricShorelinesYears.index(Year)
                            Position = Node(Intersection.x,Intersection.y)
                            
                            MinDistance = 1000.
                            
                            for OldPosition in Transect.HistoricShorelinesPositions[Index]:
                                Distance = OldPosition.get_Distance(Position)
                                if Distance < MinDistance:
                                    MinDistance = Distance
                            
                            if MinDistance > 1.:
                            
                                # add to transect
                                Transect.HistoricShorelinesPositions[Index].append(Position)
                                Transect.HistoricShorelinesDistances[Index].append(Distance)

                """
                for i, Intersection in enumerate(IntersectionsList):
                    
                    # retrieve year
                    Year = IntersectionYears[i]
                    
                    if Year not in Transect.HistoricShorelinesYears:
                       
                        # add year to transect
                        Index = bisect.bisect(Transect.HistoricShorelinesYears, Year)
                        Transect.HistoricShorelinesYears.insert(Index, Year)
                        
                        # add shoreline position
                        Position = Node(Intersection.x,Intersection.y)
                        Positions = [Position,]
                        Transect.HistoricShorelinesPositions.insert(Index, Positions)
                        
                        # add distance
                        Distances = [Transect.StartNode.get_Distance(Position),]
                        Transect.HistoricShorelinesDistances.insert(Index, Distances)
                        
                        # add source info
                        Transect.HistoricShorelinesSources.insert(Index, Path(HistoricalShorelinesShp).name)
                        
                        # add error
                        Transect.HistoricShorelinesErrors.insert(Index, Error)
                        
                    else:
                        
                        # find and either add or replace depending on proximity
                        Index = Transect.HistoricShorelinesYears.index(Year)
                        Position = Node(Intersection.x,Intersection.y)
                        
                        MinDistance = 1000.
                        
                        for OldPosition in Transect.HistoricShorelinesPositions[Index]:
                            Distance = OldPosition.get_Distance(Position)
                            if Distance < MinDistance:
                                MinDistance = Distance
                        
                        if MinDistance > 1.:
                        
                            # add to transect
                            Transect.HistoricShorelinesPositions[Index].append(Position)
                            Transect.HistoricShorelinesDistances[Index].append(Distance)
                """


    def ExtractMLWS(self, MLWSShp, NearestNode=0):

        """
        Function to find nearest location of MLWS
        from shapefile for each transect

        MDH, December 2020

        Parameters
        ----------
        MLWSShp : string
            Filename for polyline shapfile containing MLWS
        NearestNode : string
            Name of node from which to find the shortest distance to MLWS contour
            If not spcified, use CoastNode.
        
        """
        print("Coast.ExtractMLWS: Finding nearest MLWS position")
        
        # read shapefile using geopandas
        GDF = gp.read_file(MLWSShp)
        
        # get lines geometry
        Lines = GDF['geometry']
        
        # catch situation where only one line
        MultiLines = []

        if len(Lines) == 1:
            MultiLines = Lines[0]

        # deal with invalid geometries on the fly? This is messy!
        else:
            for ThisLine in Lines:
                if not ThisLine:
                    continue
                elif ThisLine.geom_type == "LineString":
                    MultiLines.append(ThisLine)
                elif ThisLine.geom_type == "MultiLineString":
                    for SubLine in ThisLine.geoms:                  # NH: fix compile error "MultiLineString object is not iterable"
                        if SubLine.geom_type == "LineString":
                            MultiLines.append(SubLine)
        
            MultiLines = MultiLineString(MultiLines) # NH fix compile error: "object of type LineString has no len()". Change this to be inside the else statement. 
        
        for ThisLine in self.CoastLines:
            for Transect in ThisLine.Transects:
                
                # NH: check if "NearestNode" specified and exists. If not use CoastNode
                if NearestNode and hasattr(Transect, NearestNode):
                    ThisNode = getattr(Transect, NearestNode)
                else:
                    ThisNode = getattr(Transect, "CoastNode")
                
                # shapely goes here
                BasePoint = Point(ThisNode.X, ThisNode.Y)
                NearestPoint = nearest_points(MultiLines, BasePoint)[0]
                Transect.MLWS = Node(NearestPoint.x,NearestPoint.y)
            
    
    def ExtractIntersection(self, Shp, NodeToSave, MostSeaward=1):
        
        """
        Function to find the intersection between each transect and the given contour.
        If no intersect or no input file, NodeToSave set to (0,0)

        NH September 2023

        Parameters
        ----------
        Shp : string
            Filename for shapefile to intersect with transects
        NodeToSave : string
            Name of transect node in which to save intersect point
        MostSeaward : boolean
            In case of multiple intersections, this defines whether to
            save the most seaward node (MostSeaward=1) or 
            most landward node (MostSeaward=0)
            
        Writes to 
        ---------
        - Transect."NodeToSave" (Node)
        
        Works
        
        """
        
        print("Coast.ExtractIntersection: Finding intersection between each transect and", Shp) 
        
        # Check if file exists. If not, set intersect to (0,0) and return
        shapefile_path = Path(Shp)
        if not shapefile_path.is_file():
            print("\t NO FILE:", Shp, "Setting intersect to (0,0)")
            
            for Line in self.CoastLines:
                for Transect in Line.Transects:
                    Intersection = Point(0,0) 
                    setattr(Transect, NodeToSave, Node(Intersection.x, Intersection.y))
                    
            return
        
        # read shapefile using geopandas
        GDF = gp.read_file(Shp)
        
        # check for empty geometry - case when e.g. no rail within subcell and empty file was saved
        if GDF.empty:
            print("\t NO GEOMETRY:", Shp, "Setting intersect to (0,0)")
            
            for Line in self.CoastLines:
                for Transect in Line.Transects:
                    Intersection = Point(0,0) 
                    setattr(Transect, NodeToSave, Node(Intersection.x, Intersection.y))
                    
            return
        
        # get GeoDataFrame geometry (GeoSeries)
        Vector = GDF['geometry']
        #print("v1=",Vector)
        #print(Vector.geom_type[0])
        #return
        
        # if polygon, use GeoSeries.boundary to get LineString vector of the polygon outline
        if Vector.geom_type[0] == "Polygon":
            Vector = Vector.boundary
            #print("v2=",Vector)
        
        MultiLines = []
        
        for v in Vector:
            if not v:
                continue
            elif v.geom_type == "LineString":
                MultiLines.append(v)
            elif v.geom_type == "MultiLineString":
                for SubLine in v.geoms:
                    if SubLine.geom_type == "LineString":
                        MultiLines.append(SubLine)
    
        MultiLines = MultiLineString(MultiLines) 

        # Find coordinates of intersection between transect and contour. If no intersection (0,0). Save as Transect."NodeToSave"
        for Line in self.CoastLines:
            for Transect in Line.Transects:
        
                # construct linestring and find intersection
                TransectLS = LineString([(Transect.StartNode.X,Transect.StartNode.Y), (Transect.EndNode.X,Transect.EndNode.Y)])
                if TransectLS.intersects(MultiLines):
                    Intersections = TransectLS.intersection(MultiLines)
                    
                    # if more than one intersection, use MostSeaward flag to pick point. StartNode is in the sea. 
                    if Intersections.geom_type == "MultiPoint":
                        #if __debug__:
                            #print(Transect.LineID, Transect.ID, "\t More than one intersection!")
                        StartPoint = Point(Transect.StartNode.X, Transect.StartNode.Y)
                        Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersections.geoms]
                        if MostSeaward:
                            Index = Distances.index(min(Distances))
                        else:
                            Index = Distances.index(max(Distances))
                        Intersection = Intersections.geoms[Index]
                        
                    else:
                        Intersection = Intersections
                        
                else:
                    Intersection = Point(0,0)
                    
                setattr(Transect, NodeToSave, Node(Intersection.x, Intersection.y))
                
                #if __debug__:
                    #ThisNode = getattr(Transect, NodeToSave) 
                    #print(Transect.LineID, Transect.ID, "\t", NodeToSave, Intersection, ThisNode)            
       
    def IntersectShingle(self, Baseline, Shingle):
        """
        Find if transect intersects shingle habitat
        Buffer baseline by 75m. Intersect with Shingle shapefile, save
        Find if transect intersects this 
        If so, set Shingle flag, to be used in extreme runup calc.
        
        NH, Feb 2024
        
        """
        
        print("Coast.IntersectShingle: Finding if intersection between transect and", Shingle) 
        
        buffer_dist = 75.0
        
        # Read in shapefiles as geodataframes using geopandas
        coastline = gp.read_file(Baseline)
        shingle = gp.read_file(Shingle)
        
        #print("Coastline", coastline)
        
        # Buffer baseline by 50 m. This way retains it as a geodataframe
        coastline['geometry'] = coastline.geometry.buffer(buffer_dist)
        #print("Coastline_buffered",coastline)
        #coastline.to_file("coastline_buffered.shp")            # works
        
        # Intersect with Habmos B2 shingle polygon. Both inputs must be geodataframes
        coastal_shingle = gp.overlay(coastline, shingle, how="intersection")
        #print("Coastal shingle=",coastal_shingle['geometry'])
        #coastal_shingle.to_file("coastal_shingle.shp")         # works
        
        # If transect intersects coastal shingle, set flag
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                TransectLS = LineString([(Transect.StartNode.X,Transect.StartNode.Y), (Transect.EndNode.X,Transect.EndNode.Y)])
                # turn into geodataframe to use in gp.overlay
                d = {'geometry':[TransectLS]}
                #print(d)
                transect_gdf = gp.GeoDataFrame(d, crs="EPSG:27700")
                #print(transect_gdf)
                intersect = gp.overlay(coastal_shingle, transect_gdf, how="intersection", keep_geom_type=False) # if keep_geom_type=True, return only geometries of the same geometry type the GeoDataFrame has, if False, return all resulting geometries
                #print(Line.ID,"_",Transect.ID, intersect)
                if intersect.empty:
                    Transect.Shingle = False
                else:
                    Transect.Shingle = True
                    #print("Shingle!", Line.ID,"_",Transect.ID)
        
    def ExtractCoastalAssets(self, Baseline, AssetShp, BufferDist, OutputPath):
        """
        
        Create coastal buffer and intersect with given asset shapefile 
        
        Input Parameters:
        Baseline: MHWS contour shapefile 
        AssetPath: national / regional asset shapefile 
        BufferDist: Distance in meters for the coastal buffer
        
        Output:
        Coastal asset shapefile saved to OutputPath
        
        NH, April 2024
        
        """
        
        print("Coast.ExtractCoastalAssets: Buffering coastline by", BufferDist, "m and extracting intersection with", AssetShp)
        
        # Read in shapefiles as geodataframes using geopandas
        coastline = gp.read_file(Baseline)
        assets = gp.read_file(AssetShp)
        
        # Buffer and dissolve baseline
        coastline['geometry'] = coastline.geometry.buffer(BufferDist)
        dissolved = coastline.dissolve()
        #print("dissolved=",dissolved)        
        
        # Clip assets to buffer
        coastal_assets = gp.clip(assets, dissolved)
        #print("Coastal assets=",coastal_assets)
        
        # Save as coastal asset shapefile
        if coastal_assets.empty:
            print("\tNo coastal assets for", AssetShp)  
        
        print("\tSaving", OutputPath)
        coastal_assets.to_file(OutputPath)              # save, even if empty shapefile
        
    def MergeGeoDataFrames(self, Input1, Input2, Output):
        """
        Merge two input geodataframes and save to output
        
        NH, April 2024
        
        """
        print("Coast.MergeGeoDataFrames:", Input1, Input2, "Save as:", Output)
        
        # Read in shapefiles as geodataframes using geopandas
        gdf1 = gp.read_file(Input1)
        gdf2 = gp.read_file(Input2)
        
        # Merge using pandas concat(). Geopandas append() has been deprecated
        merged = pd.concat([gdf1, gdf2])
        merged.to_file(Output)
    
    def CalculateDistanceToFirstAsset(self):
        """
        Funcion to calculate the distance between the CoastNode and first 
        road / rail / property asset that intersects the transect
        
        Uses Transect.RoadsIntersect, Transect.RailIntersect and Transect.PropertyIntersect
        which are (0,0) for no intersect.
        If no intersect, dist_xxx very large (>900,000), so check before saving.
        
        Save distance as Transect.FirstAssetDist. None if dist > transect length/2.
        Also save individual asset distances.
        
        NH, Mar 2024
        
        """
        print("Coast.CalculateDistanceToFirstAsset: Finding distance from coastline to first road/rail/property")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # Turn Nodes into Points
                CoastPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                RoadPoint = Point(Transect.RoadsIntersect.X, Transect.RoadsIntersect.Y)
                RailPoint = Point(Transect.RailIntersect.X, Transect.RailIntersect.Y)
                PropertyPoint = Point(Transect.PropertyIntersect.X, Transect.PropertyIntersect.Y)
                
                # Use Geopandas distance
                dist_road = CoastPoint.distance(RoadPoint) 
                dist_rail = CoastPoint.distance(RailPoint)
                dist_prop = CoastPoint.distance(PropertyPoint)
                
                # Pick smaller distance, only if on landward part of transect
                dist_asset = min(dist_road, dist_rail, dist_prop)
                Transect.FirstAssetDist = (dist_asset if (dist_asset < Transect.Length/2) else None)
                
                # set flag
                if Transect.FirstAssetDist:
                    Transect.AssetPresent = True
                else:
                    Transect.AssetPresent = False
                
                # Save all asset distances
                Transect.FirstRoadDist = (dist_road if (dist_road < Transect.Length/2) else None)
                Transect.FirstRailDist = (dist_rail if (dist_rail < Transect.Length/2) else None)
                Transect.FirstPropertyDist = (dist_prop if (dist_prop < Transect.Length/2) else None)
                
                #print(Line.ID, Transect.ID, "NearestAsset=", Transect.FirstAssetDist, "flag=", Transect.AssetPresent)
                #print("FirstRoadDist", Transect.FirstRoadDist, "FirstRailDist", Transect.FirstRailDist, "FirstPropertyDist", Transect.FirstPropertyDist)
    
    def my_round(x, base=5.0):
        return base * round(x/base)
    
    def FindAssetElevations(self):
        """
        Use asset distances to find asset elevations.
        First round decimal (exact) distance to nearest 5 m to match Transect.Distance
        Then get index and corresponding sampled interpolated elevation from Transect.Elevtion. 
       
        NH, Mar 2024
       
        """
        
        print("Coast.FindAssetElevations: Finding elevations of first road/rail/property")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                # Landward/seaward transect length. Assumes symmetrical transect, Round to remove any decimals
                TransectLen = round(Transect.Length / 2)
                
                # round to nearest 5m of transect distance vector. As FirstAssetDist is from CoastPoint, add Tlen/2 for distance from transect StartPoint
                if Transect.AssetPresent:
                    dist_asset = Coast.my_round(Transect.FirstAssetDist) + TransectLen
                    idx = (np.where(Transect.Distance == dist_asset))[0]                                    # tuple, with array of matching indices in first element
                    Transect.FirstAssetElev = Transect.Elevation[idx[0]]                                    # first element of matching indexes (should only be one)
                    #print("D=", Transect.Distance)
                    #print("E=", Transect.Elevation)
                    #print(Line.ID, Transect.ID, "\tL1=", Transect.Length, "\tL2=",TransectLen, "\tdist_asset=", dist_asset, "\tidx=", idx)
                    #print(Line.ID, Transect.ID, "\tdist_asset=", dist_asset, "\telev_asset=", Transect.FirstAssetElev)
                   
                # repeat for individual assets
                if Transect.FirstRoadDist:
                    dist_road = Coast.my_round(Transect.FirstRoadDist) + TransectLen
                    idx = (np.where(Transect.Distance == dist_road))[0] 
                    Transect.FirstRoadElev = Transect.Elevation[idx[0]] 
                    #print("\tdist_road=", dist_road, "\telev_road=", Transect.FirstRoadElev)
                
                if Transect.FirstRailDist:
                    dist_rail = Coast.my_round(Transect.FirstRailDist) + TransectLen
                    idx = (np.where(Transect.Distance == dist_rail))[0] 
                    Transect.FirstRailElev = Transect.Elevation[idx[0]] 
                    #print("\tdist_rail=", dist_rail, "\telev_rail=", Transect.FirstRailElev)
                    
                if Transect.FirstPropertyDist:
                    dist_prop = Coast.my_round(Transect.FirstPropertyDist) + TransectLen
                    idx = (np.where(Transect.Distance == dist_prop))[0] 
                    Transect.FirstPropertyElev = Transect.Elevation[idx[0]] 
                    #print("\tdist_prop=", dist_prop, "\telev_prop=", Transect.FirstPropertyElev)
                
                
    
    def SetBarrierSearchWindow(self):
        """
        Function to set the window within which to search for coastal barrier.
        NOTE: Requires transect min length of 200 m.
        
        Uses the nearest coastal asset location to find LandwardMask: 
        - if assets within 200 m of coast, use the most seaward asset location as the landward edge of the 
        barrier search window (to only look for barriers seaward of assets, e.g. Golspie)
        - else if no assets within 200 m of coast, use min elevation between 50 m and 200 m landward
        as the landward edge of the barrier search window (to find wider barriers).
        
        Set SeawardMask to -50 m for now. 
        
        Save to Transect.LandwardMask and Transect.SeawardMask
        
        NH, Mar 2024
        
        """
        print("Coast.SetBarrierSearchWindow: Setting search window for coastal barriers")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                # Landward transect length. Assumes symmetrical transect
                TransectLen = round(Transect.Length / 2)
                
                # Set seaward edge of search 50 m seaward of coastline
                Transect.SeawardMask = TransectLen - 50
                
                # Landward window: If assets present inside potential barrier region, look only seaward of asset
                if (Transect.AssetPresent and Transect.FirstAssetDist < 200):
                    Transect.LandwardMask = round(TransectLen + Transect.FirstAssetDist)
                    #print(Line.ID, Transect.ID, "*1", Transect.LandwardMask)
                else:
                    # If no assets, look seaward of min elevation between 50 m and 200 m (shingle) or 100 m and 200 m landward (sand). 
                    # This copes with wide/narrow/high/low barriers
                    # Sand barriers tend to be wider, and shingle narrower and closer to MHWS
                    dstart = 50 if Transect.Shingle else 100
                    idx = np.where((Transect.Distance > TransectLen+dstart) & (Transect.Distance < TransectLen+200))
                    idx = idx[0]                                                                                # take first element of tuple, which is the array of indexes
                    idx_min_elev = np.argmin(Transect.Elevation[idx]) + idx[0]
                    Transect.LandwardMask = Transect.Distance[idx_min_elev]
                    #print(f"{Line.ID}, {Transect.ID}, *2, idx={idx}, idx_min_elev={idx_min_elev}")
                    #print(Line.ID, Transect.ID, "*2", Transect.LandwardMask)
        
    
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
                        if not val == RSLRDataset.nodata:
                            Transect.HistoricalRSLR = val[0]
                        else:
                            Transect.HistoricalRSLR = 0
                        
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
                        
    def SampleRaster(self, Raster=None, NodeToSample=None, Attrib=None):
    
        """
        Samples raster at the specified node, 
        and saves value to the specified attribute.
        
        Parameters
        ----------
        Raster : string
            Filename of raster to be sampled
        NodeToSample : string
            Name of node containing (x,y) coordinates to be sampled.
            Default is CoastNode
        Attrib : string
            Name of Transect attribute in which to save the sampled raster value
        
        NH, November 2023
        
        Works
        
        """
        
        print(f"Coast.SampleRaster: Sampling raster {Raster} band 0 and saving to Transect.{Attrib}")
        
        # check parameters
        if not Raster:
            raise SystemExit("\tNo raster passed in function call")
        if not NodeToSample:
            NodeToSample = "CoastNode"
        if not Attrib:
            raise SystemExit("\tNo Transect attribute passed in function call")
            
        RasterDataset = rasterio.open(Raster)
        
        # get extent of raster
        XMin = RasterDataset.bounds[0]
        XMax = RasterDataset.bounds[2]
        YMin = RasterDataset.bounds[1]
        YMax = RasterDataset.bounds[3]
        RasterExtent = Polygon([[XMin, YMin], [XMin, YMax], [XMax, YMax], [XMax, YMin]])
        
        print("\tRaster width, height:", RasterDataset.width, RasterDataset.height)
        print("\tRaster bounds:", RasterDataset.bounds)
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
        
                # Check if Transect contains NodeToSample as attribute 
                # If not, continue to next transect as need (x,y) coords to sample.
                if not hasattr(Transect, NodeToSample):
                    print(f"\t{Transect.LineID}_{Transect.ID}: Transect has no attribute", NodeToSample)
                    continue
                
                # get attribute   
                SampleNode = getattr(Transect, NodeToSample) 
                #print(f"\t{Transect.LineID}_{Transect.ID}:{SampleNode}")                
                    
                # check if node inside raster
                SamplePoint = Point(SampleNode.X, SampleNode.Y) 
                if not SamplePoint.within(RasterExtent):
                    print(f"\t{Transect.LineID}_{Transect.ID}: {NodeToSample} outwith {Raster}")
                    continue
                    
                for val in RasterDataset.sample([(SampleNode.X, SampleNode.Y)]):
                    sampled = val[0]
                        
                # check if Transect contains Attrib 
                #if not hasattr(Transect, Attrib):
                #    print(f"\t{Transect.LineID}_{Transect.ID}: Creating {Attrib}")
                    
                setattr(Transect, Attrib, sampled)
                #print("\t",getattr(Transect, Attrib))
        
    
    def SampleNodeElevation(self, NodeToSample, DEMFileList=None):
    
        """
        Samples the DEM elevation of given node for each transect.
        Assigns elevation to Transect."NodeToSample".Z
        
        Parameters
        ----------
        
        NodeToSample: String
            Name of node containing (x,y) coordinates to be sampled.
        DEMFileList: list
            List of unique DEMs associated with this part of the coast.
            
        Writes to
        ---------
        Transect."NodeToSample".Z
        
        NH, September 2023
        
        Works
        
        """
        
        print("Coast.SampleNodeElevation: Sampling DEM for transect node", NodeToSample)
        
        # set up dem file list
        if DEMFileList:
            # check if list and make list if not
            if not isinstance(DEMFileList, list):
                DEMFileList = [DEMFileList,]
            self.UniqueDEMList = DEMFileList

        # loop through DEMs
        for DEM in self.UniqueDEMList:
            
            print("\t" + DEM.split("/")[-1])

            DTM_Dataset = rasterio.open(DEM)
            DTMArray = DTM_Dataset.read(1)
            NCols = DTM_Dataset.width
            NRows = DTM_Dataset.height
            NDV = DTM_Dataset.nodata
            Resolutions = DTM_Dataset.res
            
            # check if we're missing no data
            if not DTM_Dataset.nodata:
                # raise SystemExit("DTM missing no data value") # NH: remove this as .asc files don't have nodata set.
                # NH add print and NDV assignment
                print("\tDTM missing no data value!")
                NDV = -9999

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
            
            for Line in self.CoastLines:
                for Transect in Line.Transects:

                    # check for intersection
                    if not Transect.LineString.intersects(DTM_Extent):
                        continue
                        
                    # Check if Transect contains the passed nodename as attribute 
                    # If not, then return as need (x,y) coords to sample.
                    if not hasattr(Transect, NodeToSample):
                        print("\tError: Transect has no attribute", NodeToSample)
                        return
                        
                    # get attribute   
                    ThisNode = getattr(Transect, NodeToSample)                    
                    
                    # use point to sample elevation if inside DTM, else point zero and elevation zero
                    NodePoint = Point(ThisNode.X, ThisNode.Y) 
                    NodePoint = NodePoint if NodePoint.within(DTM_Extent) else Point((0,0))
                    Coords = [(NodePoint.x, NodePoint.y)]
                 
                    for val in DTM_Dataset.sample(Coords):
                        Elevation = val[0] 
                        #print(Transect.LineID, Transect.ID, "\t", Elevation)

                    # ensure value not overwritten if node is outside current DTM and was sampled previously
                    if not ThisNode.Z: 
                        ThisNode.Z = Elevation
                    
    
    def SampleFutureRSL(self, FutureRSLFolder, RCP=8, Percentile=95, Years=[2020,2030,2040,2050,2060,2070,2080,2090,2100], Location=None):

        """ 
        
        Samples a raster of future rates of relative sea level change (rise/fall)
        at each transect location on coast

        Parameters
        ----------
        FutureRSLFolder : string
            Folder containing future sea level elevation rasters for Scotland
        RCP : int
            RCP scenario to use
        Percentile : int
            Percentile scenario to use
        Years : list
            List of integers corresponding to the years to be analysed
        Location: Node object with location to use
        
        MDH, September 2019

        """

        print("Coast.SampleFutureRSL: Sampling future Relative Sea Level raster dataset")

        if self.FutureShoreLinesYears:
            print("\tFuture sea levels already sampled")
            return

        self.FutureShoreLinesYears = Years

        for Year in Years:
            FutureRSLRaster = FutureRSLFolder + "/RCP" + str(RCP) + "_" + str(Percentile) + "th_" + str(Year) + "_filled.tif"

            # open the raster dataset to work on
            with rasterio.open(FutureRSLRaster) as RSLDataset:
            
                # loop through transects and sample
                for Line in self.CoastLines:
                    for i, Transect in enumerate(Line.Transects[:]):
                        if Location:
                            for val in RSLDataset.sample([(Location.X,Location.Y)]):
                                Transect.FutureSeaLevels.append(val[0])
                                Transect.FutureSeaLevelYears.append(Year)
                        else:
                            for val in RSLDataset.sample([(Transect.CoastNode.X,Transect.CoastNode.Y)]):
                                Transect.FutureSeaLevels.append(val[0])
                                Transect.FutureSeaLevelYears.append(Year)

    def SampleRockHeadPosition(self, UPSMRaster, MaxRockHeadErosionDistance=25.):

        """
        Function to check values of UPSM and identify if a limit on shoreline erosion position 
        is required based on a threshold value of 0.4

        MDH, January 2020

        """

        print("Coast.SampleRockHeadPosition: Sampling rock head dataset to set maximum extent of erosion")

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
                    X = np.linspace(X1,X2,50)
                    Y = np.linspace(Y1,Y2,50)
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
                    NVals = np.int32(np.sqrt(dX**2. + dY**2.))
                    
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

                    if not RockBool.any():
                        continue
                    
                    JInd = np.argmax(RockBool)
                    
                    # flag position as attribute of transect
                    Transect.RockHeadPosition = Node(X[JInd],Y[JInd])
                    Transect.RockHeadDistance = Transect.StartNode.get_Distance(Transect.RockHeadPosition)

                    # check rockhead position relative to starting shoreline position and adjust to allow 
                    # some erosion to take place or not to take place
                    if Transect.HistoricShorelinesDistances and (Transect.HistoricShorelinesDistances[-1][0] > Transect.RockHeadDistance):
                        Transect.RockHeadDistance = Transect.HistoricShorelinesDistances[-1][0] + MaxRockHeadErosionDistance
                        Transect.RockHeadPosition = Transect.get_Position(Transect.RockHeadDistance)
                    else:
                        Transect.RockHeadDistance += MaxRockHeadErosionDistance
                        Transect.RockHeadPosition = Transect.get_Position(Transect.RockHeadDistance)
                        
    def SampleDefencesPosition(self, DefencesShp, MaxDefencesErosionDistance=0.):

        """
        Function to find defences and identify if a limit on shoreline erosion position 
        
        MDH, January 2021

        """

        print("Coast.SampleDefencesPosition: Sampling position of coastal defences")


        # set a distance to look inland to check for intersections
        LookDistance = 0.

        # read shapefile using geopandas
        GDF = gp.read_file(DefencesShp)
        Lines = GDF['geometry']
        
        if len(Lines) == 0:
            print("No Lines")
            import pdb
            pdb.set_trace()
            return
        
        # catch situation where only one line
        MultiLines = []

        if len(Lines) == 1:
            MultiLines = Lines[0]

        # deal with invalid geometries on the fly? This is messy!
        else:
            for Line in Lines:
                if not Line:
                    continue
                elif Line.geom_type == "LineString":
                    MultiLines.append(Line)
                elif Line.geom_type == "MultiLineString":
                    for SubLine in Line:
                        if SubLine.geom_type == "LineString":
                            MultiLines.append(SubLine)

            MultiLines = MultiLineString(MultiLines)    
            #MultiLines = MultiLineString([Line for Line in Lines if Line.geom_type == "LineString"])
            
        if not MultiLines:
            print("No Lines")
            return
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # extend transect line inland to look for intersection
                #Calculate start and end nodes and generate Transect
                X1 = Transect.EndNode.X + LookDistance * np.sin( np.radians( Transect.Orientation ) )
                Y1 = Transect.EndNode.Y + LookDistance * np.cos( np.radians( Transect.Orientation ) )
                TransectLine = LineString(((Transect.StartNode.X,Transect.StartNode.Y),(X1,Y1)))
            
                # intersect with historical shoreline
                try:
                    Intersections = TransectLine.intersection(MultiLines)
                except:
                    import pdb
                    pdb.set_trace()
                    
                # catch no intersections and flag for deletion?
                if Intersections.is_empty:
                    continue

                # check there arent multiple intersections
                StartPoint = Point(Transect.StartNode.X, Transect.StartNode.Y)
                # store multiple intersections if so
                if Intersections.geom_type == "MultiPoint":
                    Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersections.geoms]
                    Index = Distances.index(min(Distances))
                    Distance = Distances[Index]
                    Intersection = Intersections.geoms[Index]
                    
                else:
                    # check if this is a new endnode by intersecting with line from startnode to endnode
                    Intersection = Intersections
                    Distance = StartPoint.distance(Intersection)
                
                # assign to transect
                Transect.Defences = True
                Transect.DefencesDistance = Distance+MaxDefencesErosionDistance
                Transect.DefencesPosition = Transect.get_Position(Transect.DefencesDistance)
                
    def PredictFutureShorelines(self, MinMaxFlag=None):

        """

        Wrapper to call Transects function to predict future shoreline positions

        MDH, September 2019

        """
        print("Coast.PredictFutureShorelines: predicting future shoreline positions")
        # loop through transects and sample
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.PredictFutureShorelines(MinMaxFlag=MinMaxFlag)

    def PredictFutureShorelinesBestWorstCase(self):
        """

        Wrapper to call Transects function to predict future shoreline positions
        flagged to use the best and worst case historic rates on each transect

        MDH, December 2023

        """
        print("Coast.PredictFutureShorelinesBestWorstCase: predicting future shoreline positions")
        # loop through transects and sample
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.PredictFutureShorelines()

    def PredictFutureShorelinesUncertainty(self, Year=2100):

        """

        Wrapper to call Transects function to predict future shoreline positions uncertainty

        MDH, September 2019
        
        """
        print("Coast.PredictFutureShorelinesUncertainty: predicting future shoreline positions uncertainty %d", Year)
        # loop through transects and sample
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                if Transect.Future:
                    Transect.PredictFutureShorelineUncertainty(Year)

    def PredictFutureShorelinesError(self, Year=2100):

        """

        Wrapper to call Transects function to predict future shoreline positional error

        MDH, September 2020

        """
        print("Coast.PredictFutureShorelines: predicting future shoreline positions error %d", Year)
        # loop through transects and sample
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                if Transect.Future:
                    Transect.PredictFutureShorelineError(Year)

    def PredictFutureVegEdge(self,VegEdgeShp, Year=None):

        """

        Wrapper function to call Transects function to predict future shoreline position
        based on position of vegetation edge provided in a shapefile.


        MDH, Feb 2020

        """

        print("Coast.PredictFutureVegEdge: Finding position of future veg edge ", end="")
        
        # set a distance to look inland to check for intersections
        LookDistance = 100.

        # read shapefile using geopandas
        GDF = gp.read_file(VegEdgeShp)
        Lines = GDF['geometry']
        
        # catch situation where only one line
        if len(Lines) == 0:
            sys.exit("Error: No Veg Edge Lines!")
        elif len(Lines) == 1:
            MultiLines = Lines[0]
        else:
            MultiLines = MultiLineString([Line for Line in Lines if Line])
            MultiLines = MultiLineString([Line for Line in MultiLines if Line.geom_type == "LineString"])
            

        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # extend transect line inland to look for intersection
                #Calculate start and end nodes and generate Transect
                X1 = Transect.EndNode.X + LookDistance * np.sin( np.radians( Transect.Orientation ) )
                Y1 = Transect.EndNode.Y + LookDistance * np.cos( np.radians( Transect.Orientation ) )
                TransectLine = LineString(((Transect.StartNode.X,Transect.StartNode.Y),(X1,Y1)))
            
                # intersect with historical shoreline
                Intersection = TransectLine.intersection(MultiLines)

                # catch no intersections and flag for deletion?
                if Intersection.is_empty:
                    Transect.VegEdge = False
                    continue

                # check there arent multiple intersections, if there are just get the nearest
                if Intersection.geom_type == "MultiPoint":
                    StartPoint = Point(Transect.StartNode.X, Transect.StartNode.Y)
                    Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersection.geoms]
                    Index = Distances.index(min(Distances))
                    Intersection = Intersection[Index]

                # check if this is a new endnode by intersecting with line from startnode to endnode
                Distance = Transect.LineString.distance(Intersection)
                
                if Distance > 0.001:
                    
                    # set this as the new end node
                    NewEndNode = Node(Intersection.x,Intersection.y)
                    Transect.Redraw(Transect.StartNode, NewEndNode)

                # use minimum of line.distance to find line
                # need date attribute if rates are to be calculated
                Distances = Lines.distance(Intersection)
                NearestLine = GDF.iloc[Distances.idxmin()]
                
                # check it hasnt already been read
                if not Year:
                    if "Surv_End_A" in NearestLine:
                        Year = int(NearestLine.Surv_End_A)
                    elif "Surv_End_B" in NearestLine:
                        Year = int(NearestLine.Surv_End_B)
                    elif "Surv_End_C" in NearestLine:
                        Year = int(NearestLine.Surv_End_C)
                    elif "Surv_End_D" in NearestLine:
                        Year = int(NearestLine.Surv_End_D)
                    else:
                        sys.exit("Couldnt find survey year for MHWS historic shoreline position")

                # add point to transect
                Transect.VegEdgePosition = Node(Intersection.x,Intersection.y)
                Transect.VegEdgeYear = Year
                Transect.VegEdge = True
                
                # analyse future veg edge
                Transect.PredictFutureVegEdge()

                
    def ExtendTransects2Hinterland(self, Distance):

        """
        Extends transects by a fixed distance into the hinterland in order to 
        measure hinterland topography. N.B. does not extend start/end point but 
        creates a new node in the hinterland.

        MDH, March 2020

        """

        print("Coast.ExtendTransects2Hinterland: Puts a new node landward of existing transect")

        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.ExtendTransect(Distance, 0)
                
    def ExtendTransects2Line(self, LineShp):

        """
        Extends transects to a line shp file

        MDH, August 2020

        """

        print("Coast.ExtendTransects2Hinterland: Puts a new node landward of existing transect")

        # read in the lines object file
        
        for Line in self.CoastLines:
            Line.ExtendTransectsToLineShp(LineShp)
            
    def TruncateTransects(self):
        
        """
        function to cut the length of transects the the extrermes of historical
        or future shoreline positions, including uncertainties
        
        MDH, November 2020
        
        """
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Transect.Truncate()
                            
    def FindDEM(self, DEMIndexFileShp):

        """
        Identifies which DEMs transects intersect with, where interesction is with
        more than one transect DEMs will get merged.

        Need to think this through more carefully... dont want to end up having to repeatedly open the same DEM
        Get a list of transects that intersect each DEM along the coast object?
        Get a list of unique DEMs that are intersected.
        Intersect Coast lines and transects with DEMIndexFileShp
        Open each DEM and extract topography for all transects that fall within
        What to do about transects crossing from one DEM to another?

        MDH, March 2020

        """

        print("Coast.FindDEM: Identifying DEM for each transect to sample from")

        # read the DEM index file
        PolyGDF = gp.read_file(DEMIndexFileShp)
        
        # list of unique DEMs
        self.UniqueDEMList = []
        
        #print(len(self.CoastLines))
        for Line in self.CoastLines:
            

            # get multilinestring of transects
            Lines = [LineString([(Transect.EndNode.X,Transect.EndNode.Y),(Transect.StartNode.X,Transect.StartNode.Y)]) for Transect in Line.Transects]
            
            if not Lines:
                continue
            
            LineGDF = gp.GeoDataFrame(geometry=Lines,crs=PolyGDF.crs)
            
            JoinGDF = gp.sjoin(LineGDF, PolyGDF, predicate='intersects')
            
            # set DEMs to list 
            # NH: For each CoastLine, a list of unique DEMs. 
            # But, if a DEM spans two CoastLines, it is also added for the second CoastLine interation. 
            ### self.UniqueDEMList.extend(list(JoinGDF.location.unique()))
            self.UniqueDEMList.extend(list(JoinGDF[JoinGDF['HiResExist']=='Y'].loc_HiRes.unique()))
            self.UniqueDEMList.extend(list(JoinGDF[JoinGDF['HiResExist']=='N'].location.unique()))
            
        # NH: This list is only unique for each CoastLine, not unique overall
        if __debug__:
            print("DEM list: unique per CoastLine", self.UniqueDEMList,"\n")
        
        # NH fix: drop duplicate DEMs from final list: convert to dictionariy and back again to list
        self.UniqueDEMList = list(dict.fromkeys(self.UniqueDEMList))
        if __debug__:
            print("DEM list: unique overall", self.UniqueDEMList)
        
        # replace extension with *.tif
        #for i, DEMPath in enumerate(self.UniqueDEMList):
        #    self.UniqueDEMList[i] = DEMPath.rstrip("asc")+"tif"

    def ExtractTransectTopography(self, DEMFileList=None):

        """
        Function to sample elevations for transect lines from list of DEM files
        
        MDH, March 2020

        """      
        print("Coast.ExtractTransectTopography: Sampling DEM(s) along transects")

        # set up dem file list
        if DEMFileList:
            # check if list and make list if not
            if not isinstance(DEMFileList, list):
                DEMFileList = [DEMFileList,]
            self.UniqueDEMList = DEMFileList

        # loop through DEMs
        for DEM in self.UniqueDEMList:
            
            print("\t" + DEM.split("/")[-1])

            DTM_Dataset = rasterio.open(DEM)
            DTMArray = DTM_Dataset.read(1)
            NCols = DTM_Dataset.width
            NRows = DTM_Dataset.height
            NDV = DTM_Dataset.nodata
            Resolutions = DTM_Dataset.res
            
            # check if we're missing no data
            if not DTM_Dataset.nodata:
                # raise SystemExit("DTM missing no data value") # NH: remove this as .asc files don't have nodata set.
                # NH add print and NDV assignment
                print("\tDTM missing no data value!")
                NDV = -9999

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

            for Line in self.CoastLines:
                for Transect in Line.Transects:
                    
                    # check we have nodes to sample
                    if not Transect.DistanceNodes:
                        Transect.DistanceSpacing = DTM_Dataset.res[0]
                        Transect.GenerateSampleNodes()

                    # check for intersection
                    if not Transect.LineString.intersects(DTM_Extent):
                        continue
                    
                    # get list of points that intersect DTM only
                    Points = [Point(ThisNode.X,ThisNode.Y) for ThisNode in Transect.DistanceNodes]
                    Points = [ThisPoint if ThisPoint.within(DTM_Extent) else Point((0,0)) for ThisPoint in Points]
                    Coords = [(Point.x, Point.y) for Point in Points]
                    Elevations = [Sample[0] for Sample in DTM_Dataset.sample(Coords)]
                    Transect.Elevation = Elevations

                    # problem here gettign back to transects
                    for i, ThisNode in enumerate(Transect.DistanceNodes):
                        
                        if not ThisNode.Z and Elevations[i] > 0:
                            Transect.DistanceNodes[i].Z = Elevations[i]

                    # Set up the mask from NDVs
                    Mask = Elevations == NDV
                    Transect.Distance = ma.masked_where(Mask,Transect.Distance)
                    Transect.Elevation = ma.masked_where(Mask,Elevations)

                    Transect.HaveTopography = True
                    
                    # NH add Note: issue where transect overlaps 2 DTMs, Transect.Elevation gets overwritten in 2nd DTM iteration (StF L0 T30)
                    # But, correct elevations are in Transect.DisanceNodes.Z
                    #if __debug__:
                        #print(Line.ID, Transect.ID)
                        #print("Elevation:\n", Transect.Elevation)
                        #print("Distance:\n", Transect.Distance)
                        #for i, ThisNode in enumerate(Transect.DistanceNodes):
                            #print("DistNodes:\n", Transect.DistanceNodes[i].X, Transect.DistanceNodes[i].Y, Transect.DistanceNodes[i].Z)

    def ExtractTransectTopographySwath(self, DEMFileList=None, SwathDistance=-9999, DistanceSpacing=None, CrossShoreWindowSize=None):
        """
        Now deprecated, as this function only handles transect crossing 2 DTMs.
        Replaced with SampleTransectTopographySwath and PerformIDWInterpolation.
        This separates topo sampling and IDW interpolation into separate functions,
        and handles transect spanning multiple DTMs.
        
        ExtractTransectTopographySwath:
        Profile to populate transects with topographic data
        Uses swath profile routine to collect elevations within a certain distance
        of each transect line then takes IDW values for the transect topography

        ADD FUNCTIONALITY TO CATCH WHEN DEM EDGE HAS BEEN EXCEEDED? NO TRANSECTS IN THIS CASE

        MDH, June 2019
        
        NH modification, October 2023:
        - Add check for missing nodata value
        - Add ability to work with multiple DTMs, as in ExtractTransectTopography
        - Fix bug of negative index in bounding box
        - Extend bounding box start and end coordinates by SwathDistance
        - Handle transect crossing two DTMs
        - Add parameter to set crosshore interpolation window size
        
        Parameters
        ----------
        DTMFile : str  - DEPRECATED
            Name of DTM File, must be a *.tif
            
        DEMFileList : list or single string - NEW
            Either a) List of strings containing pathnames of unique DEMs for current coast
            or     b) A single DTM filename string (backwards compatible)
            Coast.FindDEM can be called prior to write to self.UniqueDEMList
            In that case you don't have to send the list as a parameter.

        SwathDistance : float
            Distance away from transect line to sample elevations in DEM
            Default is 2 times the resolution of the DTM
            
        DistanceSpacing : float
            Distance in m between elevation nodes on the transect
            
        CrossShoreWindowSize : float
            Size in m of the cross-shore window landward and seaward of
            each point during the interpolation.
            Ultimate inrerpolation window width is thus two times this value.
            Minimum of DTM resolution, max of 5*DTM resolution
            Default of 2*DTM resolution
            
        """
        
        print("Coast.ExtractTransectTopographySwath: Sampling DTMs for each transect")
                            
        # set up dem file list
        if DEMFileList:
            # check if list and make list if not
            if not isinstance(DEMFileList, list):
                DEMFileList = [DEMFileList,]
            self.UniqueDEMList = DEMFileList

        # loop through DEMs
        for DEM in self.UniqueDEMList:
            
            print("\t" + DEM.split("/")[-1])

            # load the DTM and get its properties
            print("\tLoading DTM... ", end="")
            DTM_Dataset = rasterio.open(DEM) 
            DTMArray = DTM_Dataset.read(1)
            NCols = DTM_Dataset.width
            NRows = DTM_Dataset.height
            NDV = DTM_Dataset.nodata
            Resolutions = DTM_Dataset.res
            print("Done")

            # check for square pixels
            if not DTM_Dataset.res[0] == DTM_Dataset.res[1]:
                raise SystemExit("DTM has non-square cells")
            
            # NH add: check if we're missing no data
            if not DTM_Dataset.nodata:
                # raise SystemExit("DTM missing no data value") # NH: remove this as .asc files don't have nodata set.
                print("\tDTM missing no data value!")
                NDV = -9999
        
            # get resolution
            DTM_Resolution = DTM_Dataset.res[0]

            # get extent of DTM and set up polygon of extent
            XMin = DTM_Dataset.bounds[0]
            XMax = DTM_Dataset.bounds[2]
            YMin = DTM_Dataset.bounds[1]
            YMax = DTM_Dataset.bounds[3]
            DTM_Extent = Polygon([[XMin, YMin], [XMin,YMax], [XMax, YMax], [XMax, YMin]])
            
            if __debug__:
                print("\tXMin, XMax, YMin, YMax = ", XMin, XMax, YMin, YMax) 

            # check swath distance
            if SwathDistance < 0:
                SwathDistance = DTM_Resolution*2.
            
            if SwathDistance > DTM_Resolution*20:
                print("\tSwathDistance > DTM_Resolution*20! Setting to DTM_Resolution*20")
                SwathDistance = DTM_Resolution*20.
                
            # check cross shore window size
            if not CrossShoreWindowSize:
                CrossShoreWindowSize = DTM_Resolution*2.
            if CrossShoreWindowSize < DTM_Resolution:
                CrossShoreWindowSize = DTM_Resolution
            if CrossShoreWindowSize > DTM_Resolution*5.:
                CrossShoreWindowSize = DTM_Resolution*5.
           
            # Get vectors of X and Y coordinates, NB reversal of Y in line with 
            # DTM indexing from top left
            XVector = XMin+np.arange(0,NCols)*DTM_Resolution+0.5*DTM_Resolution
            YVector = YMin+DTM_Resolution*np.arange(0,NRows)[::-1]+0.5*DTM_Resolution
        
            if __debug__:
                print("\tXVector len = ", len(XVector)) 
                print("\tYVector len = ", len(YVector))

            # Track progress
            NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1 # NH: subtract one as counting from zero
            CurrentTransect = 0
                        
            for Line in self.CoastLines:
                for Transect in Line.Transects:
                    
                    # print progress to screen
                    print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")

                    #Get line points
                    X1, Y1 = Transect.StartNode.get_XY()
                    X2, Y2 = Transect.EndNode.get_XY()
                    TransectLine = LineString([(X1, Y1), (X2, Y2)])
                    
                    #if __debug__:
                        #print("\tTransect X1, Y1, X2, Y2 = ", X1, Y1, X2, Y2)

                    # check for intersection
                    if not TransectLine.intersects(DTM_Extent):
                        CurrentTransect += 1 # NH: increment transect count if no intersect
                        continue

                    # NH: Bounding box size to extend past transect bounds by SwathDistance
                    iStart = np.argmin(np.abs(YVector-np.max([Y1,Y2])))-(int)(SwathDistance/DTM_Resolution) 
                    iEnd = np.argmin(np.abs(YVector-np.min([Y1,Y2])))+(int)(SwathDistance/DTM_Resolution)
                    jStart = np.argmin(np.abs(XVector-np.min([X1,X2])))-(int)(SwathDistance/DTM_Resolution)
                    jEnd = np.argmin(np.abs(XVector-np.max([X1,X2])))+(int)(SwathDistance/DTM_Resolution)
                    
                    # Catch Start index of -1, when bounding box intersects top (i) or left hand side (j) of DEM.
                    # Catch End index larger than the length or width of the DTM. Set InterpolationInconplete flag.  
                    if iStart < 0:
                        print("\tiStart < 0! Setting to 0")
                        iStart = 0
                        Transect.InterpolationIncomplete = True
                    if jStart < 0:
                        print("\tjStart < 0! Setting to 0")
                        jStart = 0
                        Transect.InterpolationIncomplete = True
                    if iEnd > len(YVector):
                        print("\tiEnd > len(YVector)! Setting to", len(YVector))
                        iEnd = len(YVector)
                        Transect.InterpolationIncomplete = True
                    if jEnd > len(XVector):
                        print("\tjEnd > len(XVector)! Setting to", len(XVector))
                        jEnd = len(XVector)
                        Transect.InterpolationIncomplete = True                        
                    
                    #if __debug__:
                        #print("\t\tiStart, iEnd, jStart, jEnd = ", iStart, iEnd, jStart, jEnd)
                        #print("\tXVector[jStart], XVector[jEnd-1], YVector[iStart], YVector[iEnd-1] = ", XVector[jStart], XVector[jEnd-1], YVector[iStart], YVector[iEnd-1])

                    #Get Vector X and Y
                    dX12 = X2-X1
                    dY12 = Y2-Y1

                    #Declare list holders for profile data
                    if Transect.InterpolationIncomplete and Transect.DistTo: # second run
                        X = Transect.X
                        Y = Transect.Y
                        Z = Transect.Z
                        DistAlong = Transect.DistAlong
                        DistTo = Transect.DistTo
                        Transect.InterpolationIncomplete = False 
                        print("\t\tSECOND run... Completing interpolation")
                    else:
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
                                    
                    # If first run of crossing transect, save values to Transect and don't complete IDW calculation
                    if Transect.InterpolationIncomplete and not Transect.DistTo:
                        Transect.X = X
                        Transect.Y = Y
                        Transect.Z = Z
                        Transect.DistAlong = DistAlong
                        Transect.DistTo = DistTo
                        print("\t\tFIRST interpolation run... Save and continue")
                        CurrentTransect += 1
                        continue
                    
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
                    
                    # Determination of distance spacing now externalised.
                    if not DistanceSpacing:
                        DistanceSpacing = DTM_Resolution*2.
                    if DistanceSpacing < 0:
                        DistanceSpacing = -DistanceSpacing
                    
                    # Create a line for interpolating to
                    LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
                    
                    NoPoints = (int)(LineLength/DistanceSpacing)+1
                    if NoPoints < 1:
                        raise SystemExit("LineLength/DistanceSpacing leads to zero elevation points")
                        
                    Transect.DistanceSpacing = DistanceSpacing
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
                        DistAlongTransect[i] = i*DistanceSpacing
                        
                        # Sample a reduced array here i.e. a neighbourhood to reduce computation time                      
                        Neighbourhood = np.abs(DistAlongTransect[i]-DistAlong) < CrossShoreWindowSize
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
                    #print("ZIDW.data=", ZIDW.data, "ZIDW.mask=", ZIDW.mask)        ### NH DEBUG: ZIDW does have .data and .mask componenets. BUT .mask is single boolean=False (not array) when no masked elements
                    ZMin = ma.masked_where(Mask,ZMin)
                    ZMax = ma.masked_where(Mask,ZMax)
                    ZStd = ma.masked_where(Mask,ZStd)
                    
                    Transect.Distance = DistAlongTransect.copy()                    ### NH ADD: use ma.MaskedArray.copy() to copy whole masked array
                    Transect.DistanceSpacing = DistAlongTransect[1]-DistAlongTransect[0]
                    Transect.DistanceNodes = [Node(X,Y) for X, Y in zip(XLine,YLine)]
                    Transect.Elevation = ZIDW.copy()
                    Transect.ElevationMin = ZMin.copy()
                    Transect.ElevationMax = ZMax.copy()
                    Transect.ElevStd = ZStd.copy()
                    
                    # update transect no
                    CurrentTransect += 1
            
            print("")
            
        # Catch outer edge transects: complete interpolation with existing data
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                if Transect.InterpolationIncomplete:
                    Transect.InterpolationIncomplete = False
                    print(f"\tCompleting edge transect {Transect.LineID}:{Transect.ID} interpolation")
                
                    X = Transect.X
                    Y = Transect.Y
                    Z = Transect.Z
                    DistAlong = Transect.DistAlong
                    DistTo = Transect.DistTo
                    
                    #Sort by distance along line, need to convert to numpy arrays as we go to sort
                    Sortedi = np.argsort(DistAlong)
                    X = np.asarray(X)[Sortedi]
                    Y = np.asarray(Y)[Sortedi]
                    DistAlong = np.asarray(DistAlong)[Sortedi]
                    DistTo = np.asarray(DistTo)[Sortedi]
                    Z = np.asarray(Z)[Sortedi]
                    
                    # Determination of distance spacing now externalised
                    if not DistanceSpacing:
                        DistanceSpacing = DTM_Resolution*2.
                    if DistanceSpacing < 0:
                        DistanceSpacing = -DistanceSpacing
                    
                    #Get line points
                    X1, Y1 = Transect.StartNode.get_XY()
                    X2, Y2 = Transect.EndNode.get_XY()
                    TransectLine = LineString([(X1, Y1), (X2, Y2)])
                    
                    # Create a line for interpolating to
                    LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
                    
                    NoPoints = (int)(LineLength/DistanceSpacing)
                    if NoPoints < 1:
                        raise SystemExit("LineLength/DistanceSpacing leads to zero elevation points")
                        
                    Transect.DistanceSpacing = DistanceSpacing
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
                        DistAlongTransect[i] = i*DistanceSpacing
                        
                        # Sample a reduced array here i.e. a neighbourhood to reduce computation time
                        Neighbourhood = np.abs(DistAlongTransect[i]-DistAlong) < CrossShoreWindowSize
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
                    
                    Transect.Distance = DistAlongTransect.copy()        ### NH ADD: use ma.MaskedArray.copy() to copy whole masked array
                    Transect.DistanceSpacing = DistAlongTransect[1]-DistAlongTransect[0]
                    Transect.Elevation = ZIDW.copy()
                    Transect.ElevationMin = ZMin.copy()
                    Transect.ElevationMax = ZMax.copy()
                    Transect.ElevStd = ZStd.copy()
                    Transect.DistanceNodes = [Node(X,Y) for X, Y in zip(XLine,YLine)]
                    
    def SampleTransectTopographySwath(self, DEMFileList=None, SwathDistance=-9999):
        """
        Profile to populate transects with topographic data
        Uses swath profile routine to collect elevations within a certain distance
        of each transect line
        
        Original by MDH. Now split into separate sampling function here.
        Thi sis to allow multiple rasters to be sampled by a transect.

        NH, Jan 2024
        
        Parameters
        ----------
        DEMFileList : list or single string - NEW
            Either a) List of strings containing pathnames of unique DEMs for current coast
            or     b) A single DTM filename string (backwards compatible)
            Coast.FindDEM can be called prior to write to self.UniqueDEMList
            In that case you don't have to send the list as a parameter.

        SwathDistance : float
            Distance away from transect line to sample elevations in DEM
            Default is 2 times the resolution of the DTM
            
        """  
        
        print("Coast.SampleTransectTopographySwath: Sampling DTMs for each transect")
                            
        # set up dem file list
        if DEMFileList:
            # check if list and make list if not
            if not isinstance(DEMFileList, list):
                DEMFileList = [DEMFileList,]
            self.UniqueDEMList = DEMFileList

        # loop through DEMs
        for DEM in self.UniqueDEMList:
            
            print("\t" + DEM.split("/")[-1])

            # load the DTM and get its properties
            print("\tLoading DTM... ", end="")
            DTM_Dataset = rasterio.open(DEM) 
            DTMArray = DTM_Dataset.read(1)
            NCols = DTM_Dataset.width
            NRows = DTM_Dataset.height
            NDV = DTM_Dataset.nodata
            Resolutions = DTM_Dataset.res
            print("Done")

            # check for square pixels
            if not DTM_Dataset.res[0] == DTM_Dataset.res[1]:
                raise SystemExit("DTM has non-square cells")
            
            # NH add: check if we're missing no data
            if not DTM_Dataset.nodata:
                # raise SystemExit("DTM missing no data value") # NH: remove this as .asc files don't have nodata set.
                print("\tDTM missing no data value!")
                NDV = -9999
        
            # get resolution
            DTM_Resolution = DTM_Dataset.res[0]

            # get extent of DTM and set up polygon of extent
            XMin = DTM_Dataset.bounds[0]
            XMax = DTM_Dataset.bounds[2]
            YMin = DTM_Dataset.bounds[1]
            YMax = DTM_Dataset.bounds[3]
            DTM_Extent = Polygon([[XMin, YMin], [XMin,YMax], [XMax, YMax], [XMax, YMin]])
            
            if __debug__:
                print("\tXMin, XMax, YMin, YMax = ", XMin, XMax, YMin, YMax) 

            # check swath distance
            if SwathDistance < 0:
                SwathDistance = DTM_Resolution*2.
            
            if SwathDistance > DTM_Resolution*20:
                print("\tSwathDistance > DTM_Resolution*20! Setting to DTM_Resolution*20")
                SwathDistance = DTM_Resolution*20.
           
            # Get vectors of X and Y coordinates, NB reversal of Y in line with 
            # DTM indexing from top left
            XVector = XMin+np.arange(0,NCols)*DTM_Resolution+0.5*DTM_Resolution
            YVector = YMin+DTM_Resolution*np.arange(0,NRows)[::-1]+0.5*DTM_Resolution
        
            if __debug__:
                print("\tXVector len = ", len(XVector)) 
                print("\tYVector len = ", len(YVector))

            # Track progress
            NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1 # NH: subtract one as counting from zero
            CurrentTransect = 0
            
            for Line in self.CoastLines:
                for Transect in Line.Transects:
                    
                    # print progress to screen
                    print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")

                    #Get line points
                    X1, Y1 = Transect.StartNode.get_XY()
                    X2, Y2 = Transect.EndNode.get_XY()
                    TransectLine = LineString([(X1, Y1), (X2, Y2)])
                    
                    #if __debug__:
                        #print("\tTransect X1, Y1, X2, Y2 = ", X1, Y1, X2, Y2)

                    # check for intersection
                    if not TransectLine.intersects(DTM_Extent):
                        CurrentTransect += 1 # NH: increment transect count if no intersect
                        continue

                    # NH: Bounding box size to extend past transect bounds by SwathDistance
                    iStart = np.argmin(np.abs(YVector-np.max([Y1,Y2])))-(int)(SwathDistance/DTM_Resolution) 
                    iEnd = np.argmin(np.abs(YVector-np.min([Y1,Y2])))+(int)(SwathDistance/DTM_Resolution)
                    jStart = np.argmin(np.abs(XVector-np.min([X1,X2])))-(int)(SwathDistance/DTM_Resolution)
                    jEnd = np.argmin(np.abs(XVector-np.max([X1,X2])))+(int)(SwathDistance/DTM_Resolution)
                    
                    # Catch Start index of -1, when bounding box intersects top (i) or left hand side (j) of DEM.
                    # Catch End index larger than the length or width of the DTM. Set InterpolationInconplete flag.  
                    if iStart < 0:
                        print("\tiStart < 0! Setting to 0")
                        iStart = 0
                        #Transect.InterpolationIncomplete = True
                    if jStart < 0:
                        print("\tjStart < 0! Setting to 0")
                        jStart = 0
                        #Transect.InterpolationIncomplete = True
                    if iEnd > len(YVector):
                        print("\tiEnd > len(YVector)! Setting to", len(YVector))
                        iEnd = len(YVector)
                        #Transect.InterpolationIncomplete = True
                    if jEnd > len(XVector):
                        print("\tjEnd > len(XVector)! Setting to", len(XVector))
                        jEnd = len(XVector)
                        #Transect.InterpolationIncomplete = True                        
                    
                    #if __debug__:
                        #print("\t\tiStart, iEnd, jStart, jEnd = ", iStart, iEnd, jStart, jEnd)
                        #print("\tXVector[jStart], XVector[jEnd-1], YVector[iStart], YVector[iEnd-1] = ", XVector[jStart], XVector[jEnd-1], YVector[iStart], YVector[iEnd-1])

                    #Get Vector X and Y
                    dX12 = X2-X1
                    dY12 = Y2-Y1

                    # Declare list holders for profile data
                    # If data sampled previously from another raster, load it
                    if Transect.X: 
                        X = Transect.X
                        Y = Transect.Y
                        Z = Transect.Z
                        DistAlong = Transect.DistAlong
                        DistTo = Transect.DistTo
                        Transect.InterpolationIncomplete = False 
                        print("\t\tContinuing elevation sampling...")
                    else:
                        X = []
                        Y = []
                        Z = []
                        DistAlong = []
                        DistTo = []
                        print("\t\tStarting elevation sampling...")
                    
                    # Sample elevation data in swath around transect
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
                    
                    # Save data                    
                    Transect.X = X
                    Transect.Y = Y
                    Transect.Z = Z
                    Transect.DistAlong = DistAlong
                    Transect.DistTo = DistTo
                    Transect.DTM_Resolution = DTM_Resolution
                    Transect.NDV = NDV
                    CurrentTransect += 1
            
            print("")
            
    
    def PerformIDWInterpolation(self, DistanceSpacing=None, CrossShoreWindowSize=None):
        """
        Perform inverse distance weighted interpolation on the sampled swath data
        
        Parameters
        ----------
        DistanceSpacing : float
            Distance in m between elevation nodes on the transect
            
        CrossShoreWindowSize : float
            Size in m of the cross-shore window landward and seaward of
            each point during the interpolation.
            Ultimate inrerpolation window width is thus two times this value.
            Minimum of DTM resolution, max of 5*DTM resolution
            Default of 2*DTM resolution
            
        """
        
        print("Coast.PerformIDWInterpolation: IDW interpolation on sampled elevation data")
        
        # Track progress
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])-1  # counting from zero
        CurrentTransect = 0
        
        # Perfrom interpolation        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
            
                # print progress to screen
                print(" \r\tTransect %3d / %3d" % (CurrentTransect, NoTransects), end="")
                
                # Load sampled topography data
                X = Transect.X
                Y = Transect.Y
                Z = Transect.Z
                DistAlong = Transect.DistAlong
                DistTo = Transect.DistTo
                DTM_Resolution = Transect.DTM_Resolution
                NDV = Transect.NDV
                
                # check input parameters - have to do this here as need transect saved data
                if not DistanceSpacing:
                    DistanceSpacing = DTM_Resolution*2.
                if DistanceSpacing < 0:
                    DistanceSpacing = -DistanceSpacing
                    
                if not CrossShoreWindowSize:
                    CrossShoreWindowSize = DTM_Resolution*2.
                if CrossShoreWindowSize < DTM_Resolution:
                    CrossShoreWindowSize = DTM_Resolution
                if CrossShoreWindowSize > DTM_Resolution*5.:
                    CrossShoreWindowSize = DTM_Resolution*5.
        
                #Get line points
                X1, Y1 = Transect.StartNode.get_XY()
                X2, Y2 = Transect.EndNode.get_XY()
                    
                #Sort by distance along line, need to convert to numpy arrays as we go to sort
                Sortedi = np.argsort(DistAlong)
                X = np.asarray(X)[Sortedi]
                Y = np.asarray(Y)[Sortedi]
                DistAlong = np.asarray(DistAlong)[Sortedi]
                DistTo = np.asarray(DistTo)[Sortedi]
                Z = np.asarray(Z)[Sortedi]
                
                # Create a line for interpolating to
                LineLength = np.sqrt((X2-X1)**2 + (Y2-Y1)**2)
                
                NoPoints = round(LineLength/DistanceSpacing)+1
                if NoPoints < 1:
                    raise SystemExit("LineLength/DistanceSpacing leads to zero elevation points")
                    
                Transect.DistanceSpacing = DistanceSpacing
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
                    DistAlongTransect[i] = i*DistanceSpacing
                    
                    # Sample a reduced array here i.e. a neighbourhood to reduce computation time                      
                    Neighbourhood = np.abs(DistAlongTransect[i]-DistAlong) < CrossShoreWindowSize
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
                #print("ZIDW.data=", ZIDW.data, "ZIDW.mask=", ZIDW.mask)        ### NH DEBUG: ZIDW does have .data and .mask componenets. BUT .mask is single boolean=False (not array) when no masked elements
                ZMin = ma.masked_where(Mask,ZMin)
                ZMax = ma.masked_where(Mask,ZMax)
                ZStd = ma.masked_where(Mask,ZStd)
                
                Transect.Distance = DistAlongTransect.copy()                    ### NH ADD: use ma.MaskedArray.copy() to copy whole masked array
                Transect.DistanceSpacing = DistAlongTransect[1]-DistAlongTransect[0]
                Transect.DistanceNodes = [Node(X,Y) for X, Y in zip(XLine,YLine)]
                Transect.Elevation = ZIDW.copy()
                Transect.ElevationMin = ZMin.copy()
                Transect.ElevationMax = ZMax.copy()
                Transect.ElevStd = ZStd.copy()
                
                # update transect no
                CurrentTransect += 1
                
        print("")
    
    def AnalyseTransectMorphology(self, StormImpactAnalysis=None, FrontToeMin=-0.001):

        """

        Barrier focus for now

        MDH, June 2019
        
        NH edits: 
            Add StormImpactAnalysis selection to call revised FindBarrier2 and FindCliff2 functions.
            If not set, will call MDH original FindCliff and FindBarrier functions. 
        
            Add ability to set FrontToeMin when calling FindBarrier2: 
            FrontToeMin defined as minimum negative detrended elevation for new front toe. 
            Default is -0.001 (1mm) as per MDH original code.

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
                if StormImpactAnalysis == True:
                    # NH: Revised cliff detection: mask elevations < 0m
                    Transect.FindCliff2()
                    
                    # NH: Revised front toe detection
                    Transect.FindBarrier2(FrontToeMin=FrontToeMin)

                    # Save dune toe and crest elevations
                    Transect.SaveBarrierElevations()
                    
                    # Extract hinterland characteristics
                    Transect.ExtractHinterlandElevSlope()
                    
                    # Clear masks applied to Transect.Distance and Transect.Elevation
                    Transect.ClearTopographyMasks()
                    
                else:
                    Transect.FindCliff()
                    Transect.FindBarrier()
                
                # update transect progress no
                CurrentTransect += 1
        
        print("")
        
    def CalculateExtremeRunup(self, Scenario=None):
        
        """
        Implement the Stockdon (2006) equations that estimate 
        extreme runup R2 under storm wave conditions.
        
        Calcuation requires the foreshore slope, deepwater significant wave height
        and deepwater peak wave period. 
        
        This will allow the application of the Sallenger (2000) Storm Impace Scale 
        by comparing total water level with dune crest and toe elevations.

        Parameters
        ----------
        Scenario - string   
            - String describing the scenario of interest
            - Options: 
                - "Hist" = Historic 
                - "M45" = Mid-century RCP4.5
                - "M85" = Mid-century RCP8.8
                - "E45" = End-century RCP4.5
                - "E85" = End-century RCP8.5
        
        NH, November 2023
        
        """
        
        print("Coast.CalculateExtremeRunup: Estimating extreme wave runup under storm conditions")
        
        # check input parameters
        if not (Scenario == "Hist" or Scenario == "M45" or Scenario == "M85" or \
                Scenario == "E45" or Scenario == "E85"):
            print("\tInvalid Scenario:", Scenario)
            sys.exit()
        
        g = 9.81                                                                            # gravitational constant in m/s2
        Cp = 0.33                                                                           # Constant in Poate (2016) eq(12)
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                Bf = Transect.IntertidalSlope 
                
                if Scenario == "Hist":
                    Tp = Transect.H_Tp_p99                                                  # Offshore peak wave period
                    H0 = Transect.H_Hs_p99                                                  # Offshore significant wave height
                    L0 = g*Transect.H_Tp_p99**2/(2*np.pi)                                   # Stockdon eq(1)
                    Iribarren = Bf/np.sqrt(H0/L0)                                           # Stockdon eq(2)
                    """
                    if Transect.Shingle:
                        Transect.H_R2 = Cp*np.sqrt(Bf)*H0*Tp                                # Poate eq(12), modified by Blenkinsopp (2022) to use intertidal slope, to accommodate composite sand/gravel beaches
                        if Iribarren < 0.3:                                                 # extremely dissipative beach
                            Transect.H_setup = 0.016*np.sqrt(H0*L0)                         # Stockdon eq(16) 
                            Transect.H_Dissipative = True                                   # set flag for extremely dissipative beach
                        else:
                            Transect.H_setup = 0.35*Bf*np.sqrt(H0*L0)                       # Stockdon eq(10)
                            Transect.H_Dissipative = False
                    else: 
                    """                    
                    if Iribarren < 0.3:                                                 # extremely dissipative beach
                        Transect.H_R2 = 0.043*np.sqrt(H0*L0)                            # Stockdon eq(18): Extreme wave runup
                        Transect.H_setup = 0.016*np.sqrt(H0*L0)                         # Stockdon eq(16) 
                        Transect.H_Dissipative = True                                   # set flag for extremely dissipative beach
                    else:
                        Transect.H_R2 = 1.1*(0.35*Bf*np.sqrt(H0*L0) + \
                                        np.sqrt(H0*L0*(0.563*Bf**2 + 0.004))/2)         # Stockdon eq(19): Extreme wave runup (all other sandy beaches)
                        Transect.H_setup = 0.35*Bf*np.sqrt(H0*L0)                       # Stockdon eq(10)
                        Transect.H_Dissipative = False
                    
                    # save parameters 
                    Transect.H_WaveSteepness = H0/L0
                    Transect.H_Iribarren = Iribarren
                    
                elif Scenario == "M45":                                                     # repeat for each climate scenario
                    Tp = Transect.M45_Tp_p99
                    H0 = Transect.M45_Hs_p99
                    L0 = g*Transect.M45_Tp_p99**2/(2*np.pi)                                              
                    Iribarren = Bf/np.sqrt(H0/L0)
                    """
                    if Transect.Shingle:
                        Transect.M45_R2 = Cp*np.sqrt(Bf)*H0*Tp                                
                        if Iribarren < 0.3:                                                 
                            Transect.M45_setup = 0.016*np.sqrt(H0*L0)                         
                            Transect.M45_Dissipative = True                                   
                        else:
                            Transect.M45_setup = 0.35*Bf*np.sqrt(H0*L0)                      
                            Transect.M45_Dissipative = False
                    
                    else:
                    """
                    if Iribarren < 0.3:                                                
                        Transect.M45_R2 = 0.043*np.sqrt(H0*L0)    
                        Transect.M45_setup = 0.016*np.sqrt(H0*L0)                                   
                        Transect.M45_Dissipative = True
                    else:
                        Transect.M45_R2 = 1.1*(0.35*Bf*np.sqrt(H0*L0) + \
                                        np.sqrt(H0*L0*(0.563*Bf**2 + 0.004))/2) 
                        Transect.M45_setup = 0.35*Bf*np.sqrt(H0*L0)                         
                        Transect.M45_Dissipative = False 
                    
                    # save parameters 
                    Transect.M45_WaveSteepness = H0/L0
                    Transect.M45_Iribarren = Iribarren
                
                elif Scenario == "M85":
                    Tp = Transect.M85_Tp_p99
                    H0 = Transect.M85_Hs_p99
                    L0 = g*Transect.M85_Tp_p99**2/(2*np.pi)                                              
                    Iribarren = Bf/np.sqrt(H0/L0)
                    """
                    if Transect.Shingle:
                        Transect.M85_R2 = Cp*np.sqrt(Bf)*H0*Tp                                
                        if Iribarren < 0.3:                                                 
                            Transect.M85_setup = 0.016*np.sqrt(H0*L0)                         
                            Transect.M85_Dissipative = True                                   
                        else:
                            Transect.M85_setup = 0.35*Bf*np.sqrt(H0*L0)                      
                            Transect.M85_Dissipative = False
                    
                    else:
                    """
                    if Iribarren < 0.3:                                                
                        Transect.M85_R2 = 0.043*np.sqrt(H0*L0) 
                        Transect.M85_setup = 0.016*np.sqrt(H0*L0)                                
                        Transect.M85_Dissipative = True
                    else:
                        Transect.M85_R2 = 1.1*(0.35*Bf*np.sqrt(H0*L0) + \
                                        np.sqrt(H0*L0*(0.563*Bf**2 + 0.004))/2) 
                        Transect.M85_setup = 0.35*Bf*np.sqrt(H0*L0)                     
                        Transect.M85_Dissipative = False 
                            
                    # save parameters 
                    Transect.M85_WaveSteepness = H0/L0
                    Transect.M85_Iribarren = Iribarren
                                        
                elif Scenario == "E45":
                    Tp = Transect.E45_Tp_p99
                    H0 = Transect.E45_Hs_p99
                    L0 = g*Transect.E45_Tp_p99**2/(2*np.pi)                                              
                    Iribarren = Bf/np.sqrt(H0/L0)
                    """
                    if Transect.Shingle:
                        Transect.E45_R2 = Cp*np.sqrt(Bf)*H0*Tp                                
                        if Iribarren < 0.3:                                                 
                            Transect.E45_setup = 0.016*np.sqrt(H0*L0)                         
                            Transect.E45_Dissipative = True                                   
                        else:
                            Transect.E45_setup = 0.35*Bf*np.sqrt(H0*L0)                      
                            Transect.E45_Dissipative = False
                            
                    else:
                    """
                    if Iribarren < 0.3:                                                
                        Transect.E45_R2 = 0.043*np.sqrt(H0*L0)   
                        Transect.E45_setup = 0.016*np.sqrt(H0*L0)                                  
                        Transect.E45_Dissipative = True                        
                    else:
                        Transect.E45_R2 = 1.1*(0.35*Bf*np.sqrt(H0*L0) + \
                                        np.sqrt(H0*L0*(0.563*Bf**2 + 0.004))/2)
                        Transect.E45_setup = 0.35*Bf*np.sqrt(H0*L0)                       
                        Transect.E45_Dissipative = False
                            
                    # save parameters 
                    Transect.E45_WaveSteepness = H0/L0
                    Transect.E45_Iribarren = Iribarren
                                        
                elif Scenario == "E85":
                    Tp = Transect.E85_Tp_p99
                    H0 = Transect.E85_Hs_p99
                    L0 = g*Transect.E85_Tp_p99**2/(2*np.pi)                                              
                    Iribarren = Bf/np.sqrt(H0/L0)
                    """
                    if Transect.Shingle:
                        Transect.E85_R2 = Cp*np.sqrt(Bf)*H0*Tp                                
                        if Iribarren < 0.3:                                                 
                            Transect.E85_setup = 0.016*np.sqrt(H0*L0)                         
                            Transect.E85_Dissipative = True                                   
                        else:
                            Transect.E85_setup = 0.35*Bf*np.sqrt(H0*L0)                      
                            Transect.E85_Dissipative = False
                    
                    else:
                    """
                    if Iribarren < 0.3:                                                
                        Transect.E85_R2 = 0.043*np.sqrt(H0*L0)  
                        Transect.E85_setup = 0.016*np.sqrt(H0*L0)                                
                        Transect.E85_Dissipative = True  
                    else:
                        Transect.E85_R2 = 1.1*(0.35*Bf*np.sqrt(H0*L0) + \
                                        np.sqrt(H0*L0*(0.563*Bf**2 + 0.004))/2) 
                        Transect.E85_setup = 0.35*Bf*np.sqrt(H0*L0)                       
                        Transect.E85_Dissipative = False
                            
                    # save parameters 
                    Transect.E85_WaveSteepness = H0/L0
                    Transect.E85_Iribarren = Iribarren
                                        
                else:
                    print(f"\t{Transect.LineID}_{Transect.ID}:Invalid scenario {Scenario}") # should not ever get this

    def ExtractExtremeSeaLevel(self, Shapefile=None, Scenario=None, MaxDist=None):
        
        """
        Input data is SLR uplifted CFB2018 extreme still water levels, provided as
        dataproduct by UKCP18.
        Find nearest input data point within MaxDist (m) of transect.
        Extract 25-yr return level and its likely range for each point.
        Likely range: c1 = 5th percentile, c3 = 95th percentile of projected SLR
        
        Parameters
        ----------
        Shapefile : string 
            - geospatial point data vector location of ESL data
        Scenario : string
            - String describing the scenario of interest
            - Options: 
                - "Hist" = Historic 
                - "M45" = Mid-century RCP4.5
                - "M85" = Mid-century RCP8.8
                - "E45" = End-century RCP4.5
                - "E85" = End-century RCP8.5
        MaxDist : integer
            - Search radius in meters from CoastNode to ESL datapoint
            - Must be positive and less than 50 km
                
        NH, November 2023
        Revised July 2024 to pass MaxDist as parameter
        
        """
        
        print("Coast.ExtractExtremeSeaLevel: Extracting extreme still water level, uplifted according to climate change scenario")
        
        # check input parameters
        if not (Scenario == "Hist" or Scenario == "M45" or Scenario == "M85" or \
                Scenario == "E45" or Scenario == "E85"):
            print("\tInvalid Scenario:", Scenario)
            sys.exit()
            
        if not (MaxDist > 0 and MaxDist < 50000):
            print("\tInvalid search radius:", MaxDist)
            sys.exit()
            
        # read shapefile using geopandas
        GDF = gp.read_file(Shapefile)
        DataPoints = GDF['geometry']
        
        if len(DataPoints) == 0:
            print(f"\tNo Points in {Shapefile}!")
            return
        
        # Extract data: uplifted extreme still water levels for 25-yr return period, plus likely range
        t25_geoser = GDF["t25"]
        t25_c1_geoser = GDF["c1_t25"]
        t25_c3_geoser = GDF["c3_t25"]         
        
        # For each transect, find nearest ESL point to CoastNode
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                CoastPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                
                # extract nearest ESL index within 4 km of CoastNode
                nearest_idx_array = DataPoints.sindex.nearest(CoastPoint, max_distance=MaxDist) 
                nearest_idx = nearest_idx_array[1]
                     
                if len(nearest_idx) > 0:
                    t25 = t25_geoser[nearest_idx].values[0]                   # returns geoseries of index,value pair. get value only
                    t25_c1 = t25_c1_geoser[nearest_idx].values[0]                     
                    t25_c3 = t25_c3_geoser[nearest_idx].values[0]                    
                    
                else:
                    print(f"\t{Transect.LineID}_{Transect.ID}: No nearby points!")
                    sys.exit()
                    
                # save extracted ESL values to the given scenario
                if Scenario == "Hist":
                    Transect.H_ESL = t25
                    Transect.H_ESL_c1 = t25_c1
                    Transect.H_ESL_c3 = t25_c3
                    
                elif Scenario == "M45":
                    Transect.M45_ESL = t25
                    Transect.M45_ESL_c1 = t25_c1
                    Transect.M45_ESL_c3 = t25_c3
                
                elif Scenario == "M85":
                    Transect.M85_ESL = t25
                    Transect.M85_ESL_c1 = t25_c1
                    Transect.M85_ESL_c3 = t25_c3
                
                elif Scenario == "E45":
                    Transect.E45_ESL = t25
                    Transect.E45_ESL_c1 = t25_c1
                    Transect.E45_ESL_c3 = t25_c3
                
                elif Scenario == "E85":
                    Transect.E85_ESL = t25
                    Transect.E85_ESL_c1 = t25_c1
                    Transect.E85_ESL_c3 = t25_c3
                
                else:
                    print(f"\t{Transect.LineID}_{Transect.ID}:Invalid scenario {Scenario}")
           
                #print(f"\t{Transect.LineID}_{Transect.ID}:")
                #print(f"\t\tt25:{t25}, {Transect.H_ESL}")
                #print(f"\t\tc1: {t25_c1}, {Transect.H_ESL_c1}")
                #print(f"\t\tc3: {t25_c3}, {Transect.H_ESL_c3}")
    
    def CalculateTotalWaterLevel(self):
    
        """
        
        Adds up the extreme still water level and extreme wave runup 
        to estimate extreme total water level.
        Also calculate extreme wave setup. 
        Repeat for each climate scenario. Use 95th percentile SLR (c3 data in uplifted ESL).
        
        NH, Novembeer 2023
        
        """
        
        print("Coast.CalculateTotalWaterLevel: Adding extreme sea level to extreme wave runup")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                # Wave total extreme runup level (Stockdon 20006)
                Transect.H_TWL = Transect.H_ESL_c3 + Transect.H_R2
                Transect.M45_TWL = Transect.M45_ESL_c3 + Transect.M45_R2
                Transect.M85_TWL = Transect.M85_ESL_c3 + Transect.M85_R2
                Transect.E45_TWL = Transect.E45_ESL_c3 + Transect.E45_R2
                Transect.E85_TWL = Transect.E85_ESL_c3 + Transect.E85_R2
                
                # Wave setup component of extreme wave runup (Stockdon 2006)
                Transect.H_TWL_setup = Transect.H_ESL_c3 + Transect.H_setup
                Transect.M45_TWL_setup = Transect.M45_ESL_c3 + Transect.M45_setup
                Transect.M85_TWL_setup = Transect.M85_ESL_c3 + Transect.M85_setup
                Transect.E45_TWL_setup = Transect.E45_ESL_c3 + Transect.E45_setup
                Transect.E85_TWL_setup = Transect.E85_ESL_c3 + Transect.E85_setup
    
    def StormImpactScale(self):
    
        """
        Apply Sallenger (2000) Storm Impact Scale
        For future scenarios use adjusted dune elevations.
        
        NH, November 2023
        
        """
        
        print("Coast.StormImpactScale: Comparing total water level and dune elevations")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                if Transect.Barrier:
                    if Transect.H_TWL < Transect.H_FrontToe:
                        Transect.H_StormImpactScale = "Swash"
                    elif Transect.H_TWL > Transect.H_FrontToe and Transect.H_TWL < Transect.H_Crest:
                        Transect.H_StormImpactScale = "Collision"
                    elif Transect.H_TWL > Transect.H_Crest:
                        if Transect.H_TWL_setup > Transect.H_Crest:
                            Transect.H_StormImpactScale = "Inundation"
                        else:
                            Transect.H_StormImpactScale = "Overwash"
                    else:
                        print(f"\t{Transect.LineID}_{Transect.ID}: No assigned storm impact scale for Historic scenario!")
                    
                    if Transect.M45_TWL < Transect.M45_FrontToe:
                        Transect.M45_StormImpactScale = "Swash"
                    elif Transect.M45_TWL > Transect.M45_FrontToe and Transect.M45_TWL < Transect.M45_Crest:
                        Transect.M45_StormImpactScale = "Collision"
                    elif Transect.M45_TWL > Transect.M45_Crest:
                        if Transect.M45_TWL_setup > Transect.M45_Crest:
                            Transect.M45_StormImpactScale = "Inundation"
                        else:
                            Transect.M45_StormImpactScale = "Overwash"
                    else:
                        print(f"\t{Transect.LineID}_{Transect.ID}: No assigned storm impact scale for MidC RCP4.5 scenario!")
                        
                    if Transect.M85_TWL < Transect.M85_FrontToe:
                        Transect.M85_StormImpactScale = "Swash"
                    elif Transect.M85_TWL > Transect.M85_FrontToe and Transect.M85_TWL < Transect.M85_Crest:
                        Transect.M85_StormImpactScale = "Collision"
                    elif Transect.M85_TWL > Transect.M85_Crest:
                        if Transect.M85_TWL_setup > Transect.M85_Crest:
                            Transect.M85_StormImpactScale = "Inundation"
                        else:
                            Transect.M85_StormImpactScale = "Overwash"
                    else:
                        print(f"\t{Transect.LineID}_{Transect.ID}: No assigned storm impact scale for MidC RCP8.5 scenario!")
                        
                    if Transect.E45_TWL < Transect.E45_FrontToe:
                        Transect.E45_StormImpactScale = "Swash"
                    elif Transect.E45_TWL > Transect.E45_FrontToe and Transect.E45_TWL < Transect.E45_Crest:
                        Transect.E45_StormImpactScale = "Collision"
                    elif Transect.E45_TWL > Transect.E45_Crest:
                        if Transect.E45_TWL_setup > Transect.E45_Crest:
                            Transect.E45_StormImpactScale = "Inundation"
                        else:
                            Transect.E45_StormImpactScale = "Overwash"
                    else:
                        print(f"\t{Transect.LineID}_{Transect.ID}: No assigned storm impact scale for EndC RCP4.5 scenario!")
                        
                    if Transect.E85_TWL < Transect.E85_FrontToe:
                        Transect.E85_StormImpactScale = "Swash"
                    elif Transect.E85_TWL > Transect.E85_FrontToe and Transect.E85_TWL < Transect.E85_Crest:
                        Transect.E85_StormImpactScale = "Collision"
                    elif Transect.E85_TWL > Transect.E85_Crest:
                        if Transect.E85_TWL_setup > Transect.E85_Crest:
                            Transect.E85_StormImpactScale = "Inundation"
                        else:
                            Transect.E85_StormImpactScale = "Overwash"
                    else:
                        print(f"\t{Transect.LineID}_{Transect.ID}: No assigned storm impact scale for EndC RCP8.5 scenario!")
                else:
                    #print(f"\t{Transect.LineID}_{Transect.ID}: Not a barrier")
                    if (Transect.AssetPresent and Transect.FirstAssetDist < 200):   # If assets present near coast, apply Sallenger classfication to asset elevations
                        if Transect.H_TWL > Transect.FirstAssetElev:
                            if Transect.H_TWL_setup > Transect.FirstAssetElev:
                                Transect.H_StormImpactScale = "NB_Inundation"
                            else:
                                Transect.H_StormImpactScale = "NB_Overwash"
                        elif Transect.FirstAssetElev - Transect.H_TWL > 5.0:        # This 5 m breakpoint is arbitrary. Arguing that if no barrier present and assets > 5m higher than severe storm runuop, not of immediate concern. 
                            Transect.H_StormImpactScale = "NB_Swash"
                        else:
                            Transect.H_StormImpactScale = "NB_Collision"            # No brrier and assets < 5m above severe storm runup
                            
                        if Transect.M45_TWL > Transect.FirstAssetElev:
                            if Transect.M45_TWL_setup > Transect.FirstAssetElev:
                                Transect.M45_StormImpactScale = "NB_Inundation"
                            else:
                                Transect.M45_StormImpactScale = "NB_Overwash"
                        elif Transect.FirstAssetElev - Transect.M45_TWL > 5.0:       
                            Transect.M45_StormImpactScale = "NB_Swash"
                        else:
                            Transect.M45_StormImpactScale = "NB_Collision"  
                            
                        if Transect.M85_TWL > Transect.FirstAssetElev:
                            if Transect.M85_TWL_setup > Transect.FirstAssetElev:
                                Transect.M85_StormImpactScale = "NB_Inundation"
                            else:
                                Transect.M85_StormImpactScale = "NB_Overwash"
                        elif Transect.FirstAssetElev - Transect.M85_TWL > 5.0:       
                            Transect.M85_StormImpactScale = "NB_Swash"
                        else:
                            Transect.M85_StormImpactScale = "NB_Collision" 
                        
                        if Transect.E45_TWL > Transect.FirstAssetElev:
                            if Transect.E45_TWL_setup > Transect.FirstAssetElev:
                                Transect.E45_StormImpactScale = "NB_Inundation"
                            else:
                                Transect.E45_StormImpactScale = "NB_Overwash"
                        elif Transect.FirstAssetElev - Transect.E45_TWL > 5.0:       
                            Transect.E45_StormImpactScale = "NB_Swash"
                        else:
                            Transect.E45_StormImpactScale = "NB_Collision"
                            
                        if Transect.E85_TWL > Transect.FirstAssetElev:
                            if Transect.E85_TWL_setup > Transect.FirstAssetElev:
                                Transect.E85_StormImpactScale = "NB_Inundation"
                            else:
                                Transect.E85_StormImpactScale = "NB_Overwash"
                        elif Transect.FirstAssetElev - Transect.E85_TWL > 5.0:       
                            Transect.E85_StormImpactScale = "NB_Swash"
                        else:
                            Transect.E85_StormImpactScale = "NB_Collision"
                            
                    else:
                        Transect.H_StormImpactScale = "NB_NoAsset"
                        Transect.M45_StormImpactScale = "NB_NoAsset"
                        Transect.M85_StormImpactScale = "NB_NoAsset"
                        Transect.E45_StormImpactScale = "NB_NoAsset"
                        Transect.E85_StormImpactScale = "NB_NoAsset"
                    
                    
    def CountStormImpacts(self, subcell, OutputFilename, delimiter):
        
        """
        Function to count to total number of transects in the given subcell,
        and the total number predicted of each storm regime, for each climate scenario.
       
        Write out to .csv file
        
        """
        
        # initialise all counts
        H_SwashCount = 0
        H_CollisionCount = 0
        H_OverwashCount = 0
        H_InundationCount = 0
        H_NB_SwashCount = 0
        H_NB_CollisionCount = 0
        H_NB_OverwashCount = 0
        H_NB_InundationCount = 0
        H_NB_NoAssetCount = 0
        
        M45_SwashCount = 0
        M45_CollisionCount = 0
        M45_OverwashCount = 0
        M45_InundationCount = 0
        M45_NB_SwashCount = 0
        M45_NB_CollisionCount = 0
        M45_NB_OverwashCount = 0
        M45_NB_InundationCount = 0
        M45_NB_NoAssetCount = 0
        
        M85_SwashCount = 0
        M85_CollisionCount = 0
        M85_OverwashCount = 0
        M85_InundationCount = 0
        M85_NB_SwashCount = 0
        M85_NB_CollisionCount = 0
        M85_NB_OverwashCount = 0
        M85_NB_InundationCount = 0
        M85_NB_NoAssetCount = 0
        
        E45_SwashCount = 0
        E45_CollisionCount = 0
        E45_OverwashCount = 0
        E45_InundationCount = 0
        E45_NB_SwashCount = 0
        E45_NB_CollisionCount = 0
        E45_NB_OverwashCount = 0
        E45_NB_InundationCount = 0
        E45_NB_NoAssetCount = 0
        
        E85_SwashCount = 0
        E85_CollisionCount = 0
        E85_OverwashCount = 0
        E85_InundationCount = 0
        E85_NB_SwashCount = 0
        E85_NB_CollisionCount = 0
        E85_NB_OverwashCount = 0
        E85_NB_InundationCount = 0
        E85_NB_NoAssetCount = 0
        
        NoTransects = np.sum([Line.NoTransects for Line in self.CoastLines])
        print("NoTransects =", NoTransects)
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                #print(Transect.LineID, Transect.ID)
                match Transect.H_StormImpactScale:              # works
                    case "Swash":
                        H_SwashCount += 1
                    case "Collision":
                        H_CollisionCount += 1
                    case "Overwash":
                        H_OverwashCount += 1
                    case "Inundation":
                        H_InundationCount += 1
                    case "NB_Swash":
                        H_NB_SwashCount += 1
                    case "NB_Collision":
                        H_NB_CollisionCount += 1
                    case "NB_Overwash":
                        H_NB_OverwashCount += 1
                    case "NB_Inundation":
                        H_NB_InundationCount += 1
                    case "NB_NoAsset":
                        H_NB_NoAssetCount += 1
                    case _:
                        print(Transect.LineID, Transect.ID, "No assigned historical storm regime!")
                        
                match Transect.M45_StormImpactScale:            
                    case "Swash":
                        M45_SwashCount += 1
                    case "Collision":
                        M45_CollisionCount += 1
                    case "Overwash":
                        M45_OverwashCount += 1
                    case "Inundation":
                        M45_InundationCount += 1
                    case "NB_Swash":
                        M45_NB_SwashCount += 1
                    case "NB_Collision":
                        M45_NB_CollisionCount += 1
                    case "NB_Overwash":
                        M45_NB_OverwashCount += 1
                    case "NB_Inundation":
                        M45_NB_InundationCount += 1
                    case "NB_NoAsset":
                        M45_NB_NoAssetCount += 1
                    case _:
                        print(Transect.LineID, Transect.ID, "No assigned M45 storm regime!")
                        
                match Transect.M85_StormImpactScale:            
                    case "Swash":
                        M85_SwashCount += 1
                    case "Collision":
                        M85_CollisionCount += 1
                    case "Overwash":
                        M85_OverwashCount += 1
                    case "Inundation":
                        M85_InundationCount += 1
                    case "NB_Swash":
                        M85_NB_SwashCount += 1
                    case "NB_Collision":
                        M85_NB_CollisionCount += 1
                    case "NB_Overwash":
                        M85_NB_OverwashCount += 1
                    case "NB_Inundation":
                        M85_NB_InundationCount += 1
                    case "NB_NoAsset":
                        M85_NB_NoAssetCount += 1
                    case _:
                        print(Transect.LineID, Transect.ID, "No assigned M85 storm regime!")
                        
                match Transect.E45_StormImpactScale:            
                    case "Swash":
                        E45_SwashCount += 1
                    case "Collision":
                        E45_CollisionCount += 1
                    case "Overwash":
                        E45_OverwashCount += 1
                    case "Inundation":
                        E45_InundationCount += 1
                    case "NB_Swash":
                        E45_NB_SwashCount += 1
                    case "NB_Collision":
                        E45_NB_CollisionCount += 1
                    case "NB_Overwash":
                        E45_NB_OverwashCount += 1
                    case "NB_Inundation":
                        E45_NB_InundationCount += 1
                    case "NB_NoAsset":
                        E45_NB_NoAssetCount += 1
                    case _:
                        print(Transect.LineID, Transect.ID, "No assigned E45 storm regime!")
                        
                match Transect.E85_StormImpactScale:            
                    case "Swash":
                        E85_SwashCount += 1
                    case "Collision":
                        E85_CollisionCount += 1
                    case "Overwash":
                        E85_OverwashCount += 1
                    case "Inundation":
                        E85_InundationCount += 1
                    case "NB_Swash":
                        E85_NB_SwashCount += 1
                    case "NB_Collision":
                        E85_NB_CollisionCount += 1
                    case "NB_Overwash":
                        E85_NB_OverwashCount += 1
                    case "NB_Inundation":
                        E85_NB_InundationCount += 1
                    case "NB_NoAsset":
                        E85_NB_NoAssetCount += 1
                    case _:
                        print(Transect.LineID, Transect.ID, "No assigned E85 storm regime!")
        
        """        
        print("Sw=", H_SwashCount)
        print("Col=", H_CollisionCount)
        print("Ov=", H_OverwashCount)
        print("In=", H_InundationCount)
        print("NSw=", H_NB_SwashCount)
        print("NCol=", H_NB_CollisionCount)
        print("NOv=", H_NB_OverwashCount)
        print("NIn=", H_NB_InundationCount)
        print("NNA=", H_NB_NoAssetCount)
        """
        
        # open csv fle in appand mode, save counts for current subcell. works
        f = open(OutputFilename,'a')
        f.write(subcell + delimiter + str(NoTransects) + delimiter +\
                str(H_SwashCount) + delimiter + str(H_CollisionCount) + delimiter + str(H_OverwashCount) + delimiter + str(H_InundationCount) + delimiter +\
                str(H_NB_SwashCount) + delimiter + str(H_NB_CollisionCount) + delimiter + str(H_NB_OverwashCount) + delimiter + str(H_NB_InundationCount) + delimiter + str(H_NB_NoAssetCount) + delimiter +\
                str(M45_SwashCount) + delimiter + str(M45_CollisionCount) + delimiter + str(M45_OverwashCount) + delimiter + str(M45_InundationCount) + delimiter +\
                str(M45_NB_SwashCount) + delimiter + str(M45_NB_CollisionCount) + delimiter + str(M45_NB_OverwashCount) + delimiter + str(M45_NB_InundationCount) + delimiter + str(M45_NB_NoAssetCount) + delimiter +\
                str(M85_SwashCount) + delimiter + str(M85_CollisionCount) + delimiter + str(M85_OverwashCount) + delimiter + str(M85_InundationCount) + delimiter +\
                str(M85_NB_SwashCount) + delimiter + str(M85_NB_CollisionCount) + delimiter + str(M85_NB_OverwashCount) + delimiter + str(M85_NB_InundationCount) + delimiter + str(M85_NB_NoAssetCount) + delimiter +\
                str(E45_SwashCount) + delimiter + str(E45_CollisionCount) + delimiter + str(E45_OverwashCount) + delimiter + str(E45_InundationCount) + delimiter +\
                str(E45_NB_SwashCount) + delimiter + str(E45_NB_CollisionCount) + delimiter + str(E45_NB_OverwashCount) + delimiter + str(E45_NB_InundationCount) + delimiter + str(E45_NB_NoAssetCount) + delimiter +\
                str(E85_SwashCount) + delimiter + str(E85_CollisionCount) + delimiter + str(E85_OverwashCount) + delimiter + str(E85_InundationCount) + delimiter +\
                str(E85_NB_SwashCount) + delimiter + str(E85_NB_CollisionCount) + delimiter + str(E85_NB_OverwashCount) + delimiter + str(E85_NB_InundationCount) + delimiter + str(E85_NB_NoAssetCount) + "\n")
        f.close()
    
    def CalculateHeadroom(self):
        
        """
        Calcualte the difference between the dune crest and estimated total water level
        for each climate scenario
        
        NH, Feb 2024
        
        """
        
        print("Coast.CalcualteHeadroom: Finding the difference between total water level and dune crest")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                if Transect.Barrier:
                    Transect.H_Headroom = Transect.H_Crest - Transect.H_TWL
                    Transect.M45_Headroom = Transect.M45_Crest - Transect.M45_TWL
                    Transect.M85_Headroom = Transect.M85_Crest - Transect.M85_TWL
                    Transect.E45_Headroom = Transect.E45_Crest - Transect.E45_TWL
                    Transect.E85_Headroom = Transect.E85_Crest - Transect.E85_TWL
                #else:
                    #print(f"\t{Transect.LineID}_{Transect.ID}: Not a barrier")
    
    
    def FindNearestIndex(self, Shapefile=None):
    
        """
        Find index of nearest DC2 transect to Transect.CoastNode
        Look only within 200 m of CoastNode
        Save to Transect.NearestDC2Idx
        
        Parameters
        ----------
        Shapefile - string 
            - geospatial multiline vector of DC2 transects
            
        NH, November 2023
        
        """
        
        print("Coast.FindNearestIndex: Saving index of nearest DC2 transect")
            
        # read shapefile using geopandas
        GDF = gp.read_file(Shapefile)
        TransectsGeom = GDF['geometry']
        
        if len(TransectsGeom) == 0:
            print(f"\tNo geometries in {Shapefile}!")
            return
            
        #if __debug__:
        #    print(f"\tNumber of geometries = {len(TransectsGeom)}")
        #    print(TransectsGeom[0:5])
        
        for Line in self.CoastLines:
            for Transect in Line.Transects: 
                CoastPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                
                # extract nearest DC2 transect index within 200m of CoastNode
                # returns input index in [0] (in the case of a point this is always 0), nearest index of TransectsGeom in [1]
                nearest_idx_array = TransectsGeom.sindex.nearest(CoastPoint, max_distance=200) 
                
                # if no DC2 transect within 200 m of my transect, set index to None
                if len(nearest_idx_array[1]) == 0:
                    #print(f"\t{Transect.LineID}_{Transect.ID}:{nearest_idx_array[1]}")
                    Transect.NearestDC2Idx = None
                
                else:                
                    # save index to Transect
                    Transect.NearestDC2Idx = nearest_idx_array[1]           
                
                
                    
    def ExtractFutureErosion(self, Shapefile=None, Scenario=None):
    
        """
        Extract predicted future erosion from DC2 transect.
        Requires Transect.NearestDC2Idx to be set by calling Coast.FindNearestIndex.
        
        Parameters
        ----------
        Shapefile - string 
            - geospatial multiline vector of DC2 transects for given climate scenario
        Scenario - string 
            - Climate change scenario of interest
            - Options: "RCP4" / "RCP8"
            
        NH, November 2023
        
        """
        
        print(f"Coast.ExtractFutureErosion: Read the predicted future erosion from DC2 transect for scenario {Scenario}")
        
        # check input parameters
        if not (Scenario == "RCP4" or Scenario == "RCP8"):
            print("\tInvalid Scenario:", Scenario)
            sys.exit()
            
        # read shapefile using geopandas
        GDF = gp.read_file(Shapefile)
        Erosion_2050 = GDF['Tot_E_2050']
        Erosion_2100 = GDF['Tot_E_2100']
        
        if len(Erosion_2050) == 0 or len(Erosion_2100) == 0:
            print(f"\tNo erosion data in {Shapefile}!")
            return
        
        for Line in self.CoastLines:
            for Transect in Line.Transects: 
            
                if not Transect.NearestDC2Idx:
                    print(f"\t{Transect.LineID}_{Transect.ID}: No value for Transect.NearestDC2Idx")
                    continue
                    
                # save predicted erosion values to given scenario
                if Scenario == "RCP4":
                    Transect.M45_Erosion = Erosion_2050[Transect.NearestDC2Idx].values[0] 
                    Transect.E45_Erosion = Erosion_2100[Transect.NearestDC2Idx].values[0] 
                
                elif Scenario == "RCP8":
                    Transect.M85_Erosion = Erosion_2050[Transect.NearestDC2Idx].values[0] 
                    Transect.E85_Erosion = Erosion_2100[Transect.NearestDC2Idx].values[0] 
    
    def ExtractHistoricCoastalChange(self, Shapefile=None):
    
        """
        Extract historic change rates in m/yr from the DC2 transect shapefile dataset.
        Save to storm impact transect. 
        Requires Transect.NearestDC2Idx to be set by calling Coast.FindNearestIndex.
        
        Parameters
        ----------
        Shapefile - string 
            - geospatial multiline vector of DC2 transects for given climate scenario
            
        NH, Jan 2024
        
        """
        
        print(f"Coast.ExtractHistoricCoastalChange: Read historic change rate for nearest DC2 transect")
        
        # read shapefile using geopandas
        GDF = gp.read_file(Shapefile)
        HistRate = GDF['Hist_Rate']
        
        if len(HistRate) == 0:
            print(f"\tNo historic change rate data in {Shapefile}!")
            return
            
        for Line in self.CoastLines:
            for Transect in Line.Transects: 
            
                if Transect.NearestDC2Idx == None:
                    print(f"\t{Transect.LineID}_{Transect.ID}: No value for Transect.NearestDC2Idx")
                    Transect.Hist_Rate = None            # set to None so can check for this later when value gets used
                    continue
                    
                Transect.Hist_Rate = HistRate[Transect.NearestDC2Idx].values[0] 
        
                #print(f"\t{Transect.LineID}_{Transect.ID}:\tHistRate:{Transect.Hist_Rate}")
                
    def ExtractSeaLevelRise(self, Shapefile=None, MaxDist=None):
    
        """
        Extract UKCP18 sea level rise projections from nearest point in shapefile
        Extract 50th percentile for all scenarios: RCP4.5, RCP8.5, 2050, 2100
        Save to Transect
        
        Parameters
        ----------
        Shapefile - string    
            - location of shapefile with SLR data
            - 14 column names: "lon" "lat" 
                               "SLR_M45_c1" "SLR_M45_c2" "SLR_M45_c3" 
                               "SLR_E45_c1" "SLR_E45_c2" "SLR_E45_c3"
                               "SLR_M85_c1" "SLR_M85_c2" "SLR_M85_c3" 
                               "SLR_E85_c1" "SLR_E85_c2" "SLR_E85_c3" 
            - c1 = 5th percentile, c2 = 50th percentile, c3 = 95th percentile of model simulations
            
        MaxDist - integer
            - Search radius in meters from CoastNode to SLR data
            - must be positive and less than 50 km
        
        NH, November 2023
        Revised July 2024 to pass in MaxDist
        
        """
        
        print("Coast.ExtractSeaLevelRise: Extracting UKCP18 SLR projections")
        
        # check input parameters
        if not (MaxDist > 0 and MaxDist < 50000):
            print("\tInvalid search radius:", MaxDist)
            sys.exit()
        
        # read shapefile using geopandas
        GDF = gp.read_file(Shapefile)
        VectorPoints = GDF['geometry']
        
        if len(VectorPoints) == 0:
            print(f"\tNo Points in {Shapefile}!")
            sys.exit()
        
        # Extract data: future projected SLR for different CC scenearios and years. c3=95th percentile
        SLR_M45_geoser = GDF["SLR_M45_c3"]
        SLR_E45_geoser = GDF["SLR_E45_c3"]
        SLR_M85_geoser = GDF["SLR_M85_c3"]
        SLR_E85_geoser = GDF["SLR_E85_c3"]        
        
        # For each transect, find nearest SLR point to CoastNode
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                CoastPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                
                # extract nearest SLR vector index within MAX_DIST of CoastNode
                nearest_idx_array = VectorPoints.sindex.nearest(CoastPoint, max_distance=MaxDist) 
                nearest_idx = nearest_idx_array[1]
                
                if len(nearest_idx) > 0:
                    SLR_M45 = SLR_M45_geoser[nearest_idx].values[0]                   # returns geoseries of index,value pair. get value only
                    SLR_E45 = SLR_E45_geoser[nearest_idx].values[0]   
                    SLR_M85 = SLR_M85_geoser[nearest_idx].values[0]      
                    SLR_E85 = SLR_E85_geoser[nearest_idx].values[0] 
                    
                else:
                    print(f"\t{Transect.LineID}_{Transect.ID}: No nearby points")
                    continue
                    
                # save extracted ESL values to the given scenario                
                Transect.M45_SLR = SLR_M45
                Transect.E45_SLR = SLR_E45
                Transect.M85_SLR = SLR_M85
                Transect.E85_SLR = SLR_E85
                
                #print(f"\t{Transect.LineID}_{Transect.ID}:")
                #print(f"\t\tM45_SLR:{Transect.M45_SLR} \tE45_SLR:{Transect.E45_SLR} \tM85_SLR:{Transect.M85_SLR} \tE85_SLR:{Transect.E85_SLR}")
    
    def AdjustFutureDuneElevations(self):
    
        """
        According to the below conceptual model of dune evolution, adjust dune 
        front toe and crest elevations for future storm impact analysis. 
        
        Conceptual model of dune evolution:
        For a future of accelerating SLR and increased annual extreme water level events predicted by UKCP18, 
        and our understanding of the processes that control foredune evolution, the conceptual model for 
        dune toe and crest elevation proposed for this study is:
        a.	On the assumption that sediment remains in the system, foredune toe elevation will keep pace 
            with SLR until 2050 and 2100, regardless of sediment budget.
        b.	Foredune crests of historically stable or accreting beaches will keep pace with SLR until 2050. 
            After 2050 when SLR is expected to accelerate dramatically, accretion could turn into stability or erosion, 
            and foredune crests will no longer increase at the same rate as SLR. 
            For 2100 model scenarios of historically stable or accreting beaches, dune crest elevations are thus maintained at 2050 levels.
        c.	Foredune crests of historically eroding beaches do not keep pace with SLR and remain at present day elevations for both 2050 and 2100.
        d.	In the event of future foredune/berm toe elevations exceeding future crest elevations, due to toes keeping pace with SLR and crests not, 
            future crest elevations are set to equal future toe elevations, to make sense from a morphological perspective.
        
        Need to know future SLR from Coast.ExtractSeaLevelRise.
        
        NH, Jan 2024
    
        """
        
        print(f"Coast.AdjustFutureDuneElevations: Adjusting future dune toe and crest elevations for storm impact analysis")
        
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                
                # Only adjust elevations if transect contains a barrier
                if Transect.Barrier:
                    
                    # Increase barrier TOE elevations to keep pace with SLR, regardless of sediment budget
                    Transect.M45_FrontToe = Transect.H_FrontToe + Transect.M45_SLR
                    Transect.E45_FrontToe = Transect.H_FrontToe + Transect.E45_SLR
                    Transect.M85_FrontToe = Transect.H_FrontToe + Transect.M85_SLR
                    Transect.E85_FrontToe = Transect.H_FrontToe + Transect.E85_SLR
                
                    # If no nearby DC2 transect found, historic sediment budget is not known. Treat as if barrier is eroding (percautionary):
                    # Barrier CREST elevations maintained at present-day levels for 2050 and 2100
                    if Transect.Hist_Rate == None:
                        Transect.M45_Crest = Transect.H_Crest
                        Transect.E45_Crest = Transect.H_Crest
                        Transect.M85_Crest = Transect.H_Crest
                        Transect.E85_Crest = Transect.H_Crest
                        
                    else:
                        # Historic trend of erosion (negative sediment budget): Barrier crest elevations maintained at present-day levels for 2050 and 2100
                        if Transect.Hist_Rate < 0.:
                            Transect.M45_Crest = Transect.H_Crest
                            Transect.E45_Crest = Transect.H_Crest
                            Transect.M85_Crest = Transect.H_Crest
                            Transect.E85_Crest = Transect.H_Crest
                        
                        # Historically stable or accreting (positive sediment budget): Barrier crest elevations keep pace with SLR until 2050
                        else:
                            Transect.M45_Crest = Transect.H_Crest + Transect.M45_SLR
                            Transect.E45_Crest = Transect.M45_Crest
                            Transect.M85_Crest = Transect.H_Crest + Transect.M85_SLR
                            Transect.E85_Crest = Transect.M85_Crest
                    
                    # Check if future toe elevation exceeds future crest elevation: set to equal and set flag
                    if Transect.M45_FrontToe > Transect.M45_Crest:
                        print(f"\t{Transect.LineID}_{Transect.ID}: M45 toe>crest!")
                        Transect.M45_Crest = Transect.M45_FrontToe
                        Transect.M45_BarrierDrowning = True
                    else:
                        Transect.M45_BarrierDrowning = False
                        
                    if Transect.E45_FrontToe > Transect.E45_Crest:
                        print(f"\t{Transect.LineID}_{Transect.ID}: E45 toe>crest!")
                        Transect.E45_Crest = Transect.E45_FrontToe
                        Transect.E45_BarrierDrowning = True
                    else:
                        Transect.E45_BarrierDrowning = False
                        
                    if Transect.M85_FrontToe > Transect.M85_Crest:
                        print(f"\t{Transect.LineID}_{Transect.ID}: M85 toe>crest!")
                        Transect.M85_Crest = Transect.M85_FrontToe
                        Transect.M85_BarrierDrowning = True
                    else:
                        Transect.M85_BarrierDrowning = False
                        
                    if Transect.E85_FrontToe > Transect.E85_Crest:
                        print(f"\t{Transect.LineID}_{Transect.ID}: E85 toe>crest!")
                        Transect.E85_Crest = Transect.E85_FrontToe
                        Transect.E85_BarrierDrowning = True
                    else:
                        Transect.E85_BarrierDrowning = False
                    
                    """
                    if Transect.Hist_Rate == None:
                        Transect.M45_FrontToe = Transect.H_FrontToe
                        Transect.E45_FrontToe = Transect.H_FrontToe
                        Transect.M85_FrontToe = Transect.H_FrontToe
                        Transect.E85_FrontToe = Transect.H_FrontToe
                        
                        Transect.M45_Crest = Transect.H_Crest
                        Transect.E45_Crest = Transect.H_Crest
                        Transect.M85_Crest = Transect.H_Crest
                        Transect.E85_Crest = Transect.H_Crest
                        
                    else:
                        # Historically stable or eroding coastline (rate < 0.25 m/yr chosen from qual comp w DC2 RCP8.5 2050 and 2100 erosion predictions):
                        # Dune toe and crest elevations maintained at present-day levels for 2050 and 2100 (i.e. cannot keep pace with SLR)
                        if Transect.Hist_Rate < 0.25:
                            Transect.M45_FrontToe = Transect.H_FrontToe
                            Transect.E45_FrontToe = Transect.H_FrontToe
                            Transect.M85_FrontToe = Transect.H_FrontToe
                            Transect.E85_FrontToe = Transect.H_FrontToe
                            
                            Transect.M45_Crest = Transect.H_Crest
                            Transect.E45_Crest = Transect.H_Crest
                            Transect.M85_Crest = Transect.H_Crest
                            Transect.E85_Crest = Transect.H_Crest
                        
                        # Historically accreting coastline: Increase elevations with SLR to 2050, maintain constant thereafter
                        else:
                            Transect.M45_FrontToe = Transect.H_FrontToe + Transect.M45_SLR
                            Transect.E45_FrontToe = Transect.M45_FrontToe
                            Transect.M85_FrontToe = Transect.H_FrontToe + Transect.M85_SLR
                            Transect.E85_FrontToe = Transect.M85_FrontToe
                            
                            Transect.M45_Crest = Transect.H_Crest + Transect.M45_SLR
                            Transect.E45_Crest = Transect.M45_Crest
                            Transect.M85_Crest = Transect.H_Crest + Transect.M85_SLR
                            Transect.E85_Crest = Transect.M85_Crest
                    """
                #if Transect.ID == '36':
                    #print(f"\t{Transect.LineID}_{Transect.ID}: HistRate:{Transect.Hist_Rate} \tToe:{Transect.H_FrontToe}\tCrest:{Transect.H_Crest}")
                    #print(f"\t\tM45_SLR:{Transect.M45_SLR},\tM45Toe:{Transect.M45_FrontToe}, E45Toe:{Transect.E45_FrontToe} \tM85_SLR:{Transect.M85_SLR} M85Toe:{Transect.M85_FrontToe} E85Toe:{Transect.E85_FrontToe}")
                    #print(f"\t\tM45Crest:{Transect.M45_Crest}, E45Crest:{Transect.E45_Crest} M85Crest:{Transect.M85_Crest} E85Crest:{Transect.E85_Crest}")
    
    def AnalyseExtremeWater(self, WaterElevs):
        
        """
        
        Finds position of extreme water at given elevations e.g. high water

        MDH, June 2022

        """

        print("Coast.AnalyseExtremeWater: Finding water surface positions at a given elevations and calculating metrics")

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
                Transect.FindExtremeWaterIntersections(WaterElevs)

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
                Transect.Rocky = GroupList[Counter]
                Counter += 1

    def GetFutureShoreLinesProximity(self, BufferDistance):

        Lines = []

        # Loop through prediction years
        for Year in self.FutureShoreLinesYears:

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
                
                # get a list of the start and end points of contiguous lines
                StartEndFlags = np.diff(FutureBool)
                
                # if first element is true this is a start point
                if FutureBool[0]:
                    StartEndFlags[0] = 1
                
                # if last line finishes on a start flag then remove
                if StartEndFlags[-1] == 1:
                    StartEndFlags[-1] = 0
                
                # if no start flags
                if len(StartEndFlags.nonzero()[0]) == 0:
                    continue
                
                # if last line finishes on last node then flag as end flag
                if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                    StartEndFlags[-1] = -1

                StartList = np.argwhere(StartEndFlags == 1).flatten()
                EndList = np.argwhere(StartEndFlags == -1).flatten()
                
                if len(StartList) < 1:
                    continue
                
                if not len(StartList) == len(EndList):
                    print("Start and End lists not the same length")
                    print(len(StartList),len(EndList))
                    import pdb
                    pdb.set_trace()
                    
                for i in range(0,len(StartList)):
                    
                    # catch single node cliff lines and ignore
                    if (EndList[i]-StartList[i]<2):
                        continue

                    # create empty lists for storing future nodes
                    ProximityList = []
                    
                    # add latest MHWS from previous node to start
                    # might need some logic here for first transect
                    if StartList[i] == 0:
                        FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                        ii = 1
                    else:
                        FirstNode = CoastLine.Transects[StartList[i]-1].get_RecentPosition()
                        ii = 0
                        if not FirstNode:
                            FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                            ii= 1
                    
                    if not FirstNode:
                        import pdb
                        pdb.set_trace()
                        
                    ProximityList.append(FirstNode)
                    
                    # loop through transects and get future positions
                    for Transect in CoastLine.Transects[StartList[i]+ii:EndList[i]]:
                        
                        if Transect.get_FutureDistance(Year) > Transect.get_RecentDistance():
                            Distance = Transect.get_FutureDistance(Year) + BufferDistance
                            TempNode = Transect.get_Position(Distance)
                            ProximityList.append(TempNode)
                        
                        else:
                            ProximityList.append(Transect.get_RecentPosition())
                        
                                                
                    # add latest MHWS from next node to end
                    # might need some logic here to finish
                    if not CoastLine.Transects[EndList[i]].get_RecentPosition():
                        LastNode = CoastLine.Transects[EndList[i]-1].get_RecentPosition()
                    else:
                        LastNode = CoastLine.Transects[EndList[i]].get_RecentPosition()
                    
                    ProximityList.append(LastNode)
                    
                    # create new line object for top
                    try:
                        X = [ProximityNode.X for ProximityNode in ProximityList]
                        Y = [ProximityNode.Y for ProximityNode in ProximityList]
                    except:
                        import pdb
                        pdb.set_trace()
                        
                    TempLine = Line("Proximity_"+str(FutureCount), X, Y, Year=Year)
                    Lines.append(TempLine)
                    
                    # update counter
                    FutureCount += 1

        return Lines

    def GetFutureShoreLines(self):

        """

        Extracts contiguous lines of future predicted MHWS

        """
        self.FutureShoreLines = []

        # Loop through prediction years
        for Year in self.FutureShoreLinesYears:

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
                
                # get a list of the start and end points of contiguous lines
                StartEndFlags = np.diff(FutureBool)
                
                # if first element is true this is a start point
                if FutureBool[0]:
                    StartEndFlags[0] = 1
                
                # if last line finishes on a start flag then remove
                if StartEndFlags[-1] == 1:
                    StartEndFlags[-1] = 0
                
                # if no start flags
                if len(StartEndFlags.nonzero()[0]) == 0:
                    continue
                
                # if last line finishes on last node then flag as end flag
                if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                    StartEndFlags[-1] = -1

                StartList = np.argwhere(StartEndFlags == 1).flatten()
                EndList = np.argwhere(StartEndFlags == -1).flatten()
                
                if len(StartList) < 1:
                    continue
                
                if not len(StartList) == len(EndList):
                    print("Start and End lists not the same length")
                    print(len(StartList),len(EndList))
                    import pdb
                    pdb.set_trace()
                    
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
                        ii = 1
                    else:
                        FirstNode = CoastLine.Transects[StartList[i]-1].get_RecentPosition()
                        ii = 0
                        if not FirstNode:
                            FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                            ii= 1
                    
                    if not FirstNode:
                        import pdb
                        pdb.set_trace()
                        
                    FutureList.append(FirstNode)
                    
                    # loop through transects and get future positions
                    for Transect in CoastLine.Transects[StartList[i]+ii:EndList[i]]:
                        
                        if Transect.get_FutureDistance(Year) > Transect.get_RecentDistance():
                            TempNode = Transect.get_FuturePosition(Year)
                            FutureList.append(TempNode)
                        
                        else:
                            FutureList.append(Transect.get_RecentPosition())
                        
                                                
                    # add latest MHWS from next node to end
                    # might need some logic here to finish
                    if not CoastLine.Transects[EndList[i]].get_RecentPosition():
                        LastNode = CoastLine.Transects[EndList[i]-1].get_RecentPosition()
                    else:
                        LastNode = CoastLine.Transects[EndList[i]].get_RecentPosition()
                    
                    FutureList.append(LastNode)
                    
                    # create new line object for top
                    try:
                        X = [FutureNode.X for FutureNode in FutureList]
                        Y = [FutureNode.Y for FutureNode in FutureList]
                    except:
                        import pdb
                        pdb.set_trace()
                        
                    TempLine = Line("FutureCoast_"+str(FutureCount), X, Y, Year=Year)
                    self.FutureShoreLines.append(TempLine)
                    
                    # update counter
                    FutureCount += 1
    
    def GetFutureShorelineUncertainty(self, Year=2100):

        """
        
        Extracts contiguous lines of uncertainty on Bruun Rule predictions to 2100
        
        MDH, March 2020

        """

        
        # keep track of no of coastal segments for IDs
        FutureCount = 0
        self.FutureMinUncertainty = []
        self.FutureMaxUncertainty = []

        # loop through transects and get contiguous locations where there are predictions
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
            
            # if first element is true this is a start point
            if FutureBool[0]:
                StartEndFlags[0] = 1
            
            # if last line finishes on a start flag then remove
            if StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
            
            # if no start flags
            if len(StartEndFlags.nonzero()[0]) == 0:
                continue
            
            # if last line finishes on last node then flag as end flag
            if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                StartEndFlags[-1] = -1
            
            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()
            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                print(len(StartList),len(EndList))
                import pdb
                pdb.set_trace()
                
            for i in range(0,len(StartList)):
                
                # catch single node cliff lines and ignore
                if (EndList[i]-StartList[i]<2):
                    continue

                # create empty lists for storing future nodes for min and max predictions
                FutureMinList = []
                FutureMaxList = []
                
                # add latest MHWS from previous node to start
                # might need some logic here for first transect
                if StartList[i] == 0:
                    FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                    ii = 1
                else:
                    FirstNode = CoastLine.Transects[StartList[i]-1].get_RecentPosition()
                    ii = 0
                    if not FirstNode:
                        FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                        ii= 1
                            
                FutureMinList.append(FirstNode)
                FutureMaxList.append(FirstNode)

                # loop through transects and get min and max future positions
                for Transect in CoastLine.Transects[StartList[i]+ii:EndList[i]]:
                    Transect.PredictFutureShorelineUncertainty(Year)
                    FutureMinNode = Transect.FutureShorelinesMinNode
                    try:
                        FutureMaxNode = Transect.FutureShorelinesMaxNode
                    except:
                        import pdb
                        pdb.set_trace()
                    FutureMinList.append(FutureMinNode)
                    FutureMaxList.append(FutureMaxNode)
                    
                # add latest MHWS from next node to end
                # might need some logic here to finish
                # add latest MHWS from next node to end
                # might need some logic here to finish
                if not CoastLine.Transects[EndList[i]].get_RecentPosition():
                    LastNode = CoastLine.Transects[EndList[i]-1].get_RecentPosition()
                else:
                    LastNode = CoastLine.Transects[EndList[i]].get_RecentPosition()
                    
                FutureMinList.append(LastNode)
                FutureMaxList.append(LastNode)
                
                try:
                    # create new line object for min and max
                    X = [FutureMinNode.X for FutureMinNode in FutureMinList]
                    Y = [FutureMinNode.Y for FutureMinNode in FutureMinList]
                
                except:
                    import pdb
                    pdb.set_trace()
                    
                TempLine = Line("FutureMin_"+str(FutureCount), X, Y)
                self.FutureMinUncertainty.append(TempLine)

                # create new line object for min and max
                X = [FutureMaxNode.X for FutureMaxNode in FutureMaxList]
                Y = [FutureMaxNode.Y for FutureMaxNode in FutureMaxList]
                
                TempLine = Line("FutureMax_"+str(FutureCount), X, Y)
                self.FutureMaxUncertainty.append(TempLine)
                
                # update counter
                FutureCount += 1

    def GetFutureShorelineError(self, Year=2100):

        """
        
        Extracts contiguous lines of error on Bruun Rule predictions for a given year
        Error is propoagagtion of historical shoreline positional errors only
        
        MDH, October 2020

        """

        # keep track of no of coastal segments for IDs
        FutureCount = 0

        # loop through transects and get contiguous locations where there are predictions
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

            # if first element is true this is a start point
            if FutureBool[0]:
                StartEndFlags[0] = 1
            
            # if last line finishes on a start flag then remove
            if StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
            
            # if no start flags
            if len(StartEndFlags.nonzero()[0]) == 0:
                continue
            
            # if last line finishes on last node then flag as end flag
            if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                StartEndFlags[-1] = -1

            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()
            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                print(len(StartList),len(EndList))
                import pdb
                pdb.set_trace()
                    
            for i in range(0,len(StartList)):
                
                # catch single node cliff lines and ignore
                if (EndList[i]-StartList[i]<2):
                    continue

                # create empty lists for storing future nodes for min and max predictions
                FutureMinList = []
                FutureMaxList = []
                
                # add latest MHWS from previous node to start
                # might need some logic here for first transect
                # might need some logic here for first transect
                if StartList[i] == 0:
                    FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                    ii = 1
                else:
                    FirstNode = CoastLine.Transects[StartList[i]-1].get_RecentPosition()
                    ii = 0
                    if not FirstNode:
                        FirstNode = CoastLine.Transects[StartList[i]].get_RecentPosition()
                        ii= 1
                
                FutureMinList.append(FirstNode)
                FutureMaxList.append(FirstNode)

                # loop through transects and get min and max future positions
                for Transect in CoastLine.Transects[StartList[i]:EndList[i]]:
                    Transect.PredictFutureShorelineError(Year)
                    FutureMinNode = Transect.FutureShorelinesMinNode
                    FutureMaxNode = Transect.FutureShorelinesMaxNode
                    FutureMinList.append(FutureMinNode)
                    FutureMaxList.append(FutureMaxNode)
                    
                # add latest MHWS from next node to end
                # might need some logic here to finish
                if EndList[i] == CoastLine.NoTransects-1:
                    LastNode = CoastLine.Transects[EndList[i]-1].get_RecentPosition()
                else:
                    LastNode = CoastLine.Transects[EndList[i]].get_RecentPosition()
                    if not LastNode:
                        LastNode = CoastLine.Transects[EndList[i]-1].get_RecentPosition()
                
                FutureMinList.append(LastNode)
                FutureMaxList.append(LastNode)
                
                # create new line object for min and max
                X = [FutureMinNode.X for FutureMinNode in FutureMinList]
                Y = [FutureMinNode.Y for FutureMinNode in FutureMinList]
                
                TempLine = Line("FutureMin_"+str(FutureCount), X, Y)
                self.FutureMinError.append(TempLine)

                # create new line object for min and max
                X = [FutureMaxNode.X for FutureMaxNode in FutureMaxList]
                Y = [FutureMaxNode.Y for FutureMaxNode in FutureMaxList]
                
                TempLine = Line("FutureMax_"+str(FutureCount), X, Y)
                self.FutureMaxError.append(TempLine)
                
                # update counter
                FutureCount += 1

    def GetFutureVegEdgeLines(self):

        """

        Extracts contiguous lines of future predicted vegetation edge

        MDH, Feb 2020

        """

        # Loop through prediction years
        for Year in self.FutureShoreLinesYears[1:]:

            # keep track of no of coastal segments for IDs
            FutureCount = 0

            # loop through transects and get contiguous cliff lines
            for CoastLine in self.CoastLines:
                
                # find transects with future predictions
                VegEdgeBool = [Transect.VegEdge for Transect in CoastLine.Transects]
                VegEdgeBool.insert(0, False)
                VegEdgeBool = np.array(VegEdgeBool).astype(int)
                
                # check for lines with no predictions
                if not any(VegEdgeBool):
                    continue
                
                # get a list of the start and end points of contiguous cliff lines
                StartEndFlags = np.diff(VegEdgeBool)
                
                # if first element is true this is a start point
                if VegEdgeBool[0]:
                    StartEndFlags[0] = 1
                
                # if last line finishes on a start flag then remove
                if StartEndFlags[-1] == 1:
                    StartEndFlags[-1] = 0
                
                # if no start flags
                if len(StartEndFlags.nonzero()[0]) == 0:
                    continue
                
                # if last line finishes on last node then flag as end flag
                if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                    StartEndFlags[-1] = -1

                StartList = np.argwhere(StartEndFlags == 1).flatten()
                EndList = np.argwhere(StartEndFlags == -1).flatten()
                if not len(StartList) == len(EndList):
                    print("Start and End lists not the same length")
                    print(len(StartList),len(EndList))
                    import pdb
                    pdb.set_trace()
                    
                for i in range(0,len(StartList)):
                    
                    # catch single node cliff lines and ignore
                    if (EndList[i]-StartList[i]<2):
                        continue

                    # create empty lists for storing clifftop and clifftoe nodes
                    FutureList = []
                    
                    # loop through transects and get future positions
                    
                    for Transect in CoastLine.Transects[StartList[i]:EndList[i]]:
                        FutureNode = Transect.get_FutureVegEdge(Year)
                        FutureList.append(FutureNode)
                        
                    # create new line object for top
                    X = [FutureNode.X for FutureNode in FutureList]
                    Y = [FutureNode.Y for FutureNode in FutureList]
                    
                    TempLine = Line("FutureVegEdge_"+str(FutureCount), X, Y, Year=Year)
                    self.FutureVegEdgeLines.append(TempLine)
                    
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
            
            # if first element is true this is a start point
            if BarrierBool[0]:
                StartEndFlags[0] = 1
            
            # if last line finishes on a start flag then remove
            if StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
            
            # if no start flags
            if len(StartEndFlags.nonzero()[0]) == 0:
                continue
            
            # if last line finishes on last node then flag as end flag
            if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                StartEndFlags[-1] = -1
                
            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()
            
            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                print(len(StartList),len(EndList))
                import pdb
                pdb.set_trace()
                
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

            # if first element is true this is a start point
            if CliffBool[0]:
                StartEndFlags[0] = 1
            
            # if last line finishes on a start flag then remove
            if StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
            
            # if no start flags
            if len(StartEndFlags.nonzero()[0]) == 0:
                continue
            
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
            
            # if first element is true this is a start point
            if BarrierBool[0]:
                StartEndFlags[0] = 1
            
            # if last line finishes on a start flag then remove
            if StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
            
            # if no start flags
            if len(StartEndFlags.nonzero()[0]) == 0:
                continue
            
            # if last line finishes on last node then flag as end flag
            if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                StartEndFlags[-1] = -1
                
            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()

            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                import pdb
                pdb.set_trace()
                
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
                
                # if first element is true this is a start point
                if ExtremeBool[0]:
                    StartEndFlags[0] = 1
                
                # if last line finishes on a start flag then remove
                if StartEndFlags[-1] == 1:
                    StartEndFlags[-1] = 0
                
                # if no start flags
                if len(StartEndFlags.nonzero()[0]) == 0:
                    continue
                
                # if last line finishes on last node then flag as end flag
                if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                    StartEndFlags[-1] = -1
                    
                StartList = np.argwhere(StartEndFlags == 1).flatten()
                EndList = np.argwhere(StartEndFlags == -1).flatten()

                if not len(StartList) == len(EndList):
                    print("Start and End lists not the same length")
                    import pdb
                    pdb.set_trace()


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
            
            # if first element is true this is a start point
            if ExtremeBool[0]:
                StartEndFlags[0] = 1
            
            # if last line finishes on a start flag then remove
            if StartEndFlags[-1] == 1:
                StartEndFlags[-1] = 0
            
            # if no start flags
            if len(StartEndFlags.nonzero()[0]) == 0:
                continue
            
            # if last line finishes on last node then flag as end flag
            if StartEndFlags[StartEndFlags.nonzero()[0][-1]] == 1:
                StartEndFlags[-1] = -1
            
            # start flag is gradient = 1, end flag where gradient = -1
            StartList = np.argwhere(StartEndFlags == 1).flatten()
            EndList = np.argwhere(StartEndFlags == -1).flatten()

            if not len(StartList) == len(EndList):
                print("Start and End lists not the same length")
                import pdb
                pdb.set_trace()


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

    def SetMHWS(self, MHWS):

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

    def get_MeanHistoricErosion(self):

        """ 
        
        Function to calculate the mean historic erosion on transects
        
        MDH, March 2021
        
        """

        HistoricRates = []

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                if not Transect.Future:
                    continue

                HistoricRate = Transect.ChangeRate
                
                if not HistoricRate:
                    continue
                elif not HistoricRate < 0:
                    continue
                else:
                    HistoricRates.append(HistoricRate)
        
        NErodingTransects = len(HistoricRates)
        MeanErosionRate = np.nan_to_num(np.mean(HistoricRates))

        return NErodingTransects, MeanErosionRate

    def get_MeanDC1Erosion(self):

        """ 
        
        Function to calculate the mean historic erosion on transects from DC1 data
        
        MDH, March 2021
        
        """

        HistoricRates = []

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                if not Transect.Future:
                    continue
                    
                if not Transect.DC1:
                    continue
                
                HistoricRate = Transect.DC1[2]/(Transect.DC1[1]-Transect.DC1[0])
                
                if not HistoricRate:
                    continue
                elif not HistoricRate < 0:
                    continue
                else:
                    HistoricRates.append(HistoricRate)
        
        NErodingTransects = len(HistoricRates)
        MeanErosionRate = np.nan_to_num(np.mean(HistoricRates))
        
        return NErodingTransects, MeanErosionRate

    def get_MeanTotalErosion(self, Decade=2100):

        """ 
        
        Function to calculate the mean total erosion on transects for future predictions
        
        MDH, March 2021
        
        """

        ErosionDistances = []

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                if not Transect.Future:
                    continue

                ErosionDistance = Transect.get_TotalErosion(2020,Decade)
                
                if not ErosionDistance:
                    continue
                elif not ErosionDistance < 0:
                    continue
                else:
                    ErosionDistances.append(ErosionDistance)
        
        NErodingTransects = len(ErosionDistances)
        MeanTotalErosion = np.nan_to_num(np.mean(ErosionDistances))

        return NErodingTransects, MeanTotalErosion

    def get_NumberOfTransects(self, Future=True):

        """

        Returns the total number of transects on all lines in the object

        """

        NoTransects = 0

        for Line in self.CoastLines:
            
            FutureTransects = [Transect.Future for Transect in Line.Transects]
            NoTransects += FutureTransects.count(True)
            
        return NoTransects

    def get_RecentShorelinesYearsList(self):

        """

        Function to generate a list of the most recent shorelines

        MDH, March 2021

        """
        List = []
        for Line in self.CoastLines:
            for Transect in Line.Transects:
                List.append(Transect.get_RecentYear())
        
        return List

    def get_ErosionDistancesList(self, Decade=2100):

        """
        Function to generate a list of the most recent shoreline distances

        MDH, March 2021

        """

        ErosionDistances = []

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                if not Transect.Future:
                    continue

                ErosionDistance = Transect.get_TotalErosion(2020,Decade)
                
                if not ErosionDistance:
                    continue
                elif not ErosionDistance < 0:
                    continue
                else:
                    ErosionDistances.append(ErosionDistance)
        
        return ErosionDistances
