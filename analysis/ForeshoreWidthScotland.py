"""
Driver for assessment of foreshore width in Scotland
For finding beaches mostl likely to be visited post-Covid

Martin Hurst
University of Glasgow
Dynamic Coast 2 Project

"""

import pickle, pathlib, sys
import geopandas as gp
from Coast import *

# define file names for analysis
WorkingPath = pathlib.Path.cwd().parent
OutputPath = WorkingPath/"CovidBeaches"

# set the transect spacing (in m)
TransectSpacing = 500.
SmoothingWindowSize = 51


# # this checks to see whether coast object already exists
Filename2SaveCoast = OutputPath / ("Scotland_Foreshore.pydata")

# get soft coast position as most recent
ModernPath = WorkingPath / "MHWS_Lines" / "Coastline_250k_Lines.shp"
MHWS_2019 = WorkingPath / "MHWS_Lines" / "mhws_sept19_simple.shp"
MLWS_2019 = WorkingPath / "MHWS_Lines" / "mlws_sept19_sc_simp.shp"
IntertidalPolyShp = WorkingPath / "MHWS_Lines" / "OSMM_Intertidal_Poly.shp"
  
if not ModernPath.is_file():
    sys.exit()
    
try:
    ScotlandCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
    print("Loaded Coast Object ", Filename2SaveCoast)

except:
    print("Creating New Coast Object")

    # SET UP THE COAST FROM -10m Contour
    ScotlandCoast = Coast(str(ModernPath))
    
    # may need to think carefully about how much to smooth
    ScotlandCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize)

    # write smoothed coast/bathy to file
    ScotlandCoast.WriteCoastShp(str(OutputPath / ("Scotland_Smoothed_Coast.shp")))
    
    #save here
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(ScotlandCoast, PFile)

if not ScotlandCoast.BuiltTransects:
    
    ScotlandCoast.GenerateTransects(TransectSpacing, 1000, 1000, CheckTopology=False)
            
    ScotlandCoast.WriteTransectsShp(str(OutputPath / ("Scotland_Transects_Raw.shp")))
    
    ScotlandCoast.IntersectTransectsWithIntertidal(IntertidalPolyShp)
    
    ScotlandCoast.WriteTransectsShp(str(OutputPath / ("Scotland_Transects_Poly.shp")))
        
    

