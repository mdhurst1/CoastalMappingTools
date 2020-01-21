# -*- coding: utf-8 -*-
"""
Driver for assessment of future shoreline change in St Andrews
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import sys, pickle, pathlib, shapefile
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

# # Mean High Water Springs
MHWS = 2.0

# set the transect spacing (in m)
TransectSpacing = 50.
SmoothingWindowSize = 1001

# set up a file name to save the coast object
Filename2SaveCoast = WorkingPath / "StAndrewsChange.pydata"

print("Creating New Coast Object")

# SET UP THE COAST FROM -10m Contour
StAndrewsCoast = Coast(str(WorkingPath / "Bathymetry" / "MTBathy_StAndrews_10m_Contour_BNG.shp"))
StAndrewsCoast.SmoothCoastLines(SmoothingWindowSize)

StAndrewsCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / "StAndrews_MHWS_Modern_Soft_2018.shp"),
                                            str(WorkingPath / "Bathymetry" / "MTBathy_StAndrews_Clip_Contour_BNG.shp"), Distance2Sea, Distance2Land, TransectSpacing)

StAndrewsCoast.WriteTransectsShp(str(WorkingPath / "StAndrews_Transects.shp"))

