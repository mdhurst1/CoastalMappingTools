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

        print("Coast: Initialising Coast object")

        self.CoastShp = CoastShp
        self.Shapes = []
        self.Fields = []
        self.Records = []
        self.NoCoastLines = 0
        self.CoastLines = []
        self.Projection = ""
        self.TransectsSpacing = 10.
        self.TransectsLength2Sea = 200.
        self.TransectsLength2Land = 1000.

        if CoastShp:
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
        print("Coast.ReadCoastShp: Read Coastline, no of coast segments is", self.NoCoastLines)
    
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
 
    def WriteCoastShp(self,CoastShp):
        """
        Writes the contents of a Coast object to polyline shape file

        MDH, June 2019

        """

        # open new shapefile        
        WL = shapefile.Writer(CoastShp,shapeType=shapefile.POLYLINE)
       
        # Create Fields
        self.Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0]]
        WL.fields = self.Fields[1:] 

        for Line in self.CoastLines:
            
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

    def WriteTransectsShp(self, TransectsShp):

        """
        Writes the transects of a Coast object to polyline shape file

        MDH, June 2019

        """

        # open new shapefile        
        WL = shapefile.Writer(TransectsShp,shapeType=shapefile.POLYLINE)
        
        # Create Fields
        Fields = [('DeletionFlag','C',1,0),['Line_ID', 'C', 3, 0],['Transect_ID', 'C', 3, 0]] #['Segment_ID','C', 3, 0], might add
        WL.fields = Fields[1:]

        for Line in self.CoastLines:
            for Transect in Line.Transects:

                # get transect node positions
                X, Y = Transect.get_XY()
                WriteTransect = [np.column_stack([X,Y]).tolist()]

                # Create the record
                Record = [str(Line.ID), str(Transect.ID)]

                # write transect and record
                WL.line(WriteTransect)
                WL.record(*Record) 
        
        # close the shapefiles and clean up
        WL.close()
            
        # create the projection file    
        f = open(TransectsShp.rstrip("shp")+"prj","w")
        f.write(self.Projection)
        f.close()


    def WritePointsShp(self, PointsShp):
        """
        Function to write transect points to a point shape file

        MDH, June 2019
        
        """

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

        while FlagReverse:

            # Update Flag
            FlagReverse = 0

            # Empty lists to populate with new shapes and records
            NewCoastLines = []
            NewShapes = []
            NewRecords = []

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
            for StartLine in StartList:
                
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
                NewShapes.append(np.column_stack([X1,Y1]).tolist())
                NewRecords.append(self.Records[StartLine])
                    
            # update object properties with merged geometries
            self.CoastLines = NewCoastLines
            self.Shapes = NewShapes
            self.Records = NewRecords

            # update number of shapes
            if len(self.CoastLines) != len(self.Shapes):
                sys.exit("Coast.MergeCoastlines(ERROR): Number of shapes and number of lines doesn't match!")
            self.NoCoastLines = len(self.CoastLines)

    def SmoothCoastLines(self, WindowSize=1001, PolyOrder=4):
        
        """
        Smooths the CoastLines contained in Coast object
        Wrapper to the function in the Line object
        Calls scipy.signal.savgol_filter

        Savitzky and Golay (1964) smoothing filter
    
        Savitzky, A. and Golay, M. J.: Smoothing and differentiation of data
        by simplified least squares procedures, Anal. Chem., 36, 1627–
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

        for i, Line in enumerate(self.CoastLines):
            
            # smooth the line
            Line.SmoothLine(WindowSize, PolyOrder)

            # update the shape object list
            X, Y = Line.get_XY()
            self.Shapes[i] = np.column_stack([X,Y]).tolist()

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
                ErrorString = ("Coast.ReconfigureCoastLine (ERROR): "
                    "This direction top open water [w] has not been implemented yet")
                sys.exit(ErrorString)

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
            self.Records = list(np.array(self.Records)[DescendingIndices])
            for i, Line in enumerate(self.CoastLines):
                Line.ID = str(i)

        if len(self.CoastLines[0].Transects) != 0:
            self.GenerateNormals(self.TransectsSpacing, self.TransectsLength2Sea, self.TransectsLength2Land)

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