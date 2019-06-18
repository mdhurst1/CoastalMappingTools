"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

class Node:
    
    """
    Description of object goes here

    """
    def __init__(self, ID, X, Y):
        
        self.ID = ID
        self.X = X
        self.Y = Y

    def __str__(self):
        String = "Node Object\nID: %s\nX: %.2f\nY: %.2f\n" %(str(self.ID), self.X, self.Y)
        return String