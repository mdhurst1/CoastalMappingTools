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
Scenarios = [8,4,2]
Percentiles = [95,50,50]

# set up decades for analysis
Decades = [2030, 2050, 2100]
Columns = ['Location','NoTransects']
for Decade in Decades:
    Columns.append("MeanErosion"+str(Decade))
    Columns.append("NEroding"+str(Decade))
    Columns.append("PercentEroding"+str(Decade))
    
# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")
#CellList = ["1a",]

print(" _______________________ ",
      "|                       |",
      "|   DC2 Summary Stats   |",
      "|_______________________|",
      sep="\n")

# set up excel writer
with pd.ExcelWriter(SavePath / "DC2_Total_Erosion_Summary.xlsx") as Writer: 
    
    for Scenario, Percentile in zip(Scenarios, Percentiles):
        
        # set up dataframe
        DF = pd.DataFrame(columns=tuple(Columns))
        
        print("\n****** RCP", Scenario, "*******")
        
        # loop through each cell
        for index, Row in Cells.iterrows():
            CellSub = Row.Cell_sub
            RowName = "Cell_"+CellSub
            
            # comment this out when ready to do all
            # if not CellSub in CellList:
            #    continue
            
            print(CellSub, end=",")
            
            # this may come back later
            # for Scenario, Percentile in zip(Scenarios, Percentiles):
            
            # define file names
            InnerCoastFile = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast") / (RowName+"_InnerChange.pydata")
            OpenCoastFile = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast") / (RowName+"_OpenChange.pydata")
            
            Inner = True
            Open = True
            
            try:
                InnerCoast = pickle.load( open( InnerCoastFile, "rb" ) )
                
            except:
                print("Unable to load inner", RowName)
                Inner = False
                
            try:
                OpenCoast = pickle.load( open( OpenCoastFile, "rb" ) )
                
            except:
                print("Unable to load open", RowName)
                Open = False
            
            # skip if no data ???
            if not Inner and Open:
                continue
            
            # Get number of Transects
            # logic for whether we have inner and open
            if Inner and Open:
                NTransects = OpenCoast.get_NumberOfTransects() + InnerCoast.get_NumberOfTransects()
            elif Inner:
                NTransects = InnerCoast.get_NumberOfTransects()
            elif Open:
                NTransects = OpenCoast.get_NumberOfTransects()
            else:
                raise("FUCKED")
                
            # First mean total erosion each decade
            # logic for whether we have inner and open
            if Open:
                OpenMeanErosion = [OpenCoast.get_MeanTotalErosion(Decade) for Decade in Decades]
            if Inner:
                InnerMeanErosion = [InnerCoast.get_MeanTotalErosion(Decade) for Decade in Decades]
            if Inner and Open:
                MeanErosion = [(Open[0]+Inner[0], ((Open[0]*Open[1] + Inner[0]*Inner[1])/(Open[0]+Inner[0]))) for Open, Inner in zip(OpenMeanErosion,InnerMeanErosion)]
            elif Inner:
                MeanErosion = InnerMeanErosion
            elif Open:
                MeanErosion = OpenMeanErosion
            else:
                raise("FUCKED AGAIN")
                
            values_to_add = {'Location':CellSub, 'NoTransects':NTransects}
            
            for i, Decade in enumerate(Decades):
                
                values_to_add.update({"MeanErosion"+str(Decade):MeanErosion[i][1]})
                values_to_add.update({"NEroding"+str(Decade):MeanErosion[i][0]})
                values_to_add.update({"PercentEroding"+str(Decade):100*MeanErosion[i][0]/NTransects})
            
            # add to dataframe
            row_to_add = pd.Series(values_to_add, name=CellSub)
            DF = DF.append(row_to_add)
        
        # CALCULATE TOTALS FOR SCOTLAND
        TotalNTransects = DF.NoTransects.sum()
        values_to_add = {'Location':"SCOTLAND", 'NoTransects':TotalNTransects}
        for i, Decade in enumerate(Decades):
            
            # calculate for all of Scotland
            TotalMeanErosion = (DF["MeanErosion"+str(Decade)] * DF["NEroding"+str(Decade)]).sum()/len(DF)
            TotalNEroding = (DF["NEroding"+str(Decade)]).sum()
            TotalPercentEroding = 100*TotalNEroding/TotalNTransects
            
            # update dictionary to add to dataframe
            values_to_add.update({"MeanErosion"+str(Decade):TotalMeanErosion})
            values_to_add.update({"NEroding"+str(Decade):TotalNEroding})
            values_to_add.update({"PercentEroding"+str(Decade):TotalPercentEroding})
        
        # add to dataframe
        row_to_add = pd.Series(values_to_add, name="SCOTLAND")
        DF = DF.append(row_to_add)
        
        #Write sheet for scenario
        DF.to_excel(Writer,sheet_name="RCP_"+str(Scenario)+"_"+str(Percentile)+"th")
