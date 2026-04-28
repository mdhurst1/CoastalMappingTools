"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

Modified by C. MacDonell, Montrose Project 2024

"""

# add modules
import sys
import pickle, pathlib
import geopandas as gp
from datetime import datetime
import matplotlib.pyplot as plt
%matplotlib qt5

# add src path to find custom modules
sys.path.append("../src/")

#import custom modules
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path("../../CMT_Examples")
if not WorkingPath.exists(): # checks if geometry folder exists, if not create
    WorkingPath.mkdir(parents=True, exist_ok=True)

# define data folder and files
DataPath = pathlib.Path("../example_data/")
BaselinePath = DataPath / ("montrose_baseline.shp")
LiDARPath = WorkingPath / ("montrose_MHWS_Modern_LiDAR.shp")
MLWSPath = DataPath / ("montrose_MLWS.shp") 
BathyPath = DataPath / ("montrose_bathy.shp") 
OldPath = DataPath / ("montrose_MHWS_1890.shp")
QuiteOldPath = DataPath / ("montrose_MHWS_1970.shp") 

# set up output folders
GeometryPath = WorkingPath/("Geometry")
if not GeometryPath.exists(): # checks if geometry folder exists, if not create
    GeometryPath.mkdir(parents=True, exist_ok=True)
        
# set the minimum coastal segment length
MinLength = 50.

# set the transect spacing (in m)
TransectSpacing = 10.

# parameters for smoothing the baseline
SmoothingWindowSize = 21 # do not change
NoSmooths = 100 # do not change

# setup filename for loading/saving geometry
Filename2SaveCoast = GeometryPath / ("montrose_Geometry.pydata")
    
try: # check if geometry already been created
    MontroseCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)
        
except:
    print("Creating New Coast Object") # if saved geometry not exist

    # SET UP THE COAST FROM -10m Contour
    MontroseCoast = Coast(str(BaselinePath), MinLength=MinLength)
        
    if not MontroseCoast.BuiltTransects: # do transects already exist?
        
        # may need to think carefully about how much to smooth
        MontroseCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
        
        # make sure each baseline is correctly orientated with sea on left as you look down the line
        MontroseCoast.CheckOrientation(str(BaselinePath),str(MLWSPath))
        
        # write smoothed coast/bathy to file
        MontroseCoast.WriteCoastShp(str(WorkingPath / "Montrose_Smoothed_Baseline.shp"))
    
        # create some initial dummy transects
        MontroseCoast.GenerateTransects(TransectSpacing, 500, 500, CheckTopology=False) # transect lengths

        # write initial transects
        MontroseCoast.WriteTransects(str(WorkingPath / "Montrose_Transects.shp"))            
        MontroseCoast.BuiltTransects = True
            
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(MontroseCoast, PFile)

"""
        if not MontroseCoast.GotHistoricShorelines: # goes to find shorelines
            
            # Sample MHWS positions
            
            if not SoftPath.is_file():
                print("No soft MHWS file")
            else:
                MontroseCoast.ExtractHistoricalShorelinePositions(str(SoftPath),Reset=True)
            
            if not OldPath.is_file():
                print("No 1890s MHWS file")
            else:
                MontroseCoast.ExtractHistoricalShorelinePositions(str(OldPath))
            
            if not QuiteOldPath.is_file():
                print("No 1970s MHWS file")
            else:
                MontroseCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
            
            if not LiDARPath.is_file():
                print("No LiDAR MHWS file")
            else:
                MontroseCoast.ExtractHistoricalShorelinePositions(str(LiDARPath),AllowMultiples=True)
                
            if not MLWSPath.is_file():
                print("No MLWS file")
            else:
                MontroseCoast.ExtractMLWS(str(MLWSPath))
            
            ### get DC1 results
            # comment this out for now
            MontroseCoast.SampleDC1Data(str(DC1Path))
            
            #### get MHWS elevation for each transect
            MontroseCoast.SampleMHWSElevation(str(WorkingPath / "MHWS_Lines" / "scotland_mhws_elev.tif"))
            
            #### get historical rate of relative sea level change
            MontroseCoast.SampleHistoricalRSLR(str(WorkingPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
        
            # Sample rock head position
            MontroseCoast.SampleRockHeadPosition(str(WorkingPath / "UPSM" / "upsm_ncca.tif"))
            
            # Sample coastal defences
            MontroseCoast.SampleDefencesPosition(str(WorkingPath / "Defences" / (RowName + "_Defences.shp"))) # DIFFERENT DEFENCE VERSIONS
            
            MontroseCoast.GotHistoricShorelines = True
            
            # Get OS year smarter 2020
            MontroseCoast.Check_OS_Years()
            
            # SAVE ENTIRE COAST OBJECT
            print("\tSaving Coast Object as ", Filename2SaveCoast)
            with open(str(Filename2SaveCoast), 'wb') as PFile:
                pickle.dump(MontroseCoast, PFile)
        
        if not MontroseCoast.SampledDEMs:
        
            # Extend transects landward by a fixed distance and sample DEMs
            #HinterlandDistance = 200
            #MontroseCoast.ExtendTransects2Hinterland(HinterlandDistance)
            MontroseCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
            MontroseCoast.ExtractTransectTopography()
            
            MontroseCoast.SampledDEMs = True
            
            # SAVE ENTIRE COAST OBJECT
            print("\tSaving Coast Object as ", Filename2SaveCoast)
            with open(str(Filename2SaveCoast), 'wb') as PFile:
                pickle.dump(MontroseCoast, PFile)
        
        if not MontroseCoast.PredictedFutureShorelines:    
            
            # Sample coastal defences
            MontroseCoast.SampleDefencesPosition(str(WorkingPath / "Defences" / (RowName + "_Defences.shp")), 25.)
            
            MontroseCoast.Method = "Open"
            
            ### get future relative sea level time series
            MontroseCoast.SampleFutureRSL(str(WorkingPath / "Future_RSL" / ("RCP"+str(Scenario))), RCP=Scenario, Percentile=Percentile,Years=Decades)
            
            ## predict future shorelines
            MontroseCoast.GetShorefaceSlopes(str(BathyPath))
            MontroseCoast.PredictFutureShorelines()
            MontroseCoast.PredictedFutureShorelines = True
        
            # SAVE ENTIRE COAST OBJECT
            print("\tSaving Coast Object as ", Filename2SaveAll)
            with open(str(Filename2SaveAll), 'wb') as PFile:
                pickle.dump(MontroseCoast, PFile)
                
        # write transect during debugging for GIS interface interogation
        print('Writing transects to',str(OutputPath / (RowName + "_Transects.shp")))
        MontroseCoast.WriteFutureTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
        
        # write future shorelines
        SmoothOutput = True # smooth coastlines (true) or not (false)
        
        # write coast/bathy to file
        MontroseCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))
        MontroseCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),SmoothOutput)
        
        #sys.exit(-1)

        #Loop through decades
        for i, Decade in enumerate(Decades):

            MontroseCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")), Year=Decade)
            MontroseCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
            
            MontroseCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Influence_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.)
            MontroseCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Vicinity_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.)
        

        # note min and max reversed due to sign convention on volumetric calibration terms
        MontroseCoast.PredictFutureShorelines(MinMaxFlag="Min")
        MontroseCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future_Max.shp")),SmoothOutput)

        #Loop through decades
        for i, Decade in enumerate(Decades):

            MontroseCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_Max" + str(Decade) + ".shp")), Year=Decade)
            MontroseCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_Max" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
            
            MontroseCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Influence_Max" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.)
            MontroseCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Vicinity_Max" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.)
"""