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
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")

# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize=501

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# loop through each cell
#for index, Row in Cells.iterrows():
CellSubList = ["2a",]
#CellSubList = ["2a","2b","2c","2d","3a","3b","3c","3e","3f","3g"]
#CellSubList = ["8b","8c","8d","9a","9b","9c","9d","9e","9e"]
#CellSubList = ["1a","10a","10b","10c","10d","10e","10f","10g","8a","8e"]

for CellSub in CellSubList:

    # print cell to screen
    #CellSub = Row.Cell_sub
    print("RUNNING CELL ", CellSub)
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

    # get soft coast position as most recent 
        SoftPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")
        BathyPath = WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")
        OldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")
        QuiteOldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")
        if not BathyPath.is_file():
            continue
        elif not SoftPath.is_file():
            continue
        
        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")))
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize)
        CellCoast.GenerateTransectsNormal2Shp(str(WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Final.shp")),
                                                str(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")), TransectSpacing=TransectSpacing, CheckTopology=True)
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
            

        if not OldPath.is_file():
            print("No 1890s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")))
        
        if not QuiteOldPath.is_file():
            print("No 1970s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")))
        
        
        
        CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath))
            
        CellCoast.WriteTransectsShp(str(WorkingPath / "CoastalCells" / (RowName + "_Transects.shp")))
    
        #### get MHWS for each transect
        CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
    
        #### get historical rate of relative sea level change
        CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
        ### get future relative sea level time series
        CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))
    
    # Extend transects landward by a fixed distance
    HinterlandDistance = 200
    CellCoast.ExtendTransects2Hinterland(HinterlandDistance)    
    CellCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
    
    ## predict future shorelines
    #CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
    #CellCoast.PredictFutureShorelines()
       
    # write future shorelines
    #ResultsPath = WorkingPath / "CoastalCells"
    #CellCoast.WriteFutureShorelinesShp(str(ResultsPath / (RowName + "_Future.shp")),Smooth=False)
    #CellCoast.WriteFutureShorelinesShp(str(ResultsPath / (RowName + "_FutureSmooth.shp")),Smooth=True)
    #CellCoast.WriteFutureUncertaintyShp(str(ResultsPath / (RowName + "_Uncertainty.shp")))
    #CellCoast.WriteFutureUncertaintyShp(str(ResultsPath / (RowName + "_Uncertainty.shp")),Year="2050")
    #CellCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSegments.shp")))
    #CellCoast.WriteErodedAreaShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureErosion.shp")))
    
    # SAVE ENTIRE COAST OBJECT
    #print("\tSaving Coast Object as ", Filename2SaveCoast)
    #with open(str(Filename2SaveCoast), 'wb') as PFile:
    #    pickle.dump(CellCoast, PFile)
    

    

