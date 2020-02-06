"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import pickle, pathlib
import geopandas as gp
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

# set the transect spacing (in m)
TransectSpacing = 50.
SmoothingWindowSize=1001

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCell_CA.shp")

# loop through each cell
#for index, Row in Cells.iterrows():
CellSubList = ["2a","2b","2c","2d","3a","3b","3c","3e","3f","3g"]
ReconfigureList = ["e",]
CellSubList = ["2a",]

for CellSub in CellSubList:

    # print cell to screen
    #CellSub = Row.Cell_sub
    print(CellSub)
    RowName = "Cell_"+CellSub
    
    # try opening bathy file as check on whether there is data
    try:
        gp.read_file(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"))
    except:
        print("\tUnable to access files for " + RowName)
        continue

    # # this checks to see whether coast object already exists
    Filename2SaveCoast = WorkingPath / "CoastalCells" / (RowName+"_Change.pydata")

    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("\tLoaded Coast Object ", Filename2SaveCoast)

    except:
        print("\tCreating New Coast Object")


        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")))
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize)
        CellCoast.ReconfigureCoastLines("e") # THIS WILL BE PROBLEMATIC
        CellCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Final.shp")),
                                                str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")), TransectSpacing=TransectSpacing, CheckTopology=True)
        
        #### find historic shoreline positions and extend transect accordingly
        CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")))
        CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")))
        CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")))
        CellCoast.WriteTransectsShp(str(WorkingPath / "CoastalCells" / (RowName + "_Transects.shp")))
    
        #### get MHWS for each transect
        CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
    
        #### get historical rate of relative sea level change
        CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_RSLR_Modern_BNG.tif"))
    
        ### get future relative sea level time series
        CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))
    
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)

    ## predict future shorelines
    #CellCoast.PredictFutureShorelines()
        
    # write future shorelines
    #CellCoast.WriteFutureShorelinesShp(str(WorkingPath / "CoastalCells" / (RowName + "_Future.shp")),Smooth=False)
    #CellCoast.WriteFutureShorelinesShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSmooth.shp")),Smooth=True)
    CellCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSegments.shp")))
    #CellCoast.WriteErodedAreaShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureErosion.shp")))
    
    # SAVE ENTIRE COAST OBJECT
    print("\tSaving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(CellCoast, PFile)
    
    
    

