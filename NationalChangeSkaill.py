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

# smoothing window size
WindowSize = 75

# transect spacing 
TransectSpacing = 1.
Distance2Sea = 100.
Distance2Land = 1000.

# set up a file name to save the coast object
Filename2SaveCoast = WorkingPath / "Skaill_New" / "SkaillChange.pydata"


# # this checks to see whether coast object already exists
try:
    SkaillCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

except:

    print("Creating New Coast Object")

    # SET UP THE COAST FROM -10m Contour
    SkaillCoast = Coast(str(WorkingPath / "Bathymetry" / "MTBathy_Skaill_5m_Contour_BNG.shp"))
    SkaillCoast.SmoothCoastLines(WindowSize)
    SkaillCoast.ReconfigureCoastLines("W")
    
    SkaillCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / "Skaill_MHWS_Modern_Soft_2018.shp"),
                                              str(WorkingPath / "Bathymetry" / "MTBathy_Skaill_Clip_Contour_BNG.shp"), Distance2Sea, Distance2Land, TransectSpacing)
    
    # SAVE ENTIRE COAST OBJECT
    print("Saving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(SkaillCoast, PFile)


#### find historic shoreline positions and extend transect accordingly
SkaillCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Skaill_MHWS_1890_FINAL.shp"))
SkaillCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Skaill_MHWS_1970_FINAL2.shp"))
SkaillCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / "Skaill_MHWS_Modern_Soft_2018.shp"))

SkaillCoast.WriteTransectsShp(str(WorkingPath / "Skaill_New" / "Skaill_Transects.shp"))

#### get historical rate of relative sea level change
SkaillCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_RSLR_Modern_BNG.tif"))

### get future relative sea level time series
SkaillCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))

## predict future shorelines
#### get MHWS for each transect
SkaillCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
SkaillCoast.SetShorefaceDepth(5.)
SkaillCoast.PredictFutureShorelines()

 # write future shorelines
SkaillCoast.WriteFutureShorelinesShp(str(WorkingPath / "Skaill_New" / "Skaill_Future.shp"), Smooth=False)
SkaillCoast.WriteFutureShorelinesShp(str(WorkingPath / "Skaill_New" / "Skaill_FutureSmooth.shp"), Smooth=True)
#Skaillcoast.WriteFutureUncertaintyShp(str(WorkingPath / "CoastalCells" / "Skaill_Uncertainty.shp"))

#SkaillCoast.WriteFutureShorelinesShp(str(WorkingPath / "SkaillTest.shp"))
