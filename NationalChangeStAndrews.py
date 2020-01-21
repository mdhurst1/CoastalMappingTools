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

# set the transect spacing (in m)
TransectSpacing = 50.
SmoothingWindowSize = 1001
NoSmooths = 4

# set up a file name to save the coast object
Filename2SaveCoast = WorkingPath / "StAndrewsChange.pydata"

print("Creating New Coast Object")

# SET UP THE COAST FROM -10m Contour
RowName = "Cell_2a"

CellCoast = Coast(str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")))

# may need to think carefully about how much to smooth
CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize, NoSmooths=NoSmooths)
CellCoast.WriteCoastShp(str(WorkingPath / "Test_Bathy_Smooth2.shp"))
CellCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")),
                                        str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")), TransectSpacing=TransectSpacing)

CellCoast.WriteTransectsShp(str(WorkingPath / "Test_Transects.shp"))
