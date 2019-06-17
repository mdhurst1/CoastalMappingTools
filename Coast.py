"""
Description of file goes here

Martin D. Hurst
University of Glasgow
June 2019

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
        self.NoCoastLines = 0
        self.CoastLines = []
        self.Projection = ""

    # read coast from a shapefile
    def ReadCoastShp(self,CoastShp):

        # Open coast polyline file for reading
        SF = shapefile.Reader(CoastShp)
        Shapes = SF.shapes()
        Fields = SF.fields
        Records = SF.records()

        # Get number of coast segments to work on
        self.NoCoastLines = len(Shapes)
        print("\tCoast.ReadCoastShp: Read Coastline, no of coast segments is", self.NoCoastLines)
    
        # Generate coast nodes for each segment
        for i in range(0,self.NoCoastLines):
            
            # get X and Y coordinates of segment
            X, Y = np.array(Shapes[i].points).T
            
            # Set up a line object for each

        # get projection strings
        f = open(CoastShp.rstrip("shp")+"prj")
        self.Projection = f.read()
        f.close()
        
        # reduce to single smoothed coastline
    
    return Shapes, Fields, Records, NoShapes, Projection 




    # function to do something    
    def GenerateNormals(self):
        print("trying to get coastline normals")