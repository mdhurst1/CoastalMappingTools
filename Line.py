"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import sys
import numpy as np
import shapefile
from scipy.signal import savgol_filter
import Transect
import Node

class Line:
    
    """
    """

    def __init__(self, X, Y, ID):
        """
        """
        self.ID = ""
        self.NoNodes = 0
        self.Nodes = []
        self.Projection = ""
        self.Orientation = []
        self.SegmentLength = []
        self.TotalLength = 0

        self.GenerateNodes(X,Y)

    def GenerateNodes(self, X, Y):
        """
        Function to convert X and Y data into Nodes
        """
        # check X and Y are same length
        if len(X) != len(Y):
            sys.exit("Line.GenerateNodes(ERROR): X and Y vectors are not same length.")

        # set the number of nodes on the line
        self.NoNodes = len(X)

        # loop through and create node list
        for i in range(0,self.NoNodes):
            self.Nodes.append(Node(i,X[i],Y[i]))
        
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

    def SmoothLine(self, WindowSize=1000, PolyOrder=4):
        
        """
        Savitzky and Golay (1964) smoothing filter
            
        Savitzky, A. and Golay, M. J.: Smoothing and differentiation of data
            by simplified least squares procedures, Anal. Chem., 36, 1627–
            1639, 1964.
        """

        # Get X and Y vectors from Nodes
        X, Y = self.get_XY()

        # smooth X and Y individually with Savitzky Golay filter
        # window size and polyorder must be integers you idiot!
        XSmooth = savgol_filter(X,WindowSize,PolyOrder, mode="nearest")
        YSmooth = savgol_filter(Y,WindowSize,PolyOrder, mode="nearest")

        # Write new X and Y vectors to Nodes
        GenerateNodes(X,Y)
    
    def GenerateBuffer(self,Dist1,Dist2):
        
        """
        Description goes here

        MDH, June 2019
        """




        

    def GenerateTransects(self,Args):
        """
        Description goes here

        MDH, June 2019
        """

        # Get X and Y vectors from Nodes

        # smooth X and Y individually with Savitzky Golay filter
        # window size and polyorder must be integers you idiot!
        PolyOrder = 4
        XSmooth = savgol_filter(X,WindowSize,PolyOrder, mode="nearest")
        YSmooth = savgol_filter(Y,WindowSize,PolyOrder, mode="nearest")

        # Write new X and Y vectors to Nodes

    def get_XY(self):
        """
        Returns X and Y coordinates as vector numpy arrays

        MDH, June 2019
        """
        X = []
        Y = []
        for i in range(0,NoNodes):
            X.append(Nodes[i].X)
            Y.append(Nodes[i].Y)
        
        return np.array(X), np.array(Y)
