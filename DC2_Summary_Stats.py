#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 16:30:15 2021

@author: mhurst
"""

# import modules
import pickle, pathlib, sys
import geopandas as gp
import pandas as pd
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
SavePath = WorkingPath / "Summary_Stats"

if not SavePath.exists():
    SavePath.mkdir(parents=True, exist_ok=True)
       
# set sea level scenario
# set up scenarios
Scenario = 8
Percentile = 95

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")
CellList = ["1a",]
            
# loop through each cell
for index, Row in Cells.iterrows():
    CellSub = Row.Cell_sub
    print("\nRUNNING CELL", CellSub)
    RowName = "Cell_"+CellSub
    
    # comment this out when ready to do all
    if not CellSub in CellList:
        continue
    
    # this may come back later
    # for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    # define file names
    InnerCoastFile = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast") / (RowName+"_InnerChange.pydata")
    OpenCoastFile = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast") / (RowName+"_OpenChange.pydata")
    
    try:
        InnerCoast = pickle.load( open( InnerCoastFile, "rb" ) )
        
    except:
        print("Unable to load", InnerCoastFile)
        raise
        
    try:
        OpenCoast = pickle.load( open( OpenCoastFile, "rb" ) )
        
    except:
        print("Unable to load", OpenCoastFile)
        raise
    
    # Get number of Transects    
    NOpenTransects = OpenCoast.CountTransects()
    NInnerTransects = InnerCoast.CountTransects()
    
    # First mean total erosion each decade
    Decades = [2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]
    OpenMeanTotalErosion = [OpenCoast.get_MeanTotalErosion(Decade) for Decade in Decades[1:]]
    InnerMeanTotalErosion = [OpenCoast.get_MeanTotalErosion(Decade) for Decade in Decades[1:]]
    
    