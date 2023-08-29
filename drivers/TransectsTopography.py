"""
Driver for gennerating transects along a section of coast
and extracting topography from a DEM dataset or composite dataset

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

# import modules
import pickle, sys
from pathlib import Path
import geopandas as gp

# import Coast objects
SourcePath = Path.cwd().parent / "src"
sys.path.append(str(SourcePath))
from Coast import *

# define workspace and data locations
WorkingPath = Path.cwd().parent.parent / "Musselburgh" 
NationalDEMPath = Path("/media/14TB_RAID_Array/Virtual_Box_VMs/VBox_Shared/NCCA2Final/99_NationalData/OSTerrain5")

# set up output folders
GeometryPath = WorkingPath/("Geometry")
PlotPath = WorkingPath/("Plots")
       
if not GeometryPath.exists():
    GeometryPath.mkdir(parents=True, exist_ok=True)
    
if not PlotPath.exists():
    PlotPath.mkdir(parents=True, exist_ok=True)
        
# set the minimum length for coast lines (in m)
# any linse shorter than this will be ignored
MinLength = 50.

# set the transect spacing along the coast line (in m)
TransectSpacing = 10.

# set the distance to extend the transects (in m)
DistanceOffshore = 250.
DistanceInland = 250.

# parameters for smoothing the baseline before creating transect
# larger window and larger nosmooths results in more smoothing
# suggest leaving alone for now.
SmoothingWindowSize = 21
NoSmooths = 100

# locate the input files baseline shapefile
BaselinePath = WorkingPath / ("Musselburgh_Baseline.shp")
MLWSPath = WorkingPath / "Musselburgh_MLWS.shp"

# name the output files
SmoothedBaselinePath = WorkingPath / ("Musselburgh_SmoothedBaseline.shp")
TransectsPath = WorkingPath / ("Musselburgh_Transects.shp")

# Check input files
if not BaselinePath.is_file():
    sys.exit("No Baseline: file ", str(BaselinePath), "does not exist.")
if not MLWSPath.is_file():
    sys.exit("No MLWS: file ", str(MLWSPath), "does not exist.")
    
# create a filename and path to save the results
Filename2SaveCoast = WorkingPath / "Musselburgh.pydata"

# check if the coast object already exists    
try:
    ThisCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

# if not do the extraction    
except:
    print("Creating New Coast Object")
        
    # SET UP THE COAST FROM Baseline
    ThisCoast = Coast(str(BaselinePath), MinLength=MinLength)
        
if not ThisCoast.BuiltTransects:
        
    # may need to think carefully about how much to smooth
    ThisCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
        
    # make sure each line is correctly orientated with sea on left as you look down the line
    # ThisCoast.CheckOrientation(str(SoftPath),str(MLWSPath))
    
    # write smoothed coast/bathy to file
    ThisCoast.WriteCoastShp(str(SmoothedBaselinePath))

    # create some initial dummy transects, check inland/offshore the right way around
    ThisCoast.GenerateTransects(TransectSpacing, DistanceInland, DistanceOffshore, CheckTopology=False)
    
    ThisCoast.BuiltTransects = True
        
    ThisCoast.WriteTransectsShp(str(TransectsPath))
        
    # SAVE ENTIRE COAST OBJECT
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)

if not ThisCoast.SampledDEMs:
    
    # Extend transects landward by a fixed distance and sample DEMs
    # HinterlandDistance = 200
    # ThisCoast.ExtendTransects2Hinterland(HinterlandDistance)
    # ThisCoast.CheckTransectTopology()
    # ThisCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects.shp")))
    
    # Get a list of DEMs to sample on each transect
    ThisCoast.FindDEM(str(NationalDEMPath / "OSTerrain5_fullcoastindex.shp"))
    
    # Extract the topography
    ThisCoast.ExtractTransectTopography()
    
    # Extract as a swath profile (takes longer, especially with higher resolution DEMs and wider swaths)
    # SwathDistance = 5. # max distance from transect line, default is 2*DEM_resolution
    # ThisCoast.ExtractTransectTopographySwath(str(SitePath / DTM), SwathDistance)
    # This currently only works with a single DEM file, need to update to allow list of files similar to above
    
    ThisCoast.SampledDEMs = True
    
    # SAVE ENTIRE COAST OBJECT
    print("\tSaving Coast Object as ", Filename2SaveCoast)
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(ThisCoast, PFile)
        
## plot the results
ThisCoast.PlotTransects(str(PlotPath))
