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
        if (self.X == other.X) and (self.Y == other.Y):
            return True
        elif (abs(self.X-other.X) < 0.001) and (abs(self.Y-other.Y) < 0.1):
            print ("Close but no cigar!")
            return False
        
    def __str__(self):
        String = "Node Object\nX: %.2f\nY: %.2f\n" %(self.X, self.Y)
        return String