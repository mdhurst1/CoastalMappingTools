"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import numpy as np
import shapefile
from scipy.signal import savgol_filter
import Transect
import Nodes

class Line:
    """
    Description of object goes here

    """

    def __init__(self, X, Y, ID):
        self.ID = ""
        self.NoNodes = 0
        self.Nodes = []
        self.Projection = ""

    def SmoothLine(self, WindowSize):
        """
        Description goes here
        """

        # Get X and Y vectors from Nodes

        # smooth X and Y individually with Savitzky Golay filter
        # window size and polyorder must be integers you idiot!
        PolyOrder = 4
        XSmooth = savgol_filter(X,WindowSize,PolyOrder, mode="nearest")
        YSmooth = savgol_filter(Y,WindowSize,PolyOrder, mode="nearest")

        # Write new X and Y vectors to Nodes
    
    def GenerateBuffers(self,Dist1,Dist2):
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
