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
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCell_CA.shp")

# open shapefiles of -10m contour
BathyLines = gp.read_file(WorkingPath / "Bathymetry" / "Scotland_10m_Bathy_Contour.shp")

# and historic MHWS datasets
MHWS_1890 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1890_FINAL.shp")
MHWS_1970 = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_1970_FINAL.shp")
MHWS_Soft = gp.read_file(WorkingPath / "MHWS_Lines" / "Scotland_MHWS_Modern_Soft.shp")

for index, Row in Cells.iterrows():

    print(Row.Cell_sub)
    
    # Intersection to isolate datasets for each cell
    Bathy = BathyLines.intersection(Row.geometry)
    Old = MHWS_1890.intersection(Row.geometry)
    Inter = MHWS_1970.intersection(Row.geometry)
    Soft = MHWS_Soft.intersection(Row.geometry)
    
    # Save these to new files
    RowName = "Cell_" + Row.Cell_sub
    
    try:
        Bathy.to_file(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"))
        Old.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp"))
        Inter.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp"))
        Soft.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp"))
    
    except:
        print("Unable to write some files for " + Row.Cell_sub)