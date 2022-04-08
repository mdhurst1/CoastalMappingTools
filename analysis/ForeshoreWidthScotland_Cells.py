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

# read shore and intertidal shps as gdfs
ModernGDF = gp.read_file(str(WorkingPath / "MHWS_Lines" / "Coastline_250k_Lines.shp"))
IntertidalGDF = gp.read_file(str(WorkingPath / "MHWS_Lines" / "OSMM_Intertidal_Poly.shp"))

# open shapefile of coastal cells
Cells = gp.read_file(WorkingPath / "CoastalCells" / "CoastalCells_Partitioned.shp")

def ClipLines2Poly(LinesGDF,PolyGDF):

    IntersectionGeometry = LinesGDF.intersection(PolyGDF)
    Clipped = LinesGDF.copy()
    Clipped["geometry"] = IntersectionGeometry
    return Clipped[~Clipped.geometry.is_empty]

for index, Row in Cells.iterrows():

    print("Cell", Row.Cell_sub)
    
    # Intersection to isolate for each cell
    Intertidal = ClipLines2Poly(IntertidalGDF,Row.geometry)
    Modern = ClipLines2Poly(ModernGDF,Row.geometry)
    
    # Save these to new files
    RowName = "Cell_" + Row.Cell_sub
    
    try:
        Intertidal.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Intertidal.shp"))
    except:
        sys.exit("Unable to write intertidal for " + Row.Cell_sub)
    
    try:
        Modern.to_file(WorkingPath / "MHWS_Lines" / (RowName + "_Modern.shp"))
    except:
        sys.exit("Unable to write modern for " + Row.Cell_sub)
    
    # # this checks to see whether coast object already exists
    Filename2SaveCoast = OutputPath / (RowName + "_Foreshore.pydata")

    try:
        CellCoast = pickle.load( open( Filename2SaveCoast, "rb" ) )
        print("Loaded Coast Object ", Filename2SaveCoast)
    
    except:
        print("Creating New Coast Object")

    # SET UP THE COAST FROM -10m Contour
    CellCoast = Coast(str(WorkingPath / "MHWS_Lines" / (RowName + "_Modern.shp")))
    
    # may need to think carefully about how much to smooth
    CellCoast.SmoothCoastLines(WindowSize=SmoothingWindowSize)

    # write smoothed coast/bathy to file
    CellCoast.WriteCoastShp(str(OutputPath / (RowName + "_Smoothed_Coast.shp")))
    
    #save here
    with open(str(Filename2SaveCoast), 'wb') as PFile:
        pickle.dump(CellCoast, PFile)

    if not CellCoast.BuiltTransects:
        
        CellCoast.GenerateTransects(TransectSpacing, 1000, 1000, CheckTopology=False)
                
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Raw.shp")))
        
        CellCoast.IntersectTransectsWithIntertidal(str(WorkingPath / "MHWS_Lines" / (RowName + "_Intertidal.shp")))
        
        CellCoast.WriteTransectsShp(str(OutputPath / (RowName + "_Transects_Poly.shp")))
            
