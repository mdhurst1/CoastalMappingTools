"""
Driver for assessment of future shoreline change in Scotland
Bruun Rule approach

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

# import modules
import pickle, pathlib
import geopandas as gp
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent

# set up output folders
GeometryPath = WorkingPath/("Geometry")
       
if not GeometryPath.exists():
    GeometryPath.mkdir(parents=True, exist_ok=True)
        
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

# locate the baseline shapefile
BaselinePath = WorkingPath / ("My_Baseline.shp")
    
if not BaselinePath.is_file():
    print("No Baseline")

# create a filename and path to save the results
Filename2SaveCoast = BaselinePath / "My_Baseline.pydata"

# check if the coast object already exists    
try:
    CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

# if not do the extraction    
except:
    print("Creating New Coast Object")
        
    # SET UP THE COAST FROM Baseline
    CellCoast = Coast(str(BaselinePath), MinLength=MinLength)
        
    if not CellCoast.BuiltTransects:
            
        # may need to think carefully about how much to smooth
        CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize,NoSmooths=NoSmooths)
            
        # make sure each line is correctly orientated with sea on left as you look down the line
        # this is something we'll need to think about replacing
        # CellCoast.CheckOrientation(str(SoftPath),str(MLWSPath))
        
        # write smoothed coast/bathy to file
        CellCoast.WriteCoastShp(str(BaselinePath / ("Smoothed_Baseline.shp")))
    
        # create some initial dummy transects, check inland/offshore the right way around
        CellCoast.GenerateTransects(TransectSpacing, DistanceInland, DistanceOffshore, CheckTopology=False)
        
        CellCoast.BuiltTransects = True
            
        CellCoast.WriteTransectsShp(str(BaselinePath / ("Transects.shp")))
            
        # SAVE ENTIRE COAST OBJECT
        with open(str(Filename2SaveCoast), 'wb') as PFile:
            pickle.dump(CellCoast, PFile)
        