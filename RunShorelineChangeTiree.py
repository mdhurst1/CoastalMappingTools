"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import pickle, pathlib, sys
import geopandas as gp
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

# set the transect spacing (in m)
TransectSpacing = 50.
SmoothingWindowSize=1001

# try opening bathy file as check on whether there is data
# # this checks to see whether coast object already exists
Filename2SaveCoast = WorkingPath / "CoastalCells" / "Tiree_Change.pydata"

try:
    TireeCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("\tLoaded Coast Object ", Filename2SaveCoast)

except:
    print("\tCreating New Coast Object")


    # SET UP THE COAST FROM -10m Contour
    TireeCoast = Coast(str(WorkingPath / "Bathymetry" / "Tiree_10m_Bathy_Contour.shp"))
    
    # may need to think carefully about how much to smooth
    TireeCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=3)
    TireeCoast.WriteCoastShp(str(WorkingPath / "Bathymetry" / "Tiree_Smooth_Bathy.shp"))
    TireeCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / ("Tiree_MHWS_1890.shp")),
                                            str(WorkingPath / "Bathymetry" / ("Tiree_10m_Bathy_Contour.shp")), 
                                             TransectSpacing=TransectSpacing, Distance2Sea=5000., Distance2Land=5000., CheckTopology=True)
    
    TireeCoast.WriteTransectsShp(str(WorkingPath / "CoastalCells" / ("Tiree_Transects.shp")))
    
    #### find historic shoreline positions and extend transect accordingly
    TireeCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / ("Tiree_MHWS_1890.shp")))
    TireeCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / ("Tiree_MHWS_1970.shp")))
    TireeCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / ("Tiree_Modern_Soft.shp")))
    TireeCoast.WriteTransectsShp(str(WorkingPath / "CoastalCells" / ("Tiree_Transects.shp")))

    #### get MHWS for each transect
    TireeCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))

    #### get historical rate of relative sea level change
    TireeCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_RSLR_Modern_BNG.tif"))

    ### get future relative sea level time series
    TireeCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))

    # SAVE ENTIRE COAST OBJECT
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(TireeCoast, PFile)

## predict future shorelines
#TireeCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
TireeCoast.PredictFutureShorelines()
    
# write future shorelines
TireeCoast.WriteFutureShorelinesShp(str(WorkingPath / "CoastalCells" / ("Tiree_Future.shp")),Smooth=False)
TireeCoast.WriteFutureShorelinesShp(str(WorkingPath / "CoastalCells" / ("Tiree_FutureSmooth.shp")),Smooth=True)
#TireeCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / ("Tiree" + "_FutureSegments.shp")))
#TireeCoast.WriteErodedAreaShp(str(WorkingPath / "CoastalCells" / ("Tiree" + "_FutureErosion.shp")))

# SAVE ENTIRE COAST OBJECT
print("\tSaving Coast Object as ", Filename2SaveCoast)
with open(str(Filename2SaveCoast), 'wb') as PFile:
    pickle.dump(TireeCoast, PFile)
    

    

