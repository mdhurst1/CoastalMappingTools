"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

"""

# import modules
import numpy as np
import shapefile

class Line:
    """
    Description of object goes here

    """

    def __init__(self):
        self.ID = ""
        self.NoNodes = 0
        self.Nodes = []
        self.Projection = ""