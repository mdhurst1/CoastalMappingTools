#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 18:58:31 2021

Histogram of baseline years

@author: mhurst

"""

# import modules
import pickle, pathlib
import pandas as pd
import geopandas as gp
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
SavePath = WorkingPath / "Summary_Stats"

if not SavePath.exists():
    SavePath.mkdir(parents=True, exist_ok=True)

# get all coastal cells to loop through and order
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")
Cells = Cells.sort_values(by=['Cell_sub'])

Filename = SavePath / "MostRecentYears.csv"

# switch here to load data if already extracted
Resample = False
if not Resample:
    DF = pd.read_csv(Filename)
    
else:
        
    #CellList = ["1a",]
    
    BaselineYearList = []
    
    # loop through each cell
    for index, Row in Cells.iterrows():
        CellSub = Row.Cell_sub
        RowName = "Cell_"+CellSub
        
        # comment this out when ready to do all
        #if not CellSub in CellList:
        #   continue
        
        print(CellSub, end=",")
        
        # this may come back later
        # for Scenario, Percentile in zip(Scenarios, Percentiles):
        
        # define file names
        InnerCoastFile = WorkingPath / ("RCP_8_95th_InnerCoast") / (RowName+"_InnerChange.pydata")
        OpenCoastFile = WorkingPath / ("RCP_8_95th_OpenCoast") / (RowName+"_OpenChange.pydata")
        
        Inner = True
        Open = True
                
        try:
            InnerCoast = pickle.load( open( InnerCoastFile, "rb" ) )
            
        except:
            print("\n\tUnable to load inner", RowName)
            Inner = False
            
        try:
            OpenCoast = pickle.load( open( OpenCoastFile, "rb" ) )
            
        except:
            print("\n\tUnable to load open", RowName)
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
                
        # its possible to have an object with no transects if segments were all too short
        if NTransects == 0:
            continue
                
        # Retrieve latest years on all transects
        if Open:
            BaselineYearList.append(OpenCoast.get_RecentShorelinesYearsList())
            
        if Inner:
            BaselineYearList.append(InnerCoast.get_RecentShorelinesYearsList())
    
    # flatten the list
    BaselineYearList = [Item for Sublist in BaselineYearList for Item in Sublist]

    DF = pd.DataFrame(columns=['BaselineYear'])
    DF["BaselineYear"] = BaselineYearList
    DF.to_csv(Filename)

# make the plot!

#plot style
#plt.rcParams[]

fig = plt.figure(1,figsize=(4,3))
ax = fig.add_subplot(111)

# each bin should be a single year
Min = DF["BaselineYear"].min()
Max = 2020
Edges = np.arange(Min-0.5,Max+1.5)

Freq, Edges = np.histogram(DF["BaselineYear"],Edges,density=True)

ax.bar(np.arange(Min,Max+1),Freq,color=[.4,.4,.4])
ax.xaxis.set_minor_locator(MultipleLocator(1))
#ax.set_yscale('log')
ax.set_xlim(1950,2020)

plt.xlabel("Last observed shoreline year")
plt.ylabel("Proportion of soft coastline")
plt.tight_layout()
plt.savefig(SavePath / "LatestShorelines.pdf")
plt.savefig(SavePath / "LatestShorelines.png", dpi=600)
plt.show()
