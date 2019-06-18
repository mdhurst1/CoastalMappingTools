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
    


    def MergeCoastlines(self):
        """
        Identifies individual coast Lines that are touching at one end 
        and combines them into a single Line

        MDH, June 2019
        """

        print("Coast: Merging coastlines")

        for i in range(0, self.NoCoastLines):
                            
            # get X and Y coordinates of both Lines
            # segment 1 only needs defining first time round as will be dynamic
            if i == 0:
                X1, Y1 = self.CoastLines[i].get_XY()
        
            # only define second segment and test if not at the end of the file
            if i < self.NoCoastLines-1:
                X2, Y2 = self.CoastLines[i+1].get_XY()

            # check for a match
            if ((X1[-1] == X2[0]) and (Y1[-1] == Y2[0])):
                X1 = np.concatenate((X1,X2[1:]))
                Y1 = np.concatenate((Y1,Y2[1:]))

                # write new line and delete second segment
                self.CoastLines[i] = Line(X1, Y1, str(i))
                self.CoastLines.pop(i+1)

                # update shapefile lists and delete second segment (this will need testing)
                self.Shapes[i] = np.column_stack([X1,Y1]).tolist()
                self.Shapes.pop(i+1)
                self.Records.pop(i+1)


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