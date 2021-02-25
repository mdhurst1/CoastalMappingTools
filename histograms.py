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
OpenPath = WorkingPath/("RCP_2_50th_OpenCoast")
InnerPath = WorkingPath/("RCP_2_50th_InnerCoast")

# scenario 4.5
OpenPath = WorkingPath/("RCP_4_50th_OpenCoast")
InnerPath = WorkingPath/("RCP_4_50th_InnerCoast")

# scenario 8.6
OpenPath = WorkingPath/("RCP_8_95th_OpenCoast")
InnerPath = WorkingPath/("RCP_8_95th_InnerCoast")