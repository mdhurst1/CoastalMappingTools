"""
Driver for assessment of future shoreline change in Scotland
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

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "Cell_polly.shp")

# loop through each cell
for index, Row in Cells.iterrows():

    # print cell to screen
    print(Row.Name)
    
    # try opening bathy file as check on whether there is data
    try:
        gp.read_file(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"))
    except:
        print("\tUnable to access files for " + Row.Name)
        continue

    # # this checks to see whether coast object already exists
    Filename2SaveCoast = WorkingPath / "CoastalCells" / Row.Name+"_Change.pydata"

    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("\tLoaded Coast Object ", Filename2SaveCoast)

    except:
        print("\tCreating New Coast Object")


        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")))
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines()
        CellCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")),
                                                str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"), TransectSpacing))

    #### find historic shoreline positions and extend transect accordingly
    CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")))
    CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")))
    CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")))
    CellCoast.WriteTransectsShp(str(WorkingPath / "CoastalCells" / (RowName + "_Transects.shp")))

    #### get MHWS for each transect
    CellCoast.SampleMHWS(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))

    #### get historical rate of relative sea level change
    CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_RSLR_Modern_BNG.tif"))

    ### get future relative sea level time series
    CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))

    ## predict future shorelines
    CellCoast.PredictFutureShorelines()

    # write future shorelines
    CellCoast.WriteFutureShorelinesShp(str(WorkingPath / "CoastalCells" / (RowName + "_Future.shp")))
        
    # SAVE ENTIRE COAST OBJECT
    print("\tSaving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(CellCoast, PFile)
