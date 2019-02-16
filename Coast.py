"""
Description of file goes here

Martin D. Hurst
Unviersity of Glasgow
Febraury 2019

"""

# import modules
improt numpy as np
import cartopy.io.shapereader as shpreader

class Coast:
    """
    Description of object goes here

    """

    def __init__(self,arg1,arg2):
        self.coastnodes = -9999.
        self. normals = -9999.

    # read coast from a shapefile
    def ReadCoastShp(self,Shapefile):

        # create the reader object containing shapefile geometries and records
        CoastShp = shpreader(Shapefile)

        # 




    # function to do something    
    def GenerateNormals(self):
        print("trying to get coastline normals")