#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 15:07:21 2021

@author: mhurst
"""

# import modules
import pickle, pathlib, sys
import pandas as pd
import geopandas as gp
from Coast import *

#set up working directory
WorkingPath = pathlib.Path.cwd().parent

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# set up scenarios
Scenarios = [2]
Percentiles = [50]
Decades = [2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]

#loop through scenarios
for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    print("RCP", Scenario, Percentile)
    
    # set up output folder
    OpenPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
    InnerPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast")
        
    #Loop through Cells
    for index, Row in Cells.iterrows():
        CellSub = Row.Cell_sub
        RowName = "Cell_"+CellSub
        print("\t", RowName)
        
        
        OpenCoastFlag = False
        InnerCoastFlag = False
        
        # load the coast objects
        OpenCoastFilename = OpenPath / (RowName+"_OpenChange.pydata")
        try:
            OpenCoast = pickle.load( open( OpenCoastFilename, "rb" ) )
            OpenCoastFlag = True
            
        except:
            print("No Open Coast Object")
            
        
        InnerCoastFilename = InnerPath / (RowName+"_InnerChange.pydata")
        try:
            InnerCoast = pickle.load( open( InnerCoastFilename, "rb" ) )
            InnerCoastFlag = True

        except:
            print("No Inner Coast Object")
           
        #OpenCoast.WriteFutureShorelinesShp(str(OpenPath / (RowName + "_Future.shp")), Smooth=True)
        #InnerCoast.WriteFutureShorelinesShp(str(InnerPath / (RowName + "_Future.shp")), Smooth=True)
        
        #Loop through decades
        for i, Decade in enumerate(Decades):
            
            print("\t\t", Decade)
            
            #skip 2020
            if i == 0:
                continue
            
            #Write outputs for each decade both inner and open
            if OpenCoastFlag:
                
                OpenCoast.WriteErodedAreaShp(str(OpenPath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")), Year=Decade)
                OpenCoast.WriteErodedAreaShp(str(OpenPath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
                OpenCoast.WriteErosionProximityShp(str(OpenPath / (RowName + "_Influence_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.)
                OpenCoast.WriteErosionProximityShp(str(OpenPath / (RowName + "_Vicinity_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.)
                
            if InnerCoastFlag:
                
                InnerCoast.WriteErodedAreaShp(str(InnerPath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")), Year=Decade)
                InnerCoast.WriteErodedAreaShp(str(InnerPath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
                InnerCoast.WriteErosionProximityShp(str(InnerPath / (RowName + "_Influence_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.)
                InnerCoast.WriteErosionProximityShp(str(InnerPath / (RowName + "_Vicinity_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.)

# merge results
#loop through scenarios
for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    print(Scenario)
    
    # set up output folder
    OpenPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
    InnerPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast")
    FilePaths = [OpenPath, InnerPath]
    PrefixNames = ["Open", "Inner"]
    
    #Do inner then outer
    for FilePath, PrefixName in zip(FilePaths,PrefixNames):
        
        print(PrefixName)
        
        #loop over decades
        for i, Decade in enumerate(Decades):
            
            print(Decade)
            
            # skip 2020
            if i == 0:
                continue
            
            ErodedAreaList = []
            DecadalAreaList = []
            InfluenceList = []
            VicinityList = []
            
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
                
                # load future area file and append
                InfluenceFile = FilePath / (RowName + "_Influence_" + str(Decade) + ".shp")
                
                if InfluenceFile.exists():
                    TempGDF = gp.read_file(InfluenceFile)
                    InfluenceList.append(TempGDF)
                
                # load future area file and append
                VicinityFile = FilePath / (RowName + "_Influence_" + str(Decade) + ".shp")
                
                if VicinityFile.exists():
                    TempGDF = gp.read_file(VicinityFile)
                    VicinityList.append(TempGDF)
            # write new file
            try:
                WriteGDF = pd.concat(ErodedAreaList, sort=True)
                WriteGDF.to_file(FilePath / ("Scotland_" + PrefixName + "_ErodedArea_" + str(Decade) + ".shp"))
            except:
                import pdb
                pdb.set_trace()
                
            
            WriteGDF = pd.concat(DecadalAreaList, sort=True)
            WriteGDF.to_file(FilePath / ("Scotland_" + PrefixName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp"))
            
            WriteGDF = pd.concat(InfluenceList, sort=True)
            WriteGDF.to_file(FilePath / ("Scotland_" + PrefixName + "_Influence_" + str(Decade) + ".shp"))
            
            WriteGDF = pd.concat(VicinityList, sort=True)
            WriteGDF.to_file(FilePath / ("Scotland_" + PrefixName + "_Vicinity_" + str(Decade) + ".shp"))