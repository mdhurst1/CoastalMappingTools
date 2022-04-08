# -*- coding: utf-8 -*-
"""
Driver for assessment of future shoreline change in Montrose
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import sys, pickle, pathlib, shapefile
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

# # Montrose Mean High Water Springs
MHWS = 2.5

# set up a file name to save the coast object
Filename2SaveCoast = WorkingPath / "MontroseChange.pydata"


# # this checks to see whether coast object already exists
try:
    MontroseCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

except:

    print("Creating New Coast Object")

    # SET UP THE COAST FROM -10m Contour
    MontroseCoast = Coast(str(WorkingPath / "Bathymetry" / "MTBathy_Montrose_Clip_Contour_BNG.shp"))
    MontroseCoast.SmoothCoastLines()
    MontroseCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / "OS_Montrose_MHWS.shp"),
                                              str(WorkingPath / "Bathymetry" / "MTBathy_Montrose_Clip_Contour_BNG.shp"), 50.)
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(MontroseCoast, PFile)

#### find historic shoreline positions and extend transect accordingly
#MontroseCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Montrose_MHWS_1890_FINAL.shp"))
#MontroseCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Montrose_MHWS_1970_FINAL.shp"))
#MontroseCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Montrose_MHWS_Modern_Soft.shp"))
#MontroseCoast.WriteTransectsShp(str(WorkingPath / "Montrose_Transects.shp"))

#### get historical rate of relative sea level change
#MontroseCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_RSLR_Modern_BNG.tif"))

### get future relative sea level time series
#MontroseCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))

## predict future shorelines
#MontroseCoast.SetMHWS(2.)
MontroseCoast.PredictFutureShorelines()

MontroseCoast.WriteFutureShorelinesShp(str(WorkingPath / "test2.shp"))
