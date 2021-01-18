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

FilePaths = [WorkingPath/"ShorelineRun", WorkingPath/"ShorelineRunInner"]
PrefixNames = ["Open", "Inner"]
FilenameExts = ["_Future.shp", "_ErodedArea_2050.shp", "_ErodedArea_2100.shp", "_Transects.shp"]

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

FutureList = []
Area2050List = []
Area2100List = []
TransectsList = []

#Do inner then outer
for FilePath, PrefixName in zip(FilePaths,PrefixNames):
    
    print(PrefixName)
    
    for FilenameExt in FilenameExts:
        
        # empty list to accumulate shapes
        TempList = []
    
        # loop through each cell
        for index, Row in Cells.iterrows():
    
            # get cell
            CellSub = Row.Cell_sub
            RowName = "Cell_"+CellSub

            # load future file and append
            FutureFile = FilePath / (RowName + FilenameExt)
            if FutureFile.exists():
                TempGDF = gp.read_file(FutureFile)
                TempList.append(TempGDF)
        
        # write new file
        try:
            WriteGDF = pd.concat(TempList, sort=True)
            WriteGDF.to_file(FilePath / ("Scotland_" + PrefixName + FilenameExt))
            print("Written", ("Scotland_" + PrefixName + FilenameExt))
        except:
            import pdb
            pdb.set_trace()
