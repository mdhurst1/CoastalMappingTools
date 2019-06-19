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

class Line:
    
    """
    """

    def __init__(self, ID, X, Y):
        """
        """
        self.ID = ID
        self.NoNodes = 0
        self.Nodes = []
        self.Projection = ""
        self.Orientation = []
        self.SegmentLength = []
        self.TotalLength = 0

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

    def CalculateGeometry(self):
        
        """
        Calculate the orientation and length along the line
        Orientation is the direction towards the next node in the vector
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


    def GenerateTransects(self,Args):
        """
        Description goes here

        MDH, June 2019
        """

        

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
