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

# add src path to find custom modules
sys.path.append("../src/")

#import custom modules
from CMT.Coast import *

# define file names for analysis
DC2Path = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2/WS2_National_Scale_Change/Supersites/Montrose_2024/CMT/")
NewMHWSPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/CCMP/02_secondary_data/Montrose_MHWS/")
VEdgePath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/CCMP/02_secondary_data/Montrose_VEdge/")
WorkingPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/CCMP/03_analysis/Montrose/")
NationalDEMPath = pathlib.Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5/")

# set sea level scenario
# set up scenarios
#Scenarios = [2,4,8]
#Percentiles = [50,50,95]

Scenarios = [8]
Percentiles = [95]

# Decades for writing
Decades = ['2020-01-01', # include current decade as script catches and adjusts future predictions for most recent shoreline date
           '2030-01-01',
           '2040-01-01', 
           '2050-01-01',
           '2060-01-01',
           '2070-01-01',
           '2080-01-01',
           '2090-01-01',
           '2100-01-01',
           '2110-01-01',
           '2120-01-01',
           '2150-01-01',
           '2200-01-01',
           '2250-01-01',
           '2300-01-01'] 

# set up output folders
GeometryPath = WorkingPath/("Geometry")
       
if not GeometryPath.exists(): # checks if geometry folder exists, if not create
    GeometryPath.mkdir(parents=True, exist_ok=True)

PlottingPath = WorkingPath/("Plots")
       
if not PlottingPath.exists(): # checks if geometry folder exists, if not create
    PlottingPath.mkdir(parents=True, exist_ok=True)
        
# set the minimum length
MinLength = 50.

# set the transect spacing (in m)
TransectSpacing = 10.
SmoothingWindowSize = 21 # do not change
NoSmooths = 100 # do not change

# get all coastal cells to loop through
Cells = gp.read_file(DC2Path / "CoastalCells" / "CoastalCells_Partitioned.shp")

# Cell list
CellList = ["2b"] # Montrose in Cell 2b

# loop through each cell
#for index, Row in Cells.iterrows():
for CellSub in CellList:
    # print cell to screen
    #CellSub = Row.Cell_sub
    print("\nRUNNING CELL", CellSub)
    RowName = "Cell_"+CellSub
    
    # try opening bathy file as check on whether there is data
    try:
        gp.read_file(DC2Path / "Bathymetry" / (RowName + "_Bathy.shp"))
    except:
        print("\tUnable to access files for " + RowName)
        continue

    # get soft coast position as most recent
    ModernPath = DC2Path / "MHWS_Lines" / (RowName + "_Open_Baseline_revised_v2.shp") 
    SoftPath = DC2Path / "MHWS_Lines" / (RowName + "_Modern_Soft.shp") 
    LiDARPath = DC2Path / "MHWS_Lines" / (RowName + "_Modern_LiDAR_Montrose2024_PolTips.shp")
    MLWSPath = DC2Path / "MLWS_Lines" / (RowName + "_MLWS.shp") 
    BathyPath = DC2Path / "Bathymetry" / (RowName + "_Bathy.shp") 
    OldPath = DC2Path / "MHWS_Lines" / (RowName + "_MHWS_1890.shp") 
    QuiteOldPath = DC2Path / "MHWS_Lines" / (RowName + "_MHWS_1970.shp") 
    
    DC1Path = DC2Path / "DC1_Results" / (RowName +"_DC1_Results.shp")
    
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
    
    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("Loaded Coastal Object with geomery only", Filename2SaveCoast)
    
    except:
        print("Creating New Coast Object") # if saved geometry not exist

        # SET UP THE COAST FROM -10m Contour
        CellCoast = Coast(str(ModernPath), MinLength=MinLength)
        
    if not CellCoast.BuiltTransects: # do transects already exist?
        
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
        
        # make sure each baseline is correctly orientated with sea on left as you look down the line
        CellCoast.CheckOrientation(str(SoftPath),str(MLWSPath))
        
        # write smoothed coast/bathy to file
        CellCoast.WriteCoastShp(str(GeometryPath / (RowName + "_Smoothed_Baseline.shp")))
    
        # create some initial dummy transects
        CellCoast.GenerateTransects(TransectSpacing, 500, 500, CheckTopology=False) # transect lengths
        
        CellCoast.BuiltTransects = True
        
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.GotHistoricShorelines: # goes to find shorelines
        
        ### loop over all shp in a folder to sample MHWS
        for shp in NewMHWSPath.glob("*.shp"):
            CellCoast.ExtractIndicatorPositions(str(shp), "MHWS", "Date")

        if not MLWSPath.is_file():
            print("No MLWS file")
        else:
            CellCoast.ExtractMLWS(str(MLWSPath))
        
        ### get DC1 results
        # comment this out for now
        CellCoast.SampleDC1Data(str(DC1Path))
        
        #### get MHWS elevation for each transect
        CellCoast.SampleMHWSElevation(str(NewMHWSPath / "scotland_mhws_elev.tif"))
        
        #### get historical rate of relative sea level change
        CellCoast.SampleHistoricalRSLR(str(DC2Path / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
        # Sample rock head position
        CellCoast.SampleRockHeadPosition(str(DC2Path / "UPSM" / "upsm_ncca.tif"))
        
        # Sample coastal defences
        CellCoast.SampleDefencesPosition(str(DC2Path / "Defences" / (RowName + "_Defences.shp"))) # DIFFERENT DEFENCE VERSIONS
        
        CellCoast.GotHistoricShorelines = True
        
        # Get OS year smarter 2020
        CellCoast.Check_OS_Years()
        
        # SAVE ENTIRE COAST OBJECT
        print("\tSaving Coast Object as ", Filename2SaveCoast)
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
    
    if not CellCoast.GotVEdge:

        ### Add capability to loop over all shp in a folder to sample VEdge
        for shp in VEdgePath.glob("*.shp"):
            CellCoast.ExtractIndicatorPositions(str(shp), "VEdge", "SrcDate")
        
        CellCoast.GotVEdge = True
        
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
    
    """
    for Scenario, Percentile in zip(Scenarios, Percentiles): # main loop starting
        
        OutputPath = WorkingPath/("RCP_"+str(Scenario)+"_"+str(Percentile)+"th_OpenCoast")
        
        if not OutputPath.exists():
            OutputPath.mkdir(parents=True, exist_ok=True)
            
        PolygonsPath = OutputPath/("Erosion_Polygons")
        
        if not PolygonsPath.exists():
            PolygonsPath.mkdir(parents=True, exist_ok=True)
        
        # # this checks to see whether coast object already exists
        Filename2SaveAll = OutputPath / (RowName+"_OpenChange.pydata")

        if not CellCoast.PredictedFutureShorelines:    
            
            # Sample coastal defences
            CellCoast.SampleDefencesPosition(str(DC2Path / "Defences" / (RowName + "_Defences.shp")), 25.)
            
            CellCoast.Method = "Open"
            
            ### get future relative sea level time series
            CellCoast.SampleFutureRSL(str(DC2Path / "Future_RSL" / ("RCP"+str(Scenario))), RCP=Scenario, Percentile=Percentile,Years=Decades)
            
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
        CellCoast.TruncateTransects()
        CellCoast.WriteFutureTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
        CellCoast.WriteTransectPointsShp(str(OutputPath / (RowName + "_Points.shp")))
        # write future shorelines
        SmoothOutput = True # smooth coastlines (true) or not (false)
        
        # write coast/bathy to file
        CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Baseline.shp")))
        CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future.shp")),SmoothOutput)
        
        #sys.exit(-1)

        """
    
    # import plotting library
    # from CMT.plotting.Transect_Timeseries_Plots import *

    # loop over transects and plot
    # ThisLine = CellCoast.CoastLines[0]
    # ThisTransect = ThisLine.Transects[373]
    # ThisTransect.AnalyseTimeseries()
    
    # analyse all timeseries
    for ThisTransect in (T for Line in CellCoast.CoastLines for T in Line.Transects):
        ThisTransect.AnalyseTimeseries()
    
    # loop over transects and plot
    ThisLine = CellCoast.CoastLines[0]
    ThisTransect = ThisLine.Transects[373]
    print(ThisTransect.Timeseries)
    
    # write timeseries to shapefiles
    CellCoast.WriteTimeseriesPointsShp(WorkingPath, "Montrose")

    # if True:    
    #     # run the plotting script
    #     Signals = list(ThisTransect.Timeseries.values())
    #     fig, ax = PlotTimeSeriesSignals(Signals, ax=None, ShowErrors=True, RegressionMethods=("TWR",), Title=None)
    #     #fig, ax = PlotShorelineTimeseries(ThisTransect, ax=None, show_errors=True, show_weights=False, StartDate=None, Regression=True)
        
    #     # set up file to save
    #     FigFilename = PlottingPath / ("Transect_" + str(ThisTransect.ID) + ".png")

    #     fig.savefig(FigFilename)
    #     plt.close(fig)
            
        # #Loop through decades
        # for i, Decade in enumerate(Decades):

        #     CellCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_" + str(Decade) + ".shp")), Year=Decade)
        #     CellCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
            
        #     CellCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Influence_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.)
        #     CellCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Vicinity_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.)
        

        # note min and max reversed due to sign convention on volumetric calibration terms
        #CellCoast.PredictFutureShorelines(MinMaxFlag="Min")
        #CellCoast.WriteFutureShorelinesShp(str(OutputPath / (RowName + "_Future_Max.shp")),SmoothOutput)

        #Loop through decades
        #for i, Decade in enumerate(Decades):

            #CellCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_Max" + str(Decade) + ".shp")), Year=Decade)
            #CellCoast.WriteErodedAreaShp(str(PolygonsPath / (RowName + "_ErodedArea_Max" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
            
            #CellCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Influence_Max" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.)
            #CellCoast.WriteErosionProximityShp(str(PolygonsPath / (RowName + "_Vicinity_Max" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.)
