#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 16:42:00 2021

@author: mhurst
"""

import pathlib
import geopandas as gp

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

### FUNCTIONALITY HERE TO SAMPLE FROM NATIONAL DATASETS BASED ON COASTAL CELLS ###
# open shapefile of coastal cells
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

MHWS_LiDAR = gp.read_file(WorkingPath / "MHWS_Lines" / "DC2_Scotland_MHWS_Modern.shp")

CellList = ["1c",]


def ClipLines2Poly(LinesGDF,PolyGDF):

    IntersectionGeometry = LinesGDF.intersection(PolyGDF)
    Clipped = LinesGDF.copy()
    Clipped["geometry"] = IntersectionGeometry
    return Clipped[~Clipped.geometry.is_empty]


for index, Row in Cells.iterrows():

    # Save these to new files
    RowName = "Cell_" + Row.Cell_sub
    print(RowName)
    
    if not Row.Cell_sub in CellList:
        continue
    
    LiDAR = ClipLines2Poly(MHWS_LiDAR, Row.geometry)
    
    for Line in LiDAR:
        if not Line.geometry.type == "LineString":
            print(Line.geometry.type)