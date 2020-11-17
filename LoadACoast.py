#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 13 15:06:27 2020

@author: mhurst
"""

import pickle, pathlib
from Coast import *


# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
Cell = "1a"
Filename2LoadCoast = WorkingPath / "ShorelineRun" / ("Cell_"+Cell+"_Change.pydata")
Cst = pickle.load( open( Filename2LoadCoast, "rb" ) )

# set a line and a transect if needed
LineID = "1"
TransectID = "7"

# get line
Lns = Cst.CoastLines
Ln = [Ln for Ln in Lns if Ln.ID == LineID][0]

# get transect
Trs = Ln.Transects
Tr = [Tr for Tr in Trs if Tr.ID == TransectID][0]

#Cst.GetFutureShoreLines()