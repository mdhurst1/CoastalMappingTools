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

# set sea level scenario
SeaLevelScenario = 8
SeaLevelScenarioPercentile = 95

# set up output folder
OutputPath = WorkingPath/("RCP_"+str(SeaLevelScenario)+"_"+str(SeaLevelScenarioPercentile)+"th_InnerCoast")
if not OutputPath:
    OutputPath.mkdir(parents=True, exist_ok=True)
    
# set the minimum length
MinLength = 100.

# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize = 21
NoSmooths = 50

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

CellList = ["5f",]

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
    Filename2SaveCoast = OutputPath / (RowName+"_InnerChange.pydata")
    
    # define soft coast position from baseline
    BaselinePath = WorkingPath / "MHWS_Lines" / (RowName + "_Inner_Baseline.shp")
    
    # define other files required
    SoftInnerPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft_Inner.shp")
    SoftPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")
    LiDARPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_LiDAR.shp")
    MLWSPath = WorkingPath / "MLWS_Lines" / (RowName + "_MLWS.shp")
    BathyPath = WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")
    OldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890_Inner.shp")
    QuiteOldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970_Inner.shp")
    DC1Path = WorkingPath / "DC1_Results" / (RowName +"_DC1_Results.shp")
    
    if not BathyPath.is_file():
        print("No Bathy")
        continue
    elif not BaselinePath.is_file():
        print("No Baseline")
        continue
    elif not SoftPath.is_file():
        print("No Soft")
        continue
    elif not DC1Path.is_file():
        print("No DC1")
        continue
    
    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("Loaded Coast Object ", Filename2SaveCoast)

    except:
        print("Creating New Coast Object")

        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(BaselinePath), MinLength=MinLength)
    
    if not CellCoast.BuiltTransects:
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
        
        # make sure each line is correctly orientated with sea on left as you look down the line
        CellCoast.CheckOrientation(str(SoftPath),str(MLWSPath))
        
        # write smoothed coast/bathy to file
        CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))

        # create some initial dummy transects
        CellCoast.GenerateTransects(TransectSpacing, 100, 100, CheckTopology=False)
        
        CellCoast.BuiltTransects = True
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    # force resampling of historical shorelines
    # CellCoast.GotHistoricShorelines = False
    # CellCoast.PredictedFutureShorelines = False
    
    if not CellCoast.GotHistoricShorelines:
        
        # Sample MHWS positions
        if not OldPath.is_file():
            print("No 1890s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(OldPath),Reset=True)
        
        if not QuiteOldPath.is_file():
            print("No 1970s MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
        
        #CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Sampled1.shp")))
        
        if not SoftPath.is_file():
            print("No soft MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath))
            
        if not SoftInnerPath.is_file():
            print("No soft inner MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(SoftInnerPath))
        
        #CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Sampled2.shp")))
        
        if not LiDARPath.is_file():
            print("No LiDAR MHWS file")
        else:
            CellCoast.ExtractHistoricalShorelinePositions(str(LiDARPath))
            
        if not MLWSPath.is_file():
            print("No MLWS file")
        else:
            CellCoast.ExtractMLWS(str(MLWSPath))
        
        ### get DC1 results
        #CellCoast.SampleDC1Data(str(DC1Path))
        
        #### get MHWS elevation for each transect
        CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
    
        #### get historical rate of relative sea level change
        CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
        ### get future relative sea level time series
        CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL" / ("RCP"+str(SeaLevelScenario))), RCP=SeaLevelScenario, Percentile=SeaLevelScenarioPercentile)
        
        # Sample rock head position
        CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
        
        # Sample coastal defences
        CellCoast.SampleDefencesPosition(str(WorkingPath / "Defences" / (RowName + "_Defences.shp")))
        
        CellCoast.GotHistoricShorelines = True
        
        # Get OS year smarter 2020
        CellCoast.Check_OS_Years()
        
        # Wrtie transects
        # CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "Transects_Sampled.shp")))
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.SampledDEMs:
    
        # Extend transects landward by a fixed distance and sample DEMs
        HinterlandDistance = 200
        CellCoast.ExtendTransects2Hinterland(HinterlandDistance)
        #CellCoast.CheckTransectTopology()
        #CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
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
        CellCoast.GetShorefaceSlopesMLWS()
        CellCoast.PredictFutureShorelines()
        CellCoast.PredictedFutureShorelines = True
    
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    # write future shorelines
    CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),Smooth=True)
    
    CellCoast.WriteErodedAreaShp(str(OutputPath / (RowName + "_ErodedArea_2050.shp")), 2050)
    CellCoast.WriteErodedAreaShp(str(OutputPath / (RowName + "_ErodedArea_2100.shp")))
    #CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_UncertaintyArea_2050.shp")), 2050)
    #CellCoast.WriteFutureUncertaintyShp(str(OutputPath / (RowName + "_UncertaintyArea_2100.shp")))
    #CellCoast.WriteFutureErrorShp(str(OutputPath / (RowName + "_ErrorArea_2050.shp")), 2050)
    #CellCoast.WriteFutureErrorShp(str(OutputPath / (RowName + "_ErrorArea_2100.shp")))
    
    CellCoast.TruncateTransects()
    CellCoast.WriteFutureTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
    
    #CellCoast.WriteFutureShorelineSegmentsShp(str(WorkingPath / "CoastalCells" / (RowName + "_FutureSegments.shp")))
    
    Decades = [2020, 2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100]
    
    for i, Decade in enumerate(Decades):
            
        #skip 2020
        if i == 0:
            continue
        
        #Write outputs for each decade both inner and open
        CellCoast.WriteErodedAreaShp(str(OutputPath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")), Year=Decade)
        CellCoast.WriteErodedAreaShp(str(OutputPath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
        CellCoast.WriteErosionProximityShp(str(OutputPath / (RowName + "_Influence_" + str(Decade) + ".shp")), Year=Decade, Distance = 10.)
        CellCoast.WriteErosionProximityShp(str(OutputPath / (RowName + "_Vicinity_" + str(Decade) + ".shp")), Year=Decade, Distance = 60.)
            