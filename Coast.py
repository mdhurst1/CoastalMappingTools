"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import os, sys, time, pickle
import numpy as np
import numpy.ma as ma
from sklearn.cluster import KMeans

import shapefile
import itertools
import rasterio
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

        self.CoastShp = CoastShp
        self.NoCoastLines = 0
        self.CoastLines = []
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
            print("Coast: Initialised coast from " + CoastShp)

        else:
            print("Coast: Generating empty coast object")

    def __str__(self):
        String = "Coast Object:\n\tFile: %s\n\tNumber of Coastlines:%d\n\t" % (str(self.CoastShp), self.NoCoastLines)
        return String

    # a function to save to a pickle file
    def Save(self, PickleFile):
        with open(PickleFile, 'wb') as PFile:
            pickle.dump(self, PFile)

    # read coast from a shapefile
    def ReadCoastShp(self,CoastShp):

        # Open coast polyline file for reading
        SF = shapefile.Reader(CoastShp)
        Shapes = SF.shapes()
        
        # I HAVE DELETED THE RECORDING OF SHAPES AND RECORDS INTO THE OBJECT DUE TO COMPATIBILITY ISSUES
        # WITH PICKLING THAT I CAN UNDERSTAND!!!!

        # Get number of coast segments to work on
        self.NoCoastLines = len(Shapes)
        print("Coast.ReadCoastShp: Read Coastline, no of coast segments is", self.NoCoastLines)
    
        # Generate coast nodes for each segment
        for i in range(0,self.NoCoastLines):
            
            print(" \r\tCoastline %4d / %4d" % (i, self.NoCoastLines), end="")

            # get X and Y coordinates of segment
            X, Y = np.array(Shapes[i].points).T
            
            # Set up a line object for each
            ThisLine = Line(str(i), X, Y)

            # append to list of coast lines
            self.CoastLines.append(ThisLine)
            
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

    def WriteLinesShp(self, DictionaryKey, CoastShp):
        
        """
        Writes the contents of a list of line objects to polyline shape file

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
        Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0],['Transect_ID', 'C', 3, 0]] #['Segment_ID','C', 3, 0], might add 
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
        Fields = [('DeletionFlag','C',1,0), ['LineID', 'C', 3, 0], ['TransectID', 'C', 3, 0], 
        ['Cliff_H','N', 5, 2],['Cliff_S','N', 5, 2],
        ['Rocky','N', 2, 1], 
        ['Bar_FH','N', 5, 2], ['Bar_FS','N', 5, 2],
        ['Bar_BH','N', 5, 2], ['Bar_BS','N', 5, 2],
        ['Bar_ToeW','N', 6, 2], ['Bar_TopW','N', 6, 2],
        ['Bar_Volume','N', 7, 2], ['Crest_Elev','N', 5, 2], 
        ['Ext_W_low','N', 6, 2], ['Ext_V_low','N', 7, 2],
        ['Ext_W_med','N', 6, 2], ['Ext_V_med','N', 7, 2],
        ['Ext_W_high','N', 6, 2], ['Ext_V_high','N', 7, 2]]
        
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
                            Transect.ExtremeWidths[2], Transect.ExtremeVolumes[2]]

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
        Fields = [('DeletionFlag','C',1,0), ['LineID', 'C', 3, 0], ['TransectID', 'C', 3, 0], 
        ['Cliff_H','N', 5, 2],['Cliff_S','N', 5, 2],
        ['Rocky','N', 2, 1], 
        ['Bar_FH','N', 5, 2], ['Bar_FS','N', 5, 2],
        ['Bar_BH','N', 5, 2], ['Bar_BS','N', 5, 2],
        ['Bar_ToeW','N', 6, 2], ['Bar_TopW','N', 6, 2],
        ['Bar_Volume','N', 7, 2], ['Crest_Elev','N', 5, 2], 
        ['Ext_W_low','N', 6, 2], ['Ext_V_low','N', 7, 2],
        ['Ext_W_med','N', 6, 2], ['Ext_V_med','N', 7, 2],
        ['Ext_W_high','N', 6, 2], ['Ext_V_high','N', 7, 2]]

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
                            Transect.ExtremeWidths[2], Transect.ExtremeVolumes[2]]

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
        Fields = [('DeletionFlag','C',1,0), ['LineID', 'C', 3, 0], ['TransectID', 'C', 3, 0], 
        ['Cliff_H','N', 5, 2],['Cliff_S','N', 5, 2],
        ['Rocky','N', 2, 1], 
        ['Bar_FH','N', 5, 2], ['Bar_FS','N', 5, 2],
        ['Bar_BH','N', 5, 2], ['Bar_BS','N', 5, 2],
        ['Bar_ToeW','N', 6, 2], ['Bar_TopW','N', 6, 2],
        ['Bar_Volume','N', 7, 2], ['Crest_Elev','N', 5, 2], 
        ['Ext_W_low','N', 6, 2], ['Ext_V_low','N', 7, 2],
        ['Ext_W_med','N', 6, 2], ['Ext_V_med','N', 7, 2],
        ['Ext_W_high','N', 6, 2], ['Ext_V_high','N', 7, 2]]

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
                            Transect.ExtremeWidths[2], Transect.ExtremeVolumes[2]]

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

    def MergeCoastLines(self):

        """
        Identifies individual coast Lines that are touching at one end 
        and combines them into a single Line

        Reversal of line directions might cause bugs, works so far

        MDH, June 2019
        """

        print("Coast: Merging coastlines")

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

    def SmoothCoastLines(self, WindowSize=101, PolyOrder=4):
        
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
        
        """

        print("Coast: Smoothing CoastLines")

        for Line in self.CoastLines:
            
            # smooth the line
            Line.SmoothLine(WindowSize, PolyOrder)


    def ReconfigureCoastLines(self, Direction2OpenWater):
        """
        Function to arrange coastline so that lines are ordered along the coast
        and line segments progress along the coast. The "along coast" direction
        is always that which results in the water being on the left as you look
        down the coastal vector.

        This might be buggy as anything and need lots more work. Should be run
        after MergeCoast and SmoothCoast but before Transects are built, though 
        if Transects have been built they will get rebuilt

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
            self.GenerateNormals(self.TransectsSpacing, self.TransectsLength2Sea, self.TransectsLength2Land)

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
    def GenerateNormals(self, TransectSpacing, TransectLength2Sea, TransectLength2Land):
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
                    
        """
        print("Coast: Generating CoastLine transects perpendicular to the coast")

        self.TransectsSpacing = TransectSpacing
        self.TransectsLength2Sea = TransectLength2Sea
        self.TransectsLength2Land = TransectLength2Land

        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateTransects(TransectSpacing, TransectLength2Sea, TransectLength2Land)

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
        print("Coast: Generating CoastLine nodes")

        self.NodeSpacing = TransectSpacing
        
        for Line in self.CoastLines:

            # generate transects along each line
            Line.GenerateNodes(NodeSpacing)

    def ExtractTransectTopography(self, DEMFile, SwathDistance=-9999):
        """
        Profile to populate transects with topographic data
        Uses swath profile routine to collect elevations within a certain distance
        of each transect line then takes IDW values for the transect topography

        MDH, June 2019
        
        Parameters
        ----------
        DEMFile : str
            Name of DEM File, must be a *.tif

        SwathDistance : float
            Distance away from transect line to sample elevations in DEM
            Default is 2 times the resolution of the DTM

        """
        
        print("Coast.EstractTransectTopography: Sampling the DTM for each transect")
        
        # load the DTM and get its properties
        print("\tLoading DTM... ", end="")
        DTM_Dataset = rasterio.open(DEMFile)
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

        Generate line objects from extreme water positions on transects,
        
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

    def PlotTransects(self, PlotFolder):
        
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
                #if Transect.ID == "0":
                Transect.Plot(PlotFolder)
                    
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