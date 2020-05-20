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
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")
OutputPath = WorkingPath/"FinalNationalRun"
# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize=501

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# loop through each cell
for index, Row in Cells.iterrows():

    # print cell to screen
    CellSub = Row.Cell_sub
    print("\nRUNNING CELL", CellSub)
    RowName = "Cell_"+CellSub
    
    # try opening bathy file as check on whether there is data
    try:
        gp.read_file(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"))
    except:
        print("\tUnable to access files for " + RowName)
        continue

    # # this checks to see whether coast object already exists
    Filename2SaveCoast = OutputPath / (RowName+"_Change.pydata")

    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("Loaded Coast Object ", Filename2SaveCoast)

    except:
        print("Creating New Coast Object")

        # get soft coast position as most recent
        ModernPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Final.shp")
        SoftPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")
        BathyPath = WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")
        OldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")
        QuiteOldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")
        
        if not BathyPath.is_file():
            continue
        elif not SoftPath.is_file():
            continue
        
        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(BathyPath))
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize)
        
        # write smoothed coast/bathy to file
        CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))

        CellCoast.GenerateTransectsBetweenContoursShp(str(ModernPath), str(BathyPath), 
                                            TransectSpacing=TransectSpacing, CheckTopology=False)
        
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Test.shp")))
        sys.exit()
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
            
        if not OldPath.is_file():
            print("No 1890s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(OldPath))
        
        if not QuiteOldPath.is_file():
            print("No 1970s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
        
        if not SoftPath.is_file():
            print("No soft MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath))
            
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
    
        #### get MHWS for each transect
        CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
    
        #### get historical rate of relative sea level change
        CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
        ### get future relative sea level time series
        CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    sys.exit()
    
    # Extend transects landward by a fixed distance
    HinterlandDistance = 200
    CellCoast.ExtendTransects2Hinterland(HinterlandDistance)
    CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_ExtendedTransects.shp")))
    CellCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
    CellCoast.ExtractTransectTopography()
    
    ## predict future shorelines
    #CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
    CellCoast.PredictFutureShorelines()

    # write future shorelines
    CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),Smooth=True)
    CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_Uncertainty_2100.shp")))
    CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_Uncertainty_2050.shp")),Year="2050")

    CellCoast.WriteErodedAreaShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureErosion.shp")))
    #CellCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSegments.shp")))
    
    # SAVE ENTIRE COAST OBJECT
    print("\tSaving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(CellCoast, PFile)
    

    

