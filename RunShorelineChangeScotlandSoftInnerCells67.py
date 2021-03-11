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
# set up scenarios
Scenarios = [2,4,8]
Percentiles = [50,50,95]

# set up output folders
GeometryPath = WorkingPath/("Geometry")
       
if not GeometryPath.exists():
    GeometryPath.mkdir(parents=True, exist_ok=True)
        
# set the minimum length
MinLength = 50.

# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize = 21
NoSmooths = 50

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

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

    # define soft coast position from baseline
    BaselinePath = WorkingPath / "MHWS_Lines" / (RowName + "_Inner_Baseline.shp")
    
    # define other files required
    SoftPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp")
    LiDARPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_LiDAR.shp")
    MLWSPath = WorkingPath / "MLWS_Lines" / (RowName + "_MLWS.shp")
    BathyPath = WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp")
    OldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp")
    QuiteOldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp")
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
    
    Filename2SaveCoast = GeometryPath / (RowName+"_InnerGeometry.pydata")
    
    FirstTime = True
    
    for Scenario, Percentile in zip(Scenarios, Percentiles):
        
        OutputPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_InnerCoast")
        
        if not OutputPath.exists():
            OutputPath.mkdir(parents=True, exist_ok=True)
        
        # # this checks to see whether coast object already exists
        Filename2SaveAll = OutputPath / (RowName+"_InnerChange.pydata")
            
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
        if FirstTime:
            CellCoast.GotHistoricShorelines = False
            FirstTime = False
        
        if not CellCoast.GotHistoricShorelines:
            
            # Sample MHWS positions
            if not SoftPath.is_file():
                print("No soft MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath), Reset=True)
                
            if not OldPath.is_file():
                print("No 1890s MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(OldPath),Reset=True)
            
            if not QuiteOldPath.is_file():
                print("No 1970s MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
            
            if not LiDARPath.is_file():
                print("No LiDAR MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(LiDARPath))
                
            if not MLWSPath.is_file():
                print("No MLWS file")
            else:
                CellCoast.ExtractMLWS(str(MLWSPath))
            
            ### get DC1 results
            ### Save this for later
            # CellCoast.SampleDC1Data(str(DC1Path))
            
            #### get MHWS elevation for each transect
            CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
        
            #### get historical rate of relative sea level change
            CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
        
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
            
            CellCoast.Method = "Inner"
            
            ### get future relative sea level time series
            CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL" / ("RCP"+str(Scenario))), RCP=Scenario, Percentile=Percentile)
            
            ## predict future shorelines
            #CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
            CellCoast.GetShorefaceSlopesMLWS()
            CellCoast.PredictFutureShorelines()
            CellCoast.PredictedFutureShorelines = True
        
            # SAVE ENTIRE COAST OBJECT
            print("\tSaving Coast Object as ", Filename2SaveAll)
            with open(str(Filename2SaveAll), 'wb') as PFile:
                pickle.dump(CellCoast, PFile)
        
        # write future shorelines
        CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),Smooth=True)
        
        CellCoast.TruncateTransects()
        CellCoast.WriteFutureTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
            