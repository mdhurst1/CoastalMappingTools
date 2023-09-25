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
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS2_National_Scale_Change/Supersites/Musselburgh_2023")

Scenario = 8
Percentile = 95
Cell = "1b"
InnerorOpen = "Open"

#Filename2LoadCoast = WorkingPath / "ShorelineRunInner" / ("Cell_"+Cell+"_InnerChange.pydata")
#Filename2LoadCoast = WorkingPath / ("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast") / ("Cell_"+Cell+"_OpenChange.pydata")
#Filename2LoadCoast = WorkingPath / "Geometry" / ("Cell_" + Cell + "_" + InnerorOuter + "Geometry.pydata")
Filename2LoadCoast = WorkingPath / "Geometry" / ("Cell_" + Cell + "_" + InnerorOpen + "Geometry.pydata")

Cst = pickle.load( open( Filename2LoadCoast, "rb" ) )

# set a line and a transect if needed
LineID = "0"
TransectID = "80"

# get line
Lns = Cst.CoastLines
Ln = [Ln for Ln in Lns if Ln.ID == LineID][0]

# get transect
Trs = Ln.Transects
Tr = [Tr for Tr in Trs if Tr.ID == TransectID][0]

#Cst.GetFutureShoreLines()
print(Tr.ID)
print(Tr.HistoricShorelinesYears)
print(Tr.HistoricShorelinesDistances)

Tr.PlotFuturePositions(WorkingPath / "Plots")
Tr.PlotShorelineDistances(WorkingPath / "Plots")
