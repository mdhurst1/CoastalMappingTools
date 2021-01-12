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

FutureGDFList = []
Area2050List = []
Area2100List = []
TransectsList = []
Uncertainty2050List = []
Uncertainty2100List = []

# loop through each cell
for index, Row in Cells.iterrows():
    
    # print cell to screen
    CellSub = Row.Cell_sub
    RowName = "Cell_"+CellSub
    
    # load future file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_Future.shp"))
        FutureGDFList.append(TempGDF)
    
    except:
        continue
    
    # load area 2050 file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_2050.shp"))
        Area2050List.append(TempGDF)
    
    except:
        continue
    
    # load area 2100 file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_2100.shp"))
        Area2100List.append(TempGDF)
    
    except:
        continue
    
    # load future file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_Transects.shp"))
        TransectsList.append(TempGDF)
    
    except:
        continue
    
    # load uncertainty 2050 file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_2050.shp"))
        Uncertainty2050List.append(TempGDF)
    
    except:
        continue
    
    # load uncertainty 2050 file and append
    try:
        TempGDF = gp.read_file(FilePath / (RowName + "_2100.shp"))
        Uncertainty2100List.append(TempGDF)
    
    except:
        continue
    
    FutureGDF = pd.concat(FutureGDFList)
    FutureGDF.to_file(FilePath / "Scotland_Future.shp")
    
    Area2050GDF = pd.concat(Area2050List)
    Area2050GDF.to_file(FilePath / "Scotland_Erosion_Area_2050.shp")
    
    Area2100GDF = pd.concat(FutureGDFList)
    Area2100GDF.to_file(FilePath / "Scotland_Erosion_Area_2100.shp")
    
    TransectsGDF = pd.concat(FutureGDFList)
    TransectsGDF.to_file(FilePath / "Scotland_Transects.shp")
    
    Uncertainty2050GDF = pd.concat(FutureGDFList)
    Uncertainty2050GDF.to_file(FilePath / "Scotland_Uncertainty_2050.shp")
    
    Uncertainty2100GDF = pd.concat(FutureGDFList)
    Uncertainty2100GDF.to_file(FilePath / "Scotland_Uncertainty_2100.shp")