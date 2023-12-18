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

# add src path to find custom modules
sys.path.append("../src/")

#import custom modules
from Coast import *

#set up working directory
#WorkingPath = pathlib.Path.cwd().parent
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS2_National_Scale_Change/Supersites/Musselburgh_2023/CMT")

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# set up scenarios
Scenarios = [2]
Percentiles = [50]
Decades = [2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]
#Decades = [2020,2050,2100]

CellList = ["1b"]

#%% loop through scenarios
for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    print("RCP", Scenario, Percentile)
    
    # set up output folder
    OpenPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
    InnerPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast")
        
    #Loop through Cells
    #for index, Row in Cells.iterrows():
        #CellSub = Row.Cell_sub
    RowName = "Cell_1b"
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

#%% merge results

# set up output folder
OpenPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast") # repeated...
InnerPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast") # repeated...
FilePaths = [OpenPath, InnerPath] # earlier?
PrefixNames = ["Open", "Inner"] # earlier ?

#%%Do inner then outer
for FilePath, PrefixName in zip(FilePaths,PrefixNames):
    
    print(PrefixName)
    
    #loop over decades
    for i, Decade in enumerate(Decades):
        
        print(PrefixName)
        print(Decade)
        
        # skip 2020
        if i == 0:
            continue
        
        ErodedAreaList = []
        DecadalAreaList = []
        InfluenceList = []
        VicinityList = []
        
        # loop through cells
        #for index, Row in Cells.iterrows():
                #CellSub = Row.Cell_sub
        RowName = "Cell_1b"
            
        # load future area file and append
        FutureFile = FilePath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")
        print('FutureFile1')
        print(FutureFile)
        
        if FutureFile.exists():
            TempGDF = gp.read_file(FutureFile)
            ErodedAreaList.append(TempGDF)
        else:
            print('Future File (1) does not exist, nothing to be appended to Eroded Area List')
            
        # load future area file and append
        FutureFile = FilePath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")
        print('FutureFile2')
        print(FutureFile)
        
        if FutureFile.exists():
            TempGDF = gp.read_file(FutureFile)
            DecadalAreaList.append(TempGDF)
        else:
            print('Future File (2) does not exist, nothing to be appended to Decadal Area List')
        
        # load future area file and append
        InfluenceFile = FilePath / (RowName + "_Influence_" + str(Decade) + ".shp")
        print('InfluenceFile')
        print(InfluenceFile)
        
        if InfluenceFile.exists():
            TempGDF = gp.read_file(InfluenceFile)
            InfluenceList.append(TempGDF)
        else:
            print('Influence File does not exist, nothing to be appended to Influence List')
        
        # load future area file and append
        VicinityFile = FilePath / (RowName + "_Vicinity_" + str(Decade) + ".shp")
        print('VicinityFile')
        print(VicinityFile)
        
        if VicinityFile.exists():
            TempGDF = gp.read_file(VicinityFile)
            VicinityList.append(TempGDF)
        else:
            print('Vicinity File does not exist, nothing to be appended to Vicinity List')
            
        print(Decade)
        print('end \n')
        
        # write new file
        if len(ErodedAreaList) == 0:
            print('Eroded Area list has no contents')
            continue
        elif len(ErodedAreaList) > 0:
            print('writing Eroded Area list')
            WriteGDF = pd.concat(ErodedAreaList, sort=True)
            WriteGDF.to_file(FilePath / ("Musselburgh_" + PrefixName + "_ErodedArea_" + str(Decade) + ".shp"))
            
        if len(DecadalAreaList) == 0:
            print('Decadal Area list has no contents')
            continue
        elif len(DecadalAreaList) > 0:
            print('writing Decadal Area list')
            WriteGDF = pd.concat(DecadalAreaList, sort=True)
            WriteGDF.to_file(FilePath / ("Musselburgh_" + PrefixName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp"))
            
        if len(InfluenceList) == 0:
            print('Influence list has no contents')
            continue
        elif len(InfluenceList) > 0:
            print('writing Influence list')
            WriteGDF = pd.concat(InfluenceList, sort=True)
            WriteGDF.to_file(FilePath / ("Musselburgh_" + PrefixName + "_Influence_" + str(Decade) + ".shp"))
            
        if len(VicinityList) == 0:
            print('Vicinity list has no contents')
            continue
        elif len(VicinityList) > 0:
            print('writing Vicinity list')
            WriteGDF = pd.concat(VicinityList, sort=True)
            WriteGDF.to_file(FilePath / ("Musselburgh_" + PrefixName + "_Vicinity_" + str(Decade) + ".shp"))
