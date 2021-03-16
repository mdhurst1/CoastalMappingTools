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
from matplotlib import cm
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

Filename = SavePath / "ErosionDistances.csv"

# set sea level scenario
# set up scenarios
Scenarios = [8,4,2]
Percentiles = [95,50,50]
# set up colours for scenarios as red, yellow, blue
ScenarioCms = [cm.Reds, cm.Wistia, cm.Blues]

# set up decades for analysis
Decades = [2030, 2050, 2100]

Resample = False

if Resample:
    
    # this may come back later
    for Scenario, Percentile in zip(Scenarios, Percentiles):
    
        # sample data and save to excel
        with pd.ExcelWriter(SavePath / ("DC2_Total_Erosion_Histogram_Data_RCP_"+str(Scenario)+".xlsx")) as Writer:
        
            # loop through each cell
            for index, Row in Cells.iterrows():
                
                # split cell and letter
                CellSub = Row.Cell_sub
                Sub = CellSub.lstrip('0123456789')
                
                try:
                    Cell = int(CellSub[:len(CellSub)-1])
                except:
                    Cell = int(CellSub)
    
                RowName = "Cell_"+CellSub
                
                # comment this out when ready to do all
                #if not CellSub in CellList:
                #   continue
                
                print(CellSub, end=",")
            
                # define file names
                InnerCoastFile = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast") / (RowName+"_InnerChange.pydata")
                OpenCoastFile = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast") / (RowName+"_OpenChange.pydata")
                            
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
                if not Inner and not Open:
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
                        
                # Retrieve erosion distances on all transects
                ColumnList = ["ED_"+str(Decade) for Decade in Decades]    
                DF = pd.DataFrame()
        
                for Decade in Decades:
                    
                    ErosionDistancesList = []
                    if Open:
                        ErosionDistancesList.append(OpenCoast.get_ErosionDistancesList(Decade))
                    if Inner:
                        ErosionDistancesList.append(InnerCoast.get_ErosionDistancesList(Decade))
                            
                    # flatten the list
                    ErosionDistancesList = [Item for Sublist in ErosionDistancesList for Item in Sublist]
    
                    # add to dataframe
                    ED_DF = pd.DataFrame({'ED'+str(Decade): ErosionDistancesList})
                    DF = pd.concat([DF,ED_DF], axis=1)
                
                DF.to_excel(Writer,sheet_name=RowName)

# make the plots!
# loop through each subcell
for index, Row in Cells.iterrows():

    CellSub = Row.Cell_sub
    RowName = "Cell_"+CellSub
    
    fig = plt.figure(1,figsize=(4,9))
    DF_List = []
    ax_List = []
    Min = 0
    
    for i, (Scenario, Percentile) in enumerate(zip(Scenarios, Percentiles)):
        
        # load sheet
        Filename = SavePath / ("DC2_Total_Erosion_Histogram_Data_RCP_"+str(Scenario)+".xlsx")
        DF = pd.read_excel(Filename, sheet_name=RowName)
        ThisMin = DF["ED"+str(Decades[-1])].dropna().min()
        if ThisMin < Min:
            Min=ThisMin
        DF_List.append(DF)
        
    for i, (Scenario, Percentile) in enumerate(zip(Scenarios, Percentiles)):
        
        SubplotNo = int("31"+str(i+1))
        print(SubplotNo)
        ax = fig.add_subplot(SubplotNo)
        
        Min = DF["ED"+str(Decades[-1])].dropna().min()
        for j, Decade in enumerate(Decades):
            
            Edges = np.arange(Min, 0., 5.)
            Freq, Edges = np.histogram(DF_List[i]["ED"+str(Decade)].dropna(), Edges, density=True)
            Midpoints = (Edges[:-1] + Edges[1:]) / 2
            ax.bar(Midpoints*-1, Freq, align='center', width = Edges[1]-Edges[0],color=ScenarioCms[i](0.1+j*0.4), zorder=10-j)
        
        ax.set_zorder(10)
        ax.set_xlim(0,-Min)
        ax.set_ylim(10^-4,3*10^-1)
        ax.xaxis.set_visible = False
        ax.set_yscale("log")
        ax.set_ylabel("Proportion of coast")
        ax.title.set_text('RCP '+ str(Scenario) + " " + str(Percentile) + "th")

    ax.xaxis.set_visible = True
    ax.set_xlabel("Erosion Distance (m)")
    
    plt.show()
    import sys
    sys.exit()
    

# for each cell overall
    
    
# for Scotland!
    

#plot style
#plt.rcParams[]


#
## each bin should be a single year
#Min = DF["BaselineYear"].min()
#Max = 2020
#Edges = np.arange(Min-0.5,Max+1.5)
#
#Freq, Edges = np.histogram(DF["BaselineYear"],Edges,density=True)
#
#ax.bar(np.arange(Min,Max+1),Freq,color=[.4,.4,.4])
#ax.xaxis.set_minor_locator(MultipleLocator(1))
##ax.set_yscale('log')
#ax.set_xlim(1950,2020)
#
#plt.xlabel("Last observed shoreline year")
#plt.ylabel("Proportion of soft coastline")
#plt.tight_layout()
#plt.savefig(SavePath / "LatestShorelines.pdf")
#plt.savefig(SavePath / "LatestShorelines.png", dpi=600)
#plt.show()
