"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import numpy as np
import shapefile
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
        print(WL.fields)
        
        for Record, Line in zip( self.Records, self.CoastLines):
            
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

        MDH, June 2019
        """

        print("Coast: Merging coastlines")

        NewShapes = []
        NewRecords = []
        NewCoastLines = [] 
        ID = 0
        for i, CoastLine in enumerate(self.CoastLines):
                            
            # get X and Y coordinates of both Lines
            # segment 1 only needs defining first time round as will be dynamic
            if i == 0:
                X1, Y1 = CoastLine.get_XY()
        
            # only define second segment and test if not at the end of the file
            else:
                X2, Y2 = CoastLine.get_XY()

                # check for a match
                if ((X1[-1] == X2[0]) and (Y1[-1] == Y2[0])):
                    X1 = np.concatenate((X1,X2[1:]))
                    Y1 = np.concatenate((Y1,Y2[1:]))

                    # write new line, and update shape and records lists
                    NewCoastLines.append(Line(str(ID), X1, Y1))
                    NewShapes.append(np.column_stack([X1,Y1]).tolist())
                    NewRecords.append([str(ID)])
                    
                    # update X1 and Y1 for next iteration
                    X1 = X2
                    Y1 = Y2

                    # iterate ID
                    ID += 1

        # update object properties with merged geometries
        self.CoastLines = NewCoastLines
        self.Shapes = NewShapes
        self.Records = NewRecords

        # update number of shapes
        if len(self.CoastLines) != len(self.Shapes):
            sys.exit("Coast.MergeCoastlines(ERROR): Number of shapes and number of lines doesn't match!")
        self.NoCoastLines = len(self.CoastLines)

        print(self.Records[0])

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