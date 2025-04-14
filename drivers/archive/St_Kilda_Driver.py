"""
Driver for assessment of future shoreline change in Cullipool

Martin Hurst
University of Glasgow
June 2022

"""

import pickle, pathlib
import geopandas as gp
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/StKilda/")
DC2Path = WorkingPath.parent / ("WS2_National_Scale_Change/")
DEMPath = WorkingPath/("S10StKilda/_Village_Bay/DEM/StK_VillBay_05m.tif")
ProjectName = "StKilda"

# set sea level scenario
# set up scenarios
Scenarios = [2,4,8]
Percentiles = [50,50,95]


# set up output folders
GeometryPath = WorkingPath/("Geometry")
PlotPath = WorkingPath/("Plots")
       
if not GeometryPath.exists():
    GeometryPath.mkdir(parents=True, exist_ok=True)
    
if not PlotPath.exists():
    PlotPath.mkdir(parents=True, exist_ok=True)
    
# set the minimum length
MinLength = 50.

# set the transect spacing (in m)
TransectSpacing = 5.
SmoothingWindowSize = 21
NoSmooths = 100

# get soft coast position as most recent

#ModernPath = WorkingPath / ("OSMM_StK/OSMM_StK_MHWS_Line.shp")
ModernPath = WorkingPath / ("OSMM_StK/MHWS_1968.shp")
LiDARPath = WorkingPath / ("LiDAR/MHWS_2011_HES_LiDAR_1.82m.shp")
SoftPath = WorkingPath / ("OSMM_StK/MHWS_1968.shp")
QuiteOldPath = WorkingPath / ("OSMM_StK/MHWS_1968.shp")
OldPath = WorkingPath / "nope"

# get bathymetry path
BathyPath = WorkingPath / "Bathy" / ("StKilda_10m_DepthContour.shp")

if not BathyPath.is_file():
    sys.exit("No Bathy")
elif not ModernPath.is_file():
    print(ModernPath)
    sys.exit("No Baseline")
elif not SoftPath.is_file():
    sys.exit("No Soft")
    
Filename2SaveCoast = GeometryPath / (ProjectName+"_Geometry.pydata")

Reset = True
    
for Scenario, Percentile in zip(Scenarios, Percentiles):
    
    OutputPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
    
    if not OutputPath.exists():
        OutputPath.mkdir(parents=True, exist_ok=True)
    
    # # this checks to see whether coast object already exists
    Filename2SaveAll = OutputPath / (ProjectName+"_OpenChange.pydata")

    if not Reset:
        try:
            ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
            print("Loaded Coast Object ", Filename2SaveCoast)
    
        except:
            print("Creating New Coast Object")
            # SET UP THE COAST FROM -10m Contour
            ThisCoast = Coast(str(ModernPath), MinLength=MinLength)
    
    else:
        # SET UP THE COAST FROM -10m Contour
        ThisCoast = Coast(str(ModernPath), MinLength=MinLength)
        
    if not ThisCoast.BuiltTransects:
        
        # may need to think carefully about how much to smooth
        ThisCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
        
        # make sure each line is correctly orientated with sea on left as you look down the line
        ThisCoast.CheckOrientation(str(SoftPath),str(BathyPath))
        
        # write smoothed coast/bathy to file
        ThisCoast.WriteCoastShp(str(OutputPath / (ProjectName + "_Smoothed_Baseline.shp")))
    
        # create some initial dummy transects
        ThisCoast.GenerateTransects(TransectSpacing, 200, 200, CheckTopology=False)
        
        ThisCoast.BuiltTransects = True
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(ThisCoast, PFile)
    
    if not ThisCoast.GotHistoricShorelines:
        
        # Sample MHWS positions
        
        if not SoftPath.is_file():
            print("No soft MHWS file")
        else:
            ThisCoast.ExtractHistoricalShorelinePositions(str(SoftPath),Reset=True)
        
        if not OldPath.is_file():
            print("No 1890s MHWS file")
        else:
            ThisCoast.ExtractHistoricalShorelinePositions(str(OldPath))
        
        if not QuiteOldPath.is_file():
            print("No 1970s MHWS file")
        else:
            ThisCoast.ExtractHistoricalShorelinePositions(str(QuiteOldPath))
        
        if not LiDARPath.is_file():
            print("No LiDAR MHWS file")
        else:
            ThisCoast.ExtractHistoricalShorelinePositions(str(LiDARPath),AllowMultiples=True)
            
        #### get historical rate of relative sea level change
        ThisCoast.SampleHistoricalRSLR(str(DC2Path / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
        ThisCoast.GotHistoricShorelines = True
        
        # Get OS year smarter 2020
        ThisCoast.Check_OS_Years()
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(ThisCoast, PFile)
    
#    if not ThisCoast.SampledDEMs:
#    
#        # Extend transects landward by a fixed distance and sample DEMs
#        #HinterlandDistance = 200
#        #ThisCoast.ExtendTransects2Hinterland(HinterlandDistance)
#        #ThisCoast.CheckTransectTopology()
#        #ThisCoast.WriteTransectsShp(str(OutputPath / (ProjectName + "_Transects.shp")))
#        ThisCoast.ExtractTransectTopography(DEMFileList=[str(DEMPath),])
#        
#        ThisCoast.SampledDEMs = True
#        
#        # SAVE ENTIRE COAST OBJECT
#        print("\tSaving Coast Object as ", Filename2SaveCoast)
#        with open(str(Filename2SaveCoast), 'wb') as PFile:
#            pickle.dump(ThisCoast, PFile)
    
    if not ThisCoast.PredictedFutureShorelines:    
        
        ThisCoast.Method = "Open"
        
        ### get future relative sea level time series
        
        ThisCoast.SampleFutureRSL(str(DC2Path / "Future_RSL" / ("RCP"+str(Scenario))), RCP=Scenario, Percentile=Percentile)
        
        ## predict future shorelines
        ThisCoast.SetMHWS(1.68)
        ThisCoast.GetShorefaceSlopes(str(BathyPath))
        ThisCoast.PredictFutureShorelines()
        ThisCoast.PredictedFutureShorelines = True
    
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveAll)
        with open(str(Filename2SaveAll), 'wb') as PFile:
            pickle.dump(ThisCoast, PFile)
    
    # write future shorelines
    # write smoothed coast/bathy to file
    ThisCoast.WriteFutureTransectsShp(str(OutputPath / (ProjectName + "_Transects.shp")))
    
    ThisCoast.WriteCoastShp(str(OutputPath / (ProjectName + "_Smoothed_Baseline.shp")))
    ThisCoast.WriteFutureShorelinesShp(str(OutputPath / (ProjectName + "_Future.shp")),Smooth=False)
        
    ThisCoast.TruncateTransects()
    ThisCoast.WriteFutureTransectsShp(str(OutputPath / (ProjectName + "_Transects_Truncated.shp")))

#ThisCoast.AnalyseExtremeWater([3.2,4.0,4.9])
#ThisCoast.PlotTransects(str(PlotPath))
    