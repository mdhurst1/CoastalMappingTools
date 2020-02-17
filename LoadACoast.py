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
Cell = "2a"
Filename2LoadCoast = WorkingPath / "CoastalCells" / ("Cell_"+Cell+"_Change.pydata")
CellCoast = pickle.load( open( Filename2LoadCoast, "rb" ) )