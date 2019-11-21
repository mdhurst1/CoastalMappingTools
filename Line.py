"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import sys
import numpy as np
from scipy.signal import savgol_filter
import Transect
from Node import *
from Transect import *

import geopandas as gp
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import nearest_points

class Line:
    
    """
    """

    def __init__(self, ID, X, Y, Contour=None, Year=None):
        """
        """
        self.ID = ID
        self.Year = Year
        self.NoNodes = 0
        self.Nodes = []
        self.RawNodes = []
        self.Projection = ""
        self.Orientation = []
        self.Curvature = []
        self.SegmentLength = []
        self.TotalLength = 0
        self.Transects = []
        self.NoTransects = 0
        self.Points = []
        self.NoPoints = 0
        self.Contour = Contour
        self.GenerateNodes(X, Y)

    def __str__(self):
        """
        """
        String = "Line Object:\nID: %s\nNoNodes: %d\nLength: %.2f" % (str(self.ID), self.NoNodes, self.TotalLength)
        return String

    def GenerateNodes(self, X, Y):
        """
        Function to convert X and Y data into Nodes
        """
        # check X and Y are same length
        if len(X) != len(Y):
            sys.exit("Line.GenerateNodes(ERROR): X and Y vectors are not same length.\n\t \
length of X: %d\n\tlength of Y:%d\n\n" % (len(X),len(Y)))

        # reset node list
        self.Nodes = []

        # set the number of nodes on the line
        self.NoNodes = len(X)

        # loop through and create node list
        for x, y in zip(X, Y):
            self.Nodes.append(Node(x,y))
        
        self.CalculateGeometry()
        
        if not self.RawNodes:
            self.RawNodes = self.Nodes

    def CalculateGeometry(self):
        
        """
        Calculate the orientation, curvature and length along the line
        Orientation is the direction towards the next node in the vector
        Curvature is the difference in orientation between two segments
        SegmentLength is the distance to the next node in the vector

        MDH, June 2019

        """
        # reset arrays
        self.Orientation = np.ones(self.NoNodes)*-9999
        self.SegmentLength = np.ones(self.NoNodes)*-9999
        self.TotalLength = 0

        # loop through the nodes
        for i in range(0,self.NoNodes-1):
            
            # Get the two nodes
            ThisNode = self.Nodes[i]
            NextNode = self.Nodes[i+1]

            #calculate the spatial change
            dx = NextNode.X - ThisNode.X
            dy = NextNode.Y - ThisNode.Y

            #Calculate the orientation of the line from ThisNode to NextNode
            if dx > 0 and dy > 0:
                self.Orientation[i] = np.degrees( np.arctan( dx / dy ) )
            elif dx > 0 and dy < 0:
                self.Orientation[i] = 180.0 + np.degrees( np.arctan( dx / dy ) )
            elif dx < 0 and dy < 0:
                self.Orientation[i] = 180.0 + np.degrees( np.arctan( dx / dy ) )
            elif dx < 0 and dy > 0:
                self.Orientation[i] = 360 + np.degrees( np.arctan( dx / dy ) )
            
            

            #Calculate the length of the segment
            self.SegmentLength[i] = np.sqrt(dx**2. + dy**2.)

            #Update the cumulative length of the line
            self.TotalLength += self.SegmentLength[i]

        # Properties of last node
        self.Orientation[-1] = self.Orientation[-2]
        self.SegmentLength[-1] = 0
        
    def SmoothLine(self, WindowSize=1001, PolyOrder=4):
        
        """
        Savitzky and Golay (1964) smoothing filter
            
        Savitzky, A. and Golay, M. J.: Smoothing and differentiation of data
            by simplified least squares procedures, Anal. Chem., 36, 1627-
            1639, 1964.
        """

        # Get X and Y vectors from Nodes
        X, Y = self.get_XY()
        
        # smooth X and Y individually with Savitzky Golay filter
        # window size and polyorder must be integers you idiot!
        XSmooth = savgol_filter(X,WindowSize,PolyOrder, mode="nearest")
        YSmooth = savgol_filter(Y,WindowSize,PolyOrder, mode="nearest")

        self.RawNodes = self.Nodes
        
        # Write new X and Y vectors to Nodes
        self.GenerateNodes(XSmooth,YSmooth)
        self.CalculateGeometry()
    
    def GenerateBuffer(self, Dist1, Dist2):
        
        """
        Description goes here

        MDH, June 2019

        """

        # empty lists for new nodes
        BufferNodesLeft = []
        BufferNodesRight = []

        # Orientation increments by 1 degree when rounding required
        OrientationInc = 1.

        # Node Counter to give each node a unique ID
        NodeCounter = 0

        # loop through nodes 
        for i, ThisNode in enumerate(self.NoNodes):
            
            # this section of code could definately be more efficient
            # or better written but will do for now

            # check if line is convex/concave left
            if not self.Orientation[i] < self.Orientation[i-1]:
                        
                # find point perpendicular to orientation on left side
                TempOrientation = self.Orientation[i]
                XL = ThisNode.X + Dist1 * np.sin( np.radians (TempOrientation-90.) )
                YL = ThisNode.Y + Dist1 * np.cos( np.radians (TempOrientation-90.) )
                BufferNodesLeft.append(Node(NodeCounter, XL, YL))
                NodeCounter += 1

                # increment orientation to complete radius
                while TempOrientation < self.Orientation[i+1]:
                    TempOrientation += OrientationInc
                    XL = ThisNode.X + Dist1 * np.sin( np.radians (TempOrientation-90.) )
                    YL = ThisNode.Y + Dist1 * np.cos( np.radians (TempOrientation-90.) )
                    BufferNodesLeft.append(Node(NodeCounter, XL, YL))
                    NodeCounter += 1

                # find point on right perpendicular to mean orientation
                TempOrientation = np.mean(self.Orientation[i-1:i+1])
                XR = ThisNode.X + Dist2 * np.sin( np.radians (TempOrientation+90.) )
                YR = ThisNode.X + Dist2 * np.sin( np.radians (TempOrientation+90.) )
                BufferNodesRight.append(Node(NodeCounter, XR, YR))
                NodeCounter += 1

            else:

                # find point perpendicular to orientation on right side
                TempOrientation = self.Orientation[i]
                XR = ThisNode.X + Dist2 * np.sin( np.radians (TempOrientation+90.) )
                YR = ThisNode.Y + Dist2 * np.cos( np.radians (TempOrientation+90.) )
                BufferNodesRight.append(Node(NodeCounter, XR, YR))
                NodeCounter += 1

                # increment orientation to complete radius
                while TempOrientation < self.Orientation[i+1]:
                    TempOrientation += OrientationInc
                    XR = ThisNode.X + Dist2 * np.sin( np.radians (TempOrientation+90.) )
                    YR = ThisNode.Y + Dist2 * np.cos( np.radians (TempOrientation+90.) )
                    BufferNodesRight.append(Node(NodeCounter, XR, YR))
                    NodeCounter += 1

                # find point on right perpendicular to mean orientation
                TempOrientation = np.mean(self.Orientation[i-1:i+1])
                XL = ThisNode.X + Dist1 * np.sin( np.radians (TempOrientation-90.) )
                YL = ThisNode.X + Dist1 * np.sin( np.radians (TempOrientation-90.) )
                BufferNodesLeft.append(Node(NodeCounter, XL, YL))
                NodeCounter += 1

        return Line(XL,YL,"LeftBuffer"), Line(XL,YL,"RightBuffer")


    def GenerateTransects(self, Spacing, TransectLength2Sea, TransectLength2Land, CheckTopology=True):
        """
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
            Check for overlapping transects and correct. Default is True
        
        """

        # print("Line: Generating Transects perpendicular to the coast")
        
        # if rewriting Transects, empty the Transects list
        if len(self.Transects) != 0:
            self.Transects = []
            self.Points = []

        # Give each transect unique ID
        TransectCount = 0
        
        # Parameters for tracing along length
        CumulativeLength = 0.0
        NextPosition = Spacing

        # Track spacing and generate profile at desired distances
        for i in range(0, self.NoNodes):

            #Update the cumulative length of the line
            CumulativeLength += self.SegmentLength[i]

            # get orientation
            TempOrientation = self.Orientation[i]
            
            # Test to see if we're going to create a cross section
            while CumulativeLength > NextPosition:

                #calculate point for section
                DistanceToStepBack = CumulativeLength - NextPosition
                dX = DistanceToStepBack * np.sin( np.radians( TempOrientation ) )
                dY = DistanceToStepBack * np.cos( np.radians( TempOrientation ) )
                
                # find the point for the transect along the line
                PointX = self.Nodes[i+1].X - dX
                PointY = self.Nodes[i+1].Y - dY

                #Create cross section line
                #Get line orientation
                if TempOrientation < 0:
                    TransectOrientation = TempOrientation + 90.
                else:
                    TransectOrientation = TempOrientation - 90.

                #Calculate start and end nodes and generate Transect
                X1 = PointX + TransectLength2Sea * np.sin( np.radians( TransectOrientation ) )
                Y1 = PointY + TransectLength2Sea * np.cos( np.radians( TransectOrientation ) )
                X2 = PointX - TransectLength2Land * np.sin( np.radians( TransectOrientation ) )
                Y2 = PointY - TransectLength2Land * np.cos( np.radians( TransectOrientation ) )
                self.Transects.append( Transect(str(self.ID), str(TransectCount), Node(PointX, PointY), Node(X1, Y1), Node(X2, Y2) ) )

                # update to find next transect
                TransectCount += 1
                NextPosition += Spacing
        
        # record number of transects
        self.NoTransects = TransectCount   

        # check for overlaps?
        if CheckTopology:
            self.CheckTransectTopology()     

    def GenerateTransectsFromContour(self, ContourShp, Spacing):

        """

        Generates regularly spaced transects along the coastline by 
        finding the nearest point in another line dataset and drawing
        connecting lines
    
        MDH, August 2019

        Parameters
        ----------
        Spacing : float
            The distance between consecutive points along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]

        """

        # if rewriting Transects, empty the Transects list
        if len(self.Points) != 0:
            self.Transects = []
            self.Points = []
        
        # generate points along the line
        self.GeneratePoints(Spacing)

        # load the contour shapefile
        GDF = gp.read_file(ContourShp)
        Lines = GDF['geometry']
        
        # make a multlinestring if there are multiple lines
        LineList = []
        for LineObj in Lines:
            if (LineObj.geom_type == "MultiLineString"):
                for ThisLine in LineObj:
                    LineList.append(ThisLine)
            else:
                LineList.append(LineObj)

        Lines = MultiLineString(LineList)
        
        for ThisPoint in self.Points:
                
                # find nearest point in contour lines
                BasePoint = Point(ThisPoint.X, ThisPoint.Y)
                NearestPoint = nearest_points(Lines, BasePoint)[0]
                
                # build transect using these two points
                self.Transects.append(Transect(str(self.ID), str(ThisPoint.ID), Node(NearestPoint.x, NearestPoint.y), Node(BasePoint.x, BasePoint.y), Node(NearestPoint.x, NearestPoint.y)))

    def GenerateTransectsNormal2Contours(self, ContourShp1, ContourShp2, Spacing):

        """

        Generates regularly spaced transects along the coastline by 
        finding the nearest point in another line dataset and drawing
        connecting lines
    
        MDH, August 2019

        Parameters
        ----------
        Spacing : float
            The distance between consecutive points along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]

        """

        # load the contour shapefile
        GDF = gp.read_file(ContourShp1)
        Lines = GDF['geometry']
        
        # make a multlinestring if there are multiple lines
        LineList = []
        for LineObj in Lines:
            if (LineObj.geom_type == "MultiLineString"):
                for ThisLine in LineObj:
                    LineList.append(ThisLine)
            else:
                LineList.append(LineObj)

        Lines1 = MultiLineString(LineList)
        
        # load the second contour shapefile
        GDF = gp.read_file(ContourShp2)
        Lines = GDF['geometry']
        
        # make a multlinestring if there are multiple lines
        LineList = []
        for LineObj in Lines:
            if (LineObj.geom_type == "MultiLineString"):
                for ThisLine in LineObj:
                    LineList.append(ThisLine)
            else:
                LineList.append(LineObj)

        Lines2 = MultiLineString(LineList)

        # get points to define initial transect line and make it nice and long
        self.GenerateTransects(Spacing,5000.,5000.)

        # intersect Transect with shapefile to find new end node of transect
        for Transect in self.Transects:
            
            # find intersection between transect line and shapefile lines
            Intersection = Transect.LineString.intersection(Lines1)
            
            # catch no intersections
            if Intersection.geom_type == "GeometryCollection":
                continue

            # check there arent multiple intersections, if there are just get the nearest
            if Intersection.geom_type is "MultiPoint":
                StartPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersection]
                Index = Distances.index(min(Distances))
                Intersection = Intersection[Index]
                
            # set this as the new end node
            NewEndNode = Node(Intersection.x,Intersection.y)
            
            # now do the same with the raw coastline data (i.e. the original contour)
            Intersection = Transect.LineString.intersection(Lines2)
            
            # catch no intersections
            if Intersection.geom_type == "GeometryCollection":
                continue

            # check there arent multiple intersections, if there are just get the nearest
            if Intersection.geom_type is "MultiPoint":
                StartPoint = Point(Transect.CoastNode.X, Transect.CoastNode.Y)
                Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersection]
                Index = Distances.index(min(Distances))
                Intersection = Intersection[Index]

            NewStartNode = Node(Intersection.x,Intersection.y)

            # reinitialise transect with new startnode and new endnode
            Transect.__init__(Transect.LineID, Transect.ID, Transect.CoastNode, NewStartNode, NewEndNode)

    def CheckTransectTopology(self):

        """
        Check for overlapping transects and correct by truncating to point of intersection

        MDH, November 2019

        """

        # create list of transects organised by descending curvature
        # based on gradient in orientation
        self.Curvature = np.ones(self.NoTransects)*-9999.
        TransectOrientations = [Transect.Orientation for Transect in self.Transects]

        for i in range(1,self.NoTransects-1):
            if ((TransectOrientations[i-1] > 270.) and (TransectOrientations[i] < 90.)):
                self.Curvature[i] = TransectOrientations[i]-(TransectOrientations[i-1]-360.)
            elif ((TransectOrientations[i] > 270.) and (TransectOrientations[i-1] < 90.)):
                self.Curvature[i] = (TransectOrientations[i]-360.)-TransectOrientations[i-1]
            else:
                self.Curvature[i] = TransectOrientations[i]-TransectOrientations[i-1]

        # fix start and end node values
        self.Curvature[0] = self.Curvature[1]
        self.Curvature[-1] = self.Curvature[-2]

        # sort in descending order
        Indices = np.argsort(self.Curvature)

        IntersectionsFlag = True

        # while IntersectionsFlag == True:

        InteresectionsFlag = False

        # intersect Transect with shapefile to find new end node of transect
        for i in Indices:

            # get the transect
            Transect = self.Transects[i]
            
            # remove current transect from line list for comparison
            # make a shapely object containing all transect lines
            LinesList = [Transect.LineString for Transect in self.Transects]
            LinesList.remove(Transect.LineString)
            Lines = MultiLineString(LinesList)

            # find intersection between transect line and shapefile lines
            try:
                Intersection = Transect.LineString.intersection(Lines)
            except:
                continue
            
            # catch no intersections
            if Intersection.geom_type == "GeometryCollection":
                continue
            
            IntersectionsFlag = True

            # check there arent multiple intersections, if there are just get the nearest
            if Intersection.geom_type is "MultiPoint":
                StartPoint = Point(Transect.StartNode.X, Transect.StartNode.Y)
                Distances = [IntersectPoint.distance(StartPoint) for IntersectPoint in Intersection]
                Index = Distances.index(min(Distances))
                Intersection = Intersection[Index]
            
            # reinitialise transect with new endnode
            NewEndNode = Node(Intersection.x,Intersection.y)
            Transect.__init__(Transect.LineID, Transect.ID, Transect.CoastNode, Transect.StartNode, NewEndNode)

            # fig = plt.figure(1)
            # ax = fig.add_subplot(111)
            # plt.axis("equal")
            # plt.plot([Transect.StartNode.X,Transect.EndNode.X],[Transect.StartNode.Y,Transect.EndNode.Y],lw=0.5)
            # plt.plot(Intersection.x,Intersection.y,'ro')

            # find intersecting transect
            for OtherTransect in self.Transects:
                
                if Intersection.intersects(OtherTransect.LineString):

                    if (Transect.StartNode.X == OtherTransect.StartNode.X):
                        continue

                    else:
                        NewEndNode = Node(Intersection.x,Intersection.y)

                        # reinitialise transect with new startnode and new endnode
                        OtherTransect.__init__(OtherTransect.LineID, OtherTransect.ID, OtherTransect.CoastNode, OtherTransect.StartNode, NewEndNode)
                        
                        # plt.plot([OtherTransect.StartNode.X,OtherTransect.EndNode.X],[OtherTransect.StartNode.Y,OtherTransect.EndNode.Y],'r')
                        # plt.show()

    def GeneratePoints(self, Spacing):
        """
        Generates regularly spaced points along the coastline

        MDH, August 2019

        Parameters
        ----------
        Spacing : float
            The distance between consecutive points along the CoastLines
            in map units, spatial units depend on units of the CoastLine read in,
            Should be [m]
              
        """

        # print("Line: Generating Transects perpendicular to the coast")
        
        # if rewriting Points, empty the Points and transects list
        if len(self.Points) != 0:
            self.Points = []
            self.Transects = []

        # Give each node unique ID
        PointCount = 0
        
        # Parameters for tracing along length
        CumulativeLength = 0.0
        NextPosition = Spacing

        # Track spacing and generate profile at desired distances
        for i in range(0, self.NoNodes):

            #Update the cumulative length of the line
            CumulativeLength += self.SegmentLength[i]

            # get orientation
            TempOrientation = self.Orientation[i]
            
            # Test to see if we're going to create a node
            while CumulativeLength > NextPosition:

                #calculate point for section
                DistanceToStepBack = CumulativeLength - NextPosition
                dX = DistanceToStepBack * np.sin( np.radians( TempOrientation ) )
                dY = DistanceToStepBack * np.cos( np.radians( TempOrientation ) )
                
                # find the point for the node along the line
                PointX = self.Nodes[i+1].X - dX
                PointY = self.Nodes[i+1].Y - dY

                self.Points.append(Node(PointX, PointY, ID=PointCount))

                # update to find next transect
                PointCount += 1
                NextPosition += Spacing
        
        # record number of transects
        self.NoPoints = PointCount

    

    def ReverseLine(self):
        """
        Reverses the order of a line object
        
        MDH, June 2019
        """

        X, Y = self.get_XY()
        self.GenerateNodes(X[::-1], Y[::-1])

    def get_XY(self):
        """
        Returns X and Y coordinates as vector numpy arrays

        MDH, June 2019
        """
        X = []
        Y = []
        for Node in self.Nodes:
            X.append(Node.X)
            Y.append(Node.Y)
        
        return np.array(X), np.array(Y)
