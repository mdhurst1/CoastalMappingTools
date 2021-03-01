#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 09:55:53 2021

Summary Statistics for DC2

@author: mhurst
"""

import pathlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, ticker, gridspec, cm
import geopandas as gp
import pandas as pd

# Set up fonts for plots
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['arial']
rcParams['font.size'] = 10
rcParams['text.usetex'] = True
    
fig = plt.figure(1, figsize=(4,12))
ax1 = fig.add_subplot(311)
ax2 = fig.add_subplot(312)
ax3 = fig.add_subplot(313)

#set up working directory
WorkingPath = pathlib.Path.cwd().parent

# first for scenario 2.4
OpenPath = WorkingPath/("RCP_2_50th_National")
TransectsFile = OpenPath / "Scotland__Transects.shp"
GDF = gp.read_file(TransectsFile)
GDF.replace("",float("NaN"),inplace=True)
GDF.dropna(subset=["DC1_RateBC"], inplace=True)

bins = np.arange(-5., 5., 0.2)
ax1.hist([GDF.Hist_Rate,GDF.Rate_2050,GDF.Rate_2100],bins=bins, color=[[0.7,0.7,1.],[0.6,0.6,1.],[0.5,0.5,1.]])

# first for scenario 4.5
#OpenPath = WorkingPath/("RCP_4_50th_National")
#TransectsFile = OpenPath / "Scotland__Transects.shp"
#GDF = gp.read_file(TransectsFile)
#GDF.replace("",float("NaN"),inplace=True)
#GDF.dropna(subset=["DC1_RateBC"], inplace=True)

#bins = np.arange(-5., 5., 0.2)
#ax2.hist([GDF.Hist_Rate,GDF.Rate_2050,GDF.Rate_2100],bins=bins)


# first for scenario 2.4
#OpenPath = WorkingPath/("RCP_2_50th_National")
#TransectsFile = OpenPath / "Scotland__Transects.shp"
#GDF = gp.read_file(TransectsFile)
#GDF.replace("",float("NaN"),inplace=True)
#GDF.dropna(subset=["DC1_RateBC"], inplace=True)

#bins = np.arange(-5., 5., 0.2)
#ax3.hist([GDF.Hist_Rate,GDF.Rate_2050,GDF.Rate_2100],bins=bins)

#ax1.hist(GDF.Rate_2050,bins=bins)
#ax1.hist(GDF.Rate_2100,bins=bins)

