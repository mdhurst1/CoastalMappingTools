#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 15:06:27 2020

@author: mhurst
"""

import pickle, pathlib

# add src path to find custom modules
import sys
sys.path.append("../src/")
from Coast import *


# define file names for analysis
#WorkingPath = pathlib.Path.cwd().parent
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS2_National_Scale_Change/Supersites/Montrose_2024/CMT")

Scenario = 8
Percentile = 95
Cell = "2b"
InnerorOpen = "Open"

#Filename2LoadCoast = WorkingPath / "ShorelineRunInner" / ("Cell_"+Cell+"_InnerChange.pydata")
Filename2LoadCoast = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast") / ("Cell_"+Cell+"_OpenChange.pydata")
#Filename2LoadCoast = WorkingPath / "Geometry" / ("Cell_" + Cell + "_" + InnerorOuter + "Geometry.pydata")
#Filename2LoadCoast = WorkingPath / "Geometry" / ("Cell_" + Cell + "_" + InnerorOpen + "Geometry.pydata")

Cst = pickle.load( open( Filename2LoadCoast, "rb" ) )

# set a line and a transect if needed
LineID = "0"
TransectID = "118"

# get line
Lns = Cst.CoastLines
Ln = [Ln for Ln in Lns if Ln.ID == LineID][0]

# get transect
Trs = Ln.Transects
Tr = [Tr for Tr in Trs if Tr.ID == TransectID][0]

Tr.CalculateHistoricalRegression_testing()


# =============================================================================
# #Cst.GetFutureShoreLines()
# print("Transect ID =", Tr.ID,"\n")
# print("Transect Shoreline Years:\n",Tr.HistoricShorelinesYears,"\n")
# print("Transect Hist. Shoreline Dists:\n", Tr.HistoricShorelinesDistances,"\n")
# 
# printout = []
# if len(Tr.HistoricShorelinesYears) == len(Tr.HistoricShorelinesDistances):
#     for i in range(len(Tr.HistoricShorelinesYears)-1):
#         SLineList = []
#         SLineList.append(Tr.HistoricShorelinesYears[i])
#         SLineList.append(Tr.HistoricShorelinesDistances[i][0])
#         SLineList.append(Tr.HistoricShorelinesSources[i])
#         printout.append(SLineList)
#         
#         crList = []
#         crYears = str(Tr.HistoricShorelinesYears[i]) + "-" + str(Tr.HistoricShorelinesYears[i+1])
#         crList.append(crYears)
#         crYearsCalc = Tr.HistoricShorelinesYears[i+1] - Tr.HistoricShorelinesYears[i]
#         crDist = round((Tr.HistoricShorelinesDistances[i+1][0] - Tr.HistoricShorelinesDistances[i][0])*-1,3) # *-1 is for directionality
#         crList.append(crDist)
#         cRate = round(crDist / crYearsCalc,3)
#         crList.append(cRate)
#         printout.append(crList)
#         
#     SLineList = []
#     SLineList.append(Tr.HistoricShorelinesYears[-1])
#     SLineList.append(Tr.HistoricShorelinesDistances[-1][0])
#     SLineList.append(Tr.HistoricShorelinesSources[-1])
#     printout.append(SLineList)
#     
# print(printout)
#         
# PlotsPath = WorkingPath / "Plots"
# 
# if not PlotsPath.exists():
#     PlotsPath.mkdir(parents=True, exist_ok=True)
# 
# Tr.PlotFuturePositions(PlotsPath)
# Tr.PlotShorelineDistances(PlotsPath)
# =============================================================================
