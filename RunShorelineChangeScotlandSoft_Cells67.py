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
OutputPath = WorkingPath/"ShorelineRun"

# set the minimum length
MinLength = 100.

# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize = 21
NoSmooths = 50

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# Cell list
CellList = ["6a","6b","6c","6d","6e","6f","7"]

# loop through each cell
#for index, Row in Cells.iterrows():
for CellSub in CellList:
    # print cell to screen
    #CellSub = Row.Cell_sub
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
    
    # get soft coast position as most recent
    ModernPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Final.shp")
    SoftPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")
    LiDARPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_LiDAR.shp")
    BathyPath = WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")
    OldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")
    QuiteOldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")
    
    if not BathyPath.is_file():
        print("No Bathy")
        continue
    elif not ModernPath.is_file():
        print("No soft baseline")
        continue
    elif not SoftPath.is_file():
        print("No Soft")
        continue
        
    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("Loaded Coast Object ", Filename2SaveCoast)

    except:
        print("Creating New Coast Object")

        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(ModernPath), MinLength=MinLength)
    
    if not CellCoast.BuiltTransects:
        
        # rewrite coasts read in
        # CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Raw_Baseline.shp")))
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
        
        CellCoast.CheckOrientation(str(SoftPath),str(BathyPath))
        
        # write smoothed coast/bathy to file
        CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))

        CellCoast.GenerateTransects(TransectSpacing, 200, 200, CheckTopology=False)
        
        # CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Raw.shp")))
        
        CellCoast.BuiltTransects = True
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    # force resampling of historical shorelines
    # CellCoast.GotHistoricShorelines = False
    # CellCoast.PredictedFutureShorelines = False
    
    if not CellCoast.GotHistoricShorelines:
        
        if not OldPath.is_file():
            print("No 1890s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(OldPath),Reset=True)
        
        if not QuiteOldPath.is_file():
            print("No 1970s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
        
        if not SoftPath.is_file():
            print("No soft MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath))
            
        if not LiDARPath.is_file():
            print("No LiDAR MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(LiDARPath))
            
        # CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Sampled.shp")))
    
        #### get MHWS for each transect
        CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
    
        #### get historical rate of relative sea level change
        CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
        ### get future relative sea level time series
        CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL"))
        
        # Sample rock head position
        CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
        
        CellCoast.GotHistoricShorelines = True
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.SampledDEMs:
    
        # Extend transects landward by a fixed distance and sample DEMs
        HinterlandDistance = 200
        CellCoast.ExtendTransects2Hinterland(HinterlandDistance)
        #CellCoast.CheckTransectTopology()
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
        CellCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
        CellCoast.ExtractTransectTopography()
        
        CellCoast.SampledDEMs = True
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
            
    if not CellCoast.PredictedFutureShorelines:    
    
        ## predict future shorelines
        #CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
        CellCoast.GetShorefaceSlopes(str(BathyPath))
        CellCoast.PredictFutureShorelines()
        CellCoast.PredictedFutureShorelines = True
    
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    # write future shorelines
    CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),Smooth=True)
    CellCoast.WriteFutureTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
    CellCoast.WriteErodedAreaShp(str(OutputPath / (RowName + "_ErodedArea_2050.shp")), 2050)
    CellCoast.WriteErodedAreaShp(str(OutputPath / (RowName + "_ErodedArea_2100.shp")))
    CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_UncertaintyArea_2050.shp")), 2050)
    CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_UncertaintyArea_2100.shp")))
    CellCoast.WriteFutureErrorShp(str(OutputPath / (RowName + "_ErrorArea_2050.shp")), 2050)
    CellCoast.WriteFutureErrorShp(str(OutputPath / (RowName + "_ErrorArea_2100.shp")))
    
    #CellCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSegments.shp")))

