# -*- coding: utf-8 -*-
"""
Organise coastal datasets for national change assessment based on coasta cells

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

Jan 2020

"""

import pathlib
import geopandas as gp

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

### FUNCTIONALITY HERE TO SAMPLE FROM NATIONAL DATASETS BASED ON COASTAL CELLS ###
# open shapefile of coastal cells
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# and historic MHWS datasets
DC1 = gp.read_file(WorkingPath / "DC1_Results" / "Scotland_Change_1970_Modern_FINAL.shp")

def ClipLines2Poly(LinesGDF,PolyGDF):

    IntersectionGeometry = LinesGDF.intersection(PolyGDF)
    Clipped = LinesGDF.copy()
    Clipped["geometry"] = IntersectionGeometry
    return Clipped[~Clipped.geometry.is_empty]


for index, Row in Cells.iterrows():

    # Intersection to isolate bathy for each cell
    DC1_Clipped = ClipLines2Poly(DC1, Row.geometry)
    
    # Save these to new files
    RowName = "Cell_" + Row.Cell_sub
    
    try:
        DC1_Clipped.to_file(WorkingPath / "DC1_Results" / (RowName + "_DC1_Results.shp"))
    except:
        print("Unable to write DC1 for " + Row.Cell_sub)
    
    