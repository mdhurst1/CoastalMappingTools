"""
Description of file goes here

Martin D. Hurst
Unviersity of Glasgow
Febraury 2019

"""

# import modules
import numpy as np
import shapefile

class Coast:
    """
    Description of object goes here

    """

    def __init__(self,CoastShp):
        self.CoastShp = CoastShp
        self.CoastNodes = []
        self.Projection = ""

    # read coast from a shapefile
    def ReadCoastShp(self,CoastShp):

        # Open coast polyline file for reading
        SF = shapefile.Reader(CoastShp)
        Shapes = SF.shapes()
        Fields = SF.fields
        Records = SF.records()
        NoShapes = len(Shapes)
        print("\tCoast.ReadCoastShp: Read Coastline, no of segments is", NoShapes)
    
        # get projection strings
        f = open(CoastShp.rstrip("shp")+"prj")
        self.Projection = f.read()
        f.close()
        
        # reduce to single smoothed coastline
    
    return Shapes, Fields, Records, NoShapes, Projection 




    # function to do something    
    def GenerateNormals(self):
        print("trying to get coastline normals")