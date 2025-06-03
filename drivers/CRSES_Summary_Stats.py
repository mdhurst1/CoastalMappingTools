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

# add src path to find custom modules
sys.path.append("../src/")

#import custom modules
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path('/media/14TB_RAID_Array/User_Homes/Craig_MacDonell/CMT_CRSES')
SavePath = WorkingPath / "Summary_Stats"

if not SavePath.exists():
    SavePath.mkdir(parents=True, exist_ok=True)
       
# set sea level scenario
# set up scenarios
Scenarios = [8,4,2]
Percentiles = [95,50,50]

# set up decades for analysis
Decades = [2030, 2050, 2100]
Columns = ['Cell','NoTransects','HistMeanErosion','HistNEroding','HistPercentEroding']

for Decade in Decades:
    Columns.append("MeanErosion"+str(Decade))
    Columns.append("NEroding"+str(Decade))
    Columns.append("PercentEroding"+str(Decade))
    
# get all coastal cells to loop through and order
#Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")
#Cells = Cells.sort_values(by=['Cell_sub'])
CellList = ["1a","1b","1c","1d","2a"]

print(" _______________________ ",
      "|                       |",
      "|   DC2 Summary Stats   |",
      "|_______________________|",
      sep="\n")

# set up excel writer
with pd.ExcelWriter(SavePath / "CRSES_Erosion_Summary_byCell.xlsx") as Writer: 
    
    for Scenario, Percentile in zip(Scenarios, Percentiles):
        
        # set up dataframe
        DF = pd.DataFrame(columns=tuple(Columns))
        
        print("\n****** RCP", Scenario, "*******")
        
        # loop through each cell
        for Cell in CellList:
            
            RowName = "Cell_"+Cell
            # define file names
            OpenCoastFile = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast") / (RowName +"_OpenChange.pydata")
            
            Open = True
            
            try:
                OpenCoast = pickle.load( open( OpenCoastFile, "rb" ) )
                
            except:
                print("\n\tUnable to load open", RowName)
                Open = False
            
            # skip if no data ???
            if not Open:
                continue
            
            # Get number of Transects
            # logic for whether we have inner and open
            if Open:
                NOpenTransects = OpenCoast.get_NumberOfTransects()
            else:
                NOpenTransects = 0
                
            if NOpenTransects == 0:
                Open = False
            
            NTransects = NOpenTransects 
            # its possible to have an object with no transects if segments were all too short
            if NTransects == 0:
                continue
            
            # Get historic erosion
            if Open:
                OpenMeanHistoricErosion = OpenCoast.get_MeanHistoricErosion()
                MeanHistoricErosion = OpenMeanHistoricErosion
            else:
                raise("Refucked")
                
            # First mean total erosion each decade
            # logic for whether we have inner and open
            if Open:
                OpenMeanErosion = [OpenCoast.get_MeanTotalErosion(Decade) for Decade in Decades]
                MeanErosion = OpenMeanErosion
            else:
                raise("FUCKED AGAIN")
                
            values_to_add = {'Cell':Cell, 'NoTransects':NTransects,
                             'HistMeanErosion':MeanHistoricErosion[1], 
                             'HistNEroding':MeanHistoricErosion[0],
                             'HistPercentEroding':100*MeanHistoricErosion[0]/NTransects}
            
            for i, Decade in enumerate(Decades):
                
                values_to_add.update({"MeanErosion"+str(Decade):MeanErosion[i][1]})
                values_to_add.update({"NEroding"+str(Decade):MeanErosion[i][0]})
                values_to_add.update({"PercentEroding"+str(Decade):100*MeanErosion[i][0]/NTransects})
            
            # add to dataframe
            row_df = pd.DataFrame([values_to_add], index=[Cell])
            DF = pd.concat([DF, row_df])
            
        #Write sheet for scenario
        print("Writing Excel for RCP",str(Scenario))
        DF.to_excel(Writer,sheet_name="RCP_"+str(Scenario)+"_"+str(Percentile)+"th")