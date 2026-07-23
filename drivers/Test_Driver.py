"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

Modified by C. MacDonell, Montrose Project 2024
Example configured by MH 3/7/26

"""

# import modules needed to run the tools
import sys, pickle
from pathlib import Path

# add src path to find custom modules
sys.path.append("../")

#import custom modules
from CMT.Coast import *

# define file names for analysis
ScriptPath = Path(__file__).resolve().parent
DataPath = ScriptPath.parent / "Example_Data" / "Montrose"
ResultsPath = ScriptPath.parent / "Results" / "Montrose"

if not ResultsPath.exists(): # checks if geometry folder exists, if not create
    ResultsPath.mkdir(parents=True, exist_ok=True)

# define data folder and files
BaselinePath = DataPath / ("montrose_baseline.shp")
MLWSPath = DataPath / ("montrose_MLWS.shp") 
BathyPath = DataPath / ("montrose_bathy.shp") 
MHWSPath = DataPath / ("MHWS_Lines")
VEdgePath = DataPath / ("VEdge_Lines")
DEMPath = DataPath / ("OS_Terrain_5")

# set up output folders
GeometryPath = ResultsPath/("Geometry")
if not GeometryPath.exists(): # checks if geometry folder exists, if not create
    GeometryPath.mkdir(parents=True, exist_ok=True)
        
# set the minimum coastal segment length
MinLength = 50.

# set the transect spacing (in m)
TransectSpacing = 10.

print("Creating New Coast Object") # if saved geometry not exist

# SET UP THE COAST FROM -10m Contour
print(BaselinePath)

MontroseCoast = Coast(str(BaselinePath), MinLength=MinLength)
    
# may need to think carefully about how much to smooth
MontroseCoast.SmoothCoastLines(WindowSize=21,NoSmooths=100)

# make sure each baseline is correctly orientated with sea on left as you look down the line
MontroseCoast.CheckOrientation(str(BaselinePath),str(MLWSPath))

# write smoothed coast/bathy to file
MontroseCoast.WriteCoast(ResultsPath / "Montrose_Smoothed_Baseline.shp")
MontroseCoast.WriteCoast(ResultsPath / "Montrose_Smoothed_Baseline.geojson")


# create some initial dummy transects extending 500m offshore and inland
MontroseCoast.GenerateTransects(TransectSpacing, 500, 500, CheckTopology=False) # transect lengths

# write initial transects
MontroseCoast.WriteTransectsShp(str(ResultsPath / "Montrose_Raw_Transects.shp"))            

### loop over all shapefiles in MHWS folder to sample MHWS positions
for shp in MHWSPath.glob("*.shp"):
    MontroseCoast.ExtractIndicatorPositions(str(shp), "MHWS", "Date")

### loop over all shp in a folder to sample VEdge
for shp in VEdgePath.glob("*.shp"):
    MontroseCoast.ExtractIndicatorPositions(str(shp), "VEdge", "SrcDate")

# Sample MLWS positions
MontroseCoast.ExtractMLWS(str(MLWSPath))
        
#### get MHWS elevation for each transect
# The commened out line below will work when a distributed dataset of MHWS elevation is available
# For Dynamic Coast 2 this was a raster dataset provided by poltips
# MontroseCoast.SampleMHWSElevation(str(MHWSPath / "scotland_mhws_elev.tif"))
# In small scale examples such as this a single value is appropriate. 
# The value 2.14 has been sample from the poltips dataset for Scotland
MontroseCoast.SetMHWS(2.14)        

#### get historical rate of relative sea level change
MontroseCoast.SampleHistoricalRSLR(str(DataPath / "RSL_Bradley_Model" / "Scotland_NEngland_RSLR_Modern_BNG.tif"))
    
# Sample rock head position if avaialable
# CellCoast.SampleRockHeadPosition(str(DataPath / "UPSM" / "upsm_ncca.tif"))
        
# Sample coastal defences
MontroseCoast.SampleDefencesPosition(str(DataPath / "Defences" / ("Montrose_Defences.shp")), 25.)
        
# Sample DEMs, this has been designed to work with OSTerrain5 under licence
# MontroseCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
DEMFileList = [str(f) for f in DEMPath.glob("*.tif")]
MontroseCoast.ExtractTransectTopography(DEMFileList)
            
            
# set method for future shoreline predictions "
# Open" is standard Bruun Rule, 
# "Inner" uses a modification for shallow (< 10 m) estuary settings
MontroseCoast.Method = "Open"
            
### get future relative sea level time series from UKCP18 data
Scenario = 8 # RCP 8.5
Percentile = 95 # 95th percentile
MontroseCoast.SampleFutureRSL(str(DataPath / "Future_RSL" / ("RCP"+str(Scenario))), RCP=Scenario, Percentile=Percentile)

## predict future shorelines
MontroseCoast.GetShorefaceSlopes(str(BathyPath))
MontroseCoast.PredictFutureShorelines()

### FUTURE SHORELINE ANALYSIS NEEDS MODIFIED TO WORK WITH TIMESERIES OBJECTS

# Write Future Transects
MontroseCoast.WriteFutureTransectsShp(str(ResultsPath / ("Montrose_Transects.shp")))
MontroseCoast.WriteFutureTransectsShp(str(ResultsPath / ("Montrose_Transects.geojson")))

# write future shorelines
MontroseCoast.WriteFutureShorelinesShp(str(ResultsPath / ("Montrose_Future.shp")), True)
MontroseCoast.WriteFutureShorelinesShp(str(ResultsPath / ("Montrose_Future.geojson")), True)

"""

#Loop through decades to write areas eroded
Decades = [2050, 2100]
for i, Decade in enumerate(Decades):

    MontroseCoast.WriteErodedAreaShp(str(ResultsPath / ("Montrose_ErodedArea_" + str(Decade) + ".shp")), Year=Decade)
    MontroseCoast.WriteErodedAreaShp(str(ResultsPath / ("Montrose_ErodedArea_" + str(Decades[i-1])+"_"+str(Decade) + ".shp")), StartYear = Decades[i-1], Year=Decade)
    
    MontroseCoast.WriteErosionProximityShp(str(ResultsPath / ("Montrose_Influence_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 10.)
    MontroseCoast.WriteErosionProximityShp(str(ResultsPath / ("Montrose_Vicinity_" + str(Decade) + ".shp")), Year=Decade, BufferDistance = 60.)
"""