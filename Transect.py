"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

import numpy as np
from Node import *

class Transect:
    """
    Description of object goes here

    """
    def __init__(self, ID, CoastNode, StartNode, EndNode):
        
        self.ID = ID
        self.CoastNode = CoastNode
        self.StartNode = StartNode
        self.EndNode = EndNode
        
        self.Orientation = self.CalculateOrientation(self.StartNode, self.EndNode)
        self.Length = self.CalculateLength(self.StartNode, self.EndNode)
        
        self.Distance = None
        self.Elevation = None
        self.ElevationMin = None
        self.ElevationMax = None

        self.FrontHeight = None
        self.FrontTopNode = None
        self.FrontToeNode = None
        self.BackHeight = None
        self.BackTopNode = None
        self.BackToeNode = None
                
        self.ToeWidth = None
        self.TopWidth = None

        self.FrontSlope = None
        self.BackSlope = None


        self.Barrier = True
    
    def __str__(self):
        String = "Transect Object:\nID: %s\n" % (str(self.ID))
        String += "StartNode: "
        String += self.StartNode.__str__()
        String += "EndNode: "
        String += self.EndNode.__str__()
        return String

    def CalculateOrientation(self, Node1, Node2):
        
        """
        
        Maybe this could be a more general function external to class?
        
        MDH
        
        """
        
        #calculate the spatial change
        dx = Node2.X - Node1.X
        dy = Node2.Y - Node1.Y

        #Calculate the orientation of the line
        #N.B. this will depend on where the start segment is
        #so that 270 is esseintially the same as 90 but depends
        #which end of the line the cycle starts at
        if dx > 0 and dy > 0:
            Orientation = np.degrees( np.arctan( dx / dy ) )
        elif dx > 0 and dy < 0:
            Orientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy < 0:
            Orientation = 180.0 + np.degrees( np.arctan( dx / dy ) )
        elif dx < 0 and dy > 0:
            Orientation = 360 + np.degrees( np.arctan( dx / dy ) )
            
        return Orientation
    
    def CalculateLength(self, Node1, Node2):
        
        """
        
        Maybe this could be a more general function external to class?
        
        MDH
        
        """
        
        #calculate the spatial change
        dx = Node2.X - Node1.X
        dy = Node2.Y - Node1.Y
        
        return np.sqrt(dx**2 + dy**2.)

    def AnalyseMorphology(self):
        
        """

        MDH, June 2019

        """

        #Find the highest point of the barrier Zmax
        MaxInd = np.argmax(self.Elevation)
        
        #Get Angle to detrend towards the coast
        Angle = np.degrees(np.arctan((self.Elevation[MaxInd]-self.Elevation[0]) 
                                        / (self.Distance[MaxInd]-self.Distance[0])))
        
        #Get detrended elevation
        ElevDetrendFront = (self.Elevation+(self.Distance[-1]-self.Distance)*np.tan(np.radians(Angle)))
        ElevDetrendFront[0:MaxInd] = np.nan
            
        #Find Minimum and Maximum Ztrend
        self.FrontTopInd = np.argmax(ElevDetrendFront)
        self.FrontToeInd = np.argmin(ElevDetrendFront)
        self.FrontTopNode = Node(self.Distance[self.FrontTopInd], self.Elevation[self.FrontTopInd])
        self.FrontToeNode = Node(self.Distance[self.FrontToeInd], self.Elevation[self.FrontToeInd])
            
        #Check top is not at the end, bottom is ok to be at end
        if not self.FrontTopInd > self.FrontToeInd:
            self.Barrier = False
            print(self.FrontTopInd, self.FrontToeInd)
            print("NOT A BARRIER 1")
            return
        
        #Get Angle to detrend towards away from the coast
        Angle = np.degrees(np.arctan((self.Elevation[self.FrontTopInd]-self.Elevation[0])
                                        / (self.Distance[self.FrontTopInd]-self.Distance[0])))
        
        #Get detrended elevation
        ElevDetrendBack = (self.Elevation+(self.Distance[0]-self.Distance)*np.tan(np.radians(Angle)))
        ElevDetrendBack[self.FrontTopInd+1:] = np.nan
        
        #Find Minimum and Maximum Ztrend
        self.BackTopInd = np.argmax(ElevDetrendBack)
        self.BackToeInd = np.argmin(ElevDetrendBack)
        self.BackTopNode = Node(self.Distance[self.BackTopInd], self.Elevation[self.BackTopInd])
        self.BackToeNode = Node(self.Distance[self.BackToeInd], self.Elevation[self.BackToeInd])
                
        #Check top is not at the end, bottom is ok to be at end
        # again not sure what this is acheiving
        if self.BackTopInd < self.BackToeInd:
            self.Barrier = False
            print("NOT A BARRIER 2")
            return
            
        # Calculate Barrier Height, front and back
        self.FrontHeight = self.FrontTopNode.Y-self.FrontToeNode.Y
        self.BackHeight = self.BackTopNode.Y-self.BackToeNode.Y
                
        # Calculate Barrier Width, top and bottom
        self.ToeWidth = self.FrontToeNode.X-self.BackToeNode.X
        self.TopWidth = self.FrontTopNode.X-self.BackTopNode.X

        # Calculate Slope, front and back
        self.FrontSlope = self.FrontHeight/(self.FrontTopNode.X-self.FrontToeNode.X)
        self.BackSlope = self.BackHeight/(self.BackTopNode.X-self.BackToeNode.X)

        # Volume m3/m
        self.BarrierVolume =  (self.BackToeNode.X * self.BackTopNode.Y - self.BackTopNode.X * self.BackToeNode.Y) 
        self.BarrierVolume += (self.BackTopNode.X * self.FrontTopNode.Y - self.FrontTopNode.X * self.BackTopNode.Y)
        self.BarrierVolume += (self.FrontTopNode.X * self.FrontToeNode.Y - self.FrontToeNode.X * self.FrontTopNode.Y)
        self.BarrierVolume += (self.FrontToeNode.X * self.BackToeNode.Y - self.BackToeNode.X * self.FrontToeNode.Y)
        self.BarrierVolume /= 2

    def ExtractBarrierWidth(self, Elev):

        """
        Extract barrier width at a given elevation (e.g. extreme water level)

        MDH, June 2019
        """


    def get_XY(self):
        
        """
        Returns X and Y coordinates of start and end nodes

        MDH, June 2019
        
        """

        X = [self.StartNode.X, self.EndNode.X]
        Y = [self.StartNode.Y, self.EndNode.Y]
        
        return np.array(X), np.array(Y)