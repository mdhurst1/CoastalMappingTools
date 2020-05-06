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

# open shapefiles of -10m contour
BathyLines = gp.read_file(WorkingPath / "Bathymetry" / "Scotland_10m_Bathy_Contour_Simple.shp")

# and historic MHWS datasets
MHWS_1890 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1890_FINAL.shp")
MHWS_1970 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1970_Final.shp")
MHWS_Soft = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_Modern_Soft_Simple.shp")
MHWS_Modern = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_Modern_FINAL.shp")

def ClipLines2Poly(LinesGDF,PolyGDF):

    IntersectionGeometry = LinesGDF.intersection(PolyGDF)
    Clipped = LinesGDF.copy()
    Clipped["geometry"] = IntersectionGeometry
    return Clipped[~Clipped.geometry.is_empty]


for index, Row in Cells.iterrows():

    # temporary to work on one cell at a time
    if Row.Cell_sub != "4":
        continue
    
    print(Row.Cell_sub)
    
    # Intersection to isolate bathy for each cell
    BathyClipped = ClipLines2Poly(BathyLines, Row.geometry)
    Old = ClipLines2Poly(MHWS_1890,Row.geometry)
    Inter = ClipLines2Poly(MHWS_1970,Row.geometry)
    Soft = ClipLines2Poly(MHWS_Soft,Row.geometry)
    Modern = ClipLines2Poly(MHWS_Modern,Row.geometry)
    
    # Save these to new files
    RowName = "Cell_" + Row.Cell_sub
    
    try:
        BathyClipped.to_file(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"))
    except:
        print("Unable to write bathy for " + Row.Cell_sub)
    
    try:
        Old.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp"))
    except:
        print("Unable to write 1890s for " + Row.Cell_sub)
    
    try:
        Inter.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp"))
    except:
        print("Unable to write 1970s for " + Row.Cell_sub)
    
    try:    
        Soft.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp"))
    except:
        print("Unable to write soft for " + Row.Cell_sub)
    
    try:
        Modern.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Final.shp"))
    except:
        print("Unable to write modern for " + Row.Cell_sub)