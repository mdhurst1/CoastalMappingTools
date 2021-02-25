#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 12:16:42 2021

@author: mhurst
"""

# import modules
import pathlib
import pandas as pd
import geopandas as gp
from Coast import *

#set up working directory
WorkingPath = pathlib.Path.cwd().parent

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# set up scenarios
Scenarios = [2,4,8]
Percentiles = [50,50,95]
Decades = [2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]

# merge results
#loop through scenarios
for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    print(Scenario)
    
    # set up output folder
    OpenPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
    InnerPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast")
    WritePath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_National")
    
    if not WritePath.exists():
        WritePath.mkdir(parents=True, exist_ok=True)
        
    FilePaths = [OpenPath, InnerPath]
    PrefixNames = ["Open", "Inner"]
    
    #loop over decades
    for i, Decade in enumerate(Decades):
        
        print(Decade)
        
        # skip 2020
        if i == 0:
            continue
        
        ErodedAreaList = []
        DecadalAreaList = []
        
        #Do inner then outer
        for FilePath, PrefixName in zip(FilePaths,PrefixNames):
            
            # loop through cells
            for index, Row in Cells.iterrows():
                CellSub = Row.Cell_sub
                RowName = "Cell_"+CellSub
                
                # load future area file and append
                FutureFile = FilePath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")
                
                if FutureFile.exists():
                    TempGDF = gp.read_file(FutureFile)
                    ErodedAreaList.append(TempGDF)
                    
                # load future area file and append
                FutureFile = FilePath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")
                
                if FutureFile.exists():
                    TempGDF = gp.read_file(FutureFile)
                    DecadalAreaList.append(TempGDF)
                    
        # write new file
        WriteGDF = pd.concat(ErodedAreaList, sort=True)
        WriteGDF.to_file(WritePath / ("Scotland_ErodedArea_" + str(Decade) + ".shp"))
        WriteGDF = pd.concat(DecadalAreaList, sort=True)
        WriteGDF.to_file(WritePath / ("Scotland_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp"))