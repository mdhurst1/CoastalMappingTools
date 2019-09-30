"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

import numpy

class Node:
    
    """
    Description of object goes here

    """
    
    def __init__(self, X, Y, Z=None, Dist=None, ID=None):
        
        self.X = X
        self.Y = Y
        self.Z = Z
        self.Dist = Dist
        self.ID = ID

    def __eq__(self,other):
        if (self.X == other.X) and (self.Y == other.Y):
            return True
        elif (abs(self.X-other.X) < 0.0001) and (abs(self.Y-other.Y) < 0.0001):
            print ("Close but no cigar!")
            return False
        else:
            return False
    
        
    def __str__(self):
        String = "Node Object\nX: %.2f\nY: %.2f\n" %(self.X, self.Y)
        return String

    def get_XY(self):
        return self.X, self.Y
    
    def get_XZ(self):
        return self.X, self.Z
    
    def get_Distance(self,OtherNode):
        return np.sqrt((self.X-OtherNode.X)**2.+(self.Y-OtherNode.Y)**2.)
        