#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 15:06:27 2020

@author: mhurst
"""

import pickle, pathlib

import numpy as np
import pymc3 as pm

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

# Generate some sample data for demonstration
X = Tr.HistoricShorelinesYears
Y = [Distance[0] for Distance in Tr.HistoricShorlinesDistances]

# Define the model
with pm.Model() as model:
    
    # Priors for the parameters
    alpha = pm.Normal('alpha', mu=0, sd=10)
    beta = pm.Normal('beta', mu=0, sd=10)
    epsilon = pm.HalfCauchy('epsilon', 5)  # Noise term
    
    # Expected value of Y
    mu = alpha + beta * X
    
    # Likelihood (sampling distribution) of Y
    Y_obs = pm.Normal('Y_obs', mu=mu, sd=epsilon, observed=Y)
    
    # Perform MCMC sampling
    trace = pm.sample(2000, tune=1000, cores=1)

# Plot the posterior distributions of parameters
pm.plot_posterior(trace, var_names=['alpha', 'beta', 'epsilon'])

# Print summary statistics of the posterior distributions
print(pm.summary(trace, var_names=['alpha', 'beta', 'epsilon']))