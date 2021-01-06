#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 14:34:46 2021

@author: mhurst
"""

# import geopandas
import pathlib
import geopandas as gp

# Set working directory
WorkingPath = pathlib.Path.cwd().parent
FilePath = WorkingPath/"ShorelineRun"

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

FutureGDF = []

# loop through each cell
for index, Row in Cells.iterrows():
    
    # print cell to screen
    CellSub = Row.Cell_sub
    print("\nAPPENDING CELL", CellSub)
    RowName = "Cell_"+CellSub
    
    # load future file and append
    TempGDF = gp.read_file(FilePath / (RowName + "_Future.shp"))
    FutureGDF.append(TempGDF)

FutureGDF.to_file(FilePath / "Scotland_Future.shp")