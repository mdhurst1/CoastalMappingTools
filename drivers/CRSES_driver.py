"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

Modified by C. MacDonell, CRSES Project 2025

"""

# add modules
import os, sys
import pickle, pathlib
import geopandas as gp
from datetime import datetime
import matplotlib.pyplot as plt
#%matplotlib qt5

#import custom modules
from src.Coast import *

# define file names for analysis
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/CMT_CRSES")
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")

# set sea level scenario
# set up scenarios
Scenarios = [2,4,8]
Percentiles = [50,50,95]

# Decades for writing
Decades = ['2020-01-01', # include current decade as script catches and adjusts future predictions for most recent shoreline date
           '2030-01-01',
           '2040-01-01', 
           '2050-01-01',
           '2060-01-01',
           '2070-01-01',
           '2080-01-01',
           '2090-01-01',
           '2100-01-01']
# =============================================================================
#            '2110-01-01',
#            '2120-01-01',
#            '2150-01-01',
#            '2200-01-01',
#            '2250-01-01',
#            '2300-01-01'] 
# =============================================================================

# set up output folders
GeometryPath = WorkingPath/("Geometry")
       
if not GeometryPath.exists(): # checks if geometry folder exists, if not create
    GeometryPath.mkdir(parents=True, exist_ok=True)
        
# set the minimum length of baseline segments
MinLength = 50.

# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize = 21 # do not change
NoSmooths = 100 # do not change

# get all coastal cells to loop through
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

# Cell list
CellList = ["1a","1b","1c","1d","2a"]


# loop through each cell
for CellSub in CellList:
    # print cell to screen
    print("\nRUNNING CELL", CellSub)
    RowName = "Cell_"+CellSub
    
    # try opening bathy file as check on whether there is data
    try:
        gp.read_file(WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp"))
    except:
        print("\tUnable to access files for " + RowName)
        continue

    # get soft coast position as most recent
    ModernPath = WorkingPath / "MHWS_Lines" / (RowName + "_Open_Baseline.shp") # only doing open?
    
    OldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1890.shp") 
    QuiteOldPath = WorkingPath / "MHWS_Lines" / (RowName + "_MHWS_1970.shp") 
    SoftPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_Soft.shp") 
    
    LiDARPath = WorkingPath / "MHWS_Lines" / (RowName + "_Modern_LiDAR_CRSESupdate.shp")
    
    MLWSPath = WorkingPath / "MLWS_Lines" / (RowName + "_MLWS.shp") 
    
    BathyPath = WorkingPath / "Bathymetry" / (RowName + "_Bathy.shp") 
    
    DC1Path = WorkingPath / "DC1_Results" / (RowName +"_DC1_Results.shp")
    
    if not BathyPath.is_file():
        print("No Bathy")
        continue
    elif not ModernPath.is_file():
        print("No soft baseline")
        continue
    elif not SoftPath.is_file():
        print("No Soft")
        continue
    
    Filename2SaveCoast = GeometryPath / (RowName+"_OpenGeometry.pydata")
    
    for Scenario, Percentile in zip(Scenarios, Percentiles): # main loop starting
        print("\n\t Scenario:",str(Scenario))
        print("\n\t Percentile:",str(Percentile))
        print("\n")
        
        OutputPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
        
        if not OutputPath.exists():
            OutputPath.mkdir(parents=True, exist_ok=True)
            
        PolygonsPath = OutputPath/("Erosion_Polygons")
        
        if not PolygonsPath.exists():
            PolygonsPath.mkdir(parents=True, exist_ok=True)
        
        # # this checks to see whether coast object already exists
        Filename2SaveAll = OutputPath / (RowName+"_OpenChange.pydata")
    
        if Filename2SaveCoast.exists():
            CellCoast = pickle.load(open(Filename2SaveCoast, "rb" ))
            print("Loaded Coast Object ", Filename2SaveCoast)
        else:
            print("Creating New Coast Object") # if saved geometry not exist
            # SET UP THE COAST FROM -10m Contour
            CellCoast = Coast(str(ModernPath), MinLength=MinLength)
        
        if not CellCoast.BuiltTransects: # do transects already exist?
            
            # may need to think carefully about how much to smooth
            CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
            
            # make sure each baseline is correctly orientated with sea on left as you look down the line
            CellCoast.CheckOrientation(str(SoftPath),str(MLWSPath))
            
            # write smoothed coast/bathy to file
            CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))
        
            # create some initial dummy transects
            CellCoast.GenerateTransects(TransectSpacing, 200, 200, CheckTopology=False) # transect lengths
            CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_RawTransects.shp")))
            #continue # to quickly build transects only
            #sys.exit('Finished transects for editing')
            CellCoast.BuiltTransects = True
            
            # SAVE ENTIRE COAST OBJECT
            with open(str(Filename2SaveCoast), 'wb') as PFile:
                pickle.dump(CellCoast, PFile)
        
        if not CellCoast.GotHistoricShorelines: # goes to find shorelines
            
            # Sample MHWS positions
            
            if not SoftPath.is_file():
                print("No soft MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(SoftPath),Reset=True)
            
            if not OldPath.is_file():
                print("No 1890s MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(OldPath))
            
            if not QuiteOldPath.is_file():
                print("No 1970s MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
            
            if not LiDARPath.is_file():
                print("No LiDAR MHWS file")
            else:
                CellCoast.ExtractHistoricalShorelinePositions(str(LiDARPath),AllowMultiples=True)
                
            if not MLWSPath.is_file():
                print("No MLWS file")
            else:
                CellCoast.ExtractMLWS(str(MLWSPath))
            
            ### get DC1 results
            # comment this out for now
            CellCoast.SampleDC1Data(str(DC1Path))
            
            #### get MHWS elevation for each transect
            CellCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
            
            #### get historical rate of relative sea level change
            CellCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
        
            # Sample rock head position
            CellCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
                       
            # Sample coastal defences
            CellCoast.SampleDefencesPosition(str(WorkingPath / "Defences" / (RowName + "_Defences.shp")),25.) # DIFFERENT DEFENCE VERSIONS
            #CellCoast.SampleDefencesPosition(str(WorkingPath / "Defences" / "Cells_1a_2a_NoDefences_CRSES.shp")) # DIFFERENT DEFENCE VERSIONS
            
            CellCoast.GotHistoricShorelines = True
            
            # Get OS year smarter 2020
            CellCoast.Check_OS_Years()
            
            # SAVE ENTIRE COAST OBJECT
            print("\tSaving Coast Object as ", Filename2SaveCoast)
            with open(str(Filename2SaveCoast), 'wb') as PFile:
                pickle.dump(CellCoast, PFile)
        
        if not CellCoast.SampledDEMs:
        
            # Extend transects landward by a fixed distance and sample DEMs
            #HinterlandDistance = 200
            #CellCoast.ExtendTransects2Hinterland(HinterlandDistance)
            CellCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
            CellCoast.ExtractTransectTopography()
            
            CellCoast.SampledDEMs = True
            
            # SAVE ENTIRE COAST OBJECT
            print("\tSaving Coast Object as ", Filename2SaveCoast)
            with open(str(Filename2SaveCoast), 'wb') as PFile:
                pickle.dump(CellCoast, PFile)
        
        if not CellCoast.PredictedFutureShorelines:    
            
            # Sample coastal defences
            #CellCoast.SampleDefencesPosition(str(WorkingPath / "Defences" / (RowName + "_Defences.shp")), 25.)
            CellCoast.SampleDefencesPosition(str(WorkingPath / "Defences" / "Cells_1a_2a_NoDefences_CRSES.shp"))
            
            CellCoast.Method = "Open"
            
            ### get future relative sea level time series
            CellCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL" / ("RCP"+str(Scenario))), RCP=Scenario, Percentile=Percentile,Years=Decades)
            
            ## predict future shorelines
            CellCoast.GetShorefaceSlopes(str(BathyPath))
            CellCoast.PredictFutureShorelines()
            CellCoast.PredictedFutureShorelines = True
        
            # SAVE ENTIRE COAST OBJECT
            print("\tSaving Coast Object as ", Filename2SaveAll)
            with open(str(Filename2SaveAll), 'wb') as PFile:
                pickle.dump(CellCoast, PFile)
                
        # write transect during debugging for GIS interface interogation
        print('Writing transects to',str(OutputPath / (RowName + "_Transects.shp")))
        CellCoast.WriteFutureTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
        
        # write future shorelines
        SmoothOutput = False # smooth coastlines (true) or not (false)
        
        # write coast/bathy to file
        CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))
        CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),SmoothOutput)
        
        #sys.exit(-1)
        
        # FUTURE POLYGONS
        print('\n\n\t STARTING POLYGONS:',str(RowName),'Scenario:',Scenario,'Percentile:',Percentile,"\n")

        polySmooth = False
        
        #Loop through decades
        for i, Decade in enumerate(Decades):
            print("\t Write Eroded Area, Decade:",str(Decade))
            CellCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")), Year=Decade, Smooth=polySmooth)
            #if i >= 1:
                #print("\t Decade:",str(Decades[i-1])+"_"+str(Decade))
                #CellCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade,Smooth=polySmooth)
            
            print("\t Write Erosion Influence, Decade:",str(Decade))
            CellCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Influence_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.,Smooth=polySmooth)
            print("\t Write Erosion Vicinity, Decade:",str(Decade))
            CellCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Vicinity_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.,Smooth=polySmooth)

print('\n \n COMPLETED ALL PROCESSING FOR ',str(RowName))
