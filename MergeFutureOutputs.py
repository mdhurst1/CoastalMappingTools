#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  6 14:34:46 2021

@author: mhurst
"""

# import geopandas
import pathlib
import pandas as pd
import geopandas as gp

# Set working directory
WorkingPath = pathlib.Path.cwd().parent
FilePath = WorkingPath/"ShorelineRun"

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

FutureList = []
Area2050List = []
Area2100List = []
TransectsList = []

# loop through each cell
for index, Row in Cells.iterrows():
    
    # print cell to screen
    CellSub = Row.Cell_sub
    RowName = "Cell_"+CellSub
    
    # load future file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_Future.shp"))
        FutureList.append(TempGDF)
    
    except:
        continue
    
    # load area 2050 file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_ErodedArea_2050.shp"))
        Area2050List.append(TempGDF)
    
    except:
        continue
    
    # load area 2100 file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_ErodedArea_2100.shp"))
        Area2100List.append(TempGDF)
    
    except:
        continue
    
    # load future file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_Transects.shp"))
        TransectsList.append(TempGDF)
    
    except:
        continue
    
    FutureGDF = pd.concat(FutureList)
    FutureGDF.to_file(FilePath / "Scotland_Open_Future.shp")
    
    Area2050GDF = pd.concat(Area2050List)
    Area2050GDF.to_file(FilePath / "Scotland_Open_Erosion_Area_2050.shp")
    
    Area2100GDF = pd.concat(Area2100List)
    Area2100GDF.to_file(FilePath / "Scotland_Open_Erosion_Area_2100.shp")
    
    TransectsGDF = pd.concat(TransectsList)
    TransectsGDF.to_file(FilePath / "Scotland_Open_Transects.shp")
    