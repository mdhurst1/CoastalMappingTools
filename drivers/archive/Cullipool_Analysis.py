#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 16:34:08 2022

@author: mhurst
"""

import pickle, pathlib
import geopandas as gp
from Coast import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Customise figure font style
# Set up fonts for plots
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['arial']
rcParams['font.size'] = 12
rcParams['text.usetex'] = True

# define file names for analysis
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/Cullipool/")
DC2Path = WorkingPath.parent / ("WS2_National_Scale_Change/")
DEMPath = WorkingPath/("UAV_Survey_19_4_22/Luing/1_dsm/Luing2_19th_April22_dsm.tif")
ProjectName = "Cullipool"

# set sea level scenario
# set up scenarios
Scenarios = [2,] #4,8]
Percentiles = [50,] #50,95]
   
for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    OutputPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
    
    # # this checks to see whether coast object already exists
    Filename2SaveAll = OutputPath / (ProjectName+"_OpenChange.pydata")

    ThisCoast = pickle.load( open( Filename2SaveAll, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveAll)
    

ChangeRates = [ThisTransect.ChangeRate for ThisLine in ThisCoast.CoastLines for ThisTransect in ThisLine.Transects]

print("Median is", np.median(ChangeRates))
print("Lower quartile is", np.percentile(ChangeRates,16))
print("Upper quartile is", np.percentile(ChangeRates,84))
print("Min", np.min(ChangeRates))
print("Max", np.max(ChangeRates))


print("Median is", np.median(ChangeRates)*27)
print("Lower quartile is", np.percentile(ChangeRates,16)*27)
print("Upper quartile is", np.percentile(ChangeRates,84)*27)
print("Min", np.min(ChangeRates)*27)
print("Max", np.max(ChangeRates)*27)


plt.figure(1, figsize=(4.3,3.3))
plt.hist(ChangeRates)
plt.xlabel("Recession Rate (m yr$^{-1}$)")
plt.ylabel("No Transects")
plt.tight_layout()
plt.savefig("ChangeRateHistogram.png", dpi=600)
plt.show()