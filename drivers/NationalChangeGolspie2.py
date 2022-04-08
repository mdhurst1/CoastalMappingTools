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

# # Mean High Water Springs
MHWS = 2.0

# set up a file name to save the coast object
Filename2SaveCoast = WorkingPath / "GolspieChange.pydata"


# # this checks to see whether coast object already exists
try:
    GolspieCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

except:

    print("Creating New Coast Object")

    # SET UP THE COAST FROM -10m Contour
    GolspieCoast = Coast(str(WorkingPath / "Bathymetry" / "MTBathy_Golspie_Clip_Contour_BNG.shp"))
    GolspieCoast.SmoothCoastLines()
    GolspieCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / "OS_Golspie_MHWS_dissolved.shp"),
                                              str(WorkingPath / "Bathymetry" / "MTBathy_Golspie_Clip_Contour_BNG.shp"), 50.)
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(GolspieCoast, PFile)

#### find historic shoreline positions and extend transect accordingly
GolspieCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Golspie_MHWS_1890_FINAL.shp"))
GolspieCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Golspie_MHWS_1970_FINAL.shp"))
GolspieCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Golspie_MHWS_Modern_Soft.shp"))
GolspieCoast.WriteTransectsShp(str(WorkingPath / "Golspie_Transects.shp"))

#### get historical rate of relative sea level change
GolspieCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_RSLR_Modern_BNG.tif"))

### get future relative sea level time series
GolspieCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))

## predict future shorelines
GolspieCoast.SetMHWS(2.)
GolspieCoast.PredictFutureShorelines()

GolspieCoast.WriteFutureShorelinesShp(str(WorkingPath / "GolspieTest.shp"))
