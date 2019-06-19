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
    def __init__(self, X, Y):
        
        self.X = X
        self.Y = Y

    def __eq__(self,other):
        return self.__dict__ == other.__dict__
        
    def __str__(self):
        String = "Node Object\nX: %.2f\nY: %.2f\n" %(self.X, self.Y)
        return String