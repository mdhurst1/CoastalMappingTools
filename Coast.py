"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import numpy as np
import shapefile
import itertools
from Line import *

class Coast:
    """
    Description of object goes here

    """

    def __init__(self, CoastShp=""):
        """
        MDH, June 2019
        """
        self.CoastShp = CoastShp
        self.Shapes = []
        self.Fields = []
        self.Records = []
        self.NoCoastLines = 0
        self.CoastLines = []
        self.Projection = ""

        if CoastShp:
            print("Coast: Reading coast from " + CoastShp)
            self.ReadCoastShp(CoastShp)

        else:
            print("Coast: Generating empty coast object")

    def __str__(self):
        String = "Coast Object:\n\tFile: %s\n\tNumber of Coastlines:%d\n\t" % (str(self.CoastShp), self.NoCoastLines)
        return String

    # read coast from a shapefile
    def ReadCoastShp(self,CoastShp):

        # Open coast polyline file for reading
        SF = shapefile.Reader(CoastShp)
        self.Shapes = SF.shapes()
        self.Fields = SF.fields
        self.Records = SF.records()

        # Get number of coast segments to work on
        self.NoCoastLines = len(self.Shapes)
        print("\tCoast.ReadCoastShp: Read Coastline, no of coast segments is", self.NoCoastLines)
    
        # Generate coast nodes for each segment
        for i in range(0,self.NoCoastLines):
            
            # get X and Y coordinates of segment
            X, Y = np.array(self.Shapes[i].points).T
            
            # Set up a line object for each
            ThisLine = Line(str(i), X, Y)

            # append to list of coast lines
            self.CoastLines.append(ThisLine)
            
        # get projection strings
        f = open(CoastShp.rstrip("shp")+"prj")
        self.Projection = f.read()
        f.close()
        
        # reduce to single smoothed coastline
        print((self.Shapes[0]))

 
    def WriteCoastShp(self,CoastShp):
        """
        Writes the contents of a Coast object to polyline shape file

        MDH, June 2019

        """

        # open new shapefile        
        WL = shapefile.Writer(CoastShp,shapeType=shapefile.POLYLINE)
        WL.fields = self.Fields[1:]
                
        for Record, Line in zip(self.Records, self.CoastLines):
            
            # get line node positions
            X, Y = Line.get_XY()
            WriteLine = [np.column_stack([X,Y]).tolist()]
            
            # write line and record
            WL.line(WriteLine)
            WL.record(*Record) ####### ISSUE WITH RECORDS NEEDS FIXING ########
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(CoastShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()

    def MergeCoastlines(self):
        """
        Identifies individual coast Lines that are touching at one end 
        and combines them into a single Line

        THIS NEEDS MORE WORK AS CURRENTLY SEGMENTS NOT IN ORDER DOWN COAST

        MDH, June 2019
        """

        print("Coast: Merging coastlines")

        # Empty lists to populate with new shapes and records
        NewCoastLines = []
        NewShapes = []
        NewRecords = []

        # create list of joins
        JoinList = np.zeros(NoCoastLines,dtype=int)-9999
        JoinedList = np.zeros(NoCoastLines,dtype=int)-9999
        
        # get start and end nodes from line sections
        StartNodes = [CoastLine.Nodes[0] for CoastLine in CoastLines]
        EndNodes = [CoastLine.Nodes[-1] for CoastLine in CoastLines]
        
        # compare start nodes and end nodes to populate join list
        # this could probably be done better!
        for i, EndNode in enumerate(EndNodes):
            for j, StartNode in enumerate(StartNodes):
                if StartNode == EndNode:
                    JoinList[i] = j
                    JoinedList[j] = i
        
        # get list of line sections to start at
        StartList = np.where(JoinedList < 0)

        for i, StartNode in enumerate(StartList):
            
            # get vector of line section
            X1, Y1 = self.CoastLines[StartNode].get_XY()
            
            # get first line section to join
            JoinLine = JoinList[StartNode]

            while JoinNode > -1:
                
                # get next line
                X2, Y2 = self.CoastLines[JoinLine].get_XY()

                # join the lines
                X1 = np.concatenate((X1,X2[1:]))
                Y1 = np.concatenate((Y1,Y2[1:]))

                # get next n
                JoinLine = JoinList[JoinLine]

            # write new line, and update shape and records lists
            NewCoastLines.append(Line(str(ID), X1, Y1))
            NewShapes.append(np.column_stack([X1,Y1]).tolist())
            NewRecords.append(Record[i])
                
        # update object properties with merged geometries
        self.CoastLines = NewCoastLines
        self.Shapes = NewShapes
        self.Records = NewRecords

        # update number of shapes
        if len(self.CoastLines) != len(self.Shapes):
            sys.exit("Coast.MergeCoastlines(ERROR): Number of shapes and number of lines doesn't match!")
        self.NoCoastLines = len(self.CoastLines)

    def SmoothCoastlines(self, WindowSize):
        """
        Wrapper to the function in the Line object

        Savitzky and Golay (1964) smoothing filter
    
        Savitzky, A. and Golay, M. J.: Smoothing and differentiation of data
        by simplified least squares procedures, Anal. Chem., 36, 1627–
        1639, 1964.

        MDH, June 2019
        """

        print("Coast: Smoothing coastlines")

        for i, Line in enumerate(self.CoastLines):

            # smooth the line
            Line.SmoothLine(WindowSize)

            # update the shape object list
            X, Y = Line.get_XY()
            self.Shapes[i] = np.column_stack([X,Y]).tolist()


    # function to do something    
    def GenerateNormals(self):
        """
        Wrapper to the function in the Line object

        Generates transects perpendicular to the coastline
        """
        print("Coast: Generating coastline normals")

        for Line in self.CoastLines:

            # smooth the line
            Line.GenerateTransects()