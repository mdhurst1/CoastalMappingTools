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

# set up scenarios
Scenarios = [2,4,8]
Percentiles = [50,50,95]

PrefixNames = ["Open", "Inner"]
FilenameExts = ["_Future.shp", "_Transects.shp"]

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# merge results
#loop through scenarios
for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    print(Scenario)
    
    # set up output folder
    OpenPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
    InnerPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast")
    WritePath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_National")
    

    # For each file type
    for FilenameExt in FilenameExts:
    
        # empty list to accumulate shapes
        TempList = []
        
        # loop through each cell
        for index, Row in Cells.iterrows():
    
            # get cell
            CellSub = Row.Cell_sub
            RowName = "Cell_"+CellSub

            # load future files for open and inner and append
            FutureFile = OpenPath / (RowName + FilenameExt)
            if FutureFile.exists():
                TempGDF = gp.read_file(FutureFile)
                TempList.append(TempGDF)
                
            FutureFile = InnerPath / (RowName + FilenameExt)
            if FutureFile.exists():
                TempGDF = gp.read_file(FutureFile)
                TempList.append(TempGDF)
        
        
        # write new file
        try:
            WriteGDF = pd.concat(TempList, sort=True)
            WriteGDF.to_file(WritePath / ("Scotland_" + FilenameExt))
            print("Written", ("Scotland_" + FilenameExt))
        except:
            import pdb
            pdb.set_trace()
